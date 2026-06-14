import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import texttospeech
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_VOICES = {
    "en-US": "en-US-Neural2-J",
}

TTS_MAX_BYTES = 4800

_client: texttospeech.TextToSpeechClient | None = None


def _get_client() -> texttospeech.TextToSpeechClient:
    global _client
    if _client is None:
        _client = texttospeech.TextToSpeechClient()
    return _client


def _pick_voice(language_code: str) -> str:
    override = os.getenv("TTS_VOICE", "").strip()
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


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=20),
    reraise=True,
)
def _synthesize_chunk(chunk: str, language_code: str, voice_name: str) -> bytes:
    response = _get_client().synthesize_speech(
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
    return response.audio_content


def _merge_mp3(audio_parts: list[bytes]) -> bytes:
    if len(audio_parts) == 1:
        return audio_parts[0]
    if shutil.which("ffmpeg") is None:
        logger.warning("ffmpeg not found, falling back to byte concat for MP3")
        return b"".join(audio_parts)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        list_lines: list[str] = []
        for index, part in enumerate(audio_parts):
            part_path = tmp_path / f"part_{index}.mp3"
            part_path.write_bytes(part)
            list_lines.append(f"file '{part_path}'")

        list_path = tmp_path / "list.txt"
        list_path.write_text("\n".join(list_lines), encoding="utf-8")
        output_path = tmp_path / "merged.mp3"

        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_path),
                "-c",
                "copy",
                str(output_path),
            ],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace")[:300]
            logger.warning("ffmpeg merge failed (%s), falling back to byte concat", stderr)
            return b"".join(audio_parts)
        return output_path.read_bytes()


def synthesize_speech(text: str, language_code: str = "en-US") -> bytes:
    voice_name = _pick_voice(language_code)
    chunks = _split_for_tts(text)
    logger.info("Synthesizing %d TTS chunk(s)", len(chunks))
    audio_parts = [
        _synthesize_chunk(chunk, language_code, voice_name) for chunk in chunks
    ]
    return _merge_mp3(audio_parts)
