#!/usr/bin/env python3
"""mdbook preprocessor: render ```mermaid blocks to inline SVG with mmdc.

Expects the `mmdc` from nix/mermaid.nix, which comes wrapped with the
headless chromium it drives.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

# Fence length varies: preprocessors that re-serialize the markdown (mdbook-graphviz)
# emit four backticks, so the closing fence has to match the opening one.
FENCE = re.compile(
    r"^(?P<fence>`{3,})mermaid[^\n]*\n(?P<body>.*?)^(?P=fence)[ \t]*$",
    re.S | re.M,
)


def render(source):
    with tempfile.TemporaryDirectory() as tmp:
        mmd = os.path.join(tmp, "in.mmd")
        svg = os.path.join(tmp, "out.svg")
        with open(mmd, "w") as f:
            f.write(source)
        result = subprocess.run(
            ["mmdc", "-i", mmd, "-o", svg, "-b", "transparent"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            sys.stderr.write(result.stdout + result.stderr)
            sys.exit(1)
        with open(svg) as f:
            # `svg` is not a block-level tag in commonmark, so bare svg
            # markup would be parsed as inline html and escaped. The div
            # wrapper (blank-line delimited) makes it a raw html block.
            return "\n\n<div class=\"mermaid\">\n%s\n</div>\n\n" % f.read()


def walk(items):
    for item in items:
        chapter = item.get("Chapter")
        if not chapter:
            continue
        chapter["content"] = FENCE.sub(
            lambda m: render(m.group("body")), chapter["content"]
        )
        walk(chapter["sub_items"])


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "supports":
        sys.exit(0)
    _context, book = json.load(sys.stdin)
    # mdbook 0.5 renamed the top level key from `sections` to `items`.
    walk(book.get("items", book.get("sections")))
    json.dump(book, sys.stdout)


if __name__ == "__main__":
    main()
