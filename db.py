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
    return conn


def has_seen(conn: sqlite3.Connection, source: str, external_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM jobs WHERE source = ? AND external_id = ?",
        (source, external_id),
    ).fetchone()
    return row is not None


def save_job(conn: sqlite3.Connection, job: JobPosting) -> None:
    conn.execute(
        """
        INSERT INTO jobs (source, external_id, title, company, location, url, first_seen_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (job.source, job.external_id, job.title, job.company, job.location, job.url),
    )
    # Commit immediately, per job, rather than batching at the end of the run —
    # see architecture.md decision 9. A crash mid-run then loses at most the
    # one job in flight, and rerunning is safe because dedup picks up here.
    conn.commit()
