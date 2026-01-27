import type {
    ChatMessage,
    ChatStreamChunk,
    ChatResponse,
    PositionsResponse,
    MarketNewsResponse,
    StockNewsResponse,
    Quote,
    StockAnalysis,
} from '../types/api';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// ═══════════════════════════════════════════════════════════════
// CHAT API (STREAMING)
// ═══════════════════════════════════════════════════════════════

/**
 * Stream chat response from the API
 * 
 * @param messages - Conversation history
 * @param onChunk - Callback for each streamed chunk
 * @param onComplete - Callback when stream is complete
 * @param onError - Callback for errors
 */
export async function streamChat(
    messages: ChatMessage[],
    onChunk: (chunk: ChatStreamChunk) => void,
    onComplete: (fullResponse: string) => void,
    onError: (error: string) => void
): Promise<void> {
    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ messages, stream: true }),
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
            throw new Error('No response body');
        }

        const decoder = new TextDecoder();
        let fullResponse = '';

        let lineBuffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const text = decoder.decode(value, { stream: true });
            lineBuffer += text;

            const lines = lineBuffer.split('\n');
            // Keep the last partial line (if any) in the buffer
            lineBuffer = lines.pop() || '';

            for (const line of lines) {
                const trimmedLine = line.trim();
                if (!trimmedLine || !trimmedLine.startsWith('data: ')) continue;

                try {
                    const jsonStr = line.slice(6);
                    if (jsonStr.trim() === '[DONE]') {
                        // Handle legacy [DONE] if backend sends it, though checks say "done" event
                        onChunk({ type: 'done', content: fullResponse });
                        onComplete(fullResponse);
                        return;
                    }

                    const event: any = JSON.parse(jsonStr);

                    // Map backend event types to ChatStreamChunk
                    // Backend: thinking, tool_call, tool_result, text, done, error
                    // Frontend Type: text, tool_call, tool_result, error, done

                    if (event.type === 'text') {
                        fullResponse += (event.content || '');
                        onChunk({ type: 'text', content: event.content });
                    }
                    else if (event.type === 'thinking') {
                        // Pass through as thinking type, content is the status message
                        onChunk({ type: 'thinking', content: event.content });
                    }
                    else if (event.type === 'tool_call') {
                        onChunk({ type: 'tool_call', name: event.name || 'Unknown Tool' });
                    }
                    else if (event.type === 'tool_result') {
                        onChunk({ type: 'tool_result', name: event.name || 'Unknown Tool', result: event.result });
                    }
                    else if (event.type === 'error') {
                        onError(event.content || 'Unknown error');
                        return;
                    }
                    else if (event.type === 'done') {
                        onComplete(fullResponse);
                        return;
                    }
                } catch (e) {
                    console.warn('Malformed JSON chunk:', line);
                }
            }
        }

        onComplete(fullResponse);
    } catch (error) {
        onError(error instanceof Error ? error.message : 'Chat failed');
    }
}

/**
 * Non-streaming chat (simpler but no real-time updates)
 */
export async function chat(messages: ChatMessage[]): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages, stream: false }),
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
}

// ═══════════════════════════════════════════════════════════════
// POSITIONS API
// ═══════════════════════════════════════════════════════════════

export async function getPositions(): Promise<PositionsResponse> {
    const response = await fetch(`${API_BASE}/positions`);
    if (!response.ok) throw new Error('Failed to fetch positions');
    return response.json();
}

// ═══════════════════════════════════════════════════════════════
// NEWS API
// ═══════════════════════════════════════════════════════════════

export async function getMarketNews(limit = 15): Promise<MarketNewsResponse> {
    const response = await fetch(`${API_BASE}/market/news?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch market news');
    return response.json();
}

export async function getStockNews(symbol: string, limit = 10): Promise<StockNewsResponse> {
    const response = await fetch(`${API_BASE}/news/${symbol.toUpperCase()}?limit=${limit}`);
    if (!response.ok) throw new Error(`Failed to fetch news for ${symbol}`);
    return response.json();
}

// ═══════════════════════════════════════════════════════════════
// STOCK API
// ═══════════════════════════════════════════════════════════════

export async function getQuote(symbol: string): Promise<Quote> {
    const response = await fetch(`${API_BASE}/quote/${symbol.toUpperCase()}`);
    if (!response.ok) throw new Error(`Failed to fetch quote for ${symbol}`);
    return response.json();
}

export async function analyzeStock(symbol: string): Promise<StockAnalysis> {
    const response = await fetch(`${API_BASE}/analyze/${symbol.toUpperCase()}`);
    if (!response.ok) throw new Error(`Failed to analyze ${symbol}`);
    return response.json();
}

// ═══════════════════════════════════════════════════════════════
// HEALTH CHECK
// ═══════════════════════════════════════════════════════════════

export async function checkHealth(): Promise<boolean> {
    try {
        const response = await fetch(`${API_BASE}/health`);
        return response.ok;
    } catch {
        return false;
    }
}
