import os
import re

from dotenv import load_dotenv
from google.cloud import texttospeech

load_dotenv()

DEFAULT_VOICES = {
    "en-US": "en-US-Neural2-J",
}

TTS_MAX_BYTES = 4800


def _pick_voice(language_code: str) -> str:
    override = os.getenv("TTS_VOICE")
    if override:
        return override
    return DEFAULT_VOICES.get(language_code, DEFAULT_VOICES["en-US"])


def _split_for_tts(text: str, max_bytes: int = TTS_MAX_BYTES) -> list[str]:
    text = re.sub(r"\n{2,}", "\n\n", text.strip())
    if len(text.encode("utf-8")) <= max_bytes:
        return [text]

    chunks: list[str] = []
    paragraphs = text.split("\n\n")
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate.encode("utf-8")) <= max_bytes:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = paragraph
        else:
            sentences = re.split(r"(?<=[.!?])\s+", paragraph)
            buffer = ""
            for sentence in sentences:
                candidate = f"{buffer} {sentence}".strip() if buffer else sentence
                if len(candidate.encode("utf-8")) <= max_bytes:
                    buffer = candidate
                else:
                    if buffer:
                        chunks.append(buffer)
                    buffer = sentence
            if buffer:
                current = buffer

    if current:
        chunks.append(current)

    return chunks or [text[:max_bytes]]


def synthesize_speech(text: str, language_code: str = "en-US") -> bytes:
    client = texttospeech.TextToSpeechClient()
    voice_name = _pick_voice(language_code)
    chunks = _split_for_tts(text)
    audio_parts: list[bytes] = []

    for chunk in chunks:
        response = client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=chunk),
            voice=texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name,
            ),
            audio_config=texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.0,
            ),
        )
        audio_parts.append(response.audio_content)

    return b"".join(audio_parts)
