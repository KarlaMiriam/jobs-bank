# priority.py

# termos que queremos jogar pra cima
EB3_KEYWORDS = [
    "housekeeper",
    "room attendant",
    "housekeeping",
    "laundry",
    "janitor",
    "cleaner",
    "dishwasher",
    "prep cook",
    "line cook",
    "cook",
    "food service",
    "cafeteria",
    "restaurant",
    "crew",
    "fast food",
]

def compute_priority(title: str, company: str, source: str) -> int:
    t = (title or "").lower()
    c = (company or "").lower()
    s = (source or "").lower()

    # 1) McDonald's / mchire sempre no topo
    if "mcdonald" in c or s == "mchire":
        return 5090

    # 2) hotelaria
    if "hotel" in c or "resort" in c or "marriott" in c or "hilton" in c or "ihg" in c:
        return 4000

    # 3) palavras EB-3 clássicas
    if any(k in t for k in EB3_KEYWORDS):
        return 3500

    # 4) food / catering
    if "food" in t or "kitchen" in t:
        return 3000

    return 10
