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
npx @anthropic/playwright-mcp@latest

# 4. Clone and set up project
git clone <repo>
cd kosher
python -m venv venv
source venv/bin/activate
pip install -e .

# 5. Run proof of concept
python poc/main.py
```
