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
    "Rewrite the following academic abstract into a brief, engaging explanation for a curious general audience.\n\n"
    "Follow these guidelines carefully:\n"
    "1. Begin by explaining the real-world problem or motivation behind the research in simple terms.\n"
    "2. Describe what the researchers did to address the problem, in everyday language.\n"
    "3. Summarize the key findings and why they matter.\n"
    "4. Avoid technical jargon or complex terms; explain ideas as if speaking to an interested teenager.\n"
    "5. Keep the explanation between 5 and 8 sentences, concise and easy to follow.\n"
    "6. Use a natural, friendly tone but maintain professionalism.\n"
    "7. Write only in third person (no 'I' or 'we').\n"
    "8. Do not repeat ideas or phrases unnecessarily; be clear and to the point.\n"
    "9. Do not include any headings, labels, or phrases like 'Summary:' or 'Abstract:'. Just provide the explanation.\n"
    "10. Add a brief sentence about why this research matters to everyday people or society.\n\n"
    "Here is the abstract to rewrite:\n\n"
    f"{abstract.strip()}"
)


response = requests.post(
    f"https://api-inference.huggingface.co/models/{MODEL}",
    headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
    json={"inputs": prompt, "parameters": {"temperature": 0.7, "max_new_tokens": 500, "return_full_text": False}},
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
