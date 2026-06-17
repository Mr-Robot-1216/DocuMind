from app.core.chunking import chunk_text


def test_empty_text_returns_no_chunks() -> None:
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_short_text_returns_single_chunk() -> None:
    text = "This is a short paragraph."
    assert chunk_text(text, chunk_size=800, chunk_overlap=100) == [text]


def test_long_text_splits_on_paragraph_boundaries() -> None:
    para_a = "Sentence one. Sentence two. Sentence three." * 3
    para_b = "Another paragraph entirely with different content." * 3
    text = f"{para_a}\n\n{para_b}"

    chunks = chunk_text(text, chunk_size=120, chunk_overlap=20)

    assert len(chunks) > 1
    assert all(len(c) <= 120 for c in chunks)
    # content is preserved across chunks
    assert "Sentence one" in chunks[0]
    assert "Another paragraph" in chunks[-1]


def test_consecutive_chunks_overlap() -> None:
    text = " ".join(f"word{i}" for i in range(100))

    chunks = chunk_text(text, chunk_size=50, chunk_overlap=15)

    assert len(chunks) > 1
    for prev, nxt in zip(chunks, chunks[1:]):
        overlap = prev[-15:].strip()
        assert any(part in nxt for part in overlap.split())


def test_pathological_long_word_falls_back_to_hard_split() -> None:
    text = "a" * 500
    chunks = chunk_text(text, chunk_size=100, chunk_overlap=10)

    assert all(len(c) <= 100 for c in chunks)
    assert "".join(chunks).replace("", "") != ""
