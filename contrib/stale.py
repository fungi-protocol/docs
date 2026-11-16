#!/usr/bin/env python3
"""Open an issue for each draft chapter that goes stale within a week.

A chapter gets no second issue while the first word of an open one's
title is its path, nor an issue titled like a closed one, so closing the
issue without moving the chapter's stale_after leaves it closed. Stubs
are skipped: a stub's draft is under review on its pull request's
branch, so its stale_after does not date anything in docs/.

    GH_TOKEN=... python3 stale.py ROOT
"""

import argparse
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import book

NOTICE = timedelta(days=7)


def issues(pages, existing, now):
    """The title and body of an issue for each of `pages` that is a draft,
    not a stub, stale no later than `now + NOTICE` and not yet raised in
    `existing`, the issues as `gh issue list --json title,state` gives
    them."""
    out = []
    for name, text in pages.items():
        fields = book.check(name, text)
        if fields["status"] != "draft" or fields["type"] == "Stub":
            continue
        stale_after = fields["stale_after"]
        path = f"{book.DOCS}/{name}"
        title = f"{path} goes stale on {stale_after:%Y-%m-%d}"
        if stale_after - now > NOTICE or any(
            i["title"] == title
            or (i["state"] == "OPEN" and i["title"].partition(" ")[0] == path)
            for i in existing
        ):
            continue
        out.append(
            (
                title,
                f"`{path}` is a draft to be treated as possibly outdated from "
                f"{stale_after.isoformat()}. Review it, then move its "
                "`stale_after` later or change its `status`.",
            )
        )
    return out


def gh(*args):
    return subprocess.run(
        ["gh", *args], check=True, capture_output=True, text=True
    ).stdout


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("root", type=Path)
    root = p.parse_args(argv).root
    listed = gh("issue", "list", "--state=all", "--limit=1000", "--json=title,state")
    pages = book.read_pages(root / book.DOCS)
    now = datetime.now(timezone.utc)
    for title, body in issues(pages, json.loads(listed), now):
        print(gh("issue", "create", "--title", title, "--body", body), end="")


if __name__ == "__main__":
    main()
