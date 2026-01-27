
// ═══════════════════════════════════════════════════════════════
// CHAT TYPES
// ═══════════════════════════════════════════════════════════════

export interface ChatMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
}

export interface ChatStreamChunk {
    type: 'text' | 'tool_call' | 'tool_result' | 'done' | 'error' | 'thinking';
    content?: string;
    name?: string;
    arguments?: Record<string, any>;
    result?: Record<string, any>;
}

export interface ChatRequest {
    messages: ChatMessage[];
    stream?: boolean;
}

export interface ChatResponse {
    response: string;
    tools_used: string[];
    error?: string;
}

// ═══════════════════════════════════════════════════════════════
// POSITION TYPES
// ═══════════════════════════════════════════════════════════════

export interface Position {
    symbol: string;
    company_name: string;
    shares: number;
    avg_cost: number;
    current_price: number;
    current_value: number;
    cost_basis: number;
    gain_loss: number;
    gain_loss_percent: number;
    day_change: number;
    day_change_percent: number;
}

export interface PositionsSummary {
    total_value: number;
    total_cost: number;
    total_gain_loss: number;
    total_gain_loss_percent: number;
}

export interface PositionsResponse {
    positions: Position[];
    summary: PositionsSummary;
    updated_at: string;
}

// ═══════════════════════════════════════════════════════════════
// NEWS TYPES
// ═══════════════════════════════════════════════════════════════

export interface NewsArticle {
    id: number;
    title: string;
    source: string;
    url: string;
    published_at: string;
    sentiment: 'positive' | 'negative' | 'neutral';
    summary?: string;
}

export interface MarketNewsResponse {
    overall_sentiment: string;
    article_count: number;
    articles: NewsArticle[];
    fetched_at: string;
}

export interface StockNewsResponse {
    symbol: string;
    overall_sentiment: string;
    earnings_date?: string;
    catalysts: string[];
    article_count: number;
    articles: NewsArticle[];
}

// ═══════════════════════════════════════════════════════════════
// QUOTE & ANALYSIS TYPES
// ═══════════════════════════════════════════════════════════════

export interface Quote {
    symbol: string;
    price: number;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    previous_close: number;
    change: number;
    change_percent: number;
    timestamp: string;
}

export interface AlphaSignal {
    name: string;
    type: 'bullish' | 'bearish' | 'neutral';
    strength: number;
    description: string;
}

export interface AlphaScore {
    total_score: number;
    signal_strength: 'strong' | 'moderate' | 'weak';
    overall_grade: 'A' | 'B' | 'C' | 'D' | 'F';
    bullish_signals: number;
    bearish_signals: number;
    signals: AlphaSignal[];
    summary: string;
}

export interface AIAnalysis {
    summary: string;
    sentiment: 'bullish' | 'bearish' | 'neutral';
    confidence: number;
    thesis?: string;
    key_points: string[];
    catalysts: string[];
    risks: string[];
    projections?: {
        bull_case: { price: number; thesis: string };
        base_case: { price: number; thesis: string };
        bear_case: { price: number; thesis: string };
        timeframe: string;
    };
    price_targets?: {
        support: number;
        resistance: number;
    };
    recommendation: string;
    source_references?: Array<{
        num: number;
        source: string;
        title: string;
        url: string;
    }>;
}

export interface StockAnalysis {
    symbol: string;
    company_name: string;
    quote: Quote;
    alpha_score: AlphaScore;
    ai_analysis?: AIAnalysis;
    technicals: any;
    options?: any;
    news?: any;
    fundamentals?: any;
    analyzed_at: string;
}
