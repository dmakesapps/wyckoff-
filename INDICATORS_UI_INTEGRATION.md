# Market Indicators UI Integration Guide

## Overview

The API provides 7 market indicator categories that update every 30 minutes. This guide shows how to integrate them into your React UI.

---

## API Endpoints

### 1. All Indicators (Main Dashboard)
```
GET http://localhost:8000/api/market/indicators
```

### 2. Fear & Greed Only
```
GET http://localhost:8000/api/market/fear-greed
```

### 3. Historical Data (For Charts)
```
GET http://localhost:8000/api/market/indicators/history?limit=48
```

---

## TypeScript Types

```typescript
// types/indicators.ts

export interface MarketIndicators {
  timestamp: string;
  market_breadth: MarketBreadth;
  volume_analysis: VolumeAnalysis;
  momentum: Momentum;
  sector_performance: SectorPerformance[];
  fear_greed: FearGreed;
  volatility: Volatility;
}

export interface MarketBreadth {
  advancing: number;
  declining: number;
  unchanged: number;
  total: number;
  ad_ratio: number;           // Advance/Decline ratio
  ad_line: number;            // Advancing - Declining
  advance_percent: number;    // % of stocks advancing
  decline_percent: number;    // % of stocks declining
  new_highs: number;          // Stocks at 52-week high
  new_lows: number;           // Stocks at 52-week low
}

export interface VolumeAnalysis {
  up_volume: number;          // Total volume of advancing stocks
  down_volume: number;        // Total volume of declining stocks
  volume_ratio: number;       // up_volume / down_volume
  total_volume: number;
  unusual_volume_count: number; // Stocks with 2x+ avg volume
  up_volume_percent: number;  // % of volume in advancing stocks
}

export interface Momentum {
  gainers_1pct: number;       // Stocks up 1%+
  gainers_3pct: number;       // Stocks up 3%+
  gainers_5pct: number;       // Stocks up 5%+
  losers_1pct: number;        // Stocks down 1%+
  losers_3pct: number;        // Stocks down 3%+
  losers_5pct: number;        // Stocks down 5%+
  net_gainers_1pct: number;   // gainers_1pct - losers_1pct
  net_gainers_3pct: number;   // gainers_3pct - losers_3pct
}

export interface SectorPerformance {
  sector: string;
  stock_count: number;
  avg_change: number;
  percent_advancing: number;
  avg_rvol: number;
  total_volume: number;
  total_market_cap: number;
}

export interface FearGreed {
  score: number;              // 0-100
  label: string;              // "Extreme Fear" | "Fear" | "Neutral" | "Greed" | "Extreme Greed"
  components: {
    breadth: number;          // 0-100
    volume: number;           // 0-100
    momentum: number;         // 0-100
    strength: number;         // 0-100
  };
  interpretation: string;     // Human-readable explanation
}

export interface Volatility {
  big_movers_up: number;      // Stocks up 5%+
  big_movers_down: number;    // Stocks down 5%+
  total_big_movers: number;
  volatility_level: "low" | "moderate" | "high" | "extreme";
}

// Fear & Greed endpoint response
export interface FearGreedResponse {
  score: number;
  label: string;
  components: {
    breadth: number;
    volume: number;
    momentum: number;
    strength: number;
  };
  interpretation: string;
  timestamp: string;
}

// History endpoint response
export interface IndicatorHistory {
  history: HistoryEntry[];
  count: number;
}

export interface HistoryEntry {
  timestamp: string;
  fear_greed_score: number;
  fear_greed_label: string;
  advancing: number;
  declining: number;
  ad_ratio: number;
  volume_ratio: number;
}
```

---

## API Client

```typescript
// api/indicators.ts

const API_BASE = 'http://localhost:8000';

export async function fetchIndicators(): Promise<MarketIndicators> {
  const res = await fetch(`${API_BASE}/api/market/indicators`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchFearGreed(): Promise<FearGreedResponse> {
  const res = await fetch(`${API_BASE}/api/market/fear-greed`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchIndicatorHistory(limit = 48): Promise<IndicatorHistory> {
  const res = await fetch(`${API_BASE}/api/market/indicators/history?limit=${limit}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
```

---

## React Hook

```typescript
// hooks/useMarketIndicators.ts

import { useState, useEffect } from 'react';
import { fetchIndicators, MarketIndicators } from '../api/indicators';

export function useMarketIndicators(refreshInterval = 60000) {
  const [indicators, setIndicators] = useState<MarketIndicators | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const data = await fetchIndicators();
        setIndicators(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load');
      } finally {
        setLoading(false);
      }
    }

    load();
    const interval = setInterval(load, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  return { indicators, loading, error };
}
```

---

## UI Components

### 1. Fear & Greed Gauge

```tsx
// components/FearGreedGauge.tsx

import { FearGreed } from '../types/indicators';

interface Props {
  data: FearGreed;
}

export function FearGreedGauge({ data }: Props) {
  const { score, label } = data;
  
  // Color based on score
  const getColor = (score: number) => {
    if (score <= 20) return '#dc2626'; // red - extreme fear
    if (score <= 40) return '#f97316'; // orange - fear
    if (score <= 60) return '#eab308'; // yellow - neutral
    if (score <= 80) return '#84cc16'; // lime - greed
    return '#22c55e'; // green - extreme greed
  };

  const getEmoji = (label: string) => {
    switch (label) {
      case 'Extreme Fear': return '😱';
      case 'Fear': return '😟';
      case 'Neutral': return '😐';
      case 'Greed': return '😊';
      case 'Extreme Greed': return '🤑';
      default: return '📊';
    }
  };

  return (
    <div className="fear-greed-gauge">
      <div className="gauge-header">
        <span className="emoji">{getEmoji(label)}</span>
        <h3>Fear & Greed Index</h3>
      </div>
      
      <div className="gauge-score" style={{ color: getColor(score) }}>
        {score}
      </div>
      
      <div className="gauge-label">{label}</div>
      
      {/* Progress bar */}
      <div className="gauge-bar">
        <div 
          className="gauge-fill"
          style={{ 
            width: `${score}%`,
            backgroundColor: getColor(score)
          }}
        />
      </div>
      
      <div className="gauge-scale">
        <span>0 Fear</span>
        <span>50</span>
        <span>100 Greed</span>
      </div>
      
      <p className="interpretation">{data.interpretation}</p>
      
      {/* Component breakdown */}
      <div className="components">
        <ComponentBar label="Breadth" value={data.components.breadth} />
        <ComponentBar label="Volume" value={data.components.volume} />
        <ComponentBar label="Momentum" value={data.components.momentum} />
        <ComponentBar label="Strength" value={data.components.strength} />
      </div>
    </div>
  );
}

function ComponentBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="component-row">
      <span className="component-label">{label}</span>
      <div className="component-bar">
        <div className="component-fill" style={{ width: `${value}%` }} />
      </div>
      <span className="component-value">{value.toFixed(1)}</span>
    </div>
  );
}
```

### 2. Market Breadth Card

```tsx
// components/MarketBreadthCard.tsx

import { MarketBreadth } from '../types/indicators';

interface Props {
  data: MarketBreadth;
}

export function MarketBreadthCard({ data }: Props) {
  const bullish = data.ad_ratio >= 1;
  
  return (
    <div className="breadth-card">
      <h3>📊 Market Breadth</h3>
      
      <div className="breadth-main">
        <div className="advancing">
          <span className="number green">▲ {data.advancing}</span>
          <span className="label">Advancing ({data.advance_percent}%)</span>
        </div>
        <div className="declining">
          <span className="number red">▼ {data.declining}</span>
          <span className="label">Declining ({data.decline_percent}%)</span>
        </div>
      </div>
      
      {/* Visual bar */}
      <div className="breadth-bar">
        <div 
          className="advancing-bar"
          style={{ width: `${data.advance_percent}%` }}
        />
      </div>
      
      <div className="breadth-stats">
        <div className="stat">
          <span className="stat-label">A/D Ratio</span>
          <span className={`stat-value ${bullish ? 'green' : 'red'}`}>
            {data.ad_ratio.toFixed(2)}
          </span>
        </div>
        <div className="stat">
          <span className="stat-label">A/D Line</span>
          <span className={`stat-value ${data.ad_line >= 0 ? 'green' : 'red'}`}>
            {data.ad_line > 0 ? '+' : ''}{data.ad_line}
          </span>
        </div>
        <div className="stat">
          <span className="stat-label">New Highs</span>
          <span className="stat-value green">{data.new_highs}</span>
        </div>
        <div className="stat">
          <span className="stat-label">New Lows</span>
          <span className="stat-value red">{data.new_lows}</span>
        </div>
      </div>
    </div>
  );
}
```

### 3. Volume Analysis Card

```tsx
// components/VolumeAnalysisCard.tsx

import { VolumeAnalysis } from '../types/indicators';

interface Props {
  data: VolumeAnalysis;
}

export function VolumeAnalysisCard({ data }: Props) {
  const bullish = data.volume_ratio >= 1;
  
  const formatVolume = (vol: number) => {
    if (vol >= 1e9) return `${(vol / 1e9).toFixed(1)}B`;
    if (vol >= 1e6) return `${(vol / 1e6).toFixed(0)}M`;
    return vol.toLocaleString();
  };

  return (
    <div className="volume-card">
      <h3>📈 Volume Analysis</h3>
      
      <div className="volume-main">
        <div className="up-volume">
          <span className="number green">{formatVolume(data.up_volume)}</span>
          <span className="label">Up Volume ({data.up_volume_percent}%)</span>
        </div>
        <div className="down-volume">
          <span className="number red">{formatVolume(data.down_volume)}</span>
          <span className="label">Down Volume ({(100 - data.up_volume_percent).toFixed(1)}%)</span>
        </div>
      </div>
      
      {/* Visual bar */}
      <div className="volume-bar">
        <div 
          className="up-volume-bar"
          style={{ width: `${data.up_volume_percent}%` }}
        />
      </div>
      
      <div className="volume-stats">
        <div className="stat">
          <span className="stat-label">Volume Ratio</span>
          <span className={`stat-value ${bullish ? 'green' : 'red'}`}>
            {data.volume_ratio.toFixed(2)}
          </span>
        </div>
        <div className="stat">
          <span className="stat-label">Total Volume</span>
          <span className="stat-value">{formatVolume(data.total_volume)}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Unusual Volume</span>
          <span className="stat-value highlight">{data.unusual_volume_count}</span>
        </div>
      </div>
      
      <div className={`signal ${bullish ? 'bullish' : 'bearish'}`}>
        {bullish ? '🟢 Bullish Volume' : '🔴 Bearish Volume'}
      </div>
    </div>
  );
}
```

### 4. Momentum Card

```tsx
// components/MomentumCard.tsx

import { Momentum } from '../types/indicators';

interface Props {
  data: Momentum;
}

export function MomentumCard({ data }: Props) {
  return (
    <div className="momentum-card">
      <h3>🚀 Momentum</h3>
      
      <div className="momentum-grid">
        {/* Gainers column */}
        <div className="gainers-col">
          <h4 className="green">Gainers</h4>
          <div className="momentum-row">
            <span className="threshold">+1%</span>
            <span className="count green">{data.gainers_1pct}</span>
          </div>
          <div className="momentum-row">
            <span className="threshold">+3%</span>
            <span className="count green">{data.gainers_3pct}</span>
          </div>
          <div className="momentum-row highlight">
            <span className="threshold">+5%</span>
            <span className="count green">{data.gainers_5pct}</span>
          </div>
        </div>
        
        {/* Net column */}
        <div className="net-col">
          <h4>Net</h4>
          <div className="momentum-row">
            <span className={data.net_gainers_1pct >= 0 ? 'green' : 'red'}>
              {data.net_gainers_1pct > 0 ? '+' : ''}{data.net_gainers_1pct}
            </span>
          </div>
          <div className="momentum-row">
            <span className={data.net_gainers_3pct >= 0 ? 'green' : 'red'}>
              {data.net_gainers_3pct > 0 ? '+' : ''}{data.net_gainers_3pct}
            </span>
          </div>
        </div>
        
        {/* Losers column */}
        <div className="losers-col">
          <h4 className="red">Losers</h4>
          <div className="momentum-row">
            <span className="count red">{data.losers_1pct}</span>
            <span className="threshold">-1%</span>
          </div>
          <div className="momentum-row">
            <span className="count red">{data.losers_3pct}</span>
            <span className="threshold">-3%</span>
          </div>
          <div className="momentum-row highlight">
            <span className="count red">{data.losers_5pct}</span>
            <span className="threshold">-5%</span>
          </div>
        </div>
      </div>
    </div>
  );
}
```

### 5. Volatility Card

```tsx
// components/VolatilityCard.tsx

import { Volatility } from '../types/indicators';

interface Props {
  data: Volatility;
}

export function VolatilityCard({ data }: Props) {
  const getLevelColor = (level: string) => {
    switch (level) {
      case 'low': return '#22c55e';
      case 'moderate': return '#eab308';
      case 'high': return '#f97316';
      case 'extreme': return '#dc2626';
      default: return '#6b7280';
    }
  };

  const getLevelEmoji = (level: string) => {
    switch (level) {
      case 'low': return '😴';
      case 'moderate': return '😐';
      case 'high': return '⚡';
      case 'extreme': return '🔥';
      default: return '📊';
    }
  };

  return (
    <div className="volatility-card">
      <h3>⚡ Volatility</h3>
      
      <div 
        className="volatility-level"
        style={{ color: getLevelColor(data.volatility_level) }}
      >
        <span className="emoji">{getLevelEmoji(data.volatility_level)}</span>
        <span className="level">{data.volatility_level.toUpperCase()}</span>
      </div>
      
      <div className="volatility-stats">
        <div className="stat">
          <span className="stat-label">Big Movers Up (+5%)</span>
          <span className="stat-value green">{data.big_movers_up}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Big Movers Down (-5%)</span>
          <span className="stat-value red">{data.big_movers_down}</span>
        </div>
        <div className="stat total">
          <span className="stat-label">Total Big Movers</span>
          <span className="stat-value">{data.total_big_movers}</span>
        </div>
      </div>
    </div>
  );
}
```

### 6. Sector Heatmap

```tsx
// components/SectorHeatmap.tsx

import { SectorPerformance } from '../types/indicators';

interface Props {
  sectors: SectorPerformance[];
}

export function SectorHeatmap({ sectors }: Props) {
  const getColor = (change: number) => {
    if (change >= 3) return '#166534';   // dark green
    if (change >= 1) return '#22c55e';   // green
    if (change >= 0) return '#86efac';   // light green
    if (change >= -1) return '#fca5a5';  // light red
    if (change >= -3) return '#ef4444';  // red
    return '#991b1b';                     // dark red
  };

  return (
    <div className="sector-heatmap">
      <h3>🏢 Sector Performance</h3>
      
      <div className="sectors-grid">
        {sectors.map(sector => (
          <div 
            key={sector.sector}
            className="sector-tile"
            style={{ backgroundColor: getColor(sector.avg_change) }}
          >
            <span className="sector-name">{sector.sector}</span>
            <span className="sector-change">
              {sector.avg_change >= 0 ? '+' : ''}{sector.avg_change.toFixed(2)}%
            </span>
            <span className="sector-advancing">
              {sector.percent_advancing.toFixed(0)}% advancing
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## Complete Dashboard Example

```tsx
// pages/MarketDashboard.tsx

import { useMarketIndicators } from '../hooks/useMarketIndicators';
import { FearGreedGauge } from '../components/FearGreedGauge';
import { MarketBreadthCard } from '../components/MarketBreadthCard';
import { VolumeAnalysisCard } from '../components/VolumeAnalysisCard';
import { MomentumCard } from '../components/MomentumCard';
import { VolatilityCard } from '../components/VolatilityCard';
import { SectorHeatmap } from '../components/SectorHeatmap';

export function MarketDashboard() {
  const { indicators, loading, error } = useMarketIndicators();

  if (loading) return <div className="loading">Loading market data...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!indicators) return null;

  return (
    <div className="market-dashboard">
      <header>
        <h1>Market Dashboard</h1>
        <span className="updated">
          Updated: {new Date(indicators.timestamp).toLocaleTimeString()}
        </span>
      </header>

      <div className="dashboard-grid">
        {/* Main Feature - Fear & Greed */}
        <div className="featured">
          <FearGreedGauge data={indicators.fear_greed} />
        </div>

        {/* Primary Indicators */}
        <div className="primary-row">
          <MarketBreadthCard data={indicators.market_breadth} />
          <VolumeAnalysisCard data={indicators.volume_analysis} />
        </div>

        {/* Secondary Indicators */}
        <div className="secondary-row">
          <MomentumCard data={indicators.momentum} />
          <VolatilityCard data={indicators.volatility} />
        </div>

        {/* Sector Performance */}
        <div className="full-width">
          <SectorHeatmap sectors={indicators.sector_performance} />
        </div>
      </div>
    </div>
  );
}
```

---

## CSS Styling (Tailwind Classes Reference)

```css
/* styles/indicators.css */

.market-dashboard {
  padding: 1.5rem;
  background: #0f0f0f;
  min-height: 100vh;
}

.dashboard-grid {
  display: grid;
  gap: 1.5rem;
  max-width: 1400px;
  margin: 0 auto;
}

/* Cards */
.fear-greed-gauge,
.breadth-card,
.volume-card,
.momentum-card,
.volatility-card,
.sector-heatmap {
  background: #1a1a1a;
  border-radius: 12px;
  padding: 1.5rem;
  border: 1px solid #2a2a2a;
}

/* Colors */
.green { color: #22c55e; }
.red { color: #ef4444; }
.yellow { color: #eab308; }

/* Bars */
.breadth-bar,
.volume-bar,
.gauge-bar {
  height: 8px;
  background: #333;
  border-radius: 4px;
  overflow: hidden;
}

.advancing-bar,
.up-volume-bar,
.gauge-fill {
  height: 100%;
  background: #22c55e;
  transition: width 0.3s ease;
}

/* Fear & Greed specific */
.gauge-score {
  font-size: 4rem;
  font-weight: bold;
  text-align: center;
}

.gauge-label {
  font-size: 1.5rem;
  text-align: center;
  margin-bottom: 1rem;
}

/* Sector tiles */
.sectors-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 0.5rem;
}

.sector-tile {
  padding: 1rem;
  border-radius: 8px;
  text-align: center;
  color: white;
}
```

---

## API Response Examples

### `/api/market/indicators`
```json
{
  "timestamp": "2026-01-25T17:01:10.332215+00:00",
  "market_breadth": {
    "advancing": 1101,
    "declining": 1801,
    "unchanged": 55,
    "total": 2957,
    "ad_ratio": 0.611,
    "ad_line": -700,
    "advance_percent": 37.2,
    "decline_percent": 60.9,
    "new_highs": 4,
    "new_lows": 2
  },
  "volume_analysis": {
    "up_volume": 408445364,
    "down_volume": 606175147,
    "volume_ratio": 0.674,
    "total_volume": 1047766835,
    "unusual_volume_count": 0,
    "up_volume_percent": 39.0
  },
  "momentum": {
    "gainers_1pct": 515,
    "gainers_3pct": 212,
    "gainers_5pct": 119,
    "losers_1pct": 1215,
    "losers_3pct": 537,
    "losers_5pct": 266,
    "net_gainers_1pct": -700,
    "net_gainers_3pct": -325
  },
  "sector_performance": [
    {
      "sector": "Real Estate",
      "stock_count": 7,
      "avg_change": 7.64,
      "percent_advancing": 85.7,
      "avg_rvol": 1.22,
      "total_volume": 9286836,
      "total_market_cap": 147670632522
    }
  ],
  "fear_greed": {
    "score": 43,
    "label": "Neutral",
    "components": {
      "breadth": 37.2,
      "volume": 39.0,
      "momentum": 28.3,
      "strength": 66.7
    },
    "interpretation": "Neutral sentiment - market is balanced between buyers and sellers"
  },
  "volatility": {
    "big_movers_up": 119,
    "big_movers_down": 266,
    "total_big_movers": 385,
    "volatility_level": "high"
  }
}
```

### `/api/market/fear-greed`
```json
{
  "score": 43,
  "label": "Neutral",
  "components": {
    "breadth": 37.2,
    "volume": 39.0,
    "momentum": 28.3,
    "strength": 66.7
  },
  "interpretation": "Neutral sentiment - market is balanced between buyers and sellers",
  "timestamp": "2026-01-25T17:01:10.332215+00:00"
}
```

---

## Quick Reference

| Endpoint | Use Case | Refresh |
|----------|----------|---------|
| `/api/market/indicators` | Full dashboard | 60 sec |
| `/api/market/fear-greed` | Sentiment widget | 60 sec |
| `/api/market/indicators/history` | Charts | 5 min |

| Indicator | Bullish Signal | Bearish Signal |
|-----------|----------------|----------------|
| A/D Ratio | > 1.0 | < 1.0 |
| Volume Ratio | > 1.0 | < 1.0 |
| Fear/Greed | > 60 | < 40 |
| Net Gainers | Positive | Negative |

