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
    "You are an expert science communicator. Your task is to rewrite the following academic abstract into a short, clear, and engaging explanation for a curious reader with no technical background.\n\n"
    "Follow these guidelines:\n"
    "1. Start by explaining the real-world problem the research addresses.\n"
    "2. Describe what the researchers did to tackle it.\n"
    "3. Clearly state what they found and why it matters.\n"
    "4. Avoid technical jargon—explain complex ideas in everyday language.\n"
    "5. Use 5–8 natural, flowing sentences. Imagine talking to an interested teenager.\n"
    "6. Write in third person only (never “we” or “I”).\n"
    "7. Round numbers and give context when useful.\n"
    "8. Make it sound human, helpful, and easy to read.\n\n"
    "Example of style:\n"
    "Original abstract: 'This literature review examines how artificial intelligence (AI)-powered business intelligence (BI) platforms are being leveraged to advance energy management and sustainability (ESG) goals in corporations. A systematic search of recent studies from Scopus, IEEE, Web of Science, and other databases yielded ~65 relevant peer-reviewed sources. We synthesized findings into five thematic areas: (1) AI applications in ESG reporting and automation, (2) BI systems for energy data visualization and monitoring, (3) predictive analytics for carbon and utility forecasting, (4) real-time dashboards for corporate sustainability decision-making, and (5) risks, biases, and ethical considerations of ESG technology. The review finds that AI-driven BI tools are streamlining sustainability reporting and assurance, enabling real-time energy monitoring and analytics, and improving forecasting of carbon footprints and energy consumption. These technologies have helped organizations identify efficiency opportunities and inform strategic sustainability decisions, with reported energy savings and emissions reductions in various cases. However, challenges persist, including data integration issues, algorithmic biases, and the need for ethical frameworks to govern AI in ESG. We identify critical research gaps such as under-studied sectors and the social and governance dimensions of ESG tech and propose directions for future investigation.'\n\n"
    "Summary: 'This review looks at how businesses are using artificial intelligence (AI) and business intelligence (BI) tools to improve energy management and sustainability efforts. About 65 recent studies were analyzed. The findings fall into five areas: better environmental reporting through AI; systems for visualizing and monitoring energy use; predicting future energy needs and carbon emissions; dashboards for quick sustainability decisions; and the risks, biases, and ethics of these technologies. AI-driven BI tools are making sustainability reporting easier, enabling real-time energy tracking, and improving carbon-footprint forecasts. Companies have used them to find energy-saving opportunities and cut emissions. Yet challenges remain—combining diverse data, addressing algorithmic bias, and setting ethical rules for AI in sustainability. The review also highlights gaps in social and governance research and suggests where future studies should focus.'\n\n"
    "Now rewrite this abstract in the same style:\n\n"
    f"{abstract}"
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
date: {post_date}
categories: ["{topic}"]
---

### Title: {title}

### 🧠 Topic: {topic}

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
