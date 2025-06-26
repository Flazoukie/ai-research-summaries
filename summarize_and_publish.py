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
simplifier = pipeline("text2text-generation", model="t5-small")

# === Generate simplified version ===
print("🪄 Simplifying abstract...")
prompt = (
    f"Explain this academic abstract like you're telling a curious friend who doesn't know anything about AI. "
    f"Use simple language, keep it lively and interesting, and make it easy to follow:\n\n{abstract}"
)
simplified = simplifier(prompt, max_length=200)[0]['generated_text']

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
Simplified using `t5-small`.
"""

# === Save post ===
post_path.write_text(content.strip())
print(f"✅ Blog post created at {post_path}")

