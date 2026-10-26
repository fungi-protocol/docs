import json
import re

import book
import pytest

INDEX = """---
okf_version: "0.2"
---

# Part

* [One](one.md) - The first chapter.
* [Two](sub/two.md) - The second chapter.
"""
CHAPTERS = {"one.md", "sub/two.md"}
MARKDOWN_CELL = {"cell_type": "markdown", "metadata": {}, "source": ["# Three\n"]}


def notebook(*cells):
    nb = {"cells": list(cells), "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
    return json.dumps(nb, indent=1, ensure_ascii=False) + "\n"


def raw_cell(text):
    return {"cell_type": "raw", "metadata": {}, "source": text.splitlines(True)}


def test_frontmatter_is_dropped_once():
    text = "---\ntype: Chapter\n---\n\n# Title\n\n---\nnot: frontmatter\n---\n"
    assert book.strip_frontmatter(text) == "# Title\n\n---\nnot: frontmatter\n---\n"
    assert book.strip_frontmatter("# Title\n") == "# Title\n"
    assert book.strip_frontmatter("---\ntype: Chapter\n---") == ""
    text = "---\ntype: Chapter\n--- \n\n# Title\n\n---\n\nRest.\n"
    assert book.strip_frontmatter(text) == "# Title\n\n---\n\nRest.\n"


def test_summary_follows_the_index_without_descriptions():
    assert book.summary(INDEX, CHAPTERS) == (
        "# Summary\n\n"
        "[Introduction](README.md)\n"
        "[Contents](contents.md)\n\n"
        "# Part\n\n"
        "- [One](one.md)\n"
        "- [Two](sub/two.md)\n"
    )


def test_contents_keep_descriptions_under_one_title():
    assert book.contents(INDEX) == (
        "# Contents\n\n"
        "## Part\n\n"
        "* [One](one.md) - The first chapter.\n"
        "* [Two](sub/two.md) - The second chapter.\n"
    )


NESTED = """# Part

* [One](one.md) - The first chapter.
  * [Two](sub/two.md) - Under the first.
    * [Three](three.md) - Under the second.

  * [Four](four.md) - Under the first, after a blank line.
* [Five](five.md) - The last chapter.
"""
NESTED_CHAPTERS = {"one.md", "sub/two.md", "three.md", "four.md", "five.md"}


def test_summary_nests_indented_entries_under_the_entry_above():
    assert book.summary(NESTED, NESTED_CHAPTERS) == (
        "# Summary\n\n"
        "[Introduction](README.md)\n"
        "[Contents](contents.md)\n\n"
        "# Part\n\n"
        "- [One](one.md)\n"
        "  - [Two](sub/two.md)\n"
        "    - [Three](three.md)\n"
        "  - [Four](four.md)\n"
        "- [Five](five.md)\n"
    )


def test_contents_keep_the_nesting():
    assert book.contents(NESTED) == (
        "# Contents\n\n"
        "## Part\n\n"
        "* [One](one.md) - The first chapter.\n"
        "  * [Two](sub/two.md) - Under the first.\n"
        "    * [Three](three.md) - Under the second.\n\n"
        "  * [Four](four.md) - Under the first, after a blank line.\n"
        "* [Five](five.md) - The last chapter.\n"
    )


@pytest.mark.parametrize(
    "index, error",
    [
        ("# Part\n\n  * [One](one.md)\n", "no entry above"),
        ("  * [One](one.md)\n", "no entry above"),
        ("* [One](one.md)\n\n# Part\n\n  * [Two](sub/two.md)\n", "no entry above"),
        ("# Part\n\n* [One](one.md)\n    * [Two](sub/two.md)\n", "more than one level"),
        ("# Part\n\n* [One](one.md)\n * [Two](sub/two.md)\n", "odd indentation"),
        ("# Part\n\n* [One](one.md)\n   * [Two](sub/two.md)\n", "odd indentation"),
        ("# Part\n\n* [One](one.md)\n\t* [Two](sub/two.md)\n", "unexpected line"),
        ("# Part\n\n* [One](one.md)\n  # Sub\n", "unexpected line"),
    ],
)
def test_summary_rejects_entries_it_cannot_nest(index, error):
    with pytest.raises(ValueError, match=error):
        book.summary(index, CHAPTERS)


def test_summary_rejects_a_nested_chapter_listed_twice():
    with pytest.raises(ValueError, match="repeats a chapter"):
        book.summary(
            "# Part\n\n* [One](one.md)\n  * [Two](sub/two.md)\n  * [Again](one.md)\n",
            CHAPTERS,
        )


def test_summary_rejects_a_nested_entry_that_is_not_a_chapter():
    with pytest.raises(ValueError, match="not a chapter"):
        book.summary("# Part\n\n* [One](one.md)\n  * [Gone](gone.md)\n", CHAPTERS)


@pytest.mark.parametrize(
    "line, error",
    [
        ("- [One](one.md) - A dash is not an entry.", "unexpected line"),
        ("* [Readme](../README.md)", "not a chapter"),
        ("* [Nix](/../flake.nix)", "not a chapter"),
        ("* [Root](/one.md)", "not a chapter"),
        ("* [Site](https://example.org/x.md)", "not a chapter"),
        ("* [Index](index.md)", "not a chapter"),
        ("* [About](README.md)", "not a chapter"),
        ("* [Anchor](one.md#a)", "not a chapter"),
        ("* [Log](log.md)", "not a chapter"),
        ("* [Sub](sub/index.md)", "not a chapter"),
        ("* [Dir](sub/)", "not a chapter"),
        ("* [Gone](gone.md)", "not a chapter"),
    ],
)
def test_summary_rejects_what_it_cannot_place(line, error):
    with pytest.raises(ValueError, match=error):
        book.summary(f"# Part\n\n{line}\n", CHAPTERS)


def test_summary_rejects_a_chapter_listed_twice():
    with pytest.raises(ValueError, match="repeats a chapter"):
        book.summary("# Part\n\n* [One](one.md)\n* [Again](./one.md)\n", CHAPTERS)


def test_summary_rejects_a_page_left_out_of_the_index():
    with pytest.raises(ValueError, match=r"not in the index: sub/two\.md"):
        book.summary("# Part\n\n* [One](one.md)\n", CHAPTERS)


@pytest.mark.parametrize(
    "fields",
    [
        "type: Chapter\nstatus: stable",
        "type: Chapter\nstatus: deprecated",
        "type: Chapter\nstatus: draft\nstale_after: 2027-04-14T00:00:00Z",
        "type: Chapter\nstatus: draft\nstale_after: '2027-04-14T00:00:00+02:00'",
        "type: Chapter\nstatus: stable # reviewed",
        "\"type\": Chapter\nstatus : stable",
    ],
)
def test_check_accepts_a_status_and_a_draft_that_can_go_stale(fields):
    book.check("one.md", f"---\n{fields}\n---\n\n# One\n")


def test_check_reads_frontmatter_that_ends_the_page():
    book.check("one.md", "---\ntype: Chapter\nstatus: stable\n---")


@pytest.mark.parametrize(
    "text, error",
    [
        ("# One\n", "no type"),
        ("---\nstatus: stable\n---\n", "no type"),
        ("---\ntype: Chapter\n---\n", "status None"),
        ("---\ntype: Chapter\nstatus: final\n---\n", "status 'final'"),
        ("---\ntype: [Chapter\nstatus: stable\n---\n", "while parsing"),
        (
            "---\ntype: Chapter\nstatus: draft\nstale_after: 2027-02-30\n---\n",
            "day",
        ),
        ("---\ntype: Chapter\nstatus: draft\n---\n", "stale_after"),
        (
            "---\ntype: Chapter\nstatus: draft\nstale_after: 2027-04-14\n---\n",
            "stale_after",
        ),
        ("---\ntype: Chapter\nstatus: draft\nstale_after: soon\n---\n", "stale_after"),
    ],
)
def test_check_rejects_a_page_without_a_type_status_or_stale_after(text, error):
    with pytest.raises(ValueError, match=f"one.md: .*{error}"):
        book.check("one.md", text)


def test_a_notebooks_frontmatter_is_the_raw_cell_that_opens_it():
    head = "---\ntype: Chapter\nstatus: stable\n---"
    text = notebook(raw_cell(head), MARKDOWN_CELL)
    assert book.notebook_frontmatter(text) == (head, notebook(MARKDOWN_CELL))
    book.check("three.ipynb", text)


@pytest.mark.parametrize(
    "cells",
    [
        [MARKDOWN_CELL],
        [MARKDOWN_CELL, raw_cell("---\ntype: Chapter\nstatus: stable\n---")],
        [raw_cell("---\ntype: Chapter\nstatus: stable\n---\n\nMore.\n"), MARKDOWN_CELL],
    ],
)
def test_check_rejects_a_notebook_that_opens_without_frontmatter(cells):
    with pytest.raises(ValueError, match="three.ipynb: no type"):
        book.check("three.ipynb", notebook(*cells))


def test_check_rejects_a_notebook_that_is_not_json():
    with pytest.raises(ValueError, match="three.ipynb: Expecting value"):
        book.check("three.ipynb", "# Three\n")


def test_assembly_skips_reserved_files_at_any_level(tmp_path):
    root, out = tmp_path / "root", tmp_path / "root" / "src"
    (root / "docs" / "sub").mkdir(parents=True)
    (root / "README.md").write_text("# Intro\n")
    (root / "docs" / "index.md").write_text("# Part\n")
    (root / "docs" / "log.md").write_text("# Log\n\n## 2026-10-15\n* Created.\n")
    (root / "docs" / "sub" / "index.md").write_text("# Sub\n")
    book.assemble(root)
    assert sorted(p.relative_to(out).as_posix() for p in out.rglob("*.md")) == [
        "README.md",
        "SUMMARY.md",
        "contents.md",
    ]


def test_assembly_checks_the_readme_it_skips(tmp_path):
    root = tmp_path / "root"
    (root / "docs").mkdir(parents=True)
    (root / "README.md").write_text("# Intro\n")
    (root / "docs" / "index.md").write_text("# Part\n")
    (root / "docs" / "README.md").write_text("---\ntype: Readme\n---\n")
    with pytest.raises(ValueError, match=r"README\.md: status"):
        book.assemble(root)


def test_assembly_covers_every_chapter(tmp_path):
    root, out = tmp_path / "root", tmp_path / "root" / "src"
    (root / "docs" / "sub").mkdir(parents=True)
    (root / "README.md").write_text("# Intro\n\nSee [one](docs/one.md).\n")
    (root / "docs" / "index.md").write_text(INDEX)
    (root / "docs" / "README.md").write_text(
        "---\ntype: Readme\nstatus: stable\n---\n\nAbout.\n"
    )
    (root / "docs" / "one.md").write_text(
        "---\ntype: Chapter\nstatus: stable\n---\n\n# One\n"
    )
    (root / "docs" / "sub" / "two.md").write_text(
        "---\ntype: Chapter\nstatus: stable\n---\n\n# Two\n\nAfter [one](../one.md).\n"
    )
    book.assemble(root)
    assert sorted(p.relative_to(out).as_posix() for p in out.rglob("*.md")) == [
        "README.md",
        "SUMMARY.md",
        "contents.md",
        "one.md",
        "sub/two.md",
    ]
    assert (out / "README.md").read_text() == "# Intro\n\nSee [one](one.md).\n"
    contents = (out / "contents.md").read_text()
    assert "* [Two](sub/two.md) - The second chapter." in contents
    assert (out / "one.md").read_text() == "# One\n"
    assert (out / "sub" / "two.md").read_text() == "# Two\n\nAfter [one](../one.md).\n"


@pytest.mark.parametrize(
    "name", ["SUMMARY.md", "contents.md", "summary.md", "Contents.md", "readme.md"]
)
def test_assembly_rejects_a_page_named_like_one_it_generates(tmp_path, name):
    root = tmp_path / "root"
    (root / "docs").mkdir(parents=True)
    (root / "README.md").write_text("# Intro\n")
    (root / "docs" / "index.md").write_text("# Part\n")
    (root / "docs" / name).write_text("---\ntype: Chapter\nstatus: stable\n---\n")
    with pytest.raises(ValueError, match=re.escape(f"generated by book.py: {name}")):
        book.assemble(root)


def test_assembly_copies_the_other_files_of_the_bundle(tmp_path):
    root, out = tmp_path / "root", tmp_path / "root" / "src"
    (root / "docs" / "references").mkdir(parents=True)
    (root / "README.md").write_text("# Intro\n")
    (root / "docs" / "index.md").write_text("# Part\n\n* [One](one.md)\n")
    (root / "docs" / "fig.png").write_bytes(b"\x89PNG")
    (root / "docs" / "references" / "x.py").write_text("print()\n")
    (root / "docs" / "one.md").write_text(
        "---\ntype: Chapter\nstatus: stable\n---\n\n"
        "![fig](fig.png) [x](references/x.py)\n"
    )
    book.assemble(root)
    assert (out / "fig.png").read_bytes() == b"\x89PNG"
    assert (out / "references" / "x.py").read_text() == "print()\n"
    assert (out / "one.md").read_text() == "![fig](fig.png) [x](references/x.py)\n"


def test_assembly_replaces_an_earlier_one(tmp_path):
    root, out = tmp_path / "root", tmp_path / "root" / "src"
    (root / "docs").mkdir(parents=True)
    (root / "README.md").write_text("# Intro\n")
    (root / "docs" / "index.md").write_text("# Part\n\n* [One](one.md)\n")
    (root / "docs" / "one.md").write_text("---\ntype: Chapter\nstatus: stable\n---\n")
    (root / "docs" / "old.png").write_bytes(b"")
    book.assemble(root)
    (root / "docs" / "old.png").unlink()
    book.assemble(root)
    assert not (out / "old.png").exists()


def test_assembly_keeps_the_directory_it_fills(tmp_path):
    root, out = tmp_path / "root", tmp_path / "root" / "src"
    (root / "docs").mkdir(parents=True)
    (root / "README.md").write_text("# Intro\n")
    (root / "docs" / "index.md").write_text("# Part\n")
    book.assemble(root)
    inode = out.stat().st_ino
    book.assemble(root)
    assert out.stat().st_ino == inode


def test_assembly_keeps_the_earlier_one_when_the_index_is_wrong(tmp_path):
    root, out = tmp_path / "root", tmp_path / "root" / "src"
    (root / "docs").mkdir(parents=True)
    (root / "README.md").write_text("# Intro\n")
    (root / "docs" / "index.md").write_text("# Part\n\n* [One](one.md)\n")
    (root / "docs" / "one.md").write_text("---\ntype: Chapter\nstatus: stable\n---\n")
    book.assemble(root)
    (root / "docs" / "two.md").write_text("---\ntype: Chapter\nstatus: stable\n---\n")
    with pytest.raises(ValueError, match="not in the index"):
        book.assemble(root)
    assert (out / "SUMMARY.md").exists()


def test_assembly_keeps_the_earlier_one_without_a_readme(tmp_path):
    root, out = tmp_path / "root", tmp_path / "root" / "src"
    (root / "docs").mkdir(parents=True)
    (root / "README.md").write_text("# Intro\n")
    (root / "docs" / "index.md").write_text("# Part\n\n* [One](one.md)\n")
    (root / "docs" / "one.md").write_text("---\ntype: Chapter\nstatus: stable\n---\n")
    book.assemble(root)
    (root / "README.md").unlink()
    with pytest.raises(FileNotFoundError):
        book.assemble(root)
    assert (out / "one.md").exists()


def test_assembly_ignores_itself(tmp_path):
    root, out = tmp_path / "root", tmp_path / "root" / "src"
    (root / "docs").mkdir(parents=True)
    (root / "README.md").write_text("# Intro\n")
    (root / "docs" / "index.md").write_text("# Part\n")
    book.assemble(root)
    assert (out / ".gitignore").read_text() == "*\n"


def test_assembly_ignores_itself_whatever_the_bundle_ignores(tmp_path):
    root, out = tmp_path / "root", tmp_path / "root" / "src"
    (root / "docs").mkdir(parents=True)
    (root / "README.md").write_text("# Intro\n")
    (root / "docs" / "index.md").write_text("# Part\n")
    (root / "docs" / ".gitignore").write_text(".DS_Store\n")
    book.assemble(root)
    assert (out / ".gitignore").read_text() == "*\n"


def test_assembly_ignores_itself_when_the_copy_fails(tmp_path, monkeypatch):
    root, out = tmp_path / "root", tmp_path / "root" / "src"
    (root / "docs").mkdir(parents=True)
    (root / "README.md").write_text("# Intro\n")
    (root / "docs" / "index.md").write_text("# Part\n")

    def fail(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(book.shutil, "copytree", fail)
    with pytest.raises(OSError):
        book.assemble(root)
    assert (out / ".gitignore").read_text() == "*\n"


def test_assembly_makes_chapters_of_notebooks_without_their_frontmatter(tmp_path):
    root, out = tmp_path / "root", tmp_path / "root" / "src"
    (root / "docs" / ".ipynb_checkpoints").mkdir(parents=True)
    (root / "README.md").write_text("# Intro\n")
    (root / "docs" / "index.md").write_text("# Part\n\n* [Three](three.ipynb)\n")
    head = "---\ntype: Chapter\nstatus: stable\n---"
    (root / "docs" / "three.ipynb").write_text(notebook(raw_cell(head), MARKDOWN_CELL))
    # Jupyter's autosaves are neither chapters nor part of the book.
    checkpoint = root / "docs" / ".ipynb_checkpoints" / "three-checkpoint.ipynb"
    checkpoint.write_text(notebook(MARKDOWN_CELL))
    book.assemble(root)
    assert (out / "three.ipynb").read_text() == notebook(MARKDOWN_CELL)
    assert "- [Three](three.ipynb)\n" in (out / "SUMMARY.md").read_text()
    assert not (out / ".ipynb_checkpoints").exists()
