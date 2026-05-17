"""
MyannAI SaaS — Configuration
All settings loaded from .env file.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parents[1]
STORAGE  = BASE_DIR / "storage"

class Config:
    # Gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # TTS — edge-tts (no API key needed)
    # Uses Microsoft Edge's neural voices: my-MM-ThihaNeural, my-MM-NilarNeural
    TTS_MYANMAR_MALE   = "my-MM-ThihaNeural"
    TTS_MYANMAR_FEMALE = "my-MM-NilarNeural"

    # Whisper
    WHISPER_MODEL  = os.getenv("WHISPER_MODEL", "medium")
    WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cuda")

    # Storage
    UPLOADS_DIR = STORAGE / "uploads"
    QUEUE_DIR   = STORAGE / "queue"
    OUTPUTS_DIR = STORAGE / "outputs"
    DB_PATH     = STORAGE / "jobs.db"

    # Cleanup
    OUTPUT_TTL_DAYS = int(os.getenv("OUTPUT_TTL_DAYS", "7"))

    # ffmpeg
    FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")

    # Video output
    VIDEO_WIDTH  = 1080
    VIDEO_HEIGHT = 1920
    VIDEO_FPS    = 30

    @classmethod
    def ensure_dirs(cls):
        for d in [cls.UPLOADS_DIR, cls.QUEUE_DIR, cls.OUTPUTS_DIR]:
            d.mkdir(parents=True, exist_ok=True)

cfg = Config()
cfg.ensure_dirs()
