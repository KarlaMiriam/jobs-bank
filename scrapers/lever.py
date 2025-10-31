# scrapers/lever.py
from __future__ import annotations

from typing import Iterable, Optional

import requests


def _normalize_keywords(values: Optional[Iterable[str]]) -> list[str]:
    if not values:
        return []
    return [v.lower() for v in values if v]


def fetch_lever(
    company: str,
    include_departments: Optional[Iterable[str]] = None,
    include_keywords: Optional[Iterable[str]] = None,
    exclude_keywords: Optional[Iterable[str]] = None,
):
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
        print(f"[lever] resposta inválida para {company}")
        return []

    include_departments = set(v.lower() for v in include_departments or [])
    include_keywords = _normalize_keywords(include_keywords)
    exclude_keywords = _normalize_keywords(exclude_keywords)

    out = []
    for job in jobs:
        title = (job.get("text") or "").strip() or "Untitled"
        hosted = job.get("hostedUrl") or ""
        cats = job.get("categories") or {}
        loc = cats.get("location") or ""
        desc = job.get("descriptionPlain") or job.get("description") or ""

        if include_departments:
            departments = job.get("departments") or []
            dep_match = any((dep or "").lower() in include_departments for dep in departments)
            if not dep_match:
                continue

        searchable_text = f"{title} {desc}".lower()
        if include_keywords and not any(k in searchable_text for k in include_keywords):
            continue
        if exclude_keywords and any(k in searchable_text for k in exclude_keywords):
            continue

        out.append({
            "source": "lever",
            "external_id": str(job.get("id") or ""),
            "title": title,
            "company": job.get("company") or company,
            "description": desc,
            "location": loc,
            "salary": "",
            "url": hosted,
        })
    return out
