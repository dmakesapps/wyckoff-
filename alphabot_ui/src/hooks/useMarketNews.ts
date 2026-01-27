import { useState, useEffect, useCallback } from 'react';
import { getMarketNews } from '../api/alphaApi';
import type { MarketNewsResponse } from '../types/api';

export function useMarketNews(limit = 15) {
    const [data, setData] = useState<MarketNewsResponse | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchNews = useCallback(async () => {
        try {
            setIsLoading(true);
            const result = await getMarketNews(limit);
            setData(result);
            setError(null);
        } catch (err) {
            console.error(err);
            setError(err instanceof Error ? err.message : 'Failed to fetch news');
        } finally {
            setIsLoading(false);
        }
    }, [limit]);

    useEffect(() => {
        fetchNews();
    }, [fetchNews]);

    return { data, isLoading, error, refresh: fetchNews };
}
