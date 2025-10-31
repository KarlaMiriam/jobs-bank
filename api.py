# api.py
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from db import get_active_jobs_ordered
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
    allow_origins=["*"],  # troque depois pro domínio do Lovable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _sort_rows(rows):
    def key(r):
        source = (r["source"] or "").lower()
        company = (r["company"] or "").lower()
        category = (r["category"] or "").lower()
        priority = r["priority"] or 0

        # 0 – McDonald's primeiro
        if source == "mchire" or "mcdonald" in company:
            return (0, -priority)

        # 1 – hotelaria
        if category == "hotel" or "hotel" in company or "resort" in company or "marriott" in company or "hilton" in company or "ihg" in company:
            return (1, -priority)

        # 2 – food service / restaurante / wendys / cafeteria
        if category == "restaurant" or "wendy" in company or "food" in category:
            return (2, -priority)

        # 3 – warehouse / cleaning / retail
        if category in ("retail", "cleaning", "janitorial", "warehouse"):
            return (3, -priority)

        # 9 – tech low priority
        if company in LOW_PRIORITY_COMPANIES:
            return (9, -priority)

        return (5, -priority)
    return sorted(rows, key=key)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/jobs")
def get_jobs(
    limit: int = Query(default=200, ge=1, le=2000),
    company: Optional[str] = None,
    source: Optional[str] = None,
    q: Optional[str] = None,
    only_us: bool = True,
):
    rows = get_active_jobs_ordered()
    rows = _sort_rows(rows)
    items = []

    for r in rows:
        if company and company.lower() not in (r["company"] or "").lower():
            continue
        if source and source.lower() != (r["source"] or "").lower():
            continue
        if q and q.lower() not in (r["title"] or "").lower():
            continue
        if only_us and r.get("country") and r["country"].upper() not in ("US", "USA"):
            # se for hotel/fast-food mas veio sem country, não derruba
            comp = (r["company"] or "").lower()
            if not ("mcdonald" in comp or "wendy" in comp or "hilton" in comp or "marriott" in comp or "ihg" in comp):
                continue

        items.append({
            "title": r["title"],
            "company": r["company"],
            "description": r["description"] or "Job description not available.",
            "city": r["city"],
            "state": r["state"],
            "country": r["country"] or "US",
            "salary": r["salary"],
            "url": r["url"],
            "category": r["category"],
            "priority": r["priority"],
            "active": bool(r["active"]),
            "source": r["source"],
        })

        if len(items) >= limit:
            break

    return {"count": len(items), "items": items}


@app.get("/jobs/mcdonalds")
def get_mcdonalds(limit: int = 200):
    rows = get_active_jobs_ordered()
    rows = _sort_rows(rows)
    items = []
    for r in rows:
        company = (r["company"] or "").lower()
        source = (r["source"] or "").lower()
        if "mcdonald" in company or source == "mchire":
            items.append(r)
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
