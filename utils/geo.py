# utils/geo.py
from __future__ import annotations
import re

# Conjunto com siglas dos 50 estados + DC/territórios mais comuns
US_STATE_ABBR = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
    "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC","PR","GU"
}

# Nomes de estados (básico e suficiente pro nosso caso)
US_STATE_NAMES = {
    "alabama","alaska","arizona","arkansas","california","colorado","connecticut","delaware","florida","georgia",
    "hawaii","idaho","illinois","indiana","iowa","kansas","kentucky","louisiana","maine","maryland",
    "massachusetts","michigan","minnesota","mississippi","missouri","montana","nebraska","nevada","new hampshire","new jersey",
    "new mexico","new york","north carolina","north dakota","ohio","oklahoma","oregon","pennsylvania","rhode island","south carolina",
    "south dakota","tennessee","texas","utah","vermont","virginia","washington","west virginia","wisconsin","wyoming","district of columbia",
    "puerto rico","guam"
}

NON_US_HINTS = {
    "germany","deutschland","canada","united kingdom","uk","england","scotland","wales","ireland",
    "france","mexico","brazil","australia","spain","italy","netherlands","sweden","switzerland",
    "austria","portugal","belgium","poland","czech","denmark","norway","finland","japan","china","india"
}

ZIP_RE = re.compile(r"\b\d{5}(?:-\d{4})?\b")  # zip dos EUA

def looks_like_us_location(text: str) -> bool:
    """Heurística: retorna True se a string de local parecer EUA."""
    if not text:
        return False
    low = text.lower()

    # se mencionar explicitamente EUA
    if "united states" in low or "usa" in low or low.endswith(", us") or ", us," in low:
        return True

    # se mencionar países não-eua, corta
    if any(h in low for h in NON_US_HINTS):
        return False

    # se tiver CEP americano
    if ZIP_RE.search(text):
        return True

    # se tiver "City, ST"
    parts = [p.strip() for p in re.split(r"[;|/]", text)]
    for p in parts:
        # tenta "City, ST"
        if "," in p:
            tail = p.split(",")[-1].strip()
            # tail pode ser "CA" ou "California"
            if tail.upper() in US_STATE_ABBR:
                return True
            if tail.lower() in US_STATE_NAMES:
                return True
        else:
            # linha única tipo "California"
            if p.lower() in US_STATE_NAMES or p.upper() in US_STATE_ABBR:
                return True

    return False

def pick_us_piece(location: str) -> str:
    """Se vier 'City, ST; City2, Germany', devolve só o trecho que é EUA."""
    if not location:
        return ""
    candidates = [c.strip() for c in re.split(r"[;|/]", location) if c.strip()]
    for c in candidates:
        if looks_like_us_location(c):
            return c
    # nenhum trecho “bem EUA”; retorna string vazia para forçar filtro a decidir
    return ""
