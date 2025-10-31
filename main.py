# main.py

from pathlib import Path
import json

from sources import SOURCES

from scrapers import (
    fetch_greenhouse,
    fetch_lever,
    fetch_workday,
    fetch_mchire,
    fetch_ihg,
    fetch_wendys,
    fetch_walmart,
    fetch_hilton_html,
    fetch_icims,
)

from db import (
    init_db,
    upsert_job,
    mark_inactive_except,
    get_active_jobs_ordered,
)
from priority import score_job
from normalize import is_us_location, split_city_state

# empresas tech que queremos empurrar pra baixo
LOW_PRIORITY_COMPANIES = {
    "airbnb", "stripe", "datadog", "cloudflare", "dropbox", "github",
    "discord", "asana", "coinbase", "notion", "atlassian", "figma",
    "rippling", "openai", "slack", "databricks", "affirm", "hubspot",
    "twilio", "plaid", "doordash", "zapier"
}

# fontes que PODEM vir sem localização e mesmo assim queremos manter
RELAXED_SOURCES = {
    "wendys",
    "ihg",
    "hilton-html",
    "hilton",
    "walmart",
    "icims",
    "workday",
}

def sort_rows_for_business(rows):
    def key(r):
        source = (r["source"] or "").lower()
        company = (r["company"] or "").lower()
        category = (r["category"] or "").lower()
        priority = r["priority"] or 0

        # 1. sempre McDonald's
        if source == "mchire" or "mcdonald" in company:
            return (0, -priority)
        # 2. hotel / housekeeping
        if category == "hotel" or "hotel" in company or "resort" in company:
            return (1, -priority)
        # 3. rural / agro / food processing
        if category in ("agriculture", "landscaping", "food_processing"):
            return (2, -priority)
        # 9. tech e empresas que você não quer no topo
        if company in LOW_PRIORITY_COMPANIES:
            return (9, -priority)
        # 5. demais
        return (5, -priority)

    return sorted(rows, key=key)


def export_to_json():
    rows = get_active_jobs_ordered()
    rows = sort_rows_for_business(rows)
    data = []
    for r in rows:
        data.append({
            "title": r["title"],
            "company": r["company"],
            "description": r["description"],
            "city": r["city"],
            "state": r["state"],
            "country": r["country"],
            "salary": r["salary"],
            "url": r["url"],
            "category": r["category"],
            "priority": r["priority"],
            "active": bool(r["active"]),
            "source": r["source"],
        })
    out_path = Path(__file__).parent / "jobs.json"
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"💾 JSON atualizado em: {out_path}")


def main():
    init_db()
    all_urls_this_run: list[str] = []

    for src in SOURCES:
        src_type = src["type"]
        name = src["name"]

        # chama o scraper certo
        if src_type == "greenhouse":
            jobs = fetch_greenhouse(
                src["slug"],
                company_name=src.get("company")
            )
        elif src_type == "lever":
            jobs = fetch_lever(
                company=src["company"],
                include_departments=src.get("include_departments"),
                include_keywords=src.get("include_keywords"),
                exclude_keywords=src.get("exclude_keywords"),
            )
        elif src_type == "workday":
            jobs = fetch_workday(
                src["url"],
                employer=src.get("company") or src.get("name"),
                max_pages=src.get("pages", 40),
            )
        elif src_type == "mchire":
            jobs = fetch_mchire(src["url"])
        elif src_type == "ihg":
            jobs = fetch_ihg(src["url"])
        elif src_type == "wendys":
            jobs = fetch_wendys(src["url"])
        elif src_type == "walmart":
            jobs = fetch_walmart(src["url"])
        elif src_type == "hilton-html":
            jobs = fetch_hilton_html(src["url"])
        elif src_type == "icims":
            jobs = fetch_icims(src["url"])
        else:
            jobs = []

        print(f"✅ {name}: {len(jobs)} vagas (brutas)")

        for j in jobs:
            raw_loc = j.get("location") or ""
            source_name = (j.get("source") or src_type or "").lower()
            company_name = (j.get("company") or name or "").lower()

            # 👉 FILTRO DE LOCALIZAÇÃO (ajustado)
            # regra antiga: só McHire podia vir sem localização
            # regra nova: McHire + fontes que você passou manualmente (wendys, ihg, hilton, walmart, icims, workday)
            if source_name not in ("mchire",) and source_name not in RELAXED_SOURCES:
                # aqui sim vamos exigir EUA
                if raw_loc and not is_us_location(raw_loc):
                    continue
                # se não tem localização e não é fonte relaxada, pula
                if not raw_loc:
                    continue

            title = j.get("title") or ""
            desc = j.get("description") or ""

            base_priority, category = score_job(title, desc)

            # bônus de negócio
            bonus = 0
            if source_name == "mchire" or "mcdonald" in company_name:
                bonus = 5000
            elif category == "hotel" or "hotel" in company_name or "resort" in company_name:
                bonus = 4000
            elif category in ("agriculture", "landscaping", "food_processing"):
                bonus = 3500
            elif company_name in LOW_PRIORITY_COMPANIES:
                bonus = -2000

            final_priority = base_priority + bonus

            city, state = ("", "")
            if raw_loc:
                city, state = split_city_state(raw_loc)

            normalized = {
                "source": j.get("source") or src_type,
                "external_id": j.get("external_id") or "",
                "title": title,
                "company": j.get("company") or name,
                "description": desc,
                "city": city,
                "state": state,
                "country": "US",
                "salary": j.get("salary") or "",
                "url": j.get("url") or "",
                "category": category,
                "priority": final_priority,
            }

            # regra que você pediu: tem que ter link
            if not normalized["url"]:
                continue

            upsert_job(normalized)
            all_urls_this_run.append(normalized["url"])

    # desativar o que não veio nessa rodada
    mark_inactive_except(all_urls_this_run)

    # debug bonitinho
    active = get_active_jobs_ordered()
    active_sorted = sort_rows_for_business(active)
    print(f"📦 vagas ativas agora: {len(active_sorted)}")
    for r in active_sorted[:30]:
        print(f"[{r['priority']}] {r['title']} – {r['company']} – {r['city']}, {r['state']} -> {r['url']}")

    export_to_json()


if __name__ == "__main__":
    main()
