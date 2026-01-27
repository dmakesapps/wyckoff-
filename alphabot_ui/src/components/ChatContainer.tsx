"use client";

import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChatMessage } from "./ui/chat-message";
import { TextEffect } from "./ui/text-effect";
import PromptInputWithActions from "./PromptInputWithActions";
import MarketFeed from "./MarketFeed";
import FuturesBlock from "./FuturesBlock";
import { useChat } from "../hooks/useChat";

export function ChatContainer() {
    const {
        messages,
        isLoading,
        isStreaming,
        streamingContent,
        error,
        sendMessage,
        toolCalls,
        statusMessage,
    } = useChat();

    const messagesEndRef = useRef<HTMLDivElement>(null);

    const hasMessages = messages.length > 0 || isStreaming;

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, streamingContent, toolCalls]);

    const handleSendMessage = (content: string) => {
        if (!content.trim()) return;
        sendMessage(content);
    };

    return (
        <div className={`chat-container ${hasMessages ? "chat-container-active" : ""}`}>
            <AnimatePresence mode="wait">
                {!hasMessages ? (
                    <motion.div
                        key="welcome"
                        initial={{ opacity: 1 }}
                        exit={{ opacity: 0, y: -50 }}
                        transition={{ duration: 0.3 }}
                        className="welcome-wrapper"
                    >
                        <div className="welcome-left">
                            <div className="welcome-container">
                                <TextEffect per="word" preset="fade" as="h1" className="title">
                                    Welcome to alphabot
                                </TextEffect>
                            </div>
                            <motion.div
                                layout
                                className="input-container"
                            >
                                <PromptInputWithActions onSend={handleSendMessage} disabled={isLoading} />
                            </motion.div>
                        </div>
                        <div className="welcome-right">
                            <MarketFeed />
                            <FuturesBlock />
                        </div>
                    </motion.div>
                ) : (
                    <motion.div
                        key="messages"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.3 }}
                        className="messages-container"
                        style={{ paddingBottom: '10rem' }}
                    >
                        {messages.map((msg, i) => (
                            <ChatMessage
                                key={i}
                                id={i.toString()}
                                role={msg.role as "user" | "assistant"} // Cast strictly if needed
                                content={msg.content}
                            />
                        ))}

                        {/* Status / Tool Indicator */}
                        {isLoading && statusMessage && (
                            <div className="status-indicator">
                                <div className="thinking-indicator-mini" />
                                <span>{statusMessage}</span>
                            </div>
                        )}


                        {/* Streaming Message */}
                        {isStreaming && streamingContent && (
                            <ChatMessage
                                id="streaming"
                                role="assistant"
                                content={streamingContent}
                                isStreaming={true}
                            />
                        )}

                        {/* Loading Indicator (before first token) */}
                        {isLoading && !streamingContent && toolCalls.length === 0 && (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="typing-indicator"
                            >
                                <span className="typing-dot" />
                                <span className="typing-dot" />
                                <span className="typing-dot" />
                            </motion.div>
                        )}

                        {/* Error Message */}
                        {error && (
                            <div style={{ color: '#ef4444', padding: '1rem', textAlign: 'center' }}>
                                Error: {error}
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </motion.div>
                )}
            </AnimatePresence>

            {hasMessages && (
                <motion.div
                    layout
                    className="input-container input-container-bottom relative z-10"
                >
                    <div className="absolute -top-24 left-0 right-0 h-24 bg-gradient-to-t from-[var(--bg)] via-[var(--bg)]/80 to-transparent pointer-events-none" />
                    <PromptInputWithActions onSend={handleSendMessage} disabled={isLoading} />
                </motion.div>
            )}
        </div>
    );
}

