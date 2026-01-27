// api/marketPulse.ts - Client for Market Pulse API

export interface PulseUpdate {
    category: 'Markets' | 'Crypto' | 'Economy' | 'Earnings' | 'Tech' | 'Commodities';
    headline: string;
    sentiment: 'positive' | 'negative' | 'neutral';
}

export interface MarketPulseResponse {
    generated_at: string;
    updates: PulseUpdate[];
    cache_expires_at: string;
}

const API_BASE = 'http://localhost:8000';

export async function fetchMarketPulse(): Promise<MarketPulseResponse> {
    const res = await fetch(`${API_BASE}/api/market/pulse`);
    if (!res.ok) throw new Error('Failed to fetch market pulse');
    return res.json();
}
