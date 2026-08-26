import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AzureOpenAI

from src.retrieve import HybridRetriever


load_dotenv()

SYSTEM_PROMPT = """\
You are the Central Bank Information Interpretation Assistant.

Answer using only the supplied retrieved evidence.

Rules:
- Do not use outside knowledge.
- Cite every material factual claim using this exact format:
  [document_id, p. page_number].
- State publication dates or reporting periods only when present in the evidence.
- Separate factual evidence from interpretation.
- Do not make institution-specific forecasts, pricing recommendations,
  lending decisions, legal conclusions, or financial advice.
- If the evidence does not support an answer, say:
  "The retrieved sources do not provide enough evidence to answer this."
"""


def build_context(results: list[dict]) -> str:
    blocks = []

    for result in results:
        blocks.append(
            f"""SOURCE: {result["document_id"]}
PAGE: {result["page_number"]}
TEXT:
{result["text"]}"""
        )

    return "\n\n---\n\n".join(blocks)


def get_client() -> AzureOpenAI:
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
    api_key = os.environ["AZURE_OPENAI_API_KEY"]

    return AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version="2024-10-21",
    )


def answer_question(question: str) -> str:
    retriever = HybridRetriever()
    results = retriever.search(question, candidate_k=8, final_k=5)

    context = build_context(results)

    user_prompt = f"""\
Question:
{question}

Retrieved evidence:
{context}

Write a concise answer using only the retrieved evidence.
"""

    client = get_client()

    response = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content or ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", required=True)
    args = parser.parse_args()

    print(answer_question(args.question))


if __name__ == "__main__":
    main()