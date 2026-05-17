"""
Job worker — runs the full pipeline for a single job.
Called by the RQ queue worker.
"""
import traceback
from pathlib import Path
from datetime import datetime
from backend.models import update_job, get_job
from backend.config import cfg


def process_job(job_id: str) -> None:
    """Full pipeline: download → transcribe → script → TTS → video."""

    def progress(pct: int, step: str):
        update_job(job_id, progress=pct, step=step)

    try:
        update_job(job_id, status="processing", progress=0, step="Starting...")
        job      = get_job(job_id)
        settings = job["settings"]
        language = settings.get("language", "myanmar")

        # ── Step 1: Get source video ──────────────────────────────────────────
        progress(2, "Downloading source video...")
        source_path = _get_source(job, settings)

        # ── Step 2: Transcribe ────────────────────────────────────────────────
        progress(10, "Transcribing audio...")
        from faster_whisper import WhisperModel
        model = WhisperModel(
            cfg.WHISPER_MODEL,
            device=cfg.WHISPER_DEVICE,
            compute_type="float16" if cfg.WHISPER_DEVICE == "cuda" else "int8"
        )
        segments_iter, info = model.transcribe(str(source_path), beam_size=5)
        transcript = " ".join(seg.text for seg in segments_iter).strip()
        del model  # free GPU memory

        # ── Step 3: Generate script ───────────────────────────────────────────
        progress(30, "Generating script...")
        from backend.services.scripter import generate_scripts
        style   = settings.get("script_style", "standard")
        scripts = generate_scripts(transcript, style)

        # ── Step 4: TTS ───────────────────────────────────────────────────────
        progress(50, "Generating voiceover...")
        from backend.services.tts import generate_myanmar_audio, generate_english_audio
        out_dir  = cfg.OUTPUTS_DIR / job_id
        out_dir.mkdir(parents=True, exist_ok=True)

        audio_paths = {}
        if language in ("myanmar", "both"):
            my_audio = out_dir / "voiceover_my.mp3"
            generate_myanmar_audio(
                scripts.get("myanmar", ""),
                my_audio,
                gender=settings.get("voice_gender", "male"),
                speed=float(settings.get("voice_speed", 1.0)),
                pitch=settings.get("voice_pitch", "normal"),
            )
            audio_paths["myanmar"] = my_audio

        if language in ("english", "both"):
            en_audio = out_dir / "voiceover_en.mp3"
            generate_english_audio(
                scripts.get("english", ""),
                en_audio,
                speed=float(settings.get("voice_speed", 1.0)),
            )
            audio_paths["english"] = en_audio

        # ── Step 5: Assemble video(s) ─────────────────────────────────────────
        output_files = []
        langs = list(audio_paths.keys())

        for i, lang in enumerate(langs):
            base_pct = 60 + (i * 30 // max(len(langs), 1))
            progress(base_pct, f"Assembling {lang} video...")
            from backend.services.video import assemble_video

            script_text = scripts.get(lang, "")
            out_mp4     = out_dir / f"recap_{lang}.mp4"

            def _prog(pct, msg, _base=base_pct):
                progress(_base + pct // 5, msg)

            assemble_video(
                source_video=source_path,
                audio_path=audio_paths[lang],
                script=script_text,
                settings=settings,
                out_path=out_mp4,
                progress_cb=_prog,
            )
            output_files.append(str(out_mp4))

        # ── Done ──────────────────────────────────────────────────────────────
        # If single language → single file; if both → JSON list
        import json
        output_str = (output_files[0] if len(output_files) == 1
                      else json.dumps(output_files))

        update_job(job_id,
                   status="complete",
                   progress=100,
                   step="Complete",
                   output_file=output_str)

    except Exception as e:
        tb = traceback.format_exc()
        update_job(job_id,
                   status="failed",
                   step=f"Error: {str(e)[:200]}",
                   error=tb)
        raise


def _get_source(job: dict, settings: dict) -> Path:
    """Download URL or return local file path."""
    if job.get("source_url"):
        url = job["source_url"]

        # Google Drive
        from backend.services.downloader import is_gdrive_url, download_gdrive, download_url
        if is_gdrive_url(url):
            return download_gdrive(url)
        return download_url(url)

    elif job.get("source_file"):
        p = Path(job["source_file"])
        if p.exists():
            return p

    raise ValueError("No valid source video found for this job.")
