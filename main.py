# main.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple
from urllib.parse import urlparse

from scrapers.greenhouse import fetch_greenhouse
from scrapers.mchire import fetch_mchire
from scrapers.workday import fetch_workday  # aceita (tenant_host, tenant, site)
from scrapers.adzuna import fetch_adzuna, fetch_adzuna_bulk  # Adzuna

from sources import SOURCES
from normalize import normalize_job, apply_defaults
from db import init_db, upsert_job, get_active_jobs_ordered
from utils.geo import looks_like_us_city_state


def workday_url_to_parts(url: str) -> Tuple[str, str, str]:
    """Extrai (tenant_host, tenant, site) de uma URL Workday."""
    p = urlparse(url)
    host = p.netloc or ""
    tenant = host.split(".")[0] if host else ""
    site = p.path.strip("/").split("/")[0] if p.path else ""
    return host, tenant, site


def collect_from_source(src: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Dispara o scraper correto conforme src['type'].
    Retorna uma lista de dicts "raw" (formato do scraper).
    """
    t = src.get("type")
    try:
        if t == "greenhouse":
            return fetch_greenhouse(slug=src["slug"], company=src.get("company"))

        if t == "mchire":
            # 1) tentar via Playwright (se disponível)
            try:
                from scrapers.mchire_playwright import fetch_mchire_playwright
                jobs_js = fetch_mchire_playwright(src.get("url") or "")
                if jobs_js:
                    return jobs_js
            except Exception as e:
                print(f"[McHire/Playwright] falhou: {e}")
            # 2) fallback HTML estático
            return fetch_mchire(src["url"])

        if t == "workday":
            host, tenant, site = workday_url_to_parts(src["url"])
            return fetch_workday(tenant_host=host, tenant=tenant, site=site)

        # opcionais
        if t == "ihg":
            try:
                from scrapers.ihg import fetch_ihg
                return fetch_ihg(src["url"])
            except Exception:
                return []
        if t == "hilton-html":
            try:
                from scrapers.hilton import fetch_hilton_html
                return fetch_hilton_html(src["url"])
            except Exception:
                return []
        if t == "walmart":
            try:
                from scrapers.walmart import fetch_walmart
                return fetch_walmart(src["url"])
            except Exception:
                return []
        if t == "icims":
            try:
                from scrapers.icims import fetch_icims
                return fetch_icims(src["url"])
            except Exception:
                return []
    except Exception as e:
        print(f"[{t}] erro inesperado: {e}")

    return []


def is_us_job(norm: Dict[str, Any], fallback_loc: str = "") -> bool:
    """
    Heurística para EUA:
    - Se country já é US/USA/United States → aprova.
    - Senão, verifica city/state/strings no fallback.
    """
    country = (norm.get("country") or "").replace(".", "").strip().upper()
    if country in ("US", "USA", "UNITED STATES"):
        return True

    city = (norm.get("city") or "").strip()
    state = (norm.get("state") or "").strip()
    fb = fallback_loc or ", ".join([city, state, country]).strip(", ")
    return looks_like_us_city_state(city, state, country, fb)


def _process_and_save(
    name: str,
    raw_jobs: List[Dict[str, Any]],
    *,
    source_type: str,
    default_company: str = "",
) -> int:
    """Normaliza, filtra EUA, aplica defaults e salva. Retorna quantos foram salvos."""
    normalized_items: List[tuple[Dict[str, Any], Dict[str, Any]]] = []
    for raw in raw_jobs:
        try:
            norm = normalize_job(raw, source_type=source_type, default_company=default_company)
            if not norm:
                continue
            if not norm.get("url") or not norm.get("title"):
                # url e title são obrigatórios
                continue
            normalized_items.append((norm, raw))
        except Exception as e:
            print(f"[{name}] erro ao normalizar item: {e}")

    # filtro EUA usando fallback de possíveis chaves de localização brutas
    filtered: List[Dict[str, Any]] = []
    for norm, raw in normalized_items:
        fallback_loc = ""
        for k in ("location", "locations", "city", "state", "country"):
            v = raw.get(k)
            if isinstance(v, str) and v.strip():
                fallback_loc = v
                break
        try:
            if is_us_job(norm, fallback_loc=fallback_loc):
                filtered.append(norm)
        except Exception as e:
            print(f"[{name}] erro no filtro EUA: {e}")

    # salvar aplicando defaults
    saved = 0
    for job in filtered:
        try:
            job = apply_defaults(job)
            upsert_job(job)
            saved += 1
        except Exception as e:
            print(f"[{name}] erro ao salvar no DB: {e}")

    return saved


def main():
    print("🟣 JobBot iniciando coleta...")
    init_db()

    # 1) Rodar fontes fixas
    for src in SOURCES:
        name = src.get("name") or src.get("company") or src.get("type")
        try:
            raw_jobs = collect_from_source(src) or []
        except Exception as e:
            print(f"❌ {name}: falha ao coletar - {e}")
            raw_jobs = []

        saved = _process_and_save(
            name,
            raw_jobs,
            source_type=src.get("type", ""),
            default_company=src.get("company", ""),
        )
        print(f"✅ {name}: {len(raw_jobs)} vagas (brutas) | salvas EUA: {saved}")

    # 2) Batches Adzuna (volume)
    BATCH_A = [
        "housekeeper", "room attendant", "janitor", "custodian",
        "hotel housekeeping", "cleaner", "laundry attendant",
        "lobby attendant", "public area attendant",
    ]
    BATCH_B = [
        "dishwasher", "line cook", "prep cook", "food prep",
        "restaurant crew", "fast food", "kitchen helper",
    ]
    BATCH_C = [
        "maintenance", "maintenance mechanic", "general labor",
        "groundskeeper", "handyman", "porter",
    ]
    BATCH_D = [
        "farm worker", "agricultural", "warehouse associate",
        "production worker", "poultry",
    ]

    batches = [
        ("Adzuna bulk A", BATCH_A),
        ("Adzuna bulk B", BATCH_B),
        ("Adzuna bulk C", BATCH_C),
        ("Adzuna bulk D", BATCH_D),
    ]

    for label, terms in batches:
        try:
            raw_jobs = fetch_adzuna_bulk(
                terms,
                where=None,           # país já é US na URL da API
                pages=6,              # mais páginas para volume
                results_per_page=50,  # máximo Adzuna
                max_days_old=60,      # janela maior para aumentar volume
                jitter_sec=0.2,
            )
            saved = _process_and_save(label, raw_jobs, source_type="adzuna", default_company="")
            print(f"✅ {label}: {len(raw_jobs)} vagas (brutas) | salvas EUA: {saved}")
        except Exception as e:
            print(f"[adzuna] erro: {e}")

    # 3) Snapshot
    try:
        rows = get_active_jobs_ordered()
        print(f"📦 vagas ativas agora: {len(rows)}")
    except Exception as e:
        print(f"⚠️ erro ao consultar snapshot final: {e}")


if __name__ == "__main__":
    main()
