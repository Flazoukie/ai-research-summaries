import requests
import datetime
import random
import json
from pathlib import Path

# === CONFIG ===
TOPICS = [
    {"name": "Artificial Intelligence", "id": "https://openalex.org/C154945302"},
    {"name": "Machine Learning", "id": "https://openalex.org/C119857082"},
    {"name": "Natural Language Processing", "id": "https://openalex.org/C204321447"},
    {"name": "Data Science", "id": "https://openalex.org/C2522767166"},
    {"name": "Human–Computer Interaction", "id": "https://openalex.org/C107457646"},
    {"name": "Computer Vision", "id": "https://openalex.org/C31972630"},
]

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


def main():
    for topic in TOPICS:
        print(f"🔍 Trying topic: {topic['name']}")

        papers = fetch_papers_for_topic(topic["id"])

        # Filter papers that have abstract_inverted_index and are not published
        valid_papers = []
        for p in papers:
            abstract = decode_abstract(p.get("abstract_inverted_index"))
            if abstract is not None and abstract.strip() != "" and not already_published(p.get("doi") or p["id"]):
                p["decoded_abstract"] = abstract
                valid_papers.append(p)

        if not valid_papers:
            print(f"⚠️ No valid papers with abstracts found for topic '{topic['name']}', trying next.")
            continue

        selected = random.choice(valid_papers)
        paper_data = {
            "title": selected["title"],
            "abstract": selected["decoded_abstract"],
            "doi": selected.get("doi"),
            "id": selected["id"],
            "publication_date": selected.get("publication_date"),
            "topic": topic["name"],
            "authorships": selected.get("authorships", [])
        }

        # Save to JSON for next step
        with open("paper_to_summarize.json", "w", encoding="utf-8") as f:
            json.dump(paper_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Paper saved to paper_to_summarize.json for topic '{topic['name']}': {paper_data['title']}")
        return  # stop after first valid paper found

    print("❌ No new valid papers found for any topic.")


if __name__ == "__main__":
    main()



if __name__ == "__main__":
    main()


