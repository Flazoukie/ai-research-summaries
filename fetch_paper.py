# fetch_paper.py

import datetime
import hashlib
import json
import os
import random
from pathlib import Path

import requests

TOPICS = [
    "Artificial Intelligence",
    "Machine Learning",
    "NLP",
    "Education",
    "Ethics"
]

POSTS_DIR = Path("posts")
OUTPUT_FILE = Path("paper_to_summarize.json")

# === Rotate based on week number ===
def get_weekly_topic():
    week = datetime.date.today().isocalendar().week
    return TOPICS[week % len(TOPICS)]

# === Check if paper already published ===
def already_published(doi_or_id):
    if not POSTS_DIR.exists():
        return False
    for post in POSTS_DIR.glob("*.qmd"):
        if doi_or_id in post.read_text():
            return True
    return False

def get_from_date():
    return (datetime.date.today() - datetime.timedelta(days=180)).isoformat()

def fetch_papers_for_topic(keyword):
    url = (
        f"https://api.openalex.org/works"
        f"?filter=open_access.is_oa:true,from_publication_date:{get_from_date()}"
        f"&search={keyword}&sort=publication_date:desc&per-page=10"
    )
    r = requests.get(url)
    r.raise_for_status()
    return r.json().get("results", [])

def get_valid_paper(topic):
    papers = fetch_papers_for_topic(topic)
    for p in papers:
        doi_or_id = p.get('doi') or p.get('id')
        if p.get('abstract') and not already_published(doi_or_id):
            return p
    return None

def main():
    starting_index = datetime.date.today().isocalendar().week % len(TOPICS)
    for offset in range(len(TOPICS)):
        topic = TOPICS[(starting_index + offset) % len(TOPICS)]
        print(f"🔍 Trying topic: {topic}")
        paper = get_valid_paper(topic)
        if paper:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump({"topic": topic, "paper": paper}, f, indent=2)
            print(f"✅ Found paper for topic '{topic}': {paper['title']}")
            return
        else:
            print(f"⚠️ No valid paper found for topic '{topic}', trying next.")
    print("❌ No new valid papers found for any topic.")

if __name__ == "__main__":
    main()

