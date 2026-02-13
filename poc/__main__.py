"""Kosher Phase 1 PoC — run a hardcoded login scenario via LLM + Playwright MCP."""

import asyncio
import sys

from poc.llm import SYSTEM_PROMPT, execute_step
from poc.mcp_client import McpClient
from poc.server import start_server
from poc.steps import STEPS

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


async def run() -> bool:
    base_url = start_server()
    print(f"Test server running at {base_url}")

    mcp = McpClient()
    print("Connecting to Playwright MCP server...")
    await mcp.connect()
    print(f"Connected — {len(mcp.ollama_tools)} tools available\n")

    history: list[dict[str, object]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    passed = 0
    failed = 0

    for step in STEPS:
        print(f"  Step: {step}")
        text, success = await execute_step(step, mcp, history)
        if success:
            print(f"  {GREEN}PASS{RESET}: {text}\n")
            passed += 1
        else:
            print(f"  {RED}FAIL{RESET}: {text}\n")
            failed += 1
            break

    print("=" * 50)
    print(f"Results: {GREEN}{passed} passed{RESET}, {RED}{failed} failed{RESET}")

    if failed == 0:
        await mcp.close()
    else:
        print("Browser left open for review. Press Ctrl+C to exit.")
        await asyncio.Event().wait()  # Wait indefinitely

    return failed == 0


def main() -> None:
    try:
        success = asyncio.run(run())
    except KeyboardInterrupt:
        sys.exit(1)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
