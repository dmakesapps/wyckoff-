
import { motion } from "framer-motion";
import { Clock, ExternalLink, MessageCircle } from "lucide-react";
import type { NewsArticle } from "../types/api";

export function NewsCard({ news }: { news: NewsArticle }) {
    // Map API sentiment to UI styles
    const sentimentType = news.sentiment === 'positive' ? 'bullish' :
        news.sentiment === 'negative' ? 'bearish' : 'neutral';

    const sentimentColors = {
        bullish: "sentiment-bullish",
        bearish: "sentiment-bearish",
        neutral: "sentiment-neutral",
    };

    return (
        <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="news-card"
        >
            <div className={`news-sentiment-stripe ${sentimentColors[sentimentType]}`} />
            <div className="news-content">
                <div className="news-header-row">
                    <span className="news-category">{news.source}</span>
                    <span className={`news-sentiment ${sentimentColors[sentimentType]}`}>
                        {sentimentType.toUpperCase()}
                    </span>
                </div>
                <a href={news.url} target="_blank" rel="noopener noreferrer" className="news-headline-link hover:text-accent transition-colors">
                    <h3 className="news-headline">{news.title} <ExternalLink size={12} style={{ display: 'inline', marginLeft: '4px' }} /></h3>
                </a>
                <p className="news-summary">{news.summary || "No summary available."}</p>
                <div className="news-footer">
                    <span className="news-time">
                        <Clock size={12} />
                        {new Date(news.published_at).toLocaleString()}
                    </span>
                    <button className="news-action" title="Discuss">
                        <MessageCircle size={14} />
                    </button>
                </div>
            </div>
        </motion.div>
    );
}
