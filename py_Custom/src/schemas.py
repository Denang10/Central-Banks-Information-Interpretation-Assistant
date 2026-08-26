from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Chunk:
    chunk_id: str
    document_id: str
    source_file: str
    page_number: int
    text: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)