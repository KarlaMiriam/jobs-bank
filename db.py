import sqlite3
from typing import List, Dict, Any

DB_PATH = "jobs.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # só url obrigatória
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            url TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            description TEXT,
            city TEXT,
            state TEXT,
            country TEXT,
            salary TEXT,
            category TEXT,
            source TEXT,
            priority INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1
        )
        """
    )
    conn.commit()
    conn.close()


def upsert_job(job: Dict[str, Any]):
    """
    joga no banco mesmo se não tiver title/city/state.
    só não grava se não tiver url.
    """
    url = (job.get("url") or "").strip()
    if not url:
        return

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO jobs (
            url, title, company, description, city, state, country,
            salary, category, source, priority, active
        ) VALUES (
            :url, :title, :company, :description, :city, :state, :country,
            :salary, :category, :source, :priority, :active
        )
        ON CONFLICT(url) DO UPDATE SET
            title=COALESCE(excluded.title, jobs.title),
            company=COALESCE(excluded.company, jobs.company),
            description=COALESCE(excluded.description, jobs.description),
            city=COALESCE(excluded.city, jobs.city),
            state=COALESCE(excluded.state, jobs.state),
            country=COALESCE(excluded.country, jobs.country),
            salary=COALESCE(excluded.salary, jobs.salary),
            category=COALESCE(excluded.category, jobs.category),
            source=COALESCE(excluded.source, jobs.source),
            priority=COALESCE(excluded.priority, jobs.priority),
            active=1
        """
    , {
        "url": url,
        "title": job.get("title"),
        "company": job.get("company"),
        "description": job.get("description"),
        "city": job.get("city"),
        "state": job.get("state"),
        "country": job.get("country"),
        "salary": job.get("salary"),
        "category": job.get("category"),
        "source": job.get("source"),
        "priority": job.get("priority", 0),
        "active": 1,
    })
    conn.commit()
    conn.close()


def get_active_jobs_ordered() -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    # ⚠️ nada de WHERE country='US' aqui
    cur.execute(
        """
        SELECT
            url, title, company, description, city, state, country,
            salary, category, source, priority, active
        FROM jobs
        WHERE active = 1
        ORDER BY priority DESC, company ASC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows
