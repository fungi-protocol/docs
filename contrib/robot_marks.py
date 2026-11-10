#!/usr/bin/env python3
"""Check and move the 🤖 marks in the docs/ bundle.

A 🤖 marks LLM output: a chapter, by its index entry and its title, a
section, by its heading, or a paragraph or list item, by its start. A
mark covers everything under it, so a mark inside a marked chapter,
section or list item is redundant, and suggests that only the inner part
is LLM output.

A page is a tree. The chapter holds the paragraphs and list items before
its first section, and its sections; a section holds the same, down to
its subsections; a list item holds the paragraphs and list items nested
in it. Code, tables, display math, quotes, comments and footnotes can't
carry a mark, and are only covered by one.

    python3 contrib/robot_marks.py [--docs DOCS] [check]
        Lists redundant marks, and chapters whose title and index entry
        disagree, and exits with status 1 if there are any.

    python3 contrib/robot_marks.py fix [--write]
        Removes the redundant marks, and marks the title and index entry
        of a chapter if either is marked.

    python3 contrib/robot_marks.py merge [--write]
        Where every paragraph, list item and section in a chapter, section
        or list item is covered, marks it instead, and removes the
        redundant marks.

    python3 contrib/robot_marks.py relegate PAGE[:LINE] [--write]
        Moves the mark of a chapter, or of the section or list item that
        starts on LINE, onto the paragraphs, list items and sections in
        it, for when part of it has been rewritten. merge undoes this.

fix, merge and relegate print their changes as a diff, and make them
with --write. fix and merge give the same marks in either order. Chapters
nested in the index are separate pages, each marked on its own.
"""
import argparse
import difflib
import os
import re
import sys

MARK = "🤖"
ENTRY = re.compile(r"^ *\* \[([^\]]*)\]\(([^)\s]+)\)")
HEADING = re.compile(r"^(#{1,6})(\s+)(.*)$")
# A list item, as it may start a block or interrupt a paragraph.
ITEM = re.compile(r"^( {0,3})([-*+]|\d+[.)])(\s+)")
# A list item at any indentation.
NESTED_ITEM = re.compile(r"^(\s*)([-*+]|\d+[.)])(\s+)")
FENCE = re.compile(r"^\s*(```|~~~)")
FOOTNOTE = re.compile(r"^\[\^[^\]]+\]:")
FRONTMATTER = re.compile(r"\A---\n.*?\n---[ \t]*\n", re.DOTALL)
# What can carry a mark, besides the chapter.
MARKABLE = ("section", "paragraph", "item")
LABEL = {"item": "list item"}


def starts_marked(text):
    return text.lstrip().startswith(MARK)


class Node:
    def __init__(self, kind, line, marked=False):
        self.kind = kind
        # The index of its first line in the page, or None for the chapter.
        self.line = line
        self.marked = self.was_marked = marked
        self.level = 0
        self.children = []
        self.parent = None

    def add(self, child):
        child.parent = self
        self.children.append(child)
        return child

    def nodes(self):
        yield self
        for child in self.children:
            yield from child.nodes()

    def markable(self):
        return [c for c in self.children if c.kind in MARKABLE]

    def covered(self):
        node = self
        while node:
            if node.marked:
                return True
            node = node.parent
        return False

    def label(self):
        return LABEL.get(self.kind, self.kind)


class Page:
    """A chapter, its sections, and their paragraphs and list items."""

    def __init__(self, path, text, indexed):
        self.path = path
        self.lines = text.split("\n")
        m = FRONTMATTER.match(text)
        start = text[: m.end()].count("\n") if m else 0
        self.title = None
        self.title_marked = False
        self.chapter = Node("chapter", None)
        self.blocks(list(enumerate(self.lines))[start:], self.chapter, True)
        # A mark on either claims the chapter, and a change marks both.
        self.indexed = indexed
        self.chapter.marked = self.chapter.was_marked = indexed or self.title_marked

    def blocks(self, rows, parent, top):
        """Adds the blocks in rows, pairs of a line's index and its text
        with the indentation of the list item holding it removed, to
        parent. Headings are only read at the top."""
        scopes = [parent]
        k, n = 0, len(rows)
        while k < n:
            i, line = rows[k]
            stripped = line.strip()
            heading = HEADING.match(line) if top else None
            fence = FENCE.match(line)
            item = ITEM.match(line)
            if not stripped:
                k += 1
            elif fence:
                scopes[-1].add(Node("code", i))
                k += 1
                while k < n and not rows[k][1].lstrip().startswith(fence.group(1)):
                    k += 1
                k += 1
            elif heading:
                level = len(heading.group(1))
                marked = starts_marked(heading.group(3))
                if level == 1 and self.title is None:
                    self.title, self.title_marked = i, marked
                else:
                    while len(scopes) > 1 and scopes[-1].level >= level:
                        scopes.pop()
                    scopes.append(scopes[-1].add(Node("section", i, marked)))
                    scopes[-1].level = level
                k += 1
            elif stripped.startswith("$$"):
                scopes[-1].add(Node("math", i))
                if stripped == "$$" or not stripped.endswith("$$"):
                    k += 1
                    while k < n and "$$" not in rows[k][1]:
                        k += 1
                k += 1
            elif stripped.startswith("<!--"):
                scopes[-1].add(Node("comment", i))
                while k < n and "-->" not in rows[k][1]:
                    k += 1
                k += 1
            elif stripped.startswith(("|", ">")) or FOOTNOTE.match(line):
                scopes[-1].add(Node({"|": "table", ">": "quote"}.get(stripped[0], "footnote"), i))
                k += 1
                while k < n and rows[k][1].strip() and not (
                    FOOTNOTE.match(rows[k][1]) or (top and HEADING.match(rows[k][1]))
                ):
                    k += 1
            elif item:
                node = scopes[-1].add(Node("item", i, starts_marked(line[item.end():])))
                k = self.item(rows, k, item, node)
            else:
                scopes[-1].add(Node("paragraph", i, starts_marked(line)))
                k += 1
                while k < n and rows[k][1].strip() and not (
                    (top and HEADING.match(rows[k][1]))
                    or FENCE.match(rows[k][1])
                    or ITEM.match(rows[k][1])
                ):
                    k += 1

    def item(self, rows, k, item, node):
        """Adds what is nested in the list item that starts at rows[k] to
        node, and returns where the item ends."""
        indent, content = len(item.group(1)), item.end()
        n = len(rows)
        k += 1
        # The rest of the item's own paragraph.
        while k < n and rows[k][1].strip() and not (
            NESTED_ITEM.match(rows[k][1]) or FENCE.match(rows[k][1]) or HEADING.match(rows[k][1])
        ):
            k += 1
        inner = []
        while k < n:
            text = rows[k][1]
            depth = len(text) - len(text.lstrip())
            if text.strip() and depth <= indent:
                break
            inner.append((rows[k][0], text[min(depth, content):]))
            k += 1
        self.blocks(inner, node, False)
        return k

    def at(self, line):
        """The chapter, or the section or list item that starts on line,
        counted from 1."""
        if line is None or line - 1 == self.title:
            return self.chapter
        for node in self.chapter.nodes():
            if node.kind in ("section", "item") and node.line == line - 1:
                return node
        raise ValueError(f"{self.path}:{line}: no section or list item starts here")

    def where(self, node):
        if node.kind == "chapter":
            return "the chapter"
        return f"the {node.label()} on line {node.line + 1}"

    def outer(self, node):
        """The outermost marked node holding node."""
        found, above = None, node.parent
        while above:
            if above.marked:
                found = above
            above = above.parent
        return found

    def check(self):
        found = []
        if self.title is not None and self.title_marked != self.indexed:
            found.append((self.title, "title and index entry disagree"))
        for node in self.chapter.nodes():
            outer = self.outer(node)
            if node.marked and outer:
                found.append((node.line, f"{node.label()} inside {self.where(outer)}"))
        return sorted(found)

    def fix(self):
        """Removes the marks inside marked nodes, and marks the title and
        index entry of a chapter if either is."""
        for node in self.chapter.nodes():
            if self.outer(node):
                node.marked = False

    def merge(self):
        """Marks each node whose markable children are all covered, and
        removes the marks this makes redundant."""

        def visit(node):
            for child in node.children:
                visit(child)
            markable = node.markable()
            if markable and all(c.marked for c in markable):
                node.marked = True

        visit(self.chapter)
        self.fix()

    def relegate(self, node):
        """Moves node's mark onto its markable children."""
        if not node.marked:
            outer = self.outer(node)
            why = f"; {self.where(outer)} is" if outer else ""
            raise ValueError(f"{self.path}: {self.where(node)} is not marked{why}")
        if not node.markable():
            raise ValueError(f"{self.path}: {self.where(node)} has nothing to mark instead")
        node.marked = False
        for child in node.markable():
            child.marked = True

    def changes(self):
        """The nodes whose marks have changed."""
        return [n for n in self.chapter.nodes() if n.marked != n.was_marked]

    def render(self):
        lines = list(self.lines)
        for node in self.chapter.nodes():
            if node.kind == "chapter":
                if self.title is not None and node.marked != self.title_marked:
                    lines[self.title] = remark(lines[self.title], node.marked)
            elif node.marked != node.was_marked:
                lines[node.line] = remark(lines[node.line], node.marked)
        return "\n".join(lines)


def remark(line, marked):
    """line, with the mark at the start of its text added or removed."""
    m = HEADING.match(line)
    if m:
        head = line[: m.start(3)]
    else:
        m = NESTED_ITEM.match(line)
        head = line[: m.end()] if m else line[: len(line) - len(line.lstrip())]
    rest = line[len(head):]
    if marked:
        return f"{head}{MARK} {rest}"
    assert rest.startswith(MARK), line
    return head + rest[len(MARK):].lstrip()


def index_entry(index, path, marked):
    """index, with the entry for path marked or not."""
    lines = index.split("\n")
    for i, line in enumerate(lines):
        m = ENTRY.match(line)
        if m and m.group(2) == path and starts_marked(m.group(1)) != marked:
            title = m.group(1)
            title = f"{MARK} {title}" if marked else title.lstrip()[len(MARK):].lstrip()
            lines[i] = line[: m.start(1)] + title + line[m.end(1):]
    return "\n".join(lines)


def load(docs):
    index_path = os.path.join(docs, "index.md")
    with open(index_path) as f:
        index = f.read()
    pages = {}
    for line in index.split("\n"):
        m = ENTRY.match(line)
        if m and m.group(2).endswith(".md"):
            with open(os.path.join(docs, m.group(2))) as f:
                pages[m.group(2)] = Page(m.group(2), f.read(), starts_marked(m.group(1)))
    return index, pages


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0],
        epilog=__doc__.split("\n\n", 1)[1],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--docs", default="docs")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("check")
    for name in ("fix", "merge", "relegate"):
        command = commands.add_parser(name)
        if name == "relegate":
            command.add_argument("node", metavar="PAGE[:LINE]")
        command.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)

    index_path = os.path.join(args.docs, "index.md")
    index, pages = load(args.docs)

    def name(page, line):
        return f"{os.path.join(args.docs, page.path)}:{(page.title if line is None else line) + 1}"

    if args.command in (None, "check"):
        found = 0
        for page in pages.values():
            for line, message in page.check():
                print(f"{name(page, line)}: {message}")
                found += 1
        return 1 if found else 0

    if args.command == "relegate":
        path, _, line = args.node.partition(":")
        if path.startswith(args.docs.rstrip("/") + "/"):
            path = path[len(args.docs.rstrip("/")) + 1:]
        if path not in pages:
            parser.error(f"{path} is not a chapter in {index_path}")
        try:
            pages[path].relegate(pages[path].at(int(line) if line else None))
        except ValueError as e:
            parser.error(str(e))
    else:
        for page in pages.values():
            getattr(page, args.command)()

    new_index = index
    out = []
    for page in pages.values():
        for node in page.changes():
            uncovered = [c for c in node.children if c.kind not in MARKABLE]
            note = ""
            if uncovered:
                kinds = ", ".join(sorted({c.label() for c in uncovered}))
                note = f", {'covering' if node.marked else 'uncovering'} {kinds}"
            action = "mark" if node.marked else "unmark"
            print(f"{name(page, node.line)}: {action} {page.where(node)}{note}", file=sys.stderr)
        if page.chapter.marked != page.indexed:
            new_index = index_entry(new_index, page.path, page.chapter.marked)
        old, new = "\n".join(page.lines), page.render()
        if new != old:
            out.append((os.path.join(args.docs, page.path), old, new))
    if new_index != index:
        out.append((index_path, index, new_index))
    for path, old, new in out:
        if args.write:
            with open(path, "w") as f:
                f.write(new)
        else:
            sys.stdout.writelines(
                difflib.unified_diff(
                    old.splitlines(True), new.splitlines(True), f"a/{path}", f"b/{path}"
                )
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
