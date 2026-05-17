"""
Video assembly service.
Handles all ffmpeg operations:
- Clip extraction with copyright bypass
- 9:16 crop
- Flip, auto color grade
- Blur mask (user-drawn regions)
- Subtitle burning (PIL)
- Voiceover + music mix
- Logo watermark
- Intro / Outro prepend/append
"""
import json
import subprocess
import tempfile
import textwrap
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from backend.config import cfg


def ff(cmd: list) -> subprocess.CompletedProcess:
    """Run ffmpeg command, raise on failure."""
    full = [cfg.FFMPEG_PATH, "-hide_banner", "-loglevel", "error"] + cmd
    r = subprocess.run(full, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg error:\n{r.stderr[-600:]}")
    return r


def ffprobe_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", str(path)],
        capture_output=True, text=True
    )
    try:
        return float(json.loads(result.stdout)["format"]["duration"])
    except Exception:
        return 60.0


def get_video_size(path: Path) -> tuple[int, int]:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_streams", str(path)],
        capture_output=True, text=True
    )
    try:
        for s in json.loads(result.stdout)["streams"]:
            if s.get("codec_type") == "video":
                return s["width"], s["height"]
    except Exception:
        pass
    return 1920, 1080


def _get_font(size: int):
    for f in ["C:/Windows/Fonts/Arial.ttf", "C:/Windows/Fonts/arialbd.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if Path(f).exists():
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                pass
    return ImageFont.load_default()


def build_subtitle_overlay(text: str, width: int) -> Image.Image:
    font   = _get_font(42)
    words  = text.split()
    chunks = [" ".join(words[i:i+5]) for i in range(0, len(words), 5)]
    # Return first chunk as one subtitle image
    chunk  = chunks[0] if chunks else text
    wrapped = textwrap.fill(chunk, width=28)
    lines  = wrapped.split("\n")
    lh     = 52
    bh     = lh * len(lines) + 20
    img    = Image.new("RGBA", (width, bh), (0, 0, 0, 180))
    draw   = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw   = bbox[2] - bbox[0]
        x    = max(10, (width - tw) // 2)
        y    = 10 + i * lh
        draw.text((x+2, y+2), line, font=font, fill=(0, 0, 0, 200))
        draw.text((x, y),     line, font=font, fill=(255, 255, 255, 255))
    return img


def assemble_video(
    source_video: Path,
    audio_path:   Path,
    script:       str,
    settings:     dict,
    out_path:     Path,
    progress_cb   = None,
) -> Path:
    """
    Full video assembly pipeline.
    settings keys: flip, auto_color, copyright_bypass, subtitles,
                   blur_masks, logo, intro, outro, language
    """

    def _progress(pct: int, msg: str):
        if progress_cb:
            progress_cb(pct, msg)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        W, H = cfg.VIDEO_WIDTH, cfg.VIDEO_HEIGHT

        # ── 1. Get source duration ────────────────────────────────────────────
        _progress(5, "Analysing source video...")
        src_dur = ffprobe_duration(source_video)
        n_clips = min(40, max(10, int(src_dur / 5)))
        interval = src_dur / (n_clips + 1)

        # ── 2. Extract clips ──────────────────────────────────────────────────
        _progress(10, "Extracting clips...")
        clip_paths = []
        for i in range(n_clips):
            t   = interval * (i + 1)
            out = tmp / f"clip_{i:04d}.mp4"

            # Copyright bypass: vary speed and zoom slightly per clip
            zoom  = round(random.uniform(1.02, 1.06), 3)
            spd   = round(random.uniform(0.97, 1.03), 2)

            vf_parts = [
                f"scale={W*2}:{H*2}",
                f"zoompan=z={zoom}:d=1:s={W}x{H}",
                f"crop={W}:{H}",
            ]

            if settings.get("auto_color"):
                vf_parts.append("eq=saturation=1.15:contrast=1.05:brightness=0.02")

            if settings.get("flip"):
                vf_parts.append("hflip")

            # Blur masks — each mask: {x, y, w, h} as 0-1 fractions of frame
            for mask in settings.get("blur_masks", []):
                mx = int(mask["x"] * W)
                my = int(mask["y"] * H)
                mw = int(mask["w"] * W)
                mh = int(mask["h"] * H)
                vf_parts.append(
                    f"boxblur=20:enable='1'"
                    f"[base];[base]crop={mw}:{mh}:{mx}:{my},"
                    f"boxblur=30[blurred];[base][blurred]overlay={mx}:{my}"
                )
                # Simpler approach: delogo or crop+blur overlay
                # Use lavfi boxblur on the whole then overlay — simplified:
            
            vf = ",".join(vf_parts[:5])  # keep it clean

            try:
                ff(["-ss", str(t), "-i", str(source_video),
                    "-t", "4", "-vf", vf,
                    "-an", "-c:v", "libx264", "-preset", "ultrafast",
                    str(out)])
                clip_paths.append(out)
            except Exception:
                pass

        if not clip_paths:
            raise RuntimeError("No clips extracted from source video.")

        # ── 3. Concat clips ───────────────────────────────────────────────────
        _progress(35, "Assembling clips...")
        concat_txt = tmp / "concat.txt"
        concat_txt.write_text(
            "\n".join(f"file '{str(p).replace(chr(92), '/')}'"
                      for p in clip_paths),
            encoding="utf-8"
        )
        raw_video = tmp / "raw.mp4"
        ff(["-f", "concat", "-safe", "0", "-i", str(concat_txt),
            "-c", "copy", str(raw_video)])

        # ── 4. Get audio duration, loop video to match ────────────────────────
        _progress(45, "Syncing audio length...")
        audio_dur = ffprobe_duration(audio_path)
        looped    = tmp / "looped.mp4"
        ff(["-stream_loop", "-1", "-i", str(raw_video),
            "-t", str(audio_dur + 1), "-c", "copy", str(looped)])

        # ── 5. Burn subtitles (PIL overlay) ───────────────────────────────────
        sub_video = looped
        if settings.get("subtitles") and script:
            _progress(55, "Burning subtitles...")
            words     = script.split()
            chunk_sz  = 5
            chunks    = [" ".join(words[i:i+chunk_sz])
                         for i in range(0, len(words), chunk_sz)]
            chunk_dur = audio_dur / max(len(chunks), 1)

            inputs  = ["-i", str(looped)]
            sub_pngs = []
            for i, chunk in enumerate(chunks):
                img = build_subtitle_overlay(chunk, W)
                p   = tmp / f"sub_{i:04d}.png"
                img.save(str(p))
                sub_pngs.append((p, i * chunk_dur, (i+1) * chunk_dur))
                inputs += ["-i", str(p)]

            y_pos   = H - 200
            filters = []
            prev    = "[0:v]"
            for idx, (_, ts, te) in enumerate(sub_pngs):
                inp = f"[{idx+1}:v]"
                out = f"[sv{idx}]"
                en  = f"enable='between(t,{ts:.2f},{te:.2f})'"
                filters.append(f"{prev}{inp}overlay=0:{y_pos}:{en}{out}")
                prev = out

            sub_video = tmp / "subtitled.mp4"
            ff(inputs + [
                "-filter_complex", ";".join(filters),
                "-map", prev, "-map", "0:a?",
                "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
                "-c:a", "copy", str(sub_video)
            ])

        # ── 6. Add logo watermark ─────────────────────────────────────────────
        logo_video = sub_video
        logo_asset = settings.get("logo_path")
        if logo_asset and Path(logo_asset).exists():
            _progress(62, "Adding watermark...")
            logo_out = tmp / "logo.mp4"
            ff(["-i", str(sub_video), "-i", logo_asset,
                "-filter_complex",
                f"[1:v]scale=120:-1[logo];[0:v][logo]overlay=20:20",
                "-map", "0:a?", "-c:v", "libx264", "-preset", "fast",
                "-c:a", "copy", str(logo_out)])
            logo_video = logo_out

        # ── 7. Mix voiceover + background music ───────────────────────────────
        _progress(70, "Mixing audio...")
        mixed = tmp / "mixed.mp4"
        music_files = list(Path("music").glob("*.mp3")) if Path("music").exists() else []
        if music_files:
            music = random.choice(music_files)
            ff(["-i", str(logo_video), "-i", str(audio_path),
                "-stream_loop", "-1", "-i", str(music),
                "-filter_complex",
                (f"[1:a]volume=1.0[vo];"
                 f"[2:a]volume=0.15,atrim=duration={audio_dur}[bg];"
                 f"[vo][bg]amix=inputs=2:duration=first[aout]"),
                "-map", "0:v", "-map", "[aout]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-shortest", str(mixed)])
        else:
            ff(["-i", str(logo_video), "-i", str(audio_path),
                "-map", "0:v", "-map", "1:a",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-shortest", str(mixed)])

        # ── 8. Prepend intro / append outro ───────────────────────────────────
        final_input = mixed
        parts = []
        intro = settings.get("intro_path")
        outro = settings.get("outro_path")

        if intro and Path(intro).exists():
            parts.append(intro)
        parts.append(str(mixed))
        if outro and Path(outro).exists():
            parts.append(outro)

        if len(parts) > 1:
            _progress(82, "Adding intro/outro...")
            seg_list = tmp / "segments.txt"
            seg_list.write_text(
                "\n".join(f"file '{p.replace(chr(92), '/')}'"
                           for p in parts),
                encoding="utf-8"
            )
            final_with_io = tmp / "with_io.mp4"
            ff(["-f", "concat", "-safe", "0", "-i", str(seg_list),
                "-c", "copy", str(final_with_io)])
            final_input = final_with_io

        # ── 9. Final export ───────────────────────────────────────────────────
        _progress(90, "Exporting final video...")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        ff(["-i", str(final_input),
            "-c:v", "libx264", "-crf", "23", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(out_path)])

    _progress(100, "Done!")
    return out_path
