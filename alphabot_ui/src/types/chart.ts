// types/chart.ts - Types for Lightweight Charts integration

export interface ChartData {
    symbol: string;
    interval: string;
    dataPoints: number;
    candlestick: CandlestickData[];
    volume?: VolumeData[];
    sma_20?: LineData[];
    sma_50?: LineData[];
    sma_200?: LineData[];
    rsi?: LineData[];
    meta: ChartMeta;
}

export interface CandlestickData {
    time: string;        // "YYYY-MM-DD" for daily, Unix timestamp for intraday
    open: number;
    high: number;
    low: number;
    close: number;
}

export interface VolumeData {
    time: string;
    value: number;
    color: string;       // "#26a69a" green or "#ef5350" red
}

export interface LineData {
    time: string;
    value: number;
}

export interface ChartMeta {
    firstDate: string;
    lastDate: string;
    lastPrice: number;
    lastVolume: number | null;
    periodPreviousClose?: number; // Previous close before the start of the period
    periodChange?: number; // Pre-calculated percentage change
}

export interface ChartConfig {
    indicators: IndicatorInfo[];
    intervals: string[];
    periods: string[];
}

export interface IndicatorInfo {
    id: string;          // "sma_20", "rsi", etc.
    name: string;        // "SMA 20", "RSI 14"
    type: "overlay" | "separate";
    color: string;
}

// For Kimi chat responses - parse chart references
export interface KimiChartReference {
    symbol: string;
    interval: string;
    period: string;
    indicators: string[];
}
