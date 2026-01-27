import requests
import json

# 1. Configuration
#    Ollama runs on localhost:11434 by default.
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "deepseek-r1:8b"  # Make sure you have pulled this model (`ollama pull deepseek-r1:8b`)

def ask_ollama(prompt):
    # 2. Prepare the Payload
    #    "stream": False means we wait for the full response instead of getting chunks.
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    print(f"Connecting to {OLLAMA_URL} with model {MODEL}...")
    
    try:
        # 3. Send the POST Request
        response = requests.post(OLLAMA_URL, json=payload)
        
        # 4. Check for HTTP Errors
        response.raise_for_status()
        
        # 5. Parse JSON Response
        data = response.json()
        
        # 6. Extract the actual text
        return data["message"]["content"]
        
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    # Test it out
    question = "Why is the sky blue? Answer in one sentence."
    print(f"\nAsking: {question}\n")
    
    answer = ask_ollama(question)
    
    print("-" * 40)
    print("OLLAMA SAYS:")
    print("-" * 40)
    print(answer)
    print("-" * 40)
