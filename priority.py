# priority.py

HOTEL_KEYWORDS = [
    "housekeeper", "house keeping", "housekeeping",
    "room attendant", "guest room attendant",
    "laundry attendant", "laundry",
    "linen", "hotel", "resort",
    "hospitality", "housekeeping aide",
    "housekeeping attendant", "public area attendant",
    "cleaning rooms",
]

RESTAURANT_KEYWORDS = [
    "dishwasher", "dish washer", "steward",
    "prep cook", "line cook", "cook",
    "food prep", "cafeteria", "restaurant",
    "server", "fast food", "crew member"
]

CLEANING_KEYWORDS = [
    "janitor", "janitorial", "cleaner", "commercial cleaner",
    "housecleaner", "house cleaner", "cleaning", "custodian"
]

CAREGIVER_KEYWORDS = [
    "caregiver", "nursing aide", "home health aide", "personal care aide"
]

WAREHOUSE_KEYWORDS = [
    "warehouse", "production", "assembly", "packing", "picker", "associate",
    "manufacturing", "factory"
]

FOOD_PROCESSING_KEYWORDS = [
    "poultry", "meat processing", "food processing", "food production"
]

AGRICULTURE_KEYWORDS = [
    "farmworker", "farm worker", "farm laborer",
    "agriculture", "harvest", "packing house", "greenhouse worker"
]

LANDSCAPING_KEYWORDS = [
    "landscaping", "groundskeeper", "groundskeeping", "lawn care"
]

CONSTRUCTION_KEYWORDS = [
    "laborer", "construction helper", "general labor", "construction laborer"
]


def score_job(title: str, description: str) -> tuple[int, str]:
    text = f"{title} {description}".lower()

    if any(k in text for k in HOTEL_KEYWORDS):
        return 100, "hotel"

    if any(k in text for k in RESTAURANT_KEYWORDS):
        return 90, "restaurant"

    if any(k in text for k in CLEANING_KEYWORDS):
        return 80, "cleaning"

    if any(k in text for k in CAREGIVER_KEYWORDS):
        return 75, "caregiver"

    if any(k in text for k in WAREHOUSE_KEYWORDS):
        return 70, "warehouse"

    if any(k in text for k in FOOD_PROCESSING_KEYWORDS):
        return 65, "food_processing"

    if any(k in text for k in AGRICULTURE_KEYWORDS):
        return 62, "agriculture"

    if any(k in text for k in LANDSCAPING_KEYWORDS):
        return 60, "landscaping"

    if any(k in text for k in CONSTRUCTION_KEYWORDS):
        return 55, "construction"

    return 10, "other"
