"""
Text-to-speech backend, powered by gTTS (Google Translate TTS).

gTTS is free and needs no API key, which makes it a great match for a
project people should be able to clone and run instantly. Its only real
limitation is a single voice per language, which is why two-host mode
uses a different Google Translate TLD per host to add a bit of variety.
"""

import io
from gtts import gTTS

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except Exception:  # pydub / ffmpeg missing
    PYDUB_AVAILABLE = False

from config import HOST_A_TLD, HOST_B_TLD


class AudioGenerationError(Exception):
    """Raised when text-to-speech synthesis fails."""
    pass


def synthesize_single(text: str, lang_code: str, slow: bool = False) -> bytes:
    """Converts a single block of text to MP3 bytes."""
    try:
        tts = gTTS(text=text, lang=lang_code, slow=slow)
        buffer = io.BytesIO()
        tts.write_to_fp(buffer)
        buffer.seek(0)
        return buffer.read()
    except Exception as exc:  # noqa: BLE001
        raise AudioGenerationError(f"Text-to-speech failed: {exc}") from exc


def synthesize_two_host(turns: list[tuple[str, str]], lang_code: str, slow: bool = False) -> bytes:
    """
    Converts a list of (speaker, line) turns into one stitched MP3, alternating
    a subtly different accent per host. Falls back to a single merged voice
    if pydub/ffmpeg isn't available in the environment.
    """
    if not turns:
        raise AudioGenerationError("No dialogue lines to synthesize.")

    if not PYDUB_AVAILABLE:
        # Graceful fallback: just read the whole script in one voice.
        full_text = " ".join(line for _, line in turns)
        return synthesize_single(full_text, lang_code, slow)

    try:
        combined = AudioSegment.silent(duration=200)
        pause = AudioSegment.silent(duration=280)

        for speaker, line in turns:
            if not line.strip():
                continue
            tld = HOST_A_TLD if speaker == "A" else HOST_B_TLD
            tts = gTTS(text=line, lang=lang_code, slow=slow, tld=tld)
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            segment = AudioSegment.from_file(buf, format="mp3")
            combined += segment + pause

        out_buffer = io.BytesIO()
        combined.export(out_buffer, format="mp3")
        out_buffer.seek(0)
        return out_buffer.read()
    except (FileNotFoundError, OSError):
        # pydub imported fine, but ffmpeg isn't installed/on PATH (common on
        # fresh Windows setups). Don't crash the episode — just fall back to
        # a single merged voice instead of true two-host stitching.
        full_text = " ".join(line for _, line in turns)
        return synthesize_single(full_text, lang_code, slow)
    except Exception as exc:  # noqa: BLE001
        raise AudioGenerationError(f"Text-to-speech failed: {exc}") from exc