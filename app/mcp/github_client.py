from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any

from mcp import Client
from mcp import StdioServerParameters
from mcp import stdio_client


@dataclass(frozen=True)
class GitHubMCPConfig:
    """Runtime configuration for the local GitHub MCP Docker server."""

    image: str = "ghcr.io/github/github-mcp-server"
    callback_port: int = 8085
    read_only: bool = True
    toolsets: str = "context,repos,issues,pull_requests,users"
    oauth_callback: bool = True

    @classmethod
    def from_env(cls) -> "GitHubMCPConfig":
        return cls(
            image=os.getenv("GITHUB_MCP_IMAGE", cls.image),
            callback_port=int(os.getenv("GITHUB_OAUTH_CALLBACK_PORT", str(cls.callback_port))),
            read_only=os.getenv("GITHUB_READ_ONLY", "1").lower() not in {"0", "false", "no", "off"},
            toolsets=os.getenv("GITHUB_TOOLSETS", cls.toolsets),
            oauth_callback=os.getenv("GITHUB_MCP_OAUTH", "1").lower() not in {"0", "false", "no", "off"},
        )

    def docker_parameters(self) -> StdioServerParameters:
        env: dict[str, str] = {
            "GITHUB_TOOLSETS": self.toolsets,
        }

        args = [
            "run",
            "-i",
            "--rm",
        ]

        if self.oauth_callback:
            args += [
                "-p",
                f"127.0.0.1:{self.callback_port}:{self.callback_port}",
                "-e",
                "GITHUB_OAUTH_CALLBACK_PORT",
            ]
            env["GITHUB_OAUTH_CALLBACK_PORT"] = str(self.callback_port)

        if self.read_only:
            args += ["-e", "GITHUB_READ_ONLY"]
            env["GITHUB_READ_ONLY"] = "1"

        args.append(self.image)

        return StdioServerParameters(
            command="docker",
            args=args,
            env=env,
        )


class GitHubMCPError(RuntimeError):
    """Raised when the GitHub MCP adapter cannot execute an operation."""


class GitHubMCPClient:
    """Persistent MCP client for the official GitHub MCP Docker server.

    The Docker process is owned by this object and is kept alive between
    tool calls. The adapter does not contain GitHub business logic; it only
    translates Nika tool calls to MCP calls.
    """

    def __init__(self, config: GitHubMCPConfig | None = None) -> None:
        self.config = config or GitHubMCPConfig.from_env()
        self._client: Client | None = None
        self._transport = None
        self._tools: dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        async with self._lock:
            if self._client is not None:
                return

            transport = stdio_client(self.config.docker_parameters())
            read_stream, write_stream = await transport.__aenter__()
            client = Client("nika-github", version="0.1.0")

            try:
                await client.__aenter__(read_stream, write_stream)
                result = await client.list_tools()
            except Exception:
                await transport.__aexit__(None, None, None)
                raise

            self._transport = transport
            self._client = client
            self._tools = {tool.name: tool for tool in result.tools}

    async def stop(self) -> None:
        async with self._lock:
            client, transport = self._client, self._transport
            self._client = None
            self._transport = None
            self._tools = {}

            if client is not None:
                await client.__aexit__(None, None, None)
            if transport is not None:
                await transport.__aexit__(None, None, None)

    async def list_tools(self) -> list[dict[str, Any]]:
        await self.start()
        return [
            {
                "name": tool.name,
                "description": tool.description or "",
                "inputSchema": tool.input_schema,
            }
            for tool in self._tools.values()
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        await self.start()
        client = self._client
        if client is None:
            raise GitHubMCPError("GitHub MCP client is not running")

        if name not in self._tools:
            raise GitHubMCPError(f"GitHub MCP tool is not available: {name}")

        try:
            result = await client.call_tool(name, arguments)
        except Exception as exc:
            raise GitHubMCPError(f"GitHub MCP call failed: {name}") from exc

        content: list[dict[str, Any]] = []
        for block in result.content:
            if getattr(block, "type", None) == "text":
                content.append({"type": "text", "text": block.text})
            else:
                content.append({"type": getattr(block, "type", "unknown")})

        return {
            "is_error": bool(result.is_error),
            "content": content,
            "structured_content": result.structured_content,
        }

    async def __aenter__(self) -> "GitHubMCPClient":
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.stop()
