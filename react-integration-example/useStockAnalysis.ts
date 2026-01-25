// src/hooks/useStockAnalysis.ts
// React hook for fetching stock analysis

import { useState, useCallback } from 'react';
import { analyzeStock, StockAnalysis } from '../api/alphaApi';

interface UseStockAnalysisResult {
  data: StockAnalysis | null;
  loading: boolean;
  error: string | null;
  analyze: (symbol: string) => Promise<void>;
  clear: () => void;
}

export function useStockAnalysis(): UseStockAnalysisResult {
  const [data, setData] = useState<StockAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyze = useCallback(async (symbol: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await analyzeStock(symbol.toUpperCase());
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const clear = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return { data, loading, error, analyze, clear };
}


