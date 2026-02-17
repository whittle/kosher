"""Kosher Phase 1 PoC — run a hardcoded login scenario via LLM + Playwright MCP."""

import argparse
import asyncio
import sys
from collections import Counter
from typing import Optional

from kosher.parser import parse_feature
from kosher.parser.models import Step

from .llm import SYSTEM_PROMPT, execute_step
from .mcp_client import McpClient
from .server import start_server

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

FEATURE_FILE = "features/examples/login.feature"


async def run_once(mcp: McpClient, base_url: str) -> tuple[int, int, Optional[Step]]:
    """Run the scenario once.

    Returns:
        (passed, failed, failed_step) where failed_step is the step text that failed,
        or None if all steps passed.
    """
    feature = parse_feature(FEATURE_FILE)

    history: list[dict[str, object]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    passed = 0
    failed = 0
    failed_step: Optional[Step] = None

    for step in feature.scenarios[0].steps:
        print(f"  Step: {step.full_text}")
        text, success = await execute_step(step, mcp, history)
        if success:
            print(f"  {GREEN}PASS{RESET}: {text}\n")
            passed += 1
        else:
            print(f"  {RED}FAIL{RESET}: {text}\n")
            failed += 1
            failed_step = step
            break

    return passed, failed, failed_step


async def run_single() -> bool:
    """Run a single scenario (original behavior)."""
    base_url = start_server()
    print(f"Test server running at {base_url}")

    mcp = McpClient()
    print("Connecting to Playwright MCP server...")
    await mcp.connect()
    print(f"Connected — {len(mcp.ollama_tools)} tools available\n")

    passed, failed, _ = await run_once(mcp, base_url)

    print("=" * 50)
    print(f"Results: {GREEN}{passed} passed{RESET}, {RED}{failed} failed{RESET}")

    if failed == 0:
        await mcp.close()
    else:
        print("Browser left open for review. Press Ctrl+C to exit.")
        await asyncio.Event().wait()  # Wait indefinitely

    return failed == 0


async def run_benchmark(n: int) -> bool:
    """Run the scenario N times and report statistics."""
    base_url = start_server()
    print(f"Test server running at {base_url}")
    print(f"Running benchmark: {n} iterations\n")

    successes = 0
    failures = 0
    step_failures: Counter[Step] = Counter()

    for i in range(n):
        print(f"{'=' * 50}")
        print(f"Run {i + 1}/{n}")
        print(f"{'=' * 50}\n")

        mcp = McpClient()
        await mcp.connect()

        passed, failed, failed_step = await run_once(mcp, base_url)

        if failed == 0:
            successes += 1
            print(f"Run {i + 1}: {GREEN}SUCCESS{RESET}\n")
        else:
            failures += 1
            if failed_step:
                step_failures[failed_step] += 1
            print(f"Run {i + 1}: {RED}FAILURE{RESET}\n")

        await mcp.close()

    # Print statistics
    print("\n" + "=" * 50)
    print("BENCHMARK RESULTS")
    print("=" * 50)
    print(f"Total runs:   {n}")
    print(f"Successes:    {GREEN}{successes}{RESET}")
    print(f"Failures:     {RED}{failures}{RESET}")
    print(f"Success rate: {successes / n * 100:.1f}%")

    if step_failures:
        print("\nFailures by step:")
        for step, count in step_failures.most_common():
            print(f"  {count}x: {step}")

    return failures == 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Kosher PoC — run login scenario via LLM + Playwright MCP"
    )
    parser.add_argument(
        "--benchmark",
        type=int,
        metavar="N",
        help="Run the scenario N times and report statistics",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        if args.benchmark:
            success = asyncio.run(run_benchmark(args.benchmark))
        else:
            success = asyncio.run(run_single())
    except KeyboardInterrupt:
        sys.exit(1)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
