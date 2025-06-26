import requests
import datetime
import random
import json
from pathlib import Path

# === CONFIG ===
OUTPUT_PATH = Path("paper_to_summarize.json")
NUM_MONTHS = 6

TOPICS = [
    {"name": "Artificial Intelligence", "id": "C154945302"},
    {"name": "Machine Learning", "id": "C119857082"},
    {"name": "Natural Language Processing", "id": "C204321447"},
    {"name": "Data Science", "id": "C2522767166"},
    {"name": "Human–Computer Interaction", "id": "C107457646"},
    {"name": "Computer Vision", "id": "C31972630"},
]

# === HELPERS ===
def get_from_date():
    today = datetime.date.today()
    from_date = today - datetime.timedelta(days=NUM_MONTHS * 30)
    return from_date.isoformat()

def fetch_papers(concept_id):
    url = (
        f"https://api.openalex.org/works?"
        f"filter=open_access.is_oa:true,"
        f"from_publication_date:{get_from_date()},"
        f"concepts.id:{concept_id}"
        f"&sort=publication_date:desc&per_page=15"
    )
    r = requests.get(url)
    r.raise_for_status()
    return r.json().get("results", [])

def filter_valid_papers(papers):
    return [p for p in papers if p.get("abstract")]

# === MAIN LOGIC ===
def main():
    for topic in TOPICS:
        print(f"🔍 Trying topic: {topic['name']}")
        papers = fetch_papers(topic["id"])
        valid = filter_valid_papers(papers)

        if not valid:
            print(f"⚠️ No valid papers with abstracts found for topic '{topic['name']}', trying next.")
            continue

        selected = random.choice(valid)
        selected["topic"] = topic["name"]
        OUTPUT_PATH.write_text(json.dumps(selected, indent=2))
        print(f"✅ Paper saved to {OUTPUT_PATH} for topic '{topic['name']}': {selected['title']}")
        return

    print("❌ No new valid papers found for any topic.")

if __name__ == "__main__":
    main()


