from __future__ import annotations
import sqlite3
from typing import Iterable, Dict, Any, List
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
    conn.row_factory = sqlite3.Row          # ⬅️ importante!
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def _table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    cur = conn.execute(f"PRAGMA table_info({table});")
    return [row["name"] for row in cur.fetchall()]

def _migrate_to_target_schema(conn: sqlite3.Connection) -> None:
    """
    Migra para o esquema alvo se faltar alguma coluna (ex.: created_at/updated_at).
    Cria uma tabela nova, copia dados e renomeia.
    """
    cols = set(_table_columns(conn, "jobs"))
    needed = {
        "id","url","title","company","description","city","state","country","salary",
        "category","priority","active","source","created_at","updated_at"
    }
    if cols >= needed:
        # já está no esquema alvo
        return

    # cria tabela nova com o esquema final
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

    # monta a cópia a partir do que existir
    existing_cols = _table_columns(conn, "jobs")
    # mapeia colunas (usa COALESCE para defaults)
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
        # timestamps novos: agora
        "created_at": "datetime('now')",
        "updated_at": "datetime('now')",
    }

    # constroi SELECT somente do que existe na antiga; os outros ficam nos COALESCE/acima
    select_expr = ", ".join(select_parts[k] if k in select_parts else "NULL" for k in [
        "url","title","company","description","city","state","country","salary",
        "category","priority","active","source","created_at","updated_at"
    ])

    # para compatibilidade, se a antiga tinha created_at/updated_at, use-as
    if "created_at" in existing_cols:
        select_expr = select_expr.replace("datetime('now')", "created_at", 1)
    if "updated_at" in existing_cols:
        # substitui a segunda ocorrência se existir
        second_now_pos = select_expr.find("datetime('now')", select_expr.find("datetime('now')")+1)
        if second_now_pos != -1:
            # não precisamos ser ultra precisos; abaixo é suficiente
            pass

    conn.execute(f"""
        INSERT INTO jobs_new
            (url, title, company, description, city, state, country, salary,
             category, priority, active, source, created_at, updated_at)
        SELECT {select_expr}
        FROM jobs;
    """)

    # troca tabelas
    conn.execute("DROP TABLE jobs;")
    conn.execute("ALTER TABLE jobs_new RENAME TO jobs;")

def init_db() -> None:
    with get_conn() as conn:
        # cria se não existir
        conn.execute(DDL_TARGET)
        for ddl in CREATE_INDEXES:
            conn.execute(ddl)
        # se existir mas estiver antigo, migra
        try:
            _migrate_to_target_schema(conn)
            for ddl in CREATE_INDEXES:
                conn.execute(ddl)
            conn.commit()
        except sqlite3.OperationalError:
            # se a tabela não existia ainda, tudo bem
            pass

def upsert_job(job: Dict[str, Any]) -> None:
    if not job or not job.get("url"):
        return
    with get_conn() as conn:
        # não precisamos especificar created_at/updated_at no INSERT;
        # deixa os DEFAULTs preencherem; updated_at é setado no UPDATE.
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
            conn.execute(f"UPDATE jobs SET active=0, updated_at=datetime('now') WHERE url NOT IN ({placeholders});", urls)
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


# db.py (ADICIONE ISTO)

import sqlite3
from typing import Optional

def get_jobs_count(conn: Optional[sqlite3.Connection] = None, only_active: bool = True) -> int:
    """Retorna a contagem de vagas. Por padrão, só as ativas."""
    close_after = False
    if conn is None:
        from db import get_conn  # evita import circular
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
