import os

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import robot_marks
from robot_marks import MARK, Page

# The nix check runs the same examples every time, and has nowhere to
# keep a database of them.
settings.register_profile("nix", database=None, derandomize=True, max_examples=300)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "default"))


def lines(text, indexed=False):
    return [n + 1 for n, _ in Page("one.md", text, indexed).check()]


def test_a_marked_chapter_may_only_mark_its_title():
    assert lines("# 🤖 One\n\nText.\n\n## Part\n\nMore.\n", True) == []


@pytest.mark.parametrize(
    "inner",
    ["## 🤖 Part\n", "🤖 A paragraph.\n", "- 🤖 An item.\n", "1. 🤖 An item.\n"],
)
def test_a_mark_inside_a_marked_chapter_is_redundant(inner):
    assert lines(f"# 🤖 One\n\nText.\n\n{inner}", True) == [5]


def test_a_mark_inside_a_marked_section_is_redundant():
    assert lines("# One\n\n## 🤖 Part\n\n### Sub\n\n🤖 A paragraph.\n") == [7]


def test_a_mark_inside_a_marked_list_item_is_redundant():
    assert lines("# One\n\n- 🤖 An item.\n\n  🤖 More of it.\n\n  - 🤖 Nested.\n") == [5, 7]


def test_a_section_ends_at_the_next_heading_of_its_level():
    text = "# One\n\n## 🤖 Part\n\n## Other\n\n🤖 A paragraph.\n\n## 🤖 Last\n"
    assert lines(text) == []


def test_the_title_and_index_entry_must_agree():
    assert lines("# 🤖 One\n") == [1]
    assert lines("# One\n", True) == [1]


def test_marks_in_code_and_mid_paragraph_are_not_counted():
    text = "# 🤖 One\n\n```\n\n🤖 code\n```\n\nText then\n🤖 a wrapped line.\n"
    assert lines(text, True) == []


def test_line_numbers_count_the_frontmatter():
    text = "---\ntype: Chapter\n---\n\n# 🤖 One\n\n🤖 A paragraph.\n"
    assert lines(text, True) == [7]


# Pages built from a tree of blocks, rendered as markdown.

paragraph = st.builds(lambda m, wrap: ("paragraph", m, wrap, []), st.booleans(), st.booleans())
# Blocks that can't carry a mark, each with a 🤖 that isn't one.
plain = st.sampled_from(
    [
        ("code", False, ["```", "🤖 code", "", "# not a heading", "```"], []),
        ("table", False, ["| 🤖 a |", "| - |"], []),
        ("math", False, ["$$", "🤖", "$$"], []),
        ("quote", False, ["> 🤖 quoted"], []),
    ]
)
# A list item is tight when no blank line parts it from the item above it,
# or from the first line of the item holding it.
blocks = st.recursive(
    st.one_of(paragraph, plain),
    lambda inner: st.builds(
        lambda m, bullet, tight, children: ("item", m, (bullet, tight), children),
        st.booleans(),
        st.sampled_from(["- ", "* ", "1. ", "10. "]),
        st.booleans(),
        st.lists(inner, max_size=3),
    ),
    max_leaves=6,
)


@st.composite
def sections(draw, level, depth):
    """A section's blocks, then its subsections, all of one level."""
    content = draw(st.lists(blocks, max_size=3))
    if depth:
        sub = level + draw(st.sampled_from([1, 2]))
        content += draw(st.lists(section(sub, depth - 1), max_size=2))
    return content


def section(level, depth):
    return st.builds(
        lambda m, children: ("section", m, level, children), st.booleans(), sections(level, depth)
    )


@st.composite
def pages(draw):
    """A page's text, whether its index entry is marked, and its tree."""
    titled, indexed = draw(st.booleans()), draw(st.booleans())
    children = draw(sections(1, 2))
    head = "---\ntype: Chapter\n---\n\n" if draw(st.booleans()) else ""
    text = head + sequence("# " + mark(titled) + "One", False, children, "") + "\n"
    return text, indexed, ("chapter", titled or indexed, [shape(b) for b in children])


def mark(marked):
    return f"{MARK} " if marked else ""


def sequence(text, after_item, blocks, indent):
    for block in blocks:
        tight = block[0] == "item" and block[2][1] and after_item
        text += ("\n" if tight else "\n\n") + render(block, indent)
        after_item = block[0] == "item"
    return text


def render(block, indent):
    kind, marked, extra, children = block
    if kind == "paragraph":
        text = indent + mark(marked) + "Some text"
        return text + (f"\n{indent}{MARK} wrapped" if extra else "")
    if kind == "item":
        bullet = extra[0]
        first = indent + bullet + mark(marked) + "An item"
        return sequence(first, True, children, indent + " " * len(bullet))
    if kind == "section":
        return sequence("#" * extra + " " + mark(marked) + "Part", False, children, indent)
    return "\n".join(indent + line if line else "" for line in extra)


def shape(block):
    kind, marked, _, children = block
    return (kind, marked, [shape(c) for c in children])


def tree(node):
    return (node.kind, node.marked, [tree(c) for c in node.children])


def parse(text, indexed):
    return Page("one.md", text, indexed)


def apply(text, indexed, *ops):
    """The text and index mark after each op, made on the text the one
    before it left."""
    for op in ops:
        page = parse(text, indexed)
        op(page)
        text, indexed = page.render(), page.chapter.marked
    return text, indexed


def fix(page):
    page.fix()


def merge(page):
    page.merge()


def covered(page):
    return [n.covered() for n in page.chapter.nodes()]


def merge_covers(node, above=False):
    """What merge should leave covered, in the order of node.nodes(): what
    is covered, and what has markable children that it all covers."""
    alone = [merge_covers(c) for c in node.children]
    covers = above or node.marked or bool(node.markable()) and all(
        cs[0] for c, cs in zip(node.children, alone) if c.kind in robot_marks.MARKABLE
    )
    inner = [merge_covers(c, True) for c in node.children] if covers else alone
    return [covers] + [x for cs in inner for x in cs]


@given(pages())
def test_pages_are_read_as_the_tree_they_were_written_from(page):
    text, indexed, expected = page
    assert tree(parse(text, indexed).chapter) == expected


@given(pages())
def test_fix_keeps_what_is_covered_and_leaves_no_redundant_mark(page):
    text, indexed, _ = page
    fixed = parse(*apply(text, indexed, fix))
    assert covered(fixed) == covered(parse(text, indexed))
    assert fixed.check() == []


@given(pages())
def test_only_pages_that_fix_would_change_have_redundant_marks(page):
    text, indexed, _ = page
    assert (parse(text, indexed).check() == []) == (apply(text, indexed, fix) == (text, indexed))


@given(pages())
def test_fix_and_merge_converge(page):
    text, indexed, _ = page
    merged = apply(text, indexed, merge)
    assert apply(text, indexed, fix, merge) == merged
    assert apply(text, indexed, merge, fix) == merged
    assert apply(*merged, merge) == merged
    assert parse(*merged).check() == []


@given(pages())
def test_merge_covers_what_has_all_its_markable_children_covered(page):
    text, indexed, _ = page
    assert covered(parse(*apply(text, indexed, merge))) == merge_covers(parse(text, indexed).chapter)


def test_merge_leaves_a_section_with_an_unmarked_paragraph():
    text = "# One\n\n## Part\n\n🤖 Text.\n\nMore.\n\n```\ncode\n```\n"
    assert apply(text, False, merge) == (text, False)


def test_merge_covers_code_with_the_paragraphs_around_it():
    text = "# One\n\nIntro.\n\n## Part\n\n🤖 Text.\n\n```\ncode\n```\n\nMore.\n"
    merged = text.replace("## Part", "## 🤖 Part").replace("🤖 Text", "Text")
    assert apply(text.replace("More", "🤖 More"), False, merge) == (merged, False)


@given(pages(), st.data())
def test_merge_undoes_relegate(page, data):
    merged = apply(page[0], page[1], merge)
    before = parse(*merged)
    candidates = [n for n in before.chapter.nodes() if n.marked and n.markable()]
    if not candidates:
        return
    node = data.draw(st.sampled_from(candidates))
    after = parse(*merged)
    target = after.at(None if node.line is None else node.line + 1)
    after.relegate(target)
    relegated = after.render(), after.chapter.marked
    again = parse(*relegated)
    # Only the node and its markable children change.
    changed = {n.line for n in [target] + target.markable()}
    for b, a in zip(before.chapter.nodes(), again.chapter.nodes()):
        if b.line not in changed:
            assert b.marked == a.marked
        if b.line in changed and b.line != target.line:
            assert a.marked and a.covered()
    assert again.check() == []
    assert apply(*relegated, merge) == merged


def test_relegate_needs_a_marked_node_with_markable_children():
    page = parse("# 🤖 One\n\n## Part\n\n```\ncode\n```\n", True)
    with pytest.raises(ValueError, match="line 3 is not marked; the chapter is"):
        page.relegate(page.at(3))
    with pytest.raises(ValueError, match="line 3 has nothing to mark instead"):
        page.chapter.marked = False
        page.at(3).marked = True
        page.relegate(page.at(3))


def write(tmp_path, index, pages):
    (tmp_path / "index.md").write_text(index)
    for name, text in pages.items():
        (tmp_path / name).write_text(text)


def test_merge_marks_the_index_entry(tmp_path, capsys):
    write(tmp_path, "# Part\n\n* [One](one.md) - The first\n", {"one.md": "# One\n\n🤖 Text.\n"})
    assert robot_marks.main(["--docs", str(tmp_path), "merge", "--write"]) == 0
    assert (tmp_path / "index.md").read_text() == "# Part\n\n* [🤖 One](one.md) - The first\n"
    assert (tmp_path / "one.md").read_text() == "# 🤖 One\n\nText.\n"
    assert robot_marks.main(["--docs", str(tmp_path), "check"]) == 0


def test_relegate_unmarks_the_index_entry(tmp_path, capsys):
    write(tmp_path, "* [🤖 One](one.md)\n", {"one.md": "# 🤖 One\n\nText.\n\n## Part\n"})
    docs = str(tmp_path)
    assert robot_marks.main(["--docs", docs, "relegate", f"{docs}/one.md", "--write"]) == 0
    assert (tmp_path / "index.md").read_text() == "* [One](one.md)\n"
    assert (tmp_path / "one.md").read_text() == "# One\n\n🤖 Text.\n\n## 🤖 Part\n"


def test_check_fails_on_redundant_marks(tmp_path, capsys):
    write(tmp_path, "* [🤖 One](one.md)\n", {"one.md": "# 🤖 One\n\n🤖 Text.\n"})
    assert robot_marks.main(["--docs", str(tmp_path)]) == 1
    assert capsys.readouterr().out == f"{tmp_path}/one.md:3: paragraph inside the chapter\n"
