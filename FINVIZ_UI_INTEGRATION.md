# Finviz-Style UI Integration Guide

> **For Antigravity**: Complete API documentation for building a Finviz-style market dashboard

---

## Overview

The Alpha Discovery API provides Finviz-style market data endpoints that update **automatically every 30 minutes** via a background scanner. All endpoints return JSON and are ready for React integration.

**Base URL**: `http://localhost:8000`

---

## 📊 Core Dashboard Endpoints

### 1. Market Overview (Homepage Data)

```
GET /api/market/overview
```

Returns complete dashboard data in a single call - use this for the main homepage.

**Response:**
```typescript
interface MarketOverview {
  breadth: {
    advancing: number;       // Stocks up today
    declining: number;       // Stocks down today
    unchanged: number;       // Flat stocks
    total: number;
    advance_decline_ratio: number;  // e.g., 0.55
    advance_percent: number;        // e.g., 34.5
    decline_percent: number;        // e.g., 63.2
    new_highs: number;       // At 52-week high
    new_lows: number;        // At 52-week low
  };
  sectors: SectorPerformance[];
  sma_analysis: {
    sma50: { above: number; below: number; above_percent: number };
    sma200: { above: number; below: number; above_percent: number };
  };
  stats: {
    total_stocks: number;
    unusual_volume_count: number;
    near_52w_high_count: number;
    big_gainers_count: number;
    big_losers_count: number;
    last_scan: string;       // ISO timestamp
  };
  top_gainers: Stock[];      // Top 10
  top_losers: Stock[];       // Top 10
  most_active: Stock[];      // Top 10 by volume
  unusual_volume: Stock[];   // Top 10 unusual volume
  updated_at: string;        // ISO timestamp
}
```

---

## 📈 Ranking Lists

### 2. Top Gainers

```
GET /api/market/gainers?limit=50&market_cap=large
```

**Query Params:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | number | 50 | Results to return (1-200) |
| `min_volume` | number | 100000 | Minimum volume filter |
| `market_cap` | string | null | "micro", "small", "mid", "large", "mega" |

**Response:**
```typescript
interface GainersResponse {
  count: number;
  stocks: StockRanking[];
  updated_at: string;
}

interface StockRanking {
  rank: number;
  ticker: string;           // "AAPL"
  company: string;          // "Apple Inc."
  last: number;             // Current price
  change: number;           // % change (e.g., 5.23)
  volume: number;           // Trading volume
  relativeVolume: number;   // RVOL (e.g., 1.5 = 150% of avg)
  marketCap: number;        // Market cap in dollars
  sector: string;           // "Technology"
  signal: string;           // "Top Gainers" or "Gainers"
}
```

### 3. Top Losers

```
GET /api/market/losers?limit=50
```

Same params and response as gainers, but sorted by worst performers.

### 4. Most Active (By Volume)

```
GET /api/market/most-active?limit=50
```

**Response:** Same as `StockRanking[]` with `signal: "Most Active"`

### 5. Most Volatile

```
GET /api/market/most-volatile?limit=50
```

Returns stocks with biggest absolute % moves (either direction).

**Response:** Same as `StockRanking[]` plus:
```typescript
{
  absChange: number;  // Absolute value of change %
  signal: "Most Volatile"
}
```

### 6. Unusual Volume

```
GET /api/market/unusual-volume?limit=50&min_rvol=2.0
```

**Query Params:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | number | 50 | Results to return |
| `min_rvol` | number | 2.0 | Min relative volume (2.0 = 200% of avg) |
| `market_cap` | string | null | Market cap filter |

**Response:**
```typescript
interface UnusualVolumeStock {
  rank: number;
  ticker: string;
  company: string;
  last: number;
  change: number;
  volume: number;
  avgVolume: number;        // 20-day average
  relativeVolume: number;   // Current / Avg
  sector: string;
  signal: "Unusual Volume"
}
```

---

## 📍 Breakout / Breakdown Lists

### 7. New 52-Week Highs

```
GET /api/market/new-highs?limit=50
```

**Response:**
```typescript
interface NewHighStock {
  rank: number;
  ticker: string;
  company: string;
  last: number;
  change: number;
  high52w: number;              // 52-week high price
  distanceFromHigh: number;     // % distance (e.g., -0.5 = 0.5% below)
  volume: number;
  sector: string;
  signal: "New High" | "Near High"
}
```

### 8. New 52-Week Lows

```
GET /api/market/new-lows?limit=50
```

**Response:** Same structure with `low52w` and `distanceFromLow` fields.

---

## 🗺️ Sector Heatmap

### 9. Heatmap Data (For Treemap Visualization)

```
GET /api/market/heatmap
```

Returns stocks organized by sector - ideal for building a treemap like Finviz.

**Response:**
```typescript
interface HeatmapResponse {
  sectors: {
    [sectorName: string]: {
      stocks: HeatmapStock[];
      avgChange: number;      // Sector average % change
      stockCount: number;
    }
  };
  sectorSummary: SectorPerformance[];
  updated_at: string;
}

interface HeatmapStock {
  symbol: string;
  name: string;
  price: number;
  change: number;       // % change - use for color coding
  marketCap: number;    // Use for box size
  capCategory: string;  // "mega", "large", "mid", "small", "micro"
  volume: number;
  rvol: number;
}
```

**UI Implementation Notes:**
- Box SIZE = proportional to `marketCap`
- Box COLOR = based on `change` (green for positive, red for negative)
- Organize boxes by sector groups
- Use a treemap library like `recharts` or `d3`

### 10. Sector Performance (For Sector Bar Chart)

```
GET /api/market/sectors
```

**Response:**
```typescript
interface SectorsResponse {
  sectors: SectorPerformance[];
  updated_at: string;
}

interface SectorPerformance {
  sector: string;              // "Technology"
  stock_count: number;         // Stocks in sector
  avg_change: number;          // Average % change
  percent_advancing: number;   // % of stocks up
  avg_rvol: number;            // Average relative volume
  total_volume: number;        // Combined volume
  total_market_cap: number;    // Combined market cap
}
```

---

## 📰 Headlines

### 11. Top Market Headlines

```
GET /api/market/headlines?limit=20
```

**Response:**
```typescript
interface HeadlinesResponse {
  headlines: Headline[];
  count: number;
  marketSentiment: "bullish" | "bearish" | "neutral";
  sentimentBreakdown: {
    positive: number;
    negative: number;
    neutral: number;
  };
  updated_at: string;
}

interface Headline {
  id: number;
  title: string;
  source: string;           // "Reuters", "CNBC", etc.
  url: string;
  published: string;        // ISO timestamp
  sentiment: "positive" | "negative" | "neutral";
  age: string;              // "2h ago", "1d ago"
}
```

---

## 📊 Market Breadth

### 12. Market Breadth Indicators

```
GET /api/market/breadth
```

**Response:**
```typescript
interface BreadthResponse {
  advancing: number;
  declining: number;
  unchanged: number;
  total: number;
  advance_decline_ratio: number;
  advance_percent: number;
  decline_percent: number;
  new_highs: number;
  new_lows: number;
  sma_analysis: {
    sma50: { above: number; below: number; above_percent: number };
    sma200: { above: number; below: number; above_percent: number };
  };
  updated_at: string;
}
```

---

## 🔄 Scanner Status

### 13. Check Scanner Status

```
GET /api/scanner/status
```

**Response:**
```typescript
interface ScannerStatus {
  running: boolean;
  scan_in_progress: boolean;
  last_scan: string | null;     // ISO timestamp
  interval_minutes: number;     // 30
  db_stats: {
    total_stocks: number;
    unusual_volume_count: number;
    near_52w_high_count: number;
    big_gainers_count: number;
    big_losers_count: number;
    last_scan: string;
    last_scan_stocks: number;
  };
}
```

### 14. Manually Trigger Scan

```
POST /api/scanner/trigger
```

Triggers an immediate market scan (useful for testing).

---

## 🎨 UI Component Mapping

| Finviz Feature | API Endpoint | Component Type |
|----------------|--------------|----------------|
| Market Overview Stats | `/api/market/overview` | Dashboard cards |
| Advancing/Declining Bar | `/api/market/breadth` | Progress bar |
| Top Gainers Table | `/api/market/gainers` | Data table |
| Top Losers Table | `/api/market/losers` | Data table |
| Most Active Table | `/api/market/most-active` | Data table |
| Sector Heatmap | `/api/market/heatmap` | Treemap chart |
| Sector Performance | `/api/market/sectors` | Bar chart |
| News Headlines | `/api/market/headlines` | News feed list |
| 52W High List | `/api/market/new-highs` | Data table |
| 52W Low List | `/api/market/new-lows` | Data table |
| Unusual Volume | `/api/market/unusual-volume` | Data table |

---

## 📱 TypeScript Types (Copy/Paste Ready)

```typescript
// Base stock type for tables
interface Stock {
  symbol: string;
  company_name: string;
  price: number;
  change_percent: number;
  volume: number;
  relative_volume: number;
  market_cap: number;
  market_cap_category: string;
  sector: string;
  industry: string;
  week_52_high: number;
  week_52_low: number;
  distance_from_52w_high: number;
  distance_from_52w_low: number;
}

// For ranking tables (gainers, losers, etc.)
interface RankedStock {
  rank: number;
  ticker: string;
  company: string;
  last: number;
  change: number;
  volume: number;
  relativeVolume: number;
  marketCap: number;
  sector: string;
  signal: string;
}

// Sector data
interface SectorData {
  sector: string;
  stock_count: number;
  avg_change: number;
  percent_advancing: number;
  avg_rvol: number;
  total_volume: number;
  total_market_cap: number;
}

// Market breadth
interface MarketBreadth {
  advancing: number;
  declining: number;
  unchanged: number;
  total: number;
  advance_decline_ratio: number;
  advance_percent: number;
  decline_percent: number;
  new_highs: number;
  new_lows: number;
}

// Headline
interface Headline {
  id: number;
  title: string;
  source: string;
  url: string;
  published: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  age: string;
}

// Heatmap stock
interface HeatmapStock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  marketCap: number;
  capCategory: string;
  volume: number;
  rvol: number;
}
```

---

## 🚀 React Hook Examples

### useDashboard Hook

```typescript
import { useState, useEffect } from 'react';

interface DashboardData {
  overview: MarketOverview | null;
  gainers: RankedStock[];
  losers: RankedStock[];
  headlines: Headline[];
  loading: boolean;
  error: string | null;
  lastUpdate: string | null;
}

export function useDashboard() {
  const [data, setData] = useState<DashboardData>({
    overview: null,
    gainers: [],
    losers: [],
    headlines: [],
    loading: true,
    error: null,
    lastUpdate: null,
  });

  const fetchDashboard = async () => {
    try {
      const [overviewRes, gainersRes, losersRes, headlinesRes] = await Promise.all([
        fetch('/api/market/overview'),
        fetch('/api/market/gainers?limit=20'),
        fetch('/api/market/losers?limit=20'),
        fetch('/api/market/headlines?limit=10'),
      ]);

      const [overview, gainers, losers, headlines] = await Promise.all([
        overviewRes.json(),
        gainersRes.json(),
        losersRes.json(),
        headlinesRes.json(),
      ]);

      setData({
        overview,
        gainers: gainers.stocks,
        losers: losers.stocks,
        headlines: headlines.headlines,
        loading: false,
        error: null,
        lastUpdate: overview.updated_at,
      });
    } catch (err) {
      setData(prev => ({ ...prev, loading: false, error: 'Failed to fetch' }));
    }
  };

  useEffect(() => {
    fetchDashboard();
    
    // Refresh every 2 minutes
    const interval = setInterval(fetchDashboard, 120000);
    return () => clearInterval(interval);
  }, []);

  return { ...data, refresh: fetchDashboard };
}
```

### useHeatmap Hook

```typescript
export function useHeatmap() {
  const [data, setData] = useState<HeatmapResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/market/heatmap')
      .then(res => res.json())
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  return { data, loading };
}
```

---

## 🎨 Color Coding Reference

### Change % Color Scale
```typescript
const getChangeColor = (change: number): string => {
  if (change >= 5) return '#00C805';      // Bright green
  if (change >= 2) return '#26A641';      // Green
  if (change >= 0.5) return '#3FB950';    // Light green
  if (change > -0.5) return '#6B7280';    // Gray (flat)
  if (change > -2) return '#F97583';      // Light red
  if (change > -5) return '#DA3633';      // Red
  return '#B62324';                        // Bright red
};
```

### Volume Color Scale
```typescript
const getVolumeColor = (rvol: number): string => {
  if (rvol >= 3) return '#FFD700';        // Gold - very high
  if (rvol >= 2) return '#FFA500';        // Orange - high
  if (rvol >= 1.5) return '#4ADE80';      // Green - above avg
  return '#6B7280';                        // Gray - normal
};
```

---

## 📋 Sample Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  MARKET OVERVIEW                                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │Advancing │ │Declining │ │New Highs │ │New Lows  │           │
│  │  213     │ │  390     │ │   55     │ │   11     │           │
│  │ 34.5%    │ │ 63.2%    │ │          │ │          │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
├─────────────────────────────────────────────────────────────────┤
│  [=========== ADV 34.5% ===========|====== DEC 63.2% ======]   │
├──────────────────────────────┬──────────────────────────────────┤
│  TOP GAINERS                 │  TOP LOSERS                      │
│  ┌─────┬───────┬───────┐     │  ┌─────┬───────┬───────┐         │
│  │Tick │ Last  │Change │     │  │Tick │ Last  │Change │         │
│  ├─────┼───────┼───────┤     │  ├─────┼───────┼───────┤         │
│  │AKAN │ $1.50 │+11.1% │     │  │INTC │$45.07 │-17.0% │         │
│  │APLD │$37.69 │ +8.5% │     │  │APGE │$70.02 │-12.3% │         │
│  │AEMD │ $3.28 │ +7.5% │     │  │AEHR │$28.04 │ -9.3% │         │
│  └─────┴───────┴───────┘     │  └─────┴───────┴───────┘         │
├──────────────────────────────┴──────────────────────────────────┤
│  SECTOR HEATMAP                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  ┌─────────┐ ┌───────┐ ┌──────┐ ┌─────┐                    │ │
│  │  │  TECH   │ │FINANCE│ │HEALTH│ │ENRGY│  ...               │ │
│  │  │ -1.53%  │ │ -0.2% │ │-0.9% │ │+0.5%│                    │ │
│  │  │ [AAPL]  │ │ [JPM] │ │[JNJ] │ │[XOM]│                    │ │
│  │  │ [MSFT]  │ │ [BAC] │ │[UNH] │ │[CVX]│                    │ │
│  │  │ [NVDA]  │ │ [WFC] │ │[PFE] │ │     │                    │ │
│  │  └─────────┘ └───────┘ └──────┘ └─────┘                    │ │
│  └────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  HEADLINES                                                      │
│  • Intel drops 17% on earnings miss                    [2h ago] │
│  • S&P 500 closes mixed as tech weighs                 [3h ago] │
│  • Fed signals patience on rate cuts                   [5h ago] │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Data Refresh

- **Scanner runs**: Every 30 minutes automatically
- **Data availability**: Instant via SQLite cache
- **Recommended UI refresh**: Every 1-2 minutes for active users
- **Scanner status**: Check `/api/scanner/status` for last update time

---

## 🔗 Quick Links

| Feature | Endpoint |
|---------|----------|
| Full Dashboard | `GET /api/market/overview` |
| Top Gainers | `GET /api/market/gainers` |
| Top Losers | `GET /api/market/losers` |
| Most Active | `GET /api/market/most-active` |
| Unusual Volume | `GET /api/market/unusual-volume` |
| New Highs | `GET /api/market/new-highs` |
| New Lows | `GET /api/market/new-lows` |
| Headlines | `GET /api/market/headlines` |
| Heatmap | `GET /api/market/heatmap` |
| Sectors | `GET /api/market/sectors` |
| Breadth | `GET /api/market/breadth` |
| Scanner Status | `GET /api/scanner/status` |

---

**API Docs**: http://localhost:8000/docs (Swagger UI)

