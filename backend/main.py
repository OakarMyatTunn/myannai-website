"""
MyannAI SaaS — FastAPI Backend
Run: uvicorn backend.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from backend.models import init_db
from backend.routers import jobs, assets

# Init DB on startup
init_db()

app = FastAPI(title="MyannAI SaaS API", version="1.0.0")

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000",
                   "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(jobs.router)
app.include_router(assets.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "MyannAI SaaS"}


# Serve output files for video preview
outputs_dir = Path("storage/outputs")
outputs_dir.mkdir(parents=True, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=str(outputs_dir)), name="outputs")
