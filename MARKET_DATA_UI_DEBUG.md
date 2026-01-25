# Market Data UI Integration & Debug Guide

## 🚨 Issue: Market Data Page Shows Nothing

The backend API is fully functional with **5,285 stocks cached**. The issue is on the frontend side.

---

## Backend Status: ✅ CONFIRMED WORKING

```bash
# Health check
curl http://localhost:8000/api/health
# Returns: {"status":"healthy","scanner":{"running":true,"stocks_in_db":5285}}
```

---

## API Base URL

```typescript
const API_BASE = 'http://localhost:8000';
```

**Important:** The API runs on port 8000, NOT your Vite dev server port.

---

## Available Endpoints & Response Formats

### 1. Top Gainers
```
GET http://localhost:8000/api/market/gainers?limit=50
```

**Response:**
```typescript
interface GainersResponse {
  count: number;
  stocks: Stock[];
  updated_at: string;
}

interface Stock {
  rank: number;
  ticker: string;
  company: string | null;
  last: number;        // Current price
  change: number;      // Percent change (e.g., 372.18 means +372.18%)
  volume: number;
  relativeVolume: number;
  marketCap: number | null;
  sector: string | null;
  signal: string;
}
```

**Example Response:**
```json
{
  "count": 3,
  "stocks": [
    {
      "rank": 1,
      "ticker": "LPTX",
      "company": null,
      "last": 2.04,
      "change": 372.18,
      "volume": 3860719,
      "relativeVolume": 1.0,
      "marketCap": null,
      "sector": null,
      "signal": "Top Gainers"
    }
  ],
  "updated_at": "2026-01-25T16:42:03.346558+00:00"
}
```

---

### 2. Top Losers
```
GET http://localhost:8000/api/market/losers?limit=50
```

**Response:** Same format as gainers, but `change` is negative.

---

### 3. Market Overview (Dashboard Data)
```
GET http://localhost:8000/api/market/overview
```

**Response:**
```typescript
interface MarketOverview {
  breadth: {
    advancing: number;      // Stocks going up
    declining: number;      // Stocks going down
    unchanged: number;
    total: number;
    advance_decline_ratio: number;
    advance_percent: number;
    decline_percent: number;
    new_highs: number;
    new_lows: number;
  };
  sectors: SectorData[];
  top_gainers: Stock[];
  top_losers: Stock[];
  most_active: Stock[];
  unusual_volume: Stock[];
  updated_at: string;
}

interface SectorData {
  sector: string;
  stock_count: number;
  avg_change: number;
  percent_advancing: number;
  avg_rvol: number;
  total_volume: number;
  total_market_cap: number;
}
```

---

### 4. Most Active (by Volume)
```
GET http://localhost:8000/api/market/most-active?limit=50
```

---

### 5. Unusual Volume
```
GET http://localhost:8000/api/market/unusual-volume?limit=50&min_rvol=2.0
```

---

### 6. New 52-Week Highs
```
GET http://localhost:8000/api/market/new-highs?limit=50
```

---

### 7. New 52-Week Lows
```
GET http://localhost:8000/api/market/new-lows?limit=50
```

---

### 8. Market Headlines
```
GET http://localhost:8000/api/market/headlines?limit=10
```

**Response:**
```typescript
interface HeadlinesResponse {
  count: number;
  headlines: Headline[];
  updated_at: string;
}

interface Headline {
  title: string;
  link: string;
  source: string;
  published: string;
  related_symbols: string[];
  sentiment: string | null;
}
```

---

## React Integration Code

### API Client (`src/api/market.ts`)

```typescript
const API_BASE = 'http://localhost:8000';

export interface Stock {
  rank: number;
  ticker: string;
  company: string | null;
  last: number;
  change: number;
  volume: number;
  relativeVolume: number;
  marketCap: number | null;
  sector: string | null;
  signal: string;
}

export interface MarketResponse {
  count: number;
  stocks: Stock[];
  updated_at: string;
}

export async function fetchGainers(limit = 50): Promise<MarketResponse> {
  const res = await fetch(`${API_BASE}/api/market/gainers?limit=${limit}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchLosers(limit = 50): Promise<MarketResponse> {
  const res = await fetch(`${API_BASE}/api/market/losers?limit=${limit}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchOverview(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/market/overview`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchMostActive(limit = 50): Promise<MarketResponse> {
  const res = await fetch(`${API_BASE}/api/market/most-active?limit=${limit}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
```

---

### React Hook (`src/hooks/useMarketData.ts`)

```typescript
import { useState, useEffect } from 'react';
import { fetchGainers, fetchLosers, fetchOverview, Stock } from '../api/market';

export function useMarketData() {
  const [gainers, setGainers] = useState<Stock[]>([]);
  const [losers, setLosers] = useState<Stock[]>([]);
  const [overview, setOverview] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        
        const [gainersRes, losersRes, overviewRes] = await Promise.all([
          fetchGainers(20),
          fetchLosers(20),
          fetchOverview()
        ]);
        
        setGainers(gainersRes.stocks);
        setLosers(losersRes.stocks);
        setOverview(overviewRes);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load market data');
        console.error('Market data error:', err);
      } finally {
        setLoading(false);
      }
    }
    
    loadData();
    
    // Refresh every 5 minutes
    const interval = setInterval(loadData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  return { gainers, losers, overview, loading, error };
}
```

---

### Example Component (`src/components/MarketDashboard.tsx`)

```tsx
import { useMarketData } from '../hooks/useMarketData';

export function MarketDashboard() {
  const { gainers, losers, overview, loading, error } = useMarketData();

  if (loading) return <div>Loading market data...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="market-dashboard">
      {/* Market Breadth */}
      {overview && (
        <div className="breadth-card">
          <h3>Market Breadth</h3>
          <div className="stats">
            <span className="green">↑ {overview.breadth.advancing} advancing</span>
            <span className="red">↓ {overview.breadth.declining} declining</span>
          </div>
        </div>
      )}

      {/* Top Gainers */}
      <div className="gainers-card">
        <h3>🚀 Top Gainers</h3>
        <table>
          <thead>
            <tr>
              <th>Ticker</th>
              <th>Price</th>
              <th>Change</th>
              <th>Volume</th>
            </tr>
          </thead>
          <tbody>
            {gainers.map(stock => (
              <tr key={stock.ticker}>
                <td className="ticker">{stock.ticker}</td>
                <td>${stock.last.toFixed(2)}</td>
                <td className="green">+{stock.change.toFixed(2)}%</td>
                <td>{stock.volume.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Top Losers */}
      <div className="losers-card">
        <h3>📉 Top Losers</h3>
        <table>
          <thead>
            <tr>
              <th>Ticker</th>
              <th>Price</th>
              <th>Change</th>
              <th>Volume</th>
            </tr>
          </thead>
          <tbody>
            {losers.map(stock => (
              <tr key={stock.ticker}>
                <td className="ticker">{stock.ticker}</td>
                <td>${stock.last.toFixed(2)}</td>
                <td className="red">{stock.change.toFixed(2)}%</td>
                <td>{stock.volume.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

---

## Common Issues & Fixes

### Issue 1: CORS Error
**Symptom:** Browser console shows "blocked by CORS policy"

**Fix:** The backend already has CORS enabled for all origins. If still failing, check:
```typescript
// Make sure you're using the full URL
fetch('http://localhost:8000/api/market/gainers')  // ✅
fetch('/api/market/gainers')  // ❌ Won't work unless proxied
```

---

### Issue 2: Empty Data / Undefined
**Symptom:** `stocks` is undefined or empty array

**Fix:** The data is nested inside the response:
```typescript
// ❌ Wrong
const stocks = await fetch(url).then(r => r.json());

// ✅ Correct
const response = await fetch(url).then(r => r.json());
const stocks = response.stocks;  // <-- Access the stocks array
```

---

### Issue 3: Network Error
**Symptom:** `TypeError: Failed to fetch`

**Fix:** Make sure the Python server is running:
```bash
cd /Users/davis/Desktop/breakoutbot\ copy
python3 run_api.py
```

---

### Issue 4: 404 Not Found
**Symptom:** API returns 404

**Fix:** Check the exact endpoint path:
```
✅ /api/market/gainers
❌ /api/gainers
❌ /market/gainers
```

---

## Debug Checklist

Run these in browser console to verify:

```javascript
// 1. Test basic connectivity
fetch('http://localhost:8000/api/health')
  .then(r => r.json())
  .then(console.log)

// 2. Test gainers endpoint
fetch('http://localhost:8000/api/market/gainers?limit=5')
  .then(r => r.json())
  .then(data => {
    console.log('Full response:', data);
    console.log('Stocks array:', data.stocks);
    console.log('First stock:', data.stocks[0]);
  })

// 3. Test overview endpoint
fetch('http://localhost:8000/api/market/overview')
  .then(r => r.json())
  .then(console.log)
```

---

## Vite Proxy Setup (Optional)

If you want to use relative URLs like `/api/market/gainers`, add this to `vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
});
```

Then you can use:
```typescript
fetch('/api/market/gainers')  // Will proxy to localhost:8000
```

---

## Summary

| What | Status |
|------|--------|
| Backend API | ✅ Running on port 8000 |
| Data cached | ✅ 5,285 stocks |
| Gainers endpoint | ✅ Working |
| Losers endpoint | ✅ Working |
| Overview endpoint | ✅ Working |

**The backend is fully functional. Focus debugging on:**
1. Correct API URL (`http://localhost:8000`)
2. Accessing `response.stocks` (not just `response`)
3. Error handling in fetch calls

