# Nika v2 — GitHub MCP integration

Nika v2 connects to the official GitHub MCP Server as a protocol adapter.

## Architecture

```
FastAPI -> ConversationService -> AgentOrchestrator -> ToolRegistry
        -> GitHubToolAdapter -> GitHubMCPClient
        -> Docker: ghcr.io/github/github-mcp-server -> GitHub API
```

The adapter does not implement GitHub business logic. It starts one long-lived
Docker MCP process and forwards tool definitions and calls through the official
MCP protocol.

## Docker / OAuth

The official GitHub MCP image supports browser OAuth on github.com. For Docker,
the OAuth callback uses a fixed loopback port:

```bash
docker run -i --rm \
  -p 127.0.0.1:8085:8085 \
  -e GITHUB_OAUTH_CALLBACK_PORT=8085 \
  ghcr.io/github/github-mcp-server
```

Nika starts the equivalent process itself.

## Safe default

Nika uses `GITHUB_READ_ONLY=1` and
`GITHUB_TOOLSETS=context,repos,issues,pull_requests,users`.

To enable writes intentionally, set `GITHUB_READ_ONLY=0` and restart Nika.
Writes should still pass through ToolRegistry authorization and
`tool_events` auditing.

## Authentication

OAuth is preferred for the interactive local Docker setup. For non-interactive
deployments, GitHub MCP also supports `GITHUB_PERSONAL_ACCESS_TOKEN` and
GitHub App authentication. Credentials must be injected at runtime and never
committed to Git.

## Lifecycle

Create one `GitHubMCPClient` at application startup, reuse it for calls, and
stop it at application shutdown. Do not launch a container for every tool call.

## Audit boundary

Before `GitHubToolAdapter.execute()`, ToolRegistry must validate arguments,
authorize the Nika user, execute the MCP call, and record a redacted result in
`tool_events`.

## Scope

This branch adds the protocol adapter and runtime configuration. It does not
replace the existing Cloudflare Worker; Python Nika remains the application
core until the Python API is deployed.
