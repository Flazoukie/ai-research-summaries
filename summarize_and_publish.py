import json
import datetime
from pathlib import Path
from transformers import pipeline

# === CONFIG ===
INPUT_PATH = Path("paper_to_summarize.json")
POSTS_DIR = Path("data-blog/posts")
POSTS_DIR.mkdir(parents=True, exist_ok=True)

# === Load paper ===
with open(INPUT_PATH) as f:
    paper = json.load(f)

title = paper["title"]
abstract = paper["abstract"]
topic = paper["topic"]
date_str = datetime.date.today().isoformat()

# === Load Hugging Face models ===
print("🔧 Loading models...")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
simplifier = pipeline("text2text-generation", model="t5-small")

# === Generate summary and simplified version ===
print("🧠 Summarizing abstract...")
summary = summarizer(abstract, max_length=130, min_length=30, do_sample=False)[0]['summary_text']

print("🪄 Simplifying summary...")
prompt = f"Simplify this for someone without AI knowledge: {summary}"
simplified = simplifier(prompt, max_length=100)[0]['generated_text']

# === Determine paper URL ===
doi = paper.get("doi")
url = f"https://doi.org/{doi}" if doi else paper["id"].replace("https://openalex.org/", "https://doi.org/")

# === Generate post content ===
slug = f"{date_str}-ai-summary"
post_path = POSTS_DIR / f"{slug}.qmd"

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
{summary.strip()}

### 🪄 Explained Simply
{simplified.strip()}

### 🔗 [Read the full paper]({url})

### 🧪 Model Notes
Summarized with `facebook/bart-large-cnn` and simplified using `t5-small`.
"""


# === Save post ===
post_path.write_text(content.strip())
print(f"✅ Blog post created at {post_path}")

