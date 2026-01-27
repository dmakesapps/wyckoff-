"use client";

import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, RefreshCw } from "lucide-react";
import { usePositions } from "../hooks/usePositions";
import type { Position } from "../types/api";

function PositionCard({ position }: { position: Position }) {
    const isPositive = position.day_change >= 0;
    const isPLPositive = position.gain_loss >= 0;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="position-card"
        >
            <div className="position-header">
                <div className="position-ticker-info">
                    <span className="position-ticker">{position.symbol}</span>
                    <span className="position-name">{position.company_name}</span>
                </div>
                <div className={`position-day-change ${isPositive ? "positive" : "negative"}`}>
                    {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                    <span>{isPositive ? "+" : ""}{position.day_change_percent.toFixed(2)}%</span>
                </div>
            </div>

            <div className="position-details">
                <div className="position-stat">
                    <span className="position-stat-label">Shares</span>
                    <span className="position-stat-value">{position.shares}</span>
                </div>
                <div className="position-stat">
                    <span className="position-stat-label">Avg Cost</span>
                    <span className="position-stat-value">${position.avg_cost.toLocaleString()}</span>
                </div>
                <div className="position-stat">
                    <span className="position-stat-label">Current</span>
                    <span className="position-stat-value">${position.current_price.toLocaleString()}</span>
                </div>
                <div className="position-stat">
                    <span className="position-stat-label">Value</span>
                    <span className="position-stat-value">${position.current_value.toLocaleString()}</span>
                </div>
            </div>

            <div className="position-footer">
                <div className={`position-pl ${isPLPositive ? "positive" : "negative"}`}>
                    <span className="position-pl-label">Total P&L</span>
                    <span className="position-pl-value">
                        {isPLPositive ? "+" : ""}${position.gain_loss.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                        <span className="position-pl-percent">
                            ({isPLPositive ? "+" : ""}{position.gain_loss_percent.toFixed(2)}%)
                        </span>
                    </span>
                </div>
            </div>
        </motion.div>
    );
}

export function PositionsPage() {
    const { data, isLoading, error, refresh } = usePositions(true);

    if (isLoading && !data) {
        return (
            <div className="page-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                <div className="animate-spin text-accent">Loading...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="page-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', flexDirection: 'column', gap: '1rem' }}>
                <div className="text-red-500">Error loading positions: {error}</div>
                <button onClick={refresh} className="bg-card-bg border border-card-border px-4 py-2 rounded hover:bg-white/5">Retry</button>
            </div>
        );
    }

    if (!data) return null;

    const { summary, positions } = data;
    const totalDayChange = positions.reduce((sum, p) => sum + (p.day_change * p.shares), 0);
    // Approximate day change percent for total portfolio if not provided, or calculate from totals
    const totalDayChangePercent = (totalDayChange / (summary.total_value - totalDayChange)) * 100;

    return (
        <div className="page-container">
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h1 className="page-title">My Positions</h1>
                    <p className="page-subtitle">Track your portfolio performance</p>
                </div>
                <button
                    onClick={refresh}
                    className="p-2 rounded hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
                    title="Refresh Prices"
                >
                    <RefreshCw size={20} />
                </button>
            </div>

            {/* Portfolio Summary */}
            <div className="portfolio-summary">
                <div className="summary-card">
                    <span className="summary-label">Total Value</span>
                    <span className="summary-value">${summary.total_value.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
                </div>
                <div className={`summary-card ${totalDayChange >= 0 ? "positive" : "negative"}`}>
                    <span className="summary-label">Today's Change</span>
                    <span className="summary-value">
                        {totalDayChange >= 0 ? "+" : ""}${totalDayChange.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                        <span className="summary-percent">({totalDayChange >= 0 ? "+" : ""}{totalDayChangePercent.toFixed(2)}%)</span>
                    </span>
                </div>
                <div className={`summary-card ${summary.total_gain_loss >= 0 ? "positive" : "negative"}`}>
                    <span className="summary-label">Total P&L</span>
                    <span className="summary-value">
                        {summary.total_gain_loss >= 0 ? "+" : ""}${summary.total_gain_loss.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                        <span className="summary-percent">({summary.total_gain_loss >= 0 ? "+" : ""}{summary.total_gain_loss_percent.toFixed(2)}%)</span>
                    </span>
                </div>
            </div>

            {/* Positions Grid */}
            <div className="positions-grid">
                {positions.map((position) => (
                    <PositionCard key={position.symbol} position={position} />
                ))}
            </div>

            <div className="text-xs text-gray-600 mt-4 text-center">
                Last updated: {new Date(data.updated_at).toLocaleTimeString()}
            </div>
        </div>
    );
}

export default PositionsPage;
