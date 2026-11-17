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


def test_drops_display_math_inside_a_list_item():
    assert tts.text("1. A bound:\n   $$\n   x = y\n   $$\n") == "A bound:"


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


def test_keeps_the_paragraph_after_an_autolink():
    markdown = "Published at\n<https://example.com/>. Its index follows.\n"
    assert tts.text(markdown) == "Published at . Its index follows."


def test_drops_indented_code_and_link_reference_definitions():
    markdown = "See [BIP 370][370].\n\n    let x = 1;\n\n[370]: https://example.com/370\n"
    assert tts.text(markdown) == "See BIP 370."


def test_reads_underlined_headings_escapes_and_entities():
    markdown = "Fees\n====\n\nA \\*literal\\* star, __strong__ &amp; snake_case.\n"
    assert tts.text(markdown) == "Fees.\nA *literal* star, strong & snake_case."


def test_reads_an_alert_marker_as_its_title():
    assert tts.text("> [!warning]\n> Careful.\n") == "Warning.\nCareful."


def test_reads_the_title_of_an_alert_with_nothing_else_to_read():
    assert tts.text("> [!NOTE]\n\n> [!TIP]\n> ![diagram](d.svg)\n") == "Note.\nTip."


def test_reads_a_marker_that_starts_no_alert():
    """mdbook renders these markers as text: one shares its line, one is past
    the blockquote's first paragraph."""
    assert tts.text("> [!NOTE] Inline.\n\n> Lead.\n>\n> [!TIP]\n> Later.\n") == (
        "[!NOTE] Inline.\nLead.\n[!TIP] Later.")


def test_sections_cut_before_headings():
    markdown = "Lead.\n\n## Trust scope\n\nFirst.\n\n- Item\n\n### Roles\n\nSecond.\n"
    assert tts.sections(markdown) == [
        {"title": "", "level": 0, "text": "Lead."},
        {"title": "Trust scope", "level": 2, "text": "Trust scope.\nFirst.\nItem."},
        {"title": "Roles", "level": 3, "text": "Roles.\nSecond."},
    ]


def test_sections_join_to_the_text():
    markdown = "# Title\n\nOne.\n\n```\n# not a heading\n```\n\n## Next\n\nTwo.\n"
    assert "\n".join(s["text"] for s in tts.sections(markdown)) == tts.text(markdown)
    assert [s["title"] for s in tts.sections(markdown)] == ["Title", "Next"]


def test_no_sections_without_text():
    assert tts.sections("```mermaid\nA\n```\n") == []


def test_starts_add_up_durations():
    cut = [{"title": t, "level": 2, "text": ""} for t in "ABC"]
    assert tts.starts(cut, [1.5, 2.25, 3]) == [
        {"title": "A", "level": 2, "start": 0.0},
        {"title": "B", "level": 2, "start": 1.5},
        {"title": "C", "level": 2, "start": 3.75},
    ]
