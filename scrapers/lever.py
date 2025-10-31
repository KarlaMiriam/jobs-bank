# scrapers/lever.py
import requests

def fetch_lever(company: str):
    url = f"https://api.lever.co/v0/postings/{company}?mode=json"
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"[lever] erro ao buscar {company}: {e}")
        return []

    try:
        jobs = resp.json()
    except Exception:
        return []

    out = []
    for job in jobs:
        title = job.get("text") or "Untitled"
        hosted = job.get("hostedUrl") or ""
        cats = job.get("categories") or {}
        loc = cats.get("location") or ""
        desc = job.get("description") or ""

        out.append({
            "source": "lever",
            "external_id": str(job.get("id") or ""),
            "title": title,
            "company": company,
            "description": desc,
            "location": loc,
            "salary": "",
            "url": hosted,
        })
    return out
