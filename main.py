# main.py
from sources import SOURCES
from normalize import normalize_job
from db import init_db, upsert_job, get_active_jobs_ordered

from scrapers.mchire import fetch_mchire
from scrapers.workday import fetch_workday
from scrapers.greenhouse import fetch_greenhouse
from scrapers.lever import fetch_lever
from scrapers.ihg import fetch_ihg
from scrapers.hilton_html import fetch_hilton_html
from scrapers.walmart import fetch_walmart
from scrapers.icims import fetch_icims


def main():
    print("🟣 JobBot iniciando coleta...")
    init_db()  # garante tabela no Render

    total_new = 0

    for src in SOURCES:
        t = src["type"]

        if t == "mchire":
            jobs = fetch_mchire(src["url"])
        elif t == "workday":
            jobs = fetch_workday(src["url"], employer=src.get("company"))
        elif t == "greenhouse":
            jobs = fetch_greenhouse(src["slug"], company=src.get("company"))
        elif t == "lever":
            jobs = fetch_lever(
                src["company"],
                include_departments=src.get("include_departments"),
                include_keywords=src.get("include_keywords"),
                exclude_keywords=src.get("exclude_keywords"),
            )
        elif t == "ihg":
            jobs = fetch_ihg(src["url"])
        elif t == "hilton-html":
            jobs = fetch_hilton_html(src["url"])
        elif t == "walmart":
            jobs = fetch_walmart(src["url"])
        elif t == "icims":
            jobs = fetch_icims(src["url"])
        else:
            print(f"[coletor] tipo não suportado: {t}")
            jobs = []

        print(f"✅ {src['name']}: {len(jobs)} vagas (brutas)")

        for j in jobs:
            norm = normalize_job(j)
            # só salva se tiver link
            if not norm.get("url"):
                continue
            upsert_job(norm)
            total_new += 1

    active = get_active_jobs_ordered()
    print(f"📦 vagas ativas agora: {len(active)}")
    for i, r in enumerate(active[:25]):
        print(f"[{r.get('priority', 0)}] {r.get('title')} – {r.get('company')} -> {r.get('url')}")


if __name__ == "__main__":
    main()
