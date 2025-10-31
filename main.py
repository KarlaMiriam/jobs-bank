from db import init_db, upsert_job, get_active_jobs_ordered
from normalize import normalize_job
from sources import SOURCES
from scrapers import (
    fetch_mchire,
    fetch_greenhouse,
    fetch_workday,
    fetch_ihg,
    fetch_hilton_html,
    fetch_walmart,
    fetch_icims,
)

def main():
    print("🟣 JobBot iniciando coleta...")
    init_db()
    total = 0

    for src in SOURCES:
        t = src["type"]
        name = src["name"]

        jobs = []
        if t == "mchire":
            jobs = fetch_mchire(src["url"])
        elif t == "greenhouse":
            jobs = fetch_greenhouse(src["slug"], src.get("company", ""))
        elif t == "workday":
            jobs = fetch_workday(src["url"], src.get("company", ""))
        elif t == "ihg":
            jobs = fetch_ihg(src["url"])
        elif t == "hilton-html":
            jobs = fetch_hilton_html(src["url"])
        elif t == "walmart":
            jobs = fetch_walmart(src["url"])
        elif t == "icims":
            jobs = fetch_icims(src["url"])
        else:
            print(f"[warn] tipo de fonte desconhecido: {t}")

        print(f"✅ {name}: {len(jobs)} vagas (brutas)")
        for j in jobs:
            norm = normalize_job(j)
            if norm["url"]:
                upsert_job(norm)
                total += 1

    active = get_active_jobs_ordered()
    print(f"📦 vagas ativas agora: {len(active)}")
    for r in active[:50]:
        print(f"[{r['priority']}] {r['title']} – {r['company']} -> {r['url']}")


if __name__ == "__main__":
    main()
