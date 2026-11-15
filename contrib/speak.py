#!/usr/bin/env python3
"""Read a text aloud with Kokoro.

    python3 speak.py TEXT VOICE OUT

reads the text file TEXT to the FLAC file OUT, taking the model from
KOKORO_CONFIG, KOKORO_MODEL and KOKORO_VOICES (a directory of <voice>.pt
files). It lives apart from tts.py so that changes there leave the rendered
sections cached.
"""
import os
import sys
from pathlib import Path

import numpy
import soundfile
import torch
from kokoro import KModel, KPipeline


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    text, voice, out = Path(sys.argv[1]).read_text(), sys.argv[2], sys.argv[3]
    model = KModel(repo_id="hexgrad/Kokoro-82M",
                   config=os.environ["KOKORO_CONFIG"], model=os.environ["KOKORO_MODEL"])
    # The voice's first letter is its language: a for American, b for British
    # English.
    pipeline = KPipeline(lang_code=voice[0], repo_id="hexgrad/Kokoro-82M", model=model)
    pack = torch.load(Path(os.environ["KOKORO_VOICES"]) / (voice + ".pt"), weights_only=True)
    audio = [a for _, _, a in pipeline(text, voice=pack, speed=1) if a is not None]
    soundfile.write(out, numpy.concatenate(audio), 24000, format="FLAC")


if __name__ == "__main__":
    main()
