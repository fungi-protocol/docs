import base64
import hashlib
import xml.etree.ElementTree as ET

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


def test_pandoc_uses_pdf_labels_with_spaces_and_decoded_entities(tmp_path, monkeypatch):
    prerender(tmp_path, SOURCE, "pdf", (
        '<svg xmlns="http://www.w3.org/2000/svg" id="MERMAID_SSR_ID"><text>'
        "<tspan>Bob's</tspan><tspan> change</tspan><tspan> 0.1</tspan>"
        '<tspan>&amp;nbsp;?&amp;nbsp;</tspan></text></svg>'
    ))
    monkeypatch.setenv("MERMAID_SVG_DIR", str(tmp_path))
    markdown = mermaid_ssr.image(SOURCE, 2)
    encoded = markdown.split("base64,", 1)[1].split(")", 1)[0]
    svg = ET.fromstring(base64.b64decode(encoded))
    assert svg.attrib["id"] == "mermaid-2"
    assert svg.attrib["{http://www.w3.org/XML/1998/namespace}space"] == "preserve"
    assert "".join(svg.itertext()) == "Bob's change 0.1\u00a0?\u00a0"
