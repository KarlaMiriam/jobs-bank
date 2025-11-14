from __future__ import annotations
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import sqlite3
from typing import Dict, Any

from db import (
    init_db,
    get_conn,
    get_active_jobs_ordered,
    get_jobs_count,
    get_active_jobs_by_country,
    get_jobs_count_by_country,
)

app = FastAPI(title="Jobs API", version="1.0.0")


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "url": row["url"],
        "title": row["title"],
        "company": row["company"],
        "description": row["description"],
        "city": row["city"],
        "state": row["state"],
        "country": row["country"],
        "salary": row["salary"],
        "category": row["category"],
        "priority": row["priority"],
        "active": row["active"],
        "source": row["source"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@app.get("/jobs")
def list_jobs():
    """
    GET /jobs
      - Retorna TODAS as vagas ativas (sem paginação),
        ordenadas por priority DESC, created_at DESC.
    """
    init_db()
    rows = get_active_jobs_ordered()
    items = [row_to_dict(r) for r in rows]
    return JSONResponse({"count": len(items), "items": items})


@app.get("/jobs/count")
def jobs_count():
    """GET /jobs/count -> {"count": <vagas_ativas>}"""
    init_db()
    with get_conn() as conn:
        total = get_jobs_count(conn, only_active=True)
    return {"count": total}


@app.get("/jobs/canada")
def list_jobs_canada():
    """
    GET /jobs/canada
      - Retorna TODAS as vagas ativas com country = 'CA',
        ordenadas por priority DESC, created_at DESC.
    """
    init_db()
    rows = get_active_jobs_by_country("CA")
    items = [row_to_dict(r) for r in rows]
    return JSONResponse({"count": len(items), "items": items})


@app.get("/jobs/canada/count")
def jobs_count_canada():
    """
    GET /jobs/canada/count -> {"count": <vagas_ativas_no_Canada>}
    """
    init_db()
    total = get_jobs_count_by_country("CA", only_active=True)
    return {"count": total}
