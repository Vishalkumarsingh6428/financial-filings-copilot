# FilingsIQ

**Evidence-Grounded Agentic Intelligence for SEC Filings**

FilingsIQ is an evidence-grounded, agentic RAG system for researching SEC filings such as 10-K and 10-Q reports.

Unlike a basic "chat with PDF" application that performs a single retrieval followed by generation, FilingsIQ uses a LangGraph-based decision workflow that evaluates retrieval quality, retries weak retrieval, reranks candidate evidence, generates answers from retrieved excerpts, and performs a separate citation-verification pass.

The system is designed around a simple principle:

> If the available evidence is insufficient, the system should not confidently invent an answer.

`Python 3.12` · `LangChain` · `LangGraph` · `Pinecone` · `Groq` · `FastAPI` · `Gradio`

---

## Why FilingsIQ?

Financial filings contain large amounts of dense, structured information. Finding a specific answer often requires navigating hundreds of pages across annual and quarterly reports.

Traditional keyword search can miss semantically related information, while vector-only retrieval can miss exact financial terminology.

FilingsIQ combines multiple retrieval and reasoning components:

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
```
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
```

The retrieval retry loop is bounded to a maximum of two retries, preventing uncontrolled agentic loops.

## Retrieval Pipeline

### 1. Dense Retrieval

Filing chunks are embedded using `sentence-transformers/all-MiniLM-L6-v2`. The resulting vectors are stored in Pinecone using cosine similarity.

Dense retrieval helps identify passages that are semantically related to the user's question even when the exact wording differs.

### 2. BM25 Retrieval

BM25 provides lexical retrieval based on exact terms appearing in the filing — particularly useful for financial research where exact terms matter: "contractual obligations," "internal controls," "market risk," "accounts receivable," "revenue recognition." BM25 complements dense retrieval by capturing these exact terms.

### 3. Reciprocal Rank Fusion

The dense and BM25 rankings are combined using Reciprocal Rank Fusion (RRF). Instead of directly comparing vector similarity scores with BM25 scores (which aren't on comparable scales), RRF combines their rankings — benefiting from both semantic similarity and exact keyword matching.

### 4. Cross-Encoder Reranking

The hybrid retriever produces a candidate pool of 20 chunks. These are reranked using `cross-encoder/ms-marco-MiniLM-L-6-v2`, which evaluates the query and passage jointly rather than relying only on independent embeddings. The final top 5 chunks are passed to the downstream LangGraph workflow.

## Agentic Retrieval Workflow

The system is implemented as a LangGraph `StateGraph` with conditional routing:
```
retrieve → grade_docs → Relevant?
├── Yes → generate → verify → END
└── No → rewrite_query → retrieve (max 2 retries)
```

The retry mechanism is deliberately bounded to prevent the system from repeatedly rewriting queries without making progress.

## Citation Verification

Generating an answer with citations is not enough — a retrieval system can still produce an unsupported statement while attaching a legitimate-looking source. FilingsIQ performs a separate LLM verification pass after answer generation, checking whether the answer's claims are actually supported by the retrieved excerpts.

The verifier was tested against a deliberately fabricated answer to confirm it could distinguish supported information from unsupported claims rather than simply returning SUPPORTED by default.

**Important:** the current verifier evaluates whether the answer's claims are supported by the retrieved evidence *overall*. It does not guarantee that every individual inline citation marker is mapped to the exact sentence it supports.

## Evaluation

Rather than assuming hybrid retrieval and reranking improve performance, FilingsIQ evaluates each retrieval stage on a hand-built 12-question evaluation set covering technology and financial-services companies.

**Metric:** Recall@5 — a question is counted as successful when a chunk from the expected filing section appears among the top 5 retrieved results.

| Retrieval Method | Recall@5 |
|---|---|
| Vector-only | 58.33% (7/12) |
| Hybrid — BM25 + Vector + RRF | 66.67% (8/12) |
| **Hybrid + Cross-Encoder Reranking** | **75.00% (9/12)** |

Hybrid retrieval improved Recall@5 by 8.34 percentage points over vector-only retrieval. Adding cross-encoder reranking produced a further 8.33 percentage-point improvement.

**Evaluation nuance:** reranking was not an unconditional improvement. The Goldman Sachs risk-factors question passed under hybrid retrieval but regressed after reranking. Under the final Hybrid + Reranked configuration, 9/12 questions passed and 3/12 failed:

- NVIDIA — Properties
- Goldman Sachs — Risk Factors
- Meta — MD&A / Financial Results

For NVIDIA and Meta, substantial content was confirmed to exist in the correct filing sections, indicating a retrieval/ranking limitation rather than missing source data. The Goldman Sachs result demonstrates that reranking can improve overall retrieval performance while still introducing individual regressions.

## Companies Covered

**Technology:** AAPL (Apple), MSFT (Microsoft), GOOGL (Alphabet), NVDA (NVIDIA), AMZN (Amazon), META (Meta), TSLA (Tesla), AMD

**Financial Services:** AXP (American Express), JPM (JPMorgan Chase), GS (Goldman Sachs), MS (Morgan Stanley), BAC (Bank of America), C (Citigroup), STT (State Street)

**15 companies.** For each, the ingestion pipeline targets 3 most recent 10-K filings + 2 most recent 10-Q filings — a target corpus of 15 × 5 = 75 filings. The ingestion pipeline is designed without company-specific parsing logic, allowing additional tickers to be added through configuration.

## SEC Filing Pipeline
```
SEC EDGAR → Raw Filing Download → HTML/Primary Document
→ Structure-Aware Parsing → Section Extraction
→ Chunking → Embeddings → Pinecone
```

The parser removes HTML and XBRL noise while preserving meaningful filing structure (Item 1 Business, Item 1A Risk Factors, Item 7 MD&A, Item 8 Financial Statements, etc.). Section-aware metadata is retained during chunking so retrieval can be filtered and evaluated at the filing-section level.

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
| UI | Gradio | Interactive research interface |
| Data Source | SEC EDGAR | Real 10-K / 10-Q filings |
| Language | Python 3.12 | Application and pipeline |

## API

FilingsIQ exposes a FastAPI interface:

- `GET /health` — health check
- `GET /companies` — list of available companies
- `POST /query` — ask a question

Example:
```json
{
  "question": "What was Apple's total net sales in fiscal year 2023?"
}
```

The API returns the generated answer together with retrieved sources and the citation-verification result.

## Project Structure
```
financial-filings-copilot/
│
├── app.py
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
│ └── gradio_app.py
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
python -m app.ingestion.download      # download SEC filings
python -m app.ingestion.parse         # parse filings
python -m app.retrieval.chunking      # create chunks
python -m app.retrieval.vectorstore   # generate embeddings and upload to Pinecone
```

## Run the Application

**Gradio UI**
```bash
python -m app.ui.gradio_app
```

**FastAPI**
```bash
python -m uvicorn app.api.main:app --reload --port 8000
```

## Design Decisions

**Why hybrid retrieval?** Financial filings contain terminology where exact lexical matches matter — e.g. "internal control over financial reporting" may be better retrieved with lexical matching than pure semantic similarity. BM25 complements dense retrieval by capturing these exact terms.

**Why rerank?** Retrieval systems are optimized for high recall, but the first-stage ranking isn't always ideal. Retrieving more candidates (20) and reranking with a cross-encoder — which evaluates the relationship between the full query and passage jointly — improves final ordering before generation.

**Why LangGraph?** The workflow contains real conditional decisions ("is the evidence relevant?") that determine whether to generate or retry. LangGraph makes this routing explicit and keeps state across nodes, rather than hand-chaining function calls.

**Why section-aware parsing?** SEC filings are structured documents. A generic text splitter can destroy useful boundaries between Risk Factors, MD&A, Financial Statements, and Legal Proceedings. Preserving section metadata makes retrieval more meaningful and allows performance to be evaluated against expected filing sections.

## Known Limitations

1. **Claim-level citation attribution** — citation verification evaluates whether the generated answer is supported by the retrieved evidence overall; it does not guarantee exact sentence-to-citation alignment for every inline marker.
2. **Retrieval is not perfect** — the final Hybrid + Reranked configuration achieves 75.00% Recall@5 (9/12); the 3 failing questions are retained in the evaluation rather than removed from the test set.
3. **Reranking can introduce regressions** — the Goldman Sachs risk-factors question demonstrates that reranking is not guaranteed to improve every individual query, an important trade-off of multi-stage retrieval systems.
4. **Filing sections may be incorporated by reference** — some filers don't contain every Part III section directly in the 10-K body, instead incorporating portions from their proxy statement. Absence of a section in the retrieved filing doesn't always mean the information doesn't exist elsewhere in the company's reporting documents.
5. **Multi-turn contextualization** — using previous conversation history to rewrite follow-up questions is planned for a future iteration. The current validated graph focuses on Retrieve → Grade → Rewrite/Retry → Generate → Verify.

## Security

API credentials are loaded through environment variables. The following should never be committed: `.env`, API keys, Pinecone credentials, Groq credentials, or any private tokens. For hosted deployments, configure credentials using the platform's secret/environment-variable management rather than storing them in source code.

## Roadmap

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
- [x] Gradio interface
- [ ] Render deployment
- [ ] Multi-turn question contextualization
- [ ] Claim-level citation alignment
- [ ] Expanded evaluation benchmark
- [ ] Additional financial institutions and filings

## What Makes This Project Different?

FilingsIQ is intentionally built around measured retrieval performance and failure analysis, rather than only demonstrating that an LLM can answer questions from documents.

Baseline → Vector Retrieval → Hybrid Retrieval → Reranking → Generation → Citation Verification

The goal is not to claim the system is perfect. The goal is to build a transparent, testable retrieval system where retrieval quality is measured, failures are visible, and unsupported answers are treated as a system failure rather than a successful response.

## License

MIT License

## Author

**Vishal Kumar Singh**

**IIT Madras**

Built as an applied research and engineering project exploring Retrieval-Augmented Generation, Agentic AI, Information Retrieval, Financial NLP, LLM evaluation, LangGraph workflows, and evidence-grounded AI systems.