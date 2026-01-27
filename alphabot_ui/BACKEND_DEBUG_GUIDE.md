# Backend Debugging & Fix Guide for Alpha Bot

**Objective:** Fix `POST /api/chat` streaming logic.
**Current Status:** The frontend is working, but the backend terminates the connection prematurely and sends malformed tool data.

---

## 1. The Diagnosed Issue
The React frontend is receiving the following sequence from the backend before the connection closes unexpectedly:

1.  **Text Chunk:** `"Let me check..."` (Received OK)
2.  **Tool Call Chunk:** `{"type": "tool_call", "name": null, "arguments": 10}` (**CRITICAL ERROR**)
    *   `name` is `null` (Frontend expects a string like `"get_news"`).
    *   `arguments` is `10` (Frontend expects a JSON object or string args).
3.  **Connection Closed:** The stream ends immediately after this chunk. No `tool_result` or final answer is ever sent.

## 2. Required Fixes for Python Script

### A. Fix Tool Call Formatting
Ensure your streaming generator yields a valid `tool_call` event. It **must** include a valid function name.

**Incorrect (Current):**
```json
data: {"type": "tool_call", "name": null, "arguments": 10}
```

**Correct Requirement:**
```json
data: {"type": "tool_call", "name": "get_market_news", "arguments": {"symbol": "AAPL", "limit": 10}}
```

### B. Implement the "Tool Execution Loop"
The backend must not stop after sending the tool call. It must:
1.  **Yield** the `tool_call` event.
2.  **Execute** the Python function (e.g., `get_market_news`).
3.  **Yield** the `tool_result` event with the output.
4.  **Feed** the result back to the LLM to generate the final summary.
5.  **Yield** the final `text` chunks.
6.  **Yield** `{"type": "done"}`.

### C. Example Python Implementation (FastAPI)

Use this logic structure in your `/api/chat` endpoint:

```python
async def chat_stream(messages):
    # 1. Ask Model
    response = await kimi_model.chat(messages, stream=True)
    
    current_tool = None
    
    async for chunk in response:
        # CHECK: Is the model trying to call a tool?
        if chunk.has_tool_call:
            fn_name = chunk.tool_name  # e.g., "get_market_news"
            fn_args = chunk.tool_args  # e.g., {"symbol": "AAPL"}
            
            # 2. Notify Frontend we are running a tool
            yield f'data: {json.dumps({"type": "tool_call", "name": fn_name, "arguments": fn_args})}\n\n'
            
            # 3. Execute the tool Python-side
            tool_output = await execute_tool(fn_name, **fn_args)
            
            # 4. Notify Frontend of the result (HIDDEN from user, but used by UI logic)
            yield f'data: {json.dumps({"type": "tool_result", "name": fn_name, "result": tool_output})}\n\n'
            
            # 5. Send result back to Model for final answer
            final_answer_stream = await kimi_model.chat(
                messages + [{"role": "function", "name": fn_name, "content": json.dumps(tool_output)}],
                stream=True
            )
            
            # 6. Stream the final text
            async for text_chunk in final_answer_stream:
                yield f'data: {json.dumps({"type": "text", "content": text_chunk.text})}\n\n'
                
        else:
            # Normal text response
            yield f'data: {json.dumps({"type": "text", "content": chunk.text})}\n\n'

    # 7. Close gracefully
    yield f'data: {json.dumps({"type": "done"})}\n\n'
```

## 3. Checklist for Cursor
1.  [ ] **Check `extract_tool_calls`**: Verify your logic for extracting the function name isn't returning `None`.
2.  [ ] **Verify Loop**: Ensure the script doesn't `break` or `return` immediately after sending the `tool_call` event.
3.  [ ] **Parsing XML**: If Kimi outputs `<tool_code>`, ensure you parse it and **don't** just stream the raw XML to the frontend as text.
