import json

import jupyter_nb

NOTEBOOK = {"cells": [{"cell_type": "markdown", "metadata": {}, "source": ["# Nb\n"]}]}


def chapter(path, content, sub_items=()):
    return {"Chapter": {"path": path, "source_path": path, "content": content, "sub_items": list(sub_items)}}


def test_chapters_skip_separators_and_part_titles():
    items = [
        {"PartTitle": "Part"},
        chapter("one.md", "", [chapter("sub/two.md", "")]),
        "Separator",
        chapter("three.md", ""),
    ]
    assert [c["path"] for c in jupyter_nb.chapters(items)] == ["one.md", "sub/two.md", "three.md"]


def test_links_to_notebook_chapters_point_at_their_md_path(monkeypatch, capsys):
    items = [
        chapter("nb.ipynb", json.dumps(NOTEBOOK)),
        "Separator",
        chapter("sub/page.md", "[a](../nb.ipynb#x) [b](other.ipynb)\n\n[c]: ../nb.ipynb\n"),
    ]
    monkeypatch.setattr("sys.argv", ["jupyter_nb.py"])
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(json.dumps([{}, {"items": items}])))
    jupyter_nb.main()
    out = json.loads(capsys.readouterr().out)["items"]
    assert out[0]["Chapter"]["content"] == "# Nb\n"
    assert out[2]["Chapter"]["content"] == "[a](../nb.md#x) [b](other.ipynb)\n\n[c]: ../nb.md\n"
