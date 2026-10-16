#!/usr/bin/env python3
"""Assemble the mdbook source from README.md and the docs/ bundle.

docs/index.md, the bundle's OKF index, states the chapter order: its
headings become the parts of SUMMARY.md and its entries the chapters,
without their descriptions. The README is the introduction, and the index,
with its descriptions, is the contents page to which links to docs/index.md
lead. Frontmatter is dropped, as mdbook would render it as text, and links
that leave docs/ point at the repository at the built revision.

    python3 book.py ROOT OUT --repository URL --rev REV
"""
import argparse
import posixpath
import re
from pathlib import Path

FRONTMATTER = re.compile(r"\A---\n.*?\n---\n+", re.DOTALL)
LINK = re.compile(r"\]\(([^)\s]+)\)")
SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:|#")
ENTRY = re.compile(r"\* \[([^\]]+)\]\(([^)\s]+)\)(?: - .*)?")
DOCS = "docs"
CONTENTS = "contents.md"


def strip_frontmatter(text):
    return FRONTMATTER.sub("", text, count=1)


def relink(text, base, blob):
    """Links of a file in directory `base` of the repository, rewritten for
    a book whose source is docs/: targets in docs/ become relative to the
    file's place in the book, and every other target a URL under `blob`."""
    here = "." if base == "." else posixpath.relpath(base, DOCS)

    def sub(m):
        url = m.group(1)
        if SCHEME.match(url):
            return m.group(0)
        path, sep, frag = url.partition("#")
        target = posixpath.normpath(posixpath.join(base, path))
        if target == f"{DOCS}/index.md":
            target = f"{DOCS}/{CONTENTS}"
        if not target.startswith(f"{DOCS}/"):
            return f"]({blob}/{target}{sep}{frag})"
        return f"]({posixpath.relpath(target, posixpath.join(DOCS, here))}{sep}{frag})"

    return LINK.sub(sub, text)


def summary(index):
    """SUMMARY.md from an OKF index: `# Part` headings and
    `* [Title](file.md) - description` entries."""
    out = ["# Summary", "", "[Introduction](README.md)", f"[Contents]({CONTENTS})"]
    for line in strip_frontmatter(index).splitlines():
        if line.startswith("# "):
            out += ["", line, ""]
        elif m := ENTRY.fullmatch(line):
            out.append(f"- [{m.group(1)}]({m.group(2)})")
        elif line.strip():
            raise ValueError(f"unexpected line in index: {line!r}")
    return "\n".join(out) + "\n"


def contents(index):
    """The contents page: the index with its descriptions, its parts one
    heading level down."""
    body = re.sub(r"^# ", "## ", strip_frontmatter(index), flags=re.MULTILINE)
    return "# Contents\n\n" + body


def assemble(root, out, repository, rev):
    blob = f"{repository}/blob/{rev}"
    docs = root / DOCS
    index = (docs / "index.md").read_text()
    out.mkdir(parents=True, exist_ok=True)
    (out / "SUMMARY.md").write_text(summary(index))
    (out / CONTENTS).write_text(contents(index))
    (out / "README.md").write_text(relink((root / "README.md").read_text(), ".", blob))
    for page in sorted(docs.rglob("*.md")):
        name = page.relative_to(docs)
        # docs/README.md directs readers of the repository to the book; as a
        # chapter it would overwrite the introduction.
        if name.as_posix() in ("index.md", "README.md"):
            continue
        base = page.parent.relative_to(root).as_posix()
        (out / name).parent.mkdir(parents=True, exist_ok=True)
        (out / name).write_text(relink(strip_frontmatter(page.read_text()), base, blob))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("root", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--repository", required=True)
    p.add_argument("--rev", required=True)
    a = p.parse_args(argv)
    assemble(a.root, a.out, a.repository, a.rev)


if __name__ == "__main__":
    main()
