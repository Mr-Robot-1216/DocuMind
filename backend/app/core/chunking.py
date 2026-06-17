"""Recursive text splitter.

Splits text into overlapping chunks, preferring to break on paragraph,
line, sentence, then word boundaries before falling back to a hard
character split. Sizes are measured in characters rather than tokens —
this keeps the splitter dependency-free (no tokenizer needed) while still
landing comfortably inside nomic-embed-text's context window for the
default chunk size.
"""

DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " "]


def chunk_text(
    text: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
    separators: list[str] | None = None,
) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    pieces = _split_recursive(text, separators or DEFAULT_SEPARATORS, chunk_size)
    return _merge_pieces(pieces, chunk_size, chunk_overlap)


def _split_recursive(text: str, separators: list[str], chunk_size: int) -> list[str]:
    if not separators:
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    separator, *rest = separators
    pieces = []
    for part in text.split(separator):
        part = part.strip()
        if not part:
            continue
        if len(part) > chunk_size:
            pieces.extend(_split_recursive(part, rest, chunk_size))
        else:
            pieces.append(part)
    return pieces


def _merge_pieces(pieces: list[str], chunk_size: int, chunk_overlap: int) -> list[str]:
    chunks: list[str] = []
    current = ""

    for piece in pieces:
        candidate = f"{current} {piece}".strip() if current else piece
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)

        if chunk_overlap > 0 and current:
            overlap = current[-chunk_overlap:]
            current = f"{overlap} {piece}".strip()
            if len(current) > chunk_size:
                current = piece
        else:
            current = piece

    if current:
        chunks.append(current)

    return chunks
