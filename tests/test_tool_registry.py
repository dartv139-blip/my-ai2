from app.core.models import ToolCall
from app.core.tool_registry import NikaToolRegistry


class FakeGitHub:
    async def definitions(self):
        return [
            {
                "name": "get_repo",
                "description": "Get repository",
                "inputSchema": {
                    "type": "object",
                    "required": ["owner", "repo"],
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
            }
        ]

    async def execute(self, **kwargs):
        return {"is_error": False, "content": [{"type": "text", "text": "ok"}]}


async def test_github_tool_is_exposed_and_executed():
    registry = NikaToolRegistry(github=FakeGitHub())
    await registry.refresh()

    result = await registry.execute(
        ToolCall(
            id="call-1",
            name="get_repo",
            arguments={"owner": "dartv139-blip", "repo": "my-ai2"},
        ),
        user_id=1,
        conversation_id="c1",
    )

    assert result.is_error is False
    assert result.name == "get_repo"
