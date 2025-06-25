# weekly_ai_summary.py

import requests
import datetime
import random
import os
from transformers import pipeline
POSTS_DIR = Path("../data-blog/posts")

# === CONFIG ===
TOPIC = {"name": "Artificial Intelligence", "id": None}  # We'll search by keyword "AI"
NUM_MONTHS = 6  # look back over past 6 months
POSTS_DIR = Path("posts")

# === STEP 1: Calculate from_date 6 months ago ===
def get_from_date():
    today = datetime.date.today()
    # Approximate 6 months as 180 days
    from_date = today - datetime.timedelta(days=180)
    return from_date.isoformat()

# === STEP 2: Query OpenAlex using keyword search ===
def fetch_recent_open_access_papers(topic_keyword):
    from_date = get_from_date()
    url = (
        f"https://api.openalex.org/works"
        f"?filter=open_access.is_oa:true,"
        f"from_publication_date:{from_date}"
        f"&search={topic_keyword}"
        f"&sort=publication_date:desc&per-page=10"
    )
    response = requests.get(url)
    response.raise_for_status()
    return response.json().get("results", [])

# === STEP 3: Load Transformers Pipelines ===
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
simplifier = pipeline("text2text-generation", model="t5-small")

# === STEP 4: Summarize and simplify ===
def summarize_and_simplify(text):
    summary = summarizer(text, max_length=130, min_length=30, do_sample=False)[0]['summary_text']
    prompt = f"Simplify this for someone without AI knowledge: {summary}"
    simplified = simplifier(prompt, max_length=100)[0]['generated_text']
    return summary.strip(), simplified.strip()

# === STEP 5: Check if paper was already published ===
def already_published(doi):
    if not POSTS_DIR.exists():
        return False
    for post_file in POSTS_DIR.glob("*.qmd"):
        content = post_file.read_text()
        if doi in content:
            print(f"⚠️ Paper DOI {doi} already published in {post_file.name}")
            return True
    return False

# === STEP 6: Create .qmd file ===
def create_post(paper, concept_name, summary, simplified):
    date_str = datetime.date.today().isoformat()
    slug = f"{date_str}-ai-summary"
    title = paper['title']
    doi_url = paper.get('doi')
    if doi_url:
        url = "https://doi.org/" + doi_url
    else:
        url = paper['id'].replace("https://openalex.org/", "https://doi.org/")

    content = f"""
---
title: "AI Paper of the Week: {title}"
date: {date_str}
categories: ["AI", "{concept_name}"]
---

### 🧠 Topic of the Week: {concept_name}

**Paper**: [{title}]({url})  
**Published**: {paper.get('publication_date', 'unknown')}

---

### TL;DR (Technical Summary)
{summary}

### 🪄 Explained Simply
{simplified}

### 🔗 [Read the full paper]({url})
"""
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    path = POSTS_DIR / f"{slug}.qmd"
    path.write_text(content.strip())
    print(f"✅ Post created: {path}")

# === MAIN ===
def main():
    topic_keyword = TOPIC["name"]
    papers = fetch_recent_open_access_papers(topic_keyword)
    if not papers:
        print("⚠️ No recent papers found for this topic.")
        return

    # Filter papers that have abstracts and are not already published
    valid_papers = [
        p for p in papers
        if p.get('abstract') and not already_published(p.get('doi') or p['id'])
    ]

    if not valid_papers:
        print("⚠️ No new papers with abstracts found that haven't been published yet.")
        return

    paper = random.choice(valid_papers)
    abstract = paper['abstract']

    summary, simplified = summarize_and_simplify(abstract)
    create_post(paper, topic_keyword, summary, simplified)

if __name__ == "__main__":
    main()
