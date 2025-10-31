# scrapers/workday.py
from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


JOB_ID_RE = re.compile(r"/([^/]+)/?$")
FACET_TOKEN = "318c8bb6f553100021d223d9780d30be"


def _build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; JobBot/1.0)"})
    return session


def fetch_workday(base_url: str, employer: Optional[str] = None, max_pages: int = 40):
    """
    Coleta vagas em sites Workday. Paginamos manualmente porque a UI usa requisições
    AJAX com o padrão .../<page>/refreshFacet/<token>.
    """
    session = _build_session()
    all_jobs = []

    for page in range(max_pages):
        if "/refreshFacet/" in base_url:
            url = f"{base_url}/{page}"
        else:
            url = f"{base_url}/{page}/refreshFacet/{FACET_TOKEN}"

        try:
            resp = session.get(url, timeout=25)
            resp.raise_for_status()
        except Exception as exc:
            print(f"[workday] erro ao buscar {url}: {exc}")
            break

        page_jobs = _parse_workday_html(resp.text, base_url, employer)
        print(f"[workday] {base_url} page {page}: {len(page_jobs)} jobs")

        if not page_jobs:
            break

        all_jobs.extend(page_jobs)

    return all_jobs


def _parse_workday_html(html: str, base_url: str, employer: Optional[str]) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    cards = soup.select("[data-automation-id='jobCard']")
    if not cards:
        # fallback: alguns sites usam tabela simples
        cards = soup.select("li[data-automation-id='jobListing']")

    for card in cards:
        anchor = card.select_one("a[data-automation-id='jobTitle']")
        if not anchor:
            continue

        href = anchor.get("href", "")
        title = anchor.get_text(strip=True) or "Workday Job"
        url = href if href.startswith("http") else urljoin(base_url, href)

        loc_el = card.select_one("[data-automation-id='jobLocation']")
        location = loc_el.get_text(" ", strip=True) if loc_el else ""

        desc_el = card.select_one("[data-automation-id='jobPostingText']")
        description = desc_el.get_text("\n", strip=True) if desc_el else ""

        match = JOB_ID_RE.search(href)
        external_id = match.group(1) if match else href

        jobs.append({
            "source": "workday",
            "external_id": external_id,
            "title": title,
            "company": employer or "",
            "description": description,
            "location": location,
            "salary": "",
            "url": url,
        })

    return jobs
