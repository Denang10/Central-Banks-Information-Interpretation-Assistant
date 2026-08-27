# Azure / Microsoft Foundry Implementation

This directory contains the managed Azure implementation of the **Central Bank Information Interpretation Assistant**.

It uses Microsoft Foundry Agent Service, **Foundry IQ**, Azure Blob Storage, and Azure AI Search to create a retrieval-augmented agent over official European Central Bank (ECB) and Central Bank of Ireland (CBI) publications. It also uses **Code Interpreter** for calculations and charts from structured banking datasets.

The purpose of this implementation is to demonstrate a cloud-native RAG solution quickly, while retaining traceability through source-grounded answers, citations, structured agent instructions, safety tests, and documented configuration.

> **Important:** This is a technical demonstration using public information. It is not affiliated with the ECB, Central Bank of Ireland, any regulatory banks, or any other financial institution. It must not be used as financial, regulatory, lending, investment, or legal advice.

---

## What This Implementation Does

The agent answers research-style questions using two complementary tools:

| Tool | Purpose | Suitable data |
|---|---|---|
| **Foundry IQ knowledge base** | Retrieves relevant source passages and supports grounded, cited answers. | Narrative PDFs, official releases, explanatory notes, policy statements. |
| **Code Interpreter** | Runs Python in a sandbox to calculate values, compare dates, and generate charts. | CSV and XLSX time-series datasets. |

Foundry IQ is backed by Azure AI Search. For indexed knowledge sources, Azure handles the ingestion pipeline, including chunking, vectorisation, metadata extraction, and indexing. [Microsoft documentation](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/foundry-iq-faq)

---

## Architecture

```text
                   Official public sources
          ECB monetary-policy decisions and data
          CBI statistics, releases, and survey results
                              |
                              v
                  Azure Blob Storage container
                   /narrative   /structured
                              |
            +-----------------+------------------+
            |                                    |
            v                                    v
     Foundry IQ knowledge base            Code Interpreter
      + Azure AI Search index              attached CSV/XLSX
            |                                    |
            v                                    v
       Grounded retrieval                  Python calculations
       and source citations                and visualisations
            \                                    /
             \                                  /
              v                                v
                  Microsoft Foundry Agent
                              |
                              v
         Structured, cited central-bank briefing
```

---

## Prerequisites

Before starting, ensure you have:

- An Azure subscription with permission to create or use:
  - A Microsoft Foundry project.
  - Azure Blob Storage.
  - Azure AI Search.
- A deployed model available to the Foundry project.
- A local development environment with:
  - Python 3.10 or newer.
  - Azure CLI.
  - VS Code.
  - The Microsoft Foundry Toolkit extension, if using the VS Code integration.
- Public ECB and CBI documents prepared for ingestion.
- A `.env` file containing environment-specific values. Do not commit this file.

---

## Part 1 — Foundry IQ Knowledge Base

### 1. Create a Foundry agent

In Microsoft Foundry, create an agent and select an available chat model.

Give the agent a clear name, such as:

```text
central-bank-information-assistant
```

Use focused system instructions. The agent should be grounded in the connected knowledge base, distinguish evidence from interpretation, and refuse to make unsupported institution-specific claims.

Example instructions:

```text
You are the Central Bank Information Interpretation Assistant.

Use the connected knowledge base for factual claims about ECB monetary-policy
decisions and Irish banking statistics. Cite retrieved sources for every
material factual claim.

Always state:
- the publication date of the source;
- the statistical reporting period, where relevant;
- whether a value is a rate, volume, stock, flow, survey response, or
  qualitative interpretation.

Separate “Evidence from sources” from “Interpretation”.

Do not invent institution-specific impacts, forecasts, pricing decisions, or
recommendations for AIB or any other bank. Do not provide financial, lending,
investment, legal, or regulatory advice.

If the retrieved sources do not support the answer, say so clearly.
```

### 2. Create or connect Azure resources

1. Create an Azure Storage account and an Azure Blob Storage container.

2. Upload the narrative source documents first. This keeps retrieval focused while the knowledge base is being tested.

3. Recommended initial narrative corpus:

        - ECB monetary-policy decision statements.
        - CBI Retail Interest Rates release.
        - CBI Bank Lending Survey release.
        - CBI Money and Banking Statistics release.
        - CBI methodology notes for private-sector credit/deposits.
        - CBI methodology notes for mortgage arrears and repossessions.

![Azure Blob Storage container and uploaded source documents](assets/image.png)

### 3. Create a Foundry IQ knowledge base

In Foundry, open the **Knowledge** area and create or connect an Azure AI Search service that supports agentic retrieval.

Then:

1. Create a knowledge source using the Azure Blob Storage container.
2. Configure the embedding/vectorisation model.
3. Create a knowledge base and add the knowledge source.
4. Add a useful knowledge-base description.
5. Configure retrieval and answer instructions.
6. Connect the knowledge base to the agent.

![Foundry IQ knowledge base configuration](assets/image-2.png)

### 4. Configure secure access

Foundry IQ connects the agent to the knowledge base through Azure AI Search. For the purposes of this demo, this was accomplished through the use of api_keys belonging to the AI Search artifact. Production settings may require managed identity roles to be configured instead.

### 5. Connect tools and test in the playground

Attach the Foundry IQ knowledge base to the agent. Add other tools only where they are needed; in this project, Code Interpreter is used for analysis of attached structured datasets.

Use the Foundry playground to test retrieval quality, citations, and refusal behaviour before writing any client code.

![Foundry playground with the connected agent and tools](assets/image-1.png)

Suggested initial tests:

```text
What did the ECB decide at its latest monetary-policy meeting, and how did
this differ from the previous decision?

What was the latest weighted-average rate on new Irish fixed-rate mortgage
agreements, and which reporting period does the figure cover?

What did Irish banks report about mortgage credit standards and mortgage
demand in Q2 2026?

What source supports the claim that AIB will reduce deposit rates next month?
```

The final question is intentionally unsupported. A good answer should say that the supplied corpus contains no evidence for the claim rather than inventing a source.

---

## Part 2 — Code Interpreter

### Why Use Code Interpreter?

RAG is appropriate for retrieving and explaining narrative documents. It is less reliable for arithmetic over large time-series files, date filtering, or chart production.

Code Interpreter lets the agent write and run Python in a sandboxed environment. It can analyse attached files, calculate changes, create plots, and return generated files such as charts. [Microsoft documentation](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/code-interpreter)

### Attach Structured Data

Code Interpreter cannot automatically read every file held in the Foundry IQ Blob source. Attach the relevant CSV or XLSX file directly to the agent or conversation when you want it to perform an analysis.

Suggested initial files:

```text
cbi_2026-08-12_retail_interest_rates_deposits_outstanding.csv
cbi_2026-08-12_retail_interest_rates_loans_deposits_newbusiness.csv
cbi_2026-08-12_retail_interest_rates_loans_outstanding.csv
cbi_2026-08-12_retail_interest_rates_renegotiated_loans.csv
cbi_2026-08-17_retail_interest_rates_mortgage.csv
ecb_2026-07-31_corporate_interest_rates.csv
```

### Add Tool-Use Instructions

Add the following to the agent instructions:

```text
For questions requiring calculations, date comparisons, trends, percentage
changes, rankings, filtering, or charts, use Code Interpreter when the
necessary attached structured-data file is available.

Do not claim to have calculated a value unless Code Interpreter was used.

If the required dataset is not attached or cannot be located, state this
clearly and answer only from retrieved narrative sources.
```

Example prompt:

```text
Using the attached mortgage-rate CSV, calculate the three-month change in the
weighted-average rate on new fixed-rate house-purchase loans to June 2026.
Show the dates and values used, then create a line chart.
```

---

## Part 3 — VS Code Client Integration

The Foundry playground is useful for rapid experimentation. A Python client makes the implementation reproducible and provides a path to integrate the agent into a small web application, API, or evaluation script.

### 1. Create a local environment

```bash
python -m venv .venv
```

Activate it:

```bash
# macOS/Linux
source .venv/bin/activate
```

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install the packages required by the implementation:

```bash
pip install -r requirements.txt
```

### 2. Authenticate locally

Sign in with the Azure CLI:

```bash
az login
```

Confirm that the expected subscription is active:

```bash
az account show
```

Use Azure identity-based authentication where possible. Do not hard-code secrets or commit credentials.

### 3. Configure environment variables

Create a local `.env` file from the provided example:

```bash
cp .env.example .env
```

Example `.env.example`:

```text
AZURE_AI_PROJECT_ENDPOINT=
AZURE_AI_AGENT_ID=
AZURE_SUBSCRIPTION_ID=
```

Depending on the SDK and implementation, your client may use a Foundry project endpoint, an agent ID, a model deployment name, or a connection string. Keep only placeholders in `.env.example`; do not commit real values.

### 4. Maintain conversational context

The client creates or reuses a conversation/thread identifier so follow-up questions retain prior context.

Conceptually:

```text
Create or load conversation ID
        |
        v
Send user message
        |
        v
Run agent
        |
        v
Poll for completion
        |
        v
Render final response, citations, and generated files
```

Keep the conversation ID in memory for a short demo, persist it only when needed, and do not commit user conversation data.

### 5. Run the client

The exact command depends on the code in this directory. A typical pattern is:

```bash
python agent_client.py
```

Example interaction:

```text
Question: Summarise the latest Irish fixed-rate mortgage statistics.

Question: Compare this with the latest ECB policy decision.

Question: Create a chart of the latest available fixed-rate mortgage series.
```

---

## Testing

### Grounding Tests

Verify that the agent:

- Uses the knowledge base for ECB and CBI factual claims.
- Returns usable citations or source references.
- Identifies the correct source publication date.
- Distinguishes the release date from the period described by a statistic.
- States when evidence is unavailable.

### Code Interpreter Tests

Verify that the agent:

- Invokes Code Interpreter for calculations or chart requests.
- Identifies the attached structured-data file it used.
- Shows the dates and values used in calculations.
- Produces a chart that is consistent with the selected series.
- Does not claim calculations when a relevant file is unavailable.

### Safety and Red-Team Tests

Test prompts that attempt to induce:

- AIB-specific pricing or net-interest-margin predictions.
- Personalised mortgage advice.
- Credit approval/decline recommendations.
- Fabricated sources or false ECB claims.
- Prompt-instruction overrides.
- Discriminatory lending or borrower-profiling requests.
- False regulatory authority or deceptive financial communication.

Record the prompt, expected behaviour, actual response, result, and remediation in the repository evaluation materials.

---

## Limitations and Cleanup

This managed implementation relies on active Azure resources. Once the demo is complete, delete the resources to avoid ongoing cost.

Before cleanup, retain:

- Screenshots of the Blob source, Foundry IQ configuration, agent setup, and grounded responses.
- The agent and knowledge-base instructions.
- A source catalogue in `data/sources.csv`.
- Test prompts and evaluation results.
- This implementation documentation.

The companion [`../py_custom/`](../py_custom/) directory will implement the same use case with a local, transparent RAG pipeline so that the repository remains reproducible after Azure resources are deprovisioned.

---

## Related Documentation

- [Root README](../README.md)
- [Custom RAG implementation](../py_custom/README.md)
- [Microsoft Foundry IQ documentation](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/what-is-foundry-iq)
- [Connect Foundry agents to Foundry IQ knowledge bases](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/foundry-iq-connect)
- [Microsoft Foundry Code Interpreter](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/code-interpreter)