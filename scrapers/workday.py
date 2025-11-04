# scrapers/workday.py
import time
import random
import requests
from typing import List, Dict, Optional

UA_LIST = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
]

def _headers_json(ref: str):
    return {
        "User-Agent": random.choice(UA_LIST),
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Referer": ref,
        "Origin": ref.split("/")[0] + "//" + ref.split("/")[2] if "://" in ref else ref,
        "Connection": "keep-alive",
    }

def fetch_workday(tenant_host: str, tenant: str, site: str, limit: int = 50, pages: int = 40) -> List[Dict]:
    """
    Ex.: tenant_host='marriott.wd5.myworkdayjobs.com', tenant='marriott', site='MarriottCareers'
    Tenta:
      1) GET /wday/cxs/{tenant}/{site}/jobs?limit=&offset=
      2) POST /wday/cxs/{tenant}/{site}/jobs  {limit, offset, searchText:""}
    Cai para fallback HTML básico se necessário.
    """
    base = f"https://{tenant_host}"
    api_get = f"{base}/wday/cxs/{tenant}/{site}/jobs"
    api_post = api_get  # mesmo path, método POST
    ref = f"{base}/{site}"

    out: List[Dict] = []

    # 1) GET
    for page in range(pages):
        offset = page * limit
        try:
            r = requests.get(f"{api_get}?limit={limit}&offset={offset}",
                             headers=_headers_json(ref), timeout=25)
            if r.status_code == 200 and "application/json" in r.headers.get("content-type", ""):
                data = r.json()
                items = data.get("jobPostings") or data.get("items") or []
                if not items:
                    break
                for it in items:
                    title = it.get("title") or it.get("displayTitle") or it.get("jobPostingTitle")
                    loc = it.get("locationsText") or it.get("location") or ""
                    url = it.get("externalPath") or it.get("jobPostingUrl") or ""
                    if url and url.startswith("/"):
                        url = base + url
                    out.append({
                        "title": title,
                        "company": tenant.capitalize(),
                        "description": "",
                        "city": "", "state": "", "country": "",
                        "salary": "",
                        "url": url,
                        "category": it.get("primaryCategory") or it.get("jobFamily") or "other",
                        "priority": 1000,
                        "active": True,
                        "source": "workday",
                        "raw_location": loc,
                    })
            else:
                break
        except Exception:
            break

    if out:
        return out

    # 2) POST
    for page in range(pages):
        offset = page * limit
        try:
            payload = {"limit": limit, "offset": offset, "searchText": ""}
            r = requests.post(api_post, json=payload, headers=_headers_json(ref), timeout=25)
            if r.status_code == 200 and "application/json" in r.headers.get("content-type", ""):
                data = r.json()
                items = data.get("jobPostings") or data.get("items") or []
                if not items:
                    break
                for it in items:
                    title = it.get("title") or it.get("displayTitle") or it.get("jobPostingTitle")
                    loc = it.get("locationsText") or it.get("location") or ""
                    url = it.get("externalPath") or it.get("jobPostingUrl") or ""
                    if url and url.startswith("/"):
                        url = base + url
                    out.append({
                        "title": title,
                        "company": tenant.capitalize(),
                        "description": "",
                        "city": "", "state": "", "country": "",
                        "salary": "",
                        "url": url,
                        "category": it.get("primaryCategory") or it.get("jobFamily") or "other",
                        "priority": 1000,
                        "active": True,
                        "source": "workday",
                        "raw_location": loc,
                    })
            else:
                break
        except Exception:
            break

    if out:
        return out

    # 3) Fallback HTML: pega cards básicos (mínimo: URL)
    try:
        r = requests.get(ref, headers=_headers_json(ref), timeout=25)
        r.raise_for_status()
        html = r.text
        import re
        # matches de hrefs que apontam para /{site}/job/...
        links = re.findall(r'href="(/[^"]+job[^"]+)"', html, flags=re.I)
        seen = set()
        for u in links:
            if u in seen:
                continue
            seen.add(u)
            full = base + u
            out.append({
                "title": None,
                "company": tenant.capitalize(),
                "description": "",
                "city": "", "state": "", "country": "",
                "salary": "",
                "url": full,
                "category": "other",
                "priority": 800,
                "active": True,
                "source": "workday",
                "raw_location": "",
            })
    except Exception:
        pass

    return out
