#!/usr/bin/env python3
"""mdbook preprocessor: render `.ipynb` chapters from their saved outputs.

Any chapter whose source path ends in `.ipynb` is replaced with markdown
built from the notebook's cells. Nothing is executed: markdown cells pass
through verbatim and code-cell outputs (plots, tables, text) are emitted
from what the notebook already has saved, so the build needs no scientific
python stack. Images are inlined as data URIs, so no asset files are written.

Input (code) cells are hidden by default -- the plotting boilerplate does
not aid understanding. Per-cell control follows the jupyter-book tag
convention via `metadata.tags`:

    remove-cell    drop the cell entirely (no input, no output)
    show-input     force the source to be shown in a fenced block
    remove-output  drop the outputs

Plots read on every mdbook theme when the notebook saves them transparent
with medium-lightness chrome (see the style cell in the notebook); a raster
cannot be recoloured by css the way inline svg can.
"""
import json
import re
import sys


def cell_tags(cell):
    return set(cell.get("metadata", {}).get("tags", []))


def joined(value):
    return "".join(value) if isinstance(value, list) else (value or "")


def fenced(code, lang=""):
    return "\n```%s\n%s\n```\n" % (lang, code.rstrip("\n"))


def render_output(out):
    kind = out.get("output_type")
    if kind == "stream":
        # stdout/stderr is noise (warnings, progress bars); drop it.
        return ""
    if kind == "error":
        return fenced("\n".join(out.get("traceback", [])))
    data = out.get("data", {})
    if "image/png" in data:
        png = joined(data["image/png"]).replace("\n", "")
        return '\n<img class="nb-output" src="data:image/png;base64,%s" alt="">\n' % png
    if "image/svg+xml" in data:
        return '\n<div class="nb-output">\n%s\n</div>\n' % joined(data["image/svg+xml"])
    if "text/html" in data:
        html = joined(data["text/html"])
        # Colab wraps tables in interactive widget markup (scripts, sort
        # buttons) that is inert in a static book; keep just the table.
        match = re.search(r"<table.*?</table>", html, re.S)
        if match:
            html = match.group(0)
        return '\n<div class="nb-output">\n%s\n</div>\n' % html
    if "text/plain" in data:
        return fenced(joined(data["text/plain"]))
    return ""


def render_notebook(nb):
    parts = []
    for cell in nb.get("cells", []):
        tags = cell_tags(cell)
        if "remove-cell" in tags:
            continue
        kind = cell.get("cell_type")
        if kind == "markdown":
            parts.append(joined(cell.get("source")))
        elif kind == "code":
            if "show-input" in tags:
                parts.append(fenced(joined(cell.get("source")), "python"))
            if "remove-output" not in tags:
                for out in cell.get("outputs", []):
                    piece = render_output(out)
                    if piece:
                        parts.append(piece)
    return "\n\n".join(p for p in parts if p.strip())


def is_notebook(chapter):
    for key in ("source_path", "path"):
        p = chapter.get(key)
        if isinstance(p, str) and p.endswith(".ipynb"):
            return True
    return False


def walk(items):
    for item in items or []:
        chapter = item.get("Chapter")
        if not chapter:
            continue
        if is_notebook(chapter) and chapter.get("content", "").strip():
            chapter["content"] = render_notebook(json.loads(chapter["content"]))
        walk(chapter.get("sub_items"))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "supports":
        sys.exit(0)
    _context, book = json.load(sys.stdin)
    # mdbook 0.5 renamed the top level key from `sections` to `items`.
    walk(book.get("items", book.get("sections")))
    json.dump(book, sys.stdout)


if __name__ == "__main__":
    main()
