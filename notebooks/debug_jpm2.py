from app.ingestion.parse import get_filing_dirs, extract_text, find_real_section_starts

dirs = get_filing_dirs("JPM", "10-K")
text = extract_text(dirs[0] / "primary-document.html")
sections = find_real_section_starts(text)
for item_num, title, pos in sections:
    print(f"Item {item_num}: {title}  (char {pos})")
