# db.py
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

DB_PATH = Path(__file__).parent / "jobs.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Cria a tabela no formato que você já estava usando.
    Só `url` é NOT NULL e UNIQUE.
    O resto pode ser NULL.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            title TEXT,
            company TEXT,
            description TEXT,
            city TEXT,
            state TEXT,
            country TEXT,
            salary TEXT,
            category TEXT,
            priority INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1,
            source TEXT,
            external_id TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.commit()

    # garante que colunas novas existam se o banco for antigo
    _ensure_columns(conn)
    conn.close()


def _ensure_columns(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(jobs);")
    cols = {row[1] for row in cur.fetchall()}

    # se for banco antigo, adiciona
    if "external_id" not in cols:
        cur.execute("ALTER TABLE jobs ADD COLUMN external_id TEXT;")
    if "created_at" not in cols:
        cur.execute("ALTER TABLE jobs ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP;")
    if "updated_at" not in cols:
        cur.execute("ALTER TABLE jobs ADD COLUMN updated_at TEXT DEFAULT CURRENT_TIMESTAMP;")
    conn.commit()


def upsert_job(job: Dict[str, Any]):
    """
    Insere ou atualiza uma vaga.
    ÚNICA exigência: ter `url`.
    Se o resto vier vazio, salva vazio mesmo.
    """
    url = (job.get("url") or "").strip()
    if not url:
        # sem link não faz sentido guardar
        return

    conn = get_conn()
    cur = conn.cursor()

    # existe?
    cur.execute("SELECT id FROM jobs WHERE url = ?", (url,))
    row = cur.fetchone()

    if row:
        # atualiza só o que veio (se vier None, mantém o que já tinha)
        cur.execute(
            """
            UPDATE jobs
               SET title = COALESCE(?, title),
                   company = COALESCE(?, company),
                   description = COALESCE(?, description),
                   city = COALESCE(?, city),
                   state = COALESCE(?, state),
                   country = COALESCE(?, country),
                   salary = COALESCE(?, salary),
                   category = COALESCE(?, category),
                   priority = COALESCE(?, priority),
                   active = 1,
                   source = COALESCE(?, source),
                   external_id = COALESCE(?, external_id),
                   updated_at = CURRENT_TIMESTAMP
             WHERE id = ?
            """,
            (
                job.get("title"),
                job.get("company"),
                job.get("description"),
                job.get("city"),
                job.get("state"),
                job.get("country"),
                job.get("salary"),
                job.get("category"),
                job.get("priority"),
                job.get("source"),
                job.get("external_id"),
                row["id"],
            ),
        )
    else:
        # insere aceitando nulos
        cur.execute(
            """
            INSERT INTO jobs (
                url, title, company, description,
                city, state, country, salary,
                category, priority, active, source,
                external_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (
                url,
                job.get("title"),
                job.get("company"),
                job.get("description"),
                job.get("city"),
                job.get("state"),
                job.get("country"),
                job.get("salary"),
                job.get("category"),
                job.get("priority") or 0,
                job.get("source"),
                job.get("external_id"),
            ),
        )

    conn.commit()
    conn.close()


def mark_missing_as_inactive(active_urls: List[str]):
    """
    Tudo que NÃO veio na coleta atual vira inativo.
    """
    conn = get_conn()
    cur = conn.cursor()
    if active_urls:
        qmarks = ",".join("?" * len(active_urls))
        cur.execute(f"UPDATE jobs SET active = 0 WHERE url NOT IN ({qmarks})", active_urls)
    else:
        cur.execute("UPDATE jobs SET active = 0")
    conn.commit()
    conn.close()


def get_active_jobs_ordered() -> list[dict]:
    """
    Retorna vagas ativas, ordenadas por prioridade e data.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
          FROM jobs
         WHERE active = 1
         ORDER BY priority DESC, created_at DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]
