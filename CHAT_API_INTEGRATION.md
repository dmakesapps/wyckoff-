# Chat API Integration Guide

## Endpoint

```
POST /api/chat
```

**Base URL:** `http://localhost:8000`

---

## Request Format

```typescript
interface ChatRequest {
  messages: Array<{
    role: "user" | "assistant";
    content: string;
  }>;
  stream?: boolean; // Default: true
}
```

**Example:**
```json
{
  "messages": [
    {"role": "user", "content": "Find me 5 microcap stocks with unusual volume"}
  ],
  "stream": true
}
```

---

## Response: Server-Sent Events (SSE)

The endpoint streams responses as SSE events. Each event is a JSON object with a `type` field.

### Event Types

| Type | Description | When it appears |
|------|-------------|-----------------|
| `thinking` | Bot is processing/searching | During tool execution |
| `tool_call` | Tool being executed | When fetching data |
| `tool_result` | Tool returned data | After tool completes |
| `text` | Actual response content | Final answer streaming |
| `done` | Stream complete | End of response |
| `error` | Something went wrong | On errors |

### Event Flow (Silent Execution Pattern)

The model executes tools **silently** - no "Let me search..." text. The UI shows the loading state.

```
User sends message
    ↓
[tool_call] {name, arguments}      ← UI shows "Running: search_market"
    ↓
[tool_result] {name, result}       ← UI shows "Completed" (optional)
    ↓
[text] "Here are 5 microcap..."    ← Final answer streams
[text] "stocks showing unusual..."
[text] "| Ticker | Price |..."     ← Markdown table
    ↓
[done] {content: "full response"}  ← Complete
```

**Key Point**: There should be NO text before `tool_call`. The model goes straight to executing the tool.

---

## TypeScript Types

```typescript
// SSE Event Types
type ChatEventType = 
  | "thinking" 
  | "tool_call" 
  | "tool_result" 
  | "text" 
  | "done" 
  | "error";

interface ChatEvent {
  type: ChatEventType;
  content?: string;           // For thinking, text, done, error
  name?: string;              // For tool_call, tool_result
  arguments?: Record<string, any>;  // For tool_call
  result?: Record<string, any>;     // For tool_result
}

// Message format
interface Message {
  role: "user" | "assistant";
  content: string;
}
```

---

## React Implementation

### API Client

```typescript
// api/chat.ts

export async function* streamChat(
  messages: Message[]
): AsyncGenerator<ChatEvent> {
  const response = await fetch("http://localhost:8000/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, stream: true }),
  });

  if (!response.ok) {
    throw new Error(`Chat API error: ${response.status}`);
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) throw new Error("No response body");

  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6);
        if (data === "[DONE]") return;
        
        try {
          const event: ChatEvent = JSON.parse(data);
          yield event;
        } catch (e) {
          console.warn("Failed to parse SSE:", data);
        }
      }
    }
  }
}
```

### React Hook

```typescript
// hooks/useChat.ts
import { useState, useCallback } from "react";
import { streamChat, ChatEvent, Message } from "../api/chat";

interface UseChatReturn {
  messages: Message[];
  isLoading: boolean;
  isThinking: boolean;
  currentTool: string | null;
  error: string | null;
  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [currentTool, setCurrentTool] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    const userMessage: Message = { role: "user", content };
    const newMessages = [...messages, userMessage];
    
    setMessages(newMessages);
    setIsLoading(true);
    setError(null);

    let assistantContent = "";

    try {
      for await (const event of streamChat(newMessages)) {
        switch (event.type) {
          case "thinking":
            setIsThinking(true);
            setCurrentTool(event.content || "Processing...");
            break;

          case "tool_call":
            setCurrentTool(`Searching: ${event.name}`);
            break;

          case "tool_result":
            // Tool completed, about to get response
            setCurrentTool("Formatting results...");
            break;

          case "text":
            setIsThinking(false);
            setCurrentTool(null);
            assistantContent += event.content || "";
            // Update message in real-time
            setMessages([
              ...newMessages,
              { role: "assistant", content: assistantContent }
            ]);
            break;

          case "done":
            // Final state
            break;

          case "error":
            setError(event.content || "Unknown error");
            break;
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message");
    } finally {
      setIsLoading(false);
      setIsThinking(false);
      setCurrentTool(null);
    }
  }, [messages]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    isThinking,
    currentTool,
    error,
    sendMessage,
    clearMessages,
  };
}
```

### Chat Component

```tsx
// components/Chat.tsx
import { useChat } from "../hooks/useChat";
import { useState } from "react";
import ReactMarkdown from "react-markdown";

export function Chat() {
  const { 
    messages, 
    isLoading, 
    isThinking, 
    currentTool, 
    error, 
    sendMessage 
  } = useChat();
  const [input, setInput] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    
    const message = input;
    setInput("");
    await sendMessage(message);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`p-4 rounded-lg ${
              msg.role === "user"
                ? "bg-blue-600 ml-12"
                : "bg-gray-800 mr-12"
            }`}
          >
            {msg.role === "assistant" ? (
              <ReactMarkdown className="prose prose-invert">
                {msg.content}
              </ReactMarkdown>
            ) : (
              msg.content
            )}
          </div>
        ))}

        {/* Thinking indicator */}
        {isThinking && (
          <div className="bg-gray-800 mr-12 p-4 rounded-lg">
            <div className="flex items-center gap-2 text-gray-400">
              <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full" />
              <span>{currentTool || "Thinking..."}</span>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-900/50 p-4 rounded-lg text-red-300">
            {error}
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-700">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about stocks, market movers, analysis..."
            className="flex-1 bg-gray-800 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="bg-blue-600 px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
```

---

## Expected Response Format

AlphaBot responses follow this structure:

### 1. Data Table (when applicable)
```markdown
| Ticker | Price | Change | Volume | Signal |
|--------|-------|--------|--------|--------|
| **XYZ** | $2.45 | +15.2% | 3.2x | Unusual Volume |
| **ABC** | $1.12 | +8.4% | 2.8x | Breakout |
```

### 2. Insight
> "XYZ stands out with a potential FDA catalyst driving the volume surge."

### 3. Follow-up Question (always present)
> "Would you like me to pull up the full analysis or chart for any of these tickers?"

---

## Handling Charts

If the response contains a chart reference, it will be in this format:
```
[CHART:SYMBOL:INTERVAL:PERIOD:INDICATORS]
```

**Example:**
```
[CHART:AAPL:1d:3mo:sma_20,sma_50,volume]
```

### Parsing Chart References

```typescript
function parseChartReferences(content: string): ChartConfig[] {
  const regex = /\[CHART:([A-Z]+):(\w+):(\w+):([^\]]+)\]/g;
  const charts: ChartConfig[] = [];
  
  let match;
  while ((match = regex.exec(content)) !== null) {
    charts.push({
      symbol: match[1],
      interval: match[2],
      period: match[3],
      indicators: match[4].split(","),
    });
  }
  
  return charts;
}

// Then fetch chart data:
// GET /api/chart/{symbol}?interval={interval}&period={period}&indicators={indicators}
```

---

## Error Handling

| Error | Cause | User Action |
|-------|-------|-------------|
| `"API key not configured"` | Server misconfigured | Contact admin |
| `"Tool error: ..."` | Data fetch failed | Try different query |
| Empty response | Model issue | Retry request |

---

## Testing

```bash
# Test the chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "What are the top gainers today?"}]}'
```

---

## Summary

1. **POST to `/api/chat`** with messages array
2. **Handle SSE events** in order: thinking → tool_call → tool_result → text → done
3. **Show loading state** during `thinking` and `tool_call` events
4. **Stream text content** as it arrives
5. **Parse Markdown** in assistant responses (tables, bold, etc.)
6. **Detect chart references** with `[CHART:...]` pattern

