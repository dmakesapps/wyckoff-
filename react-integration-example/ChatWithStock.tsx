// src/components/ChatWithStock.tsx
// Chat component that can analyze stocks on demand

import React, { useState, useRef, useEffect } from 'react';
import { analyzeStock, StockAnalysis } from '../api/alphaApi';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  stockData?: StockAnalysis;
}

export function ChatWithStock() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I can analyze any stock for you. Just type a symbol like "AAPL" or ask me to "analyze TSLA".',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Extract stock symbol from user message
  const extractSymbol = (text: string): string | null => {
    // Common patterns: "AAPL", "analyze TSLA", "what about NVDA", etc.
    const patterns = [
      /\b([A-Z]{1,5})\b/,  // Direct symbol (1-5 uppercase letters)
      /analyze\s+([A-Za-z]{1,5})/i,
      /look at\s+([A-Za-z]{1,5})/i,
      /check\s+([A-Za-z]{1,5})/i,
    ];

    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) {
        return match[1].toUpperCase();
      }
    }
    return null;
  };

  // Format stock analysis as chat message
  const formatAnalysis = (data: StockAnalysis): string => {
    const { quote, alpha_score, ai_analysis, volume_metrics } = data;
    
    let response = `## ${data.company_name} (${data.symbol})\n\n`;
    response += `**Price:** $${quote.price.toFixed(2)} (${quote.change_percent >= 0 ? '+' : ''}${quote.change_percent.toFixed(2)}%)\n\n`;
    
    // Alpha Score
    response += `### Alpha Score: ${alpha_score.total_score} (${alpha_score.signal_strength})\n`;
    response += `Grade: **${alpha_score.overall_grade}** | `;
    response += `Momentum: ${alpha_score.momentum_grade} | `;
    response += `Trend: ${alpha_score.trend_grade} | `;
    response += `R/R: ${alpha_score.risk_reward_grade}\n\n`;
    
    // Top signals
    response += `### Key Signals\n`;
    alpha_score.signals.slice(0, 4).forEach((s) => {
      const icon = s.type === 'bullish' ? '🟢' : s.type === 'bearish' ? '🔴' : '⚪';
      response += `${icon} **${s.name}**: ${s.description}\n`;
    });
    response += '\n';
    
    // Volume
    response += `### Volume\n`;
    response += `RVOL: ${volume_metrics.relative_volume}x (${volume_metrics.relative_volume_label}) | `;
    response += `Flow: ${volume_metrics.accumulation_distribution}\n\n`;
    
    // AI Analysis
    if (ai_analysis) {
      response += `### AI Analysis\n`;
      response += `**${ai_analysis.sentiment.toUpperCase()}** (${ai_analysis.confidence}% confidence)\n\n`;
      response += `${ai_analysis.summary}\n\n`;
      
      if (ai_analysis.price_targets) {
        response += `Support: $${ai_analysis.price_targets.support} | Resistance: $${ai_analysis.price_targets.resistance}\n\n`;
      }
      
      response += `**Recommendation:** ${ai_analysis.recommendation}`;
    }
    
    return response;
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    // Try to extract a stock symbol
    const symbol = extractSymbol(input);

    if (symbol) {
      try {
        const stockData = await analyzeStock(symbol);
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: formatAnalysis(stockData),
          stockData,
        };
        
        setMessages((prev) => [...prev, assistantMessage]);
      } catch (error) {
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `Sorry, I couldn't find data for "${symbol}". Please check the symbol and try again.`,
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    } else {
      // No symbol detected
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I couldn't identify a stock symbol in your message. Try typing a symbol like \"AAPL\" or \"analyze TSLA\".",
      };
      setMessages((prev) => [...prev, assistantMessage]);
    }

    setLoading(false);
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.role}`}>
            <div className="message-content">
              {/* Simple markdown-like rendering */}
              {msg.content.split('\n').map((line, i) => {
                if (line.startsWith('## ')) {
                  return <h2 key={i}>{line.slice(3)}</h2>;
                }
                if (line.startsWith('### ')) {
                  return <h3 key={i}>{line.slice(4)}</h3>;
                }
                // Bold text
                const formatted = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
                return <p key={i} dangerouslySetInnerHTML={{ __html: formatted }} />;
              })}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <div className="message-content loading">Analyzing...</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type a stock symbol or ask to analyze..."
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}


