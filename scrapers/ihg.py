# scrapers/ihg.py
import requests
from bs4 import BeautifulSoup

def fetch_ihg(url: str):
    resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    title_el = soup.find("h1")
    title = title_el.get_text(strip=True) if title_el else "IHG Job"

    # tentativa de pegar localização
    location = ""
    for li in soup.find_all("li"):
        txt = li.get_text(" ", strip=True)
        if "Location" in txt:
            location = txt.split(":", 1)[-1].strip()
            break

    desc_el = soup.find("div", class_="description") or soup.find("div", id="description")
    description = desc_el.get_text("\n", strip=True) if desc_el else ""

    return [{
        "source": "ihg",
        "external_id": url,
        "title": title,
        "company": "IHG Hotels & Resorts",
        "description": description,
        "location": location,
        "salary": "",
        "url": url,
    }]
