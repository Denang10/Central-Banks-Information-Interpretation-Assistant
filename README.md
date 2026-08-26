# Central Bank Information Interpretation Assistant

A retrieval-augmented AI assistant for interpreting public monetary-policy decisions and Irish banking statistics.

The project explores how an AI assistant can turn official publications from the **European Central Bank (ECB)** and the **Central Bank of Ireland (CBI)** into concise, traceable briefings. It is designed as a portfolio project demonstrating both managed Azure AI capabilities and a transparent, custom-built RAG pipeline.

> **Important:** This is an educational and technical demonstration. It is not affiliated with the ECB, the Central Bank of Ireland, any regulatory bank, or any other financial institution. It does not provide financial, legal, lending, investment, or regulatory advice.

## Problem

Central-bank and banking-statistics publications are authoritative but spread across decision statements, statistical releases, survey commentary, PDFs, spreadsheets, and historical time-series files.

A banking, treasury, risk, or analytics user may want to ask questions such as:

- What changed in the ECB’s most recent policy decision?
- How have Irish new mortgage rates and deposit rates changed?
- What did Irish banks report about mortgage demand and credit standards?
- What do the latest household-credit, deposit, and business-lending figures show?
- Which source document and reporting period supports a particular claim?

This repository investigates how RAG can provide answers grounded in those sources, while clearly separating **reported evidence** from **high-level interpretation**.

## Approaches Compared

The repository contains three implementations of the same use case.

| Approach | Location | Purpose |
|---|---|---|
| **Foundry Solution Pipeline** | `py_azure/` | Uses Microsoft Foundry IQ and Azure AI Search as a managed knowledge layer over official ECB and CBI documents. Tests agent out in Foundry Model Playground. |
| **Foundry Agent with VSCode** | `py_azure/` | Makes use of the same Foundry knowledge base as above but contains custom code to be run in VSCode. |
| **Custom RAG pipeline** | `py_custom/` | Rebuilds ingestion, chunking, embedding, indexing, retrieval, and grounded generation explicitly in Python. |

The goal is not to treat managed and custom RAG as competing approaches. Instead, the project compares the trade-off between:

- **Managed RAG:** rapid implementation, integrated knowledge management, citations, and Azure-native tooling.
- **Custom RAG:** greater transparency, local reproducibility, control over chunking/retrieval, and easier experimentation with evaluation methods.

## Data Sources

The corpus uses publicly available official material from:

- [European Central Bank](https://www.ecb.europa.eu/)
  - Monetary-policy decision statements
  - Key policy-rate information
  - Corporate and monetary-financial-institution interest-rate data
- [Central Bank of Ireland](https://www.centralbank.ie/)
  - Retail interest-rate releases and time series
  - Mortgage lending and arrears statistics
  - Household, SME, and business credit data
  - Money and banking statistics
  - Bank Lending Survey results
  - Methodology and explanatory notes

Source material is public, but large raw documents and datasets are not necessarily committed to this repository. See [`data/sources.csv`](data/sources.csv) for provenance and download references.

## Architecture

```text
Official ECB and CBI publications
        |
        |-- Narrative PDFs and explanatory notes
        |        -> Azure Blob Storage
        |        -> Foundry IQ / Azure AI Search
        |        -> Foundry Agent
        |        -> Grounded, cited responses
        |
        |-- CSV / XLSX time-series data
                 -> Foundry Code Interpreter
                 -> Calculations and visualisations
                 -> Structured, source-aware answers
```

The custom implementation reproduces the central RAG stages locally:

```text
Raw documents
    -> parsing and normalisation
    -> chunking and metadata enrichment
    -> embedding generation
    -> vector and keyword retrieval
    -> optional reranking
    -> answer generation with source citations
```


## Evaluation and Safety

The project includes an evaluation set covering:

- Factual retrieval of ECB policy decisions.
- Temporal reasoning across releases.
- Source attribution and reporting-period accuracy.
- Calculations and charts using structured datasets.
- Out-of-scope and unsupported questions.
- Red-team prompts covering prompt injection, fabricated-source pressure, financial-advice requests, discriminatory lending requests, and institution-specific forecasting.

A response is considered successful when it is relevant, grounded in the source corpus, correctly qualified, and transparent about uncertainty.

## Repository Structure

```text
.
├── data/
│   ├── sources.csv                 # Source catalogue and provenance
│   └── raw/                        # Not committed; see download instructions
│
├── py_azure/
│   ├── README.md                   # Foundry IQ and Code Interpreter implementation
│   ├── docs/
│   └── ...
│
├── py_custom/
│   ├── README.md                   # Custom Python RAG implementation
│   ├── src/
│   ├── tests/
│   └── ...
│
├── eval/
│   ├── questions.jsonl
│   ├── red_team_prompts.md
│   └── results.md
│
├── docs/
│   ├── architecture.md
│   ├── screenshots/
│   └── ...
│
├── .env.example
├── LICENSE
└── README.md
```


## Getting Started

Each implementation has its own setup instructions:

- Managed Azure/Foundry implementation: [`py_azure/README.md`](py_azure/README.md)
- Custom local RAG implementation: [`py_custom/README.md`](py_custom/README.md)

To reproduce the project, begin by reviewing the source catalogue:

```bash
cat data/sources.csv
```

Then follow the instructions for the implementation you want to run.

## Limitations

- The corpus is intentionally limited and may not contain the latest release after the project’s collection date.
- Publication dates and reporting periods are different; statistical releases can report data from an earlier month or quarter.
- RAG improves source grounding but does not guarantee factual correctness.
- The assistant cannot infer confidential, institution-specific information from public aggregate releases.
- Public statistical releases should not be treated as a substitute for regulatory, legal, credit, treasury, or financial advice.

## Licence and Attribution

Source documents remain the property of their respective publishers, including the ECB and Central Bank of Ireland. This repository is intended to contain code, metadata, evaluation materials, and links to public sources rather than redistributing copyrighted or large source datasets.
