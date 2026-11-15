import tts


def test_drops_frontmatter():
    assert tts.text("---\ntitle: Scrubber\nstatus: draft\n---\n\nBody text.\n") == "Body text."


def test_drops_fenced_blocks_of_any_kind():
    markdown = (
        "Before.\n\n"
        "```mermaid\nsequenceDiagram\n  A->>B: hi\n```\n\n"
        "````rust\nfn main() {}\n````\n\n"
        "~~~\nplain\n~~~\n\n"
        "After.\n")
    assert tts.text(markdown) == "Before.\nAfter."


def test_drops_html_and_math():
    markdown = (
        "<div class=\"note\">\n<p>Hidden</p>\n</div>\n\n"
        "A fee of $f$ per input.\n\n"
        "$$\nx = y\n$$\n\n"
        "Text with <br> a tag.\n")
    assert tts.text(markdown) == "A fee of per input.\nText with a tag."


def test_keeps_link_and_inline_code_text():
    markdown = "See [BIP 370](https://example.com/370) and the `PSBT_IN_SIGHASH` field.\n"
    assert tts.text(markdown) == "See BIP 370 and the PSBT_IN_SIGHASH field."


def test_drops_images_tables_and_footnote_definitions():
    markdown = (
        "Intro.[^1]\n\n"
        "![diagram](d.svg)\n\n"
        "| Field | Kept |\n|---|---|\n| a | b |\n\n"
        "[^1]: A note.\n")
    assert tts.text(markdown) == "Intro."


def test_drops_tables_without_outer_pipes():
    markdown = (
        "Fields:\n\n"
        "`<keytype>` | PSBT version | BIP |\n"
        "--- | --- | --- |\n"
        "`PSBT_GLOBAL_XPUB = 0x01` | 0, 2 | [174](https://example.com) |\n\n"
        "After.\n")
    assert tts.text(markdown) == "Fields:\nAfter."


def test_headings_and_list_items_are_units():
    markdown = "## Trust scope\n\n- Creator\n- Signer\n\n1. First\n2. Second\n"
    assert tts.text(markdown) == "Trust scope.\nCreator.\nSigner.\nFirst.\nSecond."


def test_wrapped_paragraph_lines_join():
    assert tts.text("One sentence\nwrapped over\nthree lines.\n") == (
        "One sentence wrapped over three lines.")


def test_no_text():
    assert tts.text("---\ntitle: Stub\n---\n\n```mermaid\nA\n```\n") == ""


def test_name_depends_only_on_text():
    assert tts.name("Hello.") == tts.name("Hello.")
    assert tts.name("Hello.") != tts.name("Hello!")
    assert len(tts.name("Hello.")) == 16
