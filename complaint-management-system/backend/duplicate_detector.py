"""
Duplicate complaint detection.

Groq has no embeddings endpoint, so this uses a local sentence-transformers
model (all-MiniLM-L6-v2 by default — small, fast, runs on CPU, no API key
needed) to embed a compact text representation of each complaint, then
compares via cosine similarity.

Matching signal is a combination of:
  - Semantic similarity of (product_name + description) embeddings
  - An exact batch_number match, which is treated as a strong independent signal
    (two complaints on the exact same batch are worth flagging even if the
    wording of the description differs)

This is intentionally simple: real pharma trend-analysis systems (APQR-style)
would look at rolling windows, defect taxonomies, and statistical thresholds.
This is a "flag it for human review" signal, not an automated dedup decision —
the UI should always let the user dismiss a flagged match.
"""

from functools import lru_cache
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

from config import settings
from schemas import Complaint, DuplicateMatch


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    # Cached so the model loads once per process, not once per request.
    return SentenceTransformer(settings.EMBEDDING_MODEL_NAME)


def _complaint_text(complaint: Complaint) -> str:
    parts = [
        complaint.product_name or "",
        complaint.complaint_description or "",
        complaint.complaint_type.value if complaint.complaint_type else "",
    ]
    return " | ".join(p for p in parts if p).strip()


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def find_duplicates(complaint: Complaint, existing_complaints: List[Complaint]) -> List[DuplicateMatch]:
    """Returns candidate duplicates above the configured similarity threshold,
    sorted by descending similarity. Does not mutate or delete anything —
    purely informational, for the UI to surface as a flag."""

    target_text = _complaint_text(complaint)
    if not target_text or not existing_complaints:
        return []

    model = _get_model()
    target_embedding = model.encode(target_text)

    matches: List[DuplicateMatch] = []

    for other in existing_complaints:
        other_text = _complaint_text(other)
        if not other_text:
            continue

        other_embedding = model.encode(other_text)
        similarity = _cosine_similarity(target_embedding, other_embedding)

        matched_on = []
        if similarity >= settings.DUPLICATE_SIMILARITY_THRESHOLD:
            matched_on.append("description_similarity")

        same_batch = (
            complaint.batch_number
            and other.batch_number
            and complaint.batch_number.strip().lower() == other.batch_number.strip().lower()
        )
        if same_batch:
            matched_on.append("batch_number")
            # An exact batch match is meaningful even with moderate text
            # similarity — boost the effective score slightly so it surfaces.
            similarity = max(similarity, settings.DUPLICATE_SIMILARITY_THRESHOLD)

        if matched_on:
            matches.append(
                DuplicateMatch(
                    complaint_id=other.complaint_id,
                    similarity_score=round(similarity, 3),
                    matched_on=matched_on,
                )
            )

    matches.sort(key=lambda m: m.similarity_score, reverse=True)
    return matches