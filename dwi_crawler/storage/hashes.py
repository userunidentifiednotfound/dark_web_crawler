"""Cryptographic hashing utilities for content and URLs."""

import hashlib


def sha256_bytes(data: bytes) -> str:
    """Calculates SHA256 hex digest of raw binary data."""
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    """Calculates SHA256 hex digest of UTF-8 string."""
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
