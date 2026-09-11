import sqlite3
from pathlib import Path

from models import JobPosting

DB_PATH = Path(__file__).parent / "jobs.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            source TEXT NOT NULL,
            external_id TEXT NOT NULL,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            url TEXT NOT NULL,
            first_seen_at TEXT NOT NULL,
            PRIMARY KEY (source, external_id)
        )
        """
    )
    # Additive migration: jobs.db already has rows from before this column
    # existed, and CREATE TABLE IF NOT EXISTS above won't alter an existing
    # table, so add it here if it's missing.
    existing_columns = {row[1] for row in conn.execute("PRAGMA table_info(jobs)")}
    if "description" not in existing_columns:
        conn.execute("ALTER TABLE jobs ADD COLUMN description TEXT")
    return conn


def has_seen(conn: sqlite3.Connection, source: str, external_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM jobs WHERE source = ? AND external_id = ?",
        (source, external_id),
    ).fetchone()
    return row is not None


def save_job(conn: sqlite3.Connection, job: JobPosting, *, description: str | None) -> None:
    # description is a required keyword arg, not job.description, so the
    # caller must explicitly decide what to persist - e.g. main.py nulls it
    # out for REJECTed jobs rather than storing it unconditionally.
    conn.execute(
        """
        INSERT INTO jobs (source, external_id, title, company, location, url, description, first_seen_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (job.source, job.external_id, job.title, job.company, job.location, job.url, description),
    )
    # Commit immediately, per job, rather than batching at the end of the run —
    # see architecture.md decision 9. A crash mid-run then loses at most the
    # one job in flight, and rerunning is safe because dedup picks up here.
    conn.commit()
