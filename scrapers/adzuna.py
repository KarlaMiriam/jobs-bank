# scrapers/adzuna.py
from __future__ import annotations
import os
import time
from typing import List, Dict, Any, Iterable
import requests


ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs/us/search/{page}"
UA = "Mozilla/5.0 (JobBot Adzuna Collector)"


def _env_keys() -> tuple[str | None, str | None]:
    return os.getenv("ADZUNA_APP_ID"), os.getenv("ADZUNA_APP_KEY")


def _request(
    page: int,
    *,
    what: str = "",
    where: str | None = None,
    results_per_page: int = 50,
    max_days_old: int = 60,
    retries: int = 2,
    backoff_sec: float = 0.8,
) -> Dict[str, Any] | None:
    app_id, app_key = _env_keys()
    if not app_id or not app_key:
        print("[adzuna] faltando ADZUNA_APP_ID/ADZUNA_APP_KEY no ambiente")
        return None

    url = ADZUNA_BASE.format(page=page)
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": min(max(results_per_page, 1), 50),
        "what": what or "",
        "max_days_old": max_days_old,
        "content-type": "application/json",
    }
    if where:
        params["where"] = where

    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=25, headers={"User-Agent": UA})
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            if attempt >= retries:
                print(f"[adzuna] erro final na page {page} ({what=}): {e}")
                return None
            time.sleep(backoff_sec * (attempt + 1))
    return None


def fetch_adzuna(
    *,
    what: str,
    where: str | None = None,
    pages: int = 4,
    results_per_page: int = 50,
    max_days_old: int = 60,
) -> List[Dict[str, Any]]:
    """
    Busca direta no mercado US do Adzuna.
    Retorna lista 'raw' no formato da API do Adzuna.
    """
    out: List[Dict[str, Any]] = []
    for p in range(1, max(1, pages) + 1):
        data = _request(
            p,
            what=what,
            where=where,
            results_per_page=results_per_page,
            max_days_old=max_days_old,
        )
        if not data:
            continue
        results = data.get("results") or []
        out.extend(results)
    return out


def _dedup_by_id(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: set[Any] = set()
    out: List[Dict[str, Any]] = []
    for r in items:
        rid = r.get("id") or r.get("adref") or r.get("redirect_url")
        if rid in seen:
            continue
        seen.add(rid)
        out.append(r)
    return out


def fetch_adzuna_bulk(
    terms: List[str],
    *,
    where: str | None = None,
    pages: int = 4,
    results_per_page: int = 50,
    max_days_old: int = 60,
    jitter_sec: float = 0.2,
) -> List[Dict[str, Any]]:
    """
    Executa várias consultas (what) e consolida + deduplica.
    """
    acc: List[Dict[str, Any]] = []
    for t in terms:
        chunk = fetch_adzuna(
            what=t,
            where=where,
            pages=pages,
            results_per_page=results_per_page,
            max_days_old=max_days_old,
        )
        acc.extend(chunk)
        if jitter_sec:
            time.sleep(jitter_sec)
    return _dedup_by_id(acc)
