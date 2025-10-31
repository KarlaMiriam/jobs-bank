# scrapers/hilton_html.py
import requests
from bs4 import BeautifulSoup

def fetch_hilton_html(url: str):
    resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    title_el = soup.find("h1")
    title = title_el.get_text(strip=True) if title_el else "Hilton Job"

    location = ""
    loc_el = soup.find("span", {"data-ph-at-id": "job-location"}) or soup.find("div", class_="job-location")
    if loc_el:
        location = loc_el.get_text(" ", strip=True)

    desc_el = soup.find("div", class_="ats-description") or soup.find("div", {"data-ph-at-id": "job-description"})
    description = desc_el.get_text("\n", strip=True) if desc_el else ""

    return [{
        "source": "hilton",
        "external_id": url,
        "title": title,
        "company": "Hilton",
        "description": description,
        "location": location,
        "salary": "",
        "url": url,
    }]
