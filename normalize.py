# normalize.py

def normalize_job(raw: dict) -> dict:
    """
    Garante que todo job tenha ao menos url.
    O resto pode ser vazio.
    """
    url = (raw.get("url") or "").strip()
    if not url:
        # sem link não salva
        return {}

    return {
        "url": url,
        "title": raw.get("title") or "",
        "company": raw.get("company") or "",
        "description": raw.get("description") or "",
        "city": raw.get("city") or "",
        "state": raw.get("state") or "",
        "country": raw.get("country") or "",
        "salary": raw.get("salary") or "",
        "category": raw.get("category") or "",
        "priority": raw.get("priority") or 0,
        "source": raw.get("source") or "",
        "external_id": raw.get("external_id") or "",
    }
