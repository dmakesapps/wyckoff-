# Alpha Discovery API - React Integration Handoff

## Overview

This document provides everything needed to integrate the Alpha Discovery API into a React/Vite application. The API provides AI-powered stock analysis with real-time data, technical indicators, options flow, news with sources, and intelligent investment recommendations.

---

## API Base URL

```
Development: http://localhost:8000/api
```

---

## Core Endpoints

### 1. Full Stock Analysis (Primary)
```
GET /api/analyze/{symbol}
```

Query params:
- `include_options` (bool, default: true)
- `include_news` (bool, default: true)  
- `include_ai` (bool, default: true)
- `force_refresh` (bool, default: false) - bypass cache

### 2. Quick Quote
```
GET /api/quote/{symbol}
```

### 3. News with Sources
```
GET /api/news/{symbol}?limit=15
```

### 4. Technical Indicators
```
GET /api/technicals/{symbol}
```

### 5. Options Data
```
GET /api/options/{symbol}
```

### 6. Health Check
```
GET /api/health
```

---

## TypeScript Types

Create `src/types/api.ts`:

```typescript
// ═══════════════════════════════════════════════════════════════
// QUOTE
// ═══════════════════════════════════════════════════════════════

export interface Quote {
  symbol: string;
  price: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  previous_close: number;
  change: number;
  change_percent: number;
  timestamp: string;
}

// ═══════════════════════════════════════════════════════════════
// ALPHA SCORE
// ═══════════════════════════════════════════════════════════════

export interface AlphaSignal {
  name: string;
  type: 'bullish' | 'bearish' | 'neutral';
  strength: number; // 1-5
  description: string;
}

export interface AlphaScore {
  total_score: number; // -100 to +100
  signal_strength: 'strong' | 'moderate' | 'weak';
  overall_grade: 'A' | 'B' | 'C' | 'D' | 'F';
  momentum_grade: string;
  trend_grade: string;
  risk_reward_grade: string;
  bullish_signals: number;
  bearish_signals: number;
  signals: AlphaSignal[];
  summary: string;
}

// ═══════════════════════════════════════════════════════════════
// VOLUME METRICS
// ═══════════════════════════════════════════════════════════════

export interface VolumeMetrics {
  current_volume: number;
  relative_volume: number;
  relative_volume_label: string;
  volume_trend_5d: string;
  dollar_volume_formatted: string;
  accumulation_distribution: 'accumulation' | 'distribution' | 'neutral';
}

// ═══════════════════════════════════════════════════════════════
// AI ANALYSIS
// ═══════════════════════════════════════════════════════════════

export interface Projections {
  bull_case: { price: number; thesis: string };
  base_case: { price: number; thesis: string };
  bear_case: { price: number; thesis: string };
  timeframe: string;
}

export interface FirstPrinciples {
  core_question: string;
  key_assumptions: string[];
  what_must_be_true: string[];
}

export interface NewsAnalysis {
  summary: string;
  cited_sources: number[];
  sentiment_driver: string;
}

export interface SourceReference {
  num: number;
  source: string;
  title: string;
  url: string;
  date: string;
}

export interface AIAnalysis {
  summary: string;
  sentiment: 'bullish' | 'bearish' | 'neutral';
  confidence: number; // 0-100
  thesis?: string;
  first_principles?: FirstPrinciples;
  key_points: string[]; // May include [1], [2] citations
  news_analysis?: NewsAnalysis;
  catalysts: string[];
  risks: string[];
  projections?: Projections;
  price_targets?: {
    support: number;
    resistance: number;
  };
  recommendation: string;
  sources_cited: number[];
  source_references?: SourceReference[];
  generated_at: string;
}

// ═══════════════════════════════════════════════════════════════
// NEWS
// ═══════════════════════════════════════════════════════════════

export interface NewsArticle {
  id: number;
  title: string;
  source: string;
  url: string;
  published_at: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  summary?: string;
}

export interface NewsResponse {
  symbol: string;
  overall_sentiment: string;
  earnings_date?: string;
  catalysts: string[];
  article_count: number;
  articles: NewsArticle[];
}

// ═══════════════════════════════════════════════════════════════
// TECHNICALS
// ═══════════════════════════════════════════════════════════════

export interface MovingAverages {
  sma_20?: number;
  sma_50?: number;
  sma_200?: number;
  ema_20?: number;
  price_vs_sma_20?: 'above' | 'below';
  price_vs_sma_50?: 'above' | 'below';
  price_vs_sma_200?: 'above' | 'below';
  golden_cross?: boolean;
  death_cross?: boolean;
}

export interface Momentum {
  rsi?: number;
  rsi_signal?: 'overbought' | 'oversold' | 'neutral';
  macd?: number;
  macd_signal?: number;
  macd_histogram?: number;
  macd_trend?: 'bullish' | 'bearish' | 'neutral';
}

export interface Technicals {
  moving_averages: MovingAverages;
  momentum: Momentum;
  volatility: {
    bb_upper?: number;
    bb_middle?: number;
    bb_lower?: number;
    bb_position?: 'above_upper' | 'below_lower' | 'within';
    atr?: number;
    atr_percent?: number;
  };
  volume: {
    current_volume: number;
    avg_volume_20d?: number;
    volume_ratio?: number;
    is_unusual: boolean;
    volume_trend?: string;
  };
  price_levels: {
    ath?: number;
    atl?: number;
    week_52_high?: number;
    week_52_low?: number;
    distance_from_ath?: number;
    distance_from_52w_high?: number;
  };
  overall_trend?: 'bullish' | 'bearish' | 'neutral';
}

// ═══════════════════════════════════════════════════════════════
// FULL ANALYSIS RESPONSE
// ═══════════════════════════════════════════════════════════════

export interface StockAnalysis {
  symbol: string;
  company_name: string;
  quote: Quote;
  technicals: Technicals;
  volume_metrics: VolumeMetrics;
  alpha_score: AlphaScore;
  options?: any; // Full options data
  news?: any; // Full news data
  fundamentals?: {
    market_cap?: number;
    market_cap_formatted?: string;
    pe_ratio?: number;
    sector?: string;
    industry?: string;
  };
  ai_analysis?: AIAnalysis;
  analyzed_at: string;
}
```

---

## API Client

Create `src/api/alphaApi.ts`:

```typescript
import type { StockAnalysis, Quote, NewsResponse } from '../types/api';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// ═══════════════════════════════════════════════════════════════
// ERROR HANDLING
// ═══════════════════════════════════════════════════════════════

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(response.status, error.detail || 'Request failed');
  }
  return response.json();
}

// ═══════════════════════════════════════════════════════════════
// API FUNCTIONS
// ═══════════════════════════════════════════════════════════════

/**
 * Get full stock analysis with AI insights
 */
export async function analyzeStock(
  symbol: string,
  options?: {
    includeOptions?: boolean;
    includeNews?: boolean;
    includeAi?: boolean;
    forceRefresh?: boolean;
  }
): Promise<StockAnalysis> {
  const params = new URLSearchParams();
  if (options?.includeOptions === false) params.set('include_options', 'false');
  if (options?.includeNews === false) params.set('include_news', 'false');
  if (options?.includeAi === false) params.set('include_ai', 'false');
  if (options?.forceRefresh) params.set('force_refresh', 'true');

  const url = `${API_BASE}/analyze/${symbol.toUpperCase()}${params.toString() ? '?' + params : ''}`;
  const response = await fetch(url);
  return handleResponse<StockAnalysis>(response);
}

/**
 * Get quick quote only (fast, no AI)
 */
export async function getQuote(symbol: string): Promise<Quote> {
  const response = await fetch(`${API_BASE}/quote/${symbol.toUpperCase()}`);
  return handleResponse<Quote>(response);
}

/**
 * Get news with sources
 */
export async function getNews(symbol: string, limit = 15): Promise<NewsResponse> {
  const response = await fetch(`${API_BASE}/news/${symbol.toUpperCase()}?limit=${limit}`);
  return handleResponse<NewsResponse>(response);
}

/**
 * Get technical indicators only
 */
export async function getTechnicals(symbol: string) {
  const response = await fetch(`${API_BASE}/technicals/${symbol.toUpperCase()}`);
  return handleResponse(response);
}

/**
 * Get options data
 */
export async function getOptions(symbol: string) {
  const response = await fetch(`${API_BASE}/options/${symbol.toUpperCase()}`);
  return handleResponse(response);
}

/**
 * Check API health
 */
export async function checkHealth() {
  const response = await fetch(`${API_BASE}/health`);
  return handleResponse(response);
}
```

---

## React Hooks

Create `src/hooks/useStockAnalysis.ts`:

```typescript
import { useState, useCallback } from 'react';
import { analyzeStock, type StockAnalysis } from '../api/alphaApi';

interface UseStockAnalysisOptions {
  includeAi?: boolean;
}

export function useStockAnalysis(options?: UseStockAnalysisOptions) {
  const [data, setData] = useState<StockAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyze = useCallback(async (symbol: string, forceRefresh = false) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await analyzeStock(symbol, {
        includeAi: options?.includeAi ?? true,
        forceRefresh,
      });
      setData(result);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Analysis failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [options?.includeAi]);

  const clear = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return { data, loading, error, analyze, clear };
}
```

Create `src/hooks/useNews.ts`:

```typescript
import { useState, useCallback } from 'react';
import { getNews, type NewsResponse } from '../api/alphaApi';

export function useNews() {
  const [data, setData] = useState<NewsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchNews = useCallback(async (symbol: string, limit = 15) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await getNews(symbol, limit);
      setData(result);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch news';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, fetchNews };
}
```

---

## Component Integration Patterns

### Pattern 1: Stock Search with Analysis

```tsx
import { useState } from 'react';
import { useStockAnalysis } from '../hooks/useStockAnalysis';

export function StockSearch() {
  const [symbol, setSymbol] = useState('');
  const { data, loading, error, analyze } = useStockAnalysis();

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (symbol.trim()) {
      await analyze(symbol.trim());
    }
  };

  return (
    <div>
      <form onSubmit={handleSearch}>
        <input
          value={symbol}
          onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          placeholder="Enter symbol (e.g., AAPL)"
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      {data && (
        <div className="results">
          <h2>{data.company_name} ({data.symbol})</h2>
          <div className="price">
            ${data.quote.price.toFixed(2)}
            <span className={data.quote.change_percent >= 0 ? 'green' : 'red'}>
              {data.quote.change_percent >= 0 ? '+' : ''}
              {data.quote.change_percent.toFixed(2)}%
            </span>
          </div>
          
          {/* Alpha Score */}
          <div className="alpha-score">
            <span className="score">{data.alpha_score.total_score}</span>
            <span className="grade">{data.alpha_score.overall_grade}</span>
          </div>

          {/* AI Analysis */}
          {data.ai_analysis && (
            <AIAnalysisCard analysis={data.ai_analysis} />
          )}
        </div>
      )}
    </div>
  );
}
```

### Pattern 2: AI Analysis with Citations

```tsx
interface AIAnalysisCardProps {
  analysis: AIAnalysis;
}

export function AIAnalysisCard({ analysis }: AIAnalysisCardProps) {
  // Replace [1], [2] citations with clickable links
  const renderWithCitations = (text: string) => {
    return text.replace(/\[(\d+)\]/g, (match, num) => {
      const source = analysis.source_references?.find(s => s.num === parseInt(num));
      if (source) {
        return `<a href="${source.url}" target="_blank" rel="noopener" class="citation" title="${source.source}: ${source.title}">[${num}]</a>`;
      }
      return match;
    });
  };

  return (
    <div className="ai-analysis">
      {/* Sentiment Badge */}
      <div className={`sentiment-badge ${analysis.sentiment}`}>
        {analysis.sentiment.toUpperCase()} ({analysis.confidence}%)
      </div>

      {/* Thesis */}
      {analysis.thesis && (
        <div className="thesis">
          <strong>Thesis:</strong> {analysis.thesis}
        </div>
      )}

      {/* Summary */}
      <p className="summary">{analysis.summary}</p>

      {/* First Principles */}
      {analysis.first_principles && (
        <div className="first-principles">
          <h4>First Principles Analysis</h4>
          <p><strong>Core Question:</strong> {analysis.first_principles.core_question}</p>
          <p><strong>Key Assumptions:</strong></p>
          <ul>
            {analysis.first_principles.key_assumptions.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Key Points with Citations */}
      <div className="key-points">
        <h4>Key Points</h4>
        <ul>
          {analysis.key_points.map((point, i) => (
            <li 
              key={i}
              dangerouslySetInnerHTML={{ __html: renderWithCitations(point) }}
            />
          ))}
        </ul>
      </div>

      {/* Price Projections */}
      {analysis.projections && (
        <div className="projections">
          <h4>Price Projections ({analysis.projections.timeframe})</h4>
          <div className="projection bull">
            🟢 Bull: ${analysis.projections.bull_case.price} - {analysis.projections.bull_case.thesis}
          </div>
          <div className="projection base">
            ⚪ Base: ${analysis.projections.base_case.price} - {analysis.projections.base_case.thesis}
          </div>
          <div className="projection bear">
            🔴 Bear: ${analysis.projections.bear_case.price} - {analysis.projections.bear_case.thesis}
          </div>
        </div>
      )}

      {/* Support/Resistance */}
      {analysis.price_targets && (
        <div className="price-targets">
          <span>Support: ${analysis.price_targets.support}</span>
          <span>Resistance: ${analysis.price_targets.resistance}</span>
        </div>
      )}

      {/* Recommendation */}
      <div className="recommendation">
        <strong>Recommendation:</strong> {analysis.recommendation}
      </div>

      {/* Source References */}
      {analysis.source_references && analysis.source_references.length > 0 && (
        <div className="sources">
          <h4>Sources</h4>
          {analysis.source_references.map((src) => (
            <div key={src.num} className="source">
              <span className="citation-num">[{src.num}]</span>
              <a href={src.url} target="_blank" rel="noopener">
                {src.source}
              </a>
              <span className="title">: {src.title}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

### Pattern 3: News Panel

```tsx
import { useNews } from '../hooks/useNews';

export function NewsPanel({ symbol }: { symbol: string }) {
  const { data, loading, error, fetchNews } = useNews();

  useEffect(() => {
    if (symbol) {
      fetchNews(symbol);
    }
  }, [symbol, fetchNews]);

  if (loading) return <div>Loading news...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!data) return null;

  const sentimentIcon = {
    positive: '🟢',
    negative: '🔴',
    neutral: '⚪',
  };

  return (
    <div className="news-panel">
      <div className="news-header">
        <h3>{data.symbol} News</h3>
        <span className="sentiment">
          Overall: {sentimentIcon[data.overall_sentiment as keyof typeof sentimentIcon]} {data.overall_sentiment}
        </span>
        {data.earnings_date && (
          <span className="earnings">📅 Earnings: {data.earnings_date}</span>
        )}
      </div>

      {data.catalysts.length > 0 && (
        <div className="catalysts">
          <strong>Catalysts:</strong> {data.catalysts.join(', ')}
        </div>
      )}

      <div className="articles">
        {data.articles.map((article) => (
          <a
            key={article.id}
            href={article.url}
            target="_blank"
            rel="noopener"
            className={`article ${article.sentiment}`}
          >
            <span className="sentiment-icon">
              {sentimentIcon[article.sentiment as keyof typeof sentimentIcon]}
            </span>
            <div className="article-content">
              <div className="title">{article.title}</div>
              <div className="meta">
                <span className="source">{article.source}</span>
                <span className="date">
                  {new Date(article.published_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
```

### Pattern 4: Chat Integration

For integrating with an existing chat component, extract stock symbols from user messages and fetch analysis:

```typescript
// Utility to extract stock symbols from text
function extractStockSymbol(text: string): string | null {
  const patterns = [
    /\b([A-Z]{1,5})\b/,           // Direct symbol
    /analyze\s+([A-Za-z]{1,5})/i,  // "analyze AAPL"
    /look at\s+([A-Za-z]{1,5})/i,  // "look at TSLA"
    /what about\s+([A-Za-z]{1,5})/i,
    /check\s+([A-Za-z]{1,5})/i,
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      return match[1].toUpperCase();
    }
  }
  return null;
}

// In your chat handler
async function handleUserMessage(message: string) {
  const symbol = extractStockSymbol(message);
  
  if (symbol) {
    const analysis = await analyzeStock(symbol);
    // Format analysis as chat response
    return formatAnalysisAsMessage(analysis);
  }
  
  // Handle non-stock messages...
}

// Format analysis for chat display
function formatAnalysisAsMessage(data: StockAnalysis): string {
  const { quote, alpha_score, ai_analysis } = data;
  
  let message = `## ${data.company_name} (${data.symbol})\n\n`;
  message += `**Price:** $${quote.price.toFixed(2)} (${quote.change_percent >= 0 ? '+' : ''}${quote.change_percent.toFixed(2)}%)\n\n`;
  message += `**Alpha Score:** ${alpha_score.total_score} (${alpha_score.overall_grade})\n\n`;
  
  if (ai_analysis) {
    message += `### AI Analysis\n`;
    message += `**${ai_analysis.sentiment.toUpperCase()}** (${ai_analysis.confidence}% confidence)\n\n`;
    message += `${ai_analysis.summary}\n\n`;
    
    if (ai_analysis.recommendation) {
      message += `**Recommendation:** ${ai_analysis.recommendation}\n`;
    }
  }
  
  return message;
}
```

---

## Environment Setup

Create `.env` in your React project root:

```env
VITE_API_URL=http://localhost:8000/api
```

For production:
```env
VITE_API_URL=https://your-api-domain.com/api
```

---

## CSS Suggestions

```css
/* Sentiment colors */
.bullish, .positive, .green { color: #22c55e; }
.bearish, .negative, .red { color: #ef4444; }
.neutral { color: #6b7280; }

/* Citations */
.citation {
  color: #3b82f6;
  text-decoration: none;
  font-size: 0.8em;
  vertical-align: super;
}
.citation:hover {
  text-decoration: underline;
}

/* Alpha Score */
.alpha-score {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.alpha-score .score {
  font-size: 2rem;
  font-weight: bold;
}
.alpha-score .grade {
  padding: 0.25rem 0.5rem;
  background: #1f2937;
  border-radius: 4px;
}

/* News article */
.article {
  display: flex;
  padding: 0.75rem;
  border-bottom: 1px solid #374151;
  text-decoration: none;
  color: inherit;
}
.article:hover {
  background: #1f2937;
}
.article.positive { border-left: 3px solid #22c55e; }
.article.negative { border-left: 3px solid #ef4444; }
```

---

## Quick Start Checklist

1. [ ] Copy `src/types/api.ts` - TypeScript interfaces
2. [ ] Copy `src/api/alphaApi.ts` - API client
3. [ ] Copy hooks to `src/hooks/`
4. [ ] Add `VITE_API_URL` to `.env`
5. [ ] Integrate components into existing UI
6. [ ] Style with your design system

---

## API is Running At

```
http://localhost:8000

Docs: http://localhost:8000/docs
Health: http://localhost:8000/api/health
```

Start the API:
```bash
cd /path/to/breakoutbot
python3 run_api.py
```

