# MyannAI SaaS — Setup Guide

## Requirements
- Python 3.11+
- Node.js 18+
- ffmpeg installed and in PATH (or set FFMPEG_PATH in .env)
- NVIDIA GPU with CUDA (for Whisper)

## Step 1 — Clone & configure
```cmd
git clone https://github.com/OakarMyatTunn/myannai-website.git myannai-saas
cd myannai-saas
copy .env.example .env
notepad .env
```

Fill in:
- `GEMINI_API_KEY` — from aistudio.google.com
- `AZURE_SPEECH_KEY` — from portal.azure.com (Speech resource)
- `AZURE_SPEECH_REGION` — e.g. southeastasia

## Step 2 — Backend setup
```cmd
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install azure-cognitiveservices-speech
```

## Step 3 — Frontend setup
```cmd
cd frontend
npm install
```

## Step 4 — Run
Open two terminals:

Terminal 1 (Backend):
```cmd
cd backend
venv\Scripts\activate
uvicorn backend.main:app --reload --port 8000
```

Terminal 2 (Frontend):
```cmd
cd frontend
npm run dev
```

Open http://localhost:5173

## TTS Setup
No setup needed! Myanmar neural voice (my-MM-ThihaNeural / my-MM-NilarNeural)
uses Microsoft Edge's Read Aloud API via edge-tts library.
- No API key required
- No Azure account required  
- Same neural voice quality as Azure Cognitive Services
- Free and unlimited for personal use

## Notes
- Videos stored in storage/outputs/ — auto-deleted after 7 days
- Processing runs in background — refresh job page to see progress
- GPU required for fast Whisper transcription
