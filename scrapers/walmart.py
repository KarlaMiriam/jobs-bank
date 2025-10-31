# scrapers/walmart.py
import requests
from bs4 import BeautifulSoup


def fetch_walmart(url: str):
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except Exception as e:
        print(f"[walmart] erro ao buscar {url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    title_el = soup.find("h1")
    title = title_el.get_text(strip=True) if title_el else "Walmart Job"

    location = ""
    loc_el = soup.find("span", {"data-ph-at-id": "job-location"})
    if loc_el:
        location = loc_el.get_text(" ", strip=True)

    return [
        {
            "source": "walmart",
            "external_id": url,
            "title": title,
            "company": "Walmart",
            "description": "Job description not available.",
            "city": location,
            "state": "",
            "country": "US",
            "salary": "",
            "url": url,
            "category": "retail",
            "priority": 2000,
            "active": True,
        }
    ]
