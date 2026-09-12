# notebooks/debug_fiscal_year.py — update the ticker/accession, rerun
from app.ingestion.parse import get_filing_dirs, extract_text

dirs = get_filing_dirs("MS", "10-K")
target = [d for d in dirs if d.name == "0000895421-24-000300"][0]
text = extract_text(target / "primary-document.html")

for keyword in ["fiscal year", "period ended", "For the "]:
    idx = text.lower().find(keyword.lower())
    print(f"--- '{keyword}' found at {idx} ---")
    if idx != -1:
        print(text[max(0, idx - 100):idx + 300])
    print()