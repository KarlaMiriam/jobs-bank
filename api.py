from typing import Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from db import init_db, get_active_jobs_ordered
from main import main as run_scraper

app = FastAPI(title="EB3 Jobs API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # depois coloca o domínio do Lovable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    print("[api] rodando coletor inicial no startup...")
    init_db()
    try:
        run_scraper()
    except Exception as e:
        # não derruba a API
        print(f"[api] erro ao rodar coletor no startup: {e}")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/jobs")
def get_jobs(
    limit: int = Query(default=200, ge=1, le=2000),
    company: Optional[str] = None,
    source: Optional[str] = None,
    q: Optional[str] = None,
):
    rows = get_active_jobs_ordered()
    items = []
    for r in rows:
        if company and company.lower() not in (r["company"] or "").lower():
            continue
        if source and source.lower() != (r["source"] or "").lower():
            continue
        if q and q.lower() not in (r["title"] or "").lower():
            continue

        items.append({
            "title": r["title"] or "",
            "company": r["company"] or "",
            "description": r["description"] or "",
            "city": r["city"] or "",
            "state": r["state"] or "",
            "country": r["country"] or "",
            "salary": r["salary"] or "",
            "url": r["url"],
            "category": r["category"] or "",
            "priority": r["priority"] or 0,
            "active": bool(r["active"]),
            "source": r["source"] or "",
        })

        if len(items) >= limit:
            break

    return {"count": len(items), "items": items}


@app.post("/refresh")
def refresh():
    try:
        run_scraper()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "refreshed"}
