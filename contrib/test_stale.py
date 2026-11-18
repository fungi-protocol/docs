from datetime import datetime, timezone

import pytest
import stale

NOW = datetime(2027, 4, 8, tzinfo=timezone.utc)


def page(kind, status, stale_after=None):
    line = f"stale_after: {stale_after}\n" if stale_after else ""
    return f"---\ntype: {kind}\nstatus: {status}\n{line}---\n"


@pytest.mark.parametrize(
    "stale_after", ["2027-04-15T00:00:00Z", "2027-04-01T00:00:00Z"]
)
def test_a_draft_stale_within_a_week_or_already_gets_an_issue(stale_after):
    [(title, body)] = stale.issues(
        {"a.md": page("Chapter", "draft", stale_after)}, [], NOW
    )
    assert title == f"docs/a.md goes stale on {stale_after[:10]}"
    assert "`docs/a.md`" in body and stale_after[:10] in body


@pytest.mark.parametrize(
    "text",
    [
        page("Chapter", "draft", "2027-04-15T00:00:01Z"),
        page("Stub", "draft", "2027-04-15T00:00:00Z"),
        page("Chapter", "stable"),
    ],
)
def test_no_issue_for_a_later_draft_a_stub_or_a_stable_page(text):
    assert stale.issues({"a.md": text}, [], NOW) == []


def titles(existing):
    pages = {
        name: page("Chapter", "draft", "2027-04-10T00:00:00Z")
        for name in ("a.md", "ab.md")
    }
    return [t for t, _ in stale.issues(pages, existing, NOW)]


@pytest.mark.parametrize("title", ["docs/a.md goes stale on 2027-01-01", "docs/a.md"])
def test_no_second_issue_while_one_is_open_for_the_chapter(title):
    existing = [{"title": title, "state": "OPEN"}]
    assert titles(existing) == ["docs/ab.md goes stale on 2027-04-10"]


def test_a_closed_issue_is_not_reopened_until_stale_after_moves():
    closed = [{"title": "docs/a.md goes stale on 2027-04-10", "state": "CLOSED"}]
    assert titles(closed) == ["docs/ab.md goes stale on 2027-04-10"]
    moved = [{"title": "docs/a.md goes stale on 2027-01-01", "state": "CLOSED"}]
    assert titles(moved) == [
        "docs/a.md goes stale on 2027-04-10",
        "docs/ab.md goes stale on 2027-04-10",
    ]


def test_an_invalid_page_fails_the_run():
    with pytest.raises(ValueError, match="stale_after"):
        stale.issues({"a.md": page("Chapter", "draft")}, [], NOW)
