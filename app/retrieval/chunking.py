# app/retrieval/chunking.py
import json
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.config import PROCESSED_DATA_DIR

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def load_processed_filing(json_path: Path) -> dict:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def filing_to_documents(filing: dict) -> list[Document]:
    docs = []
    for section in filing["sections"]:
        if section["char_count"] < 50:
            continue
        chunks = splitter.split_text(section["text"])
        for i, chunk_text in enumerate(chunks):
            docs.append(Document(
                page_content=chunk_text,
                metadata={
                    "ticker": filing["ticker"],
                    "filing_type": filing["filing_type"],
                    "fiscal_year": filing["fiscal_year"],
                    "accession_number": filing["accession_number"],
                    "item_number": section["item_number"],
                    "section_title": section["section_title"],
                    "chunk_index": i,
                },
            ))
    return docs


def load_all_documents() -> list[Document]:
    all_docs = []
    for json_path in sorted(PROCESSED_DATA_DIR.glob("*.json")):
        filing = load_processed_filing(json_path)
        all_docs.extend(filing_to_documents(filing))
    return all_docs


if __name__ == "__main__":
    docs = load_all_documents()
    print(f"Total chunks across all filings: {len(docs)}")
    print(f"\nSample chunk metadata: {docs[0].metadata}")
    print(f"Sample chunk text (first 300 chars):\n{docs[0].page_content[:300]}")