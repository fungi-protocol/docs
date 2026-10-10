import book
import pytest

BLOB = "https://example.org/blob/abc"
INDEX = """---
okf_version: "0.2"
---

# Part

* [One](one.md) - The first chapter.
* [Two](sub/two.md) - The second chapter.
"""


def test_frontmatter_is_dropped_once():
    text = "---\ntype: Chapter\n---\n\n# Title\n\n---\nnot: frontmatter\n---\n"
    assert book.strip_frontmatter(text) == "# Title\n\n---\nnot: frontmatter\n---\n"
    assert book.strip_frontmatter("# Title\n") == "# Title\n"


@pytest.mark.parametrize(
    "base, link, expected",
    [
        (".", "docs/one.md#a", "one.md#a"),
        (".", "docs/index.md", "contents.md"),
        (".", "flake.nix", f"{BLOB}/flake.nix"),
        ("docs", "sub/two.md", "sub/two.md"),
        ("docs", "../README.md", f"{BLOB}/README.md"),
        ("docs/sub", "../one.md", "../one.md"),
        ("docs/sub", "../index.md", "../contents.md"),
        ("docs/sub", "../../nix/site.nix", f"{BLOB}/nix/site.nix"),
        ("docs", "https://example.org/x", "https://example.org/x"),
        ("docs", "#section", "#section"),
    ],
)
def test_links_leave_the_book_only_for_the_repository(base, link, expected):
    assert book.relink(f"[text]({link})", base, BLOB) == f"[text]({expected})"


def test_summary_follows_the_index_without_descriptions():
    assert book.summary(INDEX) == (
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


def test_summary_rejects_what_it_cannot_place():
    with pytest.raises(ValueError, match="unexpected line"):
        book.summary("# Part\n\n- [One](one.md) - A dash is not an entry.\n")


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
    book.assemble(root, out, "https://example.org", "abc")
    assert sorted(p.relative_to(out).as_posix() for p in out.rglob("*.md")) == [
        "README.md",
        "SUMMARY.md",
        "contents.md",
        "one.md",
        "sub/two.md",
    ]
    assert (out / "README.md").read_text() == "# Intro\n\nSee [one](one.md).\n"
    assert (out / "one.md").read_text() == "# One\n"
    assert (out / "sub" / "two.md").read_text() == "# Two\n\nAfter [one](../one.md).\n"
