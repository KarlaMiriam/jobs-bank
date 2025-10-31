# scrapers/ihg.py
import requests
from bs4 import BeautifulSoup


def fetch_ihg(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://careers.ihg.com/",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        resp = requests.get(url, timeout=20, headers=headers)
        resp.raise_for_status()
    except Exception as e:
        print(f"[ihg] erro ao buscar {url}: {e}")
        # mesmo assim, devolve uma vaga genérica, pra não perder a fonte
        return [
            {
                "source": "ihg",
                "external_id": url,
                "title": "IHG Job",
                "company": "IHG",
                "description": "Job description not available.",
                "city": "",
                "state": "",
                "country": "US",
                "salary": "",
                "url": url,
                "category": "hotel",
                "priority": 4000,
                "active": True,
            }
        ]

    soup = BeautifulSoup(resp.text, "html.parser")
    title = soup.find("h1")
    job_title = title.get_text(strip=True) if title else "IHG Job"

    location = ""
    loc_el = soup.find("div", class_="job-location")
    if loc_el:
        location = loc_el.get_text(" ", strip=True)

    desc = ""
    desc_el = soup.find("div", class_="job-description")
    if desc_el:
        desc = desc_el.get_text("\n", strip=True)

    return [
        {
            "source": "ihg",
            "external_id": url,
            "title": job_title,
            "company": "IHG",
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
