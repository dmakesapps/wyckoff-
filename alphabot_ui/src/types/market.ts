export interface Stock {
    symbol: string;
    company_name: string;
    price: number;
    change_percent: number;
    volume: number;
    relative_volume: number;
    market_cap: number;
    market_cap_category: string;
    sector: string;
    industry: string;
    week_52_high: number;
    week_52_low: number;
    distance_from_52w_high: number;
    distance_from_52w_low: number;
}

export interface RankedStock {
    rank: number;
    ticker: string;
    company: string;
    last: number;
    change: number;
    volume: number;
    relativeVolume: number;
    marketCap: number;
    sector: string;
    signal: string;
}

export interface SectorData {
    sector: string;
    stock_count: number;
    avg_change: number;
    percent_advancing: number;
    avg_rvol: number;
    total_volume: number;
    total_market_cap: number;
}

export interface MarketBreadth {
    advancing: number;
    declining: number;
    unchanged: number;
    total: number;
    advance_decline_ratio: number;
    advance_percent: number;
    decline_percent: number;
    new_highs: number;
    new_lows: number;
}

export interface Headline {
    id: number;
    title: string;
    source: string;
    url: string;
    published: string;
    sentiment: 'positive' | 'negative' | 'neutral';
    age: string;
}

export interface HeatmapStock {
    symbol: string;
    name: string;
    price: number;
    change: number;
    marketCap: number;
    capCategory: string;
    volume: number;
    rvol: number;
}

// Additional specific response interfaces
export interface SMAAnalysis {
    above: number;
    below: number;
    above_percent: number;
}

// NEW: Volume Analysis indicators (matches backend /api/market/indicators)
export interface VolumeAnalysis {
    up_volume: number;
    down_volume: number;
    volume_ratio: number;
    total_volume: number;
    unusual_volume_count: number;
    up_volume_percent: number;
}

// NEW: Momentum indicators (matches backend /api/market/indicators)
export interface Momentum {
    gainers_1pct: number;
    gainers_3pct: number;
    gainers_5pct: number;
    losers_1pct: number;
    losers_3pct: number;
    losers_5pct: number;
    net_gainers_1pct: number;
    net_gainers_3pct: number;
}

// NEW: Volatility indicators (matches backend /api/market/indicators)
export interface Volatility {
    big_movers_up: number;
    big_movers_down: number;
    total_big_movers: number;
    volatility_level: string;
}

// NEW: Fear & Greed Index
export interface FearGreed {
    score: number;
    label: string;
    color?: string;
    components?: {
        advance_decline: number;
        sma50_above: number;
        sma200_above: number;
        high_low_ratio: number;
        momentum_ratio: number;
    };
}

// Enhanced Sector data
export interface EnhancedSectorData extends SectorData {
    best_performer?: string;
    worst_performer?: string;
}

export interface MarketOverview {
    breadth: MarketBreadth & {
        advance_decline_ratio: number;
        advance_percent: number;
        decline_percent: number;
    };
    sectors: EnhancedSectorData[];
    sma_analysis: {
        sma50: SMAAnalysis;
        sma200: SMAAnalysis;
    };
    // NEW indicator categories
    volume_analysis?: VolumeAnalysis;
    momentum?: Momentum;
    volatility?: Volatility;
    fear_greed?: FearGreed;
    stats: {
        total_stocks: number;
        unusual_volume_count: number;
        near_52w_high_count: number;
        big_gainers_count: number;
        big_losers_count: number;
        last_scan: string;
    };
    top_gainers: Stock[];
    top_losers: Stock[];
    most_active: Stock[];
    unusual_volume: Stock[];
    updated_at: string;
}

export interface HeatmapResponse {
    sectors: {
        [sectorName: string]: {
            stocks: HeatmapStock[];
            avgChange: number;
            stockCount: number;
        }
    };
    sectorSummary: SectorData[];
    updated_at: string;
}

export interface HeadlinesResponse {
    headlines: Headline[];
    count: number;
    marketSentiment: "bullish" | "bearish" | "neutral";
    sentimentBreakdown: {
        positive: number;
        negative: number;
        neutral: number;
    };
    updated_at: string;
}
