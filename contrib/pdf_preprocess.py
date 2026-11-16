#!/usr/bin/env python3
"""Expose saved notebook HTML tables to mdbook's Pandoc renderer."""
import json
import re
import subprocess
import sys


TABLE = re.compile(r"<table\b[^>]*>.*?</table\s*>", re.I | re.S)


def convert_tables(content):
    def convert(match):
        result = subprocess.run(
            ["pandoc", "-f", "html", "-t", "gfm", "--wrap=none"],
            input=match.group(), text=True, stdout=subprocess.PIPE, check=True)
        # Blank lines end the surrounding Jupyter div's raw HTML block, so
        # mdbook parses the replacement as a Markdown table.
        return "\n\n" + result.stdout.strip() + "\n\n"

    return TABLE.sub(convert, content)


def walk(items):
    for item in items:
        chapter = item.get("Chapter") if isinstance(item, dict) else None
        if chapter is None:
            continue
        source = chapter.get("source_path") or chapter.get("path") or ""
        if source.lower().endswith(".ipynb"):
            chapter["content"] = convert_tables(chapter["content"])
        walk(chapter.get("sub_items", []))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "supports":
        sys.exit(0 if sys.argv[2:] == ["pandoc"] else 1)
    context, book = json.load(sys.stdin)
    if context["renderer"] == "pandoc":
        walk(book.get("items", book.get("sections", [])))
    json.dump(book, sys.stdout)


if __name__ == "__main__":
    main()
