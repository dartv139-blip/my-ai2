from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence


@dataclass(frozen=True)
class Message:
    id: int
    conversation_id: str
    role: str
    content: str


@dataclass(frozen=True)
class Memory:
    id: int
    user_id: int
    content: str


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolResult:
    tool_call_id: str
    name: str
    result: Any
    is_error: bool = False


@dataclass(frozen=True)
class LLMResponse:
    content: str | None = None
    tool_calls: Sequence[ToolCall] = ()
