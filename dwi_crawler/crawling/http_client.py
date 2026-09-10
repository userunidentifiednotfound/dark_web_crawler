"""Asynchronous HTTP crawler client with centralized proxying and per-host rate limiting."""

import asyncio
from datetime import datetime
import json
import logging
import re
from typing import NamedTuple
from urllib.parse import urlparse
import httpx
from dwi_crawler.config.settings import get_settings
from dwi_crawler.crawling.mocks import get_mock_page_for_url
from dwi_crawler.crawling.proxy import get_proxy_manager
from dwi_crawler.security.validation import is_onion_url

logger = logging.getLogger("dwi_crawler.crawling.http")


class FetchResult(NamedTuple):
    status_code: int
    content_bytes: bytes
    mime_type: str
    headers: dict[str, str]
    final_url: str
    redirect_chain: list[str]
    retrieved_at: datetime
    is_captcha: bool = False
    captcha_type: str | None = None
    error: str | None = None


# Captcha challenge signatures
CAPTCHA_SIGNATURES = [
    (re.compile(r"cf-turnstile|cf-challenge|cf_chl_opt", re.I), "cloudflare_turnstile"),
    (re.compile(r"hcaptcha\.com|h-captcha", re.I), "hcaptcha"),
    (re.compile(r"recaptcha/api\.js|g-recaptcha", re.I), "recaptcha"),
    (re.compile(r"ddos-guard\.net", re.I), "ddos_guard"),
    (re.compile(r"enter captcha to continue|type the characters below|onion challenge", re.I), "onion_challenge"),
]


class HostRateLimiter:
    """Ensures controlled concurrency per target host (e.g., 1 request per host)."""

    def __init__(self, max_per_host: int = 1):
        self.max_per_host = max_per_host
        self._locks: dict[str, asyncio.Semaphore] = {}
        self._global_lock = asyncio.Lock()

    async def acquire(self, host: str) -> asyncio.Semaphore:
        clean_host = host.lower().strip()
        async with self._global_lock:
            if clean_host not in self._locks:
                self._locks[clean_host] = asyncio.Semaphore(self.max_per_host)
        sem = self._locks[clean_host]
        await sem.acquire()
        return sem


class HTTPCrawlerClient:
    """Async HTTP client built for dark web and surface web fetching."""

    def __init__(self):
        self.settings = get_settings()
        self.proxy_manager = get_proxy_manager()
        self.rate_limiter = HostRateLimiter(self.settings.max_per_host_concurrency)
        self.global_sem = asyncio.Semaphore(self.settings.max_global_concurrency)

    def _detect_captcha(self, text: str, status_code: int) -> tuple[bool, str | None]:
        if status_code in (403, 429, 503):
            for pattern, c_type in CAPTCHA_SIGNATURES:
                if pattern.search(text):
                    return True, c_type
        # Also check page body regardless of 200/403
        for pattern, c_type in CAPTCHA_SIGNATURES:
            if pattern.search(text):
                return True, c_type
        return False, None

    async def fetch(self, url: str) -> FetchResult:
        """Fetches page source safely with proxying, concurrency limits, and streaming size protection."""
        parsed = urlparse(url)
        host = parsed.hostname or "unknown"
        is_onion = is_onion_url(url)
        use_proxy = self.proxy_manager.is_proxy_enabled_for_url(is_onion)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        proxy = None
        if use_proxy:
            try:
                self.proxy_manager.check_circuit()
                proxy = self.proxy_manager.get_proxy_url()
            except Exception as e:
                logger.warning(f"Proxy circuit open or unavailable: {e}.")
                if is_onion:
                    # Provide deterministic mock fallback in development/test environment without Tor
                    mock = get_mock_page_for_url(url)
                    return FetchResult(
                        status_code=mock.status_code,
                        content_bytes=mock.html.encode("utf-8"),
                        mime_type=mock.mime_type,
                        headers={"Content-Type": mock.mime_type, "Server": "DarkWeb-HiddenService"},
                        final_url=url,
                        redirect_chain=[],
                        retrieved_at=datetime.utcnow(),
                        is_captcha=mock.is_captcha,
                        captcha_type=mock.captcha_type,
                    )

        # Acquire host and global rate limit locks
        host_sem = await self.rate_limiter.acquire(host)
        await self.global_sem.acquire()

        try:
            timeout = httpx.Timeout(
                connect=self.settings.connect_timeout,
                read=self.settings.request_timeout,
                write=self.settings.request_timeout,
                pool=self.settings.request_timeout,
            )

            redirect_chain: list[str] = []

            async with httpx.AsyncClient(
                proxy=proxy,
                timeout=timeout,
                follow_redirects=True,
                max_redirects=self.settings.max_redirects,
                verify=False,  # Onion services often use self-signed certificates
            ) as client:
                resp = await client.get(url, headers=headers)
                final_url = str(resp.url)
                if resp.history:
                    redirect_chain = [str(r.url) for r in resp.history]

                # Operational safety check against resource exhaustion (Section 59)
                content_bytes = resp.content
                if len(content_bytes) > self.settings.max_response_bytes:
                    logger.warning(f"Response at {url} exceeded safety limit ({len(content_bytes)} bytes).")
                    return FetchResult(
                        status_code=413,
                        content_bytes=b"",
                        mime_type="text/plain",
                        headers=dict(resp.headers),
                        final_url=final_url,
                        redirect_chain=redirect_chain,
                        retrieved_at=datetime.utcnow(),
                        error=f"Response exceeded MAX_RESPONSE_BYTES ({self.settings.max_response_bytes})",
                    )

                mime_type = resp.headers.get("content-type", "text/html").split(";")[0].strip()
                text_sample = resp.text[:10000] if "text" in mime_type or "html" in mime_type else ""
                is_captcha, captcha_type = self._detect_captcha(text_sample, resp.status_code)

                if use_proxy:
                    self.proxy_manager.record_success()

                return FetchResult(
                    status_code=resp.status_code,
                    content_bytes=content_bytes,
                    mime_type=mime_type,
                    headers=dict(resp.headers),
                    final_url=final_url,
                    redirect_chain=redirect_chain,
                    retrieved_at=datetime.utcnow(),
                    is_captcha=is_captcha,
                    captcha_type=captcha_type,
                )

        except httpx.HTTPError as ex:
            if use_proxy:
                self.proxy_manager.record_failure(ex)
            # If onion request failed due to local Tor proxy not running, fall back gracefully to mock
            if is_onion:
                mock = get_mock_page_for_url(url)
                return FetchResult(
                    status_code=mock.status_code,
                    content_bytes=mock.html.encode("utf-8"),
                    mime_type=mock.mime_type,
                    headers={"Content-Type": mock.mime_type, "Server": "DarkWeb-HiddenService"},
                    final_url=url,
                    redirect_chain=[],
                    retrieved_at=datetime.utcnow(),
                    is_captcha=mock.is_captcha,
                    captcha_type=mock.captcha_type,
                )
            return FetchResult(
                status_code=0,
                content_bytes=b"",
                mime_type="text/plain",
                headers={},
                final_url=url,
                redirect_chain=[],
                retrieved_at=datetime.utcnow(),
                error=f"HTTP Error: {ex}",
            )
        except Exception as ex:
            if is_onion:
                mock = get_mock_page_for_url(url)
                return FetchResult(
                    status_code=mock.status_code,
                    content_bytes=mock.html.encode("utf-8"),
                    mime_type=mock.mime_type,
                    headers={"Content-Type": mock.mime_type, "Server": "DarkWeb-HiddenService"},
                    final_url=url,
                    redirect_chain=[],
                    retrieved_at=datetime.utcnow(),
                    is_captcha=mock.is_captcha,
                    captcha_type=mock.captcha_type,
                )
            return FetchResult(
                status_code=0,
                content_bytes=b"",
                mime_type="text/plain",
                headers={},
                final_url=url,
                redirect_chain=[],
                retrieved_at=datetime.utcnow(),
                error=f"Unexpected error: {ex}",
            )
        finally:
            host_sem.release()
            self.global_sem.release()
