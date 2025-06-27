import json
import datetime
import os
from pathlib import Path
import requests
import html
import re

# === CONFIG ===
INPUT_PATH = Path("paper_to_summarize.json")
POSTS_DIR = Path("data-blog/posts")
POSTS_DIR.mkdir(parents=True, exist_ok=True)
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
MODEL = "HuggingFaceH4/zephyr-7b-beta"  # or use "mistralai/Mistral-7B-Instruct-v0.2"

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

# === Generate simplified version ===
print("🪄 Simplifying abstract using Hugging Face API...")
prompt = (
    "You are an expert science communicator who explains complex research clearly and simply.\n\n"
    "Rewrite the following academic abstract completely in your own words, creating a fresh, engaging explanation for a curious general audience.\n\n"
    "Do NOT just summarize or copy phrases from the original abstract.\n"
    "Write in a natural, flowing paragraph of 5 to 8 sentences (about 80 to 150 words).\n"
    "Avoid technical jargon; explain ideas as if speaking to an interested teenager.\n"
    "Use a friendly but professional tone, and write only in third person (no 'I' or 'we').\n"
    "Do not include headings or labels like 'Summary' or 'Explanation'.\n"
    "At the end, add a brief sentence explaining why this research matters to everyday people or society.\n\n"
    "Here is the abstract to rewrite:\n\n"
    f"{abstract_for_prompt}"
)

response = requests.post(
    f"https://api-inference.huggingface.co/models/{MODEL}",
    headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
    json={
        "inputs": prompt,
        "parameters": {
            "temperature": 0.35,
            "max_new_tokens": 250,
            "top_p": 0.9,
            "repetition_penalty": 1.1,
            "return_full_text": False
        }
    },
    timeout=60
)

response.raise_for_status()
simplified = response.json()[0]["generated_text"]

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

### 📄 Original Abstract
{abstract_clean}

---

### 🔗 [Read the full paper]({url})

### 🧪 Model Notes
Simplified using `{MODEL}` via Hugging Face Inference API.
"""

# === Save post ===
post_path.write_text(content.strip())
print(f"✅ Blog post created at {post_path}")
