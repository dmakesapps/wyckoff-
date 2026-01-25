# Backend Bug Fixes - Chat Streaming

**Date:** January 24, 2026  
**Status:** ✅ Fixed and Verified

---

## Issue Summary

The frontend was receiving malformed tool call data from the `/api/chat` streaming endpoint:

```json
// BEFORE (Broken)
{"type": "tool_call", "name": null, "arguments": 10}
```

The connection would terminate immediately after this chunk, with no `tool_result` or final response.

---

## Root Cause

OpenRouter sends tool calls across **multiple SSE chunks**:

| Chunk | Contains |
|-------|----------|
| 1 | `id`, `name` (function name) |
| 2-N | `arguments` (partial JSON strings that need concatenation) |
| Final | `finish_reason: "tool_calls"` |

The original code tried to yield each chunk immediately, causing:
- `name: null` → Name hadn't arrived yet
- `arguments: 10` → Was reading chunk `index` instead of actual arguments
- Premature termination → No accumulation logic

---

## Fixes Applied

### 1. Accumulator Pattern in `_parse_stream()`

**File:** `api/services/chat.py`

```python
# NEW: Accumulator for tool calls (keyed by index)
pending_tool_calls: dict[int, dict] = {}

# For each chunk, accumulate data instead of yielding immediately
if tool_call.get("function"):
    func = tool_call["function"]
    if func.get("name"):
        pending_tool_calls[idx]["name"] = func["name"]
    if func.get("arguments"):
        pending_tool_calls[idx]["arguments_str"] += func["arguments"]

# Only yield when finish_reason == "tool_calls"
if finish_reason == "tool_calls":
    for idx in sorted(pending_tool_calls.keys()):
        tc = pending_tool_calls[idx]
        if tc.get("name"):  # Validate before yielding
            args = json.loads(tc["arguments_str"])
            yield {"type": "tool_call", "name": tc["name"], "arguments": args}
```

### 2. Validation Before Yielding Tool Calls

**File:** `api/services/chat.py`

```python
# Skip invalid tool calls
if not tool_name or not isinstance(tool_name, str):
    continue

# Ensure arguments is a dict
if not isinstance(tool_args, dict):
    tool_args = {}
```

### 3. Complete Tool Execution Loop

The flow now works correctly:
1. Stream initial text → `{"type": "text", "content": "I'll analyze..."}`
2. Accumulate tool call chunks
3. Yield complete tool call → `{"type": "tool_call", "name": "get_stock_analysis", "arguments": {...}}`
4. Execute Python function
5. Yield tool result → `{"type": "tool_result", "name": "...", "result": {...}}`
6. Continue conversation with LLM
7. Stream final response text
8. Yield done → `{"type": "done", "content": "full response"}`

---

## Verified Output

**Request:**
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Analyze TSLA"}],"stream":true}'
```

**Response (SSE Stream):**
```
data: {"type": "text", "content": "I'll get you a comprehensive TSLA analysis..."}

data: {"type": "tool_call", "name": "get_stock_analysis", "arguments": {"symbol": "TSLA", "include_news": true, "include_options": true}}

data: {"type": "tool_result", "name": "get_stock_analysis", "result": {"symbol": "TSLA", "price": 449.06, "alpha_grade": "B", "trend": "bullish", "rsi": 54.93, ...}}

data: {"type": "text", "content": "**TSLA Technical Analysis**\n\n"}
data: {"type": "text", "content": "Current price: $449.06..."}
... (more text chunks) ...

data: {"type": "done", "content": "full response text here"}
```

---

## Frontend Integration Notes

### Parsing SSE Chunks

```typescript
// Each line starts with "data: "
const lines = text.split('\n').filter(line => line.startsWith('data: '));

for (const line of lines) {
  const chunk = JSON.parse(line.slice(6)); // Remove "data: " prefix
  
  switch (chunk.type) {
    case 'text':
      // Append to streaming message
      appendToMessage(chunk.content);
      break;
      
    case 'tool_call':
      // Show loading indicator (e.g., "Fetching TSLA data...")
      // chunk.name is guaranteed to be a valid string
      // chunk.arguments is guaranteed to be an object
      showToolLoading(chunk.name, chunk.arguments);
      break;
      
    case 'tool_result':
      // Hide loading, optionally show data preview
      hideToolLoading();
      break;
      
    case 'done':
      // Stream complete
      finalizeMessage(chunk.content);
      break;
      
    case 'error':
      // Handle error
      showError(chunk.content);
      break;
  }
}
```

### Guaranteed Chunk Formats

| Type | Format |
|------|--------|
| `text` | `{"type": "text", "content": string}` |
| `tool_call` | `{"type": "tool_call", "name": string, "arguments": object}` |
| `tool_result` | `{"type": "tool_result", "name": string, "result": object}` |
| `done` | `{"type": "done", "content": string}` |
| `error` | `{"type": "error", "content": string}` |

**Key Guarantees:**
- `name` will always be a non-empty string (never `null`)
- `arguments` will always be an object (never a number or `null`)
- `tool_result` will always follow a `tool_call`
- `done` will always be the final chunk (unless `error`)

---

## Test Commands

```bash
# Health check
curl http://localhost:8000/api/health

# Non-streaming chat (simpler)
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"What is AAPL price?"}],"stream":false}'

# Streaming chat (full feature)
curl -N -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Analyze NVDA"}],"stream":true}'
```

---

## Status

- ✅ Tool calls have valid `name` (string)
- ✅ Tool calls have valid `arguments` (object)
- ✅ Tool results are returned
- ✅ Stream continues after tool execution
- ✅ Final response is generated
- ✅ `done` chunk sent at end

**Ready for frontend integration!**


