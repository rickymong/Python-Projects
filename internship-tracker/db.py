import json
import sqlite3
import re
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "tracker.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    name TEXT DEFAULT '',
    email TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    location TEXT DEFAULT '',
    linkedin_url TEXT DEFAULT '',
    portfolio_url TEXT DEFAULT '',
    summary TEXT DEFAULT '',
    skills TEXT DEFAULT '[]',
    experience TEXT DEFAULT '[]',
    education TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    location TEXT DEFAULT '',
    url TEXT DEFAULT '',
    description TEXT DEFAULT '',
    deadline TEXT DEFAULT '',
    status TEXT DEFAULT 'queued',
    match_score INTEGER DEFAULT 0,
    keywords_matched TEXT DEFAULT '[]',
    keywords_missing TEXT DEFAULT '[]',
    notes TEXT DEFAULT '',
    resume_path TEXT DEFAULT '',
    cover_letter_path TEXT DEFAULT '',
    created_at TEXT,
    updated_at TEXT,
    applied_at TEXT,
    dedup_key TEXT UNIQUE NOT NULL
);
"""

PROFILE_JSON_FIELDS = {"skills", "experience", "education"}
JOB_JSON_FIELDS = {"keywords_matched", "keywords_missing"}
VALID_STATUSES = ["queued", "ready", "applied", "interview", "offer", "rejected", "archived"]


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def dedup_key(company: str, title: str) -> str:
    norm = lambda s: re.sub(r"\s+", " ", s or "").strip().lower()
    return f"{norm(company)}|{norm(title)}"


@contextmanager
def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        row = conn.execute("SELECT id FROM profile WHERE id = 1").fetchone()
        if not row:
            conn.execute("INSERT INTO profile (id) VALUES (1)")


def _row_to_profile(row) -> dict:
    d = dict(row)
    for f in PROFILE_JSON_FIELDS:
        d[f] = json.loads(d[f] or "[]")
    return d


def get_profile() -> dict:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
        return _row_to_profile(row)


def save_profile(data: dict) -> dict:
    fields = ["name", "email", "phone", "location", "linkedin_url", "portfolio_url", "summary"]
    values = {f: data.get(f, "") for f in fields}
    for f in PROFILE_JSON_FIELDS:
        values[f] = json.dumps(data.get(f, []))
    with get_conn() as conn:
        conn.execute(
            """UPDATE profile SET name=:name, email=:email, phone=:phone, location=:location,
               linkedin_url=:linkedin_url, portfolio_url=:portfolio_url, summary=:summary,
               skills=:skills, experience=:experience, education=:education WHERE id = 1""",
            values,
        )
    return get_profile()


def _row_to_job(row) -> dict:
    d = dict(row)
    for f in JOB_JSON_FIELDS:
        d[f] = json.loads(d[f] or "[]")
    return d


def list_jobs(status: str | None = None) -> list[dict]:
    with get_conn() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC", (status,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
        return [_row_to_job(r) for r in rows]


def get_job(job_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return _row_to_job(row) if row else None


def find_duplicate(company: str, title: str) -> dict | None:
    key = dedup_key(company, title)
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE dedup_key = ?", (key,)).fetchone()
        return _row_to_job(row) if row else None


def add_job(data: dict) -> tuple[dict | None, dict | None]:
    """Returns (job, conflict). Exactly one is non-None."""
    company, title = data.get("company", "").strip(), data.get("title", "").strip()
    if not company or not title:
        raise ValueError("company and title are required")
    dup = find_duplicate(company, title)
    if dup:
        return None, dup
    key = dedup_key(company, title)
    ts = now_iso()
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO jobs (company, title, location, url, description, deadline,
               status, created_at, updated_at, dedup_key)
               VALUES (?, ?, ?, ?, ?, ?, 'queued', ?, ?, ?)""",
            (
                company, title, data.get("location", ""), data.get("url", ""),
                data.get("description", ""), data.get("deadline", ""), ts, ts, key,
            ),
        )
        job_id = cur.lastrowid
    return get_job(job_id), None


def update_job(job_id: int, fields: dict) -> dict | None:
    if not fields:
        return get_job(job_id)
    allowed = {
        "status", "notes", "deadline", "match_score", "keywords_matched",
        "keywords_missing", "resume_path", "cover_letter_path", "applied_at",
        "company", "title", "location", "url", "description",
    }
    set_parts, values = [], []
    for k, v in fields.items():
        if k not in allowed:
            continue
        if k in JOB_JSON_FIELDS:
            v = json.dumps(v)
        set_parts.append(f"{k} = ?")
        values.append(v)
    if not set_parts:
        return get_job(job_id)
    set_parts.append("updated_at = ?")
    values.append(now_iso())
    values.append(job_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE jobs SET {', '.join(set_parts)} WHERE id = ?", values)
    return get_job(job_id)


def delete_job(job_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        return cur.rowcount > 0


def stats() -> dict:
    with get_conn() as conn:
        rows = conn.execute("SELECT status, match_score FROM jobs").fetchall()
    total = len(rows)
    by_status = {s: 0 for s in VALID_STATUSES}
    score_sum, score_n = 0, 0
    for r in rows:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
        if r["status"] != "archived":
            score_sum += r["match_score"] or 0
            score_n += 1
    return {
        "total": total,
        "by_status": by_status,
        "applied": by_status.get("applied", 0) + by_status.get("interview", 0) + by_status.get("offer", 0),
        "interviews": by_status.get("interview", 0) + by_status.get("offer", 0),
        "offers": by_status.get("offer", 0),
        "avg_match": round(score_sum / score_n) if score_n else 0,
    }
