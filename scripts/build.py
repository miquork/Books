"""Build a small, allowlisted Markdown bookshelf; no private source is published."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
from string import Template
import urllib.request
import zipfile

import markdown

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def release_url(config, book, name):
    return f'https://github.com/{config["repository"]}/releases/download/{book["release_tag"]}/{name}'


def checked_download(url, target, expected):
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or digest(target) != expected:
        with urllib.request.urlopen(url, timeout=60) as response, target.open('wb') as out:
            shutil.copyfileobj(response, out)
    if digest(target) != expected:
        raise ValueError(f'Checksum mismatch: {target.name}')


def render_site(output, local_release=None):
    config = json.loads((ROOT / 'site.json').read_text())
    base = config['base_path'].rstrip('/')
    template = Template((ROOT / 'templates/page.html').read_text())
    output = Path(output)
    # The output is intentionally required to be new: never recursively delete a directory.
    output.mkdir(parents=True, exist_ok=False)
    (output / 'assets').mkdir()
    shutil.copyfile(ROOT / 'assets/style.css', output / 'assets/style.css')
    (output / '.nojekyll').touch()

    def page(route, title, description, body):
        dest = output / route / 'index.html'
        dest.parent.mkdir(parents=True, exist_ok=True)
        canonical = config['url'] + base + '/' + (route + '/' if route else '')
        dest.write_text(template.substitute(title=html.escape(title), description=html.escape(description),
            canonical=html.escape(canonical), base=base, body=body), encoding='utf-8')

    def md(name):
        return markdown.markdown((ROOT / 'content' / name).read_text())

    features = []
    for book in config['books']:
        slug = book['slug']
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
            raise ValueError('Unsafe book slug')
        media_dir = output / 'assets' / slug
        media_dir.mkdir()
        if local_release:
            archive = Path(local_release) / book['media_archive']
            pdf = Path(local_release) / book['pdf']
        else:
            cache = ROOT / 'build' / 'downloads' / book['release_tag']
            archive = cache / book['media_archive']
            pdf = cache / book['pdf']
            checked_download(release_url(config, book, book['media_archive']), archive, book['media_sha256'])
            checked_download(release_url(config, book, book['pdf']), pdf, book['pdf_sha256'])
        if digest(archive) != book['media_sha256'] or digest(pdf) != book['pdf_sha256']:
            raise ValueError('Release differs from the approved edition')
        if pdf.stat().st_size != book['pdf_bytes']:
            raise ValueError('PDF size mismatch')
        expected = set(book['images'].values())
        if any(Path(name).name != name for name in expected):
            raise ValueError('Unsafe image filename')
        with zipfile.ZipFile(archive) as z:
            if len(z.infolist()) != len(expected) or set(z.namelist()) != expected:
                raise ValueError('Unexpected or duplicate archive entries')
            for name in sorted(expected):
                info = z.getinfo(name)
                if info.file_size > 10_000_000:
                    raise ValueError('Oversized web image')
                # No extractall: ignore archive permissions and never follow symlinks.
                data = z.read(name)
                if not data.startswith(b'\xff\xd8\xff'):
                    raise ValueError('Expected JPEG image')
                (media_dir / name).write_bytes(data)

        b = {k: html.escape(v, quote=True) for k, v in book.items() if isinstance(v, str)}
        image_base = f'{base}/assets/{slug}'
        cover = f'{image_base}/{book["images"]["cover"]}'
        link = f'{base}/{slug}/'
        download = html.escape(release_url(config, book, book['pdf']), quote=True)
        size = f'{book["pdf_bytes"] / 1_000_000:.1f} MB'
        cover_img = f'<img class="cover" src="{cover}" width="630" height="900" alt="Cover of {b["title"]}">'
        actions = f'<div class="actions"><a class="button" href="{download}">Download the PDF <span aria-hidden="true">&nbsp;↓</span></a></div><p class="meta">Free download · {size} · No sign-up</p>'
        previews = []
        for preview in book.get('previews', []):
            if preview.get('quote'):
                previews.append('<blockquote>“' + html.escape(preview['quote']) + '”</blockquote>')
            image_name = book['images'][preview['image']]
            previews.append(f'''<figure class="spread"><img loading="lazy"
              src="{image_base}/{image_name}" width="1260" height="900"
              alt="{html.escape(preview['alt'], quote=True)}">
              <figcaption>{html.escape(preview['caption'])}</figcaption></figure>''')
        features.append(f'''<article class="book-feature">
          <a class="cover-link" href="{link}" aria-label="Explore {b['title']}">{cover_img}</a>
          <div><p class="eyebrow">{b['category']}</p>
          <h2 class="book-title">{b['title']}</h2><p class="subtitle">{b['subtitle']}</p>
          <p class="hook">{b['hook']}</p><p class="description">{b['description']}</p>
          <p class="meta">{b['format']}</p><div class="actions"><a class="button" href="{link}">Explore the book</a>
          <a class="text-link" href="{download}">Download PDF · {size}</a></div></div></article>''')
        body = f'''<section class="book-feature book-hero">{cover_img}<div>
          <p class="eyebrow">{b['category']}</p>
          <h1>{b['title']}</h1><p class="subtitle">{b['subtitle']}</p>
          <p class="hook">{b['hook']}</p><p class="meta">{b['format']}</p>{actions}</div></section>
          <div class="prose">{md(slug + '.md')}</div>
          {''.join(previews)}
          <section class="prose credits">{md(slug + '-credits.md')}
          <div class="download-panel"><h2>Open the experiment</h2><p>{b['format']}<br>{b['edition']}</p>{actions}
          <p class="meta">For the intended spread layout, select two-page view with the cover shown separately in your PDF reader.</p>
          <details><summary>Edition and file integrity</summary><p>SHA-256:</p><code>{b['pdf_sha256']}</code>
          <p><a href="https://github.com/{config['repository']}/releases/tag/{b['release_tag']}">Download this edition from GitHub Releases</a></p></details>
          </div></section>'''
        page(slug, book['title'] + ' · Books', book['description'], body)
    page('', config['title'], 'Independent illustrated books exploring history, physics, and the possibilities between them.',
         '<section class="shelf-intro">' + md('index.md').replace('<h2>', '<h1>').replace('</h2>', '</h1>') + '</section>' + ''.join(features))
    print(f'Built {len(config["books"]) + 1} pages in {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    parser.add_argument('--local-release', type=Path)
    args = parser.parse_args()
    render_site(args.output, args.local_release)
