"""Page-level full-text search for Research Archive Matcher."""

from __future__ import annotations

import re
from dataclasses import dataclass

from rapidfuzz import fuzz


@dataclass(slots=True)
class PageSearchResult:
    """One ranked page-level search result."""

    document_id: int
    title: str
    file_path: str
    page_number: int
    snippet: str
    score: float
    match_type: str


class PageSearchService:
    """Search the RAM page-text FTS index and rank results."""

    def __init__(self, database):
        self.database = database

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(value.casefold().split())

    @classmethod
    def _score(cls, query: str, text: str) -> tuple[float, str]:
        normalized_query = cls._normalize(query)
        normalized_text = cls._normalize(text)

        if normalized_query in normalized_text:
            return 100.0, "exact phrase"

        query_words = set(re.findall(r"\w+", normalized_query))
        text_words = set(re.findall(r"\w+", normalized_text))

        if query_words and query_words.issubset(text_words):
            return 95.0, "all query words"

        score = fuzz.partial_ratio(normalized_query, normalized_text)
        return round(float(score), 1), "fuzzy text match"

    def search(
        self,
        query: str,
        *,
        exact_phrase: bool = False,
        minimum_score: float = 0.0,
        limit: int = 100,
    ) -> list[PageSearchResult]:
        """Return ranked article/page matches for a query."""
        rows = self.database.search_pages(
            query,
            exact_phrase=exact_phrase,
            limit=limit,
        )

        # PDF extraction often inserts line breaks inside a phrase. If the
        # FTS phrase query cannot find it, search the component words and
        # verify the normalized phrase in Python.
        if exact_phrase and not rows:
            rows = self.database.search_pages(
                query,
                exact_phrase=False,
                limit=limit,
            )

        results: list[PageSearchResult] = []

        for row in rows:
            score, match_type = self._score(query, row["page_text"])

            if exact_phrase and score != 100.0:
                continue

            if score < minimum_score:
                continue

            results.append(
                PageSearchResult(
                    document_id=row["document_id"],
                    title=row["title"] or "No title",
                    file_path=row["file_path"],
                    page_number=row["page_number"],
                    snippet=row["snippet"] or row["page_text"][:300],
                    score=score,
                    match_type=match_type,
                )
            )

        results.sort(
            key=lambda result: (
                -result.score,
                result.title.casefold(),
                result.page_number,
            )
        )
        return results
