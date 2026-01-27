
import { useState, useEffect } from 'react';
import { getStockNews } from '../api/alphaApi';
import { NewsCard } from './NewsCard';
import type { StockNewsResponse } from '../types/api';

interface NewsSectionProps {
    symbol: string;
}

export function NewsSection({ symbol }: NewsSectionProps) {
    const [newsData, setNewsData] = useState<StockNewsResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let mounted = true;
        setLoading(true);

        getStockNews(symbol)
            .then(data => {
                if (mounted) {
                    setNewsData(data);
                    setError(null);
                }
            })
            .catch(err => {
                if (mounted) {
                    console.error("Failed to fetch news:", err);
                    setError("Failed to load news.");
                }
            })
            .finally(() => {
                if (mounted) setLoading(false);
            });

        return () => { mounted = false; };
    }, [symbol]);

    return (
        <div className="mt-8">
            <h2 className="text-xl font-bold mb-4 text-gray-200">Recent News for {symbol}</h2>

            {loading && (
                <div className="py-8 text-center text-gray-500">
                    <div className="animate-spin inline-block mb-2 text-2xl">⏳</div>
                    <p>Loading news...</p>
                </div>
            )}

            {error && (
                <div className="p-4 bg-red-900/20 text-red-400 rounded-lg">
                    {error}
                </div>
            )}

            {!loading && !error && newsData?.articles.length === 0 && (
                <div className="p-4 text-gray-500 text-center bg-[#111827] rounded-lg border border-gray-800">
                    No recent news found for {symbol}.
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {newsData?.articles.map(article => (
                    <NewsCard key={article.id} news={article} />
                ))}
            </div>
        </div>
    );
}
