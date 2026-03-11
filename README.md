<h1 align="center">dida365-agent-mcp</h1>

<p align="center">
  <strong>MCP server for AI agents to manage Dida365 / TickTick tasks and projects</strong>
</p>

<p align="center">
  <a href="README_zh.md">中文文档</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-blue?logo=python&logoColor=white" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/FastMCP-3.x-purple" alt="FastMCP 3.x">
  <img src="https://img.shields.io/badge/transport-stdio%20%7C%20HTTP-green" alt="Transport">
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="License">
</p>

---

A Python [MCP](https://modelcontextprotocol.io/) server built on [FastMCP](https://github.com/jlowin/fastmcp) that connects AI agents (Claude Code, Cursor, Windsurf, etc.) to the [Dida365](https://dida365.com) / [TickTick](https://ticktick.com) Open API. Manage tasks and projects through natural language.

Supports both **Dida365** (China) and **TickTick** (International) — switch with a single env var.

## Features

- **Full API coverage** — all 14 official Open API endpoints, including `move`, `filter`, and `completed` queries
- **Dual transport** — `stdio` for local clients; `streamable-http` for remote agents
- **Dual platform** — Dida365 and TickTick via `DIDA365_REGION` config
- **One-click OAuth** — script auto-opens browser, receives callback, saves token
- **Docker ready** — `docker compose up` to deploy
- **Agent-friendly** — structured JSON responses, clear tool annotations, actionable error messages

## Deployment

### Option A — Local (stdio)

For use with Claude Code, Cursor, Windsurf, and other local MCP clients.

**1. Install**

```bash
git clone https://github.com/linhai0872/dida365-agent-mcp.git
cd dida365-agent-mcp
uv sync
```

> Requires [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.12+.

**2. Get API Credentials**

Go to the developer portal, create an app, and copy the credentials:
- Dida365: https://developer.dida365.com/manage
- TickTick: https://developer.ticktick.com/manage

Set **Redirect URI** to `http://localhost:8000/oauth/callback`.

**3. Configure**

```bash
cp .env.example .env
```

```env
DIDA365_REGION=china              # or "international" for TickTick
DIDA365_CLIENT_ID=your_client_id
DIDA365_CLIENT_SECRET=your_client_secret
```

**4. Authorize**

```bash
uv run python scripts/oauth_flow.py
```

Browser opens automatically. Token saved to `~/.dida365-agent-mcp/token.json` (~180 days).

**5. Connect your AI client**

<details>
<summary>Claude Code</summary>

Edit `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "dida365": {
      "command": "uv",
      "args": ["--directory", "/path/to/dida365-agent-mcp", "run", "dida365-mcp"]
    }
  }
}
```

</details>

<details>
<summary>Cursor</summary>

Go to **Settings > MCP > Add new global MCP server**:

```json
{
  "mcpServers": {
    "dida365": {
      "command": "uv",
      "args": ["--directory", "/path/to/dida365-agent-mcp", "run", "dida365-mcp"]
    }
  }
}
```

</details>

---

### Option B — Remote (Docker + HTTP)

For always-on or team deployments accessible via HTTP.

**1. Complete OAuth locally first** (Option A steps 1–4)

**2. Configure**

```bash
cp .env.example .env
# Set DIDA365_REGION, DIDA365_ACCESS_TOKEN (from OAuth output)
```

**3. Deploy**

```bash
docker compose up -d
```

Connect to `http://your-host:8000/mcp`.

> The container cannot open a browser, so set `DIDA365_ACCESS_TOKEN` directly instead of running the OAuth script inside Docker.

---

### Try It

Talk to your AI agent naturally:

- *"List all my projects"*
- *"Create a high-priority task 'Review PR' in Work, due tomorrow"*
- *"What tasks did I complete this week?"*
- *"Move 'Design review' to the Archive project"*

## Tools

### Task Operations

| Tool | Description |
|------|-------------|
| `dida365_create_task` | Create a task with title, project, dates, priority, tags, reminders, recurrence |
| `dida365_update_task` | Update any task fields (partial update) |
| `dida365_complete_task` | Mark a task as completed |
| `dida365_delete_task` | Permanently delete a task |
| `dida365_get_task` | Get full details of a single task |
| `dida365_move_task` | Move a task between projects |

### Query Operations

| Tool | Description |
|------|-------------|
| `dida365_get_project_tasks` | Get all uncompleted tasks in a project |
| `dida365_filter_tasks` | Filter by project, date range, priority, tags, status |
| `dida365_get_completed_tasks` | Get completed tasks within a time range |

### Project Operations

| Tool | Description |
|------|-------------|
| `dida365_list_projects` | List all projects (call this first to get IDs) |
| `dida365_get_project` | Get project details |
| `dida365_create_project` | Create a project (list / kanban / timeline view) |
| `dida365_update_project` | Update project properties |
| `dida365_delete_project` | Permanently delete a project and all its tasks |

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DIDA365_REGION` | `china` (dida365.com) or `international` (ticktick.com) | `china` |
| `DIDA365_CLIENT_ID` | OAuth Client ID | — |
| `DIDA365_CLIENT_SECRET` | OAuth Client Secret | — |
| `DIDA365_ACCESS_TOKEN` | Access token (set directly to skip OAuth) | — |
| `DIDA365_REDIRECT_URI` | OAuth callback URL | `http://localhost:8000/oauth/callback` |
| `TRANSPORT` | `stdio`, `streamable-http`, or `sse` (legacy) | `stdio` |
| `HOST` | Bind address (http / sse only) | `0.0.0.0` |
| `PORT` | Port (http / sse only) | `8000` |

## Token Lifecycle

| Item | Detail |
|------|--------|
| Validity | ~180 days |
| Auto-refresh | Not supported (API limitation) |
| Expiry detection | Built-in, warns 24h before expiry |
| Renewal | Re-run `uv run python scripts/oauth_flow.py` |
| Storage | `~/.dida365-agent-mcp/token.json` (auto-loaded) |

## Development

```bash
uv sync                                    # Install dependencies
uv run pytest tests/ -v                    # Run tests
uv run ruff check src/ tests/ scripts/     # Lint
uv run ruff format src/ tests/ scripts/    # Format
uv run pyright src/                        # Type check
uv run dida365-mcp                         # Run (stdio)
TRANSPORT=streamable-http uv run dida365-mcp   # Run (Streamable HTTP)
```

## Project Structure

```
dida365-agent-mcp/
├── src/dida365_agent_mcp/
│   ├── server.py        # FastMCP server + 14 tool definitions
│   ├── client.py        # Async API client (httpx)
│   ├── auth.py          # OAuth2 flow + token management
│   ├── models.py        # Pydantic data models
│   └── config.py        # Region-aware configuration
├── scripts/
│   └── oauth_flow.py    # One-click OAuth script
├── tests/               # Unit tests (respx)
├── Dockerfile           # Multi-stage build
└── docker-compose.yml
```

## License

[MIT](LICENSE)

## Acknowledgments

- [Dida365](https://developer.dida365.com/docs#/openapi) / [TickTick](https://developer.ticktick.com/docs#/openapi) Open API
- [FastMCP](https://github.com/jlowin/fastmcp) — Python MCP framework
- [Model Context Protocol](https://modelcontextprotocol.io/)
