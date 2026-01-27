import { useState, useEffect } from 'react';
import type { HeatmapResponse } from '../types/market';

const API_BASE = 'http://localhost:8000';

export function useHeatmap() {
    const [data, setData] = useState<HeatmapResponse | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${API_BASE}/api/market/heatmap`)
            .then(res => res.json())
            .then(setData)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    return { data, loading };
}
