# Chart UI Integration Guide (Lightweight Charts)

## Overview

The API provides chart data formatted specifically for [Lightweight Charts](https://tradingview.github.io/lightweight-charts/) library. Data is fetched on-demand from Yahoo Finance to avoid rate limits.

---

## API Endpoints

### 1. Full Chart Data
```
GET /api/chart/{symbol}?interval=1d&period=1y&indicators=sma_20,sma_50,sma_200,rsi,volume
```

### 2. Mini Chart (for Kimi chat)
```
GET /api/chart/{symbol}/mini?period=3mo&candles=50
```

### 3. Chart Configuration
```
GET /api/chart/config
```

---

## TypeScript Types

```typescript
// types/chart.ts

export interface ChartData {
  symbol: string;
  interval: string;
  dataPoints: number;
  candlestick: CandlestickData[];
  volume?: VolumeData[];
  sma_20?: LineData[];
  sma_50?: LineData[];
  sma_200?: LineData[];
  rsi?: LineData[];
  meta: ChartMeta;
}

export interface CandlestickData {
  time: string;        // "YYYY-MM-DD" for daily, Unix timestamp for intraday
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface VolumeData {
  time: string;
  value: number;
  color: string;       // "#26a69a" green or "#ef5350" red
}

export interface LineData {
  time: string;
  value: number;
}

export interface ChartMeta {
  firstDate: string;
  lastDate: string;
  lastPrice: number;
  lastVolume: number | null;
}

export interface ChartConfig {
  indicators: IndicatorInfo[];
  intervals: string[];
  periods: string[];
}

export interface IndicatorInfo {
  id: string;          // "sma_20", "rsi", etc.
  name: string;        // "SMA 20", "RSI 14"
  type: "overlay" | "separate";
  color: string;
}

// For Kimi chat responses - parse chart references
export interface KimiChartReference {
  symbol: string;
  interval: string;
  period: string;
  indicators: string[];
}
```

---

## API Client

```typescript
// api/chart.ts

const API_BASE = 'http://localhost:8000';

export async function fetchChartData(
  symbol: string,
  interval = '1d',
  period = '1y',
  indicators = ['sma_20', 'sma_50', 'sma_200', 'rsi', 'volume']
): Promise<ChartData> {
  const params = new URLSearchParams({
    interval,
    period,
    indicators: indicators.join(','),
  });
  
  const res = await fetch(`${API_BASE}/api/chart/${symbol}?${params}`);
  if (!res.ok) throw new Error(`Chart error: ${res.status}`);
  return res.json();
}

export async function fetchMiniChart(
  symbol: string,
  period = '3mo',
  candles = 50
): Promise<ChartData> {
  const params = new URLSearchParams({
    period,
    candles: candles.toString(),
  });
  
  const res = await fetch(`${API_BASE}/api/chart/${symbol}/mini?${params}`);
  if (!res.ok) throw new Error(`Chart error: ${res.status}`);
  return res.json();
}

export async function fetchChartConfig(): Promise<ChartConfig> {
  const res = await fetch(`${API_BASE}/api/chart/config`);
  if (!res.ok) throw new Error(`Config error: ${res.status}`);
  return res.json();
}
```

---

## Lightweight Charts Integration

### Installation

```bash
npm install lightweight-charts
```

### Basic Chart Component

```tsx
// components/StockChart.tsx

import { useEffect, useRef, useState } from 'react';
import { createChart, IChartApi, ISeriesApi } from 'lightweight-charts';
import { fetchChartData, ChartData } from '../api/chart';

interface Props {
  symbol: string;
  interval?: string;
  period?: string;
  indicators?: string[];
  height?: number;
}

export function StockChart({ 
  symbol, 
  interval = '1d', 
  period = '1y',
  indicators = ['sma_20', 'sma_50', 'volume'],
  height = 400 
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Create chart
    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height,
      layout: {
        background: { color: '#1a1a1a' },
        textColor: '#d1d5db',
      },
      grid: {
        vertLines: { color: '#2d2d2d' },
        horzLines: { color: '#2d2d2d' },
      },
      crosshair: {
        mode: 1, // Magnet mode
      },
      rightPriceScale: {
        borderColor: '#2d2d2d',
      },
      timeScale: {
        borderColor: '#2d2d2d',
        timeVisible: true,
      },
    });

    chartRef.current = chart;

    // Fetch and render data
    loadChartData(chart, symbol, interval, period, indicators);

    // Handle resize
    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [symbol, interval, period, indicators.join(','), height]);

  async function loadChartData(
    chart: IChartApi,
    symbol: string,
    interval: string,
    period: string,
    indicators: string[]
  ) {
    setLoading(true);
    setError(null);

    try {
      const data = await fetchChartData(symbol, interval, period, indicators);
      
      // Candlestick series
      const candleSeries = chart.addCandlestickSeries({
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderUpColor: '#26a69a',
        borderDownColor: '#ef5350',
        wickUpColor: '#26a69a',
        wickDownColor: '#ef5350',
      });
      candleSeries.setData(data.candlestick);

      // SMA 20 (blue)
      if (data.sma_20?.length) {
        const sma20 = chart.addLineSeries({
          color: '#2196F3',
          lineWidth: 1,
          title: 'SMA 20',
        });
        sma20.setData(data.sma_20);
      }

      // SMA 50 (orange)
      if (data.sma_50?.length) {
        const sma50 = chart.addLineSeries({
          color: '#FF9800',
          lineWidth: 1,
          title: 'SMA 50',
        });
        sma50.setData(data.sma_50);
      }

      // SMA 200 (purple)
      if (data.sma_200?.length) {
        const sma200 = chart.addLineSeries({
          color: '#9C27B0',
          lineWidth: 1,
          title: 'SMA 200',
        });
        sma200.setData(data.sma_200);
      }

      // Volume
      if (data.volume?.length) {
        const volumeSeries = chart.addHistogramSeries({
          priceFormat: { type: 'volume' },
          priceScaleId: 'volume',
        });
        volumeSeries.setData(data.volume);
        
        // Scale volume to bottom 20% of chart
        chart.priceScale('volume').applyOptions({
          scaleMargins: { top: 0.8, bottom: 0 },
        });
      }

      chart.timeScale().fitContent();
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load chart');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="stock-chart">
      {loading && <div className="loading">Loading chart...</div>}
      {error && <div className="error">{error}</div>}
      <div ref={containerRef} />
    </div>
  );
}
```

---

## Mini Chart for Kimi Responses

### Parsing Kimi Chart References

Kimi includes chart references in its responses using this format:
```
[CHART:AAPL:1d:3mo:sma_20,sma_50,volume]
```

Parse and render them:

```typescript
// utils/parseKimiResponse.ts

export interface ParsedResponse {
  text: string;
  charts: KimiChartReference[];
}

export function parseKimiResponse(content: string): ParsedResponse {
  const chartPattern = /\[CHART:([A-Z]+):(\w+):(\w+):([a-z0-9_,]+)\]/g;
  const charts: KimiChartReference[] = [];
  
  let text = content;
  let match;
  
  while ((match = chartPattern.exec(content)) !== null) {
    charts.push({
      symbol: match[1],
      interval: match[2],
      period: match[3],
      indicators: match[4].split(','),
    });
    
    // Replace chart tag with placeholder for rendering
    text = text.replace(match[0], `{{CHART_${charts.length - 1}}}`);
  }
  
  return { text, charts };
}
```

### Mini Chart Component

```tsx
// components/MiniChart.tsx

import { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';
import { fetchMiniChart } from '../api/chart';

interface Props {
  symbol: string;
  period?: string;
  candles?: number;
}

export function MiniChart({ symbol, period = '3mo', candles = 50 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      width: 300,
      height: 150,
      layout: {
        background: { color: '#1a1a1a' },
        textColor: '#9ca3af',
      },
      grid: {
        vertLines: { visible: false },
        horzLines: { color: '#2d2d2d' },
      },
      rightPriceScale: {
        visible: false,
      },
      timeScale: {
        visible: false,
      },
      crosshair: {
        vertLine: { visible: false },
        horzLine: { visible: false },
      },
    });

    fetchMiniChart(symbol, period, candles).then(data => {
      const series = chart.addAreaSeries({
        lineColor: '#2196F3',
        topColor: 'rgba(33, 150, 243, 0.3)',
        bottomColor: 'rgba(33, 150, 243, 0.0)',
        lineWidth: 2,
      });
      
      // Convert candlestick to line data (close prices)
      const lineData = data.candlestick.map(c => ({
        time: c.time,
        value: c.close,
      }));
      
      series.setData(lineData);
      chart.timeScale().fitContent();
      setLoading(false);
    });

    return () => chart.remove();
  }, [symbol, period, candles]);

  return (
    <div className="mini-chart">
      <div className="mini-chart-header">
        <span className="symbol">{symbol}</span>
      </div>
      {loading && <div className="loading">Loading...</div>}
      <div ref={containerRef} />
    </div>
  );
}
```

### Rendering Kimi Response with Charts

```tsx
// components/ChatMessage.tsx

import { parseKimiResponse } from '../utils/parseKimiResponse';
import { MiniChart } from './MiniChart';

interface Props {
  content: string;
  role: 'user' | 'assistant';
}

export function ChatMessage({ content, role }: Props) {
  if (role === 'user') {
    return <div className="user-message">{content}</div>;
  }

  const { text, charts } = parseKimiResponse(content);
  
  // Split text by chart placeholders
  const parts = text.split(/\{\{CHART_(\d+)\}\}/);

  return (
    <div className="assistant-message">
      {parts.map((part, i) => {
        // Even indices are text, odd indices are chart indices
        if (i % 2 === 0) {
          return <span key={i}>{part}</span>;
        } else {
          const chartIndex = parseInt(part);
          const chartRef = charts[chartIndex];
          if (chartRef) {
            return (
              <div key={i} className="inline-chart">
                <MiniChart 
                  symbol={chartRef.symbol}
                  period={chartRef.period}
                />
              </div>
            );
          }
          return null;
        }
      })}
    </div>
  );
}
```

---

## Full Page Chart with Controls

```tsx
// pages/ChartPage.tsx

import { useState } from 'react';
import { StockChart } from '../components/StockChart';

export function ChartPage() {
  const [symbol, setSymbol] = useState('AAPL');
  const [interval, setInterval] = useState('1d');
  const [period, setPeriod] = useState('1y');
  const [indicators, setIndicators] = useState(['sma_20', 'sma_50', 'volume']);

  const intervals = ['1m', '5m', '15m', '30m', '1h', '1d', '1wk', '1mo'];
  const periods = ['7d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'];
  const availableIndicators = [
    { id: 'sma_20', name: 'SMA 20' },
    { id: 'sma_50', name: 'SMA 50' },
    { id: 'sma_200', name: 'SMA 200' },
    { id: 'rsi', name: 'RSI' },
    { id: 'volume', name: 'Volume' },
  ];

  const toggleIndicator = (id: string) => {
    setIndicators(prev => 
      prev.includes(id) 
        ? prev.filter(i => i !== id)
        : [...prev, id]
    );
  };

  return (
    <div className="chart-page">
      {/* Symbol Input */}
      <div className="chart-header">
        <input
          type="text"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          placeholder="Enter symbol..."
          className="symbol-input"
        />
      </div>

      {/* Interval Selector */}
      <div className="interval-selector">
        {intervals.map(int => (
          <button
            key={int}
            className={interval === int ? 'active' : ''}
            onClick={() => setInterval(int)}
          >
            {int}
          </button>
        ))}
      </div>

      {/* Period Selector */}
      <div className="period-selector">
        {periods.map(p => (
          <button
            key={p}
            className={period === p ? 'active' : ''}
            onClick={() => setPeriod(p)}
          >
            {p}
          </button>
        ))}
      </div>

      {/* Indicator Toggles */}
      <div className="indicator-toggles">
        {availableIndicators.map(ind => (
          <label key={ind.id}>
            <input
              type="checkbox"
              checked={indicators.includes(ind.id)}
              onChange={() => toggleIndicator(ind.id)}
            />
            {ind.name}
          </label>
        ))}
      </div>

      {/* Chart */}
      <StockChart
        symbol={symbol}
        interval={interval}
        period={period}
        indicators={indicators}
        height={500}
      />
    </div>
  );
}
```

---

## API Response Examples

### Full Chart Response
```json
{
  "symbol": "AAPL",
  "interval": "1d",
  "dataPoints": 252,
  "candlestick": [
    { "time": "2025-01-25", "open": 150.2, "high": 152.5, "low": 149.8, "close": 151.0 }
  ],
  "volume": [
    { "time": "2025-01-25", "value": 52000000, "color": "#26a69a" }
  ],
  "sma_20": [
    { "time": "2025-01-25", "value": 149.5 }
  ],
  "sma_50": [
    { "time": "2025-01-25", "value": 148.2 }
  ],
  "rsi": [
    { "time": "2025-01-25", "value": 55.3 }
  ],
  "meta": {
    "firstDate": "2024-01-25",
    "lastDate": "2025-01-25",
    "lastPrice": 151.0,
    "lastVolume": 52000000
  }
}
```

### Mini Chart Response
```json
{
  "symbol": "TSLA",
  "interval": "1d",
  "dataPoints": 50,
  "candlestick": [...],
  "volume": [...],
  "sma_20": [...],
  "meta": {...}
}
```

---

## Quick Reference

| Endpoint | Use Case | Data |
|----------|----------|------|
| `/api/chart/{symbol}` | Full interactive chart | All indicators |
| `/api/chart/{symbol}/mini` | Kimi inline chart | 50 candles, basic |
| `/api/chart/config` | UI setup | Available options |

| Indicator | Type | Color |
|-----------|------|-------|
| sma_20 | Overlay | #2196F3 (blue) |
| sma_50 | Overlay | #FF9800 (orange) |
| sma_200 | Overlay | #9C27B0 (purple) |
| rsi | Separate pane | #4CAF50 (green) |
| volume | Separate pane | Dynamic |

| Period | Yahoo Availability |
|--------|-------------------|
| 7d, 1mo, 3mo, 6mo | All intervals |
| 1y, 2y | Daily and above |
| 5y, 10y, max | Daily and above |

