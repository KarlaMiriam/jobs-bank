# api.py
import os
import sqlite3
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DB_PATH = os.getenv("DB_PATH", os.path.join(os.getcwd(), "jobs.db"))

app = FastAPI(title="JobBot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- utils de DB ----------

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def rows_to_dicts(rows: List[sqlite3.Row]) -> List[dict]:
    out = []
    for r in rows:
        # sqlite3.Row é indexável por coluna
        out.append({k: r[k] for k in r.keys()})
    return out

# ---------- modelos ----------

class Job(BaseModel):
    url: str
    title: Optional[str] = None
    company: Optional[str] = None
    description: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    salary: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[int] = None
    active: Optional[int] = 1
    source: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# ---------- rotas ----------

@app.get("/health")
def health():
    # também valida se a tabela existe
    try:
        with get_conn() as conn:
            conn.execute("SELECT 1 FROM jobs LIMIT 1")
        return {"ok": True}
    except sqlite3.OperationalError as e:
        return {"ok": False, "detail": f"DB not ready: {e}"}

@app.get("/stats")
def stats():
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        active = conn.execute("SELECT COUNT(*) FROM jobs WHERE active=1").fetchone()[0]
        us = conn.execute("SELECT COUNT(*) FROM jobs WHERE country='US' OR country='USA' OR country='United States'").fetchone()[0]
    return {"total": total, "active": active, "us": us}

@app.get("/jobs", response_model=dict)
def get_jobs(
    q: Optional[str] = Query(default=None, description="Busca em título/descrição/empresa/cidade/estado"),
    state: Optional[str] = Query(default=None),
    city: Optional[str] = Query(default=None),
    country: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    active: Optional[bool] = Query(default=True),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    """
    Retorna JSON:
      {"count": N, "items": [ ... ]}
    Ordenado por prioridade desc e updated_at desc (quando houver).
    """
    try:
        where = []
        params: List[object] = []

        if active is not None:
            where.append("active = ?")
            params.append(1 if active else 0)

        if q:
            like = f"%{q}%"
            where.append("(title LIKE ? OR description LIKE ? OR company LIKE ? OR city LIKE ? OR state LIKE ?)")
            params.extend([like, like, like, like, like])

        if state:
            where.append("state = ?")
            params.append(state)

        if city:
            where.append("city = ?")
            params.append(city)

        if country:
            # aceita US / USA / United States
            where.append("(country = ? OR country = ? OR country = ?)")
            params.extend([country, country.upper(), "United States" if country.upper() in ("US", "USA") else country])

        if source:
            where.append("source = ?")
            params.append(source)

        where_sql = f"WHERE {' AND '.join(where)}" if where else ""

        # COUNT
        with get_conn() as conn:
            cnt_row = conn.execute(f"SELECT COUNT(*) AS c FROM jobs {where_sql}", params).fetchone()
            total = int(cnt_row["c"] if isinstance(cnt_row, sqlite3.Row) else cnt_row[0])

            # ORDER BY: prioridade desc, updated_at desc (NULLS LAST), created_at desc, title asc
            sql = f"""
                SELECT url, title, company, description, city, state, country, salary,
                       category, priority, active, source, created_at, updated_at
                FROM jobs
                {where_sql}
                ORDER BY
                    COALESCE(priority, 0) DESC,
                    CASE WHEN updated_at IS NULL THEN 1 ELSE 0 END,
                    updated_at DESC,
                    CASE WHEN created_at IS NULL THEN 1 ELSE 0 END,
                    created_at DESC,
                    COALESCE(title, '') ASC
                LIMIT ? OFFSET ?
            """
            items = conn.execute(sql, (*params, limit, offset)).fetchall()

        return {
            "count": total,
            "items": rows_to_dicts(items),
        }
    except Exception as e:
        # Loga no console e devolve 500 amigável
        print("[/jobs] erro:", repr(e))
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")

