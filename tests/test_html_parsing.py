"""Unit tests for HTML parsing and resilient link extraction."""

from dwi_crawler.processing.links import LinkExtractor
from dwi_crawler.processing.parser import HTMLParser


def test_html_parser_headings_and_clean_text():
    html = """<!DOCTYPE html>
    <html>
    <head><title>Test Dark Web Service</title></head>
    <body>
    <script>var bad = 1;</script>
    <h1>Welcome to Breach Repository</h1>
    <h2>Subheading Details</h2>
    <p>Target credentials and exfiltrated documents.</p>
    <style>body { color: red; }</style>
    </body>
    </html>"""

    res = HTMLParser.parse(html)
    assert res.title == "Test Dark Web Service"
    assert "Welcome to Breach Repository" in res.headings
    assert "Subheading Details" in res.headings
    assert "Target credentials and exfiltrated documents." in res.text
    assert "var bad = 1" not in res.text
    assert "body { color: red; }" not in res.text


def test_link_extraction_html_and_text():
    html = """<!DOCTYPE html>
    <html>
    <body>
    <a href="http://lockbit7xxxpage2.onion/proof">Proof Archive</a>
    <a href="/internal/relative/path">Relative Link</a>
    <a href="https://clearnet-mirror.com/status">Surface Mirror</a>
    <form action="http://darkmarketxyz.onion/checkout" method="POST"></form>
    <p>Backup mirror onion address: http://expyuz7wqqhdsn6hl7fq4mg7w34k7p4lv44qgyfbfx2a67pmz72tqnyd.onion/dump</p>
    </body>
    </html>"""

    base_url = "http://lockbit7xxxpage2.onion/"
    links = LinkExtractor.extract_links(html, base_url)

    urls = [l.canonical_url for l in links]
    onion_links = [l for l in links if l.is_onion]

    assert "http://lockbit7xxxpage2.onion/proof" in urls
    assert "http://lockbit7xxxpage2.onion/internal/relative/path" in urls
    assert "https://clearnet-mirror.com/status" in urls
    assert "http://darkmarketxyz.onion/checkout" in urls
    assert any("expyuz7wqqhdsn6hl7fq4mg7w34k7p4lv44qgyfbfx2a67pmz72tqnyd.onion" in l.canonical_url for l in onion_links)
