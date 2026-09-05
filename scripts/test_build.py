"""Small offline regressions for publication boundaries and a second book."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

import build
import check


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ('content', 'templates', 'assets'):
            shutil.copytree(build.ROOT / name, self.root / name)
        self.config = json.loads((build.ROOT / 'site.json').read_text())
        self.book = self.config['books'][0]
        self.release = self.root / 'release'
        self.release.mkdir()
        # Synthetic bytes test packaging/integrity, not PDF or JPEG rendering.
        pdf = b'%PDF-1.4\nOffline test fixture\n'
        (self.release / self.book['pdf']).write_bytes(pdf)
        self.book['pdf_sha256'] = hashlib.sha256(pdf).hexdigest()
        self.book['pdf_bytes'] = len(pdf)
        self.archive = self.release / self.book['media_archive']
        with zipfile.ZipFile(self.archive, 'w') as z:
            for name in self.book['images'].values():
                z.writestr(name, b'\xff\xd8\xff offline test fixture')
        self.save()
        self.addCleanup(patch.stopall)
        patch.object(build, 'ROOT', self.root).start()
        patch.object(check, 'ROOT', self.root).start()

    def save(self):
        self.book['media_sha256'] = build.digest(self.archive)
        (self.root / 'site.json').write_text(json.dumps(self.config))

    def render(self):
        out = self.root / 'out'
        build.render_site(out, self.release)
        return out

    def test_build_and_allowlist(self):
        check.check(self.render())

    def test_second_book_gets_own_page_and_credits(self):
        second = copy.deepcopy(self.book)
        second.update(slug='another-book', title='A second book', category='A different subject')
        self.config['books'].append(second)
        (self.root / 'content/another-book.md').write_text('## A new subject\n\nDifferent content.')
        (self.root / 'content/another-book-credits.md').write_text('## Credits\n\nDifferent collaborators.')
        self.save()
        out = self.render()
        check.check(out)
        page = (out / 'another-book/index.html').read_text()
        self.assertIn('Different collaborators.', page)
        self.assertNotIn('Writing:</strong> Astra', page)

    def test_unapproved_pdf_is_rejected(self):
        (self.release / self.book['pdf']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'approved edition'):
            self.render()

    def test_extra_or_traversal_zip_entry_is_rejected(self):
        with zipfile.ZipFile(self.archive, 'a') as z:
            z.writestr('../private.txt', 'unexpected')
        self.save()
        with self.assertRaisesRegex(ValueError, 'archive entries'):
            self.render()

    def test_duplicate_zip_entry_is_rejected(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(self.archive, 'a') as z:
                z.writestr(self.book['images']['cover'], b'duplicate')
        self.save()
        with self.assertRaisesRegex(ValueError, 'archive entries'):
            self.render()

    def test_output_is_not_overwritten(self):
        self.render()
        with self.assertRaises(FileExistsError):
            self.render()

    def test_unexpected_public_file_is_rejected(self):
        out = self.render()
        (out / 'private-notes.txt').write_text('not for publication')
        with self.assertRaisesRegex(AssertionError, 'allowlist'):
            check.check(out)


if __name__ == '__main__':
    unittest.main()
