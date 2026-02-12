"""MCP client for Playwright browser automation."""

from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ALLOWED_TOOLS = {
    "browser_navigate",
    "browser_snapshot",
    "browser_click",
    "browser_type",
    "browser_press_key",
    "browser_wait_for",
}


def _mcp_tool_to_ollama(tool: Any) -> dict[str, Any]:
    """Convert an MCP Tool to an Ollama tool definition dict."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema,
        },
    }


class McpClient:
    """Manages the lifecycle of a Playwright MCP server connection."""

    def __init__(self) -> None:
        self._stack = AsyncExitStack()
        self._session: ClientSession | None = None
        self._ollama_tools: list[dict[str, Any]] = []

    async def connect(self) -> None:
        """Spawn the Playwright MCP server and initialize the session."""
        server_params = StdioServerParameters(
            command="npx",
            args=["@playwright/mcp@latest"],
        )
        read_stream, write_stream = await self._stack.enter_async_context(
            stdio_client(server_params)
        )
        self._session = await self._stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await self._session.initialize()

        result = await self._session.list_tools()
        filtered = [t for t in result.tools if t.name in ALLOWED_TOOLS]
        self._ollama_tools = [_mcp_tool_to_ollama(t) for t in filtered]

    @property
    def ollama_tools(self) -> list[dict[str, Any]]:
        """Tool definitions formatted for Ollama's chat API."""
        return self._ollama_tools

    async def call_tool(self, name: str, args: dict[str, Any]) -> str:
        """Execute a tool call and return the text result."""
        assert self._session is not None, "Not connected"
        result = await self._session.call_tool(name, args)
        parts: list[str] = []
        for block in result.content:
            text = getattr(block, "text", None)
            if isinstance(text, str):
                parts.append(text)
        return "\n".join(parts)

    async def close(self) -> None:
        """Shut down the MCP server and clean up resources."""
        await self._stack.aclose()
