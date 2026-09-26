from __future__ import annotations

import json
from typing import Any, Awaitable, Callable

from app.core.models import ToolCall, ToolResult
from app.tools.github import GitHubToolAdapter


Authorizer = Callable[[int, str, dict[str, Any]], Awaitable[bool]]
AuditRecorder = Callable[
    [int, str, str, dict[str, Any], Any], Awaitable[None]
]


class NikaToolRegistry:
    """Single execution boundary for Nika tools.

    Every tool call is validated against a registered definition, authorized,
    executed, and optionally audited. GitHub MCP is just another adapter.
    """

    def __init__(
        self,
        *,
        github: GitHubToolAdapter | None = None,
        authorizer: Authorizer | None = None,
        audit_recorder: AuditRecorder | None = None,
    ) -> None:
        self._github = github
        self._authorizer = authorizer or self._allow_all
        self._audit_recorder = audit_recorder
        self._github_definitions: dict[str, dict[str, Any]] = {}

    async def refresh(self) -> None:
        if self._github is None:
            self._github_definitions = {}
            return
        definitions = await self._github.definitions()
        self._github_definitions = {
            str(item["name"]): dict(item) for item in definitions
        }

    def definitions(self) -> list[dict[str, Any]]:
        return list(self._github_definitions.values())

    async def execute(
        self,
        call: ToolCall,
        *,
        user_id: int,
        conversation_id: str,
    ) -> ToolResult:
        definition = self._github_definitions.get(call.name)
        if definition is None or self._github is None:
            raise ValueError(f"Unknown or unavailable tool: {call.name}")

        self._validate_arguments(definition, call.arguments)

        allowed = await self._authorizer(
            user_id, call.name, call.arguments
        )
        if not allowed:
            raise PermissionError(f"Tool not authorized: {call.name}")

        try:
            result = await self._github.execute(
                name=call.name,
                arguments=call.arguments,
                user_id=user_id,
                conversation_id=conversation_id,
            )
            if self._audit_recorder:
                await self._audit_recorder(
                    user_id,
                    conversation_id,
                    call.name,
                    call.arguments,
                    self._redact_result(result),
                )
            return ToolResult(
                tool_call_id=call.id,
                name=call.name,
                result=result,
                is_error=bool(result.get("is_error")),
            )
        except Exception as exc:
            if self._audit_recorder:
                await self._audit_recorder(
                    user_id,
                    conversation_id,
                    call.name,
                    call.arguments,
                    {"error": type(exc).__name__},
                )
            raise

    @staticmethod
    async def _allow_all(
        user_id: int, name: str, arguments: dict[str, Any]
    ) -> bool:
        return True

    @staticmethod
    def _validate_arguments(
        definition: dict[str, Any], arguments: dict[str, Any]
    ) -> None:
        schema = definition.get("inputSchema") or definition.get("input_schema") or {}
        if not isinstance(schema, dict):
            return

        required = schema.get("required", [])
        properties = schema.get("properties", {})

        missing = [
            name for name in required
            if name not in arguments
        ]
        if missing:
            raise ValueError(
                f"Missing required arguments for {definition['name']}: {missing}"
            )

        if isinstance(properties, dict):
            unknown = set(arguments) - set(properties)
            if unknown and schema.get("additionalProperties") is False:
                raise ValueError(
                    f"Unknown arguments for {definition['name']}: {sorted(unknown)}"
                )

    @staticmethod
    def _redact_result(result: Any) -> Any:
        # Keep audit records bounded and avoid persisting huge MCP payloads.
        try:
            encoded = json.dumps(result, ensure_ascii=False, default=str)
        except Exception:
            return {"type": type(result).__name__}
        if len(encoded) <= 12000:
            return result
        return {
            "truncated": True,
            "preview": encoded[:12000],
        }
