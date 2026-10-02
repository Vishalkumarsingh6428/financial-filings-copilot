# Financial Filings Copilot

**Evidence-Grounded Agentic Intelligence for SEC Filings**

🔗 **Live app:** https://financial-filings-copilot.streamlit.app

Financial Filings Copilot is an evidence-grounded, agentic RAG system for researching SEC filings such as 10-K and 10-Q reports.

Unlike a basic "chat with PDF" application that performs a single retrieval followed by generation, FilingsIQ uses a LangGraph-based decision workflow that evaluates retrieval quality, retries weak retrieval, reranks candidate evidence, generates answers from retrieved excerpts, and performs a separate citation-verification pass.

The system is designed around a simple principle:

> If the available evidence is insufficient, the system should not confidently invent an answer.

`Python 3.12` · `LangChain` · `LangGraph` · `Pinecone` · `Groq` · `FastAPI` · `Streamlit`

---

## Why Financial Filings Copilot?

Financial filings contain large amounts of dense, structured information. Finding a specific answer often requires navigating hundreds of pages across annual and quarterly reports.

Traditional keyword search can miss semantically related information, while vector-only retrieval can miss exact financial terminology.

Financial Filings Copilot combines multiple retrieval and reasoning components:

- Dense vector retrieval for semantic similarity
- BM25 keyword retrieval for exact financial terminology
- Reciprocal Rank Fusion (RRF) to combine retrieval signals
- Cross-encoder reranking to improve candidate ordering
- LLM-based retrieval grading to evaluate evidence quality
- Bounded query rewriting when retrieved evidence is insufficient
- Evidence-grounded generation using retrieved filing excerpts
- Citation verification using a separate LLM verification pass

This makes the system a retrieval and decision pipeline, rather than a simple LLM wrapper.

## System Architecture

                 User Question
                      │
                      ▼
          ┌──────────────────────┐
          │   Hybrid Retrieval   │
          │                      │
          │  Dense Vector Search │
          │          +           │
          │      BM25 Search     │
          └──────────┬───────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │ Reciprocal Rank      │
          │ Fusion (RRF)         │
          └──────────┬───────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │ Cross-Encoder        │
          │ Reranking            │
          │ 20 → Top 5           │
          └──────────┬───────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │    grade_docs        │
          │                      │
          │ Is the retrieved     │
          │ evidence sufficient? │
          └──────────┬───────────┘
                     │
            ┌────────┴────────┐
            │                 │
         Relevant          Not Relevant
            │                 │
            │                 ▼
            │          ┌───────────────┐
            │          │ rewrite_query │
            │          └───────┬───────┘
            │                  │
            │                  └──► Retrieve
            │
            ▼
     ┌─────────────────┐
     │    Generate     │
     │                 │
     │ Answer +        │
     │ Citations       │
     └────────┬────────┘
              │
              ▼
     ┌────────────────────┐
     │ verify_citations   │
     │                    │
     │ Are the generated  │
     │ claims supported   │
     │ by the evidence?   │
     └─────────┬──────────┘
               │
               ▼
      Answer + Sources +
     Verification Verdict
    


The retrieval retry loop is bounded to a maximum of two retries, preventing uncontrolled agentic loops.

## Retrieval Pipeline

### 1. Dense Retrieval

Filing chunks are embedded using `sentence-transformers/all-MiniLM-L6-v2`. The resulting vectors are stored in Pinecone using cosine similarity.

### 2. BM25 Retrieval

BM25 provides lexical retrieval based on exact terms appearing in the filing — particularly useful for financial research where exact terms matter: "contractual obligations," "internal controls," "market risk," "accounts receivable," "revenue recognition."

### 3. Reciprocal Rank Fusion

The dense and BM25 rankings are combined using Reciprocal Rank Fusion (RRF), benefiting from both semantic similarity and exact keyword matching.

### 4. Cross-Encoder Reranking

The hybrid retriever produces a candidate pool of 20 chunks, reranked using `cross-encoder/ms-marco-MiniLM-L-6-v2`, which evaluates the query and passage jointly. The final top 5 chunks are passed to the downstream LangGraph workflow.

## Agentic Retrieval Workflow
```
retrieve → grade_docs → Relevant?
├── Yes → generate → verify → END
└── No → rewrite_query → retrieve (max 2 retries)
```


The retry mechanism is deliberately bounded to prevent the system from repeatedly rewriting queries without making progress.


## Citation Verification

A separate LLM pass checks whether the generated answer's claims are actually supported by the retrieved excerpts — tested against a deliberately fabricated answer to confirm it discriminates rather than defaulting to "supported."

**Important:** verification evaluates the answer's claims *overall*; it does not guarantee exact sentence-to-citation alignment for every inline marker.

## Evaluation

**Metric:** Recall@5 on a hand-built 12-question evaluation set.

| Retrieval Method | Recall@5 |
|---|---|
| Vector-only | 58.33% (7/12) |
| Hybrid — BM25 + Vector + RRF | 66.67% (8/12) |
| **Hybrid + Cross-Encoder Reranking** | **75.00% (9/12)** |

**Evaluation nuance:** reranking is not an unconditional improvement — the Goldman Sachs risk-factors question passed under hybrid retrieval but regressed after reranking. Under the final configuration, 9/12 passed and 3/12 failed (NVIDIA Properties, Goldman Sachs Risk Factors, Meta MD&A). For NVIDIA and Meta, substantial real content was confirmed in the correct section, indicating a retrieval-ranking limitation rather than missing data.

## Companies Covered

**Technology:** AAPL, MSFT, GOOGL, NVDA, AMZN, META, TSLA, AMD
**Financial Services:** AXP, JPM, GS, MS, BAC, C, STT

15 companies, 75 filings (3×10-K + 2×10-Q each). The ingestion pipeline has no company-specific logic, so more tickers can be added through configuration alone.

## SEC Filing Pipeline
```
SEC EDGAR → Raw Filing Download → HTML/Primary Document
→ Structure-Aware Parsing → Section Extraction
→ Chunking → Embeddings → Pinecone
```

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Orchestration | LangGraph | Stateful workflow and conditional routing |
| LLM Framework | LangChain | LLM/retrieval abstractions |
| Vector Database | Pinecone | Persistent vector storage and metadata filtering |
| Keyword Retrieval | BM25 (`rank_bm25`) | Exact-term retrieval |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Candidate reranking |
| Embeddings | `all-MiniLM-L6-v2` | Local 384-dimensional embeddings |
| LLM | Groq — `gpt-oss-120b` | Answer generation and grading |
| API | FastAPI | Programmatic API access |
| UI | Streamlit | Chat interface, deployed on Streamlit Community Cloud |
| Data Source | SEC EDGAR | Real 10-K / 10-Q filings |
| Language | Python 3.12 | Application and pipeline |

## UI Features

The deployed interface goes beyond a plain Q&A box to make the system's trustworthiness visible:

- **Chat-style interface** with persistent conversation history
- **Evidence cards** — each cited source shown with company, fiscal year, filing type, item number, and a real excerpt from the retrieved text
- **Verification badge** — a visible supported/unsupported indicator driven by the graph's actual verification output
- **Distinct refusal styling** — when evidence is judged insufficient, the answer renders in a clearly marked box instead of looking like a normal response
- **Retrieval details panel** — an expandable, honest summary of the pipeline stages used and real measured response time
- **Company focus selector** and **clickable example questions** for first-time use
- **Streaming reveal** of the generated answer

## API

FilingsIQ also exposes a FastAPI interface:

- `GET /health` — health check
- `GET /companies` — list of available companies
- `POST /query` — ask a question

Example:
```json
{
  "question": "What was Apple's total net sales in fiscal year 2023?"
}
```

## Project Structure
```
financial-filings-copilot/
│
├── main.py
│
├── app/
│ ├── config.py
│ ├── ingestion/
│ │ ├── download.py
│ │ └── parse.py
│ ├── retrieval/
│ │ ├── chunking.py
│ │ ├── vectorstore.py
│ │ ├── hybrid.py
│ │ └── rerank.py
│ ├── graph/
│ │ ├── state.py
│ │ ├── nodes.py
│ │ └── build.py
│ ├── api/
│ │ └── main.py
│ └── ui/
│ └── streamlit_app.py
│
├── evaluation/
│ ├── questions.json
│ └── run_eval.py
│
├── data/
│ ├── raw/
│ └── processed/
│
├── requirements.txt
├── .env.example
├── .python-version
├── .gitignore
└── README.md
```



## Local Setup

**1. Clone the repository**
```bash
git clone https://github.com/Vishalkumarsingh6428/financial-filings-copilot.git
cd financial-filings-copilot
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Configure environment variables**
```bash
cp .env.example .env
```
Fill in:
```
SEC_EDGAR_EMAIL=your-email@example.com
PINECONE_API_KEY=your-pinecone-key
GROQ_API_KEY=your-groq-key
```



Never commit `.env` or API keys to GitHub.

## Build the Corpus

```bash
python -m app.ingestion.download
python -m app.ingestion.parse
python -m app.retrieval.chunking
python -m app.retrieval.vectorstore
```

## Run the Application

**Streamlit UI**
```bash
streamlit run app/ui/streamlit_app.py
```

**FastAPI**
```bash
python -m uvicorn app.api.main:app --reload --port 8000
```

## Deployment

Live on **Streamlit Community Cloud** at https://financial-filings-copilot.streamlit.app.

Two earlier platforms were tried and ruled out for documented reasons:
- **Hugging Face Spaces** — Gradio and Docker Spaces now require a paid PRO plan; only Static Spaces (which cannot run this app) are free.
- **Render** — the free tier's 512MB memory limit was insufficient for the combined footprint of PyTorch, the embeddings model, the cross-encoder reranker, and an in-memory BM25 index over 33K+ chunks, causing the deploy to be killed with an out-of-memory error. Streamlit Community Cloud's roughly 1GB free memory was sufficient.

## Design Decisions

**Why hybrid retrieval?** Exact lexical matches matter for financial terminology — e.g. "internal control over financial reporting" may be better retrieved with lexical matching than pure semantic similarity.

**Why rerank?** First-stage ranking isn't always ideal. Retrieving 20 candidates and reranking with a cross-encoder — which evaluates the full query-passage relationship jointly — improves final ordering.

**Why LangGraph?** The workflow contains real conditional decisions ("is the evidence relevant?"). LangGraph makes this routing explicit and keeps state across nodes.

**Why section-aware parsing?** A generic text splitter can destroy useful boundaries between Risk Factors, MD&A, Financial Statements, and Legal Proceedings.

**Why Streamlit over Gradio?** Deployment attempts on Hugging Face Spaces and Render each hit real platform-specific blockers. Streamlit Community Cloud offered free hosting with a higher memory ceiling, and porting the UI required no changes to the underlying retrieval/graph logic.

## Known Limitations

1. **Claim-level citation attribution** — verification evaluates whether the answer is supported by the evidence overall; it doesn't guarantee exact sentence-to-citation alignment for every inline marker.
2. **Retrieval is not perfect** — 75.00% Recall@5 (9/12); the 3 failing questions are retained in the evaluation rather than removed.
3. **Reranking can introduce regressions** — the Goldman Sachs case demonstrates reranking isn't guaranteed to improve every individual query.
4. **Filing sections may be incorporated by reference** — some filers don't contain every Part III section directly in the 10-K body.
5. **Multi-turn contextualization** — using chat history to rewrite follow-up questions is planned future work; the current graph focuses on Retrieve → Grade → Rewrite/Retry → Generate → Verify per single question.

## Security

API credentials are loaded through environment variables. Never commit `.env`, API keys, or any credentials. Hosted deployments use the platform's own secrets manager.

## Roadmap

### Completed
- [x] SEC EDGAR ingestion
- [x] Structure-aware HTML parsing
- [x] Section-aware chunking
- [x] Local embeddings
- [x] Pinecone vector search
- [x] LangGraph RAG workflow
- [x] Retrieval evaluation
- [x] Hybrid BM25 + vector retrieval
- [x] Reciprocal Rank Fusion
- [x] Cross-encoder reranking
- [x] Citation verification
- [x] FastAPI API
- [x] Streamlit chat interface with evidence cards and refusal styling
- [x] Streamlit Community Cloud deployment

### Future Work
- [ ] Multi-turn question contextualization
- [ ] Claim-level citation alignment
- [ ] Expanded evaluation benchmark
- [ ] Additional financial institutions and filings

## What Makes This Project Different?

Financial Filings Copilot is intentionally built around measured retrieval performance and failure analysis, rather than only demonstrating that an LLM can answer questions from documents. Every improvement — and every regression — is reported, not hidden.

Baseline → Vector Retrieval → Hybrid Retrieval → Reranking → Generation → Citation Verification

The goal is not to claim the system is perfect. The goal is to build a transparent, testable retrieval system where retrieval quality is measured, failures are visible, and unsupported answers are treated as a system failure rather than a successful response.


## License

MIT License

## Author

**Vishal Kumar Singh**
**IIT Madras**

Built as an applied research and engineering project exploring Retrieval-Augmented Generation, Agentic AI, Information Retrieval, Financial NLP, LLM evaluation, LangGraph workflows, and evidence-grounded AI systems.