# notebooks/debug_jpm.py
from app.ingestion.parse import get_filing_dirs, extract_text, ITEM_PATTERN
import re

dirs = get_filing_dirs("JPM", "10-K")
text = extract_text(dirs[0] / "primary-document.html")

matches = list(ITEM_PATTERN.finditer(text))
item1_matches = [m for m in matches if m.group(1) == "1"]

print(f"Found {len(item1_matches)} raw 'Item 1' matches (before ToC filtering)\n")
for m in item1_matches:
    title = m.group(2).strip()
    after = text[m.end():m.end() + 60].strip()
    print(f"At {m.start()}: title={title!r}")
    print(f"  followed by: {after!r}")
    print()