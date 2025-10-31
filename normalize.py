# normalize.py

US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
    "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY",
    "DC"
}

def is_us_location(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    if "united states" in t or "united states of america" in t or "usa" in t or "us" == t.strip():
        return True
    # tenta ver se tem , FL / , CA ...
    parts = [p.strip() for p in text.split(",")]
    if len(parts) >= 2:
        state = parts[-1].upper()
        if state in US_STATES:
            return True
    return False


def split_city_state(text: str):
    if not text:
        return ("", "")
    parts = [p.strip() for p in text.split(",")]
    if len(parts) >= 2:
        city = ", ".join(parts[:-1])
        state = parts[-1].upper()
        return (city, state)
    return (text, "")
