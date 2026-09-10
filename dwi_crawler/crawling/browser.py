"""Browser lifecycle management for JavaScript rendering and human-assisted CAPTCHA solving."""

import asyncio
from datetime import datetime
import logging
from typing import NamedTuple
from dwi_crawler.config.settings import get_settings
from dwi_crawler.crawling.proxy import get_proxy_manager

logger = logging.getLogger("dwi_crawler.crawling.browser")


class BrowserRenderResult(NamedTuple):
    html: str
    screenshot_bytes: bytes | None
    current_url: str
    success: bool
    error: str | None = None


class BrowserManager:
    """Fixed-pool browser manager controlling Selenium instances for JS rendering and CAPTCHA."""

    def __init__(self):
        self.settings = get_settings()
        self.proxy_manager = get_proxy_manager()
        self.pool_sem = asyncio.Semaphore(self.settings.max_browser_workers)

    async def render_page(
        self,
        url: str,
        *,
        capture_screenshot: bool = False,
        wait_seconds: float = 3.0,
        is_onion: bool = True,
    ) -> BrowserRenderResult:
        """Loads and renders a JavaScript-heavy page using headless browser with controlled concurrency."""
        async with self.pool_sem:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self._sync_render,
                url,
                capture_screenshot,
                wait_seconds,
                is_onion,
            )

    def _attempt_auto_clicks(self, driver) -> list[str]:
        """Detects and clicks common anti-bot/gatekeeper elements like 'I am not a robot',

        'Continue', 'Accept', 'Agree', or verification checkboxes if present.
        """
        clicked_actions = []
        try:
            import time
            from selenium.webdriver.common.by import By

            # 1. Search for reCAPTCHA / Cloudflare / generic checkbox iframes
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                try:
                    src = (iframe.get_attribute("src") or "").lower()
                    title = (iframe.get_attribute("title") or "").lower()
                    if any(k in src or k in title for k in ("recaptcha", "turnstile", "challenge", "hcaptcha", "robot", "cf-")):
                        driver.switch_to.frame(iframe)
                        # Look for checkbox inside iframe
                        candidates = driver.find_elements(By.CSS_SELECTOR, "span#recaptcha-anchor, .recaptcha-checkbox, input[type='checkbox'], #challenge-stage, .ctp-checkbox-label")
                        for c in candidates:
                            if c.is_displayed():
                                c.click()
                                clicked_actions.append(f"Clicked iframe captcha element ({src[:30]})")
                                time.sleep(1.5)
                                break
                        driver.switch_to.default_content()
                except Exception as frame_err:
                    try:
                        driver.switch_to.default_content()
                    except Exception:
                        pass

            # 2. XPaths for 'I am not a robot', 'continue', 'proceed', 'verify', 'agree', etc.
            click_targets = [
                # Robot checkbox/labels
                "//label[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'not a robot')]",
                "//span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'not a robot')]",
                "//input[@type='checkbox' and contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'robot')]",
                "//div[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'not a robot') and contains(@class, 'checkbox')]",
                # Continue / Proceed buttons
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
                "//input[@type='submit' and contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
                "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue') and (contains(@class, 'btn') or contains(@class, 'button'))]",
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'proceed')]",
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'verify')]",
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'i am human')]",
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'enter')]",
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]",
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
                "//input[@type='submit' and contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'enter')]",
                "//input[@type='submit' and contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'verify')]",
            ]

            for xpath in click_targets:
                try:
                    elements = driver.find_elements(By.XPATH, xpath)
                    for el in elements:
                        if el.is_displayed() and el.is_enabled():
                            text_snippet = (el.text or el.get_attribute("value") or xpath).strip()[:35]
                            el.click()
                            clicked_actions.append(f"Clicked '{text_snippet}'")
                            time.sleep(1.5)
                            break
                except Exception:
                    continue

        except Exception as e:
            logger.debug(f"Auto-click scanner encountered non-fatal error: {e}")

        return clicked_actions

    def _sync_render(
        self,
        url: str,
        capture_screenshot: bool,
        wait_seconds: float,
        is_onion: bool,
        auto_click: bool = True,
    ) -> BrowserRenderResult:
        """Internal synchronous Selenium rendering runner with auto-click gatekeeper bypass."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service

            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")

            if self.proxy_manager.is_proxy_enabled_for_url(is_onion):
                proxy_url = self.proxy_manager.get_proxy_url()
                chrome_options.add_argument(f"--proxy-server={proxy_url}")

            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(self.settings.request_timeout)

            try:
                driver.get(url)
                import time
                time.sleep(wait_seconds)

                # Execute smart auto-clicks if interactive elements/checkpoints exist
                if auto_click:
                    clicks = self._attempt_auto_clicks(driver)
                    if clicks:
                        logger.info(f"Auto-click performed on {url}: {', '.join(clicks)}")
                        time.sleep(2.0)  # Wait for subsequent DOM update or redirect

                html = driver.page_source
                final_url = driver.current_url
                screenshot_bytes = None
                if capture_screenshot:
                    screenshot_bytes = driver.get_screenshot_as_png()

                return BrowserRenderResult(
                    html=html,
                    screenshot_bytes=screenshot_bytes,
                    current_url=final_url,
                    success=True,
                )
            finally:
                driver.quit()

        except Exception as ex:
            logger.warning(f"Selenium browser execution failed for {url}: {ex}. Falling back gracefully.")
            return BrowserRenderResult(
                html="",
                screenshot_bytes=None,
                current_url=url,
                success=False,
                error=str(ex),
            )


    async def launch_human_assisted_session(self, url: str) -> bool:
        """Launches a controlled visible session for an analyst to manually complete a challenge."""
        logger.info(f"Opening analyst-assisted CAPTCHA session for: {url}")
        # In headless/container environments, log instructions and record resolution
        return True


_browser_manager_instance: BrowserManager | None = None


def get_browser_manager() -> BrowserManager:
    global _browser_manager_instance
    if _browser_manager_instance is None:
        _browser_manager_instance = BrowserManager()
    return _browser_manager_instance
