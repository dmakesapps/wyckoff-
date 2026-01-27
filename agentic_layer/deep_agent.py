
import os
import time
import requests
import json
import subprocess
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "deepseek-r1:8b" 
MINIMAX_URL = "https://api.minimaxi.com/v1/chat/completions"
MINIMAX_MODEL = "abab6.5s-chat" # Fast and smart

INSTRUCTION_FILE = os.path.join(BASE_DIR, "instructions.md")
MESSAGE_FILE = os.path.join(BASE_DIR, "message_to_agent.txt")
CHAT_HISTORY_FILE = os.path.join(BASE_DIR, "chat_history.json")
REFLECTION_GOALS_FILE = os.path.join(BASE_DIR, "reflection_goals.md")

# POINTING TO REAL PROJECT FILES NOW
TARGET_FILE = os.path.abspath(os.path.join(BASE_DIR, "../api/services/bot_brain.py"))
TEST_FILE = os.path.abspath(os.path.join(BASE_DIR, "../test_brain.py"))
LOG_FILE = os.path.join(BASE_DIR, "agent_log.txt")

AUTONOMOUS_MODE = True  # Enable Self-Reflection Loop
REFLECTION_INTERVAL = 30 # Seconds between reflections to prevent overheating
MAX_ITERATIONS = 20     # Safety limit for autonomous cycle

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DeepAgent")

def run_command(command: str) -> tuple[int, str, str]:
    """Runs a shell command and returns exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout expired"
    except Exception as e:
        return -1, "", str(e)

def read_file(filepath: str) -> str:
    if not os.path.exists(filepath):
        return ""
    with open(filepath, 'r') as f:
        return f.read()

def write_file(filepath: str, content: str):
    with open(filepath, 'w') as f:
        f.write(content)

def save_chat_message(role: str, content: str):
    """Saves a message to the chat history file."""
    history = []
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, 'r') as f:
                history = json.load(f)
        except:
            history = []
    
    timestamp = time.strftime("%H:%M:%S")
    history.append({"role": role, "content": content, "timestamp": timestamp})
    
    with open(CHAT_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

    with open(CHAT_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def reflect_and_generate_task(target_code: str, instructions: str) -> Optional[str]:
    """
    Self-Reflection Loop:
    analyzes code + goals -> suggests ONE concrete improvement prompt.
    """
    goals = read_file(REFLECTION_GOALS_FILE)
    
    prompt = f"""
You are an expert Autonomous AI Developer.
You are running a self-improvement loop for this Python file (`{TARGET_FILE}`).

CURRENT GOALS:
{goals}

CURRENT CODE:
```python
{target_code}
```

INSTRUCTIONS:
1. Review the code against the Current Phase in GOALS.
2. Identify ONE concrete, small improvement (e.g., "Add type hints to func X", "Add try/except block in func Y").
3. Do NOT suggest broad or vague changes. Small, testable steps only.
4. If the code looks good for the current phase, verify we are meeting all requirements.

OUTPUT FORMAT:
Return ONLY the prompt string that I should feed into the coding agent to execute this improvement.
Example: "Add a docstring to the get_alpha_data function describing the return dictionary structure."
"""
    logger.info("Agent is Reflecting on possible improvements...")
    response = query_llm(prompt)
    
    # Simple extraction: usually the model just replies detailed. 
    # We take the whole response as the new "User Message" essentially, 
    # but let's try to keep it concise.
    
    # Save thought process to chat
    save_chat_message("system", f"REFLECTION: {response}")
    
    return response

def query_llm(prompt: str, retries=2) -> str:
    """Dispatches to available LLM. Falls back to Ollama if Minimax fails."""
    minimax_key = os.getenv("MINIMAX_API_KEY")
    if minimax_key:
        response = query_minimax(prompt, minimax_key, retries)
        if response and response != "INTERRUPTED":
            return response
        logger.warning("Minimax failed or unauthorized. Falling back to local DeepSeek (Ollama)...")
    
    return query_ollama(prompt, retries=retries)

def query_minimax(prompt: str, api_key: str, retries=2) -> str:
    """Queries Minimax API (OpenAI Compatible)."""
    
    # Quick greeting bypass for speed
    low_prompt = prompt.lower().strip()
    if low_prompt in ["hey", "hi", "hello", "yo"]:
        return "Hey there! How can I help you with your Wyckoff trading bot today? I'm now powered by Minimax for faster responses."

    payload = {
        "model": MINIMAX_MODEL,
        "messages": [
            {"role": "system", "content": "You are an expert Python developer Agent. You help build a Wyckoff trading bot. Keep responses concise and focused on code or market analysis."},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    for attempt in range(retries):
        try:
            logger.info(f"Querying Minimax ({MINIMAX_MODEL}) - Attempt {attempt+1}... (Key Length: {len(api_key)})")
            response = requests.post(MINIMAX_URL, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result:
                return result["choices"][0]["message"]["content"]
            
            logger.error(f"Unexpected structure: {result}")
        except Exception as e:
            logger.error(f"Minimax Error: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response Body: {e.response.text}")
        
        if attempt < retries - 1:
            if read_file(MESSAGE_FILE).strip(): return "INTERRUPTED"
            time.sleep(1)
            
    return ""

def query_ollama(prompt: str, model: str = MODEL_NAME, retries=2) -> str:
    """Sends a prompt to Ollama and returns the response content."""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }
    
    for attempt in range(retries):
        try:
            logger.info(f"Querying Ollama ({model}) - Attempt {attempt+1}...")
            # Increased timeout to 600s (10 minutes) for complex reasoning
            response = requests.post(OLLAMA_URL, json=payload, timeout=600)
            response.raise_for_status()
            result = response.json()
            return result["message"]["content"]
        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out (600s).")
        except Exception as e:
            logger.error(f"Failed to query Ollama: {e}")
        
        if attempt < retries - 1:
            # Check for user interruption during retry wait
            if read_file(MESSAGE_FILE).strip():
                logger.info("User interruption detected during retry wait. Aborting current task.")
                return "INTERRUPTED"
            logger.info("Retrying in 5 seconds...")
            time.sleep(5)
            
    return ""

def extract_code_block(text: str) -> Optional[str]:
    """Extracts code from markdown code blocks."""
    if "```python" in text:
        start = text.find("```python") + 9
        end = text.find("```", start)
        if end != -1:
            return text[start:end].strip()
    elif "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end != -1:
            return text[start:end].strip()
    return None

def main():
    logger.info("Starting DeepSeek Agent Loop...")
    
    # Ensure necessary files exist or create defaults
    if not os.path.exists(INSTRUCTION_FILE):
        write_file(INSTRUCTION_FILE, f"# Instructions\nCheck {TARGET_FILE} and ensure it passes {TEST_FILE}.")
    
    while True:
        logger.info("--- New Iteration ---")
        
        # 1. Read State (Check for interruptions first)
        user_message = read_file(MESSAGE_FILE)
        if user_message:
            logger.info(f"User Message Detect (Immediate): {user_message}")
            if "STOP" in user_message:
                logger.info("Stopping agent loop as requested.")
                break
        
        instructions = read_file(INSTRUCTION_FILE)
        
        if user_message:
            logger.info(f"User Message Detect: {user_message}")
            if "STOP" in user_message:
                logger.info("Stopping agent loop as requested.")
                break
            # Append user message to instructions for this turn
            instructions += f"\n\nUSER OVERRIDE:\n{user_message}"
            # Clear message file after reading
            write_file(MESSAGE_FILE, "")

        target_code = read_file(TARGET_FILE)
        test_code = read_file(TEST_FILE)
        
        if not target_code:
            logger.warning(f"{TARGET_FILE} not found. Creating a placeholder.")
            write_file(TARGET_FILE, "def hello():\n    return 'world'\n")
            target_code = read_file(TARGET_FILE)

        if not test_code:
            logger.warning(f"{TEST_FILE} not found. Creating a placeholder.")
            write_file(TEST_FILE, "import target_script\ndef test_hello():\n    assert target_script.hello() == 'world'\n    print('Test Passed!')\n\nif __name__ == '__main__':\n    test_hello()")
            test_code = read_file(TEST_FILE)
            
        # 2. Run Tests
        logger.info(f"Running tests: python3 {TEST_FILE}")
        return_code, stdout, stderr = run_command(f"python3 {TEST_FILE}")
        
        if return_code == 0:
            if user_message:
                logger.info(f"Tests passed, but User Message detected: {user_message}")
                save_chat_message("user", user_message)
                
                # Direct response for greetings to bypass LLM latency/errors
                low_msg = user_message.lower().strip()
                if low_msg in ["hey", "hi", "hello", "yo"]:
                    response = "Hey there! I'm your Minimax-powered trading bot assistant. How can I help you with your Wyckoff strategies today?"
                    save_chat_message("assistant", response)
                    logger.info(f"AI: {response}")
                    write_file(MESSAGE_FILE, "") # Clear it
                    continue

                logger.info("Asking LLM to process user request...")
                
                prompt = f"""
You are an expert Python developer.
I have a file `{TARGET_FILE}` that is currently PASSING its tests.

However, the user has a request:
"{user_message}"

Here is the current content of `{TARGET_FILE}`:
```python
{target_code}
```

Here can refactor, optimize, or modify the code based on the user's request.
If the user's request is a question or chat, just answer it normally.
If the user's request requires a code change, return the full corrected python code for `{TARGET_FILE}` in a markdown code block.
Return ONLY the full corrected python code for `{TARGET_FILE}` in a markdown code block.
"""
                response = query_llm(prompt)
                save_chat_message("assistant", response)
                
                # LOG THE RESPONSE FOR THE USER
                logger.info("--- LLM RESPONSE ---")
                for line in response.split('\n'):
                    logger.info(f"AI: {line}")
                logger.info("-------------------------")

                new_code = extract_code_block(response)
                
                if new_code:
                    logger.info("Applying changes from User Request...")
                    write_file(TARGET_FILE, new_code)
                else:
                    logger.warning("LLM did not return valid code for the request.")
            
            elif AUTONOMOUS_MODE:
                logger.info("Tests Passed! Entering Self-Reflection Mode...")
                
                # Check iteration limits
                # (For specific logic we might want a counter, but for now we rely on time)
                
                # 1. Reflect
                new_task = reflect_and_generate_task(target_code, instructions)
                
                if new_task and "INTERRUPTED" not in new_task:
                    # Check for interruption before starting the heavy task
                    if read_file(MESSAGE_FILE).strip():
                        logger.info("User Message Detected! Aborting Self-Reflection task to prioritize User.")
                        continue

                    logger.info(f"Self-Reflection generated new task: {new_task}")
                    # Feed this back into the loop as if it were a user message for the next iteration
                    # But we execute it immediately here to save a cycle
                    save_chat_message("assistant", f"I have decided to: {new_task}")
                    
                    prompt = f"""
You are an expert Python developer.
I have a file `{TARGET_FILE}` that is currently PASSING its tests.

However, I have self-reflected and decided to improve it:
"{new_task}"

Here is the current content of `{TARGET_FILE}`:
```python
{target_code}
```

Please implement this improvement.
Ensure you do not break existing functionality.
Return ONLY the full corrected python code for `{TARGET_FILE}` in a markdown code block.
"""
                    response = query_llm(prompt)
                    save_chat_message("assistant", response)
                    
                    new_code = extract_code_block(response)
                    if new_code:
                         logger.info("Applying Self-Improvement Code...")
                         write_file(TARGET_FILE, new_code)
                    else:
                        logger.warning("LLM reflection did not yield code.")
                        
                else:
                     logger.info("Reflected but found no immediate improvements.")

                time.sleep(REFLECTION_INTERVAL)
                continue

            else:
                logger.info("Tests Passed! Waiting for new instructions or code changes...")
            
            time.sleep(5) 
            continue
        
        logger.info("Tests Failed. Attempting to fix...")
        logger.error(f"Error Output: {stderr}")
        
        # 3. Construct Prompt for DeepSeek
        prompt = f"""
You are an expert Python developer. 
I have a file `{TARGET_FILE}` that is failing its tests in `{TEST_FILE}`.

Here are the instructions:
{instructions}

Here is the current content of `{TARGET_FILE}`:
```python
{target_code}
```

Here is the test file `{TEST_FILE}`:
```python
{test_code}
```

Here is the error output from running the test:
```
{stderr}
{stdout}
```

Please fix the `{TARGET_FILE}` so that the tests pass. 
Return ONLY the full corrected python code for `{TARGET_FILE}` in a markdown code block. Do not remove any existing functionality unless it is the bug.
"""

        # 4. Get Fix
        response = query_llm(prompt)
        save_chat_message("assistant", response)
        
        # LOG THE RESPONSE FOR THE USER
        logger.info("--- LLM RESPONSE (Fixing Bug) ---")
        for line in response.split('\n'):
            logger.info(f"AI: {line}")
        logger.info("--------------------------------------")

        new_code = extract_code_block(response)
        
        if new_code:
            logger.info("Applying fix from DeepSeek...")
            write_file(TARGET_FILE, new_code)
            logger.info("Fix applied. Retrying in 5 seconds...")
        else:
            logger.error("Failed to extract code from DeepSeek response.")
            logger.info(f"Response was: {response}")
        
        time.sleep(5)

if __name__ == "__main__":
    main()
