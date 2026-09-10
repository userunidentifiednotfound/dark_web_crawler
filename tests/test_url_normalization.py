"""Unit tests for URL normalization and deduplication."""

import pytest
from dwi_crawler.security.validation import URLNormalizer, is_onion_domain, is_onion_url


def test_url_normalization_standard():
    raw = "HTTP://Example.COM:80/path/../path/to/./page.html?b=2&a=1#fragment"
    expected = "http://example.com/path/to/page.html?a=1&b=2"
    normalized = URLNormalizer.normalize(raw)
    assert normalized == expected


def test_url_normalization_onion():
    raw = "http://EXAMPLe34567890123456789012345678901234567890123456789012.onion:80/hidden//sub/index.html?param=xyz"
    normalized = URLNormalizer.normalize(raw)
    assert normalized.startswith("http://example34567890123456789012345678901234567890123456789012.onion/hidden/sub/index.html")
    assert "param=xyz" in normalized
    assert ":80" not in normalized


def test_onion_detection():
    assert is_onion_url("http://example1234567890.onion/path")
    assert is_onion_url("https://sub.domain.onion/test")
    assert not is_onion_url("https://example.com/not-onion")
    assert is_onion_domain("test.onion")
    assert not is_onion_domain("test.com")


def test_url_fingerprint_deduplication():
    url1 = "http://example.com/page?a=1&b=2"
    url2 = "http://example.com:80/page?b=2&a=1#frag"
    fp1 = URLNormalizer.fingerprint(URLNormalizer.normalize(url1))
    fp2 = URLNormalizer.fingerprint(URLNormalizer.normalize(url2))
    assert fp1 == fp2
