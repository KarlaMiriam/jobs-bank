# main_canada.py
from __future__ import annotations

import re
import time
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from db import init_db, upsert_job, get_conn

BASE_URL = "https://www.jobbank.gc.ca/jobsearch/jobsearch"

# Mesmo filtro que você usa na URL:
# https://www.jobbank.gc.ca/jobsearch/jobsearch?page=1&sort=M&fskl=101020&fskl=101010
COMMON_PARAMS = {
    "sort": "M",
    "fskl": ["101020", "101010"],
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JobBot-Canada/1.0; +https://example.com)",
    "Accept-Language": "en-CA,en;q=0.9",
}


def clean_jobbank_text(text: str) -> str:
    """
    Limpa o texto do card para ficar bonito no site:
    - remove 'Job Bank'
    - remove 'Job number: 123456'
    - remove bloco de favoritos / login (Save to favourites, Sign in, Sign up...)
    - normaliza espaços
    """
    # normaliza espaços primeiro
    text = " ".join(text.split())

    # remove 'Job Bank'
    text = re.sub(r"\bJob\s*Bank\b", "", text, flags=re.IGNORECASE)

    # remove 'Job number: 3441396'
    text = re.sub(r"Job\s*number:\s*\d+", "", text, flags=re.IGNORECASE)

    # remove tudo a partir de 'Save to favourites' (favoritos, login, signup...)
    text = re.sub(r"Save to favourites.*$", "", text, flags=re.IGNORECASE)

    # remove restos de login/conta
    text = re.sub(r"\bSign in\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bSign up\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bPlus account\b", "", text, flags=re.IGNORECASE)

    # normaliza de novo e tira pontas
    text = " ".join(text.split())
    text = text.strip(" -•\n\t ")

    return text


def extract_city_state(location_str: str) -> (str, str):
    """
    Recebe algo tipo:
      'Lévis (QC)'
      'Burnaby (BC)'
    e devolve (city, state).
    """
    city = location_str.strip()
    state = ""
    m = re.search(r"(.+?) \(([A-Z]{2})\)", location_str)
    if m:
        city = m.group(1).strip()
        state = m.group(2).strip()
    return city, state


def parse_job_summary(text: str) -> Optional[Dict[str, Any]]:
    """
    Recebe o texto completo do link da vaga (a.get_text())
    e tenta extrair:
      - title (cargo)
      - company
      - city, state
      - salary

    Exemplo de texto (depois de normalizar espaços):
      'New On site Direct Apply Posted on Job Bank This job was posted directly
       by the employer on Job Bank. LMIA requested Job Bank long haul truck driver
       November 13, 2025 NORTHWEST FREIGHTWAYS LTD Location Surrey (BC)
       Salary $37.00 hourly Job Bank Job number: 3441396'
    """

    # normaliza espaços
    text = " ".join(text.split())

    pattern = (
        r"Job Bank\s*([A-Za-z0-9 \-\/]+?)\s+"      # título após 'Job Bank'
        r"([A-Z][a-z]+ \d{1,2}, \d{4})\s+"        # data ex: November 13, 2025
        r"(.+?)\s+"                               # company
        r"Location\s+(.+?\([A-Z]{2}\))\s+"        # location tipo 'Surrey (BC)'
        r"Salary\s+(.+?)(?:\s+Job\b|\s+Job\s+number|\s*$)"  # salary
    )

    m = re.search(pattern, text)
    if not m:
        return None

    title, date_str, company, location_str, salary_str = m.groups()

    city, state = extract_city_state(location_str)

    return {
        "title": title.strip(),
        "company": company.strip(),
        "city": city,
        "state": state,
        "salary": salary_str.strip(),
    }


def fetch_jobbank_page(page: int) -> List[Dict[str, Any]]:
    """
    Busca uma página de resultados do Job Bank e devolve uma lista de jobs.

    NÃO depende de <span property="title">.
    Usa o texto do <a> e extrai o título/cargo via regex.
    """
    params = COMMON_PARAMS.copy()
    params["page"] = str(page)

    resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    jobs: List[Dict[str, Any]] = []
    seen_urls: set[str] = set()

    # Mesmo jeito que funcionava antes: pega todos <a> de jobposting
    for a in soup.select('a[href*="/jobsearch/jobposting/"]'):
        href = a.get("href")
        if not href:
            continue

        full_url = urljoin("https://www.jobbank.gc.ca", href)
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        # Texto bruto (é aquele que tava indo pra title antes)
        raw_text = " ".join(a.stripped_strings)
        if not raw_text:
            continue

        # Tenta extrair os campos bonitinhos
        parsed = parse_job_summary(raw_text)

        # Description sempre vem do texto LIMPO
        description = clean_jobbank_text(raw_text)

        if not parsed:
            # Se regex não casar, salva pelo menos description e url,
            # e deixa o title igual ao description (ou parte dele)
            job: Dict[str, Any] = {
                "url": full_url,
                "title": description,   # fallback (ideal é regex casar)
                "company": "",
                "description": description,
                "city": "",
                "state": "",
                "country": "CA",
                "salary": "",
                "category": "jobbank_canada",
                "priority": 30,
                "active": 1,
                "source": "jobbank_gc_ca",
            }
            jobs.append(job)
            continue

        # Aqui é o fluxo ideal: temos um title bonitinho
        job: Dict[str, Any] = {
            "url": full_url,
            "title": parsed["title"],      # 👈 só o cargo, ex: 'long haul truck driver'
            "company": parsed["company"],
            "description": description,    # 👈 texto enxuto, sem 'Job Bank'
            "city": parsed["city"],
            "state": parsed["state"],
            "country": "CA",
            "salary": parsed["salary"],
            "category": "jobbank_canada",
            "priority": 30,
            "active": 1,
            "source": "jobbank_gc_ca",
        }
        jobs.append(job)

    return jobs


def deactivate_old_canada_jobs(urls_to_keep: List[str]) -> None:
    """
    Marca como inativas todas as vagas do país 'CA' cuja URL
    NÃO esteja em urls_to_keep. Não mexe nas vagas dos EUA.
    """
    with get_conn() as conn:
        if urls_to_keep:
            placeholders = ",".join("?" for _ in urls_to_keep)
            sql = f"""
                UPDATE jobs
                SET active = 0,
                    updated_at = datetime('now')
                WHERE country = 'CA'
                  AND url NOT IN ({placeholders});
            """
            conn.execute(sql, urls_to_keep)
        else:
            conn.execute("""
                UPDATE jobs
                SET active = 0,
                    updated_at = datetime('now')
                WHERE country = 'CA';
            """)
        conn.commit()


def main():
    print("🍁 JobBot Canada iniciando coleta (Job Bank)...")
    init_db()

    all_jobs: List[Dict[str, Any]] = []
    seen_urls: set[str] = set()

    # Limite de segurança de páginas
    MAX_PAGES = 200

    page = 1
    while page <= MAX_PAGES:
        print(f"➡️  Página {page}...")
        try:
            page_jobs = fetch_jobbank_page(page)
        except Exception as e:
            print(f"❌ Erro ao buscar página {page}: {e}")
            break

        if not page_jobs:
            print("⚠️ Nenhuma vaga encontrada nessa página, parando.")
            break

        added_this_page = 0
        for job in page_jobs:
            if job["url"] in seen_urls:
                continue
            seen_urls.add(job["url"])
            all_jobs.append(job)
            added_this_page += 1

        print(f"📄 Página {page}: {added_this_page} vagas novas.")
        time.sleep(1.0)
        page += 1

    print(f"📦 Total de vagas Job Bank coletadas (antes de salvar): {len(all_jobs)}")

    saved = 0
    for job in all_jobs:
        try:
            upsert_job(job)
            saved += 1
        except Exception as e:
            print(f"⚠️ Erro ao salvar vaga {job.get('url')}: {e}")

    print(f"✅ Vagas Job Bank salvas/atualizadas: {saved}")

    deactivate_old_canada_jobs(list(seen_urls))
    print("🧹 Vagas antigas do Canadá marcadas como inativas.")

    print("🏁 JobBot Canada finalizado.")


if __name__ == "__main__":
    main()
