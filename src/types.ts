export interface SearchedOnionLink {
  provider: string;
  query: string;
  url: string;
  domain: string;
  crawlStatus: string;
  assessment: string;
}

export interface CompanyProfile {
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

export interface ApiEndpointDef {
  id: string;
  method: 'GET' | 'POST';
  path: string;
  title: string;
  description: string;
  sampleParams?: string;
  tag: string;
}

export interface CaptureMetadata {
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
}

export interface CaptureResponse {
  success: boolean;
  url: string;
  finalUrl: string;
  title: string;
  httpStatus: number;
  screenshotBase64: string;
  rawHtml: string;
  htmlSizeBytes: number;
  durationMs: number;
  bypassedActions: string[];
  metadata: CaptureMetadata;
  error?: string;
}

export interface CaptureHistoryRecord {
  id: string;
  timestamp: string;
  url: string;
  finalUrl: string;
  title: string;
  httpStatus: number;
  durationMs: number;
  htmlSizeBytes: number;
  bypassedActions: string[];
  metadata: CaptureMetadata;
}
