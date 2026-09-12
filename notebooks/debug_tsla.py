from app.ingestion.parse import get_filing_dirs, extract_text, ITEM_PATTERN
import re

dirs = get_filing_dirs("TSLA", "10-K")
text = extract_text(dirs[0] / "primary-document.html")

matches = list(ITEM_PATTERN.finditer(text))
print(f"ITEM_PATTERN (with title capture) found {len(matches)} matches\n")

for m in matches[:15]:
    item_num, title = m.group(1), m.group(2).strip()
    after = text[m.end():m.end() + 30].strip()
    is_toc = bool(re.match(r'^\d{1,4}\b', after))
    print(f"Item {item_num}: {title!r}")
    print(f"  after: {after[:30]!r}  -> {'REJECTED (looks like ToC)' if is_toc else 'KEPT'}")
    print()

raw_matches = list(re.finditer(r"Item\s+1A\.?", text, re.IGNORECASE))
print(f"'Item 1A' appears {len(raw_matches)} times at: {[m.start() for m in raw_matches]}\n")

for pos in raw_matches:
    print(f"--- Context at {pos.start()} ---")
    print(repr(text[pos.start():pos.start() + 100]))
    print()