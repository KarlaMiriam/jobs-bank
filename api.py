# api.py
from typing import Optional
import threading

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from db import get_active_jobs_ordered, init_db
from main import main as run_scraper

LOW_PRIORITY_COMPANIES = {
    "airbnb", "stripe", "datadog", "cloudflare", "dropbox", "github",
    "discord", "asana", "coinbase", "notion", "atlassian", "figma",
    "rippling", "openai", "slack", "databricks", "affirm", "hubspot",
    "twilio", "plaid", "doordash", "zapier"
}

app = FastAPI(title="EB3 Jobs API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # depois troca pelo domínio do Lovable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _sort_rows(rows):
    def key(r):
        source = (r.get("source") or "").lower()
        company = (r.get("company") or "").lower()
        category = (r.get("category") or "").lower()
        priority = r.get("priority") or 0

        # 1) McDonald's primeiro
        if source == "mchire" or "mcdonald" in company:
            return (0, -priority)
        # 2) hotelaria
        if category == "hotel" or "hotel" in company or "resort" in company:
            return (1, -priority)
        # 3) serviços simples
        if category in ("agriculture", "landscaping", "food_processing"):
            return (2, -priority)
        # 9) tech / companies que você não quer no topo
        if company in LOW_PRIORITY_COMPANIES:
            return (9, -priority)
        # default
        return (5, -priority)

    return sorted(rows, key=key)


def _run_scraper_in_thread():
    """Roda o coletor sem travar o Render."""
    def _task():
        try:
            print("[api] rodando coletor inicial no startup...")
            run_scraper()
            print("[api] coleta inicial concluída.")
        except Exception as e:
            print("[api] erro ao rodar coletor no startup:", e)

    t = threading.Thread(target=_task, daemon=True)
    t.start()


@app.on_event("startup")
def on_startup():
    # 1) garante tabela
    init_db()
    # 2) dispara coleta em background (senão /jobs fica vazio)
    _run_scraper_in_thread()


@app.get("/")
def root():
    return {
        "name": "EB3 Jobs API",
        "endpoints": ["/health", "/jobs", "/jobs/mcdonalds", "/refresh"],
        "docs": "/docs",
    }


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
    try:
        rows = get_active_jobs_ordered()
    except Exception as e:
        print("[api] erro ao ler jobs:", e)
        return {"count": 0, "items": []}

    rows = _sort_rows(rows)
    items = []

    for r in rows:
        if company and company.lower() not in (r.get("company") or "").lower():
            continue
        if source and source.lower() != (r.get("source") or "").lower():
            continue
        if q and q.lower() not in (r.get("title") or "").lower():
            continue

        items.append({
            "title": r.get("title"),
            "company": r.get("company"),
            "description": r.get("description"),
            "city": r.get("city"),
            "state": r.get("state"),
            "country": r.get("country"),
            "salary": r.get("salary"),
            "url": r.get("url"),
            "category": r.get("category"),
            "priority": r.get("priority"),
            "active": bool(r.get("active", 1)),
            "source": r.get("source"),
        })

        if len(items) >= limit:
            break

    return {"count": len(items), "items": items}


@app.get("/jobs/mcdonalds")
def get_mcdonalds(limit: int = 200):
    try:
        rows = get_active_jobs_ordered()
    except Exception as e:
        print("[api] erro ao ler jobs:", e)
        return {"count": 0, "items": []}

    rows = _sort_rows(rows)
    items = []
    for r in rows:
        company = (r.get("company") or "").lower()
        source = (r.get("source") or "").lower()
        if "mcdonald" in company or source == "mchire":
            items.append(r)
            if len(items) >= limit:
                break
    return {"count": len(items), "items": items}


@app.post("/refresh")
def refresh():
    try:
        # aqui você consegue forçar do Lovable
        run_scraper()
    except Exception as e:
        print("[api] erro no refresh:", e)
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "refreshed"}
