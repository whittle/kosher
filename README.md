# Kosher

Kosher is a Behavior-Driven Development (BDD) tool that reads Gherkin feature
files and executes user stories against web applications using an AI inference
engine and Playwright browser automation.

## Requirements

Requires ollama and playwright-mcp running locally. Tested using Python v3.14.

## Getting Started

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull the model
ollama pull qwen2.5-coder:14b-instruct-q4_K_M

# 3. Start Playwright MCP server (separate terminal)
npx @playwright/mcp@latest

# 4. Clone and set up project
git clone <repo>
cd kosher
python -m venv venv
source venv/bin/activate
pip install -e .

# 5. Run proof of concept
python poc/main.py
```
## Reliability Summary: qwen2.5-coder:14b for Gherkin → Playwright

Success Rate: ~90% on a 6-step login flow (20 runs)

What Works Well:
- Correctly interprets Given/When/Then semantics
- Maps steps to appropriate browser tools (navigate, click, type, snapshot, wait_for)
- Extracts element refs from snapshots and uses them correctly (most of the time)
- Learns new patterns from system prompt updates (adopted browser_wait_for after instruction)

Failure Modes:
1. Placeholder refs - Sometimes outputs <EMAIL-field-ref> instead of actual ref like e5, suggesting it "knows" what to do but
doesn't execute properly
2. Skipped tool execution - Occasionally outputs JSON + "DONE" in one response without waiting for tool results
3. No native tool calling - Always outputs JSON in text content; requires parsing with parse_tool_call_from_text()
4. Instruction drift - Multi-step instructions (navigate → snapshot → confirm) sometimes get partially followed

Implications:
- Viable for PoC and demos
- Production use would need retry logic, validation, and possibly a more capable model
- System prompt engineering is effective for teaching new patterns
- The 10% failure rate is LLM variability, not fixable by prompt alone
