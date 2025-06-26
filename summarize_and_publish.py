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
authors = ", ".join(a["author"]["display_name"] for a in paper.get("authorships", []))
abstract = paper["abstract"]
topic = paper["topic"]
journal_date = paper.get("publication_date", "unknown")
post_date = datetime.date.today().isoformat()

print("🔧 Loading simplification model...")
simplifier = pipeline("text2text-generation", model="google/flan-t5-large")

# === Generate simplified version ===
print("🪄 Simplifying abstract...")
prompt = (
    f"Explain this academic abstract to a curious friend who does not have technical knowledge of the subject. "
    f"Use simple, clear language and keep it engaging and easy to follow. "
    f"Briefly explain any technical terms like Auto-Encoder, Swin Transformer, or Accuracy in simple words. "
    f"Round numbers and percentages for easier understanding. "
    f"Try to put improvements in a relatable way (for example, 'almost perfect accuracy'). "
    f"Avoid using 'we' or 'I' — write in third person, as you're describing someone else's work. "
    f"Ensure the explanation is sufficiently detailed, not overly short. "
    f"Start with a capital letter and end with a full stop.\n\n{abstract}"
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
subtitle: "{title}"
date: {post_date}
categories: ["{topic}"]
---

### 🧠 Topic: {topic}

**Authors**: {authors if authors else 'Unknown'}  
**Published in journal**: {journal_date}  

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
