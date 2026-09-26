# Nika v2 — Python interfaces and database design

Scope
Design contracts for FastAPI + Python application services + SQLite. The Cloudflare conversation-store project is used only as a source of design ideas: conversationId, persistent messages, summary, and bounded working context.

Request flow
POST /api/conversations/{conversation_id}/messages
-> FastAPI route -> authentication/current user -> ConversationService.send_message()
-> ownership check -> persist USER message -> load context -> load relevant memory
-> AgentOrchestrator -> LLM -> ToolRegistry when requested -> tool result -> LLM loop
-> persist ASSISTANT message -> response

Domain models

Conversation: id, user_id, title, summary, created_at, updated_at
Message: id, conversation_id, role, content, created_at
Memory: id, user_id, content, created_at, updated_at
Note: id, user_id, conversation_id, title, body, created_at, updated_at
ToolCall: id, name, arguments
ToolResult: tool_call_id, name, result

Python contracts

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, Sequence

class ConversationRepository(Protocol):
    async def get_for_user(self, conversation_id: str, user_id: int) -> Conversation | None: ...
    async def create(self, user_id: int, conversation_id: str, title: str | None = None) -> Conversation: ...
    async def delete_for_user(self, conversation_id: str, user_id: int) -> bool: ...

class MessageRepository(Protocol):
    async def add(self, conversation_id: str, role: str, content: str) -> Message: ...
    async def list_recent(self, conversation_id: str, limit: int) -> Sequence[Message]: ...

class MemoryRepository(Protocol):
    async def add(self, user_id: int, content: str) -> Memory: ...
    async def search(self, user_id: int, query: str, limit: int) -> Sequence[Memory]: ...

class NoteRepository(Protocol):
    async def list_for_user(self, user_id: int) -> Sequence[Note]: ...
    async def create(self, user_id: int, title: str, body: str, conversation_id: str | None = None) -> Note: ...

class ToolEventRepository(Protocol):
    async def record(self, user_id: int, conversation_id: str, tool_name: str, arguments: dict[str, Any], result: Any) -> None: ...

class LLMClient(Protocol):
    async def complete(self, messages: Sequence[dict[str, Any]], tools: Sequence[dict[str, Any]]) -> LLMResponse: ...

class Tool(Protocol):
    name: str
    description: str
    async def execute(self, *, user_id: int, conversation_id: str, arguments: dict[str, Any]) -> ToolResult: ...

class ToolRegistry(Protocol):
    async def execute(self, call: ToolCall, *, user_id: int, conversation_id: str) -> ToolResult: ...
    def definitions(self) -> Sequence[dict[str, Any]]: ...

class AgentOrchestrator:
    def __init__(self, llm: LLMClient, tools: ToolRegistry) -> None: ...
    async def run(self, *, user_id: int, conversation_id: str, user_message: str, context: Sequence[Message], memories: Sequence[Memory]) -> str: ...

class ConversationService:
    def __init__(self, conversations: ConversationRepository, messages: MessageRepository, memories: MemoryRepository, agent: AgentOrchestrator) -> None: ...
    async def send_message(self, *, user_id: int, conversation_id: str, message: str) -> Message: ...

Tool registry
memory, notes, web_search, secure_fetch, time
Every tool call: locate -> validate arguments -> authorize -> invoke service -> normalized ToolResult.

SQLite tables
users(id INTEGER PK, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TEXT NOT NULL, disabled INTEGER NOT NULL DEFAULT 0)
sessions(id TEXT PK, user_id INTEGER FK users, token_hash TEXT UNIQUE NOT NULL, created_at TEXT NOT NULL, expires_at TEXT NOT NULL, revoked_at TEXT)
conversations(id TEXT PK, user_id INTEGER FK users, title TEXT, summary TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)
messages(id INTEGER PK AUTOINCREMENT, conversation_id TEXT FK conversations, role TEXT CHECK role IN ('user','assistant'), content TEXT NOT NULL, created_at TEXT NOT NULL)
memories(id INTEGER PK AUTOINCREMENT, user_id INTEGER FK users, content TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)
notes(id INTEGER PK AUTOINCREMENT, user_id INTEGER FK users, conversation_id TEXT FK conversations nullable, title TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)
tool_events(id INTEGER PK AUTOINCREMENT, user_id INTEGER FK users, conversation_id TEXT FK conversations, tool_name TEXT NOT NULL, arguments_json TEXT NOT NULL, result_json TEXT, created_at TEXT NOT NULL)

Indexes
idx_sessions_user_id
idx_sessions_expires_at
idx_conversations_user_id_updated
idx_messages_conversation_created
idx_memories_user_id_updated
idx_notes_user_id_updated
idx_notes_conversation_id
idx_tool_events_conversation_created

Security invariants
1. Conversation access is always scoped to the owning user.
2. Client never submits server-side conversation history.
3. Tool calls always pass through ToolRegistry.
4. Tool authorization is checked before execution.
5. Tool calls/results are auditable in tool_events.
6. AgentOrchestrator does not access SQLite directly.
7. Secrets and owner data are not committed to the public repository.