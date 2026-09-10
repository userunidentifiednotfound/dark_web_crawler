"""Keyword enhancement logic for intelligence query expansion."""

import re
from typing import NamedTuple


class EnhancedQuerySet(NamedTuple):
    surface_queries: list[str]
    onion_queries: list[str]

    @property
    def all_queries(self) -> list[str]:
        return self.surface_queries + self.onion_queries


class KeywordEnhancer:
    """Generates bounded permutations for surface and onion discovery."""

    @staticmethod
    def clean_term(term: str) -> str:
        """Strips quotes and excessive punctuation."""
        return re.sub(r'[^\w\s\.\-@]', '', term).strip()

    @classmethod
    def enhance_keyword(
        cls,
        keyword: str,
        *,
        company_name: str = "",
        domain: str = "",
    ) -> EnhancedQuerySet:
        """Generates bounded discovery queries: exactly 3 surface and 7 onion queries."""
        clean_kw = cls.clean_term(keyword)
        clean_comp = cls.clean_term(company_name) if company_name else clean_kw
        clean_dom = domain.strip().lower()

        # 1. Surface Queries (strictly 3 queries)
        surface_queries = [
            f'"{clean_kw}"',                                # 1. Exact quoted
            f'"{clean_kw}" {clean_dom}' if clean_dom else f'"{clean_kw}" security', # 2. Domain / brand context
            f'"{clean_kw}" breach OR leak OR database',    # 3. Security context
        ]

        # 2. Onion Queries (strictly 7 queries)
        onion_queries = [
            f'"{clean_kw}"',                                # 1. Exact quoted
            f'{clean_kw}',                                  # 2. Unquoted broad
            f'"{clean_kw}" leak',                           # 3. Keyword + leak
            f'"{clean_kw}" database',                       # 4. Keyword + database
            f'"{clean_kw}" credentials',                    # 5. Keyword + credentials
            f'"{clean_kw}" {clean_comp}' if clean_comp != clean_kw else f'"{clean_kw}" employee', # 6. Keyword + company/employee
            f'"{clean_dom}"' if clean_dom else f'"{clean_kw}" dump', # 7. Domain or dump
        ]

        return EnhancedQuerySet(
            surface_queries=surface_queries[:3],
            onion_queries=onion_queries[:7],
        )
