"""Keyword matching and context extraction engine."""

import re
from typing import NamedTuple
from dwi_crawler.config.settings import get_settings


class KeywordMatch(NamedTuple):
    term: str
    keyword_id: int | None
    matched_text: str
    context: str
    start_pos: int
    end_pos: int
    confidence: float


class KeywordMatcher:
    """Matches content against company keywords and extracts contextual evidence."""

    @classmethod
    def match_content(
        cls,
        text: str,
        keywords: list[tuple[int | None, str]],  # [(keyword_id, term), ...]
        *,
        context_radius: int | None = None,
    ) -> list[KeywordMatch]:
        radius = context_radius or get_settings().context_radius
        matches: list[KeywordMatch] = []
        lower_text = text.lower()

        for kw_id, term in keywords:
            clean_term = term.strip().lower()
            if not clean_term:
                continue

            # Case-insensitive word boundary match
            pattern = re.compile(re.escape(clean_term), re.IGNORECASE)
            for m in pattern.finditer(text):
                start = max(0, m.start() - radius)
                end = min(len(text), m.end() + radius)
                context = text[start:end].replace("\n", " ").strip()

                # Basic confidence heuristic
                confidence = 0.80
                surrounding = context.lower()
                if any(w in surrounding for w in ("leak", "breach", "dump", "password", "database", "credential", "internal")):
                    confidence = 0.92

                matches.append(
                    KeywordMatch(
                        term=term,
                        keyword_id=kw_id,
                        matched_text=m.group(0),
                        context=context,
                        start_pos=m.start(),
                        end_pos=m.end(),
                        confidence=confidence,
                    )
                )

        return matches
