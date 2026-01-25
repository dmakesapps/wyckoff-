// src/components/StockSearch.tsx
// Stock search component with analysis display

import React, { useState, FormEvent } from 'react';
import { useStockAnalysis } from '../hooks/useStockAnalysis';

export function StockSearch() {
  const [symbol, setSymbol] = useState('');
  const { data, loading, error, analyze } = useStockAnalysis();

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (symbol.trim()) {
      analyze(symbol.trim());
    }
  };

  return (
    <div className="stock-search">
      {/* Search Form */}
      <form onSubmit={handleSubmit} className="search-form">
        <input
          type="text"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          placeholder="Enter stock symbol (e.g., AAPL)"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !symbol.trim()}>
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </form>

      {/* Error Display */}
      {error && <div className="error">{error}</div>}

      {/* Results */}
      {data && (
        <div className="analysis-results">
          {/* Header */}
          <div className="stock-header">
            <h2>{data.company_name} ({data.symbol})</h2>
            <div className="price">
              ${data.quote.price.toFixed(2)}
              <span className={data.quote.change_percent >= 0 ? 'green' : 'red'}>
                {data.quote.change_percent >= 0 ? '+' : ''}
                {data.quote.change_percent.toFixed(2)}%
              </span>
            </div>
          </div>

          {/* Alpha Score */}
          <div className="alpha-score">
            <h3>Alpha Score</h3>
            <div className="score-display">
              <span className="score">{data.alpha_score.total_score}</span>
              <span className="grade">Grade: {data.alpha_score.overall_grade}</span>
              <span className="strength">{data.alpha_score.signal_strength}</span>
            </div>
            <p className="summary">{data.alpha_score.summary}</p>
          </div>

          {/* Signals */}
          <div className="signals">
            <h3>Signals</h3>
            {data.alpha_score.signals.map((signal, i) => (
              <div key={i} className={`signal ${signal.type}`}>
                <span className="signal-icon">
                  {signal.type === 'bullish' ? '🟢' : signal.type === 'bearish' ? '🔴' : '⚪'}
                </span>
                <span className="signal-name">{signal.name}</span>
                <span className="signal-strength">{'★'.repeat(signal.strength)}</span>
                <p className="signal-desc">{signal.description}</p>
              </div>
            ))}
          </div>

          {/* Volume Metrics */}
          <div className="volume-metrics">
            <h3>Volume Analysis</h3>
            <div className="metrics-grid">
              <div className="metric">
                <label>RVOL</label>
                <span>{data.volume_metrics.relative_volume}x</span>
                <small>{data.volume_metrics.relative_volume_label}</small>
              </div>
              <div className="metric">
                <label>Trend</label>
                <span>{data.volume_metrics.volume_trend_5d}</span>
              </div>
              <div className="metric">
                <label>Dollar Volume</label>
                <span>{data.volume_metrics.dollar_volume_formatted}</span>
              </div>
              <div className="metric">
                <label>Flow</label>
                <span>{data.volume_metrics.accumulation_distribution}</span>
              </div>
            </div>
          </div>

          {/* AI Analysis */}
          {data.ai_analysis && (
            <div className="ai-analysis">
              <h3>AI Analysis (Kimi)</h3>
              <div className={`sentiment ${data.ai_analysis.sentiment}`}>
                {data.ai_analysis.sentiment.toUpperCase()} 
                ({data.ai_analysis.confidence}% confidence)
              </div>
              <p className="ai-summary">{data.ai_analysis.summary}</p>
              
              {data.ai_analysis.key_points.length > 0 && (
                <div className="key-points">
                  <h4>Key Points</h4>
                  <ul>
                    {data.ai_analysis.key_points.map((point, i) => (
                      <li key={i}>{point}</li>
                    ))}
                  </ul>
                </div>
              )}

              {data.ai_analysis.catalysts.length > 0 && (
                <div className="catalysts">
                  <h4>Catalysts</h4>
                  <ul>
                    {data.ai_analysis.catalysts.map((cat, i) => (
                      <li key={i}>{cat}</li>
                    ))}
                  </ul>
                </div>
              )}

              {data.ai_analysis.risks.length > 0 && (
                <div className="risks">
                  <h4>Risks</h4>
                  <ul>
                    {data.ai_analysis.risks.map((risk, i) => (
                      <li key={i}>{risk}</li>
                    ))}
                  </ul>
                </div>
              )}

              {data.ai_analysis.price_targets && (
                <div className="price-targets">
                  <span>Support: ${data.ai_analysis.price_targets.support}</span>
                  <span>Resistance: ${data.ai_analysis.price_targets.resistance}</span>
                </div>
              )}

              <div className="recommendation">
                <strong>Recommendation:</strong> {data.ai_analysis.recommendation}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}


