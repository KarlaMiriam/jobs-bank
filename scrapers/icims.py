# scrapers/icims.py

import requests
from bs4 import BeautifulSoup

def fetch_icims(url: str):
    """
    Raspador simples para páginas iCIMS, como:
    https://careers-grimmway.icims.com/jobs/20801/maintenance-mechanic/job
    """
    resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # título
    title_el = soup.find("h1", {"class": "iCIMS_Header"}) or soup.find("h1")
    title = title_el.get_text(strip=True) if title_el else "iCIMS Job"

    # localização
    location = ""
    loc_el = soup.find("span", {"class": "jobLocation"})
    if loc_el:
        location = loc_el.get_text(" ", strip=True)

    # descrição
    desc_el = soup.find("div", {"class": "iCIMS_JobContent"})
    description = desc_el.get_text("\n", strip=True) if desc_el else ""

    company = "Grimmway" if "grimmway" in url else "iCIMS company"

    return [{
        "source": "icims",
        "external_id": url,
        "title": title,
        "company": company,
        "description": description,
        "location": location,
        "salary": "",
        "url": url,
    }]
