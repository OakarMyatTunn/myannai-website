"""
TTS Service
- Myanmar: Azure Neural TTS (my-MM-ThihaNeural / my-MM-NilarNeural)
- English: Kokoro local → gTTS fallback
"""
import subprocess
import tempfile
from pathlib import Path
from backend.config import cfg


def generate_myanmar_audio(script: str, out_path: Path,
                           gender: str = "male",
                           speed: float = 1.0,
                           pitch: str = "normal") -> Path:
    """Azure Neural TTS for Myanmar."""
    voice = cfg.AZURE_VOICE_MALE if gender == "male" else cfg.AZURE_VOICE_FEMALE

    # Pitch map
    pitch_map = {"low": "-10%", "normal": "0%", "high": "+10%"}
    pitch_str = pitch_map.get(pitch, "0%")
    rate_str  = f"{int((speed - 1.0) * 100):+d}%"

    ssml = f"""<speak version='1.0' xml:lang='my-MM'>
  <voice name='{voice}'>
    <prosody rate='{rate_str}' pitch='{pitch_str}'>
      {script}
    </prosody>
  </voice>
</speak>"""

    try:
        import azure.cognitiveservices.speech as speechsdk

        speech_config = speechsdk.SpeechConfig(
            subscription=cfg.AZURE_SPEECH_KEY,
            region=cfg.AZURE_SPEECH_REGION,
        )
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3
        )
        audio_config = speechsdk.audio.AudioOutputConfig(filename=str(out_path))
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config,
        )
        result = synthesizer.speak_ssml_async(ssml).get()
        if result.reason.name != "SynthesizingAudioCompleted":
            raise RuntimeError(f"Azure TTS failed: {result.reason}")
        return out_path

    except ImportError:
        # Azure SDK not installed — fall back to gTTS
        return _gtts_myanmar(script, out_path)
    except Exception as e:
        # Azure failed (no key yet, quota, etc.) — fall back to gTTS
        print(f"[TTS] Azure failed ({e}), using gTTS fallback")
        return _gtts_myanmar(script, out_path)


def _gtts_myanmar(script: str, out_path: Path) -> Path:
    from gtts import gTTS
    tts = gTTS(text=script, lang="my", slow=False)
    tts.save(str(out_path))
    return out_path


def generate_english_audio(script: str, out_path: Path,
                            speed: float = 1.0) -> Path:
    """Kokoro local TTS for English → gTTS fallback."""
    try:
        import soundfile as sf
        import numpy as np
        from kokoro import KPipeline

        pipe = KPipeline(lang_code='a')
        chunks = []
        for _, _, audio in pipe(script, voice='af_heart',
                                 speed=speed, split_pattern=r'\n+'):
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
            if out_path.exists():
                return out_path
    except Exception as e:
        print(f"[TTS] Kokoro failed ({e}), using gTTS")

    from gtts import gTTS
    gTTS(text=script, lang='en', slow=False).save(str(out_path))
    return out_path
