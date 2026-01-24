// src/api/alphaApi.ts
// API client for Alpha Discovery backend

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface Quote {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  open: number;
  high: number;
  low: number;
}

export interface VolumeMetrics {
  current_volume: number;
  relative_volume: number;
  relative_volume_label: string;
  volume_trend_5d: string;
  dollar_volume_formatted: string;
  accumulation_distribution: string;
}

export interface AlphaSignal {
  name: string;
  type: 'bullish' | 'bearish' | 'neutral';
  strength: number;
  description: string;
}

export interface AlphaScore {
  total_score: number;
  signal_strength: string;
  overall_grade: string;
  momentum_grade: string;
  trend_grade: string;
  risk_reward_grade: string;
  bullish_signals: number;
  bearish_signals: number;
  signals: AlphaSignal[];
  summary: string;
}

export interface AIAnalysis {
  summary: string;
  sentiment: 'bullish' | 'bearish' | 'neutral';
  confidence: number;
  key_points: string[];
  catalysts: string[];
  risks: string[];
  price_targets?: {
    support: number;
    resistance: number;
  };
  recommendation: string;
}

export interface StockAnalysis {
  symbol: string;
  company_name: string;
  quote: Quote;
  volume_metrics: VolumeMetrics;
  alpha_score: AlphaScore;
  ai_analysis?: AIAnalysis;
  technicals: any;
  options?: any;
  news?: any;
  fundamentals?: any;
}

// ═══════════════════════════════════════════════════════════════
// API FUNCTIONS  
// ═══════════════════════════════════════════════════════════════

/**
 * Get full analysis for a stock (with AI)
 */
export async function analyzeStock(symbol: string): Promise<StockAnalysis> {
  const res = await fetch(`${API_BASE}/analyze/${symbol}`);
  if (!res.ok) {
    throw new Error(`Failed to analyze ${symbol}`);
  }
  return res.json();
}

/**
 * Get quick quote only
 */
export async function getQuote(symbol: string): Promise<Quote> {
  const res = await fetch(`${API_BASE}/quote/${symbol}`);
  if (!res.ok) {
    throw new Error(`Failed to get quote for ${symbol}`);
  }
  return res.json();
}

/**
 * Get technical indicators
 */
export async function getTechnicals(symbol: string) {
  const res = await fetch(`${API_BASE}/technicals/${symbol}`);
  if (!res.ok) {
    throw new Error(`Failed to get technicals for ${symbol}`);
  }
  return res.json();
}

/**
 * Get options data
 */
export async function getOptions(symbol: string) {
  const res = await fetch(`${API_BASE}/options/${symbol}`);
  if (!res.ok) {
    throw new Error(`Failed to get options for ${symbol}`);
  }
  return res.json();
}

/**
 * Check API health
 */
export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

