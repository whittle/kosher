"""Ollama agentic loop for interpreting Gherkin steps via tool calling."""

import json
import re
from typing import Any

from ollama import AsyncClient

MODEL = "qwen2.5-coder:14b-instruct-q4_K_M"
MAX_ROUNDS = 10

SYSTEM_PROMPT = """\
You are a browser automation agent. You receive Gherkin BDD steps and execute \
them by calling browser tools.

Rules:
1. Before interacting with any element, call browser_snapshot to see the current \
page and discover element refs.
2. Use the exact "ref" value from the snapshot when calling browser_click or \
browser_type. Pass the ref as the "ref" parameter.
3. For browser_type, set the "text" parameter to the value to type and \
"ref" to the ref of the target field. Do NOT press Enter unless the step \
says to.
4. For "Given" steps that mention a URL, call browser_navigate with that URL, \
then call browser_snapshot to confirm.
5. For "Then" assertion steps that check for text:
   - First call browser_wait_for with "text" set to the expected content
   - Then call browser_snapshot to verify
   - Respond with "PASS" if visible, "FAIL: <reason>" if not
6. For "When" action steps, after performing the action respond with "DONE".
7. Only call one tool at a time. Wait for the result before deciding the next \
action.
8. Stop calling tools once the step is complete and reply with your text verdict.
9. browser_wait_for waits for content to appear. Use parameters:
   - "text": wait for this text to be visible (preferred for assertions)
   - "timeout": milliseconds to wait (optional, default is reasonable)
"""


def parse_tool_call_from_text(text: str | None) -> tuple[str, dict[str, Any]] | None:
    """Try to parse a tool call from JSON text content.

    Returns (name, arguments) tuple if found, None otherwise.
    """
    if not text:
        return None

    # Strip markdown code blocks if present
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None

    # Handle {"name": "...", "arguments": {...}} format
    if isinstance(data, dict) and "name" in data:
        name = data.get("name")
        args = data.get("arguments", data.get("parameters", {}))
        if isinstance(name, str) and isinstance(args, dict):
            return name, args

    return None


async def execute_step(
    step: str,
    mcp: Any,
    history: list[dict[str, Any]],
) -> tuple[str, bool]:
    """Execute a single Gherkin step through the LLM agentic loop.

    Args:
        step: The Gherkin step text.
        mcp: An McpClient instance with ollama_tools and call_tool().
        history: Conversation history (mutated in place across steps).

    Returns:
        (response_text, success) where success is True unless the LLM
        responded with FAIL or we hit the round limit.
    """
    client = AsyncClient()
    history.append({"role": "user", "content": step})

    for _round in range(MAX_ROUNDS):
        response = await client.chat(
            model=MODEL,
            messages=history,
            tools=mcp.ollama_tools,
        )
        msg = response.message

        # Debug: show what the LLM returned
        content_preview = repr(msg.content[:100]) if msg.content else None
        print(
            f"    [round {_round + 1}] tool_calls={bool(msg.tool_calls)}, content={content_preview}",
            flush=True,
        )

        if msg.tool_calls:
            # Add the assistant's tool-call message to history
            history.append(msg.model_dump())

            for tool_call in msg.tool_calls:
                name = tool_call.function.name
                args = tool_call.function.arguments
                print(f"    -> {name}({args})", flush=True)

                result_text = await mcp.call_tool(name, args)
                # Truncate long snapshots for display
                preview = (
                    result_text[:200] + "..." if len(result_text) > 200 else result_text
                )
                print(f"    <- {preview}", flush=True)

                history.append(
                    {"role": "tool", "content": result_text, "tool_name": name}
                )
        else:
            # Try to parse tool call from text content
            parsed = parse_tool_call_from_text(msg.content)
            if parsed:
                name, args = parsed
                print(f"    -> {name}({args}) [parsed from text]", flush=True)

                result_text = await mcp.call_tool(name, args)
                preview = (
                    result_text[:200] + "..." if len(result_text) > 200 else result_text
                )
                print(f"    <- {preview}", flush=True)

                # Add to history as if it were a tool call
                history.append({"role": "assistant", "content": msg.content})
                history.append(
                    {"role": "tool", "content": result_text, "tool_name": name}
                )
                continue  # Next round

            # LLM responded with non-tool text — step is done
            text = msg.content or ""
            history.append({"role": "assistant", "content": text})
            success = not text.upper().startswith("FAIL")
            return text, success

    # Hit round limit without a text response
    return "FAIL: max tool-call rounds exceeded", False
