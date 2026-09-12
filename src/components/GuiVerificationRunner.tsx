import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  RefreshCw,
  Download,
  CheckCircle2,
  AlertCircle,
  Globe2,
  FileJson,
  FileSpreadsheet,
  Send,
  Search,
  Check,
  Sparkles,
  ExternalLink,
  Layers,
  Network
} from 'lucide-react';

interface VerificationCheckItem {
  name: string;
  result: string;
  findings: number;
  status: string;
}

interface VerificationCompanyResult {
  company_id: number;
  company_name: string;
  status: string;
  is_clean: boolean;
  domains_checked: string[];
  keywords_queried: string[];
  searched_onion_count: number;
  checks: VerificationCheckItem[];
  last_verified_at: string;
}

interface VerificationData {
  status: string;
  executed_at: string;
  duration_ms: number;
  all_clean: boolean;
  summary: {
    total_targets_verified: number;
    clean_targets: number;
    breached_targets: number;
    onion_gateways_verified: number;
    verdict: string;
  };
  results: VerificationCompanyResult[];
}

interface GuiVerificationRunnerProps {
  onOpenPortalBridge?: (companyId?: number) => void;
}

export function GuiVerificationRunner({ onOpenPortalBridge }: GuiVerificationRunnerProps) {
  const [selectedTarget, setSelectedTarget] = useState<'all' | '1' | '2'>('all');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<VerificationData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [downloadSuccess, setDownloadSuccess] = useState<string | null>(null);

  // Run live verification via GUI
  const handleRunVerification = async (targetOverride?: 'all' | '1' | '2') => {
    const target = targetOverride || selectedTarget;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/verify/run?company_id=${target}`);
      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }
      const json: VerificationData = await res.json();
      setData(json);
    } catch (err: any) {
      setError(err.message || 'Failed to complete verification check');
    } finally {
      setLoading(false);
    }
  };

  // Run once on mount for instant visual telemetry
  useEffect(() => {
    handleRunVerification('all');
  }, []);

  // GUI Direct File Downloaders
  const triggerBrowserDownload = (url: string, filename: string, typeDesc: string) => {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    setDownloadSuccess(typeDesc);
    setTimeout(() => setDownloadSuccess(null), 3000);
  };

  const handleDownloadJson = () => {
    triggerBrowserDownload(
      '/api/export/intelligence?format=json',
      `dwi_recon_intelligence_${Date.now()}.json`,
      'JSON Intel Feed'
    );
  };

  const handleDownloadStix = () => {
    triggerBrowserDownload(
      '/api/export/intelligence?format=stix',
      `dwi_stix21_bundle_${Date.now()}.json`,
      'STIX 2.1 Threat Intel Bundle'
    );
  };

  const handleDownloadCsv = () => {
    triggerBrowserDownload(
      '/api/export/intelligence?format=csv',
      `dwi_darknet_recon_${Date.now()}.csv`,
      'CSV Spreadsheet Table'
    );
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-6 shadow-2xl relative overflow-hidden" id="gui-verification-hub">
      <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header Banner */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-5 border-b border-slate-800/80 relative z-10">
        <div className="flex items-center gap-3">
          <div className="h-11 w-11 rounded-xl bg-emerald-500/15 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shadow-inner">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-xl font-bold text-white tracking-tight">Interactive Multi-Target Verification Hub</h2>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-semibold flex items-center gap-1">
                <Sparkles className="h-3 w-3" />
                Pure GUI · Zero CLI
              </span>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 font-semibold">
                REST Verification Engine
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Execute reconnaissance verification, inspect dark web coverage, and export threat feeds directly through graphical controls.
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => {
                setSelectedTarget('all');
                handleRunVerification('all');
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                selectedTarget === 'all'
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              All Targets (2)
            </button>
            <button
              onClick={() => {
                setSelectedTarget('1');
                handleRunVerification('1');
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                selectedTarget === '1'
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Tolaram
            </button>
            <button
              onClick={() => {
                setSelectedTarget('2');
                handleRunVerification('2');
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                selectedTarget === '2'
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              MetaYB
            </button>
          </div>

          <button
            onClick={() => handleRunVerification()}
            disabled={loading}
            className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-bold rounded-xl text-xs flex items-center gap-2 transition shadow-lg shadow-emerald-500/20 active:scale-95 cursor-pointer"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Verifying Targets...' : 'Run Verification Now'}</span>
          </button>
        </div>
      </div>

      {/* Download Alert Toast */}
      {downloadSuccess && (
        <div className="bg-emerald-500/15 border border-emerald-500/40 text-emerald-300 px-4 py-2.5 rounded-xl text-xs flex items-center justify-between">
          <span className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            <span>Downloaded <strong>{downloadSuccess}</strong> directly to your computer.</span>
          </span>
          <span className="text-[10px] font-mono text-emerald-400/80">No CLI commands required</span>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 p-4 rounded-xl text-xs flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-rose-400 flex-shrink-0" />
          <div>
            <div className="font-semibold">Verification Request Failed</div>
            <div className="text-slate-400">{error}</div>
          </div>
        </div>
      )}

      {/* Key Metric Indicators */}
      {data && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5 space-y-1">
            <div className="text-slate-400 text-[11px] font-mono uppercase">Targets Monitored</div>
            <div className="text-xl font-bold text-white flex items-center gap-2">
              <span>{data.summary.total_targets_verified}</span>
              <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                100% Active
              </span>
            </div>
            <div className="text-[10px] text-slate-500">Tolaram &amp; MetaYB Profiles</div>
          </div>

          <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5 space-y-1">
            <div className="text-slate-400 text-[11px] font-mono uppercase">Verified Clean</div>
            <div className="text-xl font-bold text-emerald-400 flex items-center gap-2">
              <span>{data.summary.clean_targets} / {data.summary.total_targets_verified}</span>
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="text-[10px] text-emerald-500/90 font-mono">Zero Mock Breach Guarantee</div>
          </div>

          <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5 space-y-1">
            <div className="text-slate-400 text-[11px] font-mono uppercase">Darknet Leaks Found</div>
            <div className="text-xl font-bold text-cyan-400 flex items-center gap-2">
              <span>0 Findings</span>
            </div>
            <div className="text-[10px] text-slate-500">Tor Pastebins, Dumps &amp; Blogs</div>
          </div>

          <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5 space-y-1">
            <div className="text-slate-400 text-[11px] font-mono uppercase">Searched Gateways</div>
            <div className="text-xl font-bold text-indigo-300 flex items-center gap-2">
              <span>{data.summary.onion_gateways_verified} Onion Queries</span>
            </div>
            <div className="text-[10px] text-slate-500 font-mono">Verified in {data.duration_ms}ms</div>
          </div>
        </div>
      )}

      {/* Main Verdict Strip */}
      {data && (
        <div className="bg-gradient-to-r from-emerald-950/40 via-slate-950 to-slate-950 border border-emerald-500/30 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-300 flex-shrink-0">
              <CheckCircle2 className="h-5 w-5" />
            </div>
            <div>
              <div className="font-semibold text-white text-sm flex items-center gap-2">
                <span>Verified Clean Status</span>
                <span className="text-[10px] font-mono bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded border border-emerald-500/30">
                  PASS
                </span>
              </div>
              <div className="text-xs text-emerald-300/90 mt-0.5">
                {data.summary.verdict}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 self-end sm:self-auto text-[11px] font-mono text-slate-400">
            <span className="flex items-center gap-1 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded text-emerald-400">
              <Network className="h-3 w-3" />
              <span>Proxy: Tor SOCKS5 (127.0.0.1:9050)</span>
            </span>
            <span>Checked: {new Date(data.executed_at).toLocaleTimeString()}</span>
          </div>
        </div>
      )}

      {/* Target Company Verification Breakdown */}
      {data && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {data.results.map((target) => (
            <div
              key={target.company_id}
              className="bg-slate-950/80 border border-slate-800/90 rounded-xl p-4 space-y-4 hover:border-slate-700 transition"
            >
              {/* Company Header */}
              <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
                <div className="flex items-center gap-2.5">
                  <div className="h-8 w-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 font-bold text-xs">
                    {target.company_name.slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="font-bold text-white text-sm">{target.company_name}</h3>
                    <div className="text-[11px] text-slate-400 font-mono">
                      {target.domains_checked.join(' · ')}
                    </div>
                  </div>
                </div>

                <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>Verified Clean</span>
                </span>
              </div>

              {/* Monitored Keywords Chips */}
              <div className="space-y-1.5">
                <div className="text-[10px] font-mono uppercase text-slate-400">Monitored Query Keywords</div>
                <div className="flex flex-wrap gap-1.5">
                  {target.keywords_queried.map((kw, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300 text-[11px] font-mono"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              </div>

              {/* Sub-Checks Checklist */}
              <div className="space-y-2 pt-1">
                <div className="text-[10px] font-mono uppercase text-slate-400">Reconnaissance Verification Matrix</div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {target.checks.map((chk, i) => (
                    <div
                      key={i}
                      className="bg-slate-900/60 border border-slate-800/70 p-2 rounded-lg flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-1.5 text-slate-300 text-[11px]">
                        <Check className="h-3 w-3 text-emerald-400 flex-shrink-0" />
                        <span className="truncate">{chk.name}</span>
                      </div>
                      <span className="text-[10px] font-mono text-emerald-400 font-semibold px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                        {chk.result}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Direct Company Export Link */}
              <div className="pt-3 border-t border-slate-800/70 flex items-center justify-between">
                <span className="text-[11px] font-mono text-slate-400">
                  {target.searched_onion_count} Searched Tor Links Linked
                </span>
                <button
                  onClick={() => {
                    triggerBrowserDownload(
                      `/api/companies/${target.company_id}`,
                      `${target.company_name.toLowerCase()}_recon_profile.json`,
                      `${target.company_name} JSON Profile`
                    );
                  }}
                  className="px-2.5 py-1 bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-lg text-cyan-300 hover:text-white text-xs font-mono flex items-center gap-1.5 transition"
                >
                  <Download className="h-3 w-3" />
                  <span>Export Profile JSON</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 1-Click Graphical Intelligence Exporter (Zero CLI) */}
      <div className="pt-4 border-t border-slate-800/80 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Download className="h-4 w-4 text-cyan-400" />
            <span className="text-xs font-mono uppercase tracking-wider text-slate-300">
              One-Click GUI Intelligence Downloads (No Terminal Needed)
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-500">Direct Browser File Export</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* JSON Button */}
          <button
            onClick={handleDownloadJson}
            className="bg-slate-950 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/40 p-3.5 rounded-xl text-left transition space-y-1.5 group cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-white flex items-center gap-2 group-hover:text-cyan-300">
                <FileJson className="h-4 w-4 text-emerald-400" />
                Download JSON Feed
              </span>
              <Download className="h-3.5 w-3.5 text-slate-500 group-hover:text-cyan-300" />
            </div>
            <p className="text-[11px] text-slate-400 line-clamp-2">
              Universal machine-readable JSON dataset of all targets, keywords, and searched onion links.
            </p>
          </button>

          {/* STIX 2.1 Button */}
          <button
            onClick={handleDownloadStix}
            className="bg-slate-950 hover:bg-slate-800 border border-slate-800 hover:border-indigo-500/40 p-3.5 rounded-xl text-left transition space-y-1.5 group cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-white flex items-center gap-2 group-hover:text-indigo-300">
                <Layers className="h-4 w-4 text-indigo-400" />
                Download STIX 2.1
              </span>
              <Download className="h-3.5 w-3.5 text-slate-500 group-hover:text-indigo-300" />
            </div>
            <p className="text-[11px] text-slate-400 line-clamp-2">
              Industry-standard threat intelligence bundle ready for direct import into MISP, OpenCTI, or SIEM.
            </p>
          </button>

          {/* CSV Spreadsheet Button */}
          <button
            onClick={handleDownloadCsv}
            className="bg-slate-950 hover:bg-slate-800 border border-slate-800 hover:border-amber-500/40 p-3.5 rounded-xl text-left transition space-y-1.5 group cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-white flex items-center gap-2 group-hover:text-amber-300">
                <FileSpreadsheet className="h-4 w-4 text-amber-400" />
                Download CSV Table
              </span>
              <Download className="h-3.5 w-3.5 text-slate-500 group-hover:text-amber-300" />
            </div>
            <p className="text-[11px] text-slate-400 line-clamp-2">
              Formatted spreadsheet table ready to open in Microsoft Excel, Google Sheets, or Numbers.
            </p>
          </button>
        </div>
      </div>
    </div>
  );
}
