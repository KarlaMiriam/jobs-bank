from __future__ import annotations
import sqlite3
from typing import Iterable, Dict, Any, List, Optional
from pathlib import Path

DB_PATH = Path("jobs.db")

DDL_TARGET = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE,                 -- chave única para upsert
    title TEXT,
    company TEXT,
    description TEXT,
    city TEXT,
    state TEXT,
    country TEXT,
    salary TEXT,
    category TEXT,
    priority INTEGER DEFAULT 10,
    active INTEGER DEFAULT 1,
    source TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_jobs_active_priority ON jobs(active, priority DESC);",
]

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def _table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    cur = conn.execute(f"PRAGMA table_info({table});")
    return [row["name"] for row in cur.fetchall()]

def _migrate_to_target_schema(conn: sqlite3.Connection) -> None:
    cols = set(_table_columns(conn, "jobs"))
    needed = {
        "id","url","title","company","description","city","state","country","salary",
        "category","priority","active","source","created_at","updated_at"
    }
    if cols >= needed:
        return

    conn.execute("""
        CREATE TABLE jobs_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            company TEXT,
            description TEXT,
            city TEXT,
            state TEXT,
            country TEXT,
            salary TEXT,
            category TEXT,
            priority INTEGER DEFAULT 10,
            active INTEGER DEFAULT 1,
            source TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
    """)

    existing_cols = _table_columns(conn, "jobs")
    select_parts = {
        "url": "url",
        "title": "title",
        "company": "company",
        "description": "description",
        "city": "city",
        "state": "state",
        "country": "country",
        "salary": "salary",
        "category": "category",
        "priority": "COALESCE(priority, 10)",
        "active": "COALESCE(active, 1)",
        "source": "source",
        "created_at": "datetime('now')",
        "updated_at": "datetime('now')",
    }

    select_expr = ", ".join(select_parts[k] if k in select_parts else "NULL" for k in [
        "url","title","company","description","city","state","country","salary",
        "category","priority","active","source","created_at","updated_at"
    ])

    if "created_at" in existing_cols:
        select_expr = select_expr.replace("datetime('now')", "created_at", 1)

    conn.execute(f"""
        INSERT INTO jobs_new
            (url, title, company, description, city, state, country, salary,
             category, priority, active, source, created_at, updated_at)
        SELECT {select_expr}
        FROM jobs;
    """)

    conn.execute("DROP TABLE jobs;")
    conn.execute("ALTER TABLE jobs_new RENAME TO jobs;")

def init_db() -> None:
    with get_conn() as conn:
        conn.execute(DDL_TARGET)
        for ddl in CREATE_INDEXES:
            conn.execute(ddl)
        try:
            _migrate_to_target_schema(conn)
            for ddl in CREATE_INDEXES:
                conn.execute(ddl)
            conn.commit()
        except sqlite3.OperationalError:
            pass

def upsert_job(job: Dict[str, Any]) -> None:
    if not job or not job.get("url"):
        return
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO jobs (url, title, company, description, city, state, country, salary,
                              category, priority, active, source)
            VALUES (:url, :title, :company, :description, :city, :state, :country, :salary,
                    :category, :priority, :active, :source)
            ON CONFLICT(url) DO UPDATE SET
                title=excluded.title,
                company=excluded.company,
                description=excluded.description,
                city=excluded.city,
                state=excluded.state,
                country=excluded.country,
                salary=excluded.salary,
                category=excluded.category,
                priority=excluded.priority,
                active=excluded.active,
                source=excluded.source,
                updated_at=datetime('now');
        """, job)
        conn.commit()

def bulk_mark_inactive(urls_to_keep: Iterable[str]) -> None:
    urls = list(urls_to_keep)
    with get_conn() as conn:
        if urls:
            placeholders = ",".join("?" for _ in urls)
            conn.execute(f"""
                UPDATE jobs SET active=0, updated_at=datetime('now')
                WHERE url NOT IN ({placeholders});
            """, urls)
        else:
            conn.execute("UPDATE jobs SET active=0, updated_at=datetime('now');")
        conn.commit()

def get_active_jobs_ordered() -> List[sqlite3.Row]:
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT url, title, company, description, city, state, country, salary,
                   category, priority, active, source, created_at, updated_at
            FROM jobs
            WHERE active=1
            ORDER BY priority DESC, created_at DESC
        """)
        return cur.fetchall()
    
def get_active_jobs_by_country(country_code: str) -> List[sqlite3.Row]:
    """
    Retorna vagas ativas filtrando pelo campo country (US, CA, etc).
    """
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT url, title, company, description, city, state, country, salary,
                   category, priority, active, source, created_at, updated_at
            FROM jobs
            WHERE active = 1
              AND UPPER(country) = UPPER(?)
            ORDER BY priority DESC, created_at DESC
        """, (country_code,))
        return cur.fetchall()


def get_jobs_count_by_country(country_code: str, only_active: bool = True) -> int:
    """
    Conta vagas por país (ex: 'CA' para Canadá).
    """
    with get_conn() as conn:
        if only_active:
            row = conn.execute("""
                SELECT COUNT(*) AS c
                FROM jobs
                WHERE active = 1
                  AND UPPER(country) = UPPER(?)
            """, (country_code,)).fetchone()
        else:
            row = conn.execute("""
                SELECT COUNT(*) AS c
                FROM jobs
                WHERE UPPER(country) = UPPER(?)
            """, (country_code,)).fetchone()

        return int(row["c"] if isinstance(row, sqlite3.Row) else row[0])


def get_jobs_count(conn: Optional[sqlite3.Connection] = None, only_active: bool = True) -> int:
    close_after = False
    if conn is None:
        conn = get_conn()
        close_after = True
    try:
        if only_active:
            row = conn.execute("SELECT COUNT(*) AS c FROM jobs WHERE active = 1").fetchone()
        else:
            row = conn.execute("SELECT COUNT(*) AS c FROM jobs").fetchone()
        return int(row["c"] if isinstance(row, sqlite3.Row) else row[0])
    finally:
        if close_after:
            conn.close()

def get_active_jobs_by_country(country_code: str) -> List[sqlite3.Row]:
        """
        Retorna vagas ativas filtrando pelo campo country (US, CA, etc).
        """
        with get_conn() as conn:
            cur = conn.execute("""
                SELECT url, title, company, description, city, state, country, salary,
                    category, priority, active, source, created_at, updated_at
                FROM jobs
                WHERE active = 1
                AND UPPER(country) = UPPER(?)
                ORDER BY priority DESC, created_at DESC
            """, (country_code,))
            return cur.fetchall()


def get_jobs_count_by_country(country_code: str, only_active: bool = True) -> int:
    """
    Conta vagas por país (ex: 'CA' para Canadá).
    """
    with get_conn() as conn:
        if only_active:
            row = conn.execute("""
                SELECT COUNT(*) AS c
                FROM jobs
                WHERE active = 1
                  AND UPPER(country) = UPPER(?)
            """, (country_code,)).fetchone()
        else:
            row = conn.execute("""
                SELECT COUNT(*) AS c
                FROM jobs
                WHERE UPPER(country) = UPPER(?)
            """, (country_code,)).fetchone()

        return int(row["c"] if isinstance(row, sqlite3.Row) else row[0])

