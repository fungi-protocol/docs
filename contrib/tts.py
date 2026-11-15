#!/usr/bin/env python3
"""Narration of the book's chapters.

A chapter's readable text is read aloud as one audio file named by the hash
of that text, so audio rendered from other text is never mistaken for it.
"""
import hashlib
import re

FRONTMATTER = re.compile(r"\A---\n.*?\n---[ \t]*(?:\n|\Z)", re.S)
FENCE = re.compile(r"^(`{3,}|~{3,})")
MATH_BLOCK = re.compile(r"\$\$")
BLANK = re.compile("")
# A header row, a delimiter row, then rows up to a blank line. Outer pipes
# are optional in markdown tables.
TABLE = re.compile(
    r"^[^\n]*\|[^\n]*\n"
    r"[ \t]*\|?[ \t]*:?-{3,}:?[ \t]*(?:\|[ \t]*:?-{3,}:?[ \t]*)*\|?[ \t]*\n"
    r"(?:[^\n]*\|[^\n]*(?:\n|\Z))*",
    re.M,
)
LIST_ITEM = re.compile(r"^(?:[-*+]|\d+[.)])\s+")
HEADING = re.compile(r"^#{1,6}\s+")
IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
REFERENCE_LINK = re.compile(r"\[([^\]]+)\]\[[^\]]*\]")
FOOTNOTE_MARKER = re.compile(r"\[\^[^\]]+\]")
INLINE_CODE = re.compile(r"`+([^`]+)`+")
INLINE_MATH = re.compile(r"\$[^$\n]+\$")
TAG = re.compile(r"<[^>]+>")
EMPHASIS = re.compile(r"(?<!\w)_(.+?)_(?!\w)")

def name(text):
    """Return the audio file name of a text, without extension."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def text(markdown):
    """Return the chapter's readable text, one unit per line.

    Kokoro reads each line as its own segment and cuts longer lines itself.
    """
    return "\n".join(units(markdown))


def units(markdown):
    """Yield headings, list items and paragraphs as plain text."""
    markdown = FRONTMATTER.sub("", markdown, count=1)
    markdown = TABLE.sub("\n", markdown)
    paragraph = []
    # The pattern of the line that closes the fenced code, math or HTML block
    # being skipped.
    closing = None

    def flush():
        text = clean(" ".join(paragraph))
        paragraph.clear()
        return [text] if text else []

    for line in markdown.splitlines():
        stripped = line.strip()
        if closing:
            if closing.fullmatch(stripped):
                closing = None
            continue
        opening = FENCE.match(stripped)
        if opening:
            yield from flush()
            fence = opening.group(1)
            closing = re.compile(re.escape(fence[0]) + "{%d,}" % len(fence))
        elif stripped == "$$":
            yield from flush()
            closing = MATH_BLOCK
        elif stripped.startswith("<"):
            yield from flush()
            closing = BLANK
        elif not stripped or is_footnote_definition(stripped):
            yield from flush()
        elif HEADING.match(stripped) or LIST_ITEM.match(stripped):
            yield from flush()
            text = clean(HEADING.sub("", LIST_ITEM.sub("", stripped)))
            if text:
                yield text if text[-1] in ".!?:" else text + "."
        else:
            paragraph.append(stripped.lstrip("> "))
    yield from flush()


def is_footnote_definition(line):
    return line.startswith("[^") and "]:" in line


def clean(text):
    text = IMAGE.sub("", text)
    text = LINK.sub(r"\1", text)
    text = REFERENCE_LINK.sub(r"\1", text)
    text = FOOTNOTE_MARKER.sub("", text)
    text = INLINE_MATH.sub("", text)
    text = INLINE_CODE.sub(r"\1", text)
    text = TAG.sub("", text)
    text = EMPHASIS.sub(r"\1", text).replace("*", "")
    return " ".join(text.split())
