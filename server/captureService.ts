import path from "path";
import fs from "fs";
import puppeteer, { Browser, Page } from "puppeteer-core";

export interface CaptureOptions {
  url: string;
  bypassWaitPages?: boolean;
  autoClickButtons?: boolean;
  removeOverlays?: boolean;
  scrollForLazyLoad?: boolean;
  timeoutMs?: number;
  viewportWidth?: number;
  viewportHeight?: number;
  customUserAgent?: string;
  proxyUrl?: string; // Optional custom proxy: e.g. "socks5://127.0.0.1:9050" or "http://proxy:8080"
  waitTimeSec?: number; // Configurable wait time (e.g., 5, 10, 15 seconds)
}

export interface CaptureResult {
  success: boolean;
  url: string;
  finalUrl: string;
  title: string;
  httpStatus: number;
  proxyEnabled: boolean;
  proxyUsed?: string;
  screenshotBase64: string; // PNG base64 string without data prefix
  rawHtml: string;
  htmlSizeBytes: number;
  durationMs: number;
  bypassedActions: string[];
  metadata: {
    description?: string;
    keywords?: string;
    favicon?: string;
    charset?: string;
    canonical?: string;
    scriptsCount: number;
    stylesheetsCount: number;
    linksCount: number;
    imagesCount: number;
    totalElements: number;
  };
  error?: string;
}

// Dynamically locate the installed Chrome binary
let cachedChromePath: string | null = null;

export function findChromeExecutable(): string {
  if (cachedChromePath && fs.existsSync(cachedChromePath)) {
    return cachedChromePath;
  }

  // Check local project chrome folder
  const baseDir = path.join(process.cwd(), "chrome");
  function walk(dir: string): string | null {
    if (!fs.existsSync(dir)) return null;
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          const found = walk(full);
          if (found) return found;
        } else if (entry.name === "chrome" && (entry.isFile() || entry.isSymbolicLink())) {
          return full;
        }
      }
    } catch {
      // ignore read error
    }
    return null;
  }

  const foundInLocal = walk(baseDir);
  if (foundInLocal) {
    cachedChromePath = foundInLocal;
    return foundInLocal;
  }

  // Fallback to standard system paths
  const systemCandidates = [
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/opt/google/chrome/chrome",
  ];

  for (const candidate of systemCandidates) {
    if (fs.existsSync(candidate)) {
      cachedChromePath = candidate;
      return candidate;
    }
  }

  throw new Error("Chrome binary could not be found. Please ensure Chrome is installed in ./chrome.");
}

export async function capturePageContent(options: CaptureOptions): Promise<CaptureResult> {
  const startTime = Date.now();
  const bypassedActions: string[] = [];
  
  let targetUrl = options.url.trim();
  if (!/^https?:\/\//i.test(targetUrl)) {
    targetUrl = `https://${targetUrl}`;
  }

  const chromePath = findChromeExecutable();
  const bypassWaitPages = options.bypassWaitPages !== false;
  const autoClickButtons = options.autoClickButtons !== false;
  const removeOverlays = options.removeOverlays !== false;
  const scrollForLazyLoad = options.scrollForLazyLoad !== false;
  const timeoutMs = options.timeoutMs || 30000;
  const width = options.viewportWidth || 1280;
  const height = options.viewportHeight || 800;

  const launchArgs = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-web-security",
    "--disable-features=IsolateOrigins,site-per-process",
    `--window-size=${width},${height}`,
  ];

  // Determine proxy routing:
  // 1. Explicit custom proxy option (e.g., socks5://127.0.0.1:9050 or http://proxy:port)
  // 2. Default SOCKS5 proxy (socks5://127.0.0.1:9050) when fetching .onion links
  let proxyConfigured: string | undefined = undefined;
  if (options.proxyUrl && options.proxyUrl.trim() && options.proxyUrl.trim() !== "direct") {
    proxyConfigured = options.proxyUrl.trim();
    launchArgs.push(`--proxy-server=${proxyConfigured}`);
    bypassedActions.push(`Proxy routed via custom gateway: ${proxyConfigured}`);
  } else if (targetUrl.includes(".onion")) {
    proxyConfigured = "socks5://127.0.0.1:9050";
    launchArgs.push(`--proxy-server=${proxyConfigured}`);
    bypassedActions.push(`Tor SOCKS5 gateway route configured for .onion hidden service (${proxyConfigured})`);
  } else {
    bypassedActions.push("Direct internet connection (No proxy enabled for standard surface web)");
  }

  let browser: Browser | null = null;
  try {
    browser = await puppeteer.launch({
      executablePath: chromePath,
      headless: true,
      args: launchArgs,
    });

    const page: Page = await browser.newPage();
    await page.setViewport({ width, height, deviceScaleFactor: 1 });

    const userAgent = options.customUserAgent || 
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36";
    await page.setUserAgent(userAgent);

    // Bypass navigator.webdriver detection and ensure __name helper is present for tsx/esbuild
    await page.evaluateOnNewDocument(`
      window.__name = function(fn) { return fn; };
      Object.defineProperty(navigator, 'webdriver', { get: function() { return false; } });
      window.chrome = { runtime: {} };
    `);

    let httpStatus = 200;
    try {
      const response = await page.goto(targetUrl, {
        waitUntil: ["domcontentloaded", "networkidle2"],
        timeout: Math.min(timeoutMs, 20000),
      });
      if (response) {
        httpStatus = response.status();
      }
      bypassedActions.push(`Initial page connection established (HTTP ${httpStatus})`);
    } catch (navErr: any) {
      bypassedActions.push(`Navigation notice: ${navErr.message?.slice(0, 80) || "Network stabilization wait"}`);
    }

    // Ensure __name helper exists on the loaded page context as well
    await page.evaluate(`window.__name = function(fn) { return fn; };`).catch(() => {});

    // -------------------------------------------------------------
    // WAIT PAGE & INTERSTITIAL BYPASS LOGIC
    // -------------------------------------------------------------
    if (bypassWaitPages) {
      // 1. Check for Meta-Refresh Redirect
      const metaRefresh = await page.evaluate(`
        (function() {
          var meta = document.querySelector('meta[http-equiv="refresh" i]');
          if (meta) {
            var content = meta.getAttribute('content') || '';
            var match = content.match(/url=(.*)/i);
            return {
              delay: parseInt(content, 10) || 0,
              targetUrl: match ? match[1].trim().replace(/^['"]|['"]$/g, '') : null
            };
          }
          return null;
        })()
      `) as { delay: number; targetUrl: string | null } | null;

      if (metaRefresh && metaRefresh.targetUrl) {
        bypassedActions.push(
          `Detected meta-refresh interstitial (${metaRefresh.delay}s delay). Following target: ${metaRefresh.targetUrl}`
        );
        try {
          let resolved = metaRefresh.targetUrl;
          if (!resolved.startsWith("http")) {
            resolved = new URL(resolved, page.url()).href;
          }
          if (metaRefresh.delay > 0) {
            const waitMs = Math.min(metaRefresh.delay, 10) * 1000;
            await new Promise((r) => setTimeout(r, waitMs));
          }
          await page.goto(resolved, { waitUntil: ["domcontentloaded", "networkidle2"], timeout: 18000 });
          await page.evaluate(`window.__name = function(fn) { return fn; };`).catch(() => {});
        } catch {
          // continue
        }
      }

      // 2. Interstitial Countdown / Security Check Timer Handling
      const timerAnalysis = await page.evaluate(`
        (function() {
          var text = document.body ? document.body.innerText : '';
          var hasWaitKeywords = /please\\s+wait|redirecting\\s+in|loading\\s+in|checking\\s+your\\s+browser|just\\s+a\\s+moment|ddos|challenge|security\\s+check|wait\\s+\\d+\\s*s/i.test(text);

          var match = text.match(/(?:wait|redirecting in|loading in|checking your browser in|standby|verifying)\\s*(?:for\\s*)?(\\d+)\\s*(?:s|sec|seconds)?/i) ||
                      text.match(/(\\d+)\\s*(?:seconds?|secs?)\\s*(?:remaining|left|to\\s+redirect)/i);
          var extractedSeconds = match ? parseInt(match[1], 10) : 0;

          var timerEl = document.querySelector('#countdown, .countdown, #timer, .timer, [id*="timer"], [class*="timer"], [id*="countdown"], [class*="countdown"]');
          if (timerEl && !extractedSeconds) {
            var num = parseInt(timerEl.textContent || '', 10);
            if (!isNaN(num) && num > 0 && num <= 60) {
              extractedSeconds = num;
            }
          }

          return {
            hasWait: hasWaitKeywords || !!timerEl || extractedSeconds > 0,
            seconds: extractedSeconds,
            hasTimerElement: !!timerEl
          };
        })()
      `) as { hasWait: boolean; seconds: number; hasTimerElement: boolean } | null;

      // Determine required wait duration
      let waitDurationMs = 0;
      if (options.waitTimeSec && options.waitTimeSec > 0) {
        waitDurationMs = Math.min(options.waitTimeSec, 30) * 1000;
        bypassedActions.push(`Enforcing wait delay (${options.waitTimeSec}s) for security/wait page transition...`);
      } else if (timerAnalysis && timerAnalysis.hasWait) {
        if (timerAnalysis.seconds > 0) {
          waitDurationMs = (Math.min(timerAnalysis.seconds, 20) + 1.5) * 1000;
          bypassedActions.push(`Detected dynamic countdown timer (${timerAnalysis.seconds}s). Waiting ${Math.round(waitDurationMs / 1000)}s for expiration...`);
        } else {
          // Standard security challenge/wait page default delay
          waitDurationMs = 5000;
          bypassedActions.push("Detected interstitial/security check page. Waiting 5s for challenge settlement...");
        }
      }

      if (waitDurationMs > 0) {
        // Wait while monitoring if navigation occurs
        const navWait = page.waitForNavigation({ waitUntil: ["domcontentloaded", "networkidle2"], timeout: waitDurationMs + 5000 }).catch(() => null);
        const sleepWait = new Promise((resolve) => setTimeout(resolve, waitDurationMs));
        await Promise.race([navWait, sleepWait]);
        await page.evaluate(`window.__name = function(fn) { return fn; };`).catch(() => {});
      }

      // 3. Auto-Click "Continue" / "Proceed" / "Enter Site" / "Skip" Buttons
      if (autoClickButtons) {
        const clickedButton = await page.evaluate(`
          (function() {
            var clickable = Array.from(document.querySelectorAll('button, a, input[type="button"], input[type="submit"], [role="button"], span.btn, div.btn'));
            var patterns = [
              /click\\s+(here\\s+)?to\\s+proceed/i,
              /proceed\\s+to\\s+site/i,
              /continue\\s+to/i,
              /skip\\s+wait/i,
              /skip\\s+ad/i,
              /enter\\s+site/i,
              /access\\s+website/i,
              /i\\s+understand/i,
              /i\\s+agree/i,
              /accept\\s+all/i,
              /continue/i,
              /proceed/i,
              /enter/i
            ];

            for (var i = 0; i < patterns.length; i++) {
              var pat = patterns[i];
              for (var j = 0; j < clickable.length; j++) {
                var el = clickable[j];
                var text = (el.textContent || el.value || '').trim();
                if (pat.test(text)) {
                  var rect = el.getBoundingClientRect();
                  if (rect.width > 0 && rect.height > 0) {
                    el.click();
                    return text;
                  }
                }
              }
            }
            return null;
          })()
        `) as string | null;

        if (clickedButton) {
          bypassedActions.push(`Auto-clicked interstitial bypass button: "${clickedButton}"`);
          // Wait for post-click navigation or DOM mutation
          await Promise.race([
            page.waitForNavigation({ waitUntil: ["domcontentloaded", "networkidle2"], timeout: 12000 }).catch(() => null),
            new Promise((resolve) => setTimeout(resolve, 3500))
          ]);
          await page.evaluate(`window.__name = function(fn) { return fn; };`).catch(() => {});
        }
      }

      // 4. Remove Blocking Overlays / Fullscreen Spinners (Safe Guarded)
      if (removeOverlays) {
        const removedCount = await page.evaluate(`
          (function() {
            var count = 0;
            var overlaySelectors = [
              '.modal-backdrop',
              '.interstitial-overlay',
              '[class*="loading-overlay"]',
              '[class*="splash-screen"]',
              '#preloader',
              '.preloader',
              '[id*="wait-gate"]',
              '.veil'
            ];

            var totalTextLen = document.body ? (document.body.innerText || '').length : 0;

            for (var i = 0; i < overlaySelectors.length; i++) {
              var els = document.querySelectorAll(overlaySelectors[i]);
              for (var j = 0; j < els.length; j++) {
                var el = els[j];
                // Safety check: Never hide elements containing majority text
                var elTextLen = (el.innerText || '').length;
                if (totalTextLen > 0 && elTextLen >= totalTextLen * 0.5) {
                  continue;
                }
                var style = window.getComputedStyle ? window.getComputedStyle(el) : null;
                var isFloating = style && (style.position === 'fixed' || style.position === 'absolute');
                if (isFloating || el.classList.contains('modal-backdrop') || el.classList.contains('veil')) {
                  el.style.display = 'none';
                  count++;
                }
              }
            }

            // Only override body overflow if it was explicitly locked to hidden
            if (document.body) {
              var currOverflow = document.body.style.overflow;
              if (currOverflow === 'hidden') {
                document.body.style.overflow = 'auto';
              }
            }
            return count;
          })()
        `) as number;

        if (removedCount > 0) {
          bypassedActions.push(`Dismissed ${removedCount} blocking floating overlay element(s)`);
        }
      }
    }

    // -------------------------------------------------------------
    // 5. BLANK BODY RECOVERY GUARD
    // Prevents returning empty transition states like <html><head></head><body style="overflow: auto;"></body></html>
    // -------------------------------------------------------------
    let bodyState = await page.evaluate(`
      (function() {
        if (!document.body) return { isEmpty: true, childCount: 0, textLength: 0 };
        var visibleChildren = Array.from(document.body.children).filter(function(el) {
          return el.tagName !== 'SCRIPT' && el.tagName !== 'STYLE' && el.tagName !== 'NOSCRIPT';
        });
        var text = (document.body.innerText || '').trim();
        return {
          isEmpty: visibleChildren.length === 0 && text.length === 0,
          childCount: visibleChildren.length,
          textLength: text.length
        };
      })()
    `).catch(() => ({ isEmpty: true, childCount: 0, textLength: 0 })) as {
      isEmpty: boolean;
      childCount: number;
      textLength: number;
    };

    if (bodyState.isEmpty) {
      bypassedActions.push("Notice: Detected blank body in transition state. Polling for page hydration and redirect completion...");
      const maxPolls = 20; // up to 10 seconds (20 * 500ms)
      for (let poll = 0; poll < maxPolls; poll++) {
        await new Promise((resolve) => setTimeout(resolve, 500));
        bodyState = await (page.evaluate(`
          (function() {
            if (!document.body) return { isEmpty: true, childCount: 0, textLength: 0 };
            var visibleChildren = Array.from(document.body.children).filter(function(el) {
              return el.tagName !== 'SCRIPT' && el.tagName !== 'STYLE' && el.tagName !== 'NOSCRIPT';
            });
            var text = (document.body.innerText || '').trim();
            return {
              isEmpty: visibleChildren.length === 0 && text.length === 0,
              childCount: visibleChildren.length,
              textLength: text.length
            };
          })()
        `).catch(() => ({ isEmpty: true, childCount: 0, textLength: 0 })) as Promise<{
          isEmpty: boolean;
          childCount: number;
          textLength: number;
        }>);

        if (!bodyState.isEmpty) {
          bypassedActions.push(`Page body resolved after ${((poll + 1) * 0.5).toFixed(1)}s (${bodyState.childCount} elements, ${bodyState.textLength} chars)`);
          break;
        }
      }

      // Check if page rendered inside an iframe
      if (bodyState.isEmpty) {
        const iframeCount = (await page.evaluate(`document.querySelectorAll('iframe').length`).catch(() => 0) as number) || 0;
        if (iframeCount > 0) {
          bypassedActions.push(`Found ${iframeCount} iframe(s) in empty parent frame; waiting for frame stabilization`);
          await new Promise((resolve) => setTimeout(resolve, 2000));
        }
      }
    }

    // -------------------------------------------------------------
    // SCROLL TO TRIGGER LAZY-LOADED SECTIONS
    // -------------------------------------------------------------
    if (scrollForLazyLoad && !bodyState.isEmpty) {
      const scrollHeight = await page.evaluate(`
        new Promise(function(resolve) {
          var totalHeight = 0;
          var distance = 400;
          var maxScroll = 12000;
          var timer = setInterval(function() {
            var bodyHeight = document.body ? document.body.scrollHeight : 0;
            window.scrollBy(0, distance);
            totalHeight += distance;
            if (totalHeight >= bodyHeight || totalHeight >= maxScroll) {
              clearInterval(timer);
              window.scrollTo(0, 0);
              resolve(bodyHeight);
            }
          }, 80);
        })
      `).catch(() => 0) as number;
      if (scrollHeight > 0) {
        bypassedActions.push(`Auto-scrolled page (${scrollHeight}px document height) to render lazy-loaded components`);
      }
    }

    // Brief stabilization delay
    await new Promise((resolve) => setTimeout(resolve, 500));

    // -------------------------------------------------------------
    // EXTRACT 1: ENTIRE PAGE SCREENSHOT
    // -------------------------------------------------------------
    const screenshotBuffer = await page.screenshot({
      fullPage: true,
      encoding: "base64",
      type: "png",
    });
    bypassedActions.push("Captured full-page high-resolution screenshot");

    // -------------------------------------------------------------
    // EXTRACT 2: RAW HTML & RICH METADATA
    // -------------------------------------------------------------
    const rawHtml = await page.content();
    const finalUrl = page.url();
    const pageTitle = (await page.title()) || "Untitled Document";

    const extractedMeta = await page.evaluate(`
      (function() {
        var getMeta = function(name) {
          var tag = document.querySelector('meta[name="' + name + '" i]') ||
                    document.querySelector('meta[property="' + name + '" i]');
          return tag ? tag.getAttribute('content') || undefined : undefined;
        };

        var faviconTag = document.querySelector('link[rel*="icon"]') ||
                         document.querySelector('link[rel="shortcut icon"]');

        var canonicalTag = document.querySelector('link[rel="canonical"]');

        return {
          description: getMeta('description') || getMeta('og:description'),
          keywords: getMeta('keywords'),
          favicon: faviconTag ? faviconTag.getAttribute('href') || undefined : undefined,
          charset: document.characterSet || 'UTF-8',
          canonical: canonicalTag ? canonicalTag.getAttribute('href') || undefined : undefined,
          scriptsCount: document.querySelectorAll('script').length,
          stylesheetsCount: document.querySelectorAll('link[rel="stylesheet"]').length,
          linksCount: document.querySelectorAll('a[href]').length,
          imagesCount: document.querySelectorAll('img').length,
          totalElements: document.querySelectorAll('*').length,
        };
      })()
    `) as any;

    const durationMs = Date.now() - startTime;

    return {
      success: true,
      url: targetUrl,
      finalUrl,
      title: pageTitle,
      httpStatus,
      proxyEnabled: Boolean(proxyConfigured),
      proxyUsed: proxyConfigured,
      screenshotBase64: screenshotBuffer as string,
      rawHtml,
      htmlSizeBytes: Buffer.byteLength(rawHtml, "utf8"),
      durationMs,
      bypassedActions,
      metadata: extractedMeta,
    };
  } catch (err: any) {
    const durationMs = Date.now() - startTime;
    return {
      success: false,
      url: targetUrl,
      finalUrl: targetUrl,
      title: "Capture Error",
      httpStatus: 500,
      proxyEnabled: Boolean(proxyConfigured),
      proxyUsed: proxyConfigured,
      screenshotBase64: "",
      rawHtml: `<!-- Page capture failed: ${err.message || err} -->`,
      htmlSizeBytes: 0,
      durationMs,
      bypassedActions,
      metadata: {
        scriptsCount: 0,
        stylesheetsCount: 0,
        linksCount: 0,
        imagesCount: 0,
        totalElements: 0,
      },
      error: err.message || "Failed to capture page",
    };
  } finally {
    if (browser) {
      await browser.close().catch(() => {});
    }
  }
}
