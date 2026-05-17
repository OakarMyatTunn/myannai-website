# MyannAI SaaS

AI-powered video recap and dubbing platform for Myanmar content creators.

## Stack
- **Backend:** FastAPI + Python + SQLite + RQ
- **Frontend:** React + Vite + Tailwind
- **AI:** Whisper (transcription) + Gemini (scripts) + Azure Neural TTS (Myanmar voice)
- **Video:** ffmpeg (assembly, effects, overlays)

## Features
- YouTube / TikTok / Facebook / Instagram / Xiaohongshu URL input
- 6 script styles: Standard, Story, Quick, Dramatic, Comedy, Educational
- Natural Myanmar voice (Azure Neural TTS)
- Natural English voice (Kokoro local)
- 9:16 auto-crop, flip, auto color grade
- Copyright bypass processing
- Burned subtitles
- Custom blur mask (draw regions to blur)
- Logo watermark
- Intro / Outro video support
- 7-day auto-delete storage
- Real-time job progress

## Setup
See `docs/SETUP.md`

## Run
```bash
# Backend
cd backend && uvicorn main:app --reload --port 8000

# Frontend
cd frontend && npm run dev
```
