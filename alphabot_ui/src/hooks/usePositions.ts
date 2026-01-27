import { useState, useEffect, useCallback } from 'react';
import { getPositions } from '../api/alphaApi';
import type { PositionsResponse } from '../types/api';

export function usePositions(autoRefresh = false, refreshInterval = 30000) {
    const [data, setData] = useState<PositionsResponse | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchPositions = useCallback(async () => {
        try {
            setIsLoading(true);
            const result = await getPositions();
            setData(result);
            setError(null);
        } catch (err) {
            console.error(err);
            setError(err instanceof Error ? err.message : 'Failed to fetch positions');
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchPositions();

        if (autoRefresh) {
            const interval = setInterval(fetchPositions, refreshInterval);
            return () => clearInterval(interval);
        }
    }, [fetchPositions, autoRefresh, refreshInterval]);

    return { data, isLoading, error, refresh: fetchPositions };
}
