# api.py
from __future__ import annotations
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from db import get_conn
import sqlite3
import math

app = FastAPI(title="JobBot API")

# CORS – ajuste allow_origins para o domínio do seu Lovable se quiser restringir
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}

def _compose_where(filters: Dict[str, Optional[str]]) -> (str, list):
    """
    Monta WHERE dinâmico para filtros simples.
    Filtros suportados: q (busca), state, category, source, company.
    """
    clauses = ["active = 1"]
    params: List[Any] = []

    q = filters.get("q")
    if q:
        clauses.append("(title LIKE ? OR company LIKE ? OR description LIKE ? OR city LIKE ?)")
        like = f"%{q}%"
        params += [like, like, like, like]

    state = filters.get("state")
    if state:
        clauses.append("state = ?")
        params.append(state)

    category = filters.get("category")
    if category:
        clauses.append("category = ?")
        params.append(category)

    source = filters.get("source")
    if source:
        clauses.append("source = ?")
        params.append(source)

    company = filters.get("company")
    if company:
        clauses.append("company = ?")
        params.append(company)

    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    return where, params

@app.get("/jobs")
def get_jobs(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    q: Optional[str] = None,
    state: Optional[str] = None,
    category: Optional[str] = None,
    source: Optional[str] = None,
    company: Optional[str] = None,
    order: str = Query("updated_at_desc", description="updated_at_desc|priority_desc|created_at_desc"),
):
    """
    Lista vagas ativas com paginação e filtros.
    """
    order_by = {
        "updated_at_desc": "updated_at DESC",
        "created_at_desc": "created_at DESC",
        "priority_desc": "priority DESC, updated_at DESC",
    }.get(order, "updated_at DESC")

    where, params = _compose_where({
        "q": q, "state": state, "category": category, "source": source, "company": company
    })

    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        # total geral p/ os mesmos filtros
        cur = conn.execute(f"SELECT COUNT(*) as c FROM jobs {where}", params)
        total = cur.fetchone()["c"]

        cur = conn.execute(
            f"""
            SELECT id, url, title, company, description, city, state, country,
                   salary, category, priority, active, source, created_at, updated_at
            FROM jobs
            {where}
            ORDER BY {order_by}
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        )
        rows = [row_to_dict(r) for r in cur.fetchall()]

    # Retorne também metadados úteis para o front
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "pages": math.ceil(total / limit) if limit else 1,
        "items": rows,
    }

@app.get("/stats")
def get_stats():
    """
    Retorna contagens para o painel (total de ativas e por fonte).
    """
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        total = conn.execute("SELECT COUNT(*) as c FROM jobs WHERE active = 1").fetchone()["c"]
        by_source = conn.execute("""
            SELECT source, COUNT(*) as c
            FROM jobs
            WHERE active = 1
            GROUP BY source
            ORDER BY c DESC
        """).fetchall()
        by_category = conn.execute("""
            SELECT COALESCE(category, '') as category, COUNT(*) as c
            FROM jobs
            WHERE active = 1
            GROUP BY COALESCE(category, '')
            ORDER BY c DESC
        """).fetchall()

    return {
        "total_active": total,
        "by_source": [row_to_dict(r) for r in by_source],
        "by_category": [row_to_dict(r) for r in by_category],
    }

@app.get("/")
def root():
    return {"ok": True, "service": "JobBot API"}
