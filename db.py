# db.py

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "jobs.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            external_id TEXT,
            title TEXT,
            company TEXT,
            description TEXT,
            city TEXT,
            state TEXT,
            country TEXT,
            salary TEXT,
            url TEXT UNIQUE,
            category TEXT,
            priority INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def upsert_job(job: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO jobs
            (source, external_id, title, company, description, city, state, country, salary, url, category, priority, active)
        VALUES
            (:source, :external_id, :title, :company, :description, :city, :state, :country, :salary, :url, :category, :priority, 1)
        ON CONFLICT(url) DO UPDATE SET
            source=excluded.source,
            external_id=excluded.external_id,
            title=excluded.title,
            company=excluded.company,
            description=excluded.description,
            city=excluded.city,
            state=excluded.state,
            country=excluded.country,
            salary=excluded.salary,
            category=excluded.category,
            priority=excluded.priority,
            active=1,
            updated_at=CURRENT_TIMESTAMP
        """
    , job)
    conn.commit()
    conn.close()


def mark_inactive_except(urls: list[str]):
    conn = get_conn()
    cur = conn.cursor()
    if urls:
        placeholders = ",".join(["?"] * len(urls))
        cur.execute(
            f"UPDATE jobs SET active=0 WHERE url NOT IN ({placeholders})",
            urls,
        )
    else:
        # se por algum motivo não veio nada nessa rodada, desativa tudo
        cur.execute("UPDATE jobs SET active=0")
    conn.commit()
    conn.close()


def get_active_jobs_ordered():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM jobs
        WHERE active=1
        ORDER BY priority DESC, updated_at DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows
