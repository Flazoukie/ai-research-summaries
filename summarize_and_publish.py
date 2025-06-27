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
    "You are an expert science communicator. Your task is to rewrite the following academic abstract into a short, clear, and engaging explanation for a curious reader with no technical background.\n\n"
    "Follow these guidelines:\n"
    "- Start by explaining the real-world problem the research addresses.\n"
    "- Then describe what the researchers did to tackle it.\n"
    "- Clearly state what they found and why it matters.\n"
    "- Avoid technical terms and explain complex ideas in everyday language.\n"
    "- Use 5 to 8 natural, flowing sentences. Imagine you're talking to an interested teenager.\n"
    "- Use third person only (never 'we' or 'I').\n"
    "- Round numbers and give context when useful.\n"
    "- Make it sound human, helpful, and easy to read.\n\n"
    "Example:\n"
    "Original abstract: 'Deep-learning models for prostate cancer detection typically require large datasets, limiting clinical applicability across institutions. This study aimed to develop a few-shot learning model that uses minimal data. It was tested on real-world scans and compared to radiologists.'\n\n"
    "Summary: 'Prostate cancer is often diagnosed using MRI scans, but training AI tools to read them usually takes lots of data. This study developed a model that learns from just a few examples. It was tested on real cases and performed almost as well as experienced doctors. This approach could help smaller hospitals use AI even if they don’t have huge datasets.'\n\n"
    "Now rewrite this abstract in the same style:\n\n"
    f"{abstract}"
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
title: "Paper of the Week"
date: {post_date}
categories: ["{topic}"]
---

### Title: {title}

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
