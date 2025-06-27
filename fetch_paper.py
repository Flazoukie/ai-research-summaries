import requests
import datetime
import random
import json
from pathlib import Path
import re

# === CONFIG ===
TOPIC_ID = "https://openalex.org/C154945302"  # Artificial intelligence
NUM_MONTHS = 6
POSTS_DIR = Path("posts")


def get_from_date():
    today = datetime.date.today()
    from_date = today - datetime.timedelta(days=NUM_MONTHS * 30)
    return from_date.isoformat()


def decode_abstract(index):
    if index is None:
        return None
    words_with_pos = [(pos, word) for word, positions in index.items() for pos in positions]
    words_with_pos.sort(key=lambda x: x[0])
    abstract = " ".join(word for pos, word in words_with_pos)
    return abstract


def already_published(doi):
    if not POSTS_DIR.exists():
        return False
    for post_file in POSTS_DIR.glob("*.qmd"):
        content = post_file.read_text()
        if doi in content:
            print(f"⚠️ Paper DOI {doi} already published in {post_file.name}")
            return True
    return False


def fetch_papers_for_topic(topic_id):
    from_date = get_from_date()
    url = (
        f"https://api.openalex.org/works"
        f"?filter=concepts.id:{topic_id},open_access.is_oa:true,from_publication_date:{from_date}"
        f"&sort=publication_date:desc&per-page=20"
    )
    response = requests.get(url)
    response.raise_for_status()
    return response.json().get("results", [])


def matches_ai_keywords(title, abstract):
    title_lower = title.lower()
    abstract_lower = abstract.lower()
    return (
        "artificial intelligence" in title_lower
        or "artificial intelligence" in abstract_lower
        or re.search(r"\bAI\b", title)
        or re.search(r"\bAI\b", abstract)
    )


def main():
    print(f"🔍 Fetching papers for topic: Artificial Intelligence")

    papers = fetch_papers_for_topic(TOPIC_ID)

    valid_papers = []
    for p in papers:
        abstract = decode_abstract(p.get("abstract_inverted_index"))
        if not abstract or abstract.strip() == "":
            continue

        if not matches_ai_keywords(p["title"], abstract):
            continue

        if already_published(p.get("doi") or p["id"]):
            continue

        p["decoded_abstract"] = abstract
        valid_papers.append(p)

    if not valid_papers:
        print("❌ No matching papers found.")
        return

    selected = random.choice(valid_papers)

    paper_data = {
        "title": selected["title"],
        "abstract": selected["decoded_abstract"],
        "doi": selected.get("doi"),
        "id": selected["id"],
        "publication_date": selected.get("publication_date"),
        "topic": "Artificial Intelligence",
        "authorships": selected.get("authorships", [])
    }

    with open("paper_to_summarize.json", "w", encoding="utf-8") as f:
        json.dump(paper_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Paper saved to paper_to_summarize.json: {paper_data['title']}")


if __name__ == "__main__":
    main()
