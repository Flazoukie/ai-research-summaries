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
MODEL = "facebook/bart-large-cnn"  
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
        json={"inputs": summary_prompt},  # 👈 simplified!
        timeout=60
    )
    response.raise_for_status()
    result = response.json()
    if isinstance(result, dict) and "error" in result:
        print(f"API Error during summarization: {result['error']}")
        return text  # fallback to original abstract if error
    return result[0].get("summary_text", text).strip()


# === Generate simplified version ===
print("🪄 Simplifying abstract using Hugging Face API...")
prompt = (
    "You are an expert AI communicator. Your goal is to rewrite a complex academic abstract for a "
    "tech-savvy but non-expert audience, like a curious student or a journalist.\n\n"
    "Follow these instructions precisely:\n"
    "1. Rewrite the abstract into a single, cohesive paragraph between 5 and 8 sentences.\n"
    "2. Start by explaining the core problem the researchers are trying to solve.\n"
    "3. Clearly describe their unique method or solution.\n"
    "4. Mention the key result or finding.\n"
    "5. The final sentence MUST explain the real-world importance or potential impact of this research.\n"
    "6. Use simple, engaging language. Avoid jargon or explain it in the simplest terms.\n"
    "7. Do not add any information not present in the original text. Do not use phrases like 'This paper...' or 'The abstract describes...'.\n\n"
    "--- ABSTRACT TO SIMPLIFY ---\n"
    f"{abstract_for_prompt}"
)

response = requests.post(
    f"https://api-inference.huggingface.co/models/{MODEL}",
    headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
    json={
        "inputs": prompt,
        "parameters": {
            "temperature": 0.35,
            "top_p": 0.85,
            "repetition_penalty": 1.15,
            "do_sample": False,
            "use_cache": False,
            "max_new_tokens": 300,
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
