def normalize_job(raw: dict) -> dict:
    """
    Garante que todo mundo tenha pelo menos url.
    O resto pode ser vazio.
    """
    return {
        "url": (raw.get("url") or "").strip(),
        "title": raw.get("title") or "",
        "company": raw.get("company") or "",
        "description": raw.get("description") or "",
        "city": raw.get("city") or "",
        "state": raw.get("state") or "",
        "country": raw.get("country") or "",
        "salary": raw.get("salary") or "",
        "category": raw.get("category") or "",
        "source": raw.get("source") or "",
        "priority": raw.get("priority", 0),
    }
