#!/usr/bin/env python3
"""Assemble the mdbook source from README.md and the docs/ bundle.

docs/index.md, the bundle's OKF index, states the chapter order: its
headings become the parts of SUMMARY.md and its entries the chapters,
without their descriptions, so an entry must name a chapter and every
chapter must have an entry. The
README is the introduction, and the index, with its descriptions, is the
contents page to which links to docs/index.md lead. Frontmatter is
dropped, as mdbook would render it as text; contrib/relink then points
links to what the book leaves out at the repository. The bundle's other
files are copied as they are.

    python3 book.py ROOT OUT
"""
import argparse
import posixpath
import re
import shutil
from pathlib import Path

FRONTMATTER = re.compile(r"\A---\n.*?\n---\n+", re.DOTALL)
ENTRY = re.compile(r"\* \[([^\]]+)\]\(([^)\s]+)\)(?: - .*)?")
DOCS = "docs"
CONTENTS = "contents.md"


def strip_frontmatter(text):
    return FRONTMATTER.sub("", text, count=1)


def resolve(base, path):
    """The repository path of link target `path` of a file in directory
    `base`. In docs/, a path from `/` starts at the bundle root."""
    if path.startswith("/"):
        base = "." if base == "." else DOCS
    return posixpath.normpath(posixpath.join(base, path.lstrip("/")))


def summary(index, pages):
    """SUMMARY.md from an OKF index: `# Part` headings and
    `* [Title](file.md) - description` entries, naming each of `pages`,
    the paths in docs/ of the pages the book is given."""
    out = ["# Summary", "", "[Introduction](README.md)", f"[Contents]({CONTENTS})"]
    listed = set()
    for line in strip_frontmatter(index).splitlines():
        if line.startswith("# "):
            out += ["", line, ""]
        elif m := ENTRY.fullmatch(line):
            chapter = posixpath.relpath(resolve(DOCS, m.group(2)), DOCS)
            if chapter not in pages:
                raise ValueError(f"index entry is not a chapter: {line!r}")
            listed.add(chapter)
            out.append(f"- [{m.group(1)}]({chapter})")
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


def assemble(root, out):
    docs = root / DOCS
    index = (docs / "index.md").read_text()
    pages = {
        page.relative_to(docs).as_posix(): page.read_text()
        for page in sorted(docs.rglob("*.md"))
    }
    # docs/README.md directs readers of the repository to the book; as a
    # chapter it would overwrite the introduction.
    for name in ("index.md", "README.md"):
        pages.pop(name, None)
    out.mkdir(parents=True, exist_ok=True)
    shutil.copytree(docs, out, ignore=shutil.ignore_patterns("*.md"), dirs_exist_ok=True)
    (out / "SUMMARY.md").write_text(summary(index, pages))
    (out / CONTENTS).write_text(contents(index))
    shutil.copyfile(root / "README.md", out / "README.md")
    for name, text in pages.items():
        (out / name).parent.mkdir(parents=True, exist_ok=True)
        (out / name).write_text(strip_frontmatter(text))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("root", type=Path)
    p.add_argument("out", type=Path)
    a = p.parse_args(argv)
    assemble(a.root, a.out)


if __name__ == "__main__":
    main()
