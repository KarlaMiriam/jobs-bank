# scrapers/greenhouse.py
import requests

def fetch_greenhouse(slug: str):
    """
    Busca vagas no Greenhouse para o board informado.
    Retorna SEMPRE uma lista de dicionários com:
    source, external_id, title, company, description, location, salary, url
    """
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"[greenhouse] erro ao buscar {slug}: {e}")
        return []

    try:
        data = resp.json()
    except Exception:
        print(f"[greenhouse] resposta não é JSON para {slug}")
        return []

    jobs = data.get("jobs", [])
    out = []

    for job in jobs:
        title = job.get("title") or "Untitled"
        abs_url = job.get("absolute_url") or ""
        desc = job.get("content") or ""
        loc = ""
        if isinstance(job.get("location"), dict):
            loc = job["location"].get("name", "") or ""
        external_id = job.get("id") or ""

        out.append({
            "source": "greenhouse",
            "external_id": str(external_id),
            "title": title,
            "company": slug,
            "description": desc,
            "location": loc,
            "salary": "",
            "url": abs_url,
        })

    return out
