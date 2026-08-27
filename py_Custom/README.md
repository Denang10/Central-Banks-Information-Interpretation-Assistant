# Custom RAG Implementation

This directory contains a transparent Python implementation of the retrieval-augmented generation (RAG) pipeline used by the **Central Bank Information Interpretation Assistant**.

Unlike the managed implementation in [`../py_azure/`](../py_azure/), this version explicitly implements the core RAG stages:

```text
PDF source documents
    -> text extraction
    -> page-level records
    -> overlapping text chunks
    -> local embeddings
    -> FAISS vector index + BM25 keyword index
    -> hybrid retrieval with Reciprocal Rank Fusion
    -> Azure-hosted LLM generation using retrieved evidence only
    -> source-aware answer
```

The purpose is to understand and demonstrate the layers abstracted by Microsoft Foundry IQ: document processing, chunking, embedding, indexing, retrieval, prompt construction, citation handling, and evaluation.

> **Important:** This is an educational and technical demonstration using public ECB and Central Bank of Ireland sources. It is not financial, legal, lending, investment, or regulatory advice.

---

## Architecture

```text
ECB / CBI narrative PDFs
        |
        v
PyMuPDF page-level text extraction
        |
        v
Overlapping word-based chunks with source metadata
        |
        +------------------------------+
        |                              |
        v                              v
Sentence Transformer embeddings       BM25 keyword tokenisation
        |                              |
        v                              v
FAISS vector index                    BM25 lexical index
        |                              |
        +---------- Hybrid retrieval --+
                         |
                         v
            Reciprocal Rank Fusion (RRF)
                         |
                         v
            Top retrieved evidence chunks
                         |
                         v
        Azure OpenAI / Foundry model deployment
                         |
                         v
         Grounded answer with document/page citations
```

---

## Project Structure

```text
py_custom/
├── data/
│   ├── raw/                         # Source PDFs; not committed
│   └── processed/
│       ├── pages.jsonl              # Extracted page-level text
│       └── chunks.jsonl             # Source-aware text chunks
│
├── artifacts/                       # Generated local indexes; not committed
│   ├── bm25.pkl
│   ├── chunks.json
│   ├── config.json
│   └── faiss.index
│
├── src/
│   ├── __init__.py
│   ├── schemas.py                   # Chunk data contract
│   ├── ingest.py                    # PDF parsing
│   ├── chunking.py                  # Overlapping chunk generation
│   ├── index.py                     # Embedding and index creation
│   ├── retrieve.py                  # Hybrid search and RRF
│   └── generate.py                  # Grounded LLM answer generation
│
├── tests/
│   ├── retrieval_baseline.md
│   └── generation_baseline.md
│
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## Prerequisites

- Python 3.10 or later.
- [`uv`](https://docs.astral.sh/uv/) for Python environment and dependency management.
- Azure OpenAI / Microsoft Foundry model deployment access for the generation stage.
- An Azure OpenAI endpoint, API key, and deployment name.
- Narrative ECB and CBI PDFs downloaded into `data/raw/`.

The retrieval pipeline works locally. Azure is only used for the optional language-model generation stage.

---

## Setup

### 1. Create the environment

From this directory:

```bash
uv venv
```

Install dependencies:

```bash
uv add pymupdf sentence-transformers faiss-cpu numpy pandas \
    pydantic python-dotenv tqdm rank-bm25 openai
```

### 2. Create local folders

```bash
mkdir -p data/raw data/processed artifacts eval
```

On Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force data/raw, data/processed, artifacts, eval
```

### 3. Add source PDFs

Place a small narrative corpus in `data/raw/` first:

```text
ecb_2026-06-11_decision-statement-17.pdf
ecb_2026-07-23_decision-statement-18.pdf
cbi_2026_06_retail_interest_rates-4.pdf
cbi_2026_07_bank_lending_survey_comments-5.pdf
cbi_2026_06_money_and_banking_statistics-20.pdf
```

Starting with five documents makes it easier to inspect retrieval quality before introducing more sources, methodology notes, CSV files, or large Excel workbooks.

---

## Configuration

Create a `.env` file in `py_custom/`.

```text
AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE-NAME.openai.azure.com/
AZURE_OPENAI_API_KEY=YOUR_SECRET_KEY
AZURE_OPENAI_DEPLOYMENT=YOUR_DEPLOYMENT_NAME
```

Important:

- `AZURE_OPENAI_ENDPOINT` should be the Azure OpenAI **resource root**, not a full `/chat/completions` or `/openai/deployments/...` URL.
- `AZURE_OPENAI_DEPLOYMENT` is the deployment name configured in Foundry, which may differ from the underlying base-model name.
- Never commit `.env`, API keys, endpoints containing sensitive information, or conversation data.

The OpenAI Python SDK supports Azure-hosted chat completion calls, where the `model` argument identifies the Azure deployment name. [Microsoft Foundry documentation](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/chatgpt)

Copy the example template where needed:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

---

## Step 1 — Extract PDF Text

Run:

```bash
uv run python -m src.ingest
```

This reads each PDF in `data/raw/` and writes page-level records to:

```text
data/processed/pages.jsonl
```

Each record retains:

- `document_id`
- `source_file`
- `page_number`
- extracted `text`

PyMuPDF is used to extract text from each PDF page with `page.get_text("text")`. Page-level extraction is important because it preserves a source location for later retrieval and citation. [PyMuPDF documentation](https://pymupdf.readthedocs.io/en/latest/recipes-text.html)

Inspect the first records:

```bash
head -n 2 data/processed/pages.jsonl
```

---

## Step 2 — Create Source-Aware Chunks

Run:

```bash
uv run python -m src.chunking
```

This converts page-level text into overlapping word-based chunks and writes:

```text
data/processed/chunks.jsonl
```

Initial settings:

```text
Chunk size: 500 words
Overlap: 75 words
```

Each chunk retains source provenance:

```json
{
  "chunk_id": "ecb_2026-07-23_decision-statement_p1_c1",
  "document_id": "ecb_2026-07-23_decision-statement",
  "source_file": "ecb_2026-07-23_decision-statement-18.pdf",
  "page_number": 1,
  "text": "..."
}
```

Source-aware metadata is necessary because an answer should be able to cite the retrieved document and page rather than merely asserting a fact.

---

## Step 3 — Build Local Indexes

Run:

```bash
uv run python -m src.index
```

This performs two forms of indexing:

### Dense semantic index

`SentenceTransformer` converts each chunk into an embedding using:

```text
BAAI/bge-small-en-v1.5
```

Document embeddings are normalised and stored in a FAISS `IndexFlatIP` index.

Using normalised embeddings with inner-product search makes the search behave as cosine-similarity matching.

### Lexical keyword index

The same chunks are tokenised and indexed with `BM25Okapi`.

BM25 is useful for exact terms that matter in this domain, such as:

```text
deposit facility
main refinancing operations
fixed-rate mortgage
non-financial corporations
credit standards
```

Generated artifacts:

```text
artifacts/
├── faiss.index
├── bm25.pkl
├── chunks.json
└── config.json
```

Sentence Transformers provides document- and query-specific encoding methods for asymmetric retrieval, while FAISS supports efficient dense-vector similarity search. [Sentence Transformers documentation](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html)

---

## Step 4 — Run Hybrid Retrieval

Run a retrieval query:

```bash
uv run python -m src.retrieve \
  --query "What was the ECB's latest monetary policy decision?"
```

The retriever performs:

```text
Query
    -> Dense FAISS retrieval
    -> BM25 keyword retrieval
    -> Reciprocal Rank Fusion
    -> Top source-aware evidence chunks
```

It retrieves candidate chunks from both indexes, then combines the rankings using **Reciprocal Rank Fusion (RRF)**.

RRF combines rank positions rather than comparing raw FAISS and BM25 scores directly, because those scores have different meanings and scales.

Try the baseline retrieval/generation tests:

```bash
uv run python -m src.retrieve \
  --query "What was the ECB's latest monetary policy decision?"
```

```bash
uv run python -m src.retrieve \
  --query "What was the new fixed-rate mortgage interest rate in Ireland?"
```

```bash
uv run python -m src.retrieve \
  --query "Did Irish banks tighten mortgage credit standards in Q2 2026?"
```

Record the results in:

```text
tests/retrieval_baseline.md
```

---

## Step 5 — Generate a Grounded Answer

Run:

```bash
uv run python -m src.generate \
  --question "What was the ECB's latest monetary policy decision?"
```

`src/generate.py`:

1. Calls the local hybrid retriever.
2. Builds a context block from the top retrieved chunks.
3. Sends the question and evidence to the Azure-hosted model.
4. Instructs the model to rely only on supplied evidence.
5. Requires citations in this format:


> Some deployed Foundry models do not accept a custom `temperature` value. The current implementation omits this parameter for compatibility. Grounding comes from retrieval, context restrictions, source citations, and evaluation—not from a sampling setting alone.

Record outputs in:

```text
tests/generation_baseline.md
```

---

## Evaluation

The project evaluates retrieval and generation separately.

### Retrieval evaluation

For each query, record:

- Expected source document.
- Top retrieved document and page.
- Pass/fail.
- Notes on whether the retrieved passage directly answers the question.

### Generation evaluation

For each response, assess:

- **Groundedness:** Does each material claim appear in the retrieved evidence?
- **Citation accuracy:** Does each citation identify the correct document/page?
- **Completeness:** Does the answer address the question?
- **Boundary adherence:** Does it avoid unsupported predictions, advice, and claims?

---

## Known Limitations

- The initial PDF parser extracts plain text. Tables, charts, headers, and reading order may not always be represented perfectly.
- The first chunking strategy is page-based and word-based; it does not yet split intelligently on headings, paragraphs, or tables.
- The corpus is small and intentionally limited. Results should not be generalised beyond its source documents.
- The system does not yet include a reranker, metadata filters, query rewriting, automated citation validation, or automated evaluation metrics.
- CSV/XLSX calculation support is not included in this initial custom RAG phase. It will be added as a separate structured-data tool rather than forcing raw tables into text retrieval.
- Azure is still required for answer generation in the current version, although ingestion, indexing, and retrieval run locally.