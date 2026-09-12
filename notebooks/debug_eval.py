# notebooks/debug_eval.py
from app.graph.nodes import extract_filters

# notebooks/debug_eval.py — add this below the existing code
import json
from pathlib import Path
from collections import defaultdict

questions = [
    "What legal proceedings is Microsoft involved in?",
    "What risk factors does Tesla disclose about its business?",
    "What is JPMorgan's business description?",
    "What quantitative market risk disclosures does Goldman Sachs make?",
    "What executive compensation information does American Express disclose?",
    "What controls and procedures does Amazon describe?",
    "What does Meta's MD&A say about its financial results?",
]

for q in questions:
    print(f"{q}\n  -> {extract_filters(q)}\n")

sections_by_ticker = defaultdict(set)
for p in Path("data/processed").glob("*.json"):
    d = json.load(open(p))
    for s in d["sections"]:
        sections_by_ticker[d["ticker"]].add((s["item_number"], s["section_title"][:40]))

for ticker in ["MSFT", "TSLA", "JPM", "GS", "AXP", "AMZN", "META"]:
    print(f"\n{ticker}:")
    for item, title in sorted(sections_by_ticker[ticker]):
        print(f"  Item {item}: {title}")