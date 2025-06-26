import json
import datetime
from pathlib import Path
from transformers import pipeline
import html 

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

# === Load Hugging Face model ===
print("🔧 Loading simplification model...")
simplifier = pipeline("text2text-generation", model="pszemraj/t5-large-eli5")

# === Generate simplified version ===
print("🪄 Simplifying abstract...")
prompt = (
    f"Explain the following academic abstract in a clear, friendly way, as if you were talking to a curious friend who doesn't know anything about AI or science. "
    f"Break it into short, readable paragraphs. Use plain language and keep it engaging. "
    f"The explanation should start with a capital letter and end with a full stop:\n\n{abstract}"
)
simplified = simplifier(prompt, max_length=1000)[0]['generated_text']

# === Determine paper URL ===
doi = paper.get("doi")
url = f"https://doi.org/{doi}" if doi else paper["id"].replace("https://openalex.org/", "https://doi.org/")

# === Generate post content ===
slug = f"{date_str}-ai-summary"
post_path = POSTS_DIR / f"{slug}.qmd"

# Clean up abstract HTML entities (e.g. &lt;, &gt;, &amp;)
abstract_clean = html.unescape(abstract.strip())

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

### 🪄 Explained Simply
{simplified.strip()}

---

### 📄 Full Abstract
{abstract_clean}

---

### 🔗 [Read the full paper]({url})

### 🧪 Model Notes
Simplified using `pszemraj/t5-large-eli5`.
"""

# === Save post ===
post_path.write_text(content.strip())
print(f"✅ Blog post created at {post_path}")

