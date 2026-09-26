from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class NikaConfig:
    github_mcp_enabled: bool = True
    github_mcp_read_only: bool = True

    @classmethod
    def from_env(cls) -> "NikaConfig":
        return cls(
            github_mcp_enabled=os.getenv("NIKA_GITHUB_MCP_ENABLED", "1").lower()
            not in {"0", "false", "no", "off"},
            github_mcp_read_only=os.getenv("GITHUB_READ_ONLY", "1").lower()
            not in {"0", "false", "no", "off"},
        )
