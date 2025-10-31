# main.py
from __future__ import annotations
from datetime import datetime
from pathlib import Path

from db import init_db, upsert_job, get_active_jobs_ordered
from normalize import normalize_job
from sources import SOURCES
from scrapers.mchire import fetch_mchire
from scrapers.workday import fetch_workday
from scrapers.greenhouse import fetch_greenhouse
from scrapers.ihg import fetch_ihg
from scrapers.hilton_html import fetch_hilton_html
from scrapers.walmart import fetch_walmart
from scrapers.icims import fetch_icims
from scrapers.lever import fetch_lever

OUTPUT_JSON = Path("jobs.json")

def main():
    print("🟣 JobBot iniciando coleta...")
    init_db()

    all_jobs = []

    for src in SOURCES:
        t = src["type"]

        try:
            if t == "mchire":
                jobs = fetch_mchire()
            elif t == "workday":
                jobs = fetch_workday(src["url"], employer=src.get("company"))
            elif t == "greenhouse":
                jobs = fetch_greenhouse(src["slug"], company=src.get("company"))
            elif t == "ihg":
                jobs = fetch_ihg(src["url"])
            elif t == "hilton-html":
                jobs = fetch_hilton_html(src["url"])
            elif t == "walmart":
                jobs = fetch_walmart(src["url"])
            elif t == "icims":
                jobs = fetch_icims(src["url"])
            elif t == "lever":
                jobs = fetch_lever(
                    src["company"],
                    include_departments=src.get("include_departments"),
                    include_keywords=src.get("include_keywords"),
                    exclude_keywords=src.get("exclude_keywords"),
                )
            else:
                print(f"[warn] tipo de fonte não suportado: {t}")
                jobs = []
        except Exception as e:
            print(f"[{t}] erro ao coletar {src.get('name')}: {e}")
            jobs = []

        print(f"✅ {src.get('name')}: {len(jobs)} vagas (brutas)")
        all_jobs.extend(jobs)

    # agora normaliza e grava
    active_count = 0
    for raw in all_jobs:
        norm = normalize_job(raw)

        # 👉 única coisa obrigatória agora: URL
        if not norm.get("url"):
            continue

        upsert_job(norm)
        active_count += 1

    # salva json pra debug
    from db import get_active_jobs_ordered
    rows = get_active_jobs_ordered()

    data = {
        "generated_at": datetime.utcnow().isoformat(),
        "count": len(rows),
        "items": rows,
    }
    OUTPUT_JSON.write_text(
        __import__("json").dumps(data, indent=2),
        encoding="utf-8"
    )
    print(f"📦 vagas ativas agora: {len(rows)}")
    for r in rows[:50]:
        print(f"[{r['priority']}] {r['title']} – {r['company']} -> {r['url']}")

if __name__ == "__main__":
    main()
