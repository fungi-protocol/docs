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
import subprocess
import sys
import tempfile
from pathlib import Path

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
    heading level, 0 if it is not a heading.

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
            yield c[0], full_stop(text)
        elif kind in ("Para", "Plain") and (text := words(c)):
            yield 0, full_stop(text) if stop else text
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
