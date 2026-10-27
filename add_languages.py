#!/usr/bin/env python3
"""Add EN / ESP page switches to an existing static GitHub Pages website.

Usage: python add_languages.py /path/to/website
Run ONCE initially; if run again, existing Spanish pages are never overwritten.
"""
from pathlib import Path
import argparse
import html
import re
import shutil
from urllib.parse import urlsplit

STYLE = '''<style id="language-switch-style">
  .language-switch { display: inline-flex; align-items: center; gap: .25rem; margin-left: .85rem; white-space: nowrap; font-size: .85rem; }
  .language-switch a { color: inherit; text-decoration: none; opacity: .65; padding: .18rem .3rem; border-radius: .2rem; }
  .language-switch a[aria-current="true"] { opacity: 1; font-weight: 700; text-decoration: underline; text-underline-offset: .2rem; }
  .language-switch a:hover { opacity: 1; }
  @media (max-width: 650px) { .language-switch { margin-left: .35rem; } }
</style>'''

# URLs inside Spanish copies that should point one level up to the original root.
# Links to other .html pages are deliberately not changed: they work inside /esp/.
def adjust_reference(url):
    if not url or url.startswith(('#', '/', '//', 'mailto:', 'tel:', 'data:', 'javascript:')):
        return url
    p = urlsplit(html.unescape(url))
    if p.scheme or not p.path:
        return url
    if p.path.lower().endswith(('.html', '.htm')):
        return url
    if p.path.startswith('../'):
        return url
    return '../' + url


def for_spanish(text):
    # Change asset links; relative HTML navigation stays in /esp/.
    def rewrite(m):
        before, quote, url = m.groups()
        return before + quote + html.escape(adjust_reference(url), quote=True) + quote
    text = re.sub(r'((?:\bhref|\bsrc|\bposter|\baction)\s*=\s*)(["\'])(.*?)\2', rewrite, text, flags=re.I|re.S)
    # Fix srcset assets, if any.
    def rewrite_srcset(m):
        prefix, quote, value = m.groups()
        parts = []
        for item in value.split(','):
            chunks = item.strip().split(None, 1)
            if chunks:
                parts.append(adjust_reference(chunks[0]) + (' ' + chunks[1] if len(chunks) > 1 else ''))
        return prefix + quote + ', '.join(parts) + quote
    text = re.sub(r'(\bsrcset\s*=\s*)(["\'])(.*?)\2', rewrite_srcset, text, flags=re.I|re.S)
    text = re.sub(r'<html\b([^>]*?)\blang\s*=\s*["\'][^"\']+["\']', lambda m: '<html' + re.sub(r'\blang\s*=\s*["\'][^"\']+["\']', 'lang="es"', m.group(1)), text, count=1, flags=re.I)
    if not re.search(r'<html\b[^>]*\blang=', text, re.I):
        text = re.sub(r'<html\b', '<html lang="es"', text, count=1, flags=re.I)
    return text


def add_switch(text, filename, spanish):
    # Idempotent: replace the switch if present, preserving all other HTML.
    text = re.sub(r'\s*<span class="language-switch".*?</span>', '', text, flags=re.S|re.I)
    text = re.sub(r'\s*<style id="language-switch-style">.*?</style>', '', text, flags=re.S|re.I)
    en = '../' + filename if spanish else filename
    es = filename if spanish else 'esp/' + filename
    controls = ('<span class="language-switch" role="group" aria-label="Language / Idioma">'
                f'<a href="{en}" lang="en" hreflang="en"' + (' aria-current="true"' if not spanish else '') + '>EN</a>'
                '<span aria-hidden="true">/</span>'
                f'<a href="{es}" lang="es" hreflang="es"' + (' aria-current="true"' if spanish else '') + '>ESP</a>'
                '</span>')
    if re.search(r'</nav\s*>', text, re.I):
        text = re.sub(r'</nav\s*>', lambda m: controls + '\n      ' + m.group(0), text, count=1, flags=re.I)
    elif re.search(r'</header\s*>', text, re.I):
        text = re.sub(r'</header\s*>', lambda m: controls + '\n    ' + m.group(0), text, count=1, flags=re.I)
    else:
        raise ValueError(f'{filename}: no <nav> or <header> found')
    text = re.sub(r'</head\s*>', STYLE + '\n</head>', text, count=1, flags=re.I)
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('website', type=Path, help='Folder containing index.html and style.css')
    args = parser.parse_args()
    root = args.website.resolve()
    if not (root / 'index.html').is_file():
        parser.error(f'No index.html found in {root}')
    spanish_dir = root / 'esp'
    spanish_dir.mkdir(exist_ok=True)
    pages = sorted([*root.glob('*.html'), *root.glob('*.htm')])
    for page in pages:
        if page.name.lower() == '404.html':
            continue
        original = page.read_text(encoding='utf-8')
        # Create the Spanish copy only if it does not exist; never erase translations.
        translated = spanish_dir / page.name
        if not translated.exists():
            spanish = add_switch(for_spanish(original), page.name, True)
            translated.write_text(spanish, encoding='utf-8')
            note = 'created Spanish copy'
        else:
            spanish = translated.read_text(encoding='utf-8')
            translated.write_text(add_switch(spanish, page.name, True), encoding='utf-8')
            note = 'preserved existing Spanish copy'
        page.write_text(add_switch(original, page.name, False), encoding='utf-8')
        print(f'{page.name}: EN switch added; {note}')
    print(f'Finished. Spanish pages: {spanish_dir}')


if __name__ == '__main__':
    main()
