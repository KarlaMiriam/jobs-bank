# scrapers/workday.py
import requests
import re

JOB_TITLE_RE = re.compile(
    r'<a[^>]*data-automation-id="jobTitle"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
)

def fetch_workday(base_url: str, max_pages: int = 40):
    all_jobs = []

    for page in range(max_pages):
        if "/refreshFacet/" in base_url:
            url = f"{base_url}/{page}"
        else:
            facet = "318c8bb6f553100021d223d9780d30be"
            url = f"{base_url}/{page}/refreshFacet/{facet}"

        try:
            resp = requests.get(
                url,
                timeout=20,
                headers={"User-Agent": "Mozilla/5.0"}
            )
        except Exception:
            break

        if resp.status_code != 200:
            break

        html = resp.text
        page_jobs = _parse_workday_html(html, base_url)
        print(f"[Workday] {base_url} page {page}: {len(page_jobs)} jobs")

        if not page_jobs:
            break

        all_jobs.extend(page_jobs)

    return all_jobs

def _parse_workday_html(html: str, base_url: str):
    jobs = []
    for m in JOB_TITLE_RE.finditer(html):
        href = m.group(1)
        title = m.group(2).strip()
        full = href if href.startswith("http") else base_url + href

        jobs.append({
            "source": "workday",
            "external_id": "",
            "title": title,
            "company": "",
            "description": "",
            "location": "",
            "salary": "",
            "url": full,
        })
    return jobs
