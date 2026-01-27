import { createContext, useContext, type ReactNode } from 'react';
import { useChatImpl, type UseChatReturn } from '../hooks/useChatImpl';

const ChatContext = createContext<UseChatReturn | null>(null);

export function ChatProvider({ children }: { children: ReactNode }) {
    const chatState = useChatImpl();

    return (
        <ChatContext.Provider value={chatState}>
            {children}
        </ChatContext.Provider>
    );
}

export function useChatContext() {
    const context = useContext(ChatContext);
    if (!context) {
        throw new Error('useChatContext must be used within a ChatProvider');
    }
    return context;
}
