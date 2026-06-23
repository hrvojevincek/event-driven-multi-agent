import tiktoken

DEFAULT_ENCODING = "cl100k_base"


def chunk_text(
    text: str,
    *,
    chunk_size: int,
    overlap: int,
    encoding_name: str = DEFAULT_ENCODING,
) -> list[str]:
    """Split text into overlapping token windows for embedding."""
    normalized = text.strip()
    if not normalized:
        return []

    if overlap >= chunk_size:
        msg = "chunk overlap must be smaller than chunk_size"
        raise ValueError(msg)

    encoder = tiktoken.get_encoding(encoding_name)
    tokens = encoder.encode(normalized)
    if len(tokens) <= chunk_size:
        return [normalized]

    chunks: list[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunks.append(encoder.decode(tokens[start:end]))
        if end >= len(tokens):
            break
        start = end - overlap
    return chunks


def build_source_text(*, title: str, snippet: str) -> str:
    """Combine source title and snippet into embeddable document text."""
    parts = [title.strip(), snippet.strip()]
    return "\n\n".join(part for part in parts if part)
