#!/usr/bin/env python3
"""Narration of the book's chapters.

A chapter's readable text is read aloud as one audio file named by the hash
of that text, so audio rendered from other text is never mistaken for it.
"""
import hashlib
import json
import subprocess


def name(text):
    """Return the audio file name of a text, without extension."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def text(markdown):
    """Return the chapter's readable text, one unit per line.

    Kokoro reads each line as its own segment and cuts longer lines itself.
    """
    return "\n".join(units(markdown))


def units(markdown):
    """Yield headings, list items and paragraphs as plain text.

    pandoc parses the chapter as GitHub Flavored Markdown, which has the
    extensions the book uses: tables, footnotes, alerts and dollar math.
    Headings, list items and alert titles end in a full stop, so that Kokoro
    pauses after them.
    """
    doc = subprocess.run(["pandoc", "-f", "gfm", "-t", "json"], input=markdown,
                         capture_output=True, text=True, check=True).stdout
    return blocks(json.loads(doc)["blocks"], stop=False)


def blocks(content, stop):
    """Yield the units of blocks, skipping tables, code, math and raw HTML.

    A paragraph ends in a full stop when `stop` is set, as inside a list item
    or an alert's title.
    """
    for block in content:
        kind, c = block["t"], block.get("c")
        if kind == "Header" and (text := words(c[2])):
            yield full_stop(text)
        elif kind in ("Para", "Plain") and (text := words(c)):
            yield full_stop(text) if stop else text
        elif kind in ("BulletList", "OrderedList"):
            for item in c if kind == "BulletList" else c[1]:
                yield from blocks(item, stop=True)
        elif kind == "BlockQuote":
            yield from blocks(c, stop)
        elif kind == "Div":
            yield from blocks(c[1], stop or "title" in c[0][1])


def full_stop(text):
    return text if text[-1] in ".!?:" else text + "."


def words(inlines):
    """Return the text and inline code of inlines, without images, math,
    footnotes, raw HTML or a link whose text is its URL."""
    out = []
    for inline in inlines:
        kind, c = inline["t"], inline.get("c")
        if kind == "Str":
            out.append(c)
        elif kind in ("Space", "SoftBreak", "LineBreak"):
            out.append(" ")
        elif kind == "Code":
            out.append(c[1])
        elif kind in ("Emph", "Strong", "Strikeout"):
            out.append(words(c))
        elif kind == "Span":
            out.append(words(c[1]))
        elif kind == "Link" and words(c[1]) != c[2][0]:
            out.append(words(c[1]))
    return " ".join("".join(out).split())
