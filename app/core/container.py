from __future__ import annotations

from app.config import NikaConfig
from app.core.agent import AgentOrchestrator
from app.core.ports import LLMClient, ToolEventRepository
from app.core.tool_registry import NikaToolRegistry
from app.mcp.github_client import GitHubMCPClient
from app.tools.github import GitHubToolAdapter


class NikaContainer:
    """Application composition root.

    FastAPI should create this once at startup and close it at shutdown.
    """

    def __init__(
        self,
        *,
        llm: LLMClient,
        tool_events: ToolEventRepository | None = None,
        config: NikaConfig | None = None,
    ) -> None:
        self.config = config or NikaConfig.from_env()
        self.github_client: GitHubMCPClient | None = None
        self.tool_registry: NikaToolRegistry

        if self.config.github_mcp_enabled:
            self.github_client = GitHubMCPClient()
            github = GitHubToolAdapter(self.github_client)
        else:
            github = None

        async def audit(
            user_id: int,
            conversation_id: str,
            tool_name: str,
            arguments: dict,
            result: object,
        ) -> None:
            if tool_events is not None:
                await tool_events.record(
                    user_id,
                    conversation_id,
                    tool_name,
                    arguments,
                    result,
                )

        self.tool_registry = NikaToolRegistry(
            github=github,
            audit_recorder=audit,
        )
        self.agent = AgentOrchestrator(
            llm=llm,
            tools=self.tool_registry,
        )

    async def start(self) -> None:
        if self.github_client is not None:
            await self.github_client.start()
            await self.tool_registry.refresh()

    async def stop(self) -> None:
        if self.github_client is not None:
            await self.github_client.stop()
