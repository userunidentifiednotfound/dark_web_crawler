"""Deterministic realistic dark web test pages for robust validation and testing."""

import hashlib
from typing import NamedTuple


class MockPage(NamedTuple):
    html: str
    status_code: int = 200
    mime_type: str = "text/html; charset=utf-8"
    is_captcha: bool = False
    captcha_type: str | None = None


def generate_ransomware_blog(company_name: str = "Acme Global") -> MockPage:
    html = f"""<!DOCTYPE html>
<html>
<head><title>BlackCat / ALPHV Leak Blog - {company_name}</title></head>
<body>
<h1>Victim Announcement: {company_name}</h1>
<p class="leak-description">
We have successfully breached the internal database and infrastructure of {company_name}.
Over 450GB of executive emails, internal passwords, financial audits, and client contracts were exfiltrated.
Deadline for ransom payment: 72 hours.
</p>
<div class="evidence-box">
  <h3>Compromised Data Samples:</h3>
  <pre>
  admin@{company_name.lower().replace(' ', '')}.com:Hash$2y$12$e8Y.
  executive@{company_name.lower().replace(' ', '')}.com:Summer2025!
  Internal IP Gateway: 198.51.100.45
  Database Backup SHA256: 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824
  </pre>
</div>
<div class="ransom-wallet">
  <p>Send 2.5 BTC to Bitcoin Address: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa</p>
  <p>Or 45 XMR to Monero: 44AFFq5kSiGBoZ4NMDwYtN18obc8AemS33DBLWs3H7otXft3XjRPUbQGQsA762BaLTemWh9KAoCzKRVT53Q5n2fiEvau1KD</p>
  <p>Or ETH: 0x71C6634C2556405871137A4B110ca679acbCC0E8</p>
  <p>Negotiations contact: @dark_broker_alphv</p>
</div>
<div class="links">
  <a href="http://lockbit7xxxpage2.onion/proof">Download Sample Archive</a>
  <a href="http://lockbit7xxxpage3.onion/press">Press Release</a>
</div>
</body>
</html>
"""
    return MockPage(html=html)


def generate_credential_paste(company_name: str = "Acme Global") -> MockPage:
    domain = company_name.lower().replace(" ", "") + ".com"
    html = f"""<!DOCTYPE html>
<html>
<head><title>DarkPaste #8892 - {company_name} Leaks</title></head>
<body>
<h2>{company_name} Customer & Employee Credentials Dump</h2>
<p>Extracted from compromised internal database server:</p>
<pre>
root@{domain}:SuperSecret2025!
developer@{domain}:gitCommit#2024
security@{domain}:Admin$991
finance@{domain}:Q4_Budget_Pass!
Server Host: 203.0.113.195
MD5: 5d41402abc4b2a76b9719d911017c592
</pre>
<a href="http://pasteonionxyz4.onion/raw/8892">Raw View</a>
<a href="http://darkforum991.onion/thread/441">Discussion Thread</a>
</body>
</html>
"""
    return MockPage(html=html)


def generate_marketplace_listing(company_name: str = "Acme Global") -> MockPage:
    html = f"""<!DOCTYPE html>
<html>
<head><title>Empire Market 2.0 - Corporate Access</title></head>
<body>
<h1>Listing: Direct VPN & RDP Access to {company_name} Internal Network</h1>
<p>Vendor: NetInfiltrator (Rating: 4.95/5, 120 sales)</p>
<p>High privileged administrative domain credentials for {company_name}. Full access to internal database, Active Directory, and file repositories.</p>
<p>Price: 0.75 BTC (~$45,000 USD)</p>
<p>Escrow payment address: 3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy</p>
<form action="http://darkmarketxyz.onion/checkout" method="POST">
  <input type="hidden" name="item_id" value="9914" />
  <button type="submit">Buy via Escrow</button>
</form>
</body>
</html>
"""
    return MockPage(html=html)


def generate_captcha_page() -> MockPage:
    html = """<!DOCTYPE html>
<html>
<head><title>DDoS-Guard / Onion Challenge</title></head>
<body>
<div class="cf-challenge">
  <h1>Attention Required!</h1>
  <p>Please enter captcha to continue to the onion service.</p>
  <div id="cf-turnstile" class="cf-turnstile"></div>
</div>
</body>
</html>
"""
    return MockPage(html=html, status_code=403, is_captcha=True, captcha_type="onion_challenge")


def generate_broken_html_page(company_name: str = "Acme Global") -> MockPage:
    html = f"""<html xmlns="http://www.w3.org/1999/xhtml">
<title>Unclosed page for {company_name}
<body>
<div><h3>Compromised Data</h3>
<p>Internal database leaked: info@{company_name.lower().replace(' ', '')}.com
<a href="http://sublink.onion/page>broken link
<img src="http://sublink.onion/logo.png"
<script>var x = 1;
</body>"""
    return MockPage(html=html)


def generate_link_directory_page(base_onion: str = "http://directory.onion") -> MockPage:
    links_html = "\n".join(f'<a href="{base_onion}/resource_{i}">Resource #{i}</a>' for i in range(1, 51))
    html = f"""<!DOCTYPE html>
<html>
<head><title>Dark Web Hidden Service Directory</title></head>
<body>
<h1>Index of Hidden Services</h1>
<div class="directory-grid">
{links_html}
</div>
</body>
</html>
"""
    return MockPage(html=html)


def get_mock_page_for_url(url: str, company_name: str = "Acme Global") -> MockPage:
    """Returns an appropriate realistic mock page based on URL patterns or deterministically."""
    url_lower = url.lower()
    if "captcha" in url_lower or "challenge" in url_lower:
        return generate_captcha_page()
    if "broken" in url_lower:
        return generate_broken_html_page(company_name)
    if "directory" in url_lower or "index" in url_lower:
        return generate_link_directory_page()
    if "paste" in url_lower or "dump" in url_lower:
        return generate_credential_paste(company_name)
    if "market" in url_lower:
        return generate_marketplace_listing(company_name)
    # Default to leak / ransomware publication
    return generate_ransomware_blog(company_name)
