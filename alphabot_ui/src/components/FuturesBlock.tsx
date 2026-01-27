"use client";

import { useState, useEffect } from "react";
import { getQuote } from "../api/alphaApi";
import type { Quote } from "../types/api";
import { TrendingUp, TrendingDown } from "lucide-react";

// Define the futures/assets we want to track
interface FuturesAsset {
    symbol: string;
    label: string;
    category: 'index' | 'commodity' | 'crypto' | 'volatility';
    formatPrice: (price: number) => string;
}

const FUTURES_ASSETS: FuturesAsset[] = [
    // Index Futures
    { symbol: 'ES=F', label: 'S&P 500', category: 'index', formatPrice: (p) => p.toLocaleString(undefined, { maximumFractionDigits: 0 }) },
    { symbol: 'NQ=F', label: 'NASDAQ', category: 'index', formatPrice: (p) => p.toLocaleString(undefined, { maximumFractionDigits: 0 }) },
    { symbol: 'YM=F', label: 'Dow', category: 'index', formatPrice: (p) => p.toLocaleString(undefined, { maximumFractionDigits: 0 }) },

    // Volatility - Critical for alpha seekers
    { symbol: '^VIX', label: 'VIX', category: 'volatility', formatPrice: (p) => p.toFixed(2) },

    // Commodities
    { symbol: 'GC=F', label: 'Gold', category: 'commodity', formatPrice: (p) => `$${p.toLocaleString(undefined, { maximumFractionDigits: 0 })}` },
    { symbol: 'CL=F', label: 'Oil', category: 'commodity', formatPrice: (p) => `$${p.toFixed(2)}` },

    // Crypto
    { symbol: 'BTC-USD', label: 'Bitcoin', category: 'crypto', formatPrice: (p) => `$${(p / 1000).toFixed(1)}K` },
    { symbol: 'ETH-USD', label: 'Ethereum', category: 'crypto', formatPrice: (p) => `$${p.toLocaleString(undefined, { maximumFractionDigits: 0 })}` },
];

interface FuturesData {
    asset: FuturesAsset;
    quote: Quote | null;
    loading: boolean;
    error: boolean;
}

export function FuturesBlock() {
    const [futuresData, setFuturesData] = useState<FuturesData[]>(() => {
        const cached = localStorage.getItem("marketQuotes_futures");
        if (cached) {
            try {
                const parsed = JSON.parse(cached);
                // Merge cached quotes with asset definitions
                return FUTURES_ASSETS.map(asset => {
                    const cachedItem = parsed.find((p: any) => p.asset.symbol === asset.symbol);
                    if (cachedItem && cachedItem.quote) {
                        return {
                            asset,
                            quote: cachedItem.quote,
                            loading: false, // Start as not loading if we have cache
                            error: false
                        };
                    }
                    return { asset, quote: null, loading: true, error: false };
                });
            } catch (e) {
                // Fallback
            }
        }
        return FUTURES_ASSETS.map(asset => ({ asset, quote: null, loading: true, error: false }));
    });

    useEffect(() => {
        let mounted = true;

        const fetchAllQuotes = async () => {
            // If we have cached data, we don't need to show loading spinners on refresh
            // But if it's the very first load and no cache, we might want to keep loading true.

            const results = await Promise.all(
                FUTURES_ASSETS.map(async (asset) => {
                    try {
                        const quote = await getQuote(asset.symbol);
                        return { asset, quote, loading: false, error: false };
                    } catch (err) {
                        console.error(`Failed to fetch ${asset.symbol}:`, err);
                        // If we have previous data, keep it? For now, just show error if fetch fails
                        return { asset, quote: null, loading: false, error: true };
                    }
                })
            );

            if (mounted) {
                setFuturesData(results);
                localStorage.setItem("marketQuotes_futures", JSON.stringify(results));
            }
        };

        fetchAllQuotes();
        const interval = setInterval(fetchAllQuotes, 30000); // Refresh every 30 seconds

        return () => {
            mounted = false;
            clearInterval(interval);
        };
    }, []);

    return (
        <div className="futures-block">
            <h4 className="futures-title">Futures & Crypto</h4>
            <div className="futures-grid">
                {futuresData.map(({ asset, quote, loading, error }) => {
                    // Logic to fix 0.00 change for Futures/Indices when API returns price == prev_close
                    // We fall back to Change from Open if standard Change is flat but Open diff is real.
                    let change = quote?.change ?? 0;
                    let changePercent = quote?.change_percent ?? 0;

                    if (quote && change === 0 && quote.price !== quote.open && quote.open > 0) {
                        change = quote.price - quote.open;
                        changePercent = (change / quote.open) * 100;
                    }

                    return (
                        <div key={asset.symbol} className="futures-item">
                            <span className="futures-label">{asset.label}</span>
                            {loading ? (
                                <span className="futures-loading">--</span>
                            ) : error || !quote ? (
                                <span className="futures-error">N/A</span>
                            ) : (
                                <>
                                    <span className="futures-price">
                                        {asset.formatPrice(quote.price)}
                                    </span>
                                    <span
                                        className={`futures-change ${changePercent >= 0 ? 'positive' : 'negative'}`}
                                    >
                                        {changePercent >= 0 ? (
                                            <TrendingUp size={10} />
                                        ) : (
                                            <TrendingDown size={10} />
                                        )}
                                        {changePercent >= 0 ? '+' : ''}
                                        {changePercent.toFixed(2)}%
                                    </span>
                                </>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

export default FuturesBlock;
