// components/MiniSparkline.tsx - Lightweight Charts mini sparkline for market indices

import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createChart, ColorType, AreaSeries } from 'lightweight-charts';
import type { IChartApi, ISeriesApi, AreaData, Time } from 'lightweight-charts';
import { fetchMiniChart } from '../api/chartApi';
import type { ChartData } from '../types/chart';

interface MiniSparklineProps {
    symbol: string;
    label: string;
    period?: string;
    candles?: number;
    width?: number;
    height?: number;
}

export function MiniSparkline({
    symbol,
    label,
    period = '1mo',
    candles = 30,
    width = 80,
    height = 40,
}: MiniSparklineProps) {
    const navigate = useNavigate();
    const containerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);

    // Generate a unique cache key based on props
    const cacheKey = `miniSparkline_${symbol}_${period}_${candles}`;

    // Initialize state from localStorage
    const [data, setData] = useState<ChartData | null>(() => {
        const cached = localStorage.getItem(cacheKey);
        if (cached) {
            try {
                return JSON.parse(cached);
            } catch (e) {
                // Ignore parse errors
            }
        }
        return null;
    });

    // If we have data, we're not technically "loading" (we show cached content)
    // but the fetch effect will run in background to update it.
    const [loading, setLoading] = useState(() => !data);
    const [error, setError] = useState<string | null>(null);

    // Fetch data
    useEffect(() => {
        let mounted = true;

        fetchMiniChart(symbol, period, candles)
            .then((chartData) => {
                if (mounted) {
                    setData(chartData);
                    setError(null);
                    setLoading(false);
                    // Update cache
                    localStorage.setItem(cacheKey, JSON.stringify(chartData));
                }
            })
            .catch((err) => {
                if (mounted) {
                    console.error(`Failed to fetch mini chart for ${symbol}:`, err);
                    setError(err.message);
                    setLoading(false);
                }
            });

        return () => { mounted = false; };
    }, [symbol, period, candles, cacheKey]);

    // Create chart
    useEffect(() => {
        if (!containerRef.current || !data || data.candlestick.length === 0) return;

        // Clear previous chart
        if (chartRef.current) {
            chartRef.current.remove();
            chartRef.current = null;
        }

        const chart = createChart(containerRef.current, {
            width,
            height,
            layout: {
                background: { type: ColorType.Solid, color: 'transparent' },
                textColor: 'transparent',
                attributionLogo: false, // Hide TradingView attribution logo
            },
            grid: {
                vertLines: { visible: false },
                horzLines: { visible: false },
            },
            rightPriceScale: { visible: false },
            leftPriceScale: { visible: false },
            timeScale: { visible: false },
            crosshair: {
                vertLine: { visible: false },
                horzLine: { visible: false },
            },
            handleScale: false,
            handleScroll: false,
        });

        chartRef.current = chart;

        // Calculate if trending up or down
        const first = data.candlestick[0]?.close || 0;
        const last = data.candlestick[data.candlestick.length - 1]?.close || 0;
        const isUp = last >= first;

        const lineColor = isUp ? '#10b981' : '#ef4444';
        const areaTopColor = isUp ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)';
        const areaBottomColor = isUp ? 'rgba(16, 185, 129, 0.0)' : 'rgba(239, 68, 68, 0.0)';

        // Lightweight Charts v5 uses addSeries with type parameter
        const areaSeries: ISeriesApi<'Area'> = chart.addSeries(AreaSeries, {
            lineColor,
            topColor: areaTopColor,
            bottomColor: areaBottomColor,
            lineWidth: 1,
            priceLineVisible: false,
            lastValueVisible: false,
            crosshairMarkerVisible: false,
        });

        // Convert candlestick to line data (close prices)
        const lineData: AreaData<Time>[] = data.candlestick.map((c) => ({
            time: c.time as Time,
            value: c.close,
        }));

        areaSeries.setData(lineData);
        chart.timeScale().fitContent();

        return () => {
            chart.remove();
            chartRef.current = null;
        };
    }, [data, width, height]);

    // Calculate change percentage
    const changePercent = data && data.candlestick.length >= 2
        ? ((data.meta.lastPrice - data.candlestick[0].close) / data.candlestick[0].close) * 100
        : 0;

    const isPositive = changePercent >= 0;

    // Format price
    const formatPrice = (price: number) => {
        if (symbol === 'BTC-USD') {
            return `$${price.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
        }
        if (symbol === '^TNX') {
            return `${price.toFixed(2)}%`;
        }
        return price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    };

    if (loading) {
        return (
            <div className="stat-card" style={{ minWidth: '140px' }}>
                <span className="stat-label">{label}</span>
                <span className="stat-value" style={{ opacity: 0.5 }}>Loading...</span>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="stat-card" style={{ minWidth: '140px' }}>
                <span className="stat-label">{label}</span>
                <span className="stat-value" style={{ opacity: 0.5 }}>--</span>
            </div>
        );
    }

    const handleClick = () => {
        navigate(`/chart/${encodeURIComponent(symbol)}`);
    };

    return (
        <div
            className="stat-card"
            onClick={handleClick}
            style={{
                minWidth: '140px',
                padding: '0.75rem 1rem',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
            }}
            onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--accent)';
                e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--card-border)';
                e.currentTarget.style.transform = 'translateY(0)';
            }}
            title={`View ${label} chart`}
        >
            <span className="stat-label">{label}</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span className="stat-value" style={{ fontSize: '1.125rem' }}>
                    {formatPrice(data.meta.lastPrice)}
                </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.25rem' }}>
                <span className={`stat-change ${isPositive ? "positive" : "negative"}`}>
                    {isPositive ? "↗" : "↘"} {isPositive ? "+" : ""}{changePercent.toFixed(2)}%
                </span>
                <div
                    ref={containerRef}
                    style={{
                        width: `${width}px`,
                        height: `${height}px`,
                        marginLeft: 'auto',
                    }}
                />
            </div>
        </div>
    );
}

export default MiniSparkline;
