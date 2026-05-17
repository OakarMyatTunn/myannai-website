"""
Assets API — upload logo, intro, outro.
"""
import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.models import save_asset, get_asset, list_assets
from backend.config import cfg

router = APIRouter(prefix="/api/assets", tags=["assets"])

ALLOWED_IMAGE = {".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_VIDEO = {".mp4", ".mov", ".avi", ".mkv"}


@router.get("")
def get_all_assets():
    return list_assets()


@router.post("/logo")
async def upload_logo(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_IMAGE:
        raise HTTPException(400, f"Logo must be an image: {ALLOWED_IMAGE}")
    path = cfg.UPLOADS_DIR / f"logo_{uuid.uuid4()}{ext}"
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return save_asset("logo", file.filename, str(path))


@router.post("/intro")
async def upload_intro(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_VIDEO:
        raise HTTPException(400, f"Intro must be a video: {ALLOWED_VIDEO}")
    path = cfg.UPLOADS_DIR / f"intro_{uuid.uuid4()}{ext}"
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return save_asset("intro", file.filename, str(path))


@router.post("/outro")
async def upload_outro(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_VIDEO:
        raise HTTPException(400, f"Outro must be a video: {ALLOWED_VIDEO}")
    path = cfg.UPLOADS_DIR / f"outro_{uuid.uuid4()}{ext}"
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return save_asset("outro", file.filename, str(path))


@router.get("/{asset_type}")
def get_asset_info(asset_type: str):
    asset = get_asset(asset_type)
    if not asset:
        raise HTTPException(404, f"No {asset_type} uploaded yet")
    return asset
