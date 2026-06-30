"""
tts.py
=== ADDITION 2: VOICEOVER GENERATION (audio half) ===

Uses gTTS (Google Text-to-Speech) — free, no API key required, good enough
for a homework-grade voiceover. Audio is synthesized to a BytesIO buffer so
it can be played with st.audio() and offered via st.download_button as .mp3,
with no temp files left on disk.

SWAP-IN POINT: if you have an OpenAI or ElevenLabs API key and want higher
quality voices, replace the body of synthesize_voiceover() — the function
signature (str -> bytes) stays the same, so nothing else in the app needs
to change. An OpenAI TTS version is sketched in the comment at the bottom.
"""

import io
from gtts import gTTS


def synthesize_voiceover(script_text: str, lang: str = "en") -> bytes:
    """
    Converts a voiceover script to MP3 audio bytes.

    Args:
        script_text: the TTS-ready script (already punctuation-adapted
                      by engine.generate_voiceover_script()).
        lang: gTTS language code.

    Returns:
        Raw MP3 bytes, ready for st.audio() / st.download_button().
    """
    if not script_text or not script_text.strip():
        raise ValueError("Cannot synthesize empty voiceover script.")

    buffer = io.BytesIO()
    tts = gTTS(text=script_text, lang=lang, slow=False)
    tts.write_to_fp(buffer)
    buffer.seek(0)
    return buffer.read()


# ---------------------------------------------------------------------------
# OPTIONAL SWAP-IN: OpenAI TTS instead of gTTS
# ---------------------------------------------------------------------------
# import requests
# import streamlit as st
#
# def synthesize_voiceover(script_text: str, lang: str = "en") -> bytes:
#     resp = requests.post(
#         "https://api.openai.com/v1/audio/speech",
#         headers={"Authorization": f"Bearer {st.secrets['OPENAI_API_KEY']}"},
#         json={"model": "tts-1", "voice": "alloy", "input": script_text},
#         timeout=60,
#     )
#     resp.raise_for_status()
#     return resp.content