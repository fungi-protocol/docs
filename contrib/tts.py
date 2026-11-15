#!/usr/bin/env python3
"""Narration of the book's chapters.

A chapter's readable text is read aloud as one audio file named by the hash
of that text, so audio rendered from other text is never mistaken for it.

Each section, cut before each of the chapter's headings, is read on its
own, so an edit re-reads only its section. nix/tts.nix runs

    python3 tts.py sections MARKDOWN

to print the sections as JSON, reads each section to a FLAC file with
contrib/speak.py, then runs

    python3 tts.py join MARKDOWN OUT FLAC...

to join them into OUT/<name>.mp3, with the start of each section in
OUT/<name>.json.
"""
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

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
HEADING = re.compile(r"^(#{1,6})\s+")
IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
REFERENCE_LINK = re.compile(r"\[([^\]]+)\]\[[^\]]*\]")
FOOTNOTE_MARKER = re.compile(r"\[\^[^\]]+\]")
INLINE_CODE = re.compile(r"`+([^`]+)`+")
INLINE_MATH = re.compile(r"\$[^$\n]+\$")
TAG = re.compile(r"<[^>]+>")
EMPHASIS = re.compile(r"(?<!\w)_(.+?)_(?!\w)")

# Kokoro's output rate, as contrib/speak.py writes it.
SAMPLE_RATE = 24000

def name(text):
    """Return the audio file name of a text, without extension."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def text(markdown):
    """Return the chapter's readable text, one unit per line.

    Kokoro reads each line as its own segment and cuts longer lines itself.
    """
    return "\n".join(unit for _, unit in units(markdown))


def sections(markdown):
    """Return the chapter's text cut before each heading, as title, heading
    level (0 before the first heading) and text.

    Joined by newlines, the sections' texts are the chapter's text.
    """
    cut = []
    for level, unit in units(markdown):
        if level or not cut:
            cut.append({"title": unit.rstrip(".") if level else "", "level": level, "text": unit})
        else:
            cut[-1]["text"] += "\n" + unit
    return cut


def units(markdown):
    """Yield headings, list items and paragraphs as plain text, each with its
    heading level, 0 if it is not a heading."""
    markdown = FRONTMATTER.sub("", markdown, count=1)
    markdown = TABLE.sub("\n", markdown)
    paragraph = []
    # The pattern of the line that closes the fenced code, math or HTML block
    # being skipped.
    closing = None

    def flush():
        text = clean(" ".join(paragraph))
        paragraph.clear()
        return [(0, text)] if text else []

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
        elif (heading := HEADING.match(stripped)) or LIST_ITEM.match(stripped):
            yield from flush()
            text = clean(HEADING.sub("", LIST_ITEM.sub("", stripped)))
            if text:
                level = len(heading.group(1)) if heading else 0
                yield level, text if text[-1] in ".!?:" else text + "."
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


def starts(sections, durations):
    """Return each section's title, level and start in seconds."""
    marks, at = [], 0.0
    for section, duration in zip(sections, durations):
        marks.append({"title": section["title"], "level": section["level"], "start": round(at, 2)})
        at += duration
    return marks


def join(markdown_path, out_dir, parts):
    """Join the sections' FLAC files into OUT_DIR/<name>.mp3 and .json."""
    import numpy
    import soundfile

    markdown = Path(markdown_path).read_text()
    cut = sections(markdown)
    assert len(cut) == len(parts), "one FLAC file per section"
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not parts:
        return
    audio = [soundfile.read(p)[0] for p in parts]
    stem = out_dir / name(text(markdown))
    stem.with_suffix(".json").write_text(
        json.dumps(starts(cut, [len(a) / SAMPLE_RATE for a in audio])))
    with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
        soundfile.write(wav.name, numpy.concatenate(audio), SAMPLE_RATE)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-i", wav.name,
                        "-ac", "1", "-b:a", "64k", str(stem.with_suffix(".mp3"))], check=True)


def main():
    command, args = sys.argv[1] if len(sys.argv) > 1 else None, sys.argv[2:]
    if command == "sections" and len(args) == 1:
        json.dump(sections(Path(args[0]).read_text()), sys.stdout)
    elif command == "join" and len(args) >= 2:
        join(args[0], args[1], args[2:])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
