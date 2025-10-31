# scrapers/greenhouse.py
import requests


def fetch_greenhouse(slug: str, company: str | None = None):
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[greenhouse] erro ao buscar {slug}: {e}")
        return []

    try:
        data = resp.json()
    except Exception as exc:
        print(f"[greenhouse] resposta inválida para {slug}: {exc}")
        return []
    jobs = data.get("jobs") or []
    out = []
    for job in jobs:
        title = job.get("title") or "Greenhouse Job"
        locs = job.get("location") or {}
        loc = locs.get("name") or ""
        apply_url = job.get("absolute_url") or job.get("url") or ""

        out.append({
            "source": "greenhouse",
            "external_id": str(job.get("id") or ""),
            "title": title,
            "company": company or slug,
            "description": job.get("content") or "",
            "city": loc,
            "state": "",
            "country": "",
            "salary": "",
            "url": apply_url,
            "category": "other",
            "priority": 10,
            "active": True,
        })
    return out
