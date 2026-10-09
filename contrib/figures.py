#!/usr/bin/env python3
"""Embed chart pictures in the book; keep repository image paths on GitHub."""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

PICTURE = re.compile(r'<picture>\s*<source\b[^>]*>\s*<img\b[^>]*>\s*</picture>', re.S)


class Picture(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.images = {}
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'img':
            self.images['light'] = attrs.get('src', '')
        elif tag == 'source' and attrs.get('media') == '(prefers-color-scheme: dark)':
            self.images['dark'] = attrs.get('srcset', '')


def embed(match, root):
    images = Picture(match.group()).images
    # Only handle the paired, checked-in chart assets, not unrelated pictures.
    if set(images) != {'light', 'dark'} or not all(
        re.fullmatch(r'src/figures/figure-\d+-' + theme + r'\.svg', path)
        for theme, path in images.items()
    ):
        return match.group()
    fragments = []
    for theme in ('light', 'dark'):
        svg = (root / images[theme]).read_text()
        scope = 'chart-' + Path(images[theme]).stem
        # Inline SVG styles belong to the whole document. Scope the asset's
        # class selectors so its palette cannot affect other figures/diagrams.
        svg = re.sub(
            r'<style>(.*?)</style>',
            lambda style: '<style>' + re.sub(
                r'(\.[a-zA-Z_][\w-]*)\s*\{',
                lambda selector: '.' + scope + ' ' + selector.group(1) + '{',
                style.group(1),
            ) + '</style>',
            svg,
            flags=re.S,
        )
        # A blank line ends a CommonMark raw HTML block. Keep the SVG in
        # one block so its text and shapes are not parsed as Markdown.
        svg = '\n'.join(line for line in svg.splitlines() if line.strip())
        fragments.append(f'<div class="chart-{theme} {scope}">\n{svg}\n</div>')
    return '\n'.join(fragments)


def walk(items, root):
    for item in items:
        chapter = item.get('Chapter')
        if chapter:
            chapter['content'] = PICTURE.sub(lambda match: embed(match, root), chapter['content'])
            walk(chapter['sub_items'], root)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'supports':
        sys.exit(0 if len(sys.argv) > 2 and sys.argv[2] == 'html' else 1)
    context, book = json.load(sys.stdin)
    walk(book.get('items', book.get('sections', [])), Path(context['root']))
    json.dump(book, sys.stdout)


if __name__ == '__main__':
    main()
