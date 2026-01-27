// components/ChatChart.tsx - Inline chart for chat messages

import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createChart, ColorType, CandlestickSeries, HistogramSeries, LineSeries } from 'lightweight-charts';
import type { IChartApi, ISeriesApi, Time, CandlestickData as LWCandlestickData } from 'lightweight-charts';
import { fetchChartData } from '../api/chartApi';
import type { ChartData } from '../types/chart';

interface ChatChartProps {
    symbol: string;
    interval?: string;
    period?: string;
    indicators?: string[];
}

export function ChatChart({
    symbol,
    interval = '1d',
    period = '3mo',
    indicators = ['sma_20', 'sma_50', 'volume'],
}: ChatChartProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const [data, setData] = useState<ChartData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const navigate = useNavigate();

    useEffect(() => {
        let mounted = true;
        setLoading(true);
        fetchChartData(symbol, interval, period, indicators)
            .then(d => {
                if (mounted) {
                    setData(d);
                    setLoading(false);
                }
            })
            .catch(err => {
                if (mounted) {
                    setError(err.message);
                    setLoading(false);
                }
            });
        return () => { mounted = false; };
    }, [symbol, interval, period, indicators.join(',')]);

    useEffect(() => {
        if (!containerRef.current || !data || data.candlestick.length === 0) return;

        if (chartRef.current) {
            chartRef.current.remove();
            chartRef.current = null;
        }

        const chart = createChart(containerRef.current, {
            width: containerRef.current.clientWidth,
            height: 300,
            layout: {
                background: { type: ColorType.Solid, color: '#111827' }, // Dark bg matching chat
                textColor: '#9ca3af',
                attributionLogo: false,
            },
            grid: {
                vertLines: { color: '#1f2937', style: 2 },
                horzLines: { color: '#1f2937', style: 2 },
            },
            rightPriceScale: {
                borderColor: '#374151',
            },
            timeScale: {
                borderColor: '#374151',
                timeVisible: true,
            },
            handleScroll: false,
            handleScale: false,
        });

        chartRef.current = chart;

        // Candlesticks
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

        // Indicators
        if (data.sma_20 && indicators.includes('sma_20')) {
            const line = chart.addSeries(LineSeries, { color: '#3b82f6', lineWidth: 1, title: 'SMA 20' });
            line.setData(data.sma_20.map(d => ({ time: d.time as Time, value: d.value })));
        }
        if (data.sma_50 && indicators.includes('sma_50')) {
            const line = chart.addSeries(LineSeries, { color: '#f59e0b', lineWidth: 1, title: 'SMA 50' });
            line.setData(data.sma_50.map(d => ({ time: d.time as Time, value: d.value })));
        }
        if (data.sma_200 && indicators.includes('sma_200')) {
            const line = chart.addSeries(LineSeries, { color: '#a855f7', lineWidth: 1, title: 'SMA 200' });
            line.setData(data.sma_200.map(d => ({ time: d.time as Time, value: d.value })));
        }

        // Volume
        if (data.volume && indicators.includes('volume')) {
            const volSeries = chart.addSeries(HistogramSeries, {
                priceFormat: { type: 'volume' },
                priceScaleId: 'volume',
            });
            chart.priceScale('volume').applyOptions({
                scaleMargins: { top: 0.8, bottom: 0 },
            });
            volSeries.setData(data.volume.map(v => ({
                time: v.time as Time,
                value: v.value,
                color: v.color,
            })));
        }

        chart.timeScale().fitContent();

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
    }, [data]);

    const handleChartClick = () => {
        navigate(`/chart/${encodeURIComponent(symbol)}`);
    };

    if (loading) return <div className="p-4 text-center text-gray-500 animate-pulse bg-gray-900/50 rounded-lg h-[300px] flex items-center justify-center">Loading chart data...</div>;
    if (error) return <div className="p-4 text-center text-red-400 bg-red-900/20 rounded-lg h-[300px] flex items-center justify-center">Failed to load chart</div>;

    return (
        <div
            className="my-4 border border-gray-800 rounded-lg overflow-hidden bg-[#111827] cursor-pointer hover:border-accent transition-colors duration-200 group relative"
            onClick={handleChartClick}
            title={`View full chart for ${symbol}`}
        >
            <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-gray-800/80 px-2 py-1 rounded text-xs text-white z-10 pointer-events-none">
                Click to expand
            </div>
            <div className="px-4 py-2 bg-gray-900/50 border-b border-gray-800 flex justify-between items-center group-hover:bg-gray-800/50 transition-colors">
                <span className="font-semibold text-gray-200">{symbol}</span>
                <span className="text-xs text-gray-500">{interval} • {period}</span>
            </div>
            <div ref={containerRef} className="w-full h-[300px]" />
        </div>
    );
}
