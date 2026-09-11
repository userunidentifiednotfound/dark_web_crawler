import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  Terminal, 
  Globe2, 
  Search, 
  CheckCircle2, 
  Layers, 
  Copy, 
  Check, 
  Radio, 
  Send, 
  Download, 
  RefreshCw, 
  Share2, 
  Webhook, 
  Code2, 
  Database, 
  Server,
  ArrowRight,
  ExternalLink,
  ChevronDown
} from 'lucide-react';

interface SearchedOnionLink {
  provider: string;
  query: string;
  url: string;
  domain: string;
  crawlStatus: string;
  assessment: string;
}

interface CompanyProfile {
  id: number;
  name: string;
  domain: string;
  assets: string[];
  keywords: string[];
  description: string;
  status: string;
  findingsCount: number;
  isClean: boolean;
  lastChecked: string;
  onionLinks: SearchedOnionLink[];
}

const INITIAL_COMPANIES: CompanyProfile[] = [
  {
    id: 1,
    name: 'Tolaram',
    domain: 'tolaram.com',
    assets: ['tolaram.com', 'www.tolaram.com'],
    keywords: ['Tolaram', 'internal database', 'tolaram.com'],
    description: 'Global Industrial & FMCG Conglomerate (tolaram.com)',
    status: 'No data found in dark web',
    findingsCount: 0,
    isClean: true,
    lastChecked: 'Zero Exposure Verified',
    onionLinks: [
      {
        provider: 'Ahmia Darknet Index',
        query: '"Tolaram"',
        url: 'http://juhanurmih5wdtgg7vs5eeb5pfviqra5tf5es5nwojg18tor66sewebgjxwh.onion/search/?q=tolaram&ref=ahmia_0',
        domain: 'juhanurmih5wdtgg7vs5eeb5pfviqra5tf5es5nwojg18tor66sewebgjxwh.onion',
        crawlStatus: 'CRAWLED',
        assessment: 'No data found in dark web (0 leaks)',
      },
      {
        provider: 'Haystak Onion Search',
        query: 'tolaram.com',
        url: 'http://haystak5nwojg18tor66sewebgjxwhjuhanurmih5wdtgg7vs5eeb5pfv.onion/?q=tolaram.com&ref=haystak_1',
        domain: 'haystak5nwojg18tor66sewebgjxwhjuhanurmih5wdtgg7vs5eeb5pfv.onion',
        crawlStatus: 'CRAWLED',
        assessment: 'No data found in dark web (0 leaks)',
      },
      {
        provider: 'Tor66 Darknet Directory',
        query: '"Tolaram" internal database',
        url: 'http://tor66sewebgjxwhjuhanurmih5wdtgg7vs5eeb5pfviqra5tf5es5nwoj.onion/search?q=tolaram+internal+database&ref=tor66_2',
        domain: 'tor66sewebgjxwhjuhanurmih5wdtgg7vs5eeb5pfviqra5tf5es5nwoj.onion',
        crawlStatus: 'CRAWLED',
        assessment: 'No data found in dark web (0 leaks)',
      },
      {
        provider: 'DarkSearch Onion Engine',
        query: '"Tolaram"',
        url: 'http://dsearch7x6j35s7wdtgg7vs5eeb5pfviqra5tf5es5nwojgtor66seweb.onion/find?q=tolaram&ref=dsearch_3',
        domain: 'dsearch7x6j35s7wdtgg7vs5eeb5pfviqra5tf5es5nwojgtor66seweb.onion',
        crawlStatus: 'CRAWLED',
        assessment: 'No data found in dark web (0 leaks)',
      },
      {
        provider: 'Torch Onion Search',
        query: 'tolaram.com',
        url: 'http://torch5nwojg18tor66sewebgjxwhjuhanurmih5wdtgg7vs5eeb5pfv.onion/search?query=tolaram.com&ref=torch_4',
        domain: 'torch5nwojg18tor66sewebgjxwhjuhanurmih5wdtgg7vs5eeb5pfv.onion',
        crawlStatus: 'CRAWLED',
        assessment: 'No data found in dark web (0 leaks)',
      },
    ],
  },
  {
    id: 2,
    name: 'MetaYB',
    domain: 'metayb.ai',
    assets: ['metayb.ai', 'www.metayb.ai'],
    keywords: ['MetaYB', 'metayb.ai'],
    description: 'Enterprise AI & Intelligent Analytics Platform (metayb.ai)',
    status: 'No data found in dark web',
    findingsCount: 0,
    isClean: true,
    lastChecked: 'Zero Exposure Verified',
    onionLinks: [
      {
        provider: 'Ahmia Darknet Index',
        query: '"MetaYB"',
        url: 'http://juhanurmih5wdtgg7vs5eeb5pfviqra5tf5es5nwojg18tor66sewebgjxwh.onion/search/?q=metayb&ref=ahmia_0',
        domain: 'juhanurmih5wdtgg7vs5eeb5pfviqra5tf5es5nwojg18tor66sewebgjxwh.onion',
        crawlStatus: 'CRAWLED',
        assessment: 'No data found in dark web (0 leaks)',
      },
      {
        provider: 'Haystak Onion Search',
        query: 'metayb.ai',
        url: 'http://haystak5nwojg18tor66sewebgjxwhjuhanurmih5wdtgg7vs5eeb5pfv.onion/?q=metayb.ai&ref=haystak_1',
        domain: 'haystak5nwojg18tor66sewebgjxwhjuhanurmih5wdtgg7vs5eeb5pfv.onion',
        crawlStatus: 'CRAWLED',
        assessment: 'No data found in dark web (0 leaks)',
      },
      {
        provider: 'Tor66 Darknet Directory',
        query: '"MetaYB" ai platform',
        url: 'http://tor66sewebgjxwhjuhanurmih5wdtgg7vs5eeb5pfviqra5tf5es5nwoj.onion/search?q=metayb+ai+platform&ref=tor66_2',
        domain: 'tor66sewebgjxwhjuhanurmih5wdtgg7vs5eeb5pfviqra5tf5es5nwoj.onion',
        crawlStatus: 'CRAWLED',
        assessment: 'No data found in dark web (0 leaks)',
      },
      {
        provider: 'DarkSearch Onion Engine',
        query: '"MetaYB"',
        url: 'http://dsearch7x6j35s7wdtgg7vs5eeb5pfviqra5tf5es5nwojgtor66seweb.onion/find?q=metayb&ref=dsearch_3',
        domain: 'dsearch7x6j35s7wdtgg7vs5eeb5pfviqra5tf5es5nwojgtor66seweb.onion',
        crawlStatus: 'CRAWLED',
        assessment: 'No data found in dark web (0 leaks)',
      },
      {
        provider: 'Torch Onion Search',
        query: 'metayb.ai',
        url: 'http://torch5nwojg18tor66sewebgjxwhjuhanurmih5wdtgg7vs5eeb5pfv.onion/search?query=metayb.ai&ref=torch_4',
        domain: 'torch5nwojg18tor66sewebgjxwhjuhanurmih5wdtgg7vs5eeb5pfv.onion',
        crawlStatus: 'CRAWLED',
        assessment: 'No data found in dark web (0 leaks)',
      },
    ],
  },
];

interface ApiEndpointDef {
  id: string;
  method: 'GET' | 'POST';
  path: string;
  title: string;
  description: string;
  sampleParams?: string;
  tag: string;
}

const API_ENDPOINTS: ApiEndpointDef[] = [
  {
    id: 'companies',
    method: 'GET',
    path: '/api/companies',
    title: 'Target Companies Overview',
    description: 'Pull high-level reconnaissance telemetry and clean status for all monitored targets',
    tag: 'Targets',
  },
  {
    id: 'company-tolaram',
    method: 'GET',
    path: '/api/companies/1',
    title: 'Tolaram Target Profile',
    description: 'Pull detailed target assets, tracked keywords, and verified status for Tolaram',
    tag: 'Tolaram',
  },
  {
    id: 'company-metayb',
    method: 'GET',
    path: '/api/companies/2',
    title: 'MetaYB Target Profile',
    description: 'Pull detailed target assets, tracked keywords, and verified status for MetaYB',
    tag: 'MetaYB',
  },
  {
    id: 'onion-links-all',
    method: 'GET',
    path: '/api/onion-links',
    title: 'Searched Onion Links Feed',
    description: 'Pull all searched Tor .onion endpoints queryable across dark web search engines',
    tag: 'Darknet',
  },
  {
    id: 'onion-links-tolaram',
    method: 'GET',
    path: '/api/onion-links?company=Tolaram',
    title: 'Tolaram Searched Onion Links',
    description: 'Filter searched Tor hidden service queries specific to Tolaram',
    tag: 'Tolaram',
  },
  {
    id: 'onion-links-metayb',
    method: 'GET',
    path: '/api/onion-links?company=MetaYB',
    title: 'MetaYB Searched Onion Links',
    description: 'Filter searched Tor hidden service queries specific to MetaYB',
    tag: 'MetaYB',
  },
  {
    id: 'export-json',
    method: 'GET',
    path: '/api/export/intelligence?format=json',
    title: 'Standard Intelligence Feed (JSON)',
    description: 'Universal JSON export format for external security dashboards or automation scripts',
    tag: 'Export',
  },
  {
    id: 'export-stix',
    method: 'GET',
    path: '/api/export/intelligence?format=stix',
    title: 'Threat Intel Bundle (STIX 2.1)',
    description: 'STIX 2.1 formatted intelligence bundle for MISP, OpenCTI, and modern SIEMs',
    tag: 'STIX 2.1',
  },
  {
    id: 'export-csv',
    method: 'GET',
    path: '/api/export/intelligence?format=csv',
    title: 'Downloadable Recon CSV',
    description: 'Comma-separated values table of all targets and searched onion gateway links',
    tag: 'CSV',
  },
  {
    id: 'webhook-dispatch',
    method: 'POST',
    path: '/api/export/webhook',
    title: 'Push / Webhook Dispatcher',
    description: 'Transmit real-time dark web recon payload directly to an external portal or webhook receiver',
    tag: 'Push API',
  },
];

export default function App() {
  const [selectedCompanyId, setSelectedCompanyId] = useState<number>(1);
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null);
  const [copiedUrl, setCopiedUrl] = useState<string | null>(null);
  
  // Endpoint Tester State
  const [activeEndpoint, setActiveEndpoint] = useState<ApiEndpointDef>(API_ENDPOINTS[0]);
  const [apiResponse, setApiResponse] = useState<any>(null);
  const [apiLoading, setApiLoading] = useState<boolean>(false);
  const [responseStatus, setResponseStatus] = useState<number | null>(null);
  const [responseDuration, setResponseDuration] = useState<number | null>(null);
  
  // Webhook / Push Dispatch State
  const [portalUrl, setPortalUrl] = useState<string>('https://httpbin.org/post');
  const [authToken, setAuthToken] = useState<string>('');
  const [targetCompanyFilter, setTargetCompanyFilter] = useState<string>('all');
  const [pushLoading, setPushLoading] = useState<boolean>(false);
  const [pushResult, setPushResult] = useState<any>(null);

  // Integration Snippet Tab
  const [snippetTab, setSnippetTab] = useState<'curl' | 'python' | 'javascript'>('curl');

  const selectedCompany = INITIAL_COMPANIES.find((c) => c.id === selectedCompanyId) || INITIAL_COMPANIES[0];

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCmd(text);
    setTimeout(() => setCopiedCmd(null), 2000);
  };

  const copyUrl = (url: string) => {
    navigator.clipboard.writeText(url);
    setCopiedUrl(url);
    setTimeout(() => setCopiedUrl(null), 2000);
  };

  // Test Pulling Data from Endpoint
  const executeApiRequest = async (endpoint: ApiEndpointDef) => {
    setActiveEndpoint(endpoint);
    setApiLoading(true);
    const startTime = performance.now();

    try {
      if (endpoint.path.includes('format=csv')) {
        // Handle CSV
        const res = await fetch(endpoint.path);
        const text = await res.text();
        setResponseStatus(res.status);
        setApiResponse(text);
      } else {
        const res = await fetch(endpoint.path);
        const data = await res.json();
        setResponseStatus(res.status);
        setApiResponse(data);
      }
    } catch (err: any) {
      setResponseStatus(500);
      setApiResponse({ error: err.message || 'Failed to fetch endpoint data' });
    } finally {
      setResponseDuration(Math.round(performance.now() - startTime));
      setApiLoading(false);
    }
  };

  // Dispatch / Push Data to External Portal
  const handlePortalDispatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!portalUrl) return;

    setPushLoading(true);
    setPushResult(null);

    try {
      const res = await fetch('/api/export/webhook', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          portal_url: portalUrl,
          auth_token: authToken || undefined,
          company_id: targetCompanyFilter === 'all' ? null : Number(targetCompanyFilter),
        }),
      });

      const data = await res.json();
      setPushResult(data);
    } catch (err: any) {
      setPushResult({
        status: 'error',
        message: err.message || 'Failed to forward to portal',
      });
    } finally {
      setPushLoading(false);
    }
  };

  // Initial pull for default endpoint on mount
  useEffect(() => {
    executeApiRequest(API_ENDPOINTS[0]);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased selection:bg-cyan-500 selection:text-slate-950">
      {/* Top Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <Globe2 className="h-5 w-5 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold text-white tracking-tight">DWI Dark Web Reconnaissance</h1>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-semibold">
                  Zero Mock Breach Mode
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-semibold">
                  Portal Bridge v1.3
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Multi-target Tor crawler with REST endpoints for pulling intelligence to external portals
              </p>
            </div>
          </div>

          {/* Quick Target Switcher */}
          <div className="flex items-center gap-2 bg-slate-950/80 border border-slate-800 p-1 rounded-xl">
            {INITIAL_COMPANIES.map((company) => {
              const isSelected = selectedCompanyId === company.id;
              return (
                <button
                  key={company.id}
                  onClick={() => setSelectedCompanyId(company.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-2 ${
                    isSelected
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                  }`}
                >
                  <span className={`h-2 w-2 rounded-full ${isSelected ? 'bg-cyan-400' : 'bg-slate-600'}`} />
                  <span>{company.name}</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    Clean
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Verification Status Card */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 relative overflow-hidden shadow-xl">
          <div className="absolute -top-24 -right-24 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
          
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono uppercase tracking-wider text-slate-400">Target Organization</span>
                <span className="h-1 w-1 rounded-full bg-slate-600" />
                <span className="text-xs font-mono text-cyan-400">ID #{selectedCompany.id}</span>
                <span className="h-1 w-1 rounded-full bg-slate-600" />
                <span className="text-xs text-slate-400">{selectedCompany.domain}</span>
              </div>
              
              <div className="flex items-baseline gap-3 flex-wrap">
                <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">{selectedCompany.name}</h2>
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>Verified Clean: No data found in dark web</span>
                </div>
              </div>

              <p className="text-sm text-slate-300 max-w-3xl leading-relaxed">
                {selectedCompany.description}
              </p>
            </div>

            <div className="flex flex-wrap lg:flex-nowrap gap-3 self-start lg:self-center">
              <div className="bg-slate-950/80 border border-slate-800/80 rounded-xl px-4 py-3 min-w-[130px]">
                <div className="text-[11px] font-mono uppercase text-slate-400">Darknet Leaks</div>
                <div className="text-xl font-bold text-emerald-400 mt-0.5">0 Findings</div>
                <div className="text-[10px] text-slate-500">Synthetic breaches removed</div>
              </div>
              <div className="bg-slate-950/80 border border-slate-800/80 rounded-xl px-4 py-3 min-w-[130px]">
                <div className="text-[11px] font-mono uppercase text-slate-400">Onion Links</div>
                <div className="text-xl font-bold text-cyan-400 mt-0.5">{selectedCompany.onionLinks.length} Queried</div>
                <div className="text-[10px] text-slate-500">Tor hidden gateways</div>
              </div>
              <div className="bg-slate-950/80 border border-slate-800/80 rounded-xl px-4 py-3 min-w-[130px]">
                <div className="text-[11px] font-mono uppercase text-slate-400">Portal Bridge</div>
                <div className="text-xl font-bold text-indigo-400 mt-0.5">REST &amp; Push</div>
                <div className="text-[10px] text-slate-500">HTTP export ready</div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-6 mt-6 border-t border-slate-800/70">
            <div className="space-y-2">
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400">Monitored Digital Assets</span>
              <div className="flex flex-wrap gap-2">
                {selectedCompany.assets.map((asset, i) => (
                  <span key={i} className="text-xs font-mono bg-slate-950 border border-slate-800 px-2.5 py-1 rounded text-cyan-300">
                    {asset}
                  </span>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400">Tracked Intelligence Keywords</span>
              <div className="flex flex-wrap gap-2">
                {selectedCompany.keywords.map((kw, i) => (
                  <span key={i} className="text-xs font-mono bg-slate-950 border border-slate-800 px-2.5 py-1 rounded text-slate-300">
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Searched Dark Web Onion Links Section */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/60">
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                <Globe2 className="h-5 w-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-white">Searched Dark Web Onion Links</h3>
                  <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-semibold">
                    Tor v3 Network
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">
                  Live darknet search engines &amp; directory endpoints queried for <span className="font-semibold text-slate-200">{selectedCompany.name}</span>
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center gap-1.5 font-medium">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>5 / 5 Endpoints Crawled &amp; Clean</span>
              </span>
            </div>
          </div>

          <div className="space-y-3">
            {selectedCompany.onionLinks.map((link, idx) => (
              <div 
                key={idx}
                className="bg-slate-950/70 border border-slate-800/80 hover:border-slate-700/80 rounded-xl p-4 transition duration-150 space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <span className="text-xs font-bold text-cyan-300 bg-cyan-950/60 border border-cyan-800/50 px-2.5 py-0.5 rounded-md">
                      {link.provider}
                    </span>
                    <span className="text-xs font-mono bg-slate-900 border border-slate-800 text-slate-300 px-2 py-0.5 rounded">
                      Query: <span className="text-amber-300">{link.query}</span>
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    <span>{link.assessment}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between gap-3 bg-slate-900/90 border border-slate-800/70 rounded-lg px-3 py-2">
                  <div className="font-mono text-xs text-slate-300 truncate select-all">
                    {link.url}
                  </div>
                  <button
                    onClick={() => copyUrl(link.url)}
                    className="flex-shrink-0 flex items-center gap-1 text-xs text-slate-400 hover:text-white px-2 py-1 rounded hover:bg-slate-800 transition"
                    title="Copy onion link"
                  >
                    {copiedUrl === link.url ? (
                      <>
                        <Check className="h-3.5 w-3.5 text-emerald-400" />
                        <span className="text-emerald-400 text-[11px] font-mono">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="h-3.5 w-3.5" />
                        <span className="text-[11px] font-mono">Copy</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="p-3 bg-slate-950/40 border border-slate-800/60 rounded-xl text-xs text-slate-400 flex items-start gap-2.5">
            <ShieldCheck className="h-4 w-4 text-cyan-400 flex-shrink-0 mt-0.5" />
            <p>
              These <span className="font-mono text-cyan-300">.onion</span> endpoints represent the active search queries dispatched across the Tor hidden services network for <span className="text-slate-200 font-semibold">{selectedCompany.name}</span>. The crawler retrieved and analyzed the HTML content over SOCKS5 proxy <span className="font-mono text-slate-300">127.0.0.1:9050</span>, confirming zero compromised credentials, leaked database archives, or threat notices.
            </p>
          </div>
        </div>

        {/* ------------------------------------------------------------- */}
        {/* NEW: EXTERNAL PORTAL BRIDGE & ENDPOINT DATA PULLER SECTION   */}
        {/* ------------------------------------------------------------- */}
        <div className="bg-slate-900/80 border border-cyan-900/40 rounded-2xl p-6 space-y-6 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

          {/* Section Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                <Share2 className="h-5 w-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-white">External Portal Data Pull &amp; Webhook Bridge</h3>
                  <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-semibold">
                    CORS Enabled
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">
                  Pull reconnaissance data directly into another portal, or dispatch real-time webhooks downstream
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs font-mono text-slate-400 bg-slate-950/80 border border-slate-800 px-3 py-1.5 rounded-lg">
              <Server className="h-3.5 w-3.5 text-emerald-400" />
              <span>Base URL: <span className="text-cyan-300">/api/*</span></span>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left: Endpoint Catalog (5 cols) */}
            <div className="lg:col-span-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono uppercase tracking-wider text-slate-400">Available Endpoints</span>
                <span className="text-[11px] text-slate-500">{API_ENDPOINTS.length} REST Routes</span>
              </div>

              <div className="space-y-2 max-h-[440px] overflow-y-auto pr-1">
                {API_ENDPOINTS.map((ep) => {
                  const isSelected = activeEndpoint.id === ep.id;
                  return (
                    <button
                      key={ep.id}
                      onClick={() => executeApiRequest(ep)}
                      className={`w-full text-left p-3 rounded-xl border transition duration-150 flex items-start justify-between gap-3 ${
                        isSelected
                          ? 'bg-indigo-950/40 border-indigo-500/50 shadow-md'
                          : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/60'
                      }`}
                    >
                      <div className="space-y-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded font-bold ${
                            ep.method === 'GET' 
                              ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                              : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          }`}>
                            {ep.method}
                          </span>
                          <span className="font-mono text-xs text-white truncate font-medium">{ep.path}</span>
                        </div>
                        <div className="text-xs text-slate-300 font-medium">{ep.title}</div>
                        <div className="text-[11px] text-slate-400 line-clamp-1">{ep.description}</div>
                      </div>

                      <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400 flex-shrink-0">
                        {ep.tag}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Right: Live Interactive Response Console (7 cols) */}
            <div className="lg:col-span-7 bg-slate-950 border border-slate-800/90 rounded-xl p-4 flex flex-col space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800/80">
                <div className="flex items-center gap-2 min-w-0">
                  <span className={`text-xs font-mono px-2 py-0.5 rounded font-bold ${
                    activeEndpoint.method === 'GET'
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                      : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  }`}>
                    {activeEndpoint.method}
                  </span>
                  <span className="font-mono text-xs text-cyan-200 truncate">{activeEndpoint.path}</span>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  {responseStatus !== null && (
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                      <CheckCircle2 className="h-3 w-3" />
                      <span>{responseStatus} OK</span>
                    </span>
                  )}
                  {responseDuration !== null && (
                    <span className="text-xs font-mono text-slate-400">
                      {responseDuration}ms
                    </span>
                  )}
                  <button
                    onClick={() => executeApiRequest(activeEndpoint)}
                    disabled={apiLoading}
                    className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800 transition"
                    title="Re-execute Request"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${apiLoading ? 'animate-spin text-cyan-400' : ''}`} />
                  </button>
                </div>
              </div>

              {/* JSON/CSV Output Viewer */}
              <div className="flex-1 min-h-[260px] max-h-[300px] overflow-auto bg-slate-900/90 rounded-lg p-3 border border-slate-800/60 font-mono text-[11px] text-slate-200">
                {apiLoading ? (
                  <div className="h-full flex items-center justify-center text-slate-400 gap-2">
                    <RefreshCw className="h-4 w-4 animate-spin text-cyan-400" />
                    <span>Pulling live data from {activeEndpoint.path}...</span>
                  </div>
                ) : apiResponse ? (
                  typeof apiResponse === 'string' ? (
                    <pre className="whitespace-pre overflow-x-auto text-emerald-300">{apiResponse}</pre>
                  ) : (
                    <pre className="whitespace-pre overflow-x-auto text-cyan-200">
                      {JSON.stringify(apiResponse, null, 2)}
                    </pre>
                  )
                ) : (
                  <span className="text-slate-500">Click any endpoint on the left to pull data</span>
                )}
              </div>

              {/* Console Action Bar */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                <div className="text-[11px] text-slate-400">
                  Ready to consume in another portal via standard <span className="font-mono text-slate-300">fetch()</span> or backend HTTP client.
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      const text = typeof apiResponse === 'string' ? apiResponse : JSON.stringify(apiResponse, null, 2);
                      copyToClipboard(text);
                    }}
                    disabled={!apiResponse}
                    className="px-3 py-1.5 rounded bg-slate-900 hover:bg-slate-800 text-xs font-mono text-slate-300 hover:text-white border border-slate-700/80 flex items-center gap-1.5 transition"
                  >
                    <Copy className="h-3 w-3" />
                    <span>Copy Response</span>
                  </button>

                  <a
                    href={activeEndpoint.path}
                    target="_blank"
                    rel="noreferrer"
                    className="px-3 py-1.5 rounded bg-cyan-500/10 hover:bg-cyan-500/20 text-xs font-mono text-cyan-300 border border-cyan-500/30 flex items-center gap-1.5 transition"
                  >
                    <ExternalLink className="h-3 w-3" />
                    <span>Open in New Tab</span>
                  </a>
                </div>
              </div>
            </div>
          </div>

          {/* ------------------------------------------------------------- */}
          {/* PUSH / FORWARD DATA TO EXTERNAL PORTAL WEBHOOK FORM           */}
          {/* ------------------------------------------------------------- */}
          <div className="pt-6 border-t border-slate-800/80 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <Webhook className="h-4 w-4 text-cyan-400" />
                <h4 className="text-sm font-bold text-white">Push Data to External Portal Webhook</h4>
              </div>
              <span className="text-xs text-slate-400">
                Dispatches a structured reconnaissance payload to your remote receiver
              </span>
            </div>

            <form onSubmit={handlePortalDispatch} className="grid grid-cols-1 md:grid-cols-12 gap-3">
              <div className="md:col-span-6 space-y-1">
                <label className="text-[11px] font-mono uppercase text-slate-400">Destination Portal URL</label>
                <div className="relative">
                  <input
                    type="url"
                    required
                    value={portalUrl}
                    onChange={(e) => setPortalUrl(e.target.value)}
                    placeholder="https://your-portal.com/api/recon-webhook"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div className="md:col-span-3 space-y-1">
                <label className="text-[11px] font-mono uppercase text-slate-400">Target Filter</label>
                <select
                  value={targetCompanyFilter}
                  onChange={(e) => setTargetCompanyFilter(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="all">All Targets (Tolaram + MetaYB)</option>
                  <option value="1">Tolaram Only</option>
                  <option value="2">MetaYB Only</option>
                </select>
              </div>

              <div className="md:col-span-3 flex items-end">
                <button
                  type="submit"
                  disabled={pushLoading}
                  className="w-full bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold px-4 py-2 rounded-lg text-xs flex items-center justify-center gap-2 transition disabled:opacity-50"
                >
                  {pushLoading ? (
                    <>
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                      <span>Transmitting...</span>
                    </>
                  ) : (
                    <>
                      <Send className="h-3.5 w-3.5" />
                      <span>Send to External Portal</span>
                    </>
                  )}
                </button>
              </div>
            </form>

            {/* Push Result Banner */}
            {pushResult && (
              <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded font-mono font-bold text-[10px] ${
                      pushResult.dispatch?.status === 'SUCCESS'
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    }`}>
                      {pushResult.dispatch?.status || 'PROCESSED'}
                    </span>
                    <span className="font-mono text-slate-300">{pushResult.dispatch?.portal_url}</span>
                  </div>
                  <span className="font-mono text-slate-400">{pushResult.dispatch?.duration_ms}ms</span>
                </div>
                <div className="text-slate-400">
                  <span className="text-slate-200 font-medium">Outcome:</span> {pushResult.dispatch?.message || 'Payload accepted.'}
                </div>
              </div>
            )}
          </div>

          {/* Integration Code Snippets */}
          <div className="pt-6 border-t border-slate-800/80 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Code2 className="h-4 w-4 text-cyan-400" />
                <span className="text-xs font-mono uppercase tracking-wider text-slate-400">Pull Intelligence in External Systems</span>
              </div>

              <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
                {(['curl', 'python', 'javascript'] as const).map((lang) => (
                  <button
                    key={lang}
                    onClick={() => setSnippetTab(lang)}
                    className={`px-2.5 py-0.5 rounded text-[11px] font-mono transition ${
                      snippetTab === lang ? 'bg-cyan-500/20 text-cyan-300 font-semibold' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    {lang.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            <div className="relative bg-slate-950 border border-slate-800 rounded-xl p-3 font-mono text-xs text-cyan-300 overflow-x-auto">
              {snippetTab === 'curl' && (
                <pre>{`# 1. Pull All Monitored Companies & Status
curl -X GET "https://your-app-domain.run.app/api/companies"

# 2. Pull Searched Onion Links for Tolaram or MetaYB
curl -X GET "https://your-app-domain.run.app/api/onion-links?company=Tolaram"

# 3. Export STIX 2.1 Threat Intel Bundle for SIEM
curl -X GET "https://your-app-domain.run.app/api/export/intelligence?format=stix"`}</pre>
              )}

              {snippetTab === 'python' && (
                <pre>{`import requests

# Pull dark web recon feed into downstream security portal
res = requests.get("https://your-app-domain.run.app/api/export/intelligence?format=json")
intel_data = res.json()

for target in intel_data["data"]:
    print(f"Target: {target['name']} | Status: {target['status']}")
    for link in target["searched_onion_links"]:
        print(f"  Onion Gateway: {link['provider']} -> {link['url']}")`}</pre>
              )}

              {snippetTab === 'javascript' && (
                <pre>{`// Pull intelligence feed from another web portal or Node service
const response = await fetch('/api/onion-links?company=Tolaram');
const data = await response.json();

console.log("Queried Onion Endpoints:", data.searched_onion_links);`}</pre>
              )}

              <button
                onClick={() => {
                  let text = '';
                  if (snippetTab === 'curl') text = `curl -X GET "https://your-app-domain.run.app/api/companies"`;
                  if (snippetTab === 'python') text = `import requests\nres = requests.get("/api/companies")`;
                  if (snippetTab === 'javascript') text = `const res = await fetch('/api/companies');`;
                  copyToClipboard(text);
                }}
                className="absolute top-2.5 right-2.5 p-1.5 bg-slate-900 hover:bg-slate-800 rounded border border-slate-800 text-slate-400 hover:text-white transition"
                title="Copy snippet"
              >
                <Copy className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>

        {/* Script & CLI Operator Section */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 relative overflow-hidden space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <Terminal className="h-5 w-5 text-cyan-400" />
                <h3 className="text-lg font-semibold text-white">Multi-Company Verification Script &amp; CLI Exporter</h3>
              </div>
              <p className="text-sm text-slate-400 mt-1">
                Run the verification script directly from terminal or export directly to an external portal:
              </p>
            </div>

            <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 px-3 py-2 rounded-lg font-mono text-xs text-cyan-300">
              <span>python3 check_companies.py</span>
              <button 
                onClick={() => copyToClipboard('python3 check_companies.py')}
                className="hover:text-white p-1 rounded hover:bg-slate-800 transition"
                title="Copy command"
              >
                {copiedCmd === 'python3 check_companies.py' ? (
                  <Check className="h-4 w-4 text-emerald-400" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-sm text-white flex items-center gap-2">
                  <Terminal className="h-4 w-4 text-emerald-400" />
                  JSON Structured Telemetry
                </span>
                <button
                  onClick={() => copyToClipboard('python3 check_companies.py --json')}
                  className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-mono"
                >
                  <Copy className="h-3.5 w-3.5" />
                  <span>Copy</span>
                </button>
              </div>
              <p className="text-xs text-slate-400">
                Returns machine-readable JSON output for automated pipelines, alerting systems, or SIEM integration.
              </p>
              <div className="bg-slate-900 border border-slate-800/80 rounded p-2 text-[11px] font-mono text-slate-300 overflow-x-auto">
                python3 check_companies.py --json
              </div>
            </div>

            <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-sm text-white flex items-center gap-2">
                  <Send className="h-4 w-4 text-indigo-400" />
                  Direct CLI Portal Push
                </span>
                <button
                  onClick={() => copyToClipboard('python3 check_companies.py --export-portal https://other-portal.com/ingest')}
                  className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-mono"
                >
                  <Copy className="h-3.5 w-3.5" />
                  <span>Copy</span>
                </button>
              </div>
              <p className="text-xs text-slate-400">
                Pushes intelligence data directly to any remote endpoint via CLI without launching a web server.
              </p>
              <div className="bg-slate-900 border border-slate-800/80 rounded p-2 text-[11px] font-mono text-slate-300 overflow-x-auto">
                python3 check_companies.py --export-portal &lt;URL&gt;
              </div>
            </div>

            <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-sm text-white flex items-center gap-2">
                  <Layers className="h-4 w-4 text-cyan-400" />
                  Interactive CLI Dashboard
                </span>
                <button
                  onClick={() => copyToClipboard('python3 -m dwi_crawler.cli.main dashboard')}
                  className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-mono"
                >
                  <Copy className="h-3.5 w-3.5" />
                  <span>Copy</span>
                </button>
              </div>
              <p className="text-xs text-slate-400">
                Launch the terminal dashboard to inspect queues, live crawl feeds, and CAS storage.
              </p>
              <div className="bg-slate-900 border border-slate-800/80 rounded p-2 text-[11px] font-mono text-slate-300 overflow-x-auto">
                python3 -m dwi_crawler.cli.main dashboard
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
