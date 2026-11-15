#!/usr/bin/env python3
"""An mdbook preprocessor that puts the narration's audio players in the book.

If TTS_AUDIO_DIR is set, it puts a block of audio elements at the top of
every chapter, one for each voice whose TTS_AUDIO_DIR/<voice>/<name>.mp3
exists, as nix/tts.nix renders them, with the start of each section from
TTS_AUDIO_DIR/<voice>/<name>.json. A chapter whose text was not rendered,
like the generated contents page, gets none. Otherwise it changes nothing.
theme/narration.js turns the block into a floating player.

It lives apart from tts.py, which renders the audio, so that changing the
player does not re-render the book.
"""
import html
import json
import os
import sys
from pathlib import Path

import tts


def narrate(chapter, audio_dir, site_url):
    """Put an audio player per rendered voice at the top of the chapter.

    The player links its audio from SITE_URL, as the print page holds every
    chapter at the root whatever the depth of its source.
    """
    spoken = tts.text(chapter["content"])
    if not spoken:
        return
    mp3 = tts.name(spoken) + ".mp3"
    players = [
        player(voice, mp3, site_url)
        for voice in sorted(Path(audio_dir).iterdir())
        if (voice / mp3).exists()
    ]
    if players:
        chapter["content"] = (
            '<div class="narration">\n' + "\n".join(players) + "\n</div>\n\n" + chapter["content"])


def player(voice, mp3, site_url):
    starts = (voice / mp3).with_suffix(".json")
    sections = (
        f' data-sections="{html.escape(starts.read_text())}"' if starts.exists() else "")
    return (f'<audio controls preload="none" title="{voice.name}"{sections} '
            f'src="{site_url}tts/{voice.name}/{mp3}"></audio>')


def walk_book(context, book):
    audio_dir = os.environ.get("TTS_AUDIO_DIR")
    if not audio_dir:
        return
    site_url = context["config"].get("output", {}).get("html", {}).get("site-url", "/")

    def walk(items):
        for item in items:
            chapter = item.get("Chapter") if isinstance(item, dict) else None
            if chapter:
                narrate(chapter, audio_dir, site_url)
                walk(chapter["sub_items"])

    # mdbook 0.5 renamed the top level key from `sections` to `items`.
    walk(book.get("items", book.get("sections")))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "supports":
        sys.exit(0)
    context, book = json.load(sys.stdin)
    walk_book(context, book)
    json.dump(book, sys.stdout)


if __name__ == "__main__":
    main()
