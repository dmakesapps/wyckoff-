
# DeepSeek Agent Instructions

1. **Install Ollama**: Ensure you have Ollama installed and running.
   `ollama serve`

2. **Run deepseek-r1**: Ensure the model is pulled.
   `ollama pull deepseek-r1:8b`

3. **Configure Targets**:
   - Edit `agentic_layer/targets.json` (optional, or specify in script).
   - Currently, `deep_agent.py` targets `target_script.py` and `test_target.py` by default.

4. **Usage**:
   - Run the agent: `python3 agentic_layer/deep_agent.py`
   - The agent will continuously loop:
     - Read `target_script.py`
     - Run `test_target.py`
     - If failure: Ask DeepSeek for a fix -> Apply -> Repeat.
     - If success: Wait for new instructions / file changes.

5. **Interacting**:
   - Edit `target_script.py` directly to introduce a bug or new feature stub.
   - Edit `test_target.py` to add a new test case that currently fails.
   - The agent will pick up changes, see the failure, and fix `target_script.py` to pass the new test.

6. **Roadmap**:
   - Add capability to create new files.
   - Add capability to run arbitrary commands.
   - Add capability to "chat" with the agent via a `chat_history.md` file.
