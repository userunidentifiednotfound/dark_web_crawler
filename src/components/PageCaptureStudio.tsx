import React, { useState, useEffect, useRef } from 'react';
import {
  Camera,
  FileCode2,
  Globe2,
  Search,
  Download,
  Copy,
  Check,
  RefreshCw,
  FastForward,
  ZoomIn,
  ZoomOut,
  Maximize2,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Sliders,
  Sparkles,
  ExternalLink,
  ChevronDown,
  Clock,
  ShieldCheck,
  CornerDownRight,
  Monitor,
  Laptop,
  Smartphone,
  Info,
  Network,
  Radio
} from 'lucide-react';
import { CaptureResponse, CaptureHistoryRecord } from '../types';

const SAMPLE_LINKS = [
  { label: 'Example Domain', url: 'https://example.com', desc: 'Standard clean HTML' },
  { label: 'HttpBin HTML', url: 'https://httpbin.org/html', desc: 'Semantic HTML markup' },
  { label: 'Wikipedia Main', url: 'https://en.wikipedia.org/wiki/Main_Page', desc: 'Rich dynamic DOM' },
];

export function PageCaptureStudio() {
  const [urlInput, setUrlInput] = useState<string>('https://example.com');
  const [bypassWaitPages, setBypassWaitPages] = useState<boolean>(true);
  const [autoClickButtons, setAutoClickButtons] = useState<boolean>(true);
  const [removeOverlays, setRemoveOverlays] = useState<boolean>(true);
  const [scrollForLazyLoad, setScrollForLazyLoad] = useState<boolean>(true);
  const [viewportPreset, setViewportPreset] = useState<'desktop' | 'standard' | 'mobile'>('standard');
  const [proxyMode, setProxyMode] = useState<'auto' | 'socks5' | 'direct' | 'custom'>('auto');
  const [customProxyUrl, setCustomProxyUrl] = useState<string>('socks5://127.0.0.1:9050');
  const [waitTimeSec, setWaitTimeSec] = useState<number>(0);
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);

  const [loading, setLoading] = useState<boolean>(false);
  const [captureData, setCaptureData] = useState<CaptureResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  
  // Output view tab: 'screenshot' | 'html' | 'telemetry'
  const [activeTab, setActiveTab] = useState<'screenshot' | 'html' | 'telemetry'>('screenshot');
  
  // Screenshot zoom & controls
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [copiedHtml, setCopiedHtml] = useState<boolean>(false);
  const [copiedUrl, setCopiedUrl] = useState<boolean>(false);
  const [htmlSearchQuery, setHtmlSearchQuery] = useState<string>('');
  
  // Recent captures from API
  const [history, setHistory] = useState<CaptureHistoryRecord[]>([]);

  // Fetch capture history on load
  const fetchHistory = async () => {
    try {
      const res = await fetch('/api/capture/history');
      const data = await res.json();
      if (data.status === 'success' && Array.isArray(data.history)) {
        setHistory(data.history);
      }
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleCapture = async (targetOverrideUrl?: string) => {
    const target = targetOverrideUrl || urlInput;
    if (!target || !target.trim()) {
      setErrorMsg('Please enter a valid website link.');
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    setZoomLevel(1);

    const dims = 
      viewportPreset === 'desktop' ? { width: 1920, height: 1080 } :
      viewportPreset === 'mobile' ? { width: 390, height: 844 } :
      { width: 1280, height: 800 };

    // Determine proxy argument
    let proxyArgument: string | undefined = undefined;
    if (proxyMode === 'socks5') {
      proxyArgument = 'socks5://127.0.0.1:9050';
    } else if (proxyMode === 'direct') {
      proxyArgument = 'direct';
    } else if (proxyMode === 'custom') {
      proxyArgument = customProxyUrl.trim() || undefined;
    } // 'auto' leaves proxyArgument undefined so the server chooses socks5 for .onion, and direct for surface web

    try {
      const res = await fetch('/api/capture', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: target.trim(),
          bypassWaitPages,
          autoClickButtons,
          removeOverlays,
          scrollForLazyLoad,
          viewportWidth: dims.width,
          viewportHeight: dims.height,
          proxyUrl: proxyArgument,
          waitTimeSec: Number(waitTimeSec) || 0,
        }),
      });

      const data: CaptureResponse = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.error || 'Failed to capture the requested page.');
      }

      setCaptureData(data);
      fetchHistory();
    } catch (err: any) {
      setErrorMsg(err.message || 'Capture failed. Verify the URL is reachable.');
    } finally {
      setLoading(false);
    }
  };

  // Download screenshot as PNG file
  const downloadScreenshot = () => {
    if (!captureData?.screenshotBase64) return;
    const link = document.createElement('a');
    link.href = `data:image/png;base64,${captureData.screenshotBase64}`;
    const cleanName = captureData.title ? captureData.title.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 30) : 'page_screenshot';
    link.download = `${cleanName}_full_screenshot.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Download raw HTML as .html file
  const downloadHtml = () => {
    if (!captureData?.rawHtml) return;
    const blob = new Blob([captureData.rawHtml], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const cleanName = captureData.title ? captureData.title.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 30) : 'page_source';
    link.download = `${cleanName}_raw.html`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Copy HTML to clipboard
  const copyRawHtml = () => {
    if (!captureData?.rawHtml) return;
    navigator.clipboard.writeText(captureData.rawHtml);
    setCopiedHtml(true);
    setTimeout(() => setCopiedHtml(false), 2000);
  };

  // Filter or match lines in HTML
  const getFilteredHtmlLines = () => {
    if (!captureData?.rawHtml) return [];
    const lines = captureData.rawHtml.split('\n');
    if (!htmlSearchQuery.trim()) return lines;
    const q = htmlSearchQuery.toLowerCase();
    return lines.filter((line) => line.toLowerCase().includes(q));
  };

  const filteredLines = getFilteredHtmlLines();

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-6 shadow-2xl relative overflow-hidden" id="page-capture-studio">
      <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-5 border-b border-slate-800/80 relative z-10">
        <div className="flex items-center gap-3">
          <div className="h-11 w-11 rounded-xl bg-cyan-500/15 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-inner">
            <Camera className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-xl font-bold text-white tracking-tight">Live Page Capture &amp; Wait-Page Bypass</h2>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-semibold">
                Entire Page Screenshot
              </span>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 font-semibold">
                Raw HTML Extraction
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Input any URL to bypass intermediate wait gates, auto-follow meta-refreshes, take full-page screenshot, and extract raw DOM source
            </p>
          </div>
        </div>

        {/* Quick Sample Links */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[11px] font-mono text-slate-500 uppercase">Quick Test:</span>
          {SAMPLE_LINKS.map((sample, idx) => (
            <button
              key={idx}
              onClick={() => {
                setUrlInput(sample.url);
                handleCapture(sample.url);
              }}
              disabled={loading}
              className="text-xs font-mono bg-slate-950 hover:bg-slate-800 border border-slate-800 text-cyan-300 hover:text-cyan-200 px-2.5 py-1 rounded-lg transition disabled:opacity-50"
            >
              {sample.label}
            </button>
          ))}
        </div>
      </div>

      {/* URL Input Bar & Controls */}
      <div className="space-y-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleCapture();
          }}
          className="flex flex-col sm:flex-row gap-3"
        >
          <div className="relative flex-1">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
              <Globe2 className="h-4 w-4 text-cyan-400" />
            </div>
            <input
              type="text"
              required
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder="Enter web link (e.g. https://domain.com or onion link)..."
              className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-xl pl-10 pr-4 py-3 text-sm font-mono text-white placeholder-slate-600 focus:outline-none transition shadow-inner"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold px-6 py-3 rounded-xl text-sm flex items-center justify-center gap-2 transition disabled:opacity-50 shadow-lg shadow-cyan-500/10 cursor-pointer flex-shrink-0"
          >
            {loading ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin text-slate-950" />
                <span>Bypassing &amp; Capturing...</span>
              </>
            ) : (
              <>
                <Camera className="h-4 w-4" />
                <span>Capture Page Content</span>
              </>
            )}
          </button>
        </form>

        {/* Feature Switches & Bypass Settings Bar */}
        <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-3.5 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex flex-wrap items-center gap-3 sm:gap-5">
            <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-white select-none">
              <input
                type="checkbox"
                checked={bypassWaitPages}
                onChange={(e) => setBypassWaitPages(e.target.checked)}
                className="rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-0 h-4 w-4"
              />
              <span className="font-medium flex items-center gap-1.5">
                <FastForward className="h-3.5 w-3.5 text-amber-400" />
                Bypass Wait Screens &amp; Timers
              </span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-white select-none">
              <input
                type="checkbox"
                checked={autoClickButtons}
                onChange={(e) => setAutoClickButtons(e.target.checked)}
                className="rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-0 h-4 w-4"
              />
              <span className="font-medium flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
                Auto-Click "Proceed / Continue"
              </span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-white select-none">
              <input
                type="checkbox"
                checked={removeOverlays}
                onChange={(e) => setRemoveOverlays(e.target.checked)}
                className="rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-0 h-4 w-4"
              />
              <span className="font-medium flex items-center gap-1.5">
                <Layers className="h-3.5 w-3.5 text-indigo-400" />
                Dismiss Blocking Overlays
              </span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer text-slate-300 hover:text-white select-none">
              <input
                type="checkbox"
                checked={scrollForLazyLoad}
                onChange={(e) => setScrollForLazyLoad(e.target.checked)}
                className="rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-0 h-4 w-4"
              />
              <span className="font-medium flex items-center gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                Full-Page Lazy Scroll
              </span>
            </label>
          </div>

          {/* Viewport Presets & Proxy Gateway Mode */}
          <div className="flex items-center gap-2 flex-wrap">
            {/* Proxy Selector Control */}
            <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 px-2 py-1 rounded-lg">
              <Network className="h-3.5 w-3.5 text-cyan-400" />
              <span className="text-[11px] font-mono text-slate-400">Proxy:</span>
              <select
                value={proxyMode}
                onChange={(e) => setProxyMode(e.target.value as any)}
                className="bg-slate-950 border border-slate-800 text-xs font-mono text-cyan-300 rounded px-2 py-0.5 focus:outline-none focus:border-cyan-500 cursor-pointer"
                title="Configure proxy routing when fetching the page"
              >
                <option value="auto">Auto (Tor SOCKS5 for .onion, Direct for Surface)</option>
                <option value="socks5">Enforce Tor SOCKS5 (127.0.0.1:9050)</option>
                <option value="direct">Direct Connection (No Proxy)</option>
                <option value="custom">Custom Proxy Gateway</option>
              </select>
            </div>

            {proxyMode === 'custom' && (
              <input
                type="text"
                value={customProxyUrl}
                onChange={(e) => setCustomProxyUrl(e.target.value)}
                placeholder="e.g. socks5://127.0.0.1:9050 or http://proxy:8080"
                className="bg-slate-950 border border-slate-800 text-xs font-mono text-white px-2.5 py-1 rounded-lg focus:outline-none focus:border-cyan-500"
              />
            )}

            {/* Wait Delay Selector (Solves Blank Pages / DDOS Countdown Interstitials) */}
            <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 px-2 py-1 rounded-lg">
              <Clock className="h-3.5 w-3.5 text-amber-400" />
              <span className="text-[11px] font-mono text-slate-400">Wait Delay:</span>
              <select
                value={waitTimeSec}
                onChange={(e) => setWaitTimeSec(Number(e.target.value))}
                className="bg-slate-950 border border-slate-800 text-xs font-mono text-amber-300 rounded px-2 py-0.5 focus:outline-none focus:border-amber-500 cursor-pointer"
                title="Configurable delay for interstitial countdowns or security challenge gates (DDoS-GUARD, Cloudflare, etc.)"
              >
                <option value={0}>Auto-Detect (Adaptive Countdown)</option>
                <option value={3}>3s (Fast Interstitial)</option>
                <option value={5}>5s (Standard Challenge / DDOS)</option>
                <option value={10}>10s (Heavy Gateway / Countdown)</option>
                <option value={15}>15s (Extended Onion Delay)</option>
              </select>
            </div>

            {/* Viewport Presets */}
            <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 p-1 rounded-lg">
              <button
                onClick={() => setViewportPreset('standard')}
                className={`px-2.5 py-1 rounded text-[11px] font-mono flex items-center gap-1 transition ${
                  viewportPreset === 'standard' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' : 'text-slate-400 hover:text-white'
                }`}
                title="Standard Viewport: 1280x800"
              >
                <Laptop className="h-3 w-3" />
                <span>1280px</span>
              </button>
              <button
                onClick={() => setViewportPreset('desktop')}
                className={`px-2.5 py-1 rounded text-[11px] font-mono flex items-center gap-1 transition ${
                  viewportPreset === 'desktop' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' : 'text-slate-400 hover:text-white'
                }`}
                title="Desktop 1080p: 1920x1080"
              >
                <Monitor className="h-3 w-3" />
                <span>1920px</span>
              </button>
              <button
                onClick={() => setViewportPreset('mobile')}
                className={`px-2.5 py-1 rounded text-[11px] font-mono flex items-center gap-1 transition ${
                  viewportPreset === 'mobile' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' : 'text-slate-400 hover:text-white'
                }`}
                title="Mobile Viewport: 390x844"
              >
                <Smartphone className="h-3 w-3" />
                <span>Mobile</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Error Notice */}
      {errorMsg && (
        <div className="p-4 bg-red-950/40 border border-red-800/80 rounded-xl text-xs text-red-300 flex items-start gap-2.5">
          <AlertTriangle className="h-4 w-4 text-red-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-semibold">Capture Encountered An Error:</span>
            <p className="text-red-300/90">{errorMsg}</p>
          </div>
        </div>
      )}

      {/* Loading Progress Feedback */}
      {loading && (
        <div className="p-8 bg-slate-950/80 border border-cyan-500/30 rounded-2xl flex flex-col items-center justify-center text-center space-y-4">
          <div className="relative">
            <div className="h-16 w-16 rounded-full border-2 border-cyan-500/20 border-t-cyan-400 animate-spin" />
            <Camera className="h-6 w-6 text-cyan-400 absolute inset-0 m-auto animate-pulse" />
          </div>
          <div className="space-y-1">
            <h4 className="text-base font-bold text-white">Capturing Content from Link...</h4>
            <p className="text-xs text-slate-400 max-w-md">
              Connecting to <span className="font-mono text-cyan-300">{urlInput}</span>, evaluating wait-page countdowns, auto-clicking continue gates, and compiling full screenshot &amp; raw HTML.
            </p>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* CAPTURED OUTPUT DISPLAY (SCREENSHOT + RAW HTML + TELEMETRY)   */}
      {/* ------------------------------------------------------------- */}
      {captureData && !loading && (
        <div className="space-y-4">
          {/* Top Summary Bar */}
          <div className="bg-slate-950 border border-slate-800/90 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-bold">
                  HTTP {captureData.httpStatus}
                </span>
                <h3 className="text-base font-bold text-white truncate max-w-lg">
                  {captureData.title || 'Untitled Document'}
                </h3>
              </div>
              <div className="flex items-center gap-2 text-xs font-mono text-slate-400 truncate">
                <CornerDownRight className="h-3 w-3 text-cyan-400 flex-shrink-0" />
                <span className="truncate">{captureData.finalUrl}</span>
                {captureData.finalUrl !== captureData.url && (
                  <span className="text-[10px] text-amber-400 bg-amber-950/60 px-1.5 py-0.2 rounded border border-amber-800/40">
                    Redirected / Bypassed
                  </span>
                )}
              </div>
            </div>

            {/* Quick Metrics */}
            <div className="flex items-center gap-3 flex-wrap">
              {/* Proxy Route Chip */}
              <div className="text-right">
                <div className="text-[10px] font-mono text-slate-500 uppercase">Proxy Route</div>
                <div className="text-xs font-bold font-mono flex items-center gap-1 justify-end">
                  {captureData.proxyEnabled ? (
                    <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                      <Network className="h-3 w-3" />
                      <span>{captureData.proxyUsed?.includes('9050') ? 'Tor SOCKS5' : 'Proxy Active'}</span>
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800 flex items-center gap-1">
                      <Radio className="h-3 w-3 text-slate-500" />
                      <span>Direct (No Proxy)</span>
                    </span>
                  )}
                </div>
              </div>

              <div className="text-right">
                <div className="text-[10px] font-mono text-slate-500 uppercase">Load Time</div>
                <div className="text-xs font-bold text-white font-mono flex items-center gap-1 justify-end">
                  <Clock className="h-3 w-3 text-cyan-400" />
                  {captureData.durationMs}ms
                </div>
              </div>
              <div className="text-right">
                <div className="text-[10px] font-mono text-slate-500 uppercase">HTML Size</div>
                <div className="text-xs font-bold text-white font-mono">
                  {(captureData.htmlSizeBytes / 1024).toFixed(1)} KB
                </div>
              </div>
              <div className="text-right">
                <div className="text-[10px] font-mono text-slate-500 uppercase">DOM Elements</div>
                <div className="text-xs font-bold text-cyan-300 font-mono">
                  {captureData.metadata.totalElements} tags
                </div>
              </div>
            </div>
          </div>

          {/* Sparse/Blank DOM or Wait Page Detection Banner */}
          {(captureData.metadata.totalElements <= 5 || captureData.rawHtml.includes('<body style="overflow: auto;"></body>') || captureData.htmlSizeBytes < 250) && (
            <div className="bg-amber-950/40 border border-amber-500/40 rounded-xl p-3.5 flex items-start gap-3 text-xs text-amber-200 shadow-sm">
              <AlertTriangle className="h-4 w-4 text-amber-400 mt-0.5 flex-shrink-0" />
              <div className="space-y-1.5 flex-1">
                <p className="font-semibold text-amber-300">
                  Minimal or Empty DOM Detected ({captureData.metadata.totalElements} tags, {(captureData.htmlSizeBytes / 1024).toFixed(2)} KB)
                </p>
                <p className="text-slate-300 text-[11px] leading-relaxed">
                  This page likely uses an interstitial security check or countdown wait screen (e.g. Cloudflare, DDoS-GUARD, or Tor onion gateway). If the initial pass settled too quickly, click below to re-fetch with an extended wait delay.
                </p>
                <div className="pt-1 flex items-center gap-2 flex-wrap">
                  <button
                    onClick={() => {
                      setWaitTimeSec(5);
                      handleCapture();
                    }}
                    className="px-2.5 py-1 bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-300 rounded font-mono text-[11px] flex items-center gap-1.5 transition cursor-pointer"
                  >
                    <Clock className="h-3 w-3" />
                    <span>Retry with 5s Wait Delay</span>
                  </button>
                  <button
                    onClick={() => {
                      setWaitTimeSec(10);
                      handleCapture();
                    }}
                    className="px-2.5 py-1 bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-300 rounded font-mono text-[11px] flex items-center gap-1.5 transition cursor-pointer"
                  >
                    <Clock className="h-3 w-3" />
                    <span>Retry with 10s Wait Delay</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Navigation Tabs between Screenshot and Raw HTML */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-2">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab('screenshot')}
                className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition cursor-pointer ${
                  activeTab === 'screenshot'
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <Camera className="h-4 w-4" />
                <span>Entire Page Screenshot</span>
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-cyan-950 border border-cyan-800 text-cyan-400">
                  PNG
                </span>
              </button>

              <button
                onClick={() => setActiveTab('html')}
                className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition cursor-pointer ${
                  activeTab === 'html'
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <FileCode2 className="h-4 w-4" />
                <span>Extracted Raw HTML</span>
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-emerald-950 border border-emerald-800 text-emerald-400">
                  {(captureData.htmlSizeBytes / 1024).toFixed(1)} KB
                </span>
              </button>

              <button
                onClick={() => setActiveTab('telemetry')}
                className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition cursor-pointer ${
                  activeTab === 'telemetry'
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <FastForward className="h-4 w-4" />
                <span>Bypass Audit ({captureData.bypassedActions.length})</span>
              </button>
            </div>

            {/* Action Buttons for active view */}
            <div className="flex items-center gap-2">
              {activeTab === 'screenshot' && (
                <>
                  <div className="flex items-center gap-1 bg-slate-950 border border-slate-800 px-2 py-1 rounded-lg">
                    <button
                      onClick={() => setZoomLevel((z) => Math.max(0.5, z - 0.25))}
                      className="p-1 text-slate-400 hover:text-white transition"
                      title="Zoom Out"
                    >
                      <ZoomOut className="h-3.5 w-3.5" />
                    </button>
                    <span className="text-[11px] font-mono text-slate-300 w-12 text-center">
                      {Math.round(zoomLevel * 100)}%
                    </span>
                    <button
                      onClick={() => setZoomLevel((z) => Math.min(2.5, z + 0.25))}
                      className="p-1 text-slate-400 hover:text-white transition"
                      title="Zoom In"
                    >
                      <ZoomIn className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => setZoomLevel(1)}
                      className="p-1 text-slate-400 hover:text-white transition text-[10px] font-mono"
                      title="Reset Zoom"
                    >
                      Reset
                    </button>
                  </div>

                  <button
                    onClick={downloadScreenshot}
                    className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold px-3 py-1.5 rounded-lg text-xs flex items-center gap-1.5 transition shadow cursor-pointer"
                  >
                    <Download className="h-3.5 w-3.5" />
                    <span>Download Screenshot (.PNG)</span>
                  </button>
                </>
              )}

              {activeTab === 'html' && (
                <>
                  <button
                    onClick={copyRawHtml}
                    className="bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-200 hover:text-white px-3 py-1.5 rounded-lg text-xs font-mono flex items-center gap-1.5 transition cursor-pointer"
                  >
                    {copiedHtml ? (
                      <>
                        <Check className="h-3.5 w-3.5 text-emerald-400" />
                        <span className="text-emerald-400">Copied HTML</span>
                      </>
                    ) : (
                      <>
                        <Copy className="h-3.5 w-3.5" />
                        <span>Copy HTML</span>
                      </>
                    )}
                  </button>

                  <button
                    onClick={downloadHtml}
                    className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold px-3 py-1.5 rounded-lg text-xs flex items-center gap-1.5 transition shadow cursor-pointer"
                  >
                    <Download className="h-3.5 w-3.5" />
                    <span>Download .html</span>
                  </button>
                </>
              )}
            </div>
          </div>

          {/* TAB 1: ENTIRE PAGE SCREENSHOT */}
          {activeTab === 'screenshot' && (
            <div className="space-y-3">
              <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-inner">
                {/* Simulated Browser Frame Bar */}
                <div className="bg-slate-900 border-b border-slate-800 px-4 py-2.5 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="h-2.5 w-2.5 rounded-full bg-red-500/80 inline-block" />
                    <span className="h-2.5 w-2.5 rounded-full bg-yellow-500/80 inline-block" />
                    <span className="h-2.5 w-2.5 rounded-full bg-green-500/80 inline-block" />
                    <span className="ml-2 text-xs font-mono text-slate-400 truncate max-w-sm">
                      {captureData.title}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                      Full-Page Render
                    </span>
                    <a
                      href={`data:image/png;base64,${captureData.screenshotBase64}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-slate-400 hover:text-white text-xs flex items-center gap-1"
                      title="Open full image in new tab"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  </div>
                </div>

                {/* Screenshot Scrollable Container */}
                <div className="max-h-[640px] overflow-auto p-4 flex justify-center bg-slate-950/90 select-none">
                  <div
                    style={{
                      transform: `scale(${zoomLevel})`,
                      transformOrigin: 'top center',
                      transition: 'transform 0.15s ease-out',
                    }}
                    className="shadow-2xl rounded-lg overflow-hidden border border-slate-800 max-w-full"
                  >
                    <img
                      src={`data:image/png;base64,${captureData.screenshotBase64}`}
                      alt={`Full page screenshot of ${captureData.url}`}
                      className="block max-w-full h-auto object-top"
                    />
                  </div>
                </div>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400 px-1">
                <span>
                  Captured with headless browser rendering, full scroll lazy-loading, and wait-page bypass.
                </span>
                <span className="font-mono text-slate-500">
                  Target resolution: {viewportPreset.toUpperCase()}
                </span>
              </div>
            </div>
          )}

          {/* TAB 2: EXTRACTED RAW HTML */}
          {activeTab === 'html' && (
            <div className="space-y-3">
              {/* Filter / Search inside HTML */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-950 p-3 rounded-xl border border-slate-800">
                <div className="relative flex-1">
                  <Search className="h-3.5 w-3.5 text-slate-500 absolute inset-y-0 left-3 my-auto" />
                  <input
                    type="text"
                    value={htmlSearchQuery}
                    onChange={(e) => setHtmlSearchQuery(e.target.value)}
                    placeholder="Search inside extracted raw HTML (e.g. title, href, meta, class)..."
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs font-mono text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500"
                  />
                </div>

                {/* Tag Metrics */}
                <div className="flex items-center gap-2 flex-wrap text-[11px] font-mono text-slate-400">
                  <span className="bg-slate-900 px-2 py-1 rounded border border-slate-800">
                    <span className="text-cyan-300">{captureData.metadata.scriptsCount}</span> scripts
                  </span>
                  <span className="bg-slate-900 px-2 py-1 rounded border border-slate-800">
                    <span className="text-emerald-300">{captureData.metadata.linksCount}</span> links
                  </span>
                  <span className="bg-slate-900 px-2 py-1 rounded border border-slate-800">
                    <span className="text-amber-300">{captureData.metadata.imagesCount}</span> images
                  </span>
                  <span className="bg-slate-900 px-2 py-1 rounded border border-slate-800">
                    <span className="text-indigo-300">{captureData.metadata.stylesheetsCount}</span> css
                  </span>
                </div>
              </div>

              {/* Code Container */}
              <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden">
                <div className="bg-slate-900/80 border-b border-slate-800 px-4 py-2 flex items-center justify-between">
                  <span className="text-xs font-mono text-slate-400">
                    Raw Document HTML ({filteredLines.length} lines shown)
                  </span>
                  <span className="text-[11px] font-mono text-slate-500">
                    Encoding: {captureData.metadata.charset || 'UTF-8'}
                  </span>
                </div>

                <div className="max-h-[550px] overflow-auto p-4 font-mono text-xs text-slate-300 space-y-0.5 select-text">
                  {filteredLines.map((line, idx) => (
                    <div key={idx} className="flex hover:bg-slate-900/60 py-0.5 rounded px-1">
                      <span className="w-12 text-slate-600 select-none text-right pr-4 font-mono text-[10px]">
                        {idx + 1}
                      </span>
                      <span className="flex-1 whitespace-pre-wrap break-all text-slate-200">
                        {line}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: BYPASS AUDIT TELEMETRY */}
          {activeTab === 'telemetry' && (
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-4">
              <div>
                <h4 className="text-sm font-bold text-white flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-emerald-400" />
                  Wait-Page &amp; Interstitial Bypass Audit Log
                </h4>
                <p className="text-xs text-slate-400 mt-0.5">
                  Execution sequence performed by headless engine to reach the unhindered target DOM
                </p>
              </div>

              <div className="space-y-2">
                {captureData.bypassedActions.map((action, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-3 bg-slate-900/80 border border-slate-800/80 rounded-lg p-3 text-xs"
                  >
                    <span className="h-5 w-5 rounded-full bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 font-mono text-[11px] flex items-center justify-center flex-shrink-0 mt-0.5 font-bold">
                      {idx + 1}
                    </span>
                    <div className="flex-1 space-y-1">
                      <div className="text-slate-200 font-medium">{action}</div>
                      <div className="text-[10px] font-mono text-slate-500">
                        Autonomous gate verification
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="pt-4 border-t border-slate-800/80 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
                <div className="bg-slate-900/50 p-3 rounded-lg border border-slate-800/60 space-y-1">
                  <div className="text-slate-400 uppercase text-[10px]">Proxy Status &amp; Gateway</div>
                  <div className={`font-semibold flex items-center gap-1.5 ${captureData.proxyEnabled ? 'text-emerald-400' : 'text-slate-300'}`}>
                    {captureData.proxyEnabled ? (
                      <>
                        <Network className="h-3.5 w-3.5 text-emerald-400" />
                        <span>Enabled ({captureData.proxyUsed})</span>
                      </>
                    ) : (
                      <>
                        <Radio className="h-3.5 w-3.5 text-slate-500" />
                        <span>Disabled (Direct Connection)</span>
                      </>
                    )}
                  </div>
                </div>
                <div className="bg-slate-900/50 p-3 rounded-lg border border-slate-800/60 space-y-1">
                  <div className="text-slate-400 uppercase text-[10px]">Canonical / Destination</div>
                  <div className="text-cyan-300 truncate">{captureData.finalUrl}</div>
                </div>
                <div className="bg-slate-900/50 p-3 rounded-lg border border-slate-800/60 space-y-1">
                  <div className="text-slate-400 uppercase text-[10px]">Description Meta Tag</div>
                  <div className="text-slate-300 truncate">
                    {captureData.metadata.description || 'None declared in document'}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Recent Captures Quick Strip */}
      {history.length > 0 && (
        <div className="pt-4 border-t border-slate-800/80 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase tracking-wider text-slate-400">Recent Captures History</span>
            <span className="text-[11px] text-slate-500 font-mono">{history.length} Saved</span>
          </div>

          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            {history.slice(0, 8).map((item) => (
              <button
                key={item.id}
                onClick={() => {
                  setUrlInput(item.url);
                  handleCapture(item.url);
                }}
                disabled={loading}
                className="bg-slate-950 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 px-3 py-1.5 rounded-lg text-left flex-shrink-0 text-xs transition space-y-0.5 max-w-[220px] cursor-pointer"
              >
                <div className="flex items-center justify-between gap-1">
                  <span className="font-semibold text-white truncate flex-1">{item.title || item.url}</span>
                  {item.proxyEnabled ? (
                    <span className="text-[9px] font-mono px-1 rounded bg-emerald-500/15 text-emerald-300 flex-shrink-0">
                      Tor Proxy
                    </span>
                  ) : (
                    <span className="text-[9px] font-mono px-1 rounded bg-slate-900 text-slate-500 flex-shrink-0">
                      Direct
                    </span>
                  )}
                </div>
                <div className="text-[10px] font-mono text-slate-400 truncate">{item.finalUrl}</div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
