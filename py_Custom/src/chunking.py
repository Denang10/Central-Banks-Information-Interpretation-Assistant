import json
import re
from pathlib import Path

from src.schemas import Chunk


PAGES_PATH = Path("data/processed/pages.jsonl")
CHUNKS_PATH = Path("data/processed/chunks.jsonl")

CHUNK_WORDS = 500
OVERLAP_WORDS = 75


def normalise_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_into_chunks(text: str) -> list[str]:
    words = normalise_text(text).split()

    if not words:
        return []

    step = CHUNK_WORDS - OVERLAP_WORDS
    chunks = []

    for start in range(0, len(words), step):
        chunk_words = words[start : start + CHUNK_WORDS]

        if len(chunk_words) < 50:
            continue

        chunks.append(" ".join(chunk_words))

        if start + CHUNK_WORDS >= len(words):
            break

    return chunks


def load_pages() -> list[dict]:
    with PAGES_PATH.open(encoding="utf-8") as file:
        return [json.loads(line) for line in file]


def main() -> None:
    CHUNKS_PATH.parent.mkdir(parents=True, exist_ok=True)

    chunks_written = 0

    with CHUNKS_PATH.open("w", encoding="utf-8") as output_file:
        for page in load_pages():
            page_chunks = split_into_chunks(page["text"])

            for chunk_number, text in enumerate(page_chunks, start=1):
                chunk = Chunk(
                    chunk_id=(
                        f'{page["document_id"]}'
                        f'_p{page["page_number"]}'
                        f'_c{chunk_number}'
                    ),
                    document_id=page["document_id"],
                    source_file=page["source_file"],
                    page_number=page["page_number"],
                    text=text,
                    metadata={
                        "chunk_words": len(text.split()),
                    },
                )

                output_file.write(
                    json.dumps(chunk.to_dict(), ensure_ascii=False) + "\n"
                )
                chunks_written += 1

    print(f"Wrote {chunks_written} chunks to {CHUNKS_PATH}")


if __name__ == "__main__":
    main()