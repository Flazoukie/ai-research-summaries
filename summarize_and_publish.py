import json
import datetime
from pathlib import Path
from transformers import pipeline
import html
import re

# === CONFIG ===
INPUT_PATH = Path("paper_to_summarize.json")
POSTS_DIR = Path("data-blog/posts")
POSTS_DIR.mkdir(parents=True, exist_ok=True)

# === Load paper ===
with open(INPUT_PATH) as f:
    paper = json.load(f)

title = paper["title"]
authors = ", ".join(
    a["author"].get("display_name", "Unknown")
    for a in paper.get("authorships", [])
    if a.get("author") and a["author"].get("display_name")
)
abstract = paper["abstract"]
topic = paper["topic"]
journal_date = paper.get("publication_date", "unknown")
post_date = datetime.date.today().isoformat()

print("🔧 Loading simplification model...")
simplifier = pipeline("text2text-generation", model="google/flan-t5-large")

# === Generate simplified version ===
print("🪄 Simplifying abstract...")
prompt = (
    f"Rewrite the following academic abstract into a clear and engaging summary for a curious reader with no technical background. "
    f"Start by explaining the real-world problem and why it matters. Then describe the approach, key findings, and what makes it important. "
    f"Avoid technical jargon and break down complex terms into plain language. "
    f"Use third person (no 'we' or 'I') and write 5–8 full sentences that flow naturally. "
    f"Round numbers and include relatable context when possible.\n\n"
    f"Example:\n"
    f"Original abstract: 'Deep-learning models for prostate cancer detection typically require large datasets, limiting clinical applicability across institutions. This study aimed to develop a few-shot learning model that uses minimal data. It was tested on real-world scans and compared to radiologists.'\n\n"
    f"Simplified summary: 'Prostate cancer is often diagnosed using MRI scans, but training AI models to interpret these scans usually requires lots of data. This study developed a model that can learn from just a few examples, using a technique called few-shot learning. It performed almost as well as experienced radiologists, even when tested on new data. This approach could help smaller hospitals use AI for diagnosis without needing huge datasets.'\n\n"
    f"Now summarize this abstract:\n\n{abstract}"
)

simplified = simplifier(prompt, max_length=1000, do_sample=False)[0]['generated_text']

# === Determine paper URL ===
doi = paper.get("doi")
url = f"https://doi.org/{doi}" if doi else paper["id"].replace("https://openalex.org/", "https://doi.org/")

# === Generate post content ===
slug = f"{post_date}-ai-summary"
post_path = POSTS_DIR / f"{slug}.qmd"

# Clean up abstract HTML entities (e.g. &lt;, &gt;, &amp;)
abstract_clean = html.unescape(abstract.strip())

# Escape double asterisks to prevent bold formatting in Markdown
abstract_clean = re.sub(r'\*\*', r'\\*\\*', abstract_clean)

content = f"""
---
title: "Paper of the Week: "{title}""
date: {post_date}
categories: ["{topic}"]
---

### 🧠 Topic: {topic}

Authors: {authors if authors else 'Unknown'}  
Published in journal: {journal_date}  

---

### 🪄 Explained Simply
{simplified.strip()}

---

### 📄 Full Abstract
{abstract_clean}

---

### 🔗 [Read the full paper]({url})

### 🧪 Model Notes
Simplified using `google/flan-t5-large`.
"""

# === Save post ===
post_path.write_text(content.strip())
print(f"✅ Blog post created at {post_path}")
