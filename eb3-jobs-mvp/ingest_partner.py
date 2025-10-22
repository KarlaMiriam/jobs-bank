
import json, os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://user:pass@localhost:5432/eb3jobs")
engine = create_engine(DATABASE_URL, future=True)

UPSERT_EMPLOYER = text("""
INSERT INTO employers (name, website)
VALUES (:name, :website)
ON CONFLICT (name) DO UPDATE SET website = EXCLUDED.website
RETURNING id
""")

UPSERT_JOB = text("""
INSERT INTO eb3_jobs (employer_id, title, city, state, wage_hourly, status, duties, apply_url, video_url, posted_date, source_tag)
VALUES (:employer_id, :title, :city, :state, :wage_hourly, :status, :duties, :apply_url, :video_url, :posted_date::date, :source_tag)
ON CONFLICT DO NOTHING
RETURNING id
""")

SELECT_EMPLOYER = text("SELECT id FROM employers WHERE name=:name")

def normalize(item: dict) -> dict:
    return {
        "employer_name": item.get("employer") or "Unknown",
        "title": item["title"],
        "city": item["city"],
        "state": item["state"].upper(),
        "wage_hourly": float(item["wage"]) if item.get("wage") is not None else None,
        "status": item.get("status", "FILING_NOW"),
        "duties": item.get("duties"),
        "apply_url": item.get("apply_url"),
        "video_url": item.get("video_url"),
        "posted_date": item.get("posted_date") or "2025-01-01",
        "source_tag": item.get("source_tag", "partner:feed1"),
    }

def main():
    path = "partner_feed.json"
    data = json.load(open(path))
    with engine.begin() as conn:
        for raw in data:
            r = normalize(raw)
            emp = conn.execute(SELECT_EMPLOYER, {"name": r["employer_name"]}).first()
            if not emp:
                emp_id = conn.execute(UPSERT_EMPLOYER, {"name": r["employer_name"], "website": None}).scalar()
            else:
                emp_id = emp[0]
            r["employer_id"] = emp_id
            conn.execute(UPSERT_JOB, r)
    print("Ingestão concluída.")

if __name__ == "__main__":
    main()
