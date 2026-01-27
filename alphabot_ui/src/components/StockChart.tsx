// components/StockChart.tsx - Full interactive chart using Lightweight Charts

import { useEffect, useRef, useState, useCallback } from 'react';
import { createChart, ColorType, CandlestickSeries, HistogramSeries, LineSeries } from 'lightweight-charts';
import type { IChartApi, ISeriesApi, Time, CandlestickData as LWCandlestickData } from 'lightweight-charts';
import { fetchChartData } from '../api/chartApi';
import type { ChartData } from '../types/chart';

interface StockChartProps {
    symbol: string;
    interval?: string;
    period?: string;
    indicators?: string[];
    height?: number;
    onDataLoaded?: (change: number, changePercent: number, price: number) => void;
}

export function StockChart({
    symbol,
    interval = '1d',
    period = '1y',
    indicators = ['sma_20', 'sma_50', 'sma_200', 'volume'],
    height = 500,
    onDataLoaded,
}: StockChartProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    // Generate cache key
    const cacheKey = `chartData_${symbol}_${interval}_${period}_${indicators.join('_')}`;

    // Initialize state from localStorage
    const [data, setData] = useState<ChartData | null>(() => {
        const cached = localStorage.getItem(cacheKey);
        if (cached) {
            try {
                return JSON.parse(cached);
            } catch (e) {
                // Ignore
            }
        }
        return null;
    });

    // If we have data, we are not loading for the user (background refresh)
    const [loading, setLoading] = useState(() => !data);
    const [error, setError] = useState<string | null>(null);

    // Fetch chart data
    const loadData = useCallback(async () => {
        // Only show loading if we don't have data
        if (!data) {
            setLoading(true);
        }
        setError(null);
        try {
            const chartData = await fetchChartData(symbol, interval, period, indicators);
            setData(chartData);

            // Update cache
            try {
                localStorage.setItem(cacheKey, JSON.stringify(chartData));
            } catch (e) {
                // Handle quota exceeded
            }

            // Calculate change over the fetched period
            if (chartData.candlestick.length > 0 && onDataLoaded) {
                const last = chartData.candlestick[chartData.candlestick.length - 1].close;
                let change: number;
                let changePercent: number;

                if (chartData.meta.periodPreviousClose) {
                    // Use the official previous close from before the period started (more accurate)
                    const prevClose = chartData.meta.periodPreviousClose;
                    change = last - prevClose;
                    changePercent = (change / prevClose) * 100;
                } else {
                    // Fallback: compare against the first open of the chart
                    // (This effectively calculates intraday return of the chart period)
                    const first = chartData.candlestick[0].open;
                    change = last - first;
                    changePercent = (change / first) * 100;
                }

                onDataLoaded(change, changePercent, last);
            }

        } catch (err) {
            console.error(err);
            // Only show error UI if we have no data at all
            if (!data) {
                setError(err instanceof Error ? err.message : 'Failed to load chart');
            }
        } finally {
            setLoading(false);
        }
    }, [symbol, interval, period, indicators.join(','), onDataLoaded, cacheKey]); // Removed 'data' from dependency to avoid loop

    useEffect(() => {
        loadData();
    }, [loadData]);

    // Create/update chart
    useEffect(() => {
        if (!containerRef.current || !data || data.candlestick.length === 0) return;

        // Clear previous chart
        if (chartRef.current) {
            chartRef.current.remove();
            chartRef.current = null;
        }

        const chart = createChart(containerRef.current, {
            width: containerRef.current.clientWidth,
            height,
            layout: {
                background: { type: ColorType.Solid, color: 'transparent' }, // Transparent to blend with container
                textColor: '#9ca3af',
                attributionLogo: false,
            },
            grid: {
                vertLines: { color: '#1f1f1f' },
                horzLines: { color: '#1f1f1f' },
            },
            crosshair: {
                mode: 1, // Magnet mode
                vertLine: {
                    color: '#6b7280',
                    width: 1,
                    style: 2,
                    labelBackgroundColor: '#1f1f1f',
                },
                horzLine: {
                    color: '#6b7280',
                    width: 1,
                    style: 2,
                    labelBackgroundColor: '#1f1f1f',
                },
            },
            rightPriceScale: {
                borderColor: '#1f1f1f',
                scaleMargins: {
                    top: 0.1,
                    bottom: 0.2, // Leave space for volume
                },
            },
            timeScale: {
                borderColor: '#1f1f1f',
                timeVisible: true,
                secondsVisible: false,
            },
        });

        chartRef.current = chart;

        // Candlestick series
        const candleSeries: ISeriesApi<'Candlestick'> = chart.addSeries(CandlestickSeries, {
            upColor: '#10b981',
            downColor: '#ef4444',
            borderUpColor: '#10b981',
            borderDownColor: '#ef4444',
            wickUpColor: '#10b981',
            wickDownColor: '#ef4444',
        });

        const candleData: LWCandlestickData<Time>[] = data.candlestick.map((c) => ({
            time: c.time as Time,
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close,
        }));
        candleSeries.setData(candleData);

        // Volume histogram (if available)
        if (data.volume && data.volume.length > 0) {
            const volumeSeries: ISeriesApi<'Histogram'> = chart.addSeries(HistogramSeries, {
                priceFormat: { type: 'volume' },
                priceScaleId: 'volume', // Set as separate scale/overlay
            });

            const volumeData = data.volume.map((v) => ({
                time: v.time as Time,
                value: v.value,
                color: v.color,
            }));
            volumeSeries.setData(volumeData);

            // Scale volume to bottom 20%
            chart.priceScale('volume').applyOptions({
                scaleMargins: { top: 0.8, bottom: 0 },
            });
        }

        // SMA 20 (blue)
        if (data.sma_20 && data.sma_20.length > 0) {
            const sma20: ISeriesApi<'Line'> = chart.addSeries(LineSeries, {
                color: '#3b82f6',
                lineWidth: 1,
                title: 'SMA 20',
                priceLineVisible: false,
                lastValueVisible: false,
            });
            sma20.setData(data.sma_20.map((d) => ({ time: d.time as Time, value: d.value })));
        }

        // SMA 50 (orange)
        if (data.sma_50 && data.sma_50.length > 0) {
            const sma50: ISeriesApi<'Line'> = chart.addSeries(LineSeries, {
                color: '#f59e0b',
                lineWidth: 1,
                title: 'SMA 50',
                priceLineVisible: false,
                lastValueVisible: false,
            });
            sma50.setData(data.sma_50.map((d) => ({ time: d.time as Time, value: d.value })));
        }

        // SMA 200 (purple)
        if (data.sma_200 && data.sma_200.length > 0) {
            const sma200: ISeriesApi<'Line'> = chart.addSeries(LineSeries, {
                color: '#a855f7',
                lineWidth: 1,
                title: 'SMA 200',
                priceLineVisible: false,
                lastValueVisible: false,
            });
            sma200.setData(data.sma_200.map((d) => ({ time: d.time as Time, value: d.value })));
        }

        chart.timeScale().fitContent();

        // Handle resize
        const handleResize = () => {
            if (containerRef.current && chartRef.current) {
                chartRef.current.applyOptions({ width: containerRef.current.clientWidth });
            }
        };
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
            chartRef.current = null;
        };
    }, [data, height]);

    return (
        <div style={{ position: 'relative', width: '100%', height: `${height}px` }}>
            <div
                ref={containerRef}
                style={{
                    width: '100%',
                    height: '100%',
                    borderRadius: '12px',
                    overflow: 'hidden',
                    backgroundColor: '#0d0d0d', // Match chart background
                }}
            />

            {/* Loading Overlay */}
            {loading && (
                <div style={{
                    position: 'absolute',
                    inset: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: 'rgba(13, 13, 13, 0.8)',
                    zIndex: 10,
                    borderRadius: '12px',
                }}>
                    <div style={{ textAlign: 'center', color: '#6b7280' }}>
                        Loading chart data...
                    </div>
                </div>
            )}

            {/* Error Overlay */}
            {!loading && error && (
                <div style={{
                    position: 'absolute',
                    inset: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: 'rgba(13, 13, 13, 0.9)',
                    zIndex: 10,
                    borderRadius: '12px',
                    color: '#ef4444',
                }}>
                    <div style={{ textAlign: 'center' }}>
                        {error}
                    </div>
                </div>
            )}
        </div>
    );
}

export default StockChart;
