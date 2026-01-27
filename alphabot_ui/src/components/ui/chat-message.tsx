"use client";

import { motion } from "framer-motion";
import { MarkdownRenderer } from "./markdown-renderer";
import { parseKimiResponse } from "../../utils/parseKimiResponse";
import { ChatChart } from "../ChatChart";
import type { KimiChartReference } from "../../types/chart";

export interface ChatMessageProps {
    id: string;
    role: "user" | "assistant";
    content: string;
    isStreaming?: boolean;
}

export function ChatMessage({ role, content, isStreaming }: ChatMessageProps) {
    const isUser = role === "user";

    if (isUser) {
        return (
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, ease: "easeOut" }}
                className="chat-message chat-message-user"
            >
                <div className="chat-message-content">
                    <p>{content}</p>
                </div>
            </motion.div>
        );
    }

    // Parse content for charts
    const { parts } = parseKimiResponse(content);

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="chat-message-assistant-container w-full py-4"
        >
            <div className="text-base leading-relaxed text-gray-200 w-full">
                {parts.map((part, index) => {
                    if (part.type === 'text') {
                        // Only show streaming cursor on the last text part if streaming
                        const isLastPart = index === parts.length - 1;
                        return (
                            <div key={index}>
                                <MarkdownRenderer content={part.content as string} isStreaming={isStreaming && isLastPart} />
                                {isStreaming && isLastPart && <span className="streaming-cursor inline-block w-2 h-4 ml-1 bg-emerald-500 animate-pulse mt-1" />}
                            </div>
                        );
                    } else if (part.type === 'chart') {
                        const chartRef = part.content as KimiChartReference;
                        return (
                            <div key={index} className="w-full max-w-3xl">
                                <ChatChart
                                    symbol={chartRef.symbol}
                                    interval={chartRef.interval}
                                    period={chartRef.period}
                                    indicators={chartRef.indicators}
                                />
                            </div>
                        );
                    }
                    return null;
                })}
                {/* Fallback cursor if empty parts (start) */}
                {isStreaming && parts.length === 0 && <span className="streaming-cursor inline-block w-2 h-4 ml-1 bg-emerald-500 animate-pulse mt-1" />}
            </div>
        </motion.div>
    );
}

export default ChatMessage;
