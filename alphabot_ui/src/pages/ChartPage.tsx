// pages/ChartPage.tsx - Full screen chart view for a stock symbol

import { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, TrendingUp, TrendingDown, Clock } from 'lucide-react';
import { StockChart } from '../components/StockChart';
import { NewsSection } from '../components/NewsSection';
import { getQuote } from '../api/alphaApi';




// Symbol to display name mapping
const symbolLabels: Record<string, string> = {
    'SPY': 'S&P 500 ETF',
    'QQQ': 'NASDAQ 100 ETF',
    'DIA': 'Dow Jones ETF',
    '^VIX': 'VIX Volatility Index',
    '^TNX': '10-Year Treasury Yield',
    'BTC-USD': 'Bitcoin USD',
    'ETH-USD': 'Ethereum USD',
    'AAPL': 'Apple Inc.',
    'MSFT': 'Microsoft Corp.',
    'GOOGL': 'Alphabet Inc.',
    'AMZN': 'Amazon.com Inc.',
    'TSLA': 'Tesla Inc.',
    'NVDA': 'NVIDIA Corp.',
    'META': 'Meta Platforms Inc.',
};

const intervals = [
    { value: '1h', label: '1H' },
    { value: '1d', label: '1D' },
    { value: '1wk', label: '1W' },
    { value: '1mo', label: '1M' },
];

const periods = [
    { value: '1d', label: '1D' },
    { value: '5d', label: '5D' },
    { value: '1mo', label: '1M' },
    { value: '3mo', label: '3M' },
    { value: '6mo', label: '6M' },
    { value: '1y', label: '1Y' },
    { value: '2y', label: '2Y' },
    { value: '5y', label: '5Y' },
    { value: 'max', label: 'MAX' },
];

const indicatorOptions = [
    { id: 'sma_20', label: 'SMA 20', color: '#3b82f6' },
    { id: 'sma_50', label: 'SMA 50', color: '#f59e0b' },
    { id: 'sma_200', label: 'SMA 200', color: '#a855f7' },
    { id: 'volume', label: 'Volume', color: '#6b7280' },
];

export function ChartPage() {
    const { symbol } = useParams<{ symbol: string }>();
    const navigate = useNavigate();

    const [interval, setInterval] = useState('1d');
    const [period, setPeriod] = useState('1y');
    const [indicators, setIndicators] = useState(['sma_20', 'sma_50', 'volume']);
    const [refreshKey, setRefreshKey] = useState(0);

    const displaySymbol = symbol || 'SPY';
    const displayName = symbolLabels[displaySymbol] || displaySymbol;

    const [changeInfo, setChangeInfo] = useState({ change: 0, changePercent: 0, price: 0 });
    const [dailyQuote, setDailyQuote] = useState<{ change: number, changePercent: number, price: number } | null>(null);

    // Initial load & refresh on 1D selection - get daily quote
    useEffect(() => {
        // We always fetch usage quote on mount (displaySymbol changed)
        // AND whenever we switch back to '1d' period to ensure freshness
        if (period === '1d' || !dailyQuote) {
            getQuote(displaySymbol)
                .then(quote => {
                    const quoteData = {
                        change: quote.change,
                        changePercent: quote.change_percent,
                        price: quote.price
                    };
                    setDailyQuote(quoteData);

                    // If we are currently on 1D, update immediately
                    if (period === '1d') {
                        setChangeInfo(quoteData);
                        // Also update the ref for the callback
                        lastUpdatedParams.current = { period: '1d', symbol: displaySymbol };
                    }
                })
                .catch(console.error);
        }
    }, [displaySymbol, period]);

    // Use a ref to track current period for the callback to access without refiring
    const periodRef = useRef(period);
    useEffect(() => { periodRef.current = period; }, [period]);

    const symbolRef = useRef(displaySymbol);
    useEffect(() => { symbolRef.current = displaySymbol; }, [displaySymbol]);

    const dailyQuoteRef = useRef(dailyQuote);
    useEffect(() => { dailyQuoteRef.current = dailyQuote; }, [dailyQuote]);

    // Track the last params we updated the header for, to prevent minor fluctuations from interval changes
    const lastUpdatedParams = useRef({ period: '1y', symbol: '' });

    const handleChartDataLoaded = useCallback((change: number, changePercent: number, price: number) => {
        const currentPeriod = periodRef.current;
        const currentSymbol = symbolRef.current;

        // For 1D period, always prioritize the daily quote for accuracy (Last - PrevClose)
        if (currentPeriod === '1d' && dailyQuoteRef.current) {
            setChangeInfo(dailyQuoteRef.current);
            lastUpdatedParams.current = { period: '1d', symbol: currentSymbol };
            return;
        }

        // For other periods, stabilize the change %
        // If the period and symbol match what's already on screen, 
        // we ONLY update the price (live data) and ignore minor variances in change % caused by 
        // using different candle intervals (e.g. 1D vs 1W candles for same 1Y period).
        if (lastUpdatedParams.current.period === currentPeriod && lastUpdatedParams.current.symbol === currentSymbol) {
            setChangeInfo(prev => ({ ...prev, price }));
        } else {
            // New period or symbol -> Update everything
            setChangeInfo({ change, changePercent, price });
            lastUpdatedParams.current = { period: currentPeriod, symbol: currentSymbol };
        }
    }, []);

    const priceInfo = useMemo(() => {
        if (changeInfo.price === 0) return { price: 0, change: 0, changePercent: 0 };
        return changeInfo;
    }, [changeInfo]);

    const isPositive = priceInfo.changePercent >= 0;

    const toggleIndicator = (id: string) => {
        setIndicators((prev) =>
            prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
        );
    };

    const handleRefresh = () => {
        setRefreshKey((k) => k + 1);
    };

    // Format price based on symbol
    const formatPrice = (price: number) => {
        if (displaySymbol === 'BTC-USD' || displaySymbol === 'ETH-USD') {
            return `$${price.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
        }
        if (displaySymbol === '^TNX') {
            return `${price.toFixed(3)}%`;
        }
        return `$${price.toFixed(2)}`;
    };

    return (
        <div className="page-container" style={{ padding: '1.5rem' }}>
            {/* Header */}
            <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                justifyContent: 'space-between',
                marginBottom: '1.5rem',
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <button
                        onClick={() => navigate(-1)}
                        style={{
                            background: 'var(--card-bg)',
                            border: '1px solid var(--card-border)',
                            borderRadius: '8px',
                            padding: '0.5rem',
                            color: 'var(--fg)',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                        }}
                        title="Go Back"
                    >
                        <ArrowLeft size={20} />
                    </button>
                    <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                            <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--fg)', margin: 0 }}>
                                {displaySymbol}
                            </h1>
                            <span style={{ fontSize: '1rem', color: '#6b7280' }}>
                                {displayName}
                            </span>
                        </div>
                        {priceInfo.price > 0 && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '0.5rem' }}>
                                <span style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--fg)' }}>
                                    {formatPrice(priceInfo.price)}
                                </span>
                                <span style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.25rem',
                                    fontSize: '1rem',
                                    fontWeight: 500,
                                    color: isPositive ? 'var(--accent)' : 'var(--accent-pink)',
                                }}>
                                    {isPositive ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                                    {isPositive ? '+' : ''}{priceInfo.change.toFixed(2)} ({isPositive ? '+' : ''}{priceInfo.changePercent.toFixed(2)}%)
                                </span>
                                <span style={{ fontSize: '0.75rem', color: '#6b7280', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                    <Clock size={12} />
                                    {new Date().toLocaleDateString()}
                                </span>
                            </div>
                        )}
                    </div>
                </div>
                <button
                    onClick={handleRefresh}
                    style={{
                        background: 'var(--card-bg)',
                        border: '1px solid var(--card-border)',
                        borderRadius: '8px',
                        padding: '0.5rem 1rem',
                        color: 'var(--fg)',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        fontSize: '0.875rem',
                    }}
                    title="Refresh Chart"
                >
                    <RefreshCw size={16} />
                    Refresh
                </button>
            </div>

            {/* Controls */}
            <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                alignItems: 'flex-end',
                gap: '2rem',
                marginBottom: '1rem',
                padding: '0.5rem 0',
            }}>
                {/* Interval Selector */}
                <div>
                    <span style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.5rem', display: 'block' }}>
                        Interval
                    </span>
                    <div style={{ display: 'flex', gap: '0.25rem' }}>
                        {intervals.map((int) => (
                            <button
                                key={int.value}
                                onClick={() => setInterval(int.value)}
                                style={{
                                    padding: '0.375rem 0.75rem',
                                    borderRadius: '6px',
                                    border: 'none',
                                    fontSize: '0.75rem',
                                    fontWeight: 500,
                                    cursor: 'pointer',
                                    backgroundColor: interval === int.value ? 'var(--accent)' : '#1f1f1f',
                                    color: interval === int.value ? '#000' : '#9ca3af',
                                    transition: 'all 0.15s',
                                }}
                            >
                                {int.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Period Selector */}
                <div>
                    <span style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.5rem', display: 'block' }}>
                        Period
                    </span>
                    <div style={{ display: 'flex', gap: '0.25rem' }}>
                        {periods.map((p) => (
                            <button
                                key={p.value}
                                onClick={() => setPeriod(p.value)}
                                style={{
                                    padding: '0.375rem 0.75rem',
                                    borderRadius: '6px',
                                    border: 'none',
                                    fontSize: '0.75rem',
                                    fontWeight: 500,
                                    cursor: 'pointer',
                                    backgroundColor: period === p.value ? 'var(--accent)' : '#1f1f1f',
                                    color: period === p.value ? '#000' : '#9ca3af',
                                    transition: 'all 0.15s',
                                }}
                            >
                                {p.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Indicator Toggles */}
                <div>
                    <span style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.5rem', display: 'block' }}>
                        Indicators
                    </span>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                        {indicatorOptions.map((ind) => (
                            <button
                                key={ind.id}
                                onClick={() => toggleIndicator(ind.id)}
                                style={{
                                    padding: '0.375rem 0.75rem',
                                    borderRadius: '6px',
                                    border: indicators.includes(ind.id) ? `2px solid ${ind.color}` : '2px solid #1f1f1f',
                                    fontSize: '0.75rem',
                                    fontWeight: 500,
                                    cursor: 'pointer',
                                    backgroundColor: indicators.includes(ind.id) ? `${ind.color}20` : '#1f1f1f',
                                    color: indicators.includes(ind.id) ? ind.color : '#6b7280',
                                    transition: 'all 0.15s',
                                }}
                            >
                                {ind.label}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Chart */}
            <div style={{
                backgroundColor: 'var(--card-bg)',
                border: '1px solid var(--card-border)',
                borderRadius: '12px',
                overflow: 'hidden',
            }}>
                <StockChart
                    key={`${displaySymbol}-${interval}-${period}-${indicators.join(',')}-${refreshKey}`}
                    symbol={displaySymbol}
                    interval={interval}
                    period={period}
                    indicators={indicators}
                    height={600}
                    onDataLoaded={handleChartDataLoaded}
                />
            </div>

            {/* Legend */}
            <div style={{
                display: 'flex',
                gap: '1.5rem',
                padding: '1rem',
                marginTop: '0.5rem',
                fontSize: '0.75rem',
                color: '#6b7280',
            }}>
                {indicators.includes('sma_20') && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ width: '12px', height: '3px', backgroundColor: '#3b82f6', borderRadius: '2px' }} />
                        SMA 20
                    </span>
                )}
                {indicators.includes('sma_50') && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ width: '12px', height: '3px', backgroundColor: '#f59e0b', borderRadius: '2px' }} />
                        SMA 50
                    </span>
                )}
                {indicators.includes('sma_200') && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ width: '12px', height: '3px', backgroundColor: '#a855f7', borderRadius: '2px' }} />
                        SMA 200
                    </span>
                )}
            </div>

            {/* News Section */}
            <NewsSection symbol={displaySymbol} />
        </div>
    );
}

export default ChartPage;
