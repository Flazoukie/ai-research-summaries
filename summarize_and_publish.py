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
    "You are a science writer skilled at explaining complex ideas to curious non-experts.\n\n"
    "Your task is to rewrite the following academic abstract into a short, engaging, and easy-to-understand explanation for a general audience.\n\n"
    "Follow these rules:\n"
    "1. Start by explaining the real-world problem or motivation behind the research.\n"
    "2. Then describe what the researchers did to study or solve it.\n"
    "3. Clearly summarize what they found and why it matters.\n"
    "4. Avoid academic language or technical jargon — explain everything in everyday words.\n"
    "5. Write in 5–8 flowing, complete sentences. Use a natural tone — like explaining it to an interested teenager.\n"
    "6. Use third person only (no 'we' or 'I').\n"
    "7. Skip unnecessary details like exact sample sizes or long lists, unless they are crucial.\n"
    "8. Do NOT include any section titles like 'Summary:' or 'Abstract:'. Just write the explanation.\n\n"
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

### 📄 Full Abstract
{abstract_clean}

---

### 🔗 [Read the full paper]({url})

### 🧪 Model Notes
Simplified using `{MODEL}` via Hugging Face Inference API.
"""

# === Save post ===
post_path.write_text(content.strip())
print(f"✅ Blog post created at {post_path}")
