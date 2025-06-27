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
                "temperature": 0.5,
                "max_new_tokens": 200,
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
    "You will receive a raw academic abstract. Rewrite it *entirely in your own words* as a new paragraph, NOT just summarizing or changing small phrases.\n"
    "Explain the motivation, approach, and findings in clear, everyday language, without technical jargon.\n\n"
    "Rules:\n"
    "- Do not quote or reuse exact phrases from the abstract.\n"
    "- Write a fresh explanation of 5–8 sentences (80–150 words).\n"
    "- Imagine you are explaining it to a smart teenager.\n"
    "- Use a professional but friendly tone.\n"
    "- End with 1 sentence about why this matters for society.\n\n"
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
