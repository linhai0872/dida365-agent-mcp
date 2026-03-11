<h1 align="center">dida365-agent-mcp</h1>

<p align="center">
  <strong>让 AI Agent 管理你的滴答清单 / TickTick 任务和项目</strong>
</p>

<p align="center">
  <a href="README.md">English</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-blue?logo=python&logoColor=white" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/FastMCP-3.x-purple" alt="FastMCP 3.x">
  <img src="https://img.shields.io/badge/transport-stdio%20%7C%20HTTP-green" alt="Transport">
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="License">
</p>

---

基于 Python [FastMCP](https://github.com/jlowin/fastmcp) 构建的 [MCP](https://modelcontextprotocol.io/) 服务，将 AI Agent（Claude Code、Cursor、Windsurf 等）连接到[滴答清单](https://dida365.com) / [TickTick](https://ticktick.com) Open API，通过自然语言管理任务和项目。

同时支持**滴答清单**（国内版）和 **TickTick**（国际版），一个环境变量即可切换。

## 特性

- **完整 API 覆盖** — 全部 14 个官方 Open API 端点，包含 `move`（移动任务）、`filter`（条件筛选）、`completed`（已完成查询）
- **双传输模式** — `stdio` 供本地客户端；`streamable-http` 供远程 Agent
- **双平台支持** — 通过 `DIDA365_REGION` 配置切换滴答清单 / TickTick
- **OAuth 一键授权** — 脚本自动打开浏览器、接收回调、保存 Token
- **Docker 就绪** — `docker compose up` 一键部署
- **Agent 友好** — 结构化 JSON 返回、清晰的 tool 标注、可操作的错误提示

## 部署

### 方案 A — 本地（stdio）

适用于 Claude Code、Cursor、Windsurf 等本地 MCP 客户端。

**1. 安装**

```bash
git clone https://github.com/linhai0872/dida365-agent-mcp.git
cd dida365-agent-mcp
uv sync
```

> 需要 [uv](https://docs.astral.sh/uv/getting-started/installation/) 和 Python 3.12+。

**2. 获取开发者凭据**

前往开发者中心，创建应用并复制凭据：
- 滴答清单：https://developer.dida365.com/manage
- TickTick：https://developer.ticktick.com/manage

将 **Redirect URI** 设置为 `http://localhost:8000/oauth/callback`。

**3. 配置**

```bash
cp .env.example .env
```

```env
DIDA365_REGION=china              # 国际版填 "international"
DIDA365_CLIENT_ID=your_client_id
DIDA365_CLIENT_SECRET=your_client_secret
```

**4. 授权**

```bash
uv run python scripts/oauth_flow.py
```

浏览器自动打开，登录后授权即可。Token 保存至 `~/.dida365-agent-mcp/token.json`，有效期约 180 天。

**5. 连接 AI 客户端**

<details>
<summary>Claude Code</summary>

编辑 `~/.claude/mcp.json`：

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

进入 **Settings > MCP > Add new global MCP server**：

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

### 方案 B — 远程（Docker + HTTP）

适用于需要持续运行或团队共享的场景。

**1. 先在本地完成授权**（方案 A 第 1–4 步）

**2. 配置**

```bash
cp .env.example .env
# 填入 DIDA365_REGION 和 DIDA365_ACCESS_TOKEN（来自授权脚本输出）
```

**3. 启动**

```bash
docker compose up -d
```

连接地址：`http://your-host:8000/mcp`

> 容器内无法打开浏览器，需在 `.env` 中直接设置 `DIDA365_ACCESS_TOKEN`。

---

### 开始使用

用自然语言和 AI 对话：

- *「列出我所有的项目」*
- *「在工作项目里创建一个高优先级任务'评审 PR'，截止明天」*
- *「这周我完成了哪些任务？」*
- *「把'设计评审'移到归档项目」*

## 工具一览

### 任务操作

| Tool | 说明 |
|------|------|
| `dida365_create_task` | 创建任务（标题、项目、日期、优先级、标签、提醒、重复规则） |
| `dida365_update_task` | 更新任务字段（部分更新） |
| `dida365_complete_task` | 标记任务为已完成 |
| `dida365_delete_task` | 永久删除任务 |
| `dida365_get_task` | 获取任务详情 |
| `dida365_move_task` | 在项目间移动任务 |

### 查询操作

| Tool | 说明 |
|------|------|
| `dida365_get_project_tasks` | 获取项目下所有未完成任务 |
| `dida365_filter_tasks` | 按项目、日期、优先级、标签、状态筛选 |
| `dida365_get_completed_tasks` | 获取已完成任务（可指定时间范围） |

### 项目操作

| Tool | 说明 |
|------|------|
| `dida365_list_projects` | 列出所有项目（首先调用以获取 ID） |
| `dida365_get_project` | 获取项目详情 |
| `dida365_create_project` | 创建项目（列表 / 看板 / 时间线视图） |
| `dida365_update_project` | 更新项目属性 |
| `dida365_delete_project` | 永久删除项目及其所有任务 |

## 配置项

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DIDA365_REGION` | `china`（dida365.com）或 `international`（ticktick.com） | `china` |
| `DIDA365_CLIENT_ID` | OAuth Client ID | — |
| `DIDA365_CLIENT_SECRET` | OAuth Client Secret | — |
| `DIDA365_ACCESS_TOKEN` | Access Token（直接设置可跳过 OAuth） | — |
| `DIDA365_REDIRECT_URI` | OAuth 回调地址 | `http://localhost:8000/oauth/callback` |
| `TRANSPORT` | `stdio`、`streamable-http` 或 `sse`（旧版兼容） | `stdio` |
| `HOST` | 绑定地址（http / sse 模式） | `0.0.0.0` |
| `PORT` | 端口（http / sse 模式） | `8000` |

## Token 生命周期

| 项目 | 说明 |
|------|------|
| 有效期 | 约 180 天 |
| 自动刷新 | 不支持（API 限制） |
| 过期检测 | 内置，到期前 24 小时预警 |
| 续期方式 | 重新运行 `uv run python scripts/oauth_flow.py` |
| 存储位置 | `~/.dida365-agent-mcp/token.json`（自动加载） |

## 开发

```bash
uv sync                                    # 安装依赖
uv run pytest tests/ -v                    # 运行测试
uv run ruff check src/ tests/ scripts/     # 代码检查
uv run ruff format src/ tests/ scripts/    # 格式化
uv run pyright src/                        # 类型检查
uv run dida365-mcp                         # 启动（stdio）
TRANSPORT=streamable-http uv run dida365-mcp   # 启动（Streamable HTTP）
```

## 项目结构

```
dida365-agent-mcp/
├── src/dida365_agent_mcp/
│   ├── server.py        # FastMCP 服务 + 14 个 tool 定义
│   ├── client.py        # 异步 API 客户端（httpx）
│   ├── auth.py          # OAuth2 授权 + Token 管理
│   ├── models.py        # Pydantic 数据模型
│   └── config.py        # 区域感知配置
├── scripts/
│   └── oauth_flow.py    # 一键 OAuth 授权脚本
├── tests/               # 单元测试（respx）
├── Dockerfile           # 多阶段构建
└── docker-compose.yml
```

## 许可证

[MIT](LICENSE)

## 致谢

- [滴答清单](https://developer.dida365.com/docs#/openapi) / [TickTick](https://developer.ticktick.com/docs#/openapi) Open API
- [FastMCP](https://github.com/jlowin/fastmcp) — Python MCP 框架
- [Model Context Protocol](https://modelcontextprotocol.io/)
