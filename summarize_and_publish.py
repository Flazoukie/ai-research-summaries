import json
import datetime
import os
from pathlib import Path
import requests
import html
import re
import yaml

# === CONFIG ===
INPUT_PATH = Path("paper_to_summarize.json")
POSTS_DIR = Path("data-blog/posts")
POSTS_DIR.mkdir(parents=True, exist_ok=True)
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
MODEL = "HuggingFaceH4/zephyr-7b-beta"  # or use "mistralai/Mistral-7B-Instruct-v0.2"
MAX_ABSTRACT_LENGTH = 1500  # threshold for abstract length

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

def summarize_text(text):
    print("📝 Summarizing long abstract before simplification...")
    summary_prompt = (
        "Summarize the following academic abstract in a concise way, capturing the main points clearly:\n\n"
        f"{text}"
    )
    response = requests.post(
        f"https://api-inference.huggingface.co/models/{MODEL}",
        headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
        json={
            "inputs": summary_prompt,
            "parameters": {
                "temperature": 0.4,
                "max_new_tokens": 400,
                "top_p": 0.9,
                "repetition_penalty": 1.1,
                "return_full_text": False
            }
        },
        timeout=60
    )
    response.raise_for_status()
    result = response.json()
    if isinstance(result, dict) and "error" in result:
        print(f"API Error during summarization: {result['error']}")
        return text  # fallback to original abstract if error
    return result[0].get("generated_text", text).strip()

# Use original abstract if short enough, else summarize first
if len(abstract) > MAX_ABSTRACT_LENGTH:
    abstract_for_prompt = summarize_text(abstract)
else:
    abstract_for_prompt = abstract.strip()

# === Generate simplified version ===
print("🪄 Simplifying abstract using Hugging Face API...")
prompt = (
    "You are an expert science communicator who explains complex research clearly and simply.\n\n"
    "Rewrite the following academic abstract entirely in your own words, creating a fresh, engaging, and complete explanation for a curious general audience.\n"
    "Write a single, self-contained paragraph of 5 to 8 sentences (about 80 to 150 words) starting from the beginning of the topic.\n"
    "Do NOT summarize or copy phrases from the original abstract.\n"
    "Avoid technical jargon and explain ideas as if speaking to an interested teenager.\n"
    "Use a friendly but professional tone, and write only in third person (no 'I' or 'we').\n"
    "Do not include headings or labels.\n"
    "At the end, add a brief sentence explaining why this research matters to everyday people or society.\n\n"
    "Here is the abstract:\n\n"
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

# === Clean up abstract text ===
abstract_clean = html.unescape(abstract.strip())
abstract_clean = re.sub(r'\*\*', r'\\*\\*', abstract_clean)

# === YAML front matter ===
front_matter = yaml.safe_dump({
    "title": "AI Paper of the Week",
    "subtitle": title,
    "date": post_date,
    "categories": [topic]
}, sort_keys=False).strip()

# === Final post content ===
content = f"""---
{front_matter}
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
slug = f"{post_date}-ai-summary"
post_path = POSTS_DIR / f"{slug}.qmd"
post_path.write_text(content.strip())

print(f"✅ Blog post created at {post_path}")
