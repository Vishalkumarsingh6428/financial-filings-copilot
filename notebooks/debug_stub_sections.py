# notebooks/debug_stub_sections.py
import json
from pathlib import Path

checks = [
    ("MSFT", "3"), ("JPM", "1"), ("GS", "7A"),
    ("AXP", "11"), ("AMZN", "9A"), ("META", "7"),
]

for ticker, item in checks:
    for p in Path("data/processed").glob(f"{ticker}_10-K_*.json"):
        d = json.load(open(p))
        for s in d["sections"]:
            if s["item_number"] == item:
                print(f"{ticker} Item {item}: {s['char_count']} chars")
                print(f"  Preview: {s['text'][:200]}")
                print()
                break
        break  # just check the first 10-K per company for now