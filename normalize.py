# normalize.py
from __future__ import annotations
from typing import Dict, Any
from utils.geo import US_STATE_ABBR, extract_city_state_country, pick_us_piece


def _basic_clean(s: str | None) -> str:
    return (s or "").strip()


def normalize_job(
    raw: Dict[str, Any],
    *,
    source_type: str | None = None,
    default_company: str = "",
) -> Dict[str, Any] | None:
    """
    Converte o dict 'raw' de cada scraper para um formato unificado:
    {
      source, url, title, company, description,
      city, state, country, salary, category, priority, active
    }
    """
    st = (source_type or "").lower()

    # === ADZUNA ===========================================================
    if st == "adzuna":
        loc = (raw.get("location") or {})
        area = loc.get("area") or []  # e.g. ["USA","Florida","Orlando"]
        country_code = (loc.get("country") or "").upper()

        # heurística simples: penúltimo = state, último = city
        city = ""
        state = ""
        if len(area) >= 2:
            city = _basic_clean(area[-1])
            state = _basic_clean(area[-2])

        comp = raw.get("company")
        company = ""
        if isinstance(comp, dict):
            company = comp.get("display_name") or comp.get("name") or ""
        else:
            company = comp or ""

        title = _basic_clean(raw.get("title"))
        url = _basic_clean(raw.get("redirect_url"))
        if not url or not title:
            return None  # url e title são essenciais

        return {
            "source": "adzuna",
            "url": url,
            "title": title,
            "company": company or default_company,
            "description": _basic_clean(raw.get("description")),
            "city": city,
            "state": state,
            "country": "US" if country_code in ("US", "USA", "UNITED STATES") else country_code,
            "salary": "",
            "category": (raw.get("category", {}) or {}).get("label") or "other",
            "priority": 20,
            "active": True,
        }

    # === GREENHOUSE (genérico) ===========================================
    if st == "greenhouse":
        # Suporta dois formatos: lista v1 e v2
        title = _basic_clean(raw.get("title"))
        url = _basic_clean(raw.get("url") or raw.get("absolute_url"))
        if not title or not url:
            return None

        # location pode ser string ou dict
        city = state = country = ""
        loc = raw.get("location")
        if isinstance(loc, dict):
            # v1/v2: (city, name, country)
            city = _basic_clean(loc.get("name") or loc.get("city"))
        elif isinstance(loc, str):
            city, state, country = extract_city_state_country(loc)

        company = _basic_clean(raw.get("company") or default_company)

        return {
            "source": "greenhouse",
            "url": url,
            "title": title,
            "company": company,
            "description": _basic_clean(raw.get("content") or raw.get("description")),
            "city": city,
            "state": state,
            "country": country,
            "salary": "",
            "category": _basic_clean(raw.get("department") or raw.get("category") or "other"),
            "priority": 50,
            "active": True,
        }

    # === MCHIRE (HTML/links) =============================================
    if st == "mchire":
        title = _basic_clean(raw.get("title") or "McDonald's Job")
        url = _basic_clean(raw.get("url"))
        if not url:
            return None
        return {
            "source": "mchire",
            "url": url,
            "title": title,
            "company": _basic_clean(raw.get("company") or default_company or "McDonald's"),
            "description": _basic_clean(raw.get("description")),
            "city": _basic_clean(raw.get("city")),
            "state": _basic_clean(raw.get("state")),
            "country": _basic_clean(raw.get("country") or "US"),
            "salary": _basic_clean(raw.get("salary")),
            "category": _basic_clean(raw.get("category") or "restaurant"),
            "priority": 5090,
            "active": True,
        }

    # === WORKDAY (já vem tratado no scraper) =============================
    if st == "workday":
        title = _basic_clean(raw.get("title"))
        url = _basic_clean(raw.get("url"))
        if not title or not url:
            return None
        city = _basic_clean(raw.get("city"))
        state = _basic_clean(raw.get("state"))
        country = _basic_clean(raw.get("country"))
        if not (city or state or country):
            # tenta extrair de um location cru, se existir
            loc = _basic_clean(raw.get("location"))
            if loc:
                city, state, country = extract_city_state_country(loc)
        return {
            "source": "workday",
            "url": url,
            "title": title,
            "company": _basic_clean(raw.get("company") or default_company),
            "description": _basic_clean(raw.get("description")),
            "city": city,
            "state": state,
            "country": country,
            "salary": _basic_clean(raw.get("salary")),
            "category": _basic_clean(raw.get("category") or "other"),
            "priority": 40,
            "active": True,
        }

    # === fallback genérico ===============================================
    title = _basic_clean(raw.get("title"))
    url = _basic_clean(raw.get("url"))
    if not title or not url:
        return None
    loc = _basic_clean(raw.get("location") or "")
    city, state, country = extract_city_state_country(loc) if loc else ("", "", "")
    return {
        "source": st or "unknown",
        "url": url,
        "title": title,
        "company": _basic_clean(raw.get("company") or default_company),
        "description": _basic_clean(raw.get("description")),
        "city": city,
        "state": state,
        "country": country,
        "salary": _basic_clean(raw.get("salary")),
        "category": _basic_clean(raw.get("category") or "other"),
        "priority": 10,
        "active": True,
    }


# normalize.py
from typing import Dict, Any

DEFAULTS: Dict[str, Any] = {
    "description": "Candidate-se para saber mais detalhes.",
    "salary": "A combinar",
    "company": "Empresa confidencial",
    "city": "Não informado",
    "state": "Não informado",
    "country": "USA",
    "category": "other",
    "priority": 10,
    "active": True,
    "source": "unknown",
}

def apply_defaults(job: Dict[str, Any]) -> Dict[str, Any]:
    """Preenche campos vazios com valores padrão (sem inventar url/title)."""
    j = dict(job)
    for k, v in DEFAULTS.items():
        if j.get(k) is None or (isinstance(j.get(k), str) and j.get(k).strip() == ""):
            j[k] = v
    return j
