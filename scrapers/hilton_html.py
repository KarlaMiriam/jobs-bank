# scrapers/hilton_html.py
import requests
from bs4 import BeautifulSoup


def fetch_hilton_html(url: str):
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except Exception as e:
        print(f"[hilton] erro ao buscar {url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    title_el = soup.find("h1") or soup.find("h2")
    title = title_el.get_text(strip=True) if title_el else "Hilton Job"

    location = ""
    loc_el = soup.find("span", class_="job-location")
    if loc_el:
        location = loc_el.get_text(" ", strip=True)

    desc = ""
    desc_el = soup.find("div", class_="job-description")
    if desc_el:
        desc = desc_el.get_text("\n", strip=True)

    return [
        {
            "source": "hilton",
            "external_id": url,
            "title": title,
            "company": "Hilton",
            "description": desc or "Job description not available.",
            "city": location,
            "state": "",
            "country": "US",
            "salary": "",
            "url": url,
            "category": "hotel",
            "priority": 4000,
            "active": True,
        }
    ]
