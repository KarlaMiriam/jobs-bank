# scrapers/walmart.py
import requests
from bs4 import BeautifulSoup

def fetch_walmart(url: str):
    resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    title_el = soup.find("h1")
    title = title_el.get_text(strip=True) if title_el else "Walmart Job"

    location = ""
    for el in soup.find_all(["p", "span", "div"]):
        txt = el.get_text(" ", strip=True)
        if "Location" in txt and ":" in txt:
            location = txt.split(":", 1)[-1].strip()
            break

    desc_el = soup.find("div", {"class": "job-description"}) or soup.find("section", {"id": "job-description"})
    description = desc_el.get_text("\n", strip=True) if desc_el else ""

    return [{
        "source": "walmart",
        "external_id": url,
        "title": title,
        "company": "Walmart",
        "description": description,
        "location": location,
        "salary": "",
        "url": url,
    }]
