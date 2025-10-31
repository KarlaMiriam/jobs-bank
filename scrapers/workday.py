# scrapers/workday.py
from __future__ import annotations

from typing import Optional, List, Dict, Tuple
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

FACET_TOKEN = "318c8bb6f553100021d223d9780d30be"
HARD_MAX_PAGES = 80  # limite de segurança


def _session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "POST"]),
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    s.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        }
    )
    return s


def _split_workday_url(base_url: str) -> Tuple[str, str, str]:
    parsed = urlparse(base_url)
    host = f"{parsed.scheme}://{parsed.netloc}"
    parts = [p for p in parsed.path.split("/") if p]
    tenant = parts[0]
    site = parts[1] if len(parts) > 1 else "jobs"
    return host, tenant, site


def fetch_workday(base_url: str, employer: Optional[str] = None, max_pages: Optional[int] = None):
    s = _session()

    # 1) tenta JSON GET
    jobs = _fetch_json_get(s, base_url, employer, max_pages)
    if jobs:
        print(f"✅ {employer or base_url} (Workday JSON-GET): {len(jobs)} vagas (brutas)")
        return jobs

    # 2) tenta JSON POST
    jobs = _fetch_json_post(s, base_url, employer, max_pages)
    if jobs:
        print(f"✅ {employer or base_url} (Workday JSON-POST): {len(jobs)} vagas (brutas)")
        return jobs

    # 3) fallback HTML
    jobs = _fetch_html(s, base_url, employer, max_pages)
    print(f"✅ {employer or base_url} (Workday HTML): {len(jobs)} vagas (brutas)")
    return jobs


def _fetch_json_get(
    s: requests.Session,
    base_url: str,
    employer: Optional[str],
    max_pages: Optional[int],
) -> List[Dict]:
    host, tenant, site = _split_workday_url(base_url)
    limit = 50
    pages = max_pages or HARD_MAX_PAGES
    all_jobs: List[Dict] = []

    for page in range(pages):
        offset = page * limit
        url = f"{host}/wday/cxs/{tenant}/{site}/jobs?offset={offset}&limit={limit}"
        try:
            r = s.get(url, timeout=10)
        except Exception as e:
            print(f"[workday-json] erro GET {url}: {e}")
            return []
        if r.status_code != 200:
            print(f"[workday-json] status {r.status_code} em {url}")
            return []

        data = r.json()
        items = data.get("jobs") or data.get("items") or []
        print(f"[workday-json] {url}: {len(items)} jobs")
        if not items:
            break

        for it in items:
            loc = ""
            if it.get("locations"):
                loc = it["locations"][0].get("descriptor", "")
            job_url = urljoin(base_url + "/", it.get("externalPath") or it.get("id") or "")
            all_jobs.append(
                {
                    "source": "workday",
                    "external_id": str(it.get("id") or ""),
                    "title": it.get("title") or None,
                    "company": employer or tenant.capitalize(),
                    "description": None,
                    "city": loc or None,
                    "state": None,
                    "country": "US",
                    "salary": None,
                    "url": job_url,
                    "category": "other",
                    "priority": 10,
                    "active": True,
                }
            )

    return all_jobs


def _fetch_json_post(
    s: requests.Session,
    base_url: str,
    employer: Optional[str],
    max_pages: Optional[int],
) -> List[Dict]:
    host, tenant, site = _split_workday_url(base_url)
    limit = 50
    pages = max_pages or HARD_MAX_PAGES
    all_jobs: List[Dict] = []

    for page in range(pages):
        offset = page * limit
        url = f"{host}/wday/cxs/{tenant}/{site}/jobs"
        payload = {"limit": limit, "offset": offset, "appliedFacets": {}}
        try:
            r = s.post(url, json=payload, timeout=10)
        except Exception as e:
            print(f"[workday-json-post] erro POST {url}: {e}")
            return []
        if r.status_code != 200:
            print(f"[workday-json-post] status {r.status_code} em {url}")
            return []

        data = r.json()
        items = data.get("jobs") or data.get("items") or []
        print(f"[workday-json-post] {url} offset={offset}: {len(items)} jobs")
        if not items:
            break

        for it in items:
            loc = ""
            if it.get("locations"):
                loc = it["locations"][0].get("descriptor", "")
            job_url = urljoin(base_url + "/", it.get("externalPath") or it.get("id") or "")
            all_jobs.append(
                {
                    "source": "workday",
                    "external_id": str(it.get("id") or ""),
                    "title": it.get("title") or None,
                    "company": employer or tenant.capitalize(),
                    "description": None,
                    "city": loc or None,
                    "state": None,
                    "country": "US",
                    "salary": None,
                    "url": job_url,
                    "category": "other",
                    "priority": 10,
                    "active": True,
                }
            )

    return all_jobs


def _fetch_html(
    s: requests.Session,
    base_url: str,
    employer: Optional[str],
    max_pages: Optional[int],
) -> List[Dict]:
    pages = max_pages or 20
    all_jobs: List[Dict] = []

    for page in range(pages):
        if "/refreshFacet/" in base_url:
            url = f"{base_url}/{page}"
        else:
            url = f"{base_url}/{page}/refreshFacet/{FACET_TOKEN}"
        try:
            r = s.get(url, timeout=10)
            r.raise_for_status()
        except Exception as e:
            print(f"[workday-html] erro ao buscar {url}: {e}")
            break

        jobs = _parse_html(r.text, base_url, employer)
        print(f"[workday-html] {base_url} page {page}: {len(jobs)} jobs")
        if not jobs:
            break
        all_jobs.extend(jobs)

    return all_jobs


def _parse_html(html: str, base_url: str, employer: Optional[str]) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("[data-automation-id='jobCard']") or soup.select("li[data-automation-id='jobListing']")
    jobs: List[Dict] = []

    for c in cards:
        a = c.select_one("a[data-automation-id='jobTitle']")
        if not a:
            continue
        href = a.get("href", "")
        title = a.get_text(strip=True) or None
        job_url = href if href.startswith("http") else urljoin(base_url + "/", href)
        loc_el = c.select_one("[data-automation-id='jobLocation']")
        loc = loc_el.get_text(" ", strip=True) if loc_el else None

        jobs.append(
            {
                "source": "workday",
                "external_id": None,
                "title": title,
                "company": employer or None,
                "description": None,
                "city": loc,
                "state": None,
                "country": "US",
                "salary": None,
                "url": job_url,
                "category": "other",
                "priority": 10,
                "active": True,
            }
        )

    return jobs
