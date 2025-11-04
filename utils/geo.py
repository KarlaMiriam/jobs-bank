from __future__ import annotations
import re
from typing import Tuple, Optional

US_STATE_ABBR = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA","ME","MD","MA","MI",
    "MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT",
    "VT","VA","WA","WV","WI","WY","DC"
}

US_STATE_NAMES = {
    "alabama","alaska","arizona","arkansas","california","colorado","connecticut","delaware","florida","georgia",
    "hawaii","idaho","illinois","indiana","iowa","kansas","kentucky","louisiana","maine","maryland","massachusetts",
    "michigan","minnesota","mississippi","missouri","montana","nebraska","nevada","new hampshire","new jersey",
    "new mexico","new york","north carolina","north dakota","ohio","oklahoma","oregon","pennsylvania","rhode island",
    "south carolina","south dakota","tennessee","texas","utah","vermont","virginia","washington","west virginia",
    "wisconsin","wyoming","district of columbia","washington dc","washington, dc"
}

COUNTRY_TOKENS_US = {"us","usa","u.s.","u.s.a","united states","united states of america","u s","u s a"}

SEP_RE = re.compile(r"\s*[;,/]\s+")

def looks_like_us_piece(piece: str) -> bool:
    s = (piece or "").strip()
    if not s:
        return False
    low = s.lower()

    # menção explícita ao país
    for tok in COUNTRY_TOKENS_US:
        if tok in low:
            return True

    # "Remote (US)"
    if "remote" in low and (" us" in low or "usa" in low or "united states" in low or " u.s" in low):
        return True

    # nome de estado
    for name in US_STATE_NAMES:
        if name in low:
            return True

    # vírgula e abreviação de estado no final
    tokens = [t.strip() for t in s.split(",")]
    if tokens:
        last = tokens[-1].upper()
        m = re.search(r"\b([A-Z]{2})\b", last)
        if m and m.group(1) in US_STATE_ABBR:
            return True

    # "City ST" ou "City - ST"
    m2 = re.search(r"\b([A-Za-z .'-]+)[,\s-]+([A-Z]{2})\b", s)
    if m2 and m2.group(2).upper() in US_STATE_ABBR:
        return True

    return False

def pick_us_piece(location: str) -> str:
    loc = (location or "").strip()
    if not loc:
        return ""
    parts = SEP_RE.split(loc)
    for p in parts:
        if looks_like_us_piece(p):
            return p.strip()
    return ""

def state_name_to_abbr(name: str) -> str:
    mapping = {
        "alabama":"AL","alaska":"AK","arizona":"AZ","arkansas":"AR","california":"CA","colorado":"CO","connecticut":"CT",
        "delaware":"DE","florida":"FL","georgia":"GA","hawaii":"HI","idaho":"ID","illinois":"IL","indiana":"IN","iowa":"IA",
        "kansas":"KS","kentucky":"KY","louisiana":"LA","maine":"ME","maryland":"MD","massachusetts":"MA","michigan":"MI",
        "minnesota":"MN","mississippi":"MS","missouri":"MO","montana":"MT","nebraska":"NE","nevada":"NV","new hampshire":"NH",
        "new jersey":"NJ","new mexico":"NM","new york":"NY","north carolina":"NC","north dakota":"ND","ohio":"OH",
        "oklahoma":"OK","oregon":"OR","pennsylvania":"PA","rhode island":"RI","south carolina":"SC","south dakota":"SD",
        "tennessee":"TN","texas":"TX","utah":"UT","vermont":"VT","virginia":"VA","washington":"WA","west virginia":"WV",
        "wisconsin":"WI","wyoming":"WY","district of columbia":"DC","washington dc":"DC","washington, dc":"DC"
    }
    return mapping.get(name.lower(), "")

def extract_city_state_country(piece: str) -> Tuple[str, str, str]:
    s = (piece or "").strip()
    if not s:
        return "", "", ""

    parts = [p.strip() for p in s.split(",")]
    city, state, country = "", "", ""

    if parts:
        last = parts[-1]
        if any(tok in last.lower() for tok in COUNTRY_TOKENS_US):
            country = "US"
            parts = parts[:-1]

    if parts:
        tail = parts[-1]
        m = re.search(r"\b([A-Z]{2})\b", tail.upper())
        if m and m.group(1) in US_STATE_ABBR:
            state = m.group(1)
            parts = parts[:-1]
        else:
            low_tail = tail.lower()
            for name in US_STATE_NAMES:
                if name == low_tail:
                    state = state_name_to_abbr(name)
                    parts = parts[:-1]
                    break

    if parts:
        city = ", ".join(parts)

    return city, state, country

def looks_like_us_city_state(city: str, state: str, country: str, fallback_text: Optional[str] = "") -> bool:
    if (country or "").lower().replace(".", "") in COUNTRY_TOKENS_US:
        return True
    if (state or "").upper() in US_STATE_ABBR:
        return True
    if fallback_text and looks_like_us_piece(fallback_text):
        return True
    return False

# alias só para compatibilidade antiga
looks_like_us_location = looks_like_us_piece
