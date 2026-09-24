#!/usr/bin/env python3
"""Point chart images at the book's copy; the source keeps repository paths for GitHub."""
import json
import sys


def walk(items):
    for item in items:
        chapter = item.get('Chapter') if isinstance(item, dict) else None
        if chapter:
            chapter['content'] = chapter['content'].replace('src="src/figures/', 'src="figures/')
            walk(chapter['sub_items'])


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'supports':
        sys.exit(0 if len(sys.argv) > 2 and sys.argv[2] == 'html' else 1)
    context, book = json.load(sys.stdin)
    walk(book.get('items', book.get('sections', [])))
    json.dump(book, sys.stdout)


if __name__ == '__main__':
    main()
