"""
SQLite database models using raw sqlite3.
No ORM — keeps it simple and lightweight.
"""
import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from backend.config import cfg


def get_db():
    conn = sqlite3.connect(str(cfg.DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id          TEXT PRIMARY KEY,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'queued',
            progress    INTEGER NOT NULL DEFAULT 0,
            step        TEXT NOT NULL DEFAULT '',
            source_url  TEXT,
            source_file TEXT,
            settings    TEXT NOT NULL DEFAULT '{}',
            output_file TEXT,
            error       TEXT,
            expires_at  TEXT
        );

        CREATE TABLE IF NOT EXISTS assets (
            id          TEXT PRIMARY KEY,
            type        TEXT NOT NULL,
            filename    TEXT NOT NULL,
            path        TEXT NOT NULL,
            created_at  TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def create_job(source_url: str = None, source_file: str = None,
               settings: dict = None) -> dict:
    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    expires = (datetime.utcnow() + timedelta(days=cfg.OUTPUT_TTL_DAYS)).isoformat()
    settings_json = json.dumps(settings or {})

    conn = get_db()
    conn.execute("""
        INSERT INTO jobs (id, created_at, updated_at, status, progress, step,
                          source_url, source_file, settings, expires_at)
        VALUES (?, ?, ?, 'queued', 0, 'Queued', ?, ?, ?, ?)
    """, (job_id, now, now, source_url, source_file, settings_json, expires))
    conn.commit()
    conn.close()
    return get_job(job_id)


def get_job(job_id: str) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["settings"] = json.loads(d["settings"] or "{}")
    return d


def list_jobs() -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM jobs ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d["settings"] = json.loads(d["settings"] or "{}")
        result.append(d)
    return result


def update_job(job_id: str, **kwargs) -> None:
    kwargs["updated_at"] = datetime.utcnow().isoformat()
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [job_id]
    conn = get_db()
    conn.execute(f"UPDATE jobs SET {sets} WHERE id = ?", vals)
    conn.commit()
    conn.close()


def delete_job(job_id: str) -> None:
    conn = get_db()
    conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()


def save_asset(asset_type: str, filename: str, path: str) -> dict:
    # Replace existing asset of same type
    conn = get_db()
    conn.execute("DELETE FROM assets WHERE type = ?", (asset_type,))
    asset_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    conn.execute("""
        INSERT INTO assets (id, type, filename, path, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (asset_id, asset_type, filename, path, now))
    conn.commit()
    conn.close()
    return get_asset(asset_type)


def get_asset(asset_type: str) -> dict | None:
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM assets WHERE type = ?", (asset_type,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def list_assets() -> list[dict]:
    conn = get_db()
    rows = conn.execute("SELECT * FROM assets").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def cleanup_expired_jobs() -> int:
    """Delete jobs and output files past their expiry date."""
    now = datetime.utcnow().isoformat()
    conn = get_db()
    rows = conn.execute(
        "SELECT id, output_file FROM jobs WHERE expires_at < ?", (now,)
    ).fetchall()
    count = 0
    for row in rows:
        if row["output_file"]:
            p = Path(row["output_file"])
            if p.exists():
                p.unlink()
        conn.execute("DELETE FROM jobs WHERE id = ?", (row["id"],))
        count += 1
    conn.commit()
    conn.close()
    return count
