"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { fetchMarketPulse, type PulseUpdate } from "../api/marketPulse";
import {
    TrendingUp,
    Bitcoin,
    Landmark,
    BarChart3,
    Cpu,
    Gem
} from "lucide-react";

// Category icons using Lucide
const categoryIcons: Record<string, React.ReactNode> = {
    Markets: <TrendingUp size={14} />,
    Crypto: <Bitcoin size={14} />,
    Economy: <Landmark size={14} />,
    Earnings: <BarChart3 size={14} />,
    Tech: <Cpu size={14} />,
    Commodities: <Gem size={14} />,
};

// Sentiment colors
const sentimentColors: Record<string, string> = {
    positive: "#22c55e", // Green
    negative: "#ef4444", // Red
    neutral: "#9ca3af",  // Gray
};

// Fallback data in case API fails
const fallbackUpdates: PulseUpdate[] = [
    { category: "Markets", headline: "Loading market data", sentiment: "neutral" },
    { category: "Crypto", headline: "Loading crypto prices", sentiment: "neutral" },
    { category: "Economy", headline: "Loading economic data", sentiment: "neutral" },
];

export function MarketFeed() {
    const [updates, setUpdates] = useState<PulseUpdate[]>(() => {
        const cached = localStorage.getItem("marketQuotes_feed");
        if (cached) {
            try {
                const parsed = JSON.parse(cached);
                return parsed.updates || fallbackUpdates;
            } catch (e) {
                return fallbackUpdates;
            }
        }
        return fallbackUpdates;
    });

    const [generatedAt, setGeneratedAt] = useState<string | null>(() => {
        const cached = localStorage.getItem("marketQuotes_feed");
        if (cached) {
            try {
                const parsed = JSON.parse(cached);
                return parsed.generated_at || null;
            } catch (e) {
                return null;
            }
        }
        return null;
    });

    const [currentIndex, setCurrentIndex] = useState(0);

    // Fetch market pulse on mount and every 60 seconds
    useEffect(() => {
        let mounted = true;

        const loadPulse = async () => {
            try {
                const data = await fetchMarketPulse();
                if (mounted && data.updates && data.updates.length > 0) {
                    setUpdates(data.updates);
                    setGeneratedAt(data.generated_at);

                    // Cache to localStorage
                    localStorage.setItem("marketQuotes_feed", JSON.stringify(data));
                }
            } catch (error) {
                console.error("Failed to fetch market pulse:", error);
            }
        };

        loadPulse();
        const interval = setInterval(loadPulse, 60000); // Refresh every 60 seconds

        return () => {
            mounted = false;
            clearInterval(interval);
        };
    }, []);

    // Auto-rotate through updates
    useEffect(() => {
        if (updates.length === 0) return;

        const interval = setInterval(() => {
            setCurrentIndex((prev) => (prev + 1) % updates.length);
        }, 4000);

        return () => clearInterval(interval);
    }, [updates.length]);

    const currentUpdate = updates[currentIndex];

    return (
        <div className="market-feed">
            <h3 className="market-feed-title">What's happening today</h3>

            <div className="market-feed-content">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={currentIndex}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ duration: 0.5, ease: "easeOut" }}
                        className="market-topic"
                    >
                        <div className="market-category" style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            color: sentimentColors[currentUpdate.sentiment]
                        }}>
                            {categoryIcons[currentUpdate.category]}
                            <span>{currentUpdate.category}</span>
                        </div>
                        <p
                            className="market-headline"
                            style={{ color: sentimentColors[currentUpdate.sentiment] }}
                        >
                            {currentUpdate.headline}
                        </p>
                    </motion.div>
                </AnimatePresence>
            </div>

            <div className="market-feed-dots">
                {updates.map((update, index) => (
                    <button
                        key={index}
                        className={`market-dot ${index === currentIndex ? "market-dot-active" : ""}`}
                        onClick={() => setCurrentIndex(index)}
                        aria-label={`Go to ${update.category} update`}
                        style={{
                            backgroundColor: index === currentIndex
                                ? sentimentColors[update.sentiment]
                                : undefined
                        }}
                    />
                ))}
            </div>

            {generatedAt && (
                <div className="market-feed-timestamp" style={{
                    fontSize: '0.65rem',
                    color: '#6b7280',
                    textAlign: 'center',
                    marginTop: '0.75rem',
                    opacity: 0.7
                }}>
                    Updated {new Date(generatedAt).toLocaleTimeString()}
                </div>
            )}
        </div>
    );
}

export default MarketFeed;
