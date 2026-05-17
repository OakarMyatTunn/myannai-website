"""
Jobs API router — CRUD + file upload + download.
"""
import json
import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from backend.models import (
    create_job, get_job, list_jobs, update_job,
    delete_job, cleanup_expired_jobs
)
from backend.config import cfg

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class JobCreate(BaseModel):
    source_url:      Optional[str]   = None
    script_style:    str             = "standard"
    language:        str             = "myanmar"
    voice_gender:    str             = "male"
    voice_speed:     float           = 1.0
    voice_pitch:     str             = "normal"
    flip_video:      bool            = False
    auto_color:      bool            = True
    copyright_bypass: bool           = True
    subtitles:       bool            = True
    blur_masks:      list            = []
    logo:            bool            = False
    logo_path:       Optional[str]   = None
    intro:           bool            = False
    intro_path:      Optional[str]   = None
    outro:           bool            = False
    outro_path:      Optional[str]   = None


@router.get("")
def get_jobs():
    cleanup_expired_jobs()
    return list_jobs()


@router.post("")
def submit_job(payload: JobCreate, background_tasks: BackgroundTasks):
    """Submit a new job with URL source."""
    if not payload.source_url:
        raise HTTPException(400, "source_url is required for this endpoint")

    settings = payload.model_dump()
    settings.pop("source_url", None)

    job = create_job(source_url=payload.source_url, settings=settings)
    background_tasks.add_task(_run_job_bg, job["id"])
    return job


@router.post("/upload")
async def submit_job_with_file(
    background_tasks: BackgroundTasks,
    file:            UploadFile = File(...),
    script_style:    str        = Form("standard"),
    language:        str        = Form("myanmar"),
    voice_gender:    str        = Form("male"),
    voice_speed:     float      = Form(1.0),
    voice_pitch:     str        = Form("normal"),
    flip_video:      bool       = Form(False),
    auto_color:      bool       = Form(True),
    copyright_bypass: bool      = Form(True),
    subtitles:       bool       = Form(True),
    blur_masks:      str        = Form("[]"),
    logo:            bool       = Form(False),
    logo_path:       str        = Form(""),
    intro:           bool       = Form(False),
    intro_path:      str        = Form(""),
    outro:           bool       = Form(False),
    outro_path:      str        = Form(""),
):
    # Save uploaded file to queue
    ext      = Path(file.filename).suffix.lower()
    safe_name = f"{uuid.uuid4()}{ext}"
    dest     = cfg.QUEUE_DIR / safe_name

    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    settings = {
        "script_style":     script_style,
        "language":         language,
        "voice_gender":     voice_gender,
        "voice_speed":      voice_speed,
        "voice_pitch":      voice_pitch,
        "flip_video":       flip_video,
        "auto_color":       auto_color,
        "copyright_bypass": copyright_bypass,
        "subtitles":        subtitles,
        "blur_masks":       json.loads(blur_masks or "[]"),
        "logo":             logo,
        "logo_path":        logo_path or None,
        "intro":            intro,
        "intro_path":       intro_path or None,
        "outro":            outro,
        "outro_path":       outro_path or None,
    }

    job = create_job(source_file=str(dest), settings=settings)
    background_tasks.add_task(_run_job_bg, job["id"])
    return job


@router.get("/{job_id}")
def get_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.delete("/{job_id}")
def remove_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    # Delete output files
    out = job.get("output_file", "")
    if out:
        try:
            paths = json.loads(out) if out.startswith("[") else [out]
            for p in paths:
                Path(p).unlink(missing_ok=True)
        except Exception:
            Path(out).unlink(missing_ok=True)
    delete_job(job_id)
    return {"deleted": job_id}


@router.get("/{job_id}/download")
def download_job(job_id: str, lang: str = "myanmar"):
    job = get_job(job_id)
    if not job or job["status"] != "complete":
        raise HTTPException(404, "Job not ready")

    out = job.get("output_file", "")
    if not out:
        raise HTTPException(404, "No output file")

    # Handle both single path and JSON list
    if out.startswith("["):
        paths = json.loads(out)
        path  = next((p for p in paths if lang in p), paths[0])
    else:
        path = out

    if not Path(path).exists():
        raise HTTPException(404, "Output file missing")

    return FileResponse(
        path,
        media_type="video/mp4",
        filename=Path(path).name
    )


def _run_job_bg(job_id: str):
    """Run job in FastAPI background task (no Redis needed for personal use)."""
    try:
        from backend.services.worker import process_job
        process_job(job_id)
    except Exception as e:
        update_job(job_id, status="failed", step=f"Failed: {str(e)[:200]}")
