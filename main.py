# main.py (trecho principal)

from db import init_db, upsert_job, mark_missing_as_inactive
from normalize import normalize_job
from sources import SOURCES
from scrapers import (
    fetch_mchire,
    fetch_workday,
    fetch_greenhouse,
    fetch_lever,
    fetch_ihg,
    fetch_hilton_html,
    fetch_walmart,
    fetch_icims,
)

def main():
    print("🟣 JobBot iniciando coleta...")
    init_db()

    all_urls = []

    for src in SOURCES:
        t = src["type"]

        if t == "mchire":
            raw_jobs = fetch_mchire(src["url"])
        elif t == "workday":
            raw_jobs = fetch_workday(src["url"], employer=src.get("company"))
        elif t == "greenhouse":
            raw_jobs = fetch_greenhouse(src["slug"], company=src.get("company"))
        elif t == "lever":
            raw_jobs = fetch_lever(
                src["company"],
                include_departments=src.get("include_departments"),
                include_keywords=src.get("include_keywords"),
                exclude_keywords=src.get("exclude_keywords"),
            )
        elif t == "ihg":
            raw_jobs = fetch_ihg(src["url"])
        elif t == "hilton-html":
            raw_jobs = fetch_hilton_html(src["url"])
        elif t == "walmart":
            raw_jobs = fetch_walmart(src["url"])
        elif t == "icims":
            raw_jobs = fetch_icims(src["url"])
        else:
            raw_jobs = []

        print(f"✅ {src['name']}: {len(raw_jobs)} vagas (brutas)")

        for r in raw_jobs:
            norm = normalize_job(r)
            if not norm:
                continue  # não tem link
            upsert_job(norm)
            all_urls.append(norm["url"])

    # marca as que não vieram como inativas
    mark_missing_as_inactive(all_urls)
    print(f"📦 vagas ativas agora: {len(all_urls)}")


if __name__ == "__main__":
    main()
