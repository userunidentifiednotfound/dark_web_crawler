"""Scope policy enforcement and link classification."""

from enum import Enum
from urllib.parse import urlparse
from dwi_crawler.config.settings import get_settings
from dwi_crawler.security.validation import is_onion_domain, is_onion_url


class LinkType(str, Enum):
    ONION = "ONION"
    SURFACE = "SURFACE"
    EXTERNAL = "EXTERNAL"
    EMAIL = "EMAIL"
    FILE = "FILE"
    UNKNOWN = "UNKNOWN"


class ScopePolicy:
    """Enforces boundaries on which URLs may be crawled or queued."""

    def __init__(
        self,
        mode: str | None = None,
        company_domains: list[str] | None = None,
        allowlist: list[str] | None = None,
    ):
        settings = get_settings()
        self.mode = mode or settings.scope_policy
        self.company_domains = {d.lower().strip() for d in (company_domains or [])}
        self.allowlist = {d.lower().strip() for d in (allowlist or [])}

    def classify_link(self, raw_url: str) -> LinkType:
        """Classifies a URL into structural link categories."""
        url_lower = raw_url.strip().lower()
        if url_lower.startswith("mailto:"):
            return LinkType.EMAIL

        # Common downloadable static files
        file_exts = (
            ".pdf", ".zip", ".tar", ".gz", ".7z", ".rar",
            ".exe", ".bin", ".iso", ".jpg", ".png", ".gif",
            ".mp3", ".mp4", ".doc", ".docx", ".xls", ".xlsx"
        )
        parsed = urlparse(url_lower)
        if any(parsed.path.endswith(ext) for ext in file_exts):
            return LinkType.FILE

        if is_onion_url(url_lower):
            return LinkType.ONION

        if parsed.scheme in ("http", "https"):
            host = parsed.hostname or ""
            if any(host == d or host.endswith("." + d) for d in self.company_domains):
                return LinkType.SURFACE
            return LinkType.EXTERNAL

        return LinkType.UNKNOWN

    def is_allowed_to_crawl(self, url: str) -> bool:
        """Determines if a target URL is permitted for active downloading."""
        link_type = self.classify_link(url)

        if link_type == LinkType.EMAIL:
            return False

        if self.mode == "ONION_ONLY":
            # Strict mode: Only dark web onion services are permitted for crawling
            return link_type == LinkType.ONION

        if self.mode == "COMPANY_DOMAINS":
            if link_type == LinkType.ONION:
                return True
            parsed = urlparse(url)
            host = (parsed.hostname or "").lower()
            return any(host == d or host.endswith("." + d) for d in self.company_domains)

        if self.mode == "EXPLICIT_ALLOWLIST":
            parsed = urlparse(url)
            host = (parsed.hostname or "").lower()
            return any(host == a or host.endswith("." + a) for a in self.allowlist)

        return False
