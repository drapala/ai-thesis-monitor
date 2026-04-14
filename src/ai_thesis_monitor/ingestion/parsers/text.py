"""Text parsing helpers for ingestion pipelines."""

from __future__ import annotations

import hashlib


def chunk_text(text: str, *, chunk_size: int = 600) -> list[dict]:
    chunks: list[dict] = []
    for index, start in enumerate(range(0, len(text), chunk_size)):
        chunk_text_value = text[start : start + chunk_size].strip()
        if not chunk_text_value:
            continue
        chunks.append(
            {
                "chunk_index": index,
                "chunk_text": chunk_text_value,
                "chunk_hash": hashlib.sha256(chunk_text_value.encode("utf-8")).hexdigest(),
            }
        )
    return chunks
