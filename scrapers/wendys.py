# scrapers/wendys.py
import requests
from bs4 import BeautifulSoup

def fetch_wendys(url: str):
    resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    title_el = soup.find(["h1", "h2"])
    title = title_el.get_text(strip=True) if title_el else "Wendy's Job"

    location = ""
    loc_el = soup.find("div", class_="job-location") or soup.find("p", class_="location")
    if loc_el:
        location = loc_el.get_text(" ", strip=True)

    desc_el = soup.find("div", class_="job-description") or soup.find("div", id="job-description")
    description = desc_el.get_text("\n", strip=True) if desc_el else ""

    return [{
        "source": "wendys",
        "external_id": url,
        "title": title,
        "company": "Wendy's",
        "description": description,
        "location": location,
        "salary": "",
        "url": url,
    }]
