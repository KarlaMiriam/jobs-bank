
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://user:pass@localhost:5432/eb3jobs")
engine = create_engine(DATABASE_URL, future=True)

app = FastAPI(title="EB3 Job Aggregator API", version="0.1")

class Job(BaseModel):
    id: str
    title: str
    city: str
    state: str
    country: str = "US"
    wage_hourly: Optional[float] = None
    status: str
    duties: Optional[str] = None
    apply_url: Optional[str] = None
    video_url: Optional[str] = None
    visa_types: List[str] = ["EB-3"]
    language_tags: List[str] = ["en", "pt"]
    posted_date: Optional[date] = None

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/jobs", response_model=List[Job])
def list_jobs(
    state: Optional[str] = Query(None, description="Filtro por estado"),
    status: Optional[str] = Query(None, description="FILING_NOW/SOLD_OUT/PAUSED"),
    q: Optional[str] = Query(None, description="Busca por título/cidade"),
    limit: int = 50,
    offset: int = 0,
):
    filters = []
    params = {}

    if state:
        filters.append("state = :state")
        params["state"] = state.upper()
    if status:
        filters.append("status = :status")
        params["status"] = status
    if q:
        filters.append("(lower(title) LIKE :q OR lower(city) LIKE :q)")
        params["q"] = f"%{q.lower()}%"

    where = (" WHERE " + " AND ".join(filters)) if filters else ""
    sql = f"""
        SELECT id::text, title, city, state, country, wage_hourly, status,
               duties, apply_url, video_url, visa_types, language_tags, posted_date
        FROM eb3_jobs
        {where}
        ORDER BY posted_date DESC NULLS LAST, created_at DESC
        LIMIT :limit OFFSET :offset
    """
    params.update({"limit": limit, "offset": offset})

    with engine.begin() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
    return [Job(**row) for row in rows]

@app.get("/jobs/{job_id}", response_model=Job)
def get_job(job_id: str):
    sql = text("""
        SELECT id::text, title, city, state, country, wage_hourly, status,
               duties, apply_url, video_url, visa_types, language_tags, posted_date
        FROM eb3_jobs WHERE id::text = :id
    """)
    with engine.begin() as conn:
        row = conn.execute(sql, {"id": job_id}).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
    return Job(**row)
