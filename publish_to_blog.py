# publish_to_blog.py

import shutil
from pathlib import Path

# Define paths
SOURCE_DIR = Path("posts")
TARGET_DIR = Path("../data-blog/posts")

# Ensure target exists
TARGET_DIR.mkdir(parents=True, exist_ok=True)

# Find the most recent .qmd file in posts/
def get_latest_qmd():
    qmd_files = list(SOURCE_DIR.glob("*.qmd"))
    if not qmd_files:
        print("⚠️ No .qmd files found in posts/")
        return None
    return max(qmd_files, key=lambda f: f.stat().st_mtime)

# Copy the file to the blog repo, overwriting if it exists
def copy_to_blog(file):
    target_file = TARGET_DIR / file.name
    shutil.copy2(file, target_file)
    print(f"✅ Copied {file.name} to blog repo at {target_file}")

if __name__ == "__main__":
    latest_post = get_latest_qmd()
    if latest_post:
        copy_to_blog(latest_post)