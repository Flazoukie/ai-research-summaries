# weekly_ai_summary.py

import requests
import datetime
import random
import os
from transformers import pipeline
from pathlib import Path

# === CONFIG ===
CONCEPT_ROTATION = [
    {"name": "Machine Learning", "id": "C41008148"},
    {"name": "AI & Ethics", "id": "C180786142"},
    {"name": "AI in Education", "id": "C2778407484"},
    {"name": "Natural Language Processing", "id": "C154945302"}
]
NUM_DAYS = 7  # look back over the past week
POSTS_DIR = "posts"

# === STEP 1: Pick this week's topic ===
def get_weekly_concept():
    week_number = datetime.date.today().isocalendar()[1]
    return CONCEPT_ROTATION[week_number % len(CONCEPT_ROTATION)]

# === STEP 2: Query OpenAlex ===
def fetch_recent_open_access_papers(concept_id):
    today = datetime.date.today()
    from_date = today - datetime.timedelta(days=NUM_DAYS)
    url = (
        f"https://api.openalex.org/works"
        f"?filter=concepts.id:{concept_id},open_access.is_oa:true,"
        f"from_publication_date:{from_date}"
        f"&sort=cited_by_count:desc&per-page=5"
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

# === STEP 5: Create .qmd file ===
def create_post(paper, concept, summary, simplified):
    date_str = datetime.date.today().isoformat()
    slug = f"{date_str}-ai-summary"
    title = paper['title']
    url = paper['id'].replace("https://openalex.org/", "https://doi.org/")

    content = f"""
---
title: "AI Paper of the Week: {title}"
date: {date_str}
categories: ["AI", "{concept['name']}"]
---

### 🧠 Topic of the Week: {concept['name']}

**Paper**: [{title}]({url})  
**Published**: {paper.get('publication_date', 'unknown')}

---

### TL;DR (Technical Summary)
{summary}

### 🪄 Explained Simply
{simplified}

### 🔗 [Read the full paper]({url})
"""
    path = Path(POSTS_DIR) / f"{slug}.qmd"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip())
    print(f"✅ Post created: {path}")

# === MAIN ===
def main():
    concept = get_weekly_concept()
    papers = fetch_recent_open_access_papers(concept['id'])
    if not papers:
        print("⚠️ No recent papers found for this topic.")
        return

    paper = random.choice(papers)
    abstract = paper.get('abstract')
    if not abstract:
        print("⚠️ Selected paper has no abstract. Skipping.")
        return

    summary, simplified = summarize_and_simplify(abstract)
    create_post(paper, concept, summary, simplified)

if __name__ == "__main__":
    main()
