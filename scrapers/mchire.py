# scrapers/mchire.py
import requests
import re

LINK_RE = re.compile(
    r'<a[^>]*href="(https?:\/\/www\.mchire\.com[^"]+|www\.mchire\.com[^"]+)"[^>]*>([^<]+)</a>'
)

def fetch_mchire(base_url: str, max_pages: int = 20):
    all_jobs = []

    for page in range(1, max_pages + 1):
        url = base_url if page == 1 else f"{base_url}/page/{page}"

        try:
            resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        except Exception:
            break

        if resp.status_code != 200:
            break

        html = resp.text
        page_jobs = _parse_mchire(html)
        print(f"[McHire] page {page}: {len(page_jobs)} jobs")

        if not page_jobs:
            break

        all_jobs.extend(page_jobs)

    return all_jobs

def _parse_mchire(html: str):
    jobs = []
    for m in LINK_RE.finditer(html):
        href = m.group(1)
        title = m.group(2).strip()

        if href.startswith("www."):
            href = "https://" + href

        href = href.replace("&#x27;", "'").replace("&amp;", "&")

        jobs.append({
            "source": "mchire",
            "external_id": "",
            "title": title,
            "company": "McDonald's",
            "description": "",
            "location": "",
            "salary": "",
            "url": href,
        })
    return jobs
