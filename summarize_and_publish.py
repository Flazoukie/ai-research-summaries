# summarize_and_publish.py

import datetime
import json
from pathlib import Path

from transformers import pipeline

POSTS_DIR = Path("posts")
INPUT_FILE = Path("paper_to_summarize.json")

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
simplifier = pipeline("text2text-generation", model="t5-small")

def summarize_and_simplify(text):
    summary = summarizer(text, max_length=130, min_length=30, do_sample=False)[0]['summary_text']
    prompt = f"Simplify this for someone without AI knowledge: {summary}"
    simplified = simplifier(prompt, max_length=100)[0]['generated_text']
    return summary.strip(), simplified.strip()

def create_post(topic, paper, summary, simplified):
    date_str = datetime.date.today().isoformat()
    slug = f"{date_str}-ai-summary"
    title = paper['title']
    doi = paper.get("doi")
    url = "https://doi.org/" + doi if doi else paper['id'].replace("https://openalex.org/", "https://doi.org/")

    content = f"""
---
title: "AI Paper of the Week: {title}"
date: {date_str}
categories: ["AI", "{topic}"]
---

### 🧠 Topic of the Week: {topic}

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

def main():
    if not INPUT_FILE.exists():
        print("⚠️ No paper_to_summarize.json file found. Run fetch_paper.py first.")
        return

    with open(INPUT_FILE, encoding="utf-8") as f:
        data = json.load(f)

    topic = data["topic"]
    paper = data["paper"]
    abstract = paper.get("abstract")

    if not abstract:
        print("❌ Paper has no abstract. Skipping.")
        return

    summary, simplified = summarize_and_simplify(abstract)
    create_post(topic, paper, summary, simplified)

if __name__ == "__main__":
    main()
