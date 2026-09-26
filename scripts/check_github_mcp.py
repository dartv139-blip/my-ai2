from __future__ import annotations

import asyncio

from app.mcp.github_client import GitHubMCPClient


async def main() -> None:
    async with GitHubMCPClient() as client:
        tools = await client.list_tools()
        print(f"GitHub MCP connected: {len(tools)} tools")
        for tool in tools:
            print(f"- {tool['name']}")


if __name__ == "__main__":
    asyncio.run(main())
