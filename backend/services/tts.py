"""
TTS Service
- Myanmar: edge-tts (my-MM-ThihaNeural / my-MM-NilarNeural)
  Free, no API key, same neural voices as Azure.
  Uses Microsoft Edge Read Aloud API under the hood.
- English: Kokoro local → edge-tts fallback → gTTS last resort
"""
import asyncio
import subprocess
import tempfile
from pathlib import Path
from backend.config import cfg

# Myanmar neural voices via edge-tts (no Azure account needed)
MYANMAR_VOICES = {
    "male":   "my-MM-ThihaNeural",   # deep, confident narrator
    "female": "my-MM-NilarNeural",   # clear, warm
}


async def _edge_tts_async(text: str, voice: str, out_path: Path,
                           rate: str = "+0%", pitch: str = "+0Hz") -> None:
    """Run edge-tts with the given voice."""
    import edge_tts
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=pitch,
    )
    await communicate.save(str(out_path))


def _run_edge_tts(text: str, voice: str, out_path: Path,
                   rate: str = "+0%", pitch: str = "+0Hz") -> None:
    """Thread-safe wrapper — creates a fresh event loop."""
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(
            _edge_tts_async(text, voice, out_path, rate, pitch)
        )
    finally:
        loop.close()


def _speed_to_rate(speed: float) -> str:
    """Convert 0.7–1.3 speed to edge-tts rate string like +10% or -15%."""
    pct = int((speed - 1.0) * 100)
    return f"{pct:+d}%"


def _pitch_to_hz(pitch: str) -> str:
    """Convert low/normal/high to edge-tts pitch string."""
    return {"low": "-10Hz", "normal": "+0Hz", "high": "+10Hz"}.get(pitch, "+0Hz")


def generate_myanmar_audio(script: str, out_path: Path,
                            gender: str = "male",
                            speed: float = 1.0,
                            pitch: str = "normal") -> Path:
    """
    Generate Myanmar neural TTS using edge-tts.
    Uses my-MM-ThihaNeural (male) or my-MM-NilarNeural (female).
    No API key or Azure account required.
    """
    voice    = MYANMAR_VOICES.get(gender, MYANMAR_VOICES["male"])
    rate_str = _speed_to_rate(speed)
    pitch_str = _pitch_to_hz(pitch)

    print(f"[TTS] Myanmar voice: {voice} | rate: {rate_str} | pitch: {pitch_str}")

    try:
        _run_edge_tts(script, voice, out_path, rate=rate_str, pitch=pitch_str)
        if out_path.exists() and out_path.stat().st_size > 1000:
            print(f"[TTS] Myanmar audio saved ({out_path.stat().st_size // 1024} KB)")
            return out_path
        raise RuntimeError("edge-tts produced empty or too-small file")
    except Exception as e:
        print(f"[TTS] edge-tts Myanmar failed ({e}), falling back to gTTS")
        return _gtts_myanmar(script, out_path)


def _gtts_myanmar(script: str, out_path: Path) -> Path:
    """gTTS fallback for Myanmar (robotic but always works)."""
    from gtts import gTTS
    gTTS(text=script, lang="my", slow=False).save(str(out_path))
    print(f"[TTS] gTTS Myanmar fallback saved ({out_path.stat().st_size // 1024} KB)")
    return out_path


def generate_english_audio(script: str, out_path: Path,
                            gender: str = "male",
                            speed: float = 1.0) -> Path:
    """
    Generate English TTS.
    Try order: Kokoro (local GPU) → edge-tts EN → gTTS EN
    """
    # 1. Try Kokoro (best quality, local)
    try:
        import soundfile as sf
        import numpy as np
        from kokoro import KPipeline

        print("[TTS] Trying Kokoro for English...")
        pipe   = KPipeline(lang_code='a')
        voice  = 'af_heart' if gender == 'female' else 'am_adam'
        chunks = []
        for _, _, audio in pipe(script, voice=voice, speed=speed, split_pattern=r'\n+'):
            chunks.append(audio)

        if chunks:
            full = np.concatenate(chunks)
            wav  = out_path.with_suffix('.wav')
            sf.write(str(wav), full, 24000)
            subprocess.run(
                [cfg.FFMPEG_PATH, "-y", "-i", str(wav),
                 "-codec:a", "libmp3lame", "-b:a", "192k", str(out_path)],
                capture_output=True
            )
            wav.unlink(missing_ok=True)
            if out_path.exists() and out_path.stat().st_size > 1000:
                print(f"[TTS] Kokoro English saved ({out_path.stat().st_size // 1024} KB)")
                return out_path
    except Exception as e:
        print(f"[TTS] Kokoro failed ({e})")

    # 2. Try edge-tts English neural voice
    try:
        en_voice = "en-US-AriaNeural" if gender == "female" else "en-US-GuyNeural"
        print(f"[TTS] Trying edge-tts English: {en_voice}")
        _run_edge_tts(script, en_voice, out_path, rate=_speed_to_rate(speed))
        if out_path.exists() and out_path.stat().st_size > 1000:
            print(f"[TTS] edge-tts English saved ({out_path.stat().st_size // 1024} KB)")
            return out_path
    except Exception as e:
        print(f"[TTS] edge-tts English failed ({e})")

    # 3. gTTS last resort
    print("[TTS] Using gTTS English fallback")
    from gtts import gTTS
    gTTS(text=script, lang='en', slow=False).save(str(out_path))
    return out_path
