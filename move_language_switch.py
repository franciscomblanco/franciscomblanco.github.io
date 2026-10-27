#!/usr/bin/env python3
"""Move the existing EN / ESP selector beneath navigation on all site pages.

Run from your downloaded repository folder:
    python move_language_switch.py .

Only relocates the language selector and updates its CSS. Existing text, links,
Spanish translations and images are preserved. Safe to run more than once.
"""
from pathlib import Path
import argparse
import re

STYLE = '''<style id="language-switch-style">
  .language-switch-row { display: flex; justify-content: flex-end; margin: .45rem 0 .7rem; }
  .language-switch { display: inline-flex; align-items: center; gap: .25rem; font-size: .85rem; white-space: nowrap; }
  .language-switch a { color: inherit; text-decoration: none; opacity: .65; padding: .18rem .3rem; border-radius: .2rem; }
  .language-switch a[aria-current="true"] { opacity: 1; font-weight: 700; text-decoration: underline; text-underline-offset: .2rem; }
  .language-switch a:hover { opacity: 1; }
</style>'''

SWITCH_PATTERN = re.compile(r'<span\s+class=["\']language-switch["\'][^>]*>.*?</span>.*?</span>', re.I | re.S)
ROW_PATTERN = re.compile(r'\s*<div\b[^>]*\bclass\s*=\s*["\']language-switch-row["\'][^>]*>.*?</div>', re.I | re.S)
STYLE_PATTERN = re.compile(r'<style\b[^>]*\bid\s*=\s*["\']language-switch-style["\'][^>]*>.*?</style>', re.I | re.S)

def update_page(text, filename):
    # Capture one switch, whether already under the nav or still inside it.
    found = SWITCH_PATTERN.search(text)
    if not found:
        print(f'  SKIPPED {filename}: existing language switch not found')
        return None
    switch = found.group(0).strip()
    text = ROW_PATTERN.sub('', text)
    # The original switch lives inside <nav>; remove it now, or if already
    # moved strip it out from its previous location.
    text = SWITCH_PATTERN.sub('', text)
    text = STYLE_PATTERN.sub('', text)
    nav = re.search(r'</nav\s*>', text, flags=re.I)
    if not nav:
        print(f'  SKIPPED {filename}: navigation element not found')
        return None
    row = '\n      <div class="language-switch-row">' + switch + '</div>'
    text = text[:nav.end()] + row + text[nav.end():]
    text, count = re.subn(r'</head\s*>', lambda m: STYLE + m.group(0), text, count=1, flags=re.I)
    if not count:
        print(f'  SKIPPED {filename}: head closing tag not found')
        return None
    return text

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('website', nargs='?', default='.', type=Path, help='Website folder (default: current folder)')
    args = parser.parse_args()
    root = args.website.resolve()
    if not (root / 'index.html').is_file():
        parser.error(f'No index.html found in {root}. Run this inside your website folder.')
    count = 0
    for folder in (root, root / 'esp'):
        if not folder.is_dir():
            print(f'SKIPPED {folder}: folder not found')
            continue
        for page in sorted([*folder.glob('*.html'), *folder.glob('*.htm')]):
            original = page.read_text(encoding='utf-8')
            modified = update_page(original, str(page.relative_to(root)))
            if modified is not None and modified != original:
                page.write_text(modified, encoding='utf-8')
                print(f'  UPDATED {page.relative_to(root)}')
                count += 1
    print(f'Done. Updated {count} pages. No page text was translated or replaced.')

if __name__ == '__main__':
    main()
