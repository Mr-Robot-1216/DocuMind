from dataclasses import dataclass


@dataclass
class ChunkRecord:
    chunk_id: str
    collection_id: str
    document_name: str
    page: int | str | None
    chunk_index: int
    text: str
    embedding: list[float] | None = None


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_name: str
    page: int | str | None
    chunk_index: int
    text: str
    score: float


def page_to_str(page: int | str | None) -> str:
    return "" if page is None else str(page)


def page_from_str(value: str) -> int | str | None:
    if value == "":
        return None
    if value.isdigit():
        return int(value)
    return value
