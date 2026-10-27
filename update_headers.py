#!/usr/bin/env python3
"""Translate Spanish-site header labels and lower header text on all site pages.

Usage (from the website folder): python update_headers.py .
Safe to run again. Does not edit article text, images or navigation links.
"""
from pathlib import Path
import argparse
import re

LABELS = {
    'About': 'Sobre mí',
    'Research': 'Investigación',
    'Publications': 'Publicaciones',
    'Notes': 'Apuntes',
    'Contact': 'Contacto',
}

CSS = '''<style id="header-alignment-adjustment">
  /* Lower the text alongside the portrait, without moving the portrait. */
  .site-header .header-content { position: relative; top: 12px; }
</style>'''
CSS_PATTERN = re.compile(r'\s*<style\b[^>]*\bid\s*=\s*["\']header-alignment-adjustment["\'][^>]*>.*?</style>', re.I | re.S)
NAV_PATTERN = re.compile(r'(<nav\b[^>]*>)(.*?)(</nav\s*>)', re.I | re.S)
SUBTITLE_PATTERN = re.compile(r'(<p\b[^>]*\bclass\s*=\s*["\'][^"\']*\bsubtitle\b[^"\']*["\'][^>]*>)(.*?)(</p\s*>)', re.I | re.S)
ANCHOR_PATTERN = re.compile(r'(<a\b[^>]*>)(.*?)(</a\s*>)', re.I | re.S)


def modify(content, spanish):
    # CSS is added once, on both language versions, without modifying style.css.
    content = CSS_PATTERN.sub('', content)
    if not re.search(r'</head\s*>', content, re.I):
        raise ValueError('No closing </head> tag found')
    content = re.sub(r'</head\s*>', lambda m: '\n' + CSS + '\n' + m.group(), content, count=1, flags=re.I)
    if spanish:
        def translate_subtitle(m):
            body = m.group(2).replace('Theoretical Physicist', 'Físico Teórico').replace('General Relativity', 'Relatividad General')
            return m.group(1) + body + m.group(3)
        content = SUBTITLE_PATTERN.sub(translate_subtitle, content, count=1)

        def translate_navigation(m):
            def replace_label(a):
                # Only replace exact navigation labels, keeping href and attributes intact.
                visible = a.group(2)
                label = visible.strip()
                return a.group(1) + visible.replace(label, LABELS.get(label, label), 1) + a.group(3) if label else a.group()
            return m.group(1) + ANCHOR_PATTERN.sub(replace_label, m.group(2)) + m.group(3)
        content = NAV_PATTERN.sub(translate_navigation, content, count=1)
    return content


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('website', nargs='?', default='.', type=Path, help='Folder containing index.html')
    args = parser.parse_args()
    root = args.website.resolve()
    if not (root / 'index.html').is_file():
        parser.error(f'Could not find index.html in {root}; run from the website folder.')
    spanish_dir = root / 'esp'
    if not spanish_dir.is_dir():
        parser.error(f'Could not find esp folder in {root}; this script does not create translations.')
    total = 0
    for folder, spanish in ((root, False), (spanish_dir, True)):
        for page in sorted([*folder.glob('*.html'), *folder.glob('*.htm')]):
            original = page.read_text(encoding='utf-8')
            updated = modify(original, spanish)
            if updated != original:
                page.write_text(updated, encoding='utf-8')
                print('UPDATED:', page.relative_to(root))
                total += 1
            else:
                print('UNCHANGED:', page.relative_to(root))
    print(f'Finished. Updated {total} pages.')


if __name__ == '__main__':
    main()
