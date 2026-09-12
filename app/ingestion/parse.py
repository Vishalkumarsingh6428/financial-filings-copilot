from pathlib import Path
import re
import json
from bs4 import BeautifulSoup
from app.config import RAW_DATA_DIR


def get_filing_dirs(ticker: str, filing_type: str) -> list[Path]:
    base = RAW_DATA_DIR / "sec-edgar-filings" / ticker / filing_type
    return sorted(base.iterdir()) if base.exists() else []

FOOTER_PATTERN = re.compile(r'^.{2,60}\|\s*\d{4}\s*Form\s*10-[KQ]\s*\|\s*\d+$')

SYMBOL_ONLY_PATTERN = re.compile(r'^[®™©]+$|^SM$|^TM$')

def clean_lines(lines: list[str]) -> list[str]:
    cleaned = []
    for line in lines:
        if FOOTER_PATTERN.match(line):
            continue
        if SYMBOL_ONLY_PATTERN.match(line.strip()):
            if cleaned:
                cleaned[-1] = cleaned[-1] + line.strip()
            continue
        cleaned.append(line)
    return cleaned


def extract_text(html_path: Path) -> str:
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    for tag in soup(["script", "style"]):
        tag.decompose()

    for tag in soup.find_all("ix:header"):
        tag.decompose()

    for tag in soup.find_all(style=lambda s: s and "display:none" in s.replace(" ", "")):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    lines = clean_lines(lines)
    return "\n".join(lines)

ITEM_PATTERN = re.compile(
    r'Item\s+(\d{1,2}[A-Z]?)\.\s*\n?\s*([^\n]{2,150})\n',
    re.IGNORECASE,
)

def find_real_section_starts(text: str):
    sections = []
    for m in ITEM_PATTERN.finditer(text):
        item_num, title = m.group(1), m.group(2).strip()

        if re.match(r'^\d+$', title):
            continue

        if re.match(r'^item\s+\d', title, re.IGNORECASE):  # title is itself a cross-reference
            continue

        after = text[m.end():m.end() + 50].strip()
        after_stripped = after.lstrip('.').strip()
        if re.match(r'^\d{1,4}\b', after_stripped):
            continue

        sections.append((item_num, title, m.start()))
    return sections

def split_into_sections(text: str, sections: list) -> list[dict]:
    """Given section boundaries, slice the text into labeled section dicts."""
    results = []
    for i, (item_num, title, start) in enumerate(sections):
        end = sections[i + 1][2] if i + 1 < len(sections) else len(text)
        section_text = text[start:end].strip()
        results.append({
            "item_number": item_num,
            "section_title": title,
            "text": section_text,
            "char_count": len(section_text),
        })
    return results


MONTHS = r'(January|February|March|April|May|June|July|August|September|October|November|December)'

def get_fiscal_year(text: str) -> str:
    """Best-effort fiscal year extraction — tolerant of table-flattening
    interleaving unrelated text between a date's month/day and its year."""
    patterns = [
        rf'fiscal year ended[\s\S]{{0,50}}{MONTHS}\s+\d{{1,2}}[\s\S]{{0,150}}?,\s*(\d{{4}})',
        rf'\bfor the year ended[\s\S]{{0,50}}{MONTHS}\s+\d{{1,2}}[\s\S]{{0,150}}?,\s*(\d{{4}})',
        rf'period ended[\s\S]{{0,50}}{MONTHS}\s+\d{{1,2}}[\s\S]{{0,150}}?,\s*(\d{{4}})',
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(2)
    return "unknown"


def process_filing(ticker: str, filing_type: str, filing_dir: Path) -> dict:
    html_path = filing_dir / "primary-document.html"
    text = extract_text(html_path)
    sections = find_real_section_starts(text)
    parsed_sections = split_into_sections(text, sections)
    fiscal_year = get_fiscal_year(text[:15000])  # cover page is near the top

    return {
        "ticker": ticker,
        "filing_type": filing_type,
        "accession_number": filing_dir.name,
        "fiscal_year": fiscal_year,
        "source_html": str(html_path),
        "sections": parsed_sections,
    }


def process_all_filings(tickers=None, filing_types=("10-K", "10-Q")):
    from app.config import TICKERS, PROCESSED_DATA_DIR
    tickers = tickers or TICKERS
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    total, failed = 0, []
    for ticker in tickers:
        for filing_type in filing_types:
            dirs = get_filing_dirs(ticker, filing_type)
            for filing_dir in dirs:
                try:
                    parsed = process_filing(ticker, filing_type, filing_dir)
                    out_path = PROCESSED_DATA_DIR / f"{ticker}_{filing_type}_{filing_dir.name}.json"
                    with open(out_path, "w", encoding="utf-8") as f:
                        json.dump(parsed, f, indent=2)
                    total += 1
                except Exception as e:
                    failed.append((ticker, filing_type, filing_dir.name, str(e)))

    print(f"Processed {total} filings")
    if failed:
        print(f"\n{len(failed)} failures:")
        for t, ft, acc, err in failed:
            print(f"  {t} {ft} {acc}: {err}")


if __name__ == "__main__":
    process_all_filings()