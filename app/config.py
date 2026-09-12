import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SEC_EDGAR_EMAIL = os.environ.get("SEC_EDGAR_EMAIL", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
LLM_MODEL = "openai/gpt-oss-120b"
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY", "")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

TICKERS = [
    "AAPL", "MSFT", "GOOGL", "NVDA", "AMZN", "META", "TSLA", "AMD",
    "AXP", "JPM", "GS", "MS", "BAC", "C", "STT",
]

# app/config.py — add this dict
COMPANY_NAME_TO_TICKER = {
    "APPLE": "AAPL", "MICROSOFT": "MSFT", "GOOGLE": "GOOGL", "ALPHABET": "GOOGL",
    "NVIDIA": "NVDA", "AMAZON": "AMZN", "META": "META", "FACEBOOK": "META",
    "TESLA": "TSLA", "AMD": "AMD", "AMERICAN EXPRESS": "AXP", "JPMORGAN": "JPM",
    "JP MORGAN": "JPM", "GOLDMAN SACHS": "GS", "GOLDMAN": "GS",
    "MORGAN STANLEY": "MS", "BANK OF AMERICA": "BAC", "CITIGROUP": "C",
    "CITI": "C", "STATE STREET": "STT",
}

INDEX_NAME = "financial-filings-rag"
N_10K = 3
N_10Q = 2