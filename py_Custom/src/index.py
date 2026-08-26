import json
import pickle
import re
from pathlib import Path

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


CHUNKS_PATH = Path("data/processed/chunks.jsonl")
ARTIFACTS_DIR = Path("artifacts")

MODEL_NAME = "BAAI/bge-small-en-v1.5"


def tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


def load_chunks() -> list[dict]:
    with CHUNKS_PATH.open(encoding="utf-8") as file:
        return [json.loads(line) for line in file]


def main() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    chunks = load_chunks()
    texts = [chunk["text"] for chunk in chunks]

    print(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    print(f"Embedding {len(texts)} chunks")
    embeddings = model.encode_document(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True,
    ).astype("float32")

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, str(ARTIFACTS_DIR / "faiss.index"))

    with (ARTIFACTS_DIR / "chunks.json").open("w", encoding="utf-8") as file:
        json.dump(chunks, file, ensure_ascii=False, indent=2)

    bm25 = BM25Okapi([tokenize(text) for text in texts])

    with (ARTIFACTS_DIR / "bm25.pkl").open("wb") as file:
        pickle.dump(bm25, file)

    with (ARTIFACTS_DIR / "config.json").open("w", encoding="utf-8") as file:
        json.dump(
            {
                "embedding_model": MODEL_NAME,
                "chunk_count": len(chunks),
                "chunk_words": 500,
                "overlap_words": 75,
                "vector_index": "FAISS IndexFlatIP",
                "lexical_index": "BM25Okapi",
            },
            file,
            indent=2,
        )

    print(f"Saved index artifacts to {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()