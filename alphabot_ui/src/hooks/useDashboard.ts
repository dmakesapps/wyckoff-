import { useState, useEffect } from 'react';
import type { MarketOverview, RankedStock, Headline, VolumeAnalysis, Momentum, Volatility, FearGreed } from '../types/market';

const API_BASE = 'http://localhost:8000';

// Type for the /api/market/indicators response
interface IndicatorsResponse {
    volume_analysis?: VolumeAnalysis;
    momentum?: Momentum;
    volatility?: Volatility;
    fear_greed?: FearGreed;
}

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
            setData(prev => ({ ...prev, loading: true }));

            const [overviewRes, indicatorsRes, gainersRes, losersRes, headlinesRes] = await Promise.all([
                fetch(`${API_BASE}/api/market/overview`),
                fetch(`${API_BASE}/api/market/indicators`),
                fetch(`${API_BASE}/api/market/gainers?limit=20`),
                fetch(`${API_BASE}/api/market/losers?limit=20`),
                fetch(`${API_BASE}/api/market/headlines?limit=10`),
            ]);

            const [overview, indicators, gainers, losers, headlines] = await Promise.all([
                overviewRes.json(),
                indicatorsRes.ok ? indicatorsRes.json() : ({} as IndicatorsResponse),
                gainersRes.json(),
                losersRes.json(),
                headlinesRes.json(),
            ]) as [MarketOverview, IndicatorsResponse, any, any, any];

            // Merge indicators data into overview
            const mergedOverview: MarketOverview = {
                ...overview,
                volume_analysis: indicators.volume_analysis,
                momentum: indicators.momentum,
                volatility: indicators.volatility,
                fear_greed: indicators.fear_greed || overview.fear_greed,
            };

            setData({
                overview: mergedOverview,
                gainers: gainers.stocks,
                losers: losers.stocks,
                headlines: headlines.headlines,
                loading: false,
                error: null,
                lastUpdate: overview.updated_at,
            });
        } catch (err) {
            console.error(err);
            setData(prev => ({ ...prev, loading: false, error: 'Failed to fetch market data' }));
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
