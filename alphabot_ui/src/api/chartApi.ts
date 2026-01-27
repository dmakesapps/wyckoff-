// api/chartApi.ts - API client for chart data

import type { ChartData, ChartConfig } from '../types/chart';

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

    const res = await fetch(`${API_BASE}/api/chart/${encodeURIComponent(symbol)}?${params}`);
    if (!res.ok) throw new Error(`Chart error: ${res.status}`);
    return res.json();
}

export async function fetchMiniChart(
    symbol: string,
    period = '1mo',
    candles = 30
): Promise<ChartData> {
    const params = new URLSearchParams({
        period,
        candles: candles.toString(),
    });

    const res = await fetch(`${API_BASE}/api/chart/${encodeURIComponent(symbol)}/mini?${params}`);
    if (!res.ok) throw new Error(`Chart error: ${res.status}`);
    return res.json();
}

export async function fetchChartConfig(): Promise<ChartConfig> {
    const res = await fetch(`${API_BASE}/api/chart/config`);
    if (!res.ok) throw new Error(`Config error: ${res.status}`);
    return res.json();
}

// Fetch multiple mini charts at once for indices
export async function fetchMultipleMiniCharts(
    symbols: string[],
    period = '1mo',
    candles = 30
): Promise<Map<string, ChartData>> {
    const results = new Map<string, ChartData>();

    const promises = symbols.map(async (symbol) => {
        try {
            const data = await fetchMiniChart(symbol, period, candles);
            return { symbol, data, error: null };
        } catch (error) {
            console.error(`Failed to fetch chart for ${symbol}:`, error);
            return { symbol, data: null, error };
        }
    });

    const responses = await Promise.all(promises);

    for (const { symbol, data } of responses) {
        if (data) {
            results.set(symbol, data);
        }
    }

    return results;
}
