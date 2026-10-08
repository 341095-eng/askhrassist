"""Markdown section parsing and lightweight BM25 retrieval."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from rank_bm25 import BM25Okapi

STOPWORDS = {
    "a", "an", "and", "are", "can", "do", "does", "for", "from", "how",
    "i", "in", "is", "it", "me", "my", "of", "on", "or", "the", "to",
    "what", "when", "where", "which", "with", "you", "give", "please", "tell",
}

PHRASE_ALIASES = {
    "paid time off": "annual leave",
    "pto": "annual leave",
    "vacation": "annual leave",
    "work from home": "remote work",
    "wfh": "remote work",
    "quit": "resignation notice",
    "leaving the company": "resignation exit",
    "appraisal": "performance review",
    "health insurance": "medical insurance benefits",
    "pay back": "reimbursement",
    "refund": "reimbursement",
    "harassing": "harassment",
    "harassed": "harassment",
    "harassment": "harassment bullying reporting concern",
}


@dataclass(frozen=True)
class HandbookChunk:
    chunk_id: str
    file_name: str
    title: str
    section: str
    text: str

    @property
    def citation(self) -> str:
        return f"{self.file_name} — {self.section}"


@dataclass(frozen=True)
class SearchResult:
    chunk: HandbookChunk
    score: float
    overlap_terms: tuple[str, ...]

    def as_debug_dict(self) -> dict[str, object]:
        return {
            "source": self.chunk.citation,
            "score": round(self.score, 3),
            "overlap_terms": list(self.overlap_terms),
            "preview": self.chunk.text[:350],
        }


@dataclass(frozen=True)
class RetrievalDecision:
    query: str
    normalized_query: str
    results: tuple[SearchResult, ...]
    confident: bool
    reason: str


def normalize_query(query: str) -> str:
    normalized = query.lower().strip()
    for phrase, replacement in PHRASE_ALIASES.items():
        normalized = re.sub(rf"\b{re.escape(phrase)}\b", replacement, normalized)
    normalized = re.sub(r"[^a-z0-9\s-]", " ", normalized)
    return " ".join(normalized.split())


def tokenize(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", normalize_query(text))
        if len(token) > 1 and token not in STOPWORDS
    ]


def load_handbook_chunks(handbook_dir: Path) -> list[HandbookChunk]:
    chunks: list[HandbookChunk] = []
    for path in sorted(handbook_dir.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        document_title = path.stem.replace("_", " ").title()
        current_section = "Overview"
        section_lines: list[str] = []
        section_number = 0

        def add_section() -> None:
            nonlocal section_number
            body = "\n".join(section_lines).strip()
            if not body:
                return
            section_number += 1
            chunks.append(
                HandbookChunk(
                    chunk_id=f"{path.stem}-{section_number}",
                    file_name=path.name,
                    title=document_title,
                    section=current_section,
                    text=body,
                )
            )

        for line in content.splitlines():
            if line.startswith("# "):
                document_title = line[2:].strip()
            elif line.startswith("## "):
                add_section()
                current_section = line[3:].strip()
                section_lines = []
            else:
                section_lines.append(line)
        add_section()
    return chunks


class HandbookRetriever:
    def __init__(self, handbook_dir: Path):
        self.chunks = load_handbook_chunks(handbook_dir)
        if not self.chunks:
            raise ValueError(f"No handbook Markdown files found in {handbook_dir}")
        corpus = [
            tokenize(f"{chunk.title} {chunk.section} {chunk.text}")
            for chunk in self.chunks
        ]
        self._corpus_terms = [set(tokens) for tokens in corpus]
        self._index = BM25Okapi(corpus)

    def retrieve(
        self, query: str, *, top_k: int = 3, min_score: float = 1.5
    ) -> RetrievalDecision:
        normalized = normalize_query(query)
        query_tokens = tokenize(normalized)
        if not query_tokens:
            return RetrievalDecision(query, normalized, (), False, "No meaningful query terms")

        scores = self._index.get_scores(query_tokens)
        ranked_indices = sorted(
            range(len(scores)), key=lambda index: float(scores[index]), reverse=True
        )[:top_k]
        results = tuple(
            SearchResult(
                chunk=self.chunks[index],
                score=float(scores[index]),
                overlap_terms=tuple(
                    sorted(set(query_tokens).intersection(self._corpus_terms[index]))
                ),
            )
            for index in ranked_indices
            if float(scores[index]) > 0
        )

        if not results:
            return RetrievalDecision(query, normalized, (), False, "No handbook term overlap")

        top = results[0]
        meaningful_overlap = len(top.overlap_terms)
        required_overlap = min(2, len(set(query_tokens)))
        overlap_ratio = meaningful_overlap / max(1, len(set(query_tokens)))
        confident = (
            top.score >= min_score
            and meaningful_overlap >= required_overlap
            and overlap_ratio >= 0.34
        )
        reason = (
            f"Top score {top.score:.2f} and term coverage {overlap_ratio:.0%} "
            f"met thresholds"
            if confident
            else f"Top score {top.score:.2f} or term coverage "
            f"{meaningful_overlap}/{len(set(query_tokens))} was below threshold"
        )
        return RetrievalDecision(query, normalized, results, confident, reason)
