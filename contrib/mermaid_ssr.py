#!/usr/bin/env python3
"""mdbook preprocessor: render ```mermaid blocks to SVG with mmdc.

Expects the `mmdc` from nix/mermaid.nix, which comes wrapped with the
headless chromium it drives. If MERMAID_SVG_DIR is set, it renders nothing
itself: it takes each diagram from MERMAID_SVG_DIR/<sha256 of its
source>/<theme>.svg, as nix/mermaid.nix renders them, with PLACEHOLDER
standing for the svg id.
"""
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from html import unescape

# Fence length varies: preprocessors that re-serialize the markdown (mdbook-graphviz)
# emit four backticks, so the closing fence has to match the opening one.
FENCE = re.compile(
    r"^(?P<fence>`{3,})mermaid[^\n]*\n(?P<body>.*?)^(?P=fence)[ \t]*$",
    re.S | re.M,
)
PLACEHOLDER = "MERMAID_SSR_ID"
SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")


def render(source, theme, svg_id):
    rendered = os.environ.get("MERMAID_SVG_DIR")
    if rendered:
        digest = hashlib.sha256(source.encode()).hexdigest()
        try:
            with open(os.path.join(rendered, digest, theme + ".svg")) as f:
                return f.read().replace(PLACEHOLDER, svg_id)
        except FileNotFoundError:
            sys.stderr.write(
                "mermaid_ssr: %s has no diagram %s; nix/mermaid.nix did not "
                "find this block:\n%s" % (rendered, digest, source))
            sys.exit(1)
    with tempfile.TemporaryDirectory() as tmp:
        mmd = os.path.join(tmp, "in.mmd")
        svg = os.path.join(tmp, "out.svg")
        with open(mmd, "w") as f:
            f.write(source)
        args = ["mmdc", "-i", mmd, "-o", svg,
                "-b", "transparent", "-t", "default" if theme == "pdf" else theme,
                "-I", svg_id]
        if theme == "pdf":
            config = os.path.join(tmp, "config.json")
            with open(config, "w") as f:
                json.dump({"htmlLabels": False, "flowchart": {"htmlLabels": False}}, f)
            args += ["-c", config]
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            sys.stderr.write(result.stdout + result.stderr)
            sys.exit(1)
        with open(svg) as f:
            return f.read()


def block(source, index):
    """Both themes of one diagram; css picks which to show.

    The svg is emitted inside a div because `svg` is not a block-level tag
    in commonmark, so bare svg markup would be parsed as inline html and
    escaped. Each svg needs its own id: mermaid scopes the stylesheet it
    embeds by id, so two diagrams sharing one would style each other.
    """
    return "\n\n" + "\n".join(
        '<div class="mermaid mermaid-%s">\n%s\n</div>'
        % (name, render(source, theme, "mermaid-%d-%s" % (index, name)))
        for name, theme in (("light", "default"), ("dark", "dark"))
    ) + "\n\n"


def image(source, index):
    """One diagram with native SVG labels, as an image for the pandoc renderer.

    Inline svg is html, which pandoc drops from a LaTeX document.
    """
    svg = render(source, "pdf", "mermaid-%d" % index)
    root = ET.fromstring(svg)
    # librsvg otherwise collapses leading spaces in adjacent text spans.
    root.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    for label in root.iter("{%s}text" % SVG):
        for node in label.iter():
            if node.text:
                node.text = unescape(node.text)
            if node.tail:
                node.tail = unescape(node.tail)
    svg = ET.tostring(root, encoding="unicode")
    return "\n\n![](data:image/svg+xml;base64,%s)\n\n" % base64.b64encode(
        svg.encode()).decode()


def walk(items, counter, emit):
    for item in items:
        chapter = item.get("Chapter")
        if not chapter:
            continue

        def substitute(match):
            counter[0] += 1
            return emit(match.group("body"), counter[0])

        chapter["content"] = FENCE.sub(substitute, chapter["content"])
        walk(chapter["sub_items"], counter, emit)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "supports":
        sys.exit(0)
    context, book = json.load(sys.stdin)
    emit = image if context["renderer"] == "pandoc" else block
    # mdbook 0.5 renamed the top level key from `sections` to `items`.
    walk(book.get("items", book.get("sections")), [0], emit)
    json.dump(book, sys.stdout)


if __name__ == "__main__":
    main()
