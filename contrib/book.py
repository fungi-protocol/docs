#!/usr/bin/env python3
"""Assemble the mdbook source from README.md and the docs/ bundle.

docs/index.md, the bundle's OKF index, states the chapter order: its
headings become the parts of SUMMARY.md and its entries the chapters,
without their descriptions, so an entry must name a chapter, by a path
relative to docs/, and every chapter must have an entry. An entry
indented two spaces more than the entry above it is a sub-chapter of
that entry. The README is the introduction, and the index, with its
descriptions, is the contents page. Frontmatter is checked and then
dropped, as mdbook would render it as text. The bundle's other files are
copied as they are.

    python3 book.py ROOT
"""
import argparse
import posixpath
import re
import shutil
from datetime import datetime
from pathlib import Path

import yaml

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---[ \t]*(?:\n+|\Z)", re.DOTALL)
ENTRY = re.compile(r"( *)\* \[([^\]]+)\]\(([^)\s]+)\)(?: - .*)?")
DOCS = "docs"
# As set in book.toml.
SRC = "src"
CONTENTS = "contents.md"
GENERATED = ("README.md", "SUMMARY.md", CONTENTS)
STATUSES = ("draft", "stable", "deprecated")
RESERVED = ("index.md", "log.md")
# A sub-chapter's entry is indented this much more than its chapter's.
INDENT = "  "


def strip_frontmatter(text):
    return FRONTMATTER.sub("", text, count=1)


def frontmatter(text):
    m = FRONTMATTER.match(text)
    fields = yaml.safe_load(m.group(1)) if m else None
    return fields if isinstance(fields, dict) else {}


def check(name, text):
    """A page must have a type and a status, and a draft the instant from
    which it is stale, where OKF makes both optional. Whether that instant
    has passed is not checked, so that a build does not depend on when it
    runs."""
    try:
        fields = frontmatter(text)
    except (yaml.YAMLError, ValueError) as e:
        raise ValueError(f"{name}: {e}") from e
    if not fields.get("type"):
        raise ValueError(f"{name}: no type")
    status = fields.get("status")
    if status not in STATUSES:
        raise ValueError(f"{name}: status {status!r} is not one of {STATUSES}")
    if status == "draft":
        stale_after = fields.get("stale_after")
        if isinstance(stale_after, str):
            try:
                stale_after = datetime.fromisoformat(stale_after)
            except ValueError:
                stale_after = None
        if not isinstance(stale_after, datetime) or stale_after.tzinfo is None:
            raise ValueError(
                f"{name}: a draft needs stale_after, an ISO 8601 instant with an offset"
            )


def summary(index, pages):
    """SUMMARY.md from an OKF index: `# Part` headings and
    `* [Title](file.md) - description` entries, naming each of `pages`,
    the paths in docs/ of the pages the book is given. Indented entries
    are nested under the entry above them."""
    out = ["# Summary", "", "[Introduction](README.md)", f"[Contents]({CONTENTS})"]
    listed = set()
    # The depth of the entry above, or -1 at the start of a part, where
    # there is none to nest under.
    above = -1
    for line in strip_frontmatter(index).splitlines():
        if line.startswith("# "):
            out += ["", line, ""]
            above = -1
        elif m := ENTRY.fullmatch(line):
            depth, odd = divmod(len(m.group(1)), len(INDENT))
            if odd:
                raise ValueError(f"index entry has odd indentation: {line!r}")
            if depth > above + 1:
                if above < 0:
                    raise ValueError(f"index entry has no entry above: {line!r}")
                raise ValueError(
                    f"index entry is nested more than one level deeper: {line!r}"
                )
            above = depth
            chapter = posixpath.normpath(m.group(3))
            if chapter not in pages:
                raise ValueError(f"index entry is not a chapter: {line!r}")
            if chapter in listed:
                raise ValueError(f"index entry repeats a chapter: {line!r}")
            listed.add(chapter)
            out.append(f"{INDENT * depth}- [{m.group(2)}]({chapter})")
        elif line.strip():
            raise ValueError(f"unexpected line in index: {line!r}")
    if unlisted := sorted(set(pages) - listed):
        raise ValueError(f"not in the index: {', '.join(unlisted)}")
    return "\n".join(out) + "\n"


def contents(index):
    """The contents page: the index with its descriptions, its parts one
    heading level down."""
    body = re.sub(r"^# ", "## ", strip_frontmatter(index), flags=re.MULTILINE)
    return "# Contents\n\n" + body


def assemble(root):
    docs, out = root / DOCS, root / SRC
    index = (docs / "index.md").read_text()
    pages = {}
    for page in sorted(docs.rglob("*.md")):
        if page.name not in RESERVED:
            name = page.relative_to(docs).as_posix()
            pages[name] = page.read_text()
            check(name, pages[name])
    # docs/README.md directs readers of the repository to the book; as a
    # chapter it would overwrite the introduction.
    pages.pop("README.md", None)
    # Compared without case, as a case-insensitive filesystem would let a
    # chapter named like a generated page replace it.
    reserved = {name.casefold() for name in GENERATED}
    if clash := sorted(name for name in pages if name.casefold() in reserved):
        raise ValueError(f"generated by book.py: {', '.join(clash)}")
    generated = {
        "README.md": re.sub(r"(?<=\]\()docs/", "", (root / "README.md").read_text()),
        "SUMMARY.md": summary(index, pages),
        CONTENTS: contents(index),
    }
    # mdbook serve watches src/ itself and skips what the root .gitignore
    # matches, so src/ is emptied rather than replaced, and ignores itself
    # before anything else is written to it.
    out.mkdir(exist_ok=True)
    (out / ".gitignore").write_text("*\n")
    for child in out.iterdir():
        if child.name == ".gitignore":
            continue
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()
    shutil.copytree(
        docs,
        out,
        ignore=shutil.ignore_patterns("*.md", ".gitignore"),
        dirs_exist_ok=True,
    )
    for name, text in generated.items():
        (out / name).write_text(text)
    for name, text in pages.items():
        (out / name).parent.mkdir(parents=True, exist_ok=True)
        (out / name).write_text(strip_frontmatter(text))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("root", type=Path)
    assemble(p.parse_args(argv).root)


if __name__ == "__main__":
    main()
