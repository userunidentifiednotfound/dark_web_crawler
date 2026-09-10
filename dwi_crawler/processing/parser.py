"""Robust HTML parser extracting clean visible text, headings, and metadata."""

import logging
from bs4 import BeautifulSoup

logger = logging.getLogger("dwi_crawler.processing.parser")


class ParsedPageContent:
    def __init__(
        self,
        title: str,
        text: str,
        headings: list[str],
        meta_tags: dict[str, str],
    ):
        self.title = title
        self.text = text
        self.headings = headings
        self.meta_tags = meta_tags


class HTMLParser:
    """Survives invalid HTML, broken encodings, and large bodies."""

    @staticmethod
    def parse(raw_html: str | bytes) -> ParsedPageContent:
        try:
            if isinstance(raw_html, bytes):
                # Attempt decode with fallback
                text_content = raw_html.decode("utf-8", errors="replace")
            else:
                text_content = raw_html

            soup = BeautifulSoup(text_content, "html.parser")

            # Extract title
            title = ""
            if soup.title and soup.title.string:
                title = soup.title.string.strip()

            # Extract headings
            headings: list[str] = []
            for h in soup.find_all(["h1", "h2", "h3"]):
                h_text = h.get_text(strip=True)
                if h_text:
                    headings.append(h_text)

            # Extract meta tags
            meta_tags: dict[str, str] = {}
            for meta in soup.find_all("meta"):
                name = meta.get("name") or meta.get("property")
                content = meta.get("content")
                if name and content:
                    meta_tags[name.strip()] = content.strip()

            # Remove unwanted tags for visible text
            for elem in soup(["script", "style", "noscript", "svg"]):
                elem.extract()

            visible_text = soup.get_text(separator=" ", strip=True)

            return ParsedPageContent(
                title=title,
                text=visible_text,
                headings=headings,
                meta_tags=meta_tags,
            )
        except Exception as ex:
            logger.warning(f"Error parsing HTML: {ex}")
            # Fallback to simple string extraction
            clean_fallback = str(raw_html)[:5000]
            return ParsedPageContent(
                title="",
                text=clean_fallback,
                headings=[],
                meta_tags={},
            )
