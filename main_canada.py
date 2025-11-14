# # main_canada.py
# from __future__ import annotations

# import re
# import time
# from typing import Dict, Any, List
# from urllib.parse import urljoin

# import requests
# from bs4 import BeautifulSoup

# from db import init_db, upsert_job, get_conn

# BASE_URL = "https://www.jobbank.gc.ca/jobsearch/jobsearch"

# # Mesmo filtro que você passou:
# # page=1&sort=M&fskl=101020&fskl=101010
# COMMON_PARAMS = {
#     "sort": "M",
#     "fskl": ["101020", "101010"],
# }

# HEADERS = {
#     # Só um User-Agent normalzinho pra não parecer request bizarro
#     "User-Agent": "Mozilla/5.0 (compatible; JobBot-Canada/1.0; +https://example.com)",
#     "Accept-Language": "en-CA,en;q=0.9",
# }


# def parse_job_summary(text: str) -> Dict[str, Any] | None:
#     """
#     Recebe o texto bruto de um card de vaga do Job Bank (página de resultados)
#     e tenta extrair:
#       - title
#       - company
#       - location (city, province)
#       - salary
#     usando regex baseada no padrão:

#     "Job Bank <title> <Month dd, yyyy> <company> Location <city (XX)> Salary <salary> Job Bank Job number: NNNNN"

#     Exemplo real (compactado):
#     "New ... Job Bank orchard worker November 07, 2025 Suncrest Orchards
#      Location Simcoe (ON) Salary $17.60 hourly Job Bank Job number: 3440629"
#     """

#     # 1) Pega a parte que começa em "Job Bank <titulo...>" e não no "Job Bank This job..."
#     m_anchor = re.search(r"Job Bank [a-z]", text)
#     if not m_anchor:
#         return None

#     sub = text[m_anchor.start():]

#     # 2) Extrai os campos principais
#     pattern = (
#         r"Job Bank (.+?) "                      # title
#         r"([A-Z][a-z]+ \d{2}, \d{4}) "         # date ex: November 07, 2025
#         r"(.+?) "                               # company
#         r"Location (.+?) "                      # location ex: Simcoe (ON)
#         r"Salary (.+?) "                        # salary ex: $17.60 hourly
#         r"Job Bank Job number"
#     )

#     m = re.search(pattern, sub)
#     if not m:
#         # Se não casar, devolve None e essa vaga é ignorada
#         return None

#     title, date_str, company, location_str, salary_str = m.groups()

#     # 3) Quebra location em city / province
#     city = location_str.strip()
#     state = ""
#     m_loc = re.search(r"(.+?) \(([A-Z]{2})\)", location_str)
#     if m_loc:
#         city = m_loc.group(1).strip()
#         state = m_loc.group(2).strip()

#     return {
#         "title": title.strip(),
#         "company": company.strip(),
#         "city": city,
#         "state": state,
#         "salary": salary_str.strip(),
#         # demais campos o caller completa
#     }


# def fetch_jobbank_page(page: int) -> List[Dict[str, Any]]:
#     """
#     Faz request da página de resultados do Job Bank para o 'page' dado,
#     filtra os links que apontam para jobposting e retorna uma lista de dicts
#     com os dados básicos (url, title, company, city, state, salary).
#     """
#     params = COMMON_PARAMS.copy()
#     # fskl pode ser lista, então garantimos isso:
#     params["page"] = str(page)

#     resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
#     resp.raise_for_status()

#     soup = BeautifulSoup(resp.text, "html.parser")

#     jobs: List[Dict[str, Any]] = []

#     # Pega todos os links para jobposting
#     for a in soup.find_all("a", href=True):
#         href = a["href"]
#         if "/jobsearch/jobposting/" not in href:
#             continue

#         full_url = urljoin("https://www.jobbank.gc.ca", href)
#         text = " ".join(a.stripped_strings)

#         parsed = parse_job_summary(text)
#         if not parsed:
#             continue

#         job: Dict[str, Any] = {
#             "url": full_url,
#             "title": parsed["title"],
#             "company": parsed["company"],
#             "description": text,  # pode melhorar pegando a página de detalhe depois
#             "city": parsed["city"],
#             "state": parsed["state"],
#             "country": "CA",
#             "salary": parsed["salary"],
#             "category": "jobbank_canada",
#             "priority": 30,           # mais alto que Adzuna, se quiser
#             "active": 1,
#             "source": "jobbank_gc_ca",
#         }
#         jobs.append(job)

#     return jobs


# def deactivate_old_canada_jobs(urls_to_keep: List[str]) -> None:
#     """
#     Marca como inativas todas as vagas do país 'CA' cuja URL
#     NÃO esteja em urls_to_keep. Não mexe nas vagas dos EUA.
#     """
#     with get_conn() as conn:
#         if urls_to_keep:
#             placeholders = ",".join("?" for _ in urls_to_keep)
#             sql = f"""
#                 UPDATE jobs
#                 SET active = 0,
#                     updated_at = datetime('now')
#                 WHERE country = 'CA'
#                   AND url NOT IN ({placeholders});
#             """
#             conn.execute(sql, urls_to_keep)
#         else:
#             conn.execute("""
#                 UPDATE jobs
#                 SET active = 0,
#                     updated_at = datetime('now')
#                 WHERE country = 'CA';
#             """)
#         conn.commit()


# def main():
#     print("🍁 JobBot Canada iniciando coleta (Job Bank)...")
#     init_db()

#     all_jobs: List[Dict[str, Any]] = []
#     seen_urls: set[str] = set()

#     # Quantas páginas você quer percorrer?
#     # Começa simples (ex: 3 páginas). Depois você aumenta.
#     MAX_PAGES = 3

#     for page in range(1, MAX_PAGES + 1):
#         print(f"➡️  Página {page}...")
#         try:
#             page_jobs = fetch_jobbank_page(page)
#         except Exception as e:
#             print(f"❌ Erro ao buscar página {page}: {e}")
#             break

#         # Se não veio nada, provavelmente acabou
#         if not page_jobs:
#             print("⚠️ Nenhuma vaga encontrada nessa página, parando.")
#             break

#         # Remove duplicadas por URL
#         for job in page_jobs:
#             if job["url"] in seen_urls:
#                 continue
#             seen_urls.add(job["url"])
#             all_jobs.append(job)

#         # pequeno delay simpático
#         time.sleep(1.0)

#     print(f"📦 Total de vagas Job Bank coletadas (antes de salvar): {len(all_jobs)}")

#     # Salvar / upsert em jobs.db
#     saved = 0
#     for job in all_jobs:
#         try:
#             upsert_job(job)
#             saved += 1
#         except Exception as e:
#             print(f"⚠️ Erro ao salvar vaga {job.get('url')}: {e}")

#     print(f"✅ Vagas Job Bank salvas/atualizadas: {saved}")

#     # Desativar vagas antigas do Canadá que não apareceram nesse ciclo
#     deactivate_old_canada_jobs(list(seen_urls))
#     print("🧹 Vagas antigas do Canadá marcadas como inativas.")

#     print("🏁 JobBot Canada finalizado.")


# if __name__ == "__main__":
#     main()








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
    # fskl pode aparecer várias vezes na query string,
    # o requests aceita lista para isso:
    "fskl": ["101020", "101010"],
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JobBot-Canada/1.0; +https://example.com)",
    "Accept-Language": "en-CA,en;q=0.9",
}


def extract_city_state(location_str: str) -> (str, str):
    """
    Recebe algo tipo:
      "Lévis (QC)"
      "Burnaby (BC)"
    e devolve (city, state).
    """
    city = location_str.strip()
    state = ""
    m = re.search(r"(.+?) \(([A-Z]{2})\)", location_str)
    if m:
        city = m.group(1).strip()
        state = m.group(2).strip()
    return city, state


def parse_job_card(title: str, card_text: str) -> Optional[Dict[str, Any]]:
    """
    Usa o texto inteiro do card (todas as strings internas) + o título
    para extrair:
      - company
      - location (city, state)
      - salary
    """

    # Normaliza espaços
    text = " ".join(card_text.split())

    # Começa a partir do título (ignora "New", "Direct Apply", etc.)
    idx = text.find(title)
    if idx == -1:
        return None
    sub = text[idx:]

    pattern = (
        re.escape(title) +
        r"\s+([A-Z][a-z]+ \d{1,2}, \d{4})\s+"  # data (não vamos usar, só pular)
        r"(.+?)\s+"                             # company (lazy)
        r"(.+?\([A-Z]{2}\))\s+"                 # location tipo "Lévis (QC)"
        r"Salary\s+(.+?)(?:\s+Job Bank|\s*$)"   # salary até "Job Bank" ou fim
    )

    m = re.search(pattern, sub)
    if not m:
        return None

    _date_str, company, location_str, salary_str = m.groups()

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
    Busca uma página de resultados do Job Bank e devolve uma lista de jobs
    com: url, title, company, city, state, salary.

    Regra:
    - tenta pegar o título do <span property="title">;
    - se não achar, usa o texto do <a> (fallback).
    """
    params = COMMON_PARAMS.copy()
    params["page"] = str(page)

    resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    jobs: List[Dict[str, Any]] = []
    seen_urls: set[str] = set()

    # Pega todos os links que levam para /jobsearch/jobposting/...
    for a in soup.select('a[href*="/jobsearch/jobposting/"]'):
        href = a.get("href")
        if not href:
            continue

        full_url = urljoin("https://www.jobbank.gc.ca", href)
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        # 1) Tenta pegar o título do <span property="title">
        span_title = a.select_one('span[property="title"]')

        # se não estiver dentro do <a>, tenta buscar no card (pai)
        card = (
            a.find_parent("article")
            or a.find_parent("li")
            or a.find_parent("div")
        )
        if not span_title and card is not None:
            span_title = card.select_one('span[property="title"]')

        if span_title is not None:
            title = span_title.get_text(strip=True)
        else:
            # fallback pra não zerar tudo
            title = a.get_text(strip=True)

        if not title:
            continue

        # Se não achou card, usa pelo menos o título como description
        if card is not None:
            card_text = " ".join(card.stripped_strings)
        else:
            card_text = title

        parsed = parse_job_card(title, card_text)
        if not parsed:
            # não conseguiu extrair company/location/salary — salva parcial
            job: Dict[str, Any] = {
                "url": full_url,
                "title": title,              # título da vaga
                "company": "",
                "description": card_text,    # tudo do card
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

        job: Dict[str, Any] = {
            "url": full_url,
            "title": title,                 # sempre o título que definimos
            "company": parsed["company"],
            "description": card_text,
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

    # Começa com poucas páginas; depois você aumenta.
    MAX_PAGES = 3

    for page in range(1, MAX_PAGES + 1):
        print(f"➡️  Página {page}...")
        try:
            page_jobs = fetch_jobbank_page(page)
        except Exception as e:
            print(f"❌ Erro ao buscar página {page}: {e}")
            break

        if not page_jobs:
            print("⚠️ Nenhuma vaga encontrada nessa página, parando.")
            break

        for job in page_jobs:
            if job["url"] in seen_urls:
                continue
            seen_urls.add(job["url"])
            all_jobs.append(job)

        time.sleep(1.0)

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
