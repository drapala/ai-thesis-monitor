"""Text-source ingestion pipeline."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_thesis_monitor.db.models.analytics import Claim
from ai_thesis_monitor.db.models.core import Document, DocumentChunk, RawObservation, Source
from ai_thesis_monitor.domain.claims.extract import extract_claims
from ai_thesis_monitor.ingestion.adapters.rss import RssAdapter
from ai_thesis_monitor.ingestion.parsers.text import chunk_text


@dataclass
class TextPipelineResult:
    raw_observations: int
    claims_created: int


def run_text_pipeline(session: Session, *, client: httpx.Client, source_keys: list[str]) -> TextPipelineResult:
    sources = session.scalars(select(Source).where(Source.source_key.in_(source_keys))).all()
    adapter = RssAdapter(client=client)

    raw_count = 0
    claim_count = 0

    for source in sources:
        items = adapter.fetch(source.base_url)
        for item in items:
            payload = {"source_key": source.source_key, "item": item}
            content_hash = hashlib.sha256(
                json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()

            raw_observation = session.scalar(
                select(RawObservation).where(
                    RawObservation.source_id == source.id,
                    RawObservation.content_hash == content_hash,
                )
            )
            if raw_observation is None:
                raw_observation = RawObservation(
                    source_id=source.id,
                    external_id=item.get("link") or None,
                    payload=payload,
                    content_hash=content_hash,
                    published_at=_parse_pub_date(item.get("pubDate", "")),
                )
                session.add(raw_observation)
                session.flush()
                raw_count += 1

            document = session.scalar(
                select(Document).where(
                    Document.source_id == source.id,
                    Document.raw_observation_id == raw_observation.id,
                )
            )
            if document is None:
                document = Document(
                    source_id=source.id,
                    raw_observation_id=raw_observation.id,
                    title=item.get("title", ""),
                    url=item.get("link") or None,
                    body_text=item.get("description", ""),
                    published_at=raw_observation.published_at,
                )
                session.add(document)
                session.flush()
            else:
                document.title = item.get("title", "")
                document.url = item.get("link") or None
                document.body_text = item.get("description", "")
                document.published_at = raw_observation.published_at

            for chunk in chunk_text(document.body_text):
                document_chunk = session.scalar(
                    select(DocumentChunk).where(
                        DocumentChunk.document_id == document.id,
                        DocumentChunk.chunk_index == chunk["chunk_index"],
                    )
                )
                if document_chunk is None:
                    document_chunk = DocumentChunk(document_id=document.id, **chunk)
                    session.add(document_chunk)
                    session.flush()
                else:
                    document_chunk.chunk_text = chunk["chunk_text"]
                    document_chunk.chunk_hash = chunk["chunk_hash"]

                extracted_claims = extract_claims(title=document.title, text=chunk["chunk_text"])
                for extracted in extracted_claims:
                    dedupe_key = (
                        f"{raw_observation.content_hash}:{document_chunk.chunk_hash}:{extracted.claim_type}"
                    )
                    claim = session.scalar(select(Claim).where(Claim.dedupe_key == dedupe_key))
                    if claim is not None:
                        continue

                    session.add(
                        Claim(
                            source_id=source.id,
                            raw_observation_id=raw_observation.id,
                            document_id=document.id,
                            chunk_id=document_chunk.id,
                            module_key=extracted.module_key,
                            claim_type=extracted.claim_type,
                            entity=extracted.entity,
                            claim_text=extracted.claim_text,
                            evidence_direction=extracted.evidence_direction,
                            strength=extracted.strength,
                            confidence=extracted.confidence,
                            dedupe_key=dedupe_key,
                            review_status=extracted.review_status,
                            published_date=raw_observation.published_at.date()
                            if raw_observation.published_at is not None
                            else None,
                        )
                    )
                    claim_count += 1

    session.commit()
    return TextPipelineResult(raw_observations=raw_count, claims_created=claim_count)


def _parse_pub_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
