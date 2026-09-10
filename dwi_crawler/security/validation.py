"""URL validation, normalization, and canonical fingerprinting."""

import hashlib
import re
from urllib.parse import parse_qsl, quote, urlencode, urlparse, urlunparse

# Onion address pattern (v3 is 56 chars base32, v2 legacy is 16 chars)
ONION_DOMAIN_REGEX = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*(?:[a-z2-7]{16}|[a-z2-7]{56})\.onion$",
    re.IGNORECASE,
)


def is_onion_url(url: str) -> bool:
    """Returns True if the URL points to a valid .onion domain."""
    try:
        parsed = urlparse(url.strip())
        hostname = (parsed.hostname or "").lower()
        return hostname.endswith(".onion") and len(hostname) >= 7
    except Exception:
        return False


def is_onion_domain(domain: str) -> bool:
    """Returns True if domain is a valid .onion domain."""
    d = domain.strip().lower()
    return d.endswith(".onion") and len(d) >= 7


class URLNormalizer:
    """Normalizes URLs to canonical representations for strict deduplication."""

    @staticmethod
    def normalize(raw_url: str, *, preserve_fragments: bool = False) -> str:
        """Transforms a URL into its canonical form.
        
        Rules:
        - Scheme: lowercased (http / https default)
        - Hostname: lowercased, punycode normalized
        - Default ports stripped (80 for http, 443 for https)
        - Path: redundant slashes collapsed, dot segments resolved
        - Trailing slash removed for root or directory if appropriate
        - Query: parameter keys sorted deterministically without destroying values
        - Fragments: removed by default
        """
        raw = raw_url.strip()
        if not raw:
            return ""

        # Prepend http:// if missing scheme
        if "://" not in raw:
            raw = "http://" + raw

        parsed = urlparse(raw)
        scheme = (parsed.scheme or "http").lower()
        netloc = parsed.netloc

        if not netloc:
            return ""

        # Extract host and port
        host = (parsed.hostname or "").lower()
        port = parsed.port

        # Strip standard ports
        if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
            port = None

        netloc_clean = host
        if port is not None:
            netloc_clean = f"{host}:{port}"

        # Resolve path dot segments
        path = parsed.path or "/"
        # Replace multiple slashes with a single slash
        path = re.sub(r"/{2,}", "/", path)

        # Normalize relative path traversal safely
        segments = []
        for seg in path.split("/"):
            if seg == "..":
                if segments:
                    segments.pop()
            elif seg and seg != ".":
                segments.append(seg)

        canonical_path = "/" + "/".join(segments)
        # If original path had trailing slash and was not root, keep single trailing slash
        if path.endswith("/") and canonical_path != "/":
            canonical_path += "/"

        # Normalize query string (sort params deterministically)
        query = ""
        if parsed.query:
            params = parse_qsl(parsed.query, keep_blank_values=True)
            params.sort(key=lambda x: x[0])
            query = urlencode(params, quote_via=quote)

        fragment = parsed.fragment if preserve_fragments else ""

        canonical = urlunparse((scheme, netloc_clean, canonical_path, "", query, fragment))
        return canonical

    @staticmethod
    def fingerprint(canonical_url: str) -> str:
        """Calculates SHA256 hex digest of the canonical URL."""
        return hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()
