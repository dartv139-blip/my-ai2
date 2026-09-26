from __future__ import annotations

from typing import Any

from app.mcp.github_client import GitHubMCPClient


class GitHubToolAdapter:
    """Expose GitHub MCP tools through Nika's ToolRegistry contract."""

    def __init__(self, client: GitHubMCPClient) -> None:
        self.client = client

    async def definitions(self) -> list[dict[str, Any]]:
        return await self.client.list_tools()

    async def execute(
        self,
        *,
        name: str,
        arguments: dict[str, Any],
        user_id: int,
        conversation_id: str,
    ) -> dict[str, Any]:
        # user_id and conversation_id are deliberately accepted at this
        # boundary so ToolRegistry can audit and authorize before execution.
        # GitHub MCP itself remains responsible for GitHub authorization.
        return await self.client.call_tool(name, arguments)
