from app.core.agent import AgentOrchestrator
from app.core.models import LLMResponse, ToolCall


class FakeLLM:
    def __init__(self):
        self.calls = 0

    async def complete(self, messages, tools):
        self.calls += 1
        if self.calls == 1:
            return LLMResponse(
                tool_calls=[
                    ToolCall(
                        id="call-1",
                        name="get_repo",
                        arguments={"owner": "dartv139-blip", "repo": "my-ai2"},
                    )
                ]
            )
        return LLMResponse(content="Repo nalezeno.")


class FakeTools:
    def __init__(self):
        self.calls = []

    def definitions(self):
        return [{
            "name": "get_repo",
            "description": "Get repository",
            "inputSchema": {"type": "object"},
        }]

    async def execute(self, call, *, user_id, conversation_id):
        from app.core.models import ToolResult
        self.calls.append(call)
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            result={"ok": True},
        )


async def test_agent_runs_tool_then_returns_final_answer():
    llm = FakeLLM()
    tools = FakeTools()
    agent = AgentOrchestrator(llm, tools)

    answer = await agent.run(
        user_id=1,
        conversation_id="c1",
        user_message="Najdi repo",
        context=[],
        memories=[],
    )

    assert answer == "Repo nalezeno."
    assert len(tools.calls) == 1
    assert llm.calls == 2
