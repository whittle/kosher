# AGENTS.md

This file provides guidance to AI agents when working with code in this repository.

## Project Overview

Kosher is a BDD tool that reads Gherkin `.feature` files and executes user stories against web applications using a local LLM (Ollama/Qwen) for step interpretation and Playwright MCP for browser automation. The project is in early development (Phase 3 in PROJECT_PLAN.md).

## Development Environment

- **Python 3.14** (managed via `.python-version`)
- **uv** for package management (`uv.lock` is checked in)
- **Pre-commit hooks** enforce: trailing whitespace, end-of-file fixup, YAML checks, large file checks, `uv-lock`/`uv-export` sync, `ruff` lint+format, and `ty` type checking

## Commands

```bash
# Install dependencies (creates .venv automatically)
uv sync

# Install pre-commit hooks.
uv run pre-commit install

# Perform all validates and fixes.
uv run pre-commit run

# Run test suite.
uv run pytest

# Run proof of concept
uv run python -m poc

# Run linter (with auto-fix)
uv run ruff check --fix .

# Run formatter
uv run ruff format .

# Run type checker
uv run ty check

# Install/update pre-commit hooks
uv run pre-commit run --all-files
```

## External Dependencies

Kosher requires two external services running locally:
1. **Ollama** with model `qwen2.5-coder:14b-instruct-q4_K_M` (or `qwen2.5-coder:7b` fallback)
2. **Playwright MCP server**: `npx @playwright/mcp@latest`

## Architecture

The system has four key components connected through an orchestrator:

- **Gherkin files** (.feature) are parsed and fed step-by-step to the orchestrator
- **Local LLM** (Ollama) interprets each Gherkin step and decides which Playwright action to take
- **Playwright MCP** executes browser actions (navigate, click, fill, screenshot, etc.)
- **Reporter** collects pass/fail results per step/scenario

The existing module structure is:
- `kosher/parser/` contains the parser that transforms Gherkin .feature files into domain models. (The models are in `kosher/parser/models.py`.)

Additionally, the proof of concept is in `poc/` and gets updated to use the new modules as they’re built.

Planned module structure (from PROJECT_PLAN.md): llm/` (Ollama client + prompts), `browser/` (Playwright MCP), `runner/` (execution), `reporter/` (output), `cli.py`, `config.py`.
