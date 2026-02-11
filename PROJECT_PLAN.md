# Kosher Project Plan

## Overview

Kosher is a Behavior-Driven Development (BDD) tool that reads Gherkin feature
files and executes user stories against web applications using an AI inference
engine and Playwright browser automation.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Gherkin Files  │────▶│   Orchestrator  │────▶│    Reporter     │
│   (.feature)    │     │    (Python)     │     │  (Pass/Fail)    │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
          ┌─────────────────┐       ┌─────────────────┐
          │   Local LLM     │       │  Playwright MCP │
          │ (Ollama/Qwen)   │       │    (Browser)    │
          └─────────────────┘       └─────────────────┘
```

## Technology Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| Language | Python 3.11+ | Primary development language |
| Gherkin Parser | `gherkin-official` or `behave` | Parse .feature files |
| Local LLM | Qwen 2.5 Coder 14B | Fits in 12GB VRAM with Q4 quantization |
| LLM Runtime | Ollama | Simple local model serving |
| Browser Automation | Playwright MCP | MCP-based browser control |
| MCP Client | `mcp` Python SDK | Connect to Playwright MCP server |

## Hardware Requirements

- **Goal** Should run well on a MacBook Pro with 18 GB of core without changing
  the VRAM max setting.
- **VRAM:** 12GB (confirmed)
- **Recommended Model:** `qwen2.5-coder:14b-instruct-q4_K_M`
- **Fallback Model:** `qwen2.5-coder:7b` (if 14B is too slow)

## Implementation Phases

### Phase 1: Proof of Concept (Validate Core Assumption)

**Goal:** Confirm that a local LLM can reliably translate Gherkin steps into Playwright actions.

**Tasks:**
- [x] Install Ollama and pull `qwen2.5-coder:14b-instruct-q4_K_M`
- [x] Set up Playwright MCP server
- [ ] Create a minimal Python script that:
   - Hardcodes 3-5 simple Gherkin steps
   - Sends each step to the LLM with available Playwright tools as context
   - Receives structured JSON output specifying the Playwright action
   - Executes the action via Playwright MCP
- [ ] Test against a simple static HTML page
- [ ] Evaluate: Does the LLM reliably produce correct actions?

**Success Criteria:**
- LLM correctly interprets 80%+ of simple steps on first attempt
- Actions execute successfully in browser

**Deliverables:**
- `poc/` directory with minimal working prototype
- Findings document on LLM reliability

---

### Phase 2: Gherkin Parser Integration

**Goal:** Replace hardcoded steps with proper Gherkin file parsing.

**Tasks:**
1. Integrate `gherkin-official` library
2. Parse `.feature` files into structured step data
3. Handle:
   - Feature descriptions
   - Scenario names
   - Given/When/Then steps
   - Scenario Outlines with examples
   - Data tables
4. Create step iterator that feeds parsed steps to the LLM

**Deliverables:**
- `parser/` module for Gherkin parsing
- Support for standard Gherkin syntax

---

### Phase 3: Robust LLM Integration

**Goal:** Build reliable, production-quality LLM communication.

**Tasks:**
1. Design prompt template that includes:
   - Current page context (URL, visible elements)
   - Available Playwright MCP tools with schemas
   - The Gherkin step to execute
   - Output format specification (JSON)
2. Implement retry logic for malformed LLM responses
3. Add response validation (is the JSON valid? does the tool exist?)
4. Implement conversation context (LLM remembers previous steps in scenario)
5. Handle LLM uncertainty (ask for clarification vs. best guess)

**Deliverables:**
- `llm/` module for Ollama communication
- Prompt templates
- Response validation logic

---

### Phase 4: Playwright MCP Integration

**Goal:** Execute LLM-generated actions via Playwright MCP.

**Tasks:**
1. Set up MCP client connection to Playwright server
2. Map LLM output to MCP tool calls:
   - `navigate(url)`
   - `click(selector)`
   - `fill(selector, value)`
   - `screenshot()`
   - `get_text(selector)`
   - etc.
3. Capture page state after each action for LLM context
4. Handle action failures gracefully
5. Implement element location strategies (text, CSS, accessibility)

**Deliverables:**
- `browser/` module for Playwright MCP communication
- Action execution with error handling

---

### Phase 5: Execution Engine & Reporting

**Goal:** Orchestrate full scenario execution with clear reporting.

**Tasks:**
1. Build scenario runner that:
   - Initializes browser session
   - Iterates through steps
   - Accumulates pass/fail status
   - Handles step dependencies
2. Implement reporting:
   - Console output (colored pass/fail)
   - JSON report for CI integration
   - Screenshot on failure
   - LLM explanation when step fails
3. Add configuration:
   - Target URL
   - Browser options (headless, viewport)
   - LLM model selection
   - Timeout settings

**Deliverables:**
- `runner/` module for orchestration
- `reporter/` module for output
- Configuration system

---

### Phase 6: CLI & Polish

**Goal:** Package as a usable command-line tool.

**Tasks:**
1. Create CLI with argparse or click:
   ```bash
   kosher run features/login.feature --base-url http://localhost:3000
   kosher run features/ --headless --report json
   ```
2. Add `--dry-run` mode (show planned actions without executing)
3. Add `--verbose` mode for debugging LLM reasoning
4. Write user documentation
5. Add example feature files

**Deliverables:**
- CLI entry point
- Documentation
- Example features

---

## Project Structure

```
kosher/
├── kosher/
│   ├── __init__.py
│   ├── cli.py              # Command-line interface
│   ├── config.py           # Configuration management
│   ├── parser/
│   │   ├── __init__.py
│   │   └── gherkin.py      # Gherkin file parsing
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py       # Ollama client
│   │   └── prompts.py      # Prompt templates
│   ├── browser/
│   │   ├── __init__.py
│   │   └── playwright.py   # Playwright MCP integration
│   ├── runner/
│   │   ├── __init__.py
│   │   └── executor.py     # Scenario execution
│   └── reporter/
│       ├── __init__.py
│       ├── console.py      # Terminal output
│       └── json.py         # JSON reports
├── features/
│   └── examples/           # Example .feature files
├── tests/
├── pyproject.toml
└── README.md
```

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| LLM produces incorrect actions | Validate output schema; implement retry with rephrased prompt |
| LLM hallucinates selectors | Include actual page elements in prompt context |
| 14B model too slow | Fall back to 7B; consider streaming responses |
| Playwright MCP connection issues | Implement reconnection logic; clear error messages |
| Ambiguous Gherkin steps | LLM asks for clarification or makes best guess with confidence score |

## Next Steps

- [x] **Immediate:** Set up Ollama with Qwen 2.5 Coder 14B
- [x] **Immediate:** Verify Playwright MCP is available and working
- [ ] **This week:** Complete Phase 1 proof of concept
- [ ] **Decision point:** After Phase 1, evaluate if local LLM is sufficient or if adjustments needed
