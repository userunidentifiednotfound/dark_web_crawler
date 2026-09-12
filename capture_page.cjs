#!/usr/bin/env node
/**
 * DWI Page Capture & Wait-Page Bypass CLI
 * Usage:
 *   node capture_page.js <URL> [options]
 *
 * Options:
 *   --output <dir>        Directory to save screenshot and raw HTML (default: ./captures)
 *   --no-bypass           Disable wait-page and interstitial bypass
 *   --no-scroll           Disable scrolling for lazy loaded components
 *   --viewport <WxH>      Viewport resolution (default: 1280x800)
 *   --timeout <ms>        Navigation timeout in ms (default: 30000)
 *   --json                Output results in JSON format
 */

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer-core');

function findChromeExecutable() {
  const baseDir = path.join(process.cwd(), 'chrome');
  function walk(dir) {
    if (!fs.existsSync(dir)) return null;
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          const found = walk(full);
          if (found) return found;
        } else if (entry.name === 'chrome' && (entry.isFile() || entry.isSymbolicLink())) {
          return full;
        }
      }
    } catch {}
    return null;
  }

  const local = walk(baseDir);
  if (local) return local;

  const candidates = [
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
  ];
  for (const c of candidates) {
    if (fs.existsSync(c)) return c;
  }
  throw new Error('Chrome binary not found in ./chrome or system paths.');
}

async function run() {
  const args = process.argv.slice(2);
  let targetUrl = null;
  let outDir = path.join(process.cwd(), 'captures');
  let bypassWait = true;
  let scrollLazy = true;
  let width = 1280;
  let height = 800;
  let timeoutMs = 30000;
  let waitTimeSec = 0;
  let asJson = false;

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--no-bypass') bypassWait = false;
    else if (arg === '--no-scroll') scrollLazy = false;
    else if (arg === '--json') asJson = true;
    else if (arg === '--output' && i + 1 < args.length) outDir = args[++i];
    else if (arg.startsWith('--output=')) outDir = arg.split('=')[1];
    else if (arg === '--wait-time' && i + 1 < args.length) waitTimeSec = parseInt(args[++i], 10) || 0;
    else if (arg.startsWith('--wait-time=')) waitTimeSec = parseInt(arg.split('=')[1], 10) || 0;
    else if (arg === '--viewport' && i + 1 < args.length) {
      const parts = args[++i].split('x').map(Number);
      if (parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1])) {
        width = parts[0];
        height = parts[1];
      }
    } else if (arg === '--timeout' && i + 1 < args.length) {
      timeoutMs = parseInt(args[++i], 10) || 30000;
    } else if (!arg.startsWith('-') && !targetUrl) {
      targetUrl = arg;
    }
  }

  if (!targetUrl) {
    console.error('Error: Please provide a target URL to capture.');
    console.log('Usage: node capture_page.js <URL> [--output <dir>] [--no-bypass] [--viewport 1920x1080] [--json]');
    process.exit(1);
  }

  if (!/^https?:\/\//i.test(targetUrl)) {
    targetUrl = 'https://' + targetUrl;
  }

  const chromePath = findChromeExecutable();
  if (!asJson) {
    console.log(`\x1b[1m\x1b[36m>>> DWI Page Capture & Wait-Page Bypass Engine\x1b[0m`);
    console.log(`\x1b[34mTarget URL:\x1b[0m       ${targetUrl}`);
    console.log(`\x1b[34mBypass Wait:\x1b[0m      ${bypassWait ? 'ENABLED (Auto-follow meta-refresh, timer wait, proceed click)' : 'DISABLED'}`);
    console.log(`\x1b[34mViewport:\x1b[0m         ${width}x${height}`);
    console.log(`\x1b[34mOutput Dir:\x1b[0m       ${outDir}\n`);
  }

  const startTime = Date.now();
  const actions = [];

  const launchArgs = [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',
    '--disable-gpu',
    '--disable-web-security',
    `--window-size=${width},${height}`,
  ];

  if (targetUrl.includes('.onion')) {
    launchArgs.push('--proxy-server=socks5://127.0.0.1:9050');
    actions.push('Routing via Tor SOCKS5 (127.0.0.1:9050)');
  }

  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: true,
    args: launchArgs,
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width, height });
    await page.setUserAgent(
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    );

    await page.evaluateOnNewDocument(`
      window.__name = function(fn) { return fn; };
      Object.defineProperty(navigator, 'webdriver', { get: function() { return false; } });
    `);

    let httpStatus = 200;
    try {
      const resp = await page.goto(targetUrl, {
        waitUntil: ['domcontentloaded', 'networkidle2'],
        timeout: Math.min(timeoutMs, 20000),
      });
      if (resp) httpStatus = resp.status();
      actions.push(`Navigation successful (HTTP ${httpStatus})`);
    } catch (e) {
      actions.push(`Navigation status: ${e.message.slice(0, 80)}`);
    }

    await page.evaluate(`window.__name = function(fn) { return fn; };`).catch(() => {});

    // Bypass wait pages
    if (bypassWait) {
      // 1. Meta refresh
      const meta = await page.evaluate(`
        (function() {
          var m = document.querySelector('meta[http-equiv="refresh" i]');
          if (m) {
            var c = m.getAttribute('content') || '';
            var u = c.match(/url=(.*)/i);
            return { delay: parseInt(c, 10) || 0, url: u ? u[1].trim() : null };
          }
          return null;
        })()
      `);

      if (meta && meta.url) {
        actions.push(`Followed meta-refresh (${meta.delay}s delay) -> ${meta.url}`);
        let resolved = meta.url;
        if (!resolved.startsWith('http')) resolved = new URL(resolved, page.url()).href;
        if (meta.delay > 0) {
          await new Promise((r) => setTimeout(r, Math.min(meta.delay, 10) * 1000));
        }
        await page.goto(resolved, { waitUntil: ['domcontentloaded', 'networkidle2'], timeout: 18000 }).catch(() => {});
        await page.evaluate(`window.__name = function(fn) { return fn; };`).catch(() => {});
      }

      // 2. Countdown / wait screen check with dynamic delay
      const timerAnalysis = await page.evaluate(`
        (function() {
          var text = document.body ? document.body.innerText : '';
          var hasWaitKeywords = /please\\s+wait|redirecting\\s+in|loading\\s+in|checking\\s+your\\s+browser|just\\s+a\\s+moment|ddos|challenge|wait\\s+\\d+\\s*s/i.test(text);
          var match = text.match(/(?:wait|redirecting in|loading in|checking your browser in)\\s*(?:for\\s*)?(\\d+)\\s*(?:s|sec|seconds)?/i) ||
                      text.match(/(\\d+)\\s*(?:seconds?|secs?)\\s*(?:remaining|left|to\\s+redirect)/i);
          var extractedSeconds = match ? parseInt(match[1], 10) : 0;
          var timerEl = document.querySelector('#countdown, .countdown, #timer, .timer, [id*="timer"], [class*="timer"]');
          if (timerEl && !extractedSeconds) {
            var num = parseInt(timerEl.textContent || '', 10);
            if (!isNaN(num) && num > 0 && num <= 60) extractedSeconds = num;
          }
          return {
            hasWait: hasWaitKeywords || !!timerEl || extractedSeconds > 0,
            seconds: extractedSeconds
          };
        })()
      `);

      let waitDurationMs = 0;
      if (waitTimeSec > 0) {
        waitDurationMs = waitTimeSec * 1000;
        actions.push(`Enforcing CLI wait delay (${waitTimeSec}s)...`);
      } else if (timerAnalysis && timerAnalysis.hasWait) {
        if (timerAnalysis.seconds > 0) {
          waitDurationMs = (Math.min(timerAnalysis.seconds, 20) + 1.5) * 1000;
          actions.push(`Detected dynamic countdown timer (${timerAnalysis.seconds}s). Waiting ${Math.round(waitDurationMs / 1000)}s...`);
        } else {
          waitDurationMs = 5000;
          actions.push('Detected interstitial/wait text. Waiting 5s for challenge settlement...');
        }
      }

      if (waitDurationMs > 0) {
        const navWait = page.waitForNavigation({ waitUntil: ['domcontentloaded', 'networkidle2'], timeout: waitDurationMs + 5000 }).catch(() => null);
        await Promise.race([navWait, new Promise((r) => setTimeout(r, waitDurationMs))]);
        await page.evaluate(`window.__name = function(fn) { return fn; };`).catch(() => {});
      }

      // 3. Auto-click Proceed / Continue buttons
      const clicked = await page.evaluate(`
        (function() {
          var els = Array.from(document.querySelectorAll('button, a, input[type="button"], input[type="submit"], [role="button"], span.btn, div.btn'));
          var p = [/proceed/i, /continue/i, /skip\\s+wait/i, /enter\\s+site/i, /access/i, /i\\s+agree/i, /accept/i];
          for (var i = 0; i < p.length; i++) {
            for (var j = 0; j < els.length; j++) {
              var el = els[j];
              var txt = (el.textContent || el.value || '').trim();
              if (p[i].test(txt)) {
                var r = el.getBoundingClientRect();
                if (r.width > 0 && r.height > 0) {
                  el.click();
                  return txt;
                }
              }
            }
          }
          return null;
        })()
      `);
      if (clicked) {
        actions.push(`Auto-clicked bypass button: "${clicked}"`);
        await Promise.race([
          page.waitForNavigation({ waitUntil: ['domcontentloaded', 'networkidle2'], timeout: 10000 }).catch(() => null),
          new Promise((r) => setTimeout(r, 3500))
        ]);
        await page.evaluate(`window.__name = function(fn) { return fn; };`).catch(() => {});
      }

      // 4. Dismiss blocking floating overlays safely
      await page.evaluate(`
        (function() {
          var sel = ['.modal-backdrop', '.interstitial-overlay', '#preloader', '.preloader', '[class*="loading-overlay"]'];
          var totalTextLen = document.body ? (document.body.innerText || '').length : 0;
          sel.forEach(function(s) {
            document.querySelectorAll(s).forEach(function(e) {
              var elTextLen = (e.innerText || '').length;
              if (totalTextLen > 0 && elTextLen >= totalTextLen * 0.5) return;
              var st = window.getComputedStyle ? window.getComputedStyle(e) : null;
              if (st && (st.position === 'fixed' || st.position === 'absolute')) {
                e.style.display = 'none';
              }
            });
          });
          if (document.body && document.body.style.overflow === 'hidden') {
            document.body.style.overflow = 'auto';
          }
        })()
      `).catch(() => {});
    }

    // 5. Blank body recovery guard
    let bodyState = await page.evaluate(`
      (function() {
        if (!document.body) return { isEmpty: true };
        var visibleChildren = Array.from(document.body.children).filter(function(el) {
          return el.tagName !== 'SCRIPT' && el.tagName !== 'STYLE' && el.tagName !== 'NOSCRIPT';
        });
        var text = (document.body.innerText || '').trim();
        return { isEmpty: visibleChildren.length === 0 && text.length === 0, count: visibleChildren.length };
      })()
    `).catch(() => ({ isEmpty: true, count: 0 }));

    if (bodyState.isEmpty) {
      actions.push('Detected blank body in transition; polling for DOM hydration...');
      for (let poll = 0; poll < 16; poll++) {
        await new Promise((r) => setTimeout(r, 500));
        bodyState = await page.evaluate(`
          (function() {
            if (!document.body) return { isEmpty: true };
            var visibleChildren = Array.from(document.body.children).filter(function(el) {
              return el.tagName !== 'SCRIPT' && el.tagName !== 'STYLE' && el.tagName !== 'NOSCRIPT';
            });
            var text = (document.body.innerText || '').trim();
            return { isEmpty: visibleChildren.length === 0 && text.length === 0, count: visibleChildren.length };
          })()
        `).catch(() => ({ isEmpty: true, count: 0 }));
        if (!bodyState.isEmpty) {
          actions.push(`DOM populated after ${((poll + 1) * 0.5).toFixed(1)}s wait`);
          break;
        }
      }
    }

    // Scroll for lazy load
    if (scrollLazy && !bodyState.isEmpty) {
      await page.evaluate(`
        new Promise(function(resolve) {
          var total = 0;
          var timer = setInterval(function() {
            window.scrollBy(0, 400);
            total += 400;
            if (total >= (document.body ? document.body.scrollHeight : 0) || total >= 8000) {
              clearInterval(timer);
              window.scrollTo(0, 0);
              resolve();
            }
          }, 80);
        })
      `).catch(() => {});
      actions.push('Auto-scrolled page to trigger lazy loading');
    }

    await new Promise((r) => setTimeout(r, 500));

    // 1. Full Page Screenshot
    if (!fs.existsSync(outDir)) {
      fs.mkdirSync(outDir, { recursive: true });
    }

    const cleanHost = new URL(page.url()).hostname.replace(/[^a-zA-Z0-9.-]/g, '_');
    const timestamp = Date.now();
    const screenshotFilename = `screenshot_${cleanHost}_${timestamp}.png`;
    const htmlFilename = `raw_${cleanHost}_${timestamp}.html`;

    const screenshotPath = path.join(outDir, screenshotFilename);
    const htmlPath = path.join(outDir, htmlFilename);

    await page.screenshot({ path: screenshotPath, fullPage: true });
    actions.push(`Screenshot saved: ${screenshotPath}`);

    // 2. Raw HTML Extraction
    const rawHtml = await page.content();
    fs.writeFileSync(htmlPath, rawHtml, 'utf8');
    actions.push(`Raw HTML saved: ${htmlPath} (${rawHtml.length} bytes)`);

    const title = await page.title();
    const finalUrl = page.url();
    const durationMs = Date.now() - startTime;

    if (asJson) {
      console.log(
        JSON.stringify(
          {
            success: true,
            url: targetUrl,
            final_url: finalUrl,
            title,
            http_status: httpStatus,
            duration_ms: durationMs,
            screenshot_path: screenshotPath,
            html_path: htmlPath,
            html_size_bytes: rawHtml.length,
            bypassed_actions: actions,
          },
          null,
          2
        )
      );
    } else {
      console.log(`\x1b[32m[✓] CAPTURE COMPLETED SUCCESSFULLY in ${durationMs}ms\x1b[0m`);
      console.log(`\x1b[1mTitle:\x1b[0m          ${title || 'Untitled'}`);
      console.log(`\x1b[1mFinal URL:\x1b[0m      ${finalUrl}`);
      console.log(`\x1b[1mStatus Code:\x1b[0m    ${httpStatus}`);
      console.log(`\x1b[1mScreenshot:\x1b[0m     \x1b[36m${screenshotPath}\x1b[0m`);
      console.log(`\x1b[1mRaw HTML:\x1b[0m       \x1b[36${htmlPath}\x1b[0m (${(rawHtml.length / 1024).toFixed(1)} KB)`);
      console.log(`\n\x1b[1mBypass & Execution Log:\x1b[0m`);
      actions.forEach((a, idx) => console.log(`  [${idx + 1}] ${a}`));
    }
  } catch (err) {
    console.error('\x1b[31m[!] Capture failed:\x1b[0m', err.message);
    process.exit(1);
  } finally {
    await browser.close().catch(() => {});
  }
}

run();
