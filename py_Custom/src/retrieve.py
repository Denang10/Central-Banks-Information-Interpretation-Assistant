import argparse
import json
import pickle
import re
from pathlib import Path

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


ARTIFACTS_DIR = Path("artifacts")
RRF_K = 60


def tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


def reciprocal_rank_fusion(
    ranked_lists: list[list[int]],
    rrf_k: int = RRF_K,
) -> list[tuple[int, float]]:
    scores: dict[int, float] = {}

    for ranked_list in ranked_lists:
        for rank, chunk_index in enumerate(ranked_list, start=1):
            scores[chunk_index] = scores.get(chunk_index, 0.0) + (
                1.0 / (rrf_k + rank)
            )

    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


class HybridRetriever:
    def __init__(self) -> None:
        with (ARTIFACTS_DIR / "config.json").open(encoding="utf-8") as file:
            config = json.load(file)

        with (ARTIFACTS_DIR / "chunks.json").open(encoding="utf-8") as file:
            self.chunks = json.load(file)

        with (ARTIFACTS_DIR / "bm25.pkl").open("rb") as file:
            self.bm25: BM25Okapi = pickle.load(file)

        self.model = SentenceTransformer(config["embedding_model"])
        self.faiss_index = faiss.read_index(
            str(ARTIFACTS_DIR / "faiss.index")
        )

    def dense_search(self, query: str, top_k: int) -> list[int]:
        query_embedding = self.model.encode_query(
            [query],
            normalize_embeddings=True,
        ).astype("float32")

        _, indices = self.faiss_index.search(query_embedding, top_k)

        return [int(index) for index in indices[0] if index != -1]

    def bm25_search(self, query: str, top_k: int) -> list[int]:
        scores = self.bm25.get_scores(tokenize(query))
        ranked_indices = np.argsort(scores)[::-1][:top_k]

        return [int(index) for index in ranked_indices]

    def search(
        self,
        query: str,
        candidate_k: int = 8,
        final_k: int = 5,
    ) -> list[dict]:
        dense_indices = self.dense_search(query, candidate_k)
        bm25_indices = self.bm25_search(query, candidate_k)

        fused = reciprocal_rank_fusion([dense_indices, bm25_indices])

        results = []
        for chunk_index, rrf_score in fused[:final_k]:
            chunk = self.chunks[chunk_index].copy()
            chunk["rrf_score"] = round(rrf_score, 6)
            results.append(chunk)

        return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--candidate-k", type=int, default=8)
    parser.add_argument("--final-k", type=int, default=5)
    args = parser.parse_args()

    retriever = HybridRetriever()
    results = retriever.search(
        query=args.query,
        candidate_k=args.candidate_k,
        final_k=args.final_k,
    )

    print(f"\nQuery: {args.query}\n")

    for rank, result in enumerate(results, start=1):
        print(f"[{rank}] {result['document_id']} — page {result['page_number']}")
        print(f"RRF score: {result['rrf_score']}")
        print(result["text"][:500].replace("\n", " "))
        print("-" * 90)


if __name__ == "__main__":
    main()