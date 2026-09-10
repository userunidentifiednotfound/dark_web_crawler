"""Link extraction engine discovering structured tags and text-embedded onion links."""

import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from dwi_crawler.security.validation import ONION_DOMAIN_REGEX, URLNormalizer, is_onion_url

# Regex to discover raw onion URLs in text
TEXT_ONION_REGEX = re.compile(
    r"https?://(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*(?:[a-z2-7]{16}|[a-z2-7]{56})\.onion(?:/[^\s\"'<>]*)?",
    re.IGNORECASE,
)


class ExtractedLink:
    def __init__(
        self,
        raw_url: str,
        canonical_url: str,
        url_hash: str,
        link_type: str,
        is_onion: bool,
    ):
        self.raw_url = raw_url
        self.canonical_url = canonical_url
        self.url_hash = url_hash
        self.link_type = link_type
        self.is_onion = is_onion


class LinkExtractor:
    """Extracts and normalizes links from HTML DOM and visible text."""

    @classmethod
    def extract_links(cls, html_content: str | bytes, base_url: str) -> list[ExtractedLink]:
        if isinstance(html_content, bytes):
            html_text = html_content.decode("utf-8", errors="replace")
        else:
            html_text = html_content

        links: list[ExtractedLink] = []
        seen_canonical: set[str] = set()

        def add_link(raw: str, tag_type: str):
            if not raw or raw.startswith(("#", "javascript:", "tel:", "data:")):
                return

            # Resolve relative URLs
            resolved = urljoin(base_url, raw.strip())
            canonical = URLNormalizer.normalize(resolved)
            if not canonical or canonical in seen_canonical:
                return

            seen_canonical.add(canonical)
            fingerprint = URLNormalizer.fingerprint(canonical)
            onion_flag = is_onion_url(canonical)

            links.append(
                ExtractedLink(
                    raw_url=resolved,
                    canonical_url=canonical,
                    url_hash=fingerprint,
                    link_type=tag_type,
                    is_onion=onion_flag,
                )
            )

        try:
            soup = BeautifulSoup(html_text, "html.parser")

            # 1. <a href>
            for a in soup.find_all("a", href=True):
                add_link(a["href"], "a_href")

            # 2. <form action>
            for f in soup.find_all("form", action=True):
                add_link(f["action"], "form_action")

            # 3. <iframe src>
            for ifr in soup.find_all("iframe", src=True):
                add_link(ifr["src"], "iframe_src")

            # 4. <link href>
            for link in soup.find_all("link", href=True):
                add_link(link["href"], "link_href")

            # 5. <script src>
            for scr in soup.find_all("script", src=True):
                add_link(scr["src"], "script_src")

            # 6. <img src>
            for img in soup.find_all("img", src=True):
                add_link(img["src"], "img_src")

            # 7. Unlinked text onion URLs
            for match in TEXT_ONION_REGEX.finditer(html_text):
                add_link(match.group(0), "text_url")

        except Exception:
            # If DOM parsing fails, scan raw text with regex
            for match in TEXT_ONION_REGEX.finditer(html_text):
                add_link(match.group(0), "text_url")

        return links
