# scrapers/wendys.py
import time
from typing import Optional
from urllib.parse import urlencode, urljoin, urlparse, urlunparse, parse_qsl

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


BASE_URL = "https://wendys-careers.com"
JOB_PATH_FRAGMENT = "/job-search/posting/"
DEFAULT_PAGES = 5
USER_AGENT = "Mozilla/5.0 (compatible; JobBot/1.0; +https://jobs-bank)"
ACCEPT_HEADER = "text/html,application/xhtml+xml"


def _build_page_url(listing_url: str, page: int) -> str:
    """
    Injects/overrides the `spage` query parameter while keeping any other params intact.
    """
    parsed = urlparse(listing_url)
    query = dict(parse_qsl(parsed.query))
    query["spage"] = str(page)
    new_query = urlencode(query)
    return urlunparse(parsed._replace(query=new_query))


def _normalize_job(session: requests.Session, job_url: str) -> Optional[dict]:
    try:
        resp = session.get(job_url, timeout=25)
        resp.raise_for_status()
    except Exception as exc:
        print(f"[wendys] erro buscando vaga {job_url}: {exc}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    title_el = soup.find("h1") or soup.find("title")
    title = title_el.get_text(strip=True) if title_el else "Wendy's Job"

    loc_el = soup.select_one(".job-location") or soup.select_one(".location")
    location = loc_el.get_text(" ", strip=True) if loc_el else ""

    desc_el = soup.select_one(".job-description") or soup.select_one(".description")
    if desc_el:
        description = desc_el.get_text("\n", strip=True)
    else:
        main_el = soup.find("main")
        # fallback to main text to avoid empty descriptions
        description = (main_el.get_text("\n", strip=True) if main_el else "").strip()

    return {
        "source": "wendys",
        "external_id": job_url,
        "title": title,
        "company": "Wendy's",
        "description": description or "Job description not available.",
        "location": location,
        "salary": "",
        "url": job_url,
    }


def _collect_links_from_listing(session: requests.Session, listing_url: str) -> set[str]:
    try:
        resp = session.get(listing_url, timeout=25)
        resp.raise_for_status()
    except Exception as exc:
        print(f"[wendys] erro listando {listing_url}: {exc}")
        return set()

    soup = BeautifulSoup(resp.text, "html.parser")
    links: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if JOB_PATH_FRAGMENT not in href:
            continue
        # evita links para âncoras internas
        if href.startswith("#"):
            continue
        full_url = urljoin(BASE_URL, href)
        links.add(full_url)
    return links


def fetch_wendys(url: str):
    """
    Scrapes Wendy's listings. When a listing page is provided,
    it paginates through the first DEFAULT_PAGES (or the value passed via ?pages=)
    to collect detail pages. If a direct job posting URL is provided, it returns
    that single job.
    """
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": USER_AGENT, "Accept": ACCEPT_HEADER})

    if JOB_PATH_FRAGMENT in url:
        job = _normalize_job(session, url)
        return [job] if job else []

    parsed = urlparse(url)
    query_pairs = parse_qsl(parsed.query)

    pages_to_scan = DEFAULT_PAGES
    filtered_query = []
    for key, value in query_pairs:
        if key == "pages":
            try:
                pages_to_scan = max(1, int(value))
            except ValueError:
                pages_to_scan = DEFAULT_PAGES
        elif key != "spage":
            filtered_query.append((key, value))

    base_listing_url = urlunparse(parsed._replace(query=urlencode(filtered_query)))
    seen_links: set[str] = set()
    jobs: list[dict] = []

    for page in range(1, pages_to_scan + 1):
        page_url = _build_page_url(base_listing_url or url, page)
        job_links = _collect_links_from_listing(session, page_url)
        if not job_links and page == 1:
            # se a URL já for uma página específica (ex: ...?spage=3), tenta usar diretamente
            job_links = _collect_links_from_listing(session, url)

        for job_url in job_links:
            if job_url in seen_links:
                continue
            seen_links.add(job_url)
            job = _normalize_job(session, job_url)
            if job:
                jobs.append(job)
                time.sleep(0.3)  # short pause to avoid hammering the site

    return jobs
