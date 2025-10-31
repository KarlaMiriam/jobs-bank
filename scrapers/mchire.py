import requests
from bs4 import BeautifulSoup

def fetch_mchire(url: str):
    """
    Antes a gente batia numa API JSON do McHire.
    Agora vamos no HTML mesmo, porque eles podem bloquear JSON.

    Coleta todos os <a> que apontam para /Job?job_id=...
    """
    jobs = []
    try:
        resp = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except Exception as exc:
        print(f"[McHire] erro ao buscar HTML: {exc}")
        return jobs

    soup = BeautifulSoup(resp.text, "html.parser")
    anchors = soup.find_all("a", href=True)

    for a in anchors:
        href = a["href"]
        if "Job?job_id=" not in href:
            continue
        full_url = href if href.startswith("http") else f"https://www.mchire.com{href}"
        title = a.get_text(strip=True) or "McDonald's Job"
        jobs.append({
            "source": "mchire",
            "url": full_url,
            "title": title,
            "company": "McDonald's",
            "description": "",
            "city": "",
            "state": "",
            "country": "US",
            "salary": "",
            "category": "restaurant",
            "priority": 5090,
        })

    print(f"✅ McDonald's (McHire): {len(jobs)} vagas (HTML)")
    return jobs
