# notebooks/inspect_chunks.py
from app.retrieval.chunking import load_all_documents

docs = load_all_documents()

print(f"Total chunks: {len(docs)}\n")

for i in range(3):
    print(f"=== Chunk {i} ===")
    print("Metadata:", docs[i].metadata)
    print("\nContent:")
    print(docs[i].page_content)
    print(f"\n(length: {len(docs[i].page_content)} chars)")
    print("=" * 60)
    print()