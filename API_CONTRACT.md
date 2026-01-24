# Alpha Discovery API Contract

This document defines the API contract between the React frontend and the Python backend.

## Base URL

```
Development: http://localhost:8000/api
Production: https://your-domain.com/api
```

---

## Endpoints

### 1. Health Check

```
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-24T20:00:00Z"
}
```

---

### 2. Full Stock Analysis (Primary Endpoint)

```
GET /api/analyze/{symbol}
```

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| include_options | bool | true | Include options chain data |
| include_news | bool | true | Include news articles |
| include_ai | bool | true | Include AI analysis |

**Response Structure:**
```typescript
interface AnalysisResponse {
  symbol: string;
  company_name: string;
  quote: Quote;
  technicals: Technicals;
  volume_metrics: VolumeMetrics;
  alpha_score: AlphaScore;
  options?: OptionsData;
  news?: NewsData;
  fundamentals?: Fundamentals;
  ai_analysis?: AIAnalysis;
  analyzed_at: string;
}
```

**Example Response:**
```json
{
  "symbol": "AAPL",
  "company_name": "Apple Inc.",
  "quote": {
    "symbol": "AAPL",
    "price": 185.50,
    "change": 2.30,
    "change_percent": 1.25,
    "volume": 45000000,
    "open": 183.20,
    "high": 186.00,
    "low": 182.50
  },
  "volume_metrics": {
    "current_volume": 45000000,
    "relative_volume": 1.35,
    "relative_volume_label": "high",
    "volume_trend_5d": "increasing",
    "dollar_volume_formatted": "$8.35B",
    "accumulation_distribution": "accumulation"
  },
  "alpha_score": {
    "total_score": 65,
    "signal_strength": "strong",
    "overall_grade": "B",
    "momentum_grade": "B",
    "trend_grade": "A",
    "risk_reward_grade": "B",
    "bullish_signals": 5,
    "bearish_signals": 1,
    "signals": [
      {
        "name": "Golden Cross",
        "type": "bullish",
        "strength": 4,
        "description": "50 SMA above 200 SMA"
      }
    ],
    "summary": "Strong bullish setup with 5 bullish signals"
  },
  "ai_analysis": {
    "summary": "AAPL shows strong technical momentum...",
    "sentiment": "bullish",
    "confidence": 75,
    "thesis": "Apple's services growth supports premium valuation",
    "first_principles": {
      "core_question": "Can Apple maintain margins while growing services?",
      "key_assumptions": ["Services growth continues", "iPhone demand stable"],
      "what_must_be_true": ["No major product delays", "China demand recovers"]
    },
    "key_points": [
      "[1] Analysts raise price targets ahead of earnings",
      "[2] Services revenue growth accelerating",
      "Technical breakout above key resistance"
    ],
    "news_analysis": {
      "summary": "Recent coverage focuses on AI integration",
      "cited_sources": [1, 2, 5],
      "sentiment_driver": "Positive analyst commentary"
    },
    "catalysts": [
      "Earnings report (Jan 28) - high impact",
      "WWDC announcements (June) - medium impact"
    ],
    "risks": [
      "China revenue weakness (prob: medium)",
      "Antitrust regulation (prob: low)"
    ],
    "projections": {
      "bull_case": {"price": 210, "thesis": "AI features drive upgrade cycle"},
      "base_case": {"price": 195, "thesis": "Steady growth continues"},
      "bear_case": {"price": 165, "thesis": "China weakness persists"},
      "timeframe": "3-6 months"
    },
    "price_targets": {
      "support": 178.50,
      "resistance": 195.00
    },
    "recommendation": "Accumulate on pullbacks to $180 support",
    "sources_cited": [1, 2, 5],
    "source_references": [
      {
        "num": 1,
        "source": "Reuters",
        "title": "Apple analysts raise price targets...",
        "url": "https://...",
        "date": "2024-01-24"
      }
    ]
  }
}
```

---

### 3. News Only

```
GET /api/news/{symbol}
```

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| limit | int | 15 | Max articles (1-50) |

**Response:**
```json
{
  "symbol": "AAPL",
  "overall_sentiment": "positive",
  "earnings_date": "2024-01-28",
  "catalysts": ["Earnings report", "Analyst upgrades"],
  "article_count": 15,
  "articles": [
    {
      "id": 1,
      "title": "Apple Stock Rises on Strong Demand...",
      "source": "Reuters",
      "url": "https://reuters.com/...",
      "published_at": "2024-01-24T15:30:00Z",
      "sentiment": "positive",
      "summary": null
    }
  ]
}
```

---

### 4. Quick Quote

```
GET /api/quote/{symbol}
```

**Response:**
```json
{
  "symbol": "AAPL",
  "price": 185.50,
  "open": 183.20,
  "high": 186.00,
  "low": 182.50,
  "close": 185.50,
  "volume": 45000000,
  "previous_close": 183.20,
  "change": 2.30,
  "change_percent": 1.25,
  "timestamp": "2024-01-24T20:00:00Z"
}
```

---

### 5. Technical Indicators

```
GET /api/technicals/{symbol}
```

**Response:**
```json
{
  "symbol": "AAPL",
  "price": 185.50,
  "technicals": {
    "moving_averages": {
      "sma_20": 182.30,
      "sma_50": 178.50,
      "sma_200": 172.00,
      "ema_20": 183.10,
      "price_vs_sma_20": "above",
      "price_vs_sma_50": "above",
      "price_vs_sma_200": "above",
      "golden_cross": true,
      "death_cross": false
    },
    "momentum": {
      "rsi": 58.5,
      "rsi_signal": "neutral",
      "macd": 1.25,
      "macd_signal": 0.98,
      "macd_histogram": 0.27,
      "macd_trend": "bullish"
    },
    "volatility": {
      "bb_upper": 192.00,
      "bb_middle": 182.30,
      "bb_lower": 172.60,
      "bb_position": "within",
      "atr": 3.50,
      "atr_percent": 1.89
    },
    "volume": {
      "current_volume": 45000000,
      "avg_volume_20d": 35000000,
      "volume_ratio": 1.29,
      "is_unusual": false,
      "volume_trend": "increasing"
    },
    "price_levels": {
      "ath": 199.62,
      "atl": 53.15,
      "week_52_high": 199.62,
      "week_52_low": 164.08,
      "distance_from_ath": -7.08,
      "distance_from_52w_high": -7.08
    },
    "overall_trend": "bullish"
  }
}
```

---

### 6. Options Data

```
GET /api/options/{symbol}
```

**Response:**
```json
{
  "symbol": "AAPL",
  "options": {
    "expirations": ["2024-01-26", "2024-02-02", "..."],
    "put_call_ratio": 0.65,
    "total_call_volume": 125000,
    "total_put_volume": 81250,
    "total_call_oi": 500000,
    "total_put_oi": 320000,
    "max_pain": 185.00,
    "unusual_activity": [
      {
        "type": "call",
        "strike": 190.00,
        "expiration": "2024-01-26",
        "volume": 15000,
        "open_interest": 5000,
        "volume_oi_ratio": 3.0,
        "implied_volatility": 28.5
      }
    ]
  },
  "sentiment": {
    "sentiment": "bullish",
    "confidence": 70,
    "signals": [
      "Low P/C ratio (0.65) - Bullish",
      "Unusual call activity (5 vs 2 puts)"
    ]
  }
}
```

---

## TypeScript Types for React

```typescript
// src/types/api.ts

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

export interface VolumeMetrics {
  current_volume: number;
  relative_volume: number;
  relative_volume_label: string;
  volume_trend_5d: string;
  dollar_volume_formatted: string;
  accumulation_distribution: 'accumulation' | 'distribution' | 'neutral';
}

export interface Projections {
  bull_case: { price: number; thesis: string };
  base_case: { price: number; thesis: string };
  bear_case: { price: number; thesis: string };
  timeframe: string;
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
  first_principles?: {
    core_question: string;
    key_assumptions: string[];
    what_must_be_true: string[];
  };
  key_points: string[]; // May include [1], [2] citations
  news_analysis?: {
    summary: string;
    cited_sources: number[];
    sentiment_driver: string;
  };
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

export interface StockAnalysis {
  symbol: string;
  company_name: string;
  quote: Quote;
  volume_metrics: VolumeMetrics;
  alpha_score: AlphaScore;
  technicals: any; // Full technicals object
  options?: any;
  news?: any;
  fundamentals?: any;
  ai_analysis?: AIAnalysis;
  analyzed_at: string;
}
```

---

## React Integration Pattern

### Recommended Architecture

```
src/
├── api/
│   └── alphaApi.ts       # API client functions
├── hooks/
│   ├── useStockAnalysis.ts
│   └── useNews.ts
├── types/
│   └── api.ts            # TypeScript interfaces
├── components/
│   ├── StockSearch.tsx
│   ├── NewsPanel.tsx
│   ├── AIAnalysisCard.tsx
│   ├── AlphaScoreCard.tsx
│   └── ChatWithStock.tsx
└── utils/
    └── formatters.ts     # Price, date formatting
```

### API Client Example

```typescript
// src/api/alphaApi.ts
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export async function analyzeStock(symbol: string): Promise<StockAnalysis> {
  const res = await fetch(`${API_BASE}/analyze/${symbol}`);
  if (!res.ok) throw new Error(`Analysis failed for ${symbol}`);
  return res.json();
}

export async function getNews(symbol: string): Promise<NewsResponse> {
  const res = await fetch(`${API_BASE}/news/${symbol}`);
  if (!res.ok) throw new Error(`News fetch failed for ${symbol}`);
  return res.json();
}
```

### Displaying Cited Sources

The AI analysis includes citations like `[1]`, `[2]` in key_points. Match these to `source_references`:

```tsx
function AIAnalysisCard({ analysis }: { analysis: AIAnalysis }) {
  const renderWithCitations = (text: string) => {
    // Replace [1], [2] with clickable links
    return text.replace(/\[(\d+)\]/g, (match, num) => {
      const source = analysis.source_references?.find(s => s.num === parseInt(num));
      if (source) {
        return `<a href="${source.url}" target="_blank" title="${source.source}">[${num}]</a>`;
      }
      return match;
    });
  };

  return (
    <div className="ai-analysis">
      <h3>{analysis.sentiment.toUpperCase()} ({analysis.confidence}%)</h3>
      <p>{analysis.summary}</p>
      
      <h4>Key Points</h4>
      <ul>
        {analysis.key_points.map((point, i) => (
          <li key={i} dangerouslySetInnerHTML={{ __html: renderWithCitations(point) }} />
        ))}
      </ul>

      {/* Source References */}
      {analysis.source_references && (
        <div className="sources">
          <h4>Sources</h4>
          {analysis.source_references.map(src => (
            <div key={src.num}>
              [{src.num}] <a href={src.url}>{src.source}</a>: {src.title}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## Error Handling

All endpoints return errors in this format:

```json
{
  "detail": "Symbol XYZ not found"
}
```

HTTP Status Codes:
- `200` - Success
- `404` - Symbol not found
- `422` - Validation error
- `500` - Server error

---

## CORS

The API allows requests from:
- `http://localhost:5173` (Vite default)
- `http://localhost:3000`

To add more origins, update `api/config.py`:

```python
CORS_ORIGINS = [
    "http://localhost:5173",
    "https://your-production-domain.com",
]
```

