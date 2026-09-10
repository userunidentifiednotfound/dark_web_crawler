"""Unit tests for bounded keyword enhancement (3 surface, 7 onion)."""

import pytest
from dwi_crawler.discovery.enhancer import KeywordEnhancer


def test_keyword_enhancement_counts():
    res = KeywordEnhancer.enhance_keyword(
        keyword="Acme Global",
        company_name="Acme Global",
        domain="acmeglobal.com",
    )
    assert len(res.surface_queries) == 3
    assert len(res.onion_queries) == 7
    assert len(res.all_queries) == 10


def test_keyword_enhancement_bounded_exact():
    res = KeywordEnhancer.enhance_keyword(
        keyword="executive breach",
        company_name="Acme Corp",
        domain="acme.com",
    )
    assert len(res.surface_queries) == 3
    assert len(res.onion_queries) == 7
    # Surface queries should contain brand/domain correlation
    assert any("acme.com" in q or "Acme Corp" in q for q in res.surface_queries)
    # Onion queries should contain specialized dark web breach indicators
    assert any("leak" in q or "database" in q or "credentials" in q for q in res.onion_queries)
