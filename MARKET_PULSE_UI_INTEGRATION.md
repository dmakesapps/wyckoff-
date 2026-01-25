# Market Pulse UI Integration

## Endpoint

```
GET /api/market/pulse
```

**Base URL:** `http://localhost:8000`

---

## Response Schema

```typescript
interface MarketPulseResponse {
  generated_at: string;      // ISO timestamp
  updates: PulseUpdate[];
  cache_expires_at: string;  // When to refresh
}

interface PulseUpdate {
  category: "Markets" | "Crypto" | "Economy" | "Earnings" | "Tech" | "Commodities";
  headline: string;          // Max ~60 chars, no period at end
  sentiment: "positive" | "negative" | "neutral";
}
```

---

## Example Response

```json
{
  "generated_at": "2026-01-25T23:07:36.994813+00:00",
  "updates": [
    {"category": "Markets", "headline": "NASDAQ up 0.32% as Dow slips 0.56%", "sentiment": "neutral"},
    {"category": "Crypto", "headline": "Bitcoin drops 3% to $86K, ETH falls 5%", "sentiment": "negative"},
    {"category": "Economy", "headline": "Dollar drops 0.89% as 10Y yield holds 4.24%", "sentiment": "neutral"},
    {"category": "Earnings", "headline": "MSFT leads tech gains ahead of earnings", "sentiment": "positive"},
    {"category": "Tech", "headline": "MSFT surges 3.3%, AMZN up 2% on growth", "sentiment": "positive"},
    {"category": "Commodities", "headline": "Gold hits $4,980, oil jumps 2.4% to $61", "sentiment": "positive"}
  ],
  "cache_expires_at": "2026-01-25T23:22:36.994813+00:00"
}
```

---

## React Integration

### API Client

```typescript
// api/marketPulse.ts

export interface PulseUpdate {
  category: string;
  headline: string;
  sentiment: 'positive' | 'negative' | 'neutral';
}

export interface MarketPulseResponse {
  generated_at: string;
  updates: PulseUpdate[];
  cache_expires_at: string;
}

export async function fetchMarketPulse(): Promise<MarketPulseResponse> {
  const res = await fetch('http://localhost:8000/api/market/pulse');
  if (!res.ok) throw new Error('Failed to fetch market pulse');
  return res.json();
}
```

### React Hook

```typescript
// hooks/useMarketPulse.ts
import { useState, useEffect } from 'react';
import { fetchMarketPulse, MarketPulseResponse } from '../api/marketPulse';

export function useMarketPulse(refreshInterval = 60000) {
  const [pulse, setPulse] = useState<MarketPulseResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      try {
        const data = await fetchMarketPulse();
        if (mounted) {
          setPulse(data);
          setError(null);
        }
      } catch (err) {
        if (mounted) setError('Failed to load market pulse');
      } finally {
        if (mounted) setLoading(false);
      }
    };

    load();
    const interval = setInterval(load, refreshInterval);
    
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [refreshInterval]);

  return { pulse, loading, error };
}
```

### Component Example

```tsx
// components/MarketPulse.tsx
import { useMarketPulse } from '../hooks/useMarketPulse';

const sentimentColors = {
  positive: 'text-green-500',
  negative: 'text-red-500',
  neutral: 'text-gray-400',
};

const categoryIcons: Record<string, string> = {
  Markets: '📈',
  Crypto: '₿',
  Economy: '🏛️',
  Earnings: '📊',
  Tech: '💻',
  Commodities: '🛢️',
};

export function MarketPulse() {
  const { pulse, loading, error } = useMarketPulse();

  if (loading) return <div className="animate-pulse">Loading market pulse...</div>;
  if (error) return <div className="text-red-500">{error}</div>;
  if (!pulse) return null;

  return (
    <div className="space-y-2">
      <h2 className="text-lg font-semibold text-white/80">What's happening today</h2>
      <div className="space-y-1">
        {pulse.updates.map((update, i) => (
          <div key={i} className="flex items-center gap-2 text-sm">
            <span>{categoryIcons[update.category] || '•'}</span>
            <span className="text-white/60">{update.category}:</span>
            <span className={sentimentColors[update.sentiment]}>
              {update.headline}
            </span>
          </div>
        ))}
      </div>
      <div className="text-xs text-white/30">
        Updated {new Date(pulse.generated_at).toLocaleTimeString()}
      </div>
    </div>
  );
}
```

---

## Styling Tips

### Sentiment Indicators
- **Positive**: Green text/dot (#22c55e)
- **Negative**: Red text/dot (#ef4444)  
- **Neutral**: Gray text/dot (#9ca3af)

### Category Icons (suggestions)
| Category | Icon |
|----------|------|
| Markets | 📈 or chart icon |
| Crypto | ₿ or Bitcoin icon |
| Economy | 🏛️ or building icon |
| Earnings | 📊 or bar chart |
| Tech | 💻 or CPU icon |
| Commodities | 🛢️ or gold bar |

---

## Caching Behavior

- Data is cached for **15 minutes** on the backend
- `cache_expires_at` tells you when fresh data will be available
- Safe to poll every 60 seconds (will return cached data)
- Force refresh: `GET /api/market/pulse?force_refresh=true`

---

## Additional Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/market/pulse` | Main endpoint - AI headlines |
| `GET /api/market/pulse/status` | Cache status (age, expires_in) |
| `GET /api/market/pulse/raw` | Includes raw market data used |

