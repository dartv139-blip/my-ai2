from __future__ import annotations

from typing import Any, Protocol, Sequence

from app.core.models import (
    LLMResponse,
    Memory,
    Message,
    ToolCall,
    ToolResult,
)


class LLMClient(Protocol):
    async def complete(
        self,
        messages: Sequence[dict[str, Any]],
        tools: Sequence[dict[str, Any]],
    ) -> LLMResponse: ...


class Tool(Protocol):
    name: str
    description: str

    async def execute(
        self,
        *,
        user_id: int,
        conversation_id: str,
        arguments: dict[str, Any],
    ) -> ToolResult: ...


class ToolRegistry(Protocol):
    async def execute(
        self,
        call: ToolCall,
        *,
        user_id: int,
        conversation_id: str,
    ) -> ToolResult: ...

    def definitions(self) -> Sequence[dict[str, Any]]: ...


class ConversationRepository(Protocol):
    async def get_for_user(
        self, conversation_id: str, user_id: int
    ) -> Any | None: ...

    async def create(
        self, user_id: int, conversation_id: str, title: str | None = None
    ) -> Any: ...

    async def delete_for_user(self, conversation_id: str, user_id: int) -> bool: ...


class MessageRepository(Protocol):
    async def add(self, conversation_id: str, role: str, content: str) -> Message: ...

    async def list_recent(
        self, conversation_id: str, limit: int
    ) -> Sequence[Message]: ...


class MemoryRepository(Protocol):
    async def add(self, user_id: int, content: str) -> Memory: ...

    async def search(
        self, user_id: int, query: str, limit: int
    ) -> Sequence[Memory]: ...


class ToolEventRepository(Protocol):
    async def record(
        self,
        user_id: int,
        conversation_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        result: Any,
    ) -> None: ...
