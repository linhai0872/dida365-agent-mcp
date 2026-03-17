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

- **40 tools** — 19 V1 (official Open API) + 21 V2 (private API: tags, search, habits, folders, parent tasks)
- **Dual transport** — `stdio` for local clients; `streamable-http` for remote agents
- **Dual platform** — Dida365 and TickTick via `DIDA365_REGION` config
- **One-click OAuth** — script auto-opens browser, receives callback, saves token
- **Docker ready** — `docker compose up` to deploy
- **Agent-friendly** — structured JSON responses, clear tool annotations, actionable error messages

## Deployment

Four options, ordered from simplest to most complex.

---

### Option A — uvx (no install)

No git clone, no venv. Requires only [uv](https://docs.astral.sh/uv/getting-started/installation/).

**1. Get API credentials**

Create an app at the developer portal and copy the Client ID and Secret:
- Dida365: https://developer.dida365.com/manage
- TickTick: https://developer.ticktick.com/manage

Set **Redirect URI** to `http://localhost:8000/oauth/callback`.

**2. Create `.env` and authorize**

```bash
# Create config file
cat > .env << 'EOF'
DIDA365_REGION=china
DIDA365_CLIENT_ID=your_client_id
DIDA365_CLIENT_SECRET=your_client_secret
EOF

# Run OAuth — opens browser, saves token (~180 days)
uvx --from dida365-agent-mcp dida365-oauth
```

**3. Connect your AI client**

<details>
<summary>Claude Code</summary>

Edit `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "dida365": {
      "command": "uvx",
      "args": ["dida365-agent-mcp"]
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
      "command": "uvx",
      "args": ["dida365-agent-mcp"]
    }
  }
}
```

</details>

---

### Option B — pip install

```bash
pip install dida365-agent-mcp
```

Then follow the same steps as Option A, replacing `uvx --from dida365-agent-mcp dida365-oauth` with `dida365-oauth` and `uvx dida365-agent-mcp` with `dida365-mcp`.

---

### Option C — git clone (source / development)

```bash
git clone https://github.com/linhai0872/dida365-agent-mcp.git
cd dida365-agent-mcp
uv sync
cp .env.example .env   # fill in CLIENT_ID and CLIENT_SECRET
uv run python scripts/oauth_flow.py
```

MCP client config:

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

---

### Option D — Remote (Docker + HTTP)

For always-on or team deployments.

**1. Get the access token first** (run OAuth from Option A, B, or C)

**2. Deploy**

```bash
git clone https://github.com/linhai0872/dida365-agent-mcp.git
cd dida365-agent-mcp
cp .env.example .env
# Set DIDA365_REGION and DIDA365_ACCESS_TOKEN in .env
docker compose up -d
```

Connect to `http://your-host:8000/mcp`.

> The container cannot open a browser, so set `DIDA365_ACCESS_TOKEN` directly instead of running the OAuth script inside Docker.

---

### (Optional) Enable V2 tools — tags, search, habits, folders, parent tasks

Add one of the following to your `.env` (or MCP client `env` block):

```env
# Method 1: Session token (manual, most secure, 30-day expiry)
# Browser DevTools → Application → Cookies → copy 't' value
DIDA365_V2_SESSION_TOKEN=your_token

# Method 2: Auto-login (convenient, does not support 2FA)
DIDA365_USERNAME=your_email
DIDA365_PASSWORD=your_password
```

Without V2 config, you still get 19 V1 tools. With V2, you get all 40.

---

### Try It

Talk to your AI agent naturally:

- *"List all my projects"*
- *"Create a high-priority task 'Review PR' in Work, due tomorrow"*
- *"What tasks did I complete this week?"*
- *"Move 'Design review' to the Archive project"*
- *"Search tasks containing 'meeting'"* (V2)
- *"List all my tags"* (V2)
- *"Did I check in my reading habit today?"* (V2)

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

### Batch Operations

| Tool | Description |
|------|-------------|
| `dida365_get_task_by_id` | Get a task by ID only (no project_id needed) |
| `dida365_list_undone_tasks` | List undone tasks by date range or project |
| `dida365_batch_create_tasks` | Batch create multiple tasks |
| `dida365_batch_update_tasks` | Batch update multiple tasks |
| `dida365_batch_complete_tasks` | Batch complete multiple tasks |

### V2 Tools (optional — requires V2 auth)

| Tool | Description |
|------|-------------|
| `dida365_search_tasks` | Server-side full-text search with keyword, project, tag, status, date filters |
| `dida365_list_tags` | List all tags |
| `dida365_create_tags` | Batch create tags |
| `dida365_update_tags` | Batch update tags |
| `dida365_delete_tags` | Batch delete tags |
| `dida365_delete_tag` | Delete a single tag by name |
| `dida365_set_task_parent` | Set parent-child task relationship |
| `dida365_unset_task_parent` | Remove parent, make task top-level |
| `dida365_pin_task` | Pin or unpin a task |
| `dida365_list_habits` | List all habits |
| `dida365_create_habit` | Batch create habits |
| `dida365_update_habit` | Batch update habits |
| `dida365_delete_habit` | Batch delete habits |
| `dida365_checkin_habit` | Check in a habit for a date |
| `dida365_undo_checkin` | Undo a habit checkin |
| `dida365_list_habit_checkins` | List checkin records for a habit |
| `dida365_list_habit_sections` | List habit sections/groups |
| `dida365_list_folders` | List project folders |
| `dida365_create_folder` | Create a project folder |
| `dida365_update_folder` | Update a project folder |
| `dida365_delete_folder` | Delete a project folder |

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DIDA365_REGION` | `china` (dida365.com) or `international` (ticktick.com) | `china` |
| `DIDA365_CLIENT_ID` | OAuth Client ID | — |
| `DIDA365_CLIENT_SECRET` | OAuth Client Secret | — |
| `DIDA365_ACCESS_TOKEN` | Access token (set directly to skip OAuth) | — |
| `DIDA365_REDIRECT_URI` | OAuth callback URL | `http://localhost:8000/oauth/callback` |
| `DIDA365_V2_SESSION_TOKEN` | V2 session token (browser cookie `t`, 30-day expiry) | — |
| `DIDA365_USERNAME` | V2 auto-login email/phone (alternative to session token) | — |
| `DIDA365_PASSWORD` | V2 auto-login password (does not support 2FA) | — |
| `TRANSPORT` | `stdio`, `streamable-http`, or `sse` (legacy) | `stdio` |
| `HOST` | Bind address (http / sse only) | `0.0.0.0` |
| `PORT` | Port (http / sse only) | `8000` |

## Token Lifecycle

| Item | Detail |
|------|--------|
| Validity | ~180 days |
| Auto-refresh | Not supported (API limitation) |
| Expiry detection | Built-in, warns 24h before expiry |
| Renewal | Re-run `dida365-oauth` (or `uvx --from dida365-agent-mcp dida365-oauth`) |
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
│   ├── server.py        # FastMCP server + 19 V1 tool definitions + MCP resource
│   ├── server_v2.py     # 21 V2 tool definitions (tags, search, habits, folders)
│   ├── client.py        # V1 async API client (httpx + OAuth)
│   ├── client_v2.py     # V2 async API client (httpx + session cookie)
│   ├── auth.py          # OAuth2 flow + token management
│   ├── models.py        # Pydantic data models (V1 + V2)
│   └── config.py        # Region-aware configuration
├── scripts/
│   └── oauth_flow.py    # One-click OAuth script
├── tests/               # 62 unit tests (respx)
├── Dockerfile           # Multi-stage build
└── docker-compose.yml
```

## License

[MIT](LICENSE)

## Acknowledgments

- [Dida365](https://developer.dida365.com/docs#/openapi) / [TickTick](https://developer.ticktick.com/docs#/openapi) Open API
- [FastMCP](https://github.com/jlowin/fastmcp) — Python MCP framework
- [Model Context Protocol](https://modelcontextprotocol.io/)
