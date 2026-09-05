"""Check the built artifact, local links, basic semantics and publication scope."""
import json
from html.parser import HTMLParser
from pathlib import Path
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids = [], set()
        self.h1 = self.main = self.title = self.images = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            assert attrs['id'] not in self.ids, 'Duplicate element ID'
            self.ids.add(attrs['id'])
        for name in ('href', 'src'):
            if name in attrs:
                self.links.append(attrs[name])
        if tag == 'h1': self.h1 += 1
        if tag == 'main': self.main += 1
        if tag == 'title': self.title += 1
        if tag == 'img':
            self.images += 1
            assert attrs.get('alt'), 'Image missing alternative text'
            assert attrs.get('width') and attrs.get('height'), 'Unreserved image dimensions'


def check(output):
    output = Path(output).resolve()
    config = json.loads((ROOT / 'site.json').read_text())
    base = config['base_path']
    expected = {'index.html', 'assets/style.css', '.nojekyll'}
    for book in config['books']:
        expected.add(book['slug'] + '/index.html')
        expected.update('assets/' + book['slug'] + '/' + name for name in book['images'].values())
    actual = {str(p.relative_to(output)) for p in output.rglob('*') if p.is_file()}
    assert actual == expected, f'Publication allowlist mismatch: {actual ^ expected}'
    assert not any(p.is_symlink() for p in output.rglob('*')), 'Symlink in artifact'
    count = 0
    for path in output.rglob('*.html'):
        source = path.read_text()
        parsed = Page()
        parsed.feed(source)
        assert (parsed.h1, parsed.main, parsed.title) == (1, 1, 1), path
        assert '<html lang="en">' in source
        assert 'PENDING' not in source and '/Users/' not in source
        for link in parsed.links:
            parts = urlsplit(link)
            if parts.scheme:
                assert parts.scheme == 'https', link
                continue
            if not parts.path:
                assert not parts.fragment or parts.fragment in parsed.ids, link
                continue
            assert parts.path.startswith(base + '/'), link
            target = output / unquote(parts.path[len(base) + 1:])
            assert target.resolve().is_relative_to(output), link
            if target.is_dir(): target = target / 'index.html'
            assert target.is_file(), f'Broken link in {path}: {link}'
            count += 1
    print(f'PASS: {len(actual)} allowlisted files; {count} local references; titles, headings, alt text, and landmarks.')


if __name__ == '__main__':
    check(sys.argv[1])
