# db.py
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "jobs.db")

DDL = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT,
    title TEXT,
    company TEXT,
    description TEXT,
    city TEXT,
    state TEXT,
    country TEXT,
    salary TEXT,
    url TEXT NOT NULL,
    category TEXT,
    priority INTEGER DEFAULT 0,
    active INTEGER DEFAULT 1,
    source TEXT,
    created_at TEXT,
    updated_at TEXT
);
"""

# índices ajudam no GET /jobs
INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_jobs_url ON jobs(url);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_active ON jobs(active);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);",
]


def get_conn():
    # garante diretório
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(DDL)
    for idx in INDEXES:
        cur.execute(idx)
    conn.commit()
    conn.close()


def _now():
    return datetime.utcnow().isoformat(timespec="seconds")


def upsert_job(job: dict):
    """
    Só 'url' é obrigatório.
    Se já existir uma vaga com o mesmo 'url', atualiza.
    """
    if not job.get("url"):
        return  # sem link não salva

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id FROM jobs WHERE url = ?", (job["url"],))
    row = cur.fetchone()

    if row:
        cur.execute(
            """
            UPDATE jobs
               SET external_id = ?,
                   title = ?,
                   company = ?,
                   description = ?,
                   city = ?,
                   state = ?,
                   country = ?,
                   salary = ?,
                   category = ?,
                   priority = ?,
                   active = 1,
                   source = ?,
                   updated_at = ?
             WHERE id = ?
            """,
            (
                job.get("external_id"),
                job.get("title"),
                job.get("company"),
                job.get("description"),
                job.get("city"),
                job.get("state"),
                job.get("country"),
                job.get("salary"),
                job.get("category"),
                job.get("priority", 0),
                job.get("source"),
                _now(),
                row["id"],
            ),
        )
    else:
        cur.execute(
            """
            INSERT INTO jobs (
                external_id, title, company, description,
                city, state, country, salary, url,
                category, priority, active, source,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
            """,
            (
                job.get("external_id"),
                job.get("title"),
                job.get("company"),
                job.get("description"),
                job.get("city"),
                job.get("state"),
                job.get("country"),
                job.get("salary"),
                job["url"],
                job.get("category"),
                job.get("priority", 0),
                job.get("source"),
                _now(),
                _now(),
            ),
        )

    conn.commit()
    conn.close()


def get_active_jobs_ordered() -> list[dict]:
    """
    Se der qualquer erro de coluna (Render ainda com DB velho),
    devolve lista vazia para não quebrar a API.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT
                external_id,
                title,
                company,
                description,
                city,
                state,
                country,
                salary,
                url,
                category,
                priority,
                active,
                source,
                created_at,
                updated_at
            FROM jobs
            WHERE active = 1
            ORDER BY priority DESC, created_at DESC
            """
        )
    except sqlite3.OperationalError as e:
        # coluna não existe? tabela faltando? devolve vazio
        print("[db] aviso:", e)
        return []

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
