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
    "You are an expert science communicator. Your task is to rewrite the following academic abstract "
    "as a short, clear, and engaging explanation for curious readers with no technical background.\n\n"
    "Write in a natural, human tone as if speaking to a smart teenager. Focus on clarity and flow.\n\n"
    "Your explanation should:\n"
    "- Start by describing the real-world problem being addressed.\n"
    "- Explain what the researchers did to tackle it.\n"
    "- Summarize what they discovered and why it matters.\n"
    "- Avoid jargon and break down any complex ideas.\n"
    "- Use 5–8 smooth, vivid sentences in third person (never 'we' or 'I').\n"
    "- Do not include section headers or labels like 'Summary' or 'Abstract'. Just write the summary itself.\n\n"
    f"{abstract}"
)

simplified = simplifier(prompt, max_length=1000, do_sample=True, temperature=0.7)[0]['generated_text']

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
title: "AI Paper of the Week"
subtitle: {title}
date: {post_date}
categories: ["{topic}"]
---

### Title: {title}

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
