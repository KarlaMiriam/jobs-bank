# scrapers/icims.py
import requests
from bs4 import BeautifulSoup


def fetch_icims(url: str):
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except Exception as e:
        print(f"[icims] erro ao buscar {url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    title_el = soup.find("h1")
    title = title_el.get_text(strip=True) if title_el else "iCIMS Job"

    # icims costuma ter um span de localização
    loc = ""
    loc_el = soup.find("div", class_="iCIMS_JobHeaderGroup")
    if loc_el:
        # pega tudo que parece localização
        loc = loc_el.get_text(" ", strip=True)

    desc = ""
    desc_el = soup.find("div", class_="iCIMS_JobContent")
    if desc_el:
        desc = desc_el.get_text("\n", strip=True)

    return [
        {
            "source": "icims",
            "external_id": url,
            "title": title,
            "company": "Grimmway",
            "description": desc or "Job description not available.",
            "city": loc,
            "state": "",
            "country": "US",
            "salary": "",
            "url": url,
            "category": "other",
            "priority": 1500,
            "active": True,
        }
    ]
