"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Plus, TrendingUp, TrendingDown, Star } from "lucide-react";

interface WatchlistItem {
    id: string;
    ticker: string;
    name: string;
    price: number;
    change: number;
    changePercent: number;
}

interface Watchlist {
    id: string;
    name: string;
    items: WatchlistItem[];
}

// Placeholder watchlists data
const watchlists: Watchlist[] = [
    {
        id: "1",
        name: "Tech Giants",
        items: [
            { id: "1", ticker: "AAPL", name: "Apple Inc.", price: 198.25, change: -1.50, changePercent: -0.75 },
            { id: "2", ticker: "GOOGL", name: "Alphabet Inc.", price: 175.80, change: 3.20, changePercent: 1.85 },
            { id: "3", ticker: "META", name: "Meta Platforms", price: 585.50, change: 12.40, changePercent: 2.16 },
            { id: "4", ticker: "AMZN", name: "Amazon.com", price: 225.30, change: 4.10, changePercent: 1.85 },
        ],
    },
    {
        id: "2",
        name: "AI Plays",
        items: [
            { id: "5", ticker: "NVDA", name: "NVIDIA Corporation", price: 892.50, change: 23.40, changePercent: 2.69 },
            { id: "6", ticker: "AMD", name: "Advanced Micro Devices", price: 178.90, change: 5.60, changePercent: 3.23 },
            { id: "7", ticker: "PLTR", name: "Palantir Technologies", price: 24.80, change: 0.85, changePercent: 3.55 },
        ],
    },
    {
        id: "3",
        name: "Crypto",
        items: [
            { id: "8", ticker: "BTC", name: "Bitcoin", price: 105250.00, change: 2150.00, changePercent: 2.08 },
            { id: "9", ticker: "ETH", name: "Ethereum", price: 3450.00, change: -45.00, changePercent: -1.29 },
            { id: "10", ticker: "SOL", name: "Solana", price: 185.20, change: 8.90, changePercent: 5.05 },
        ],
    },
];

function WatchlistCard({ watchlist }: { watchlist: Watchlist }) {
    const [isExpanded, setIsExpanded] = useState(true);

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="watchlist-card"
        >
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="watchlist-header"
            >
                <div className="watchlist-title-row">
                    <Star size={16} className="watchlist-icon" />
                    <span className="watchlist-name">{watchlist.name}</span>
                    <span className="watchlist-count">{watchlist.items.length} items</span>
                </div>
            </button>

            {isExpanded && (
                <div className="watchlist-items">
                    <div className="watchlist-table-header">
                        <span>Ticker</span>
                        <span>Price</span>
                        <span>Change</span>
                    </div>
                    {watchlist.items.map((item) => {
                        const isPositive = item.change >= 0;
                        return (
                            <div key={item.id} className="watchlist-item">
                                <div className="watchlist-item-ticker">
                                    <span className="ticker">{item.ticker}</span>
                                    <span className="name">{item.name}</span>
                                </div>
                                <span className="watchlist-item-price">
                                    ${item.price.toLocaleString()}
                                </span>
                                <span className={`watchlist-item-change ${isPositive ? "positive" : "negative"}`}>
                                    {isPositive ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                                    {isPositive ? "+" : ""}{item.changePercent.toFixed(2)}%
                                </span>
                            </div>
                        );
                    })}
                </div>
            )}
        </motion.div>
    );
}

export function WatchlistsPage() {
    return (
        <div className="page-container">
            <div className="page-header">
                <h1 className="page-title">Watchlists</h1>
                <p className="page-subtitle">Track tickers you're interested in</p>
            </div>

            <button className="add-watchlist-btn">
                <Plus size={18} />
                <span>New Watchlist</span>
            </button>

            <div className="watchlists-container">
                {watchlists.map((watchlist) => (
                    <WatchlistCard key={watchlist.id} watchlist={watchlist} />
                ))}
            </div>
        </div>
    );
}

export default WatchlistsPage;
