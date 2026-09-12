---
title: Financial Filings Copilot
emoji: 📊
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: "5.0.0"
app_file: app.py
pinned: false
---

# Financial Filings Copilot

**An evidence-grounded, agentic RAG system for SEC filings — built with LangChain + LangGraph, not a "chat with PDF" wrapper.**

Ask a question about a real 10-K or 10-Q, and instead of a single retrieve-and-generate call, the system runs a stateful graph that checks its own retrieval quality, retries on weak evidence, and verifies its own citations before answering — refusing to answer rather than hallucinating when the evidence genuinely isn't there.

`Python 3.12` · `LangChain` · `LangGraph` · `Pinecone` · `Groq` · `FastAPI` · `Gradio`

---

## Why this isn't a toy RAG demo

Most "RAG over documents" projects are a single embedding search feeding a single LLM call. This one is built as a decision system:

- **Self-checking retrieval** — a `grade_docs` node judges whether what was retrieved can actually answer the question, and reformulates the query up to twice if not, instead of blindly trusting the top-k result
- **Hybrid search, not just vectors** — BM25 keyword search and dense vector search are fused with Reciprocal Rank Fusion, because semantic similarity alone measurably misses exact-term financial queries (see Evaluation below)
- **Reranking on a wider candidate pool** — 20 candidates are pulled and rescored by a cross-encoder before the final top-5 is chosen
- **Citation verification, not just citation display** — a second, independent LLM pass checks whether the generated answer's claims are actually supported by the cited excerpts, and is validated against a deliberately fabricated answer to confirm it actually discriminates rather than rubber-stamping
- **Every claim in this README is a measured result**, not an assumption — see the evaluation table below

## Architecture

```
User question
│
▼
contextualize_question (rewrite using chat history — planned for multi-turn)
│
▼
retrieve (hybrid BM25 + vector search, top 20 → cross-encoder rerank → top 5)
│
▼
grade_docs (LLM judges: does this evidence actually answer the question?)
│
├── NOT relevant ──► rewrite_query ──┐
│ │
▼ relevant (loops back to retrieve, max 2 retries)
generate (answer + citations, strictly from retrieved excerpts)
│
▼
verify_citations (independent pass: are the claims actually supported?)
│
▼
Answer + Sources + Verification verdict
```

Built as a real `StateGraph` (LangGraph) with conditional edges and a bounded retry loop — not a linear chain, and not a fixed sequence of function calls.

## Evaluation

Rather than assert that hybrid search and reranking "help," each was measured against a hand-built 12-question evaluation set spanning all 15 companies, with Recall@5 as the metric (does a chunk from the expected section appear in the top 5 results):

| Method | Recall@5 |
|---|---|
| Vector-only | 58.33% (7/12) |
| Hybrid (BM25 + Vector, RRF) | 66.67% (8/12) |
| **Hybrid + Reranked** | **75.00% (9/12)** |

Reranking is not reported as an unconditional win: one question (Goldman Sachs risk factors) that passed under hybrid search alone regressed after reranking — a real, disclosed nuance rather than a cherry-picked number. Two questions (NVIDIA properties, Meta's MD&A) remain unsolved despite confirmed substantial content in the correct section, documented as the honest current ceiling of this architecture rather than glossed over.

## Companies covered

**Tech:** AAPL, MSFT, GOOGL, NVDA, AMZN, META, TSLA, AMD
**Financial services:** AXP, JPM, GS, MS, BAC, C, STT

15 companies, 3× 10-K + 2× 10-Q each, pulled directly from SEC EDGAR — real, messy filing data, not a cleaned toy dataset. The ingestion pipeline has no company-specific logic, so more tickers can be added without code changes.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Orchestration | LangGraph | Real conditional graph, not a linear chain |
| Framework | LangChain | Document loaders, embeddings, retriever abstraction |
| Vector DB | Pinecone (serverless) | Managed, persists across restarts, native metadata filtering |
| Keyword search | BM25 (`rank_bm25`) | Catches exact-term matches vector search misses |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Joint query-passage scoring on a shortlist |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | Free, local, no API cost |
| LLM | Groq (`openai/gpt-oss-120b`) | Free tier, fast, no card required |
| API | FastAPI | `/query`, `/health`, `/companies` |
| UI | Gradio | HF Spaces-native, single-process deployment |

## Project structure
```
app/
├── ingestion/ # EDGAR download, structure-aware HTML parsing
├── retrieval/ # chunking, Pinecone vectorstore, hybrid search, reranking
├── graph/ # LangGraph state, nodes, graph assembly
├── api/ # FastAPI backend
├── ui/ # Gradio interface
└── config.py

evaluation/
├── questions.json # 12-question hand-built eval set
└── run_eval.py # Recall@5 across vector-only / hybrid / reranked

data/
├── raw/ # EDGAR downloads (gitignored — large, regeneratable)
└── processed/ # Parsed, section-labeled filing JSON (shipped with the app)
```

## Setup (local)

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in SEC_EDGAR_EMAIL, PINECONE_API_KEY, GROQ_API_KEY
python -m app.ingestion.download    # pull filings from EDGAR
python -m app.ingestion.parse       # parse into labeled sections
python -m app.retrieval.chunking    # chunk
python -m app.retrieval.vectorstore # embed + upsert to Pinecone
python -m app.ui.gradio_app         # run the UI locally
```

Or hit the API directly:
```bash
python -m uvicorn app.api.main:app --reload --port 8000
```

## Known limitations

- **Claim-level citation attribution isn't solved** — verification confirms an answer's overall claims are supported by the retrieved excerpts, but doesn't prove each individual inline citation marker maps to the exact sentence it's meant to support
- **Some sections are legitimately absent from the data**, not missing due to a bug — several filers (e.g. American Express, JPMorgan) incorporate Part III items (Executive Compensation, Related-Party Transactions) by reference to their proxy statement rather than writing them into the 10-K body, and Microsoft/Goldman Sachs similarly incorporate certain items by reference elsewhere in the same filing
- **Retrieval isn't perfect** — 2 of 12 evaluation questions remain unsolved even after hybrid search and reranking; this is reported as the honest current ceiling, not hidden

## Roadmap

Deployed to Hugging Face Spaces as the final phase of an 11-phase build.