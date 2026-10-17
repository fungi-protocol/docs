import book
import pytest

INDEX = """---
okf_version: "0.2"
---

# Part

* [One](one.md) - The first chapter.
* [Two](/sub/two.md) - The second chapter.
"""
CHAPTERS = {"one.md", "sub/two.md"}


def test_frontmatter_is_dropped_once():
    text = "---\ntype: Chapter\n---\n\n# Title\n\n---\nnot: frontmatter\n---\n"
    assert book.strip_frontmatter(text) == "# Title\n\n---\nnot: frontmatter\n---\n"
    assert book.strip_frontmatter("# Title\n") == "# Title\n"


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
        "* [Two](/sub/two.md) - The second chapter.\n"
    )


@pytest.mark.parametrize(
    "line, error",
    [
        ("- [One](one.md) - A dash is not an entry.", "unexpected line"),
        ("* [Readme](../README.md)", "not a chapter"),
        ("* [Nix](/../flake.nix)", "not a chapter"),
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


def test_summary_rejects_a_page_left_out_of_the_index():
    with pytest.raises(ValueError, match="not in the index: sub/two.md"):
        book.summary("# Part\n\n* [One](one.md)\n", CHAPTERS)


def test_assembly_covers_every_chapter(tmp_path):
    root, out = tmp_path / "root", tmp_path / "src"
    (root / "docs" / "sub").mkdir(parents=True)
    (root / "README.md").write_text("# Intro\n\nSee [one](docs/one.md).\n")
    (root / "docs" / "index.md").write_text(INDEX)
    (root / "docs" / "README.md").write_text("---\ntype: Readme\n---\n\nAbout.\n")
    (root / "docs" / "one.md").write_text("---\ntype: Chapter\n---\n\n# One\n")
    (root / "docs" / "sub" / "two.md").write_text(
        "---\ntype: Chapter\n---\n\n# Two\n\nAfter [one](../one.md).\n"
    )
    book.assemble(root, out)
    assert sorted(p.relative_to(out).as_posix() for p in out.rglob("*.md")) == [
        "README.md",
        "SUMMARY.md",
        "contents.md",
        "one.md",
        "sub/two.md",
    ]
    assert (out / "README.md").read_text() == "# Intro\n\nSee [one](docs/one.md).\n"
    assert "* [Two](/sub/two.md) - The second chapter." in (out / "contents.md").read_text()
    assert (out / "one.md").read_text() == "# One\n"
    assert (out / "sub" / "two.md").read_text() == "# Two\n\nAfter [one](../one.md).\n"


def test_assembly_copies_the_other_files_of_the_bundle(tmp_path):
    root, out = tmp_path / "root", tmp_path / "src"
    (root / "docs" / "references").mkdir(parents=True)
    (root / "README.md").write_text("# Intro\n")
    (root / "docs" / "index.md").write_text("# Part\n\n* [One](one.md)\n")
    (root / "docs" / "fig.png").write_bytes(b"\x89PNG")
    (root / "docs" / "references" / "x.py").write_text("print()\n")
    (root / "docs" / "one.md").write_text(
        "---\ntype: Chapter\nstatus: stable\n---\n\n![fig](fig.png) [x](references/x.py)\n"
    )
    book.assemble(root, out)
    assert (out / "fig.png").read_bytes() == b"\x89PNG"
    assert (out / "references" / "x.py").read_text() == "print()\n"
    assert (out / "one.md").read_text() == "![fig](fig.png) [x](references/x.py)\n"

