"""Prepare approved book assets outside Git. Requires Pillow; does not publish."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--book-root', required=True, type=Path)
args = parser.parse_args()
book = json.loads((ROOT / 'site.json').read_text())['books'][0]
source = args.book_root / 'output/pdf' / book['pdf']
if hashlib.sha256(source.read_bytes()).hexdigest() != book['pdf_sha256']:
    raise SystemExit('The PDF does not match the approved edition. Nothing published.')
dest = ROOT / 'release'
dest.mkdir(exist_ok=True)
shutil.copyfile(source, dest / book['pdf'])
images = {
    book['images']['cover']: 'page-01.png',
    book['images']['workshop']: 'spreads/spread-14-15.png',
    book['images']['transmission']: 'spreads/spread-62-63.png',
}
with zipfile.ZipFile(dest / book['media_archive'], 'w') as archive:
    for name, relative in sorted(images.items()):
        source_image = args.book_root / 'tmp/pdfs/cinematic' / relative
        with Image.open(source_image) as image:
            stream = io.BytesIO()
            image.convert('RGB').save(stream, 'JPEG', quality=90, optimize=True, progressive=True)
        entry = zipfile.ZipInfo(name, date_time=(2026, 9, 5, 0, 0, 0))
        archive.writestr(entry, stream.getvalue())
for path in sorted(dest.iterdir()):
    print(path.name, path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest())
