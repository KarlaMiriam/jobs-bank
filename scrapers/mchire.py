# # scrapers/mchire.py
# from __future__ import annotations
# from typing import List, Dict
# from urllib.parse import urljoin, urlencode

# from bs4 import BeautifulSoup

# # Tenta com curl_cffi (emula Chrome) e cai para requests se faltar
# try:
#     from curl_cffi import requests as crequests
#     _HAS_CURL = True
# except Exception:
#     _HAS_CURL = False
# import requests


# DEFAULT_LIST_URL = "https://jobs.mchire.com/jobs?location_name=United%20States&location_type=4"

# # Cabeçalhos bem “de navegador”
# BROWSER_HEADERS = {
#     "User-Agent": (
#         "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
#         "AppleWebKit/537.36 (KHTML, like Gecko) "
#         "Chrome/126.0.0.0 Safari/537.36"
#     ),
#     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
#     "Accept-Language": "en-US,en;q=0.9",
#     "Cache-Control": "no-cache",
#     "Pragma": "no-cache",
#     "Upgrade-Insecure-Requests": "1",
# }


# def _get_html(url: str, timeout: int = 25) -> str:
#     """
#     Tenta baixar HTML usando curl_cffi (impersonate Chrome).
#     Se indisponível, usa requests com headers de navegador.
#     """
#     if _HAS_CURL:
#         try:
#             resp = crequests.get(
#                 url,
#                 headers=BROWSER_HEADERS,
#                 timeout=timeout,
#                 impersonate="chrome",  # chave para evitar 403
#             )
#             if resp.status_code == 200 and "text/html" in resp.headers.get("Content-Type", ""):
#                 return resp.text
#         except Exception:
#             pass  # cai para requests

#     # fallback requests
#     r = requests.get(url, headers=BROWSER_HEADERS, timeout=timeout)
#     r.raise_for_status()
#     return r.text


# def _parse_list(html: str, base: str = "https://jobs.mchire.com/") -> List[Dict]:
#     """
#     Procura por âncoras de vagas do McHire no HTML.
#     Regras:
#       - href contendo 'Job?job_id='        -> URL absoluta
#       - título: texto da âncora (ou padrão)
#     """
#     soup = BeautifulSoup(html, "lxml")
#     jobs: List[Dict] = []

#     # 1) Âncoras diretas para a página de vaga
#     for a in soup.find_all("a", href=True):
#         href = a["href"]
#         if "Job?job_id=" not in href:
#             continue
#         full_url = href if href.startswith("http") else urljoin(base, href)
#         title = a.get_text(strip=True) or "McDonald's Job"
#         jobs.append({
#             "source": "mchire",
#             "url": full_url,
#             "title": title,
#             "company": "McDonald's",
#             "description": "",
#             "city": "",
#             "state": "",
#             "country": "US",
#             "salary": "",
#             "category": "restaurant",
#             "priority": 5090,
#         })

#     # 2) Alguns templates usam data-attributes ou botões. Captura extra (opcional)
#     # Exemplo: <button data-job-url="/Job?job_id=...">Apply</button>
#     for tag in soup.find_all(attrs={"data-job-url": True}):
#         href = tag.get("data-job-url")
#         if not href or "Job?job_id=" not in href:
#             continue
#         full_url = href if href.startswith("http") else urljoin(base, href)
#         title = tag.get_text(strip=True) or "McDonald's Job"
#         jobs.append({
#             "source": "mchire",
#             "url": full_url,
#             "title": title,
#             "company": "McDonald's",
#             "description": "",
#             "city": "",
#             "state": "",
#             "country": "US",
#             "salary": "",
#             "category": "restaurant",
#             "priority": 5090,
#         })

#     return jobs


# def fetch_mchire(url: str | None = None, max_pages: int = 1) -> List[Dict]:
#     """
#     Coleta vagas do McHire pelo HTML.
#     - Tenta a URL informada (p.ex. com filtros de localização).
#     - Se não vier nada, tenta automaticamente a lista "United States".
#     max_pages está aqui só para manter assinatura compatível (paginador real não exposto).
#     """
#     target = url or DEFAULT_LIST_URL

#     # 1ª tentativa
#     try:
#         html = _get_html(target, timeout=25)
#         jobs = _parse_list(html)
#         if jobs:
#             print(f"✅ McDonald's (McHire): {len(jobs)} vagas (brutas) [HTML]")
#             return jobs
#         else:
#             print("[McHire] HTML sem links de vaga; tentando fallback United States…")
#     except Exception as e:
#         print(f"[McHire] erro na URL primária: {e}. Tentando fallback United States…")

#     # Fallback forçado: United States
#     try:
#         base = "https://jobs.mchire.com/jobs"
#         fallback_url = f"{base}?{urlencode({'location_name': 'United States', 'location_type': '4'})}"
#         html = _get_html(fallback_url, timeout=25)
#         jobs = _parse_list(html)
#         print(f"✅ McDonald's (McHire): {len(jobs)} vagas (brutas) [fallback]")
#         return jobs
#     except Exception as e:
#         print(f"[McHire] fallback falhou: {e}")
#         return []


# scrapers/mchire.py
from __future__ import annotations
from typing import List, Dict
import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (JobBot; +https://example.com/bot)"
}

def _from_anchor(a) -> Dict:
    href = a.get("href") or ""
    if not href:
        return {}
    if href.startswith("/"):
        full = f"https://www.mchire.com{href}"
    elif href.startswith("http"):
        full = href
    else:
        full = f"https://www.mchire.com/{href}"

    title = a.get_text(strip=True) or "McDonald's Job"
    return {
        "source": "mchire",
        "url": full,
        "title": title,
        "company": "McDonald's",
        "description": "",
        "city": "",
        "state": "",
        "country": "US",
        "salary": "",
        "category": "restaurant",
        "priority": 5090,
    }

def _scrape_html(url: str) -> List[Dict]:
    resp = requests.get(url, timeout=25, headers=HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    jobs: List[Dict] = []

    # 1) Links clássicos
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "Job?job_id=" in href:
            item = _from_anchor(a)
            if item:
                jobs.append(item)

    # 2) Alguns templates usam /jobs/<slug> com data-attrs. Captura cartões também.
    if not jobs:
        for card in soup.select("[data-job-id] a[href], a[href*='/jobs/']"):
            item = _from_anchor(card)
            if item:
                jobs.append(item)

    return jobs

def _fallback_united_states() -> List[Dict]:
    """
    Fallback para listagem agregada de vagas nos EUA (página de landing que já traz anchors).
    """
    url = "https://jobs.mchire.com/jobs?location_name=United%20States&location_type=4"
    try:
        resp = requests.get(url, timeout=25, headers=HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        jobs: List[Dict] = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            # Anchors típicos de detalhe de vaga
            if re.search(r"/Job\?job_id=|/jobs/\w", href, re.I):
                item = _from_anchor(a)
                if item:
                    jobs.append(item)
        return jobs
    except Exception as e:
        print(f"[McHire/fallback US] falhou: {e}")
        return []

def fetch_mchire(url: str) -> List[Dict]:
    """
    Tenta extrair do HTML da página de listagem/landing.
    Se não achar links de vaga, usa fallback 'United States'.
    """
    try:
        jobs = _scrape_html(url)
        if jobs:
            print(f"✅ McDonald's (McHire): {len(jobs)} vagas (HTML)")
            return jobs
        print("[McHire] HTML sem links de vaga; tentando fallback United States…")
        fb = _fallback_united_states()
        print(f"✅ McDonald's (McHire): {len(fb)} vagas (fallback)")
        return fb
    except Exception as e:
        print(f"[McHire] erro ao buscar HTML: {e}")
        return []
