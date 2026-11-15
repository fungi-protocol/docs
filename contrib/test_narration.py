import narration
import tts


CHAPTER = "## Trust scope\n\nEvery PSBT role inside it may observe the full PSBT.\n"


def render(audio_dir, voice, content):
    mp3 = tts.name(tts.text(content)) + ".mp3"
    (audio_dir / voice).mkdir(parents=True, exist_ok=True)
    (audio_dir / voice / mp3).write_bytes(b"mp3")
    return mp3


def chapter(content):
    return {"name": "Scrubber", "content": content, "sub_items": []}


CONTEXT = {"config": {"output": {"html": {"site-url": "/docs/"}}}}


def test_one_player_per_rendered_voice(tmp_path):
    mp3 = render(tmp_path, "af_heart", CHAPTER)
    render(tmp_path, "bf_emma", CHAPTER)
    item = chapter(CHAPTER)
    narration.narrate(item, tmp_path, "/docs/")
    assert item["content"] == (
        '<div class="narration">\n'
        f'<audio controls preload="none" title="af_heart" src="/docs/tts/af_heart/{mp3}"></audio>\n'
        f'<audio controls preload="none" title="bf_emma" src="/docs/tts/bf_emma/{mp3}"></audio>\n'
        '</div>\n\n'
        + CHAPTER)


def test_player_carries_the_section_starts(tmp_path):
    mp3 = render(tmp_path, "af_heart", CHAPTER)
    (tmp_path / "af_heart" / mp3).with_suffix(".json").write_text(
        '[{"title": "Trust scope", "start": 0.0}]')
    item = chapter(CHAPTER)
    narration.narrate(item, tmp_path, "/docs/")
    assert ('<audio controls preload="none" title="af_heart" data-sections='
            '"[{&quot;title&quot;: &quot;Trust scope&quot;, &quot;start&quot;: 0.0}]" '
            f'src="/docs/tts/af_heart/{mp3}"></audio>') in item["content"]


def test_text_not_rendered_gets_no_player(tmp_path):
    render(tmp_path, "af_heart", "Other text.")
    item = chapter(CHAPTER)
    narration.narrate(item, tmp_path, "/docs/")
    assert item["content"] == CHAPTER


def test_no_player_for_a_chapter_without_text(tmp_path):
    (tmp_path / "af_heart").mkdir()
    item = chapter("```mermaid\nA\n```\n")
    narration.narrate(item, tmp_path, "/docs/")
    assert item["content"] == "```mermaid\nA\n```\n"


def test_walk_defaults_to_the_root_without_site_url(tmp_path, monkeypatch):
    mp3 = render(tmp_path, "af_heart", CHAPTER)
    monkeypatch.setenv("TTS_AUDIO_DIR", str(tmp_path))
    book = {"items": [{"Chapter": chapter(CHAPTER)}]}
    narration.walk_book({"config": {}}, book)
    assert f'src="/tts/af_heart/{mp3}"' in book["items"][0]["Chapter"]["content"]


def test_walk_without_audio_dir_changes_nothing(monkeypatch):
    monkeypatch.setenv("TTS_AUDIO_DIR", "")
    book = {"items": [{"Chapter": chapter(CHAPTER)}, "Separator"]}
    narration.walk_book(CONTEXT, book)
    assert book["items"][0]["Chapter"]["content"] == CHAPTER


def test_walk_reaches_sub_chapters(tmp_path, monkeypatch):
    render(tmp_path, "af_heart", CHAPTER)
    monkeypatch.setenv("TTS_AUDIO_DIR", str(tmp_path))
    child = chapter(CHAPTER)
    book = {"items": [{"Chapter": dict(chapter("Short."), sub_items=[{"Chapter": child}])}]}
    narration.walk_book(CONTEXT, book)
    assert child["content"].startswith('<div class="narration">')
