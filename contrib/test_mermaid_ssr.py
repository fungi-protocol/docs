import hashlib

import mermaid_ssr
import pytest

SOURCE = "flowchart LR\n  a --> b\n"


def prerender(tmp_path, source, theme, svg):
    diagram = tmp_path / hashlib.sha256(source.encode()).hexdigest()
    diagram.mkdir(exist_ok=True)
    (diagram / (theme + ".svg")).write_text(svg)


def test_prerendered_diagram_gets_its_own_id(tmp_path, monkeypatch):
    prerender(tmp_path, SOURCE, "dark",
              '<svg id="MERMAID_SSR_ID"><style>#MERMAID_SSR_ID{}</style></svg>')
    monkeypatch.setenv("MERMAID_SVG_DIR", str(tmp_path))
    assert mermaid_ssr.render(SOURCE, "dark", "mermaid-3-dark") == (
        '<svg id="mermaid-3-dark"><style>#mermaid-3-dark{}</style></svg>')


def test_diagram_missing_from_the_prerendered_set_fails(tmp_path, monkeypatch):
    prerender(tmp_path, SOURCE, "default", "<svg/>")
    monkeypatch.setenv("MERMAID_SVG_DIR", str(tmp_path))
    with pytest.raises(SystemExit):
        mermaid_ssr.render(SOURCE + "  b --> c\n", "default", "mermaid-1-light")
