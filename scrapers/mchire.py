# scrapers/mchire.py
from __future__ import annotations
import requests

API_URL = "https://www.mchire.com/api/v1/jobs"

def fetch_mchire(max_pages: int = 50):
    """
    McHire às vezes devolve HTML em vez de JSON. Aqui a gente tenta JSON,
    se não for JSON a gente só para (mas não quebra o coletor).
    """
    jobs = []
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (JobBot)"})

    empty_in_a_row = 0

    for page in range(1, max_pages + 1):
        try:
            resp = session.get(f"{API_URL}?page={page}", timeout=15)
        except Exception as e:
            print(f"[McHire] erro HTTP na página {page}: {e}")
            empty_in_a_row += 1
            if empty_in_a_row >= 3:
                print("[McHire] 3 páginas seguidas com erro HTTP, parando.")
                break
            continue

        # às vezes ele devolve HTML, não JSON
        ct = resp.headers.get("content-type", "")
        if "application/json" not in ct:
            print(f"[McHire] página {page} não retornou JSON")
            empty_in_a_row += 1
            if empty_in_a_row >= 3:
                print("[McHire] 3 páginas seguidas sem JSON, encerrando só McHire.")
                break
            continue

        try:
            data = resp.json()
        except Exception:
            print(f"[McHire] página {page} não pôde ser parseada como JSON")
            empty_in_a_row += 1
            if empty_in_a_row >= 3:
                print("[McHire] 3 páginas seguidas sem JSON, encerrando só McHire.")
                break
            continue

        items = data.get("jobs") or data.get("items") or []
        if not items:
            empty_in_a_row += 1
            if empty_in_a_row >= 3:
                print("[McHire] 3 páginas seguidas vazias, encerrando.")
                break
            continue

        empty_in_a_row = 0

        for j in items:
            url = j.get("job_url") or j.get("url")
            if not url:
                # agora só URL é obrigatório
                continue

            jobs.append({
                "source": "mchire",
                "external_id": str(j.get("id") or ""),
                "title": j.get("title") or j.get("position") or "McDonald's Job",
                "company": j.get("company") or "McDonald's",
                "description": j.get("description") or "",
                "location": j.get("location") or "",
                "salary": j.get("salary") or "",
                "url": url,
            })

    print(f"✅ McDonald's (McHire): {len(jobs)} vagas (brutas)")
    return jobs
