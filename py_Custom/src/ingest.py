import json
from pathlib import Path

import pymupdf


RAW_DIR = Path("data/raw")
OUTPUT_PATH = Path("data/processed/pages.jsonl")


def extract_pdf_pages(pdf_path: Path) -> list[dict]:
    document_id = pdf_path.stem
    pages = []

    with pymupdf.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()

            if text:
                pages.append(
                    {
                        "document_id": document_id,
                        "source_file": pdf_path.name,
                        "page_number": page_number,
                        "text": text,
                    }
                )

    return pages


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    all_pages = []
    for pdf_path in sorted(RAW_DIR.glob("*.pdf")):
        pages = extract_pdf_pages(pdf_path)
        print(f"{pdf_path.name}: extracted {len(pages)} pages")
        all_pages.extend(pages)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        for page in all_pages:
            file.write(json.dumps(page, ensure_ascii=False) + "\n")

    print(f"Wrote {len(all_pages)} pages to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()