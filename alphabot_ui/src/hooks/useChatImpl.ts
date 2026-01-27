import { useState, useCallback, useEffect, useRef } from 'react';
import { streamChat } from '../api/alphaApi';
import type { ChatMessage, ChatStreamChunk } from '../types/api';

// Generate a unique ID for each chat
function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

export interface ChatSession {
    id: string;
    title: string;
    messages: ChatMessage[];
    createdAt: number;
    updatedAt: number;
}

export interface UseChatReturn {
    // Current chat
    messages: ChatMessage[];
    currentChatId: string | null;
    isLoading: boolean;
    isStreaming: boolean;
    streamingContent: string;
    error: string | null;
    sendMessage: (content: string) => Promise<void>;
    toolCalls: Array<{ name: string; result?: any }>;
    statusMessage: string | null;

    // Chat history management
    chatHistory: ChatSession[];
    startNewChat: () => void;
    loadChat: (chatId: string) => void;
    deleteChat: (chatId: string) => void;
}

const STORAGE_KEY = 'alphabot_chat_sessions';
const CURRENT_CHAT_KEY = 'alphabot_current_chat_id';

function loadChatSessions(): ChatSession[] {
    try {
        const saved = localStorage.getItem(STORAGE_KEY);
        return saved ? JSON.parse(saved) : [];
    } catch (e) {
        console.error('Failed to load chat sessions:', e);
        return [];
    }
}

function saveChatSessions(sessions: ChatSession[]) {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
    } catch (e) {
        console.error('Failed to save chat sessions:', e);
    }
}

function generateChatTitle(messages: ChatMessage[]): string {
    // Use the first user message as the title, truncated
    const firstUserMessage = messages.find(m => m.role === 'user');
    if (firstUserMessage) {
        const title = firstUserMessage.content.slice(0, 40);
        return title.length < firstUserMessage.content.length ? title + '...' : title;
    }
    return 'New Chat';
}

export function useChatImpl(): UseChatReturn {
    const [chatHistory, setChatHistory] = useState<ChatSession[]>(() => loadChatSessions());
    const [currentChatId, setCurrentChatId] = useState<string | null>(() => {
        try {
            return localStorage.getItem(CURRENT_CHAT_KEY);
        } catch {
            return null;
        }
    });

    const [messages, setMessages] = useState<ChatMessage[]>(() => {
        if (currentChatId) {
            const session = loadChatSessions().find(s => s.id === currentChatId);
            return session?.messages || [];
        }
        return [];
    });

    const [isLoading, setIsLoading] = useState(false);
    const [isStreaming, setIsStreaming] = useState(false);
    const [streamingContent, setStreamingContent] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [statusMessage, setStatusMessage] = useState<string | null>(null);
    const [toolCalls, setToolCalls] = useState<Array<{ name: string; result?: any }>>([]);

    // Keep a ref to current chat ID to avoid stale closures
    const currentChatIdRef = useRef(currentChatId);
    useEffect(() => {
        currentChatIdRef.current = currentChatId;
    }, [currentChatId]);

    // Persist current chat ID
    useEffect(() => {
        try {
            if (currentChatId) {
                localStorage.setItem(CURRENT_CHAT_KEY, currentChatId);
            } else {
                localStorage.removeItem(CURRENT_CHAT_KEY);
            }
        } catch (e) {
            console.error('Failed to save current chat ID:', e);
        }
    }, [currentChatId]);

    // Save chat history whenever it changes
    useEffect(() => {
        saveChatSessions(chatHistory);
    }, [chatHistory]);

    // Update the current chat session when messages change
    useEffect(() => {
        if (currentChatId && messages.length > 0) {
            setChatHistory(prev => {
                const existing = prev.find(s => s.id === currentChatId);
                if (existing) {
                    return prev.map(s =>
                        s.id === currentChatId
                            ? { ...s, messages, title: generateChatTitle(messages), updatedAt: Date.now() }
                            : s
                    );
                } else {
                    // New chat session
                    const newSession: ChatSession = {
                        id: currentChatId,
                        title: generateChatTitle(messages),
                        messages,
                        createdAt: Date.now(),
                        updatedAt: Date.now(),
                    };
                    return [newSession, ...prev];
                }
            });
        }
    }, [messages, currentChatId]);

    const startNewChat = useCallback(() => {
        const newId = generateId();
        setCurrentChatId(newId);
        setMessages([]);
        setStreamingContent('');
        setError(null);
        setToolCalls([]);
        setStatusMessage(null);
    }, []);

    const loadChat = useCallback((chatId: string) => {
        const session = chatHistory.find(s => s.id === chatId);
        if (session) {
            setCurrentChatId(chatId);
            setMessages(session.messages);
            setStreamingContent('');
            setError(null);
            setToolCalls([]);
            setStatusMessage(null);
        }
    }, [chatHistory]);

    const deleteChat = useCallback((chatId: string) => {
        setChatHistory(prev => prev.filter(s => s.id !== chatId));
        if (currentChatId === chatId) {
            startNewChat();
        }
    }, [currentChatId, startNewChat]);

    const sendMessage = useCallback(async (content: string) => {
        if (!content.trim() || isLoading) return;

        // Ensure we have a chat session
        let chatId = currentChatIdRef.current;
        if (!chatId) {
            chatId = generateId();
            setCurrentChatId(chatId);
            currentChatIdRef.current = chatId;
        }

        setError(null);
        setIsLoading(true);
        setIsStreaming(true);
        setStreamingContent('');
        setToolCalls([]);
        setStatusMessage('Thinking...');

        // Add user message
        const userMessage: ChatMessage = { role: 'user', content };
        const updatedMessages = [...messages, userMessage];
        setMessages(updatedMessages);

        // Keep track of stream content locally for pattern matching
        let streamBuffer = '';

        await streamChat(
            updatedMessages,
            // onChunk
            (chunk: ChatStreamChunk) => {
                if (chunk.type === 'text' && chunk.content) {
                    const text = chunk.content;
                    streamBuffer += text;
                    setStreamingContent(prev => prev + text);
                    // Clear status message when text starts appearing
                    setStatusMessage(null);

                    // Detect XML tool tags (e.g. <search_market>) to show loading indicator
                    // We look for the opening tag.
                    const toolMatch = streamBuffer.match(/<([a-z_]+)>/g);
                    if (toolMatch) {
                        const uniqueTools = new Set(toolMatch.map(t => t.replace(/[<>]/g, '')));
                        setToolCalls(prev => {
                            const newTools = [...prev];
                            uniqueTools.forEach(name => {
                                if (!newTools.some(t => t.name === name)) {
                                    newTools.push({ name });
                                }
                            });
                            return newTools;
                        });
                    }
                } else if (chunk.type === 'thinking') {
                    setStatusMessage(chunk.content || 'Thinking...');
                } else if (chunk.type === 'tool_call') {
                    const name = chunk.name || 'unknown';
                    setStatusMessage(`Running: ${name}...`);
                    setToolCalls(prev => {
                        if (prev.some(t => t.name === chunk.name)) return prev;
                        return [...prev, { name }];
                    });
                } else if (chunk.type === 'tool_result') {
                    // Optionally update status to 'Processing result...' or keep previous
                    setToolCalls(prev =>
                        prev.map(tc =>
                            tc.name === chunk.name ? { ...tc, result: chunk.result } : tc
                        )
                    );
                }
            },
            // onComplete
            (fullResponse: string) => {
                const assistantMessage: ChatMessage = { role: 'assistant', content: fullResponse };
                setMessages(prev => [...prev, assistantMessage]);
                setStreamingContent('');
                setIsStreaming(false);
                setIsLoading(false);
                setToolCalls([]);
                setStatusMessage(null);
            },
            // onError
            (errorMessage: string) => {
                setError(errorMessage);
                setIsStreaming(false);
                setIsLoading(false);
                setToolCalls([]);
                setStatusMessage(null);
            }
        );
    }, [messages, isLoading]);

    return {
        messages,
        currentChatId,
        isLoading,
        isStreaming,
        streamingContent,
        error,
        sendMessage,
        toolCalls,
        statusMessage,
        chatHistory,
        startNewChat,
        loadChat,
        deleteChat,
    };
}
