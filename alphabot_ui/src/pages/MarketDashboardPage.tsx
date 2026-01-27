import { useState } from 'react';
import { useDashboard } from '../hooks/useDashboard';
import { useHeatmap } from '../hooks/useHeatmap';
import { Activity, Layers, Newspaper, TrendingUp, TrendingDown, Volume2, Zap, BarChart3, PieChart } from 'lucide-react';
import { ResponsiveContainer, Treemap, Tooltip as RechartsTooltip } from 'recharts';

// --- Helper Functions ---

const getFillColor = (change: number): string => {
    if (change >= 3) return '#00ff85';
    if (change >= 0) return '#004225';
    if (change >= -3) return '#ff3366';
    return '#991f3d';
};

// --- Stock List Component (Matching the uploaded image style) ---

interface StockListProps {
    title: string;
    stocks: any[];
    page: number;
    onPageChange: (page: number) => void;
    pageSize?: number;
}

const StockList = ({ title, stocks, page, onPageChange, pageSize = 10 }: StockListProps) => {
    const totalPages = Math.ceil(stocks.length / pageSize);
    const startIdx = page * pageSize;
    const visibleStocks = stocks.slice(startIdx, startIdx + pageSize);

    const canGoBack = page > 0;
    const canGoForward = page < totalPages - 1;
    const canJumpBack5 = page >= 5;
    const canJumpForward5 = page + 5 < totalPages;

    // Simple arrow button style
    const arrowBtnStyle = (enabled: boolean): React.CSSProperties => ({
        padding: '0.25rem 0.5rem',
        fontSize: '0.75rem',
        fontWeight: 600,
        color: enabled ? 'var(--fg)' : '#4b5563',
        cursor: enabled ? 'pointer' : 'not-allowed',
        opacity: enabled ? 1 : 0.5,
        background: 'transparent',
        border: 'none',
        transition: 'color 0.2s',
    });

    return (
        <div style={{
            backgroundColor: 'var(--card-bg)',
            border: '1px solid var(--card-border)',
            borderRadius: '12px',
            padding: '1.25rem',
            flex: 1,
        }}>
            {/* Header */}
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '1rem',
                paddingBottom: '0.75rem',
                borderBottom: '1px solid var(--card-border)',
            }}>
                <span style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--fg)' }}>{title}</span>

                {/* Pagination Controls - Clean text arrows */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <span style={{ fontSize: '0.75rem', color: '#6b7280', marginRight: '0.5rem' }}>
                        {startIdx + 1}-{Math.min(startIdx + pageSize, stocks.length)} of {stocks.length}
                    </span>

                    {/* Jump back 5 pages */}
                    <button
                        onClick={() => canJumpBack5 && onPageChange(page - 5)}
                        disabled={!canJumpBack5}
                        style={arrowBtnStyle(canJumpBack5)}
                        title="Back 50"
                    >
                        ««
                    </button>

                    {/* Back 1 page */}
                    <button
                        onClick={() => canGoBack && onPageChange(page - 1)}
                        disabled={!canGoBack}
                        style={arrowBtnStyle(canGoBack)}
                        title="Back 10"
                    >
                        ‹
                    </button>

                    {/* Forward 1 page */}
                    <button
                        onClick={() => canGoForward && onPageChange(page + 1)}
                        disabled={!canGoForward}
                        style={arrowBtnStyle(canGoForward)}
                        title="Next 10"
                    >
                        ›
                    </button>

                    {/* Jump forward 5 pages */}
                    <button
                        onClick={() => canJumpForward5 && onPageChange(page + 5)}
                        disabled={!canJumpForward5}
                        style={arrowBtnStyle(canJumpForward5)}
                        title="Next 50"
                    >
                        »»
                    </button>
                </div>
            </div>

            {/* Stock Rows with better spacing */}
            <div>
                {visibleStocks.map((stock, i) => {
                    const ticker = stock.ticker || stock.symbol;
                    const company = stock.company || stock.company_name || '';
                    const price = stock.last || stock.price || 0;
                    const change = stock.change || stock.change_percent || 0;
                    const isPositive = change >= 0;

                    return (
                        <div
                            key={ticker || i}
                            style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                padding: '0.875rem 0',
                                borderBottom: i < visibleStocks.length - 1 ? '1px solid var(--card-border)' : 'none',
                            }}
                        >
                            {/* Left: Ticker & Company */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                <span style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--fg)' }}>{ticker}</span>
                                <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>{company}</span>
                            </div>

                            {/* Right: Price & Change pill (no icon) */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                <span style={{ fontSize: '0.875rem', color: 'var(--fg)' }}>{price.toFixed(2)}</span>

                                {/* Compact pill badge - no icon */}
                                <span style={{
                                    padding: '0.25rem 0.625rem',
                                    borderRadius: '4px',
                                    fontSize: '0.75rem',
                                    fontWeight: 600,
                                    backgroundColor: isPositive ? 'rgba(0, 255, 133, 0.15)' : 'rgba(255, 51, 102, 0.15)',
                                    color: isPositive ? 'var(--accent)' : 'var(--accent-pink)',
                                }}>
                                    {isPositive ? '+' : ''}{change.toFixed(2)}%
                                </span>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

// --- Treemap Content ---

const CustomizedTreemapContent = (props: any) => {
    const { x, y, width, height, payload } = props;

    // Guard against invalid dimensions - recharts can pass -1 or undefined values
    if (
        typeof x !== 'number' || typeof y !== 'number' ||
        typeof width !== 'number' || typeof height !== 'number' ||
        width <= 0 || height <= 0 || !payload
    ) {
        return null;
    }

    return (
        <g>
            <rect
                x={x}
                y={y}
                width={width}
                height={height}
                style={{
                    fill: getFillColor(payload.change || 0),
                    stroke: 'var(--bg)',
                    strokeWidth: 2,
                }}
            />
            {width > 30 && height > 30 && (
                <text
                    x={x + width / 2}
                    y={y + height / 2}
                    textAnchor="middle"
                    fill="#fff"
                    fontSize={Math.min(width / 4, 12)}
                    fontWeight="bold"
                    alignmentBaseline="central"
                >
                    {payload.name}
                </text>
            )}
            {width > 40 && height > 40 && (
                <text
                    x={x + width / 2}
                    y={y + height / 2 + 14}
                    textAnchor="middle"
                    fill="#eee"
                    fontSize={10}
                >
                    {(payload.change > 0 ? '+' : '') + payload.change}%
                </text>
            )}
        </g>
    );
};

// --- Main Page ---

export default function MarketDashboardPage() {
    const { overview, gainers, losers, headlines, loading, error } = useDashboard();
    const { data: heatmapData } = useHeatmap();

    // Pagination state for gainers and losers
    const [gainersPage, setGainersPage] = useState(0);
    const [losersPage, setLosersPage] = useState(0);

    if (loading && !overview) {
        return (
            <div className="page-container flex items-center justify-center h-full">
                <Activity className="animate-spin mr-2 text-[var(--accent)]" size={20} />
                <span className="text-gray-400">Loading Market Data...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className="page-container flex items-center justify-center">
                <div className="position-card p-8 text-center">
                    <p className="text-[var(--accent-pink)]">Error: {error}</p>
                    <p className="text-gray-500 text-sm mt-2">Is the backend running?</p>
                </div>
            </div>
        );
    }

    const treeData = heatmapData?.sectors ? Object.entries(heatmapData.sectors).map(([sector, data]: any) => ({
        name: sector,
        children: data.stocks.map((s: any) => ({
            name: s.symbol,
            size: s.marketCap,
            change: s.change,
            ...s
        }))
    })) : [];

    // Use backend Fear & Greed if available, otherwise calculate client-side
    const fearGreed = overview?.fear_greed || (() => {
        if (!overview) return { score: 50, label: 'Neutral', color: '#6b7280' };

        let score = 0;

        // Factor 1: Advance/Decline (0-25 points)
        const advPct = overview.breadth?.advance_percent || 50;
        score += Math.min(25, Math.max(0, (advPct - 30) * 0.625));

        // Factor 2: Stocks above SMA 50 (0-25 points)
        const sma50Pct = overview.sma_analysis?.sma50?.above_percent || 50;
        score += Math.min(25, Math.max(0, (sma50Pct - 30) * 0.625));

        // Factor 3: Stocks above SMA 200 (0-25 points)
        const sma200Pct = overview.sma_analysis?.sma200?.above_percent || 50;
        score += Math.min(25, Math.max(0, (sma200Pct - 30) * 0.625));

        // Factor 4: New Highs vs New Lows (0-25 points)
        const highs = overview.breadth?.new_highs || 0;
        const lows = overview.breadth?.new_lows || 1;
        const hlRatio = highs / lows;
        score += Math.min(25, Math.max(0, (hlRatio - 0.33) * 9.375));

        const finalScore = Math.round(score);

        let label = 'Neutral';
        let color = '#6b7280';

        if (finalScore >= 75) { label = 'Extreme Greed'; color = '#00ff85'; }
        else if (finalScore >= 55) { label = 'Greed'; color = '#22c55e'; }
        else if (finalScore >= 45) { label = 'Neutral'; color = '#6b7280'; }
        else if (finalScore >= 25) { label = 'Fear'; color = '#f59e0b'; }
        else { label = 'Extreme Fear'; color = '#ff3366'; }

        return { score: finalScore, label, color };
    })();
    const totalStocks = overview?.stats?.total_stocks || overview?.breadth?.total || 0;

    return (
        <div className="page-container">

            {/* Header */}
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h1 className="page-title">Market Overview</h1>
                    <p className="page-subtitle">
                        {totalStocks.toLocaleString()} stocks • Last updated: {overview?.updated_at ? new Date(overview.updated_at).toLocaleTimeString() : '--:--'}
                    </p>
                </div>

                {/* Fear & Greed Indicator */}
                <div style={{
                    backgroundColor: 'var(--card-bg)',
                    border: '1px solid var(--card-border)',
                    borderRadius: '12px',
                    padding: '1rem 1.5rem',
                    textAlign: 'center',
                    minWidth: '160px',
                }}>
                    <span style={{ fontSize: '0.6875rem', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                        Fear & Greed
                    </span>
                    <div style={{
                        fontSize: '2rem',
                        fontWeight: 700,
                        color: fearGreed.color,
                        lineHeight: 1.2,
                        marginTop: '0.25rem',
                    }}>
                        {fearGreed.score}
                    </div>
                    <span style={{
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        color: fearGreed.color,
                    }}>
                        {fearGreed.label}
                    </span>
                    {/* Mini gauge bar */}
                    <div style={{
                        marginTop: '0.5rem',
                        height: '4px',
                        borderRadius: '2px',
                        background: 'linear-gradient(to right, #ff3366, #f59e0b, #6b7280, #22c55e, #00ff85)',
                        position: 'relative',
                    }}>
                        <div style={{
                            position: 'absolute',
                            left: `${fearGreed.score}%`,
                            top: '-3px',
                            width: '10px',
                            height: '10px',
                            backgroundColor: 'var(--fg)',
                            borderRadius: '50%',
                            transform: 'translateX(-50%)',
                            border: '2px solid var(--card-bg)',
                        }} />
                    </div>
                </div>
            </div>

            {/* === COMPACT MARKET INDICATORS === */}
            <div style={{
                backgroundColor: 'var(--card-bg)',
                border: '1px solid var(--card-border)',
                borderRadius: '12px',
                padding: '1rem 1.25rem',
                marginBottom: '1.5rem',
            }}>
                {/* Market Breadth Bar - Integrated at top */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1rem',
                    marginBottom: '1rem',
                    paddingBottom: '0.75rem',
                    borderBottom: '1px solid var(--card-border)',
                }}>
                    <span style={{
                        fontSize: '0.875rem',
                        fontWeight: 600,
                        color: 'var(--fg)',
                        whiteSpace: 'nowrap'
                    }}>
                        Market Breadth
                    </span>
                    <div style={{
                        flex: 1,
                        height: '10px',
                        backgroundColor: 'var(--card-border)',
                        borderRadius: '5px',
                        overflow: 'hidden',
                        display: 'flex'
                    }}>
                        <div style={{
                            height: '100%',
                            backgroundColor: 'var(--accent)',
                            transition: 'width 0.5s',
                            width: `${overview?.breadth?.advance_percent || 0}%`
                        }} />
                        <div style={{
                            height: '100%',
                            backgroundColor: 'var(--accent-pink)',
                            transition: 'width 0.5s',
                            width: `${overview?.breadth?.decline_percent || 0}%`
                        }} />
                    </div>
                    <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.75rem', fontWeight: 600 }}>
                        <span style={{ color: 'var(--accent)' }}>
                            ▲ {overview?.breadth?.advancing?.toLocaleString()} ({overview?.breadth?.advance_percent?.toFixed(1)}%)
                        </span>
                        <span style={{ color: 'var(--accent-pink)' }}>
                            ▼ {overview?.breadth?.declining?.toLocaleString()} ({overview?.breadth?.decline_percent?.toFixed(1)}%)
                        </span>
                    </div>
                </div>

                {/* Compact 8-indicator grid */}
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(4, 1fr)',
                    gap: '0.5rem 1rem',
                }}>
                    {/* Row 1: Core Breadth Metrics */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0' }}>
                        <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>52W Highs</span>
                        <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--accent)' }}>
                            {overview?.breadth?.new_highs || 0}
                        </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0' }}>
                        <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>52W Lows</span>
                        <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--accent-pink)' }}>
                            {overview?.breadth?.new_lows || 0}
                        </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0' }}>
                        <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>High/Low Ratio</span>
                        <span style={{
                            fontSize: '0.875rem',
                            fontWeight: 600,
                            color: (overview?.breadth?.new_highs || 0) >= (overview?.breadth?.new_lows || 1) ? 'var(--accent)' : 'var(--accent-pink)'
                        }}>
                            {overview?.breadth?.new_lows ? ((overview?.breadth?.new_highs || 0) / overview.breadth.new_lows).toFixed(2) : '--'}
                        </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0' }}>
                        <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>A/D Ratio</span>
                        <span style={{
                            fontSize: '0.875rem',
                            fontWeight: 600,
                            color: (overview?.breadth?.advance_percent || 0) >= 50 ? 'var(--accent)' : 'var(--accent-pink)'
                        }}>
                            {overview?.breadth?.advance_decline_ratio?.toFixed(2) || '--'}
                        </span>
                    </div>

                    {/* Divider */}
                    <div style={{ gridColumn: '1 / -1', height: '1px', backgroundColor: 'var(--card-border)', margin: '0.25rem 0' }} />

                    {/* Row 2: SMA Analysis - Calculate accurate counts from percentages */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0' }}>
                        <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>Above SMA 50</span>
                        <div style={{ textAlign: 'right' }}>
                            <span style={{
                                fontSize: '0.875rem',
                                fontWeight: 600,
                                color: (overview?.sma_analysis?.sma50?.above_percent || 0) >= 50 ? 'var(--accent)' : 'var(--accent-pink)'
                            }}>
                                {overview?.sma_analysis?.sma50?.above_percent?.toFixed(1) || '--'}%
                            </span>
                            <span style={{ fontSize: '0.6875rem', color: '#6b7280', marginLeft: '0.5rem' }}>
                                ({Math.round((overview?.sma_analysis?.sma50?.above_percent || 0) / 100 * totalStocks).toLocaleString()})
                            </span>
                        </div>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0' }}>
                        <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>Below SMA 50</span>
                        <div style={{ textAlign: 'right' }}>
                            <span style={{
                                fontSize: '0.875rem',
                                fontWeight: 600,
                                color: '#6b7280'
                            }}>
                                {(100 - (overview?.sma_analysis?.sma50?.above_percent || 0)).toFixed(1)}%
                            </span>
                            <span style={{ fontSize: '0.6875rem', color: '#6b7280', marginLeft: '0.5rem' }}>
                                ({Math.round((100 - (overview?.sma_analysis?.sma50?.above_percent || 0)) / 100 * totalStocks).toLocaleString()})
                            </span>
                        </div>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0' }}>
                        <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>Above SMA 200</span>
                        <div style={{ textAlign: 'right' }}>
                            <span style={{
                                fontSize: '0.875rem',
                                fontWeight: 600,
                                color: (overview?.sma_analysis?.sma200?.above_percent || 0) >= 50 ? 'var(--accent)' : 'var(--accent-pink)'
                            }}>
                                {overview?.sma_analysis?.sma200?.above_percent?.toFixed(1) || '--'}%
                            </span>
                            <span style={{ fontSize: '0.6875rem', color: '#6b7280', marginLeft: '0.5rem' }}>
                                ({Math.round((overview?.sma_analysis?.sma200?.above_percent || 0) / 100 * totalStocks).toLocaleString()})
                            </span>
                        </div>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0' }}>
                        <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>Below SMA 200</span>
                        <div style={{ textAlign: 'right' }}>
                            <span style={{
                                fontSize: '0.875rem',
                                fontWeight: 600,
                                color: '#6b7280'
                            }}>
                                {(100 - (overview?.sma_analysis?.sma200?.above_percent || 0)).toFixed(1)}%
                            </span>
                            <span style={{ fontSize: '0.6875rem', color: '#6b7280', marginLeft: '0.5rem' }}>
                                ({Math.round((100 - (overview?.sma_analysis?.sma200?.above_percent || 0)) / 100 * totalStocks).toLocaleString()})
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* === NEW INDICATOR SECTIONS === */}

            {/* Volume Analysis Section */}
            {overview?.volume_analysis && (
                <div style={{
                    backgroundColor: 'var(--card-bg)',
                    border: '1px solid var(--card-border)',
                    borderRadius: '12px',
                    padding: '1.25rem',
                    marginBottom: '1.5rem',
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                        <Volume2 size={18} style={{ color: 'var(--accent)' }} />
                        <span style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--fg)' }}>Volume Analysis</span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
                        <div className="summary-card">
                            <span className="summary-label">Total Volume</span>
                            <span className="summary-value">
                                {(overview.volume_analysis.total_volume / 1e9).toFixed(2)}B
                            </span>
                            <span style={{ fontSize: '0.6875rem', color: '#6b7280' }}>shares traded</span>
                        </div>
                        <div className={`summary-card ${overview.volume_analysis.up_volume > overview.volume_analysis.down_volume ? 'positive' : ''}`}>
                            <span className="summary-label">Up Volume</span>
                            <span className="summary-value">{overview.volume_analysis.up_volume_percent?.toFixed(1) || '--'}%</span>
                            <span style={{ fontSize: '0.6875rem', color: 'var(--accent)' }}>
                                {(overview.volume_analysis.up_volume / 1e6).toFixed(0)}M shares
                            </span>
                        </div>
                        <div className={`summary-card ${overview.volume_analysis.down_volume > overview.volume_analysis.up_volume ? 'negative' : ''}`}>
                            <span className="summary-label">Down Volume</span>
                            <span className="summary-value">{(100 - (overview.volume_analysis.up_volume_percent || 0)).toFixed(1)}%</span>
                            <span style={{ fontSize: '0.6875rem', color: 'var(--accent-pink)' }}>
                                {(overview.volume_analysis.down_volume / 1e6).toFixed(0)}M shares
                            </span>
                        </div>
                        <div className={`summary-card ${overview.volume_analysis.volume_ratio >= 1 ? 'positive' : 'negative'}`}>
                            <span className="summary-label">Volume Ratio</span>
                            <span className="summary-value">{overview.volume_analysis.volume_ratio?.toFixed(2) || '--'}</span>
                            <span style={{ fontSize: '0.6875rem', color: '#6b7280' }}>
                                {overview.volume_analysis.volume_ratio >= 1 ? 'Bullish' : 'Bearish'} bias
                            </span>
                        </div>
                    </div>
                </div>
            )}

            {/* Momentum Section */}
            {overview?.momentum && (
                <div style={{
                    backgroundColor: 'var(--card-bg)',
                    border: '1px solid var(--card-border)',
                    borderRadius: '12px',
                    padding: '1.25rem',
                    marginBottom: '1.5rem',
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                        <Zap size={18} style={{ color: 'var(--accent)' }} />
                        <span style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--fg)' }}>Momentum</span>
                        <span style={{
                            marginLeft: 'auto',
                            padding: '0.25rem 0.75rem',
                            borderRadius: '12px',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            backgroundColor: overview.momentum.net_gainers_1pct >= 0 ? 'rgba(0, 255, 133, 0.15)' : 'rgba(255, 51, 102, 0.15)',
                            color: overview.momentum.net_gainers_1pct >= 0 ? 'var(--accent)' : 'var(--accent-pink)',
                        }}>
                            Net: {overview.momentum.net_gainers_1pct >= 0 ? '+' : ''}{overview.momentum.net_gainers_1pct}
                        </span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
                        <div className="summary-card positive">
                            <span className="summary-label">Gainers &gt;5%</span>
                            <span className="summary-value">{overview.momentum.gainers_5pct}</span>
                            <span style={{ fontSize: '0.6875rem', color: 'var(--accent)' }}>big movers up</span>
                        </div>
                        <div className="summary-card">
                            <span className="summary-label">Gainers &gt;3%</span>
                            <span className="summary-value">{overview.momentum.gainers_3pct}</span>
                            <span style={{ fontSize: '0.6875rem', color: '#6b7280' }}>strong gainers</span>
                        </div>
                        <div className="summary-card">
                            <span className="summary-label">Gainers &gt;1%</span>
                            <span className="summary-value">{overview.momentum.gainers_1pct}</span>
                            <span style={{ fontSize: '0.6875rem', color: '#6b7280' }}>moderate gainers</span>
                        </div>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
                        <div className="summary-card negative">
                            <span className="summary-label">Losers &gt;5%</span>
                            <span className="summary-value">{overview.momentum.losers_5pct}</span>
                            <span style={{ fontSize: '0.6875rem', color: 'var(--accent-pink)' }}>big movers down</span>
                        </div>
                        <div className="summary-card">
                            <span className="summary-label">Losers &gt;3%</span>
                            <span className="summary-value">{overview.momentum.losers_3pct}</span>
                            <span style={{ fontSize: '0.6875rem', color: '#6b7280' }}>strong losers</span>
                        </div>
                        <div className="summary-card">
                            <span className="summary-label">Losers &gt;1%</span>
                            <span className="summary-value">{overview.momentum.losers_1pct}</span>
                            <span style={{ fontSize: '0.6875rem', color: '#6b7280' }}>moderate losers</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Volatility Section */}
            {overview?.volatility && (
                <div style={{
                    backgroundColor: 'var(--card-bg)',
                    border: '1px solid var(--card-border)',
                    borderRadius: '12px',
                    padding: '1.25rem',
                    marginBottom: '1.5rem',
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                        <BarChart3 size={18} style={{ color: 'var(--accent)' }} />
                        <span style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--fg)' }}>Volatility</span>
                        <span style={{
                            marginLeft: 'auto',
                            padding: '0.25rem 0.75rem',
                            borderRadius: '12px',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            textTransform: 'capitalize',
                            backgroundColor: overview.volatility.volatility_level === 'high' ? 'rgba(255, 51, 102, 0.15)' :
                                overview.volatility.volatility_level === 'low' ? 'rgba(0, 255, 133, 0.15)' : 'rgba(107, 114, 128, 0.15)',
                            color: overview.volatility.volatility_level === 'high' ? 'var(--accent-pink)' :
                                overview.volatility.volatility_level === 'low' ? 'var(--accent)' : '#6b7280',
                        }}>
                            {overview.volatility.volatility_level} Volatility
                        </span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
                        <div className="summary-card positive">
                            <span className="summary-label">Big Movers Up</span>
                            <span className="summary-value">{overview.volatility.big_movers_up}</span>
                            <span style={{ fontSize: '0.6875rem', color: 'var(--accent)' }}>stocks up 5%+</span>
                        </div>
                        <div className="summary-card negative">
                            <span className="summary-label">Big Movers Down</span>
                            <span className="summary-value">{overview.volatility.big_movers_down}</span>
                            <span style={{ fontSize: '0.6875rem', color: 'var(--accent-pink)' }}>stocks down 5%+</span>
                        </div>
                        <div className="summary-card">
                            <span className="summary-label">Total Big Movers</span>
                            <span className="summary-value">{overview.volatility.total_big_movers}</span>
                            <span style={{ fontSize: '0.6875rem', color: '#6b7280' }}>high volatility stocks</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Sector Performance Section */}
            {overview?.sectors && overview.sectors.length > 0 && (
                <div style={{
                    backgroundColor: 'var(--card-bg)',
                    border: '1px solid var(--card-border)',
                    borderRadius: '12px',
                    padding: '1.25rem',
                    marginBottom: '1.5rem',
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                        <PieChart size={18} style={{ color: 'var(--accent)' }} />
                        <span style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--fg)' }}>Sector Performance</span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '0.75rem' }}>
                        {overview.sectors.slice(0, 11).map((sector, idx) => (
                            <div key={sector.sector} style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                padding: '0.75rem 1rem',
                                backgroundColor: 'var(--bg)',
                                borderRadius: '8px',
                                border: '1px solid var(--card-border)',
                            }}>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.125rem' }}>
                                    <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--fg)' }}>
                                        {idx + 1}. {sector.sector}
                                    </span>
                                    <span style={{ fontSize: '0.6875rem', color: '#6b7280' }}>
                                        {sector.stock_count} stocks • {sector.percent_advancing?.toFixed(0) || '--'}% advancing
                                    </span>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    {sector.avg_change >= 0 ? (
                                        <TrendingUp size={14} style={{ color: 'var(--accent)' }} />
                                    ) : (
                                        <TrendingDown size={14} style={{ color: 'var(--accent-pink)' }} />
                                    )}
                                    <span style={{
                                        fontSize: '0.875rem',
                                        fontWeight: 600,
                                        color: sector.avg_change >= 0 ? 'var(--accent)' : 'var(--accent-pink)',
                                    }}>
                                        {sector.avg_change >= 0 ? '+' : ''}{sector.avg_change?.toFixed(2) || '0.00'}%
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Top Gainers & Losers - Side by Side */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: '1.5rem',
                marginBottom: '1.5rem'
            }}>
                <StockList
                    title="Top Gainers"
                    stocks={gainers}
                    page={gainersPage}
                    onPageChange={setGainersPage}
                />
                <StockList
                    title="Top Losers"
                    stocks={losers}
                    page={losersPage}
                    onPageChange={setLosersPage}
                />
            </div>

            {/* Heatmap Section */}
            <div className="position-card p-4 overflow-hidden h-[400px] flex flex-col mb-6">
                <div className="flex items-center gap-2 mb-4">
                    <Layers size={18} className="text-[var(--accent)]" />
                    <span className="position-ticker">Sector Heatmap</span>
                </div>
                {treeData.length > 0 ? (
                    <div className="flex-1 min-h-0">
                        <ResponsiveContainer width="100%" height="100%">
                            <Treemap
                                data={treeData}
                                dataKey="size"
                                aspectRatio={4 / 3}
                                stroke="var(--bg)"
                                content={<CustomizedTreemapContent />}
                            >
                                <RechartsTooltip
                                    content={({ payload }: any) => {
                                        if (payload && payload.length) {
                                            const d = payload[0].payload;
                                            return (
                                                <div className="position-card p-3 text-xs">
                                                    <p className="font-bold text-[var(--fg)] text-sm">{d.name}</p>
                                                    <p className="text-gray-400">Price: ${d.price}</p>
                                                    <p className={d.change >= 0 ? 'text-[var(--accent)]' : 'text-[var(--accent-pink)]'}>
                                                        Change: {d.change}%
                                                    </p>
                                                </div>
                                            );
                                        }
                                        return null;
                                    }}
                                />
                            </Treemap>
                        </ResponsiveContainer>
                    </div>
                ) : (
                    <div className="flex-1 flex items-center justify-center text-gray-500">
                        No Heatmap Data Available
                    </div>
                )}
            </div>

            {/* Headlines */}
            <div className="position-card p-4">
                <div className="flex items-center gap-2 mb-4">
                    <Newspaper size={18} className="text-[var(--accent)]" />
                    <span className="position-ticker">Market Headlines</span>
                </div>
                <div className="divide-y divide-[var(--card-border)]">
                    {headlines.slice(0, 5).map((headline) => (
                        <a
                            key={headline.id}
                            href={headline.url}
                            target="_blank"
                            rel="noreferrer"
                            className="block py-3 hover:bg-white/5 transition-colors first:pt-0 last:pb-0"
                        >
                            <div className="flex justify-between items-start gap-4">
                                <span className="text-[var(--fg)] hover:text-[var(--accent)] transition-colors text-sm">
                                    {headline.title}
                                </span>
                                <span className="text-xs text-gray-500 whitespace-nowrap">
                                    {headline.age}
                                </span>
                            </div>
                            <div className="flex gap-2 mt-1 text-xs">
                                <span className="text-gray-600">{headline.source}</span>
                                {headline.sentiment && (
                                    <span className={`${headline.sentiment === 'positive' ? 'text-[var(--accent)]' :
                                        headline.sentiment === 'negative' ? 'text-[var(--accent-pink)]' :
                                            'text-gray-500'
                                        }`}>
                                        {headline.sentiment}
                                    </span>
                                )}
                            </div>
                        </a>
                    ))}
                </div>
            </div>

            <div className="h-8" />

        </div>
    );
}
