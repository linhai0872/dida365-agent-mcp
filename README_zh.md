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

- **40 个工具** — 19 个 V1（官方 Open API）+ 21 个 V2（私有 API：标签、搜索、习惯、文件夹、父子任务）
- **双传输模式** — `stdio` 供本地客户端；`streamable-http` 供远程 Agent
- **双平台支持** — 通过 `DIDA365_REGION` 配置切换滴答清单 / TickTick
- **OAuth 一键授权** — 脚本自动打开浏览器、接收回调、保存 Token
- **Docker 就绪** — `docker compose up` 一键部署
- **Agent 友好** — 结构化 JSON 返回、清晰的 tool 标注、可操作的错误提示

## 部署

四种方案，按复杂度从低到高排列。

---

### 方案 A — uvx（零安装，最简）

无需 git clone，无需虚拟环境，只需安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)。

**1. 获取开发者凭据**

前往开发者中心创建应用，复制 Client ID 和 Client Secret：
- 滴答清单：https://developer.dida365.com/manage
- TickTick：https://developer.ticktick.com/manage

将 **Redirect URI** 设置为 `http://localhost:8000/oauth/callback`。

**2. 创建 `.env` 并授权**

```bash
# 创建配置文件
cat > .env << 'EOF'
DIDA365_REGION=china
DIDA365_CLIENT_ID=your_client_id
DIDA365_CLIENT_SECRET=your_client_secret
EOF

# 运行 OAuth — 自动打开浏览器，保存 Token（有效期约 180 天）
uvx --from dida365-agent-mcp dida365-oauth
```

**3. 连接 AI 客户端**

<details>
<summary>Claude Code</summary>

编辑 `~/.claude/mcp.json`：

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

进入 **Settings > MCP > Add new global MCP server**：

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

### 方案 B — pip install

```bash
pip install dida365-agent-mcp
```

后续步骤与方案 A 相同，将 `uvx --from dida365-agent-mcp dida365-oauth` 替换为 `dida365-oauth`，将 `uvx dida365-agent-mcp` 替换为 `dida365-mcp`。

---

### 方案 C — git clone（源码 / 开发）

```bash
git clone https://github.com/linhai0872/dida365-agent-mcp.git
cd dida365-agent-mcp
uv sync
cp .env.example .env   # 填入 CLIENT_ID 和 CLIENT_SECRET
uv run python scripts/oauth_flow.py
```

MCP 客户端配置：

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

### 方案 D — 远程（Docker + HTTP）

适用于需要持续运行或团队共享的场景。

**1. 先获取 Access Token**（通过方案 A、B 或 C 运行 OAuth）

**2. 部署**

```bash
git clone https://github.com/linhai0872/dida365-agent-mcp.git
cd dida365-agent-mcp
cp .env.example .env
# 在 .env 中填入 DIDA365_REGION 和 DIDA365_ACCESS_TOKEN
docker compose up -d
```

连接地址：`http://your-host:8000/mcp`

> 容器内无法打开浏览器，需在 `.env` 中直接设置 `DIDA365_ACCESS_TOKEN`。

---

### （可选）启用 V2 工具 — 标签、搜索、习惯、文件夹、父子任务

在 `.env`（或 MCP 客户端的 `env` 配置块）中添加以下任一方式：

```env
# 方式 1：Session Token（手动，最安全，30 天有效）
# 浏览器 DevTools → Application → Cookies → 复制 't' 的值
DIDA365_V2_SESSION_TOKEN=your_token

# 方式 2：自动登录（方便，不支持 2FA 账号）
DIDA365_USERNAME=your_email
DIDA365_PASSWORD=your_password
```

不配 V2 仍有 19 个 V1 工具可用，配置后可用全部 40 个。

---

### 开始使用

用自然语言和 AI 对话：

- *「列出我所有的项目」*
- *「在工作项目里创建一个高优先级任务'评审 PR'，截止明天」*
- *「这周我完成了哪些任务？」*
- *「把'设计评审'移到归档项目」*
- *「搜索包含'会议'的任务」*（V2）
- *「列出我所有的标签」*（V2）
- *「我今天的阅读习惯打卡了吗？」*（V2）

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

### 批量操作

| Tool | 说明 |
|------|------|
| `dida365_get_task_by_id` | 仅凭 task_id 获取任务（无需 project_id） |
| `dida365_list_undone_tasks` | 按日期范围或项目查询未完成任务 |
| `dida365_batch_create_tasks` | 批量创建任务 |
| `dida365_batch_update_tasks` | 批量更新任务 |
| `dida365_batch_complete_tasks` | 批量完成任务 |

### V2 工具（可选 — 需要 V2 认证）

| Tool | 说明 |
|------|------|
| `dida365_search_tasks` | 服务端全文搜索（关键词 + 项目/标签/状态/日期过滤） |
| `dida365_list_tags` | 列出所有标签 |
| `dida365_create_tags` | 批量创建标签 |
| `dida365_update_tags` | 批量更新标签 |
| `dida365_delete_tags` | 批量删除标签 |
| `dida365_delete_tag` | 按名称删除单个标签 |
| `dida365_set_task_parent` | 设置父子任务关系 |
| `dida365_unset_task_parent` | 解除父子关系，变为顶层任务 |
| `dida365_pin_task` | 置顶/取消置顶任务 |
| `dida365_list_habits` | 列出所有习惯 |
| `dida365_create_habit` | 批量创建习惯 |
| `dida365_update_habit` | 批量更新习惯 |
| `dida365_delete_habit` | 批量删除习惯 |
| `dida365_checkin_habit` | 习惯打卡 |
| `dida365_undo_checkin` | 撤销习惯打卡 |
| `dida365_list_habit_checkins` | 查询习惯打卡记录 |
| `dida365_list_habit_sections` | 列出习惯分组 |
| `dida365_list_folders` | 列出项目文件夹 |
| `dida365_create_folder` | 创建项目文件夹 |
| `dida365_update_folder` | 更新项目文件夹 |
| `dida365_delete_folder` | 删除项目文件夹 |

## 配置项

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DIDA365_REGION` | `china`（dida365.com）或 `international`（ticktick.com） | `china` |
| `DIDA365_CLIENT_ID` | OAuth Client ID | — |
| `DIDA365_CLIENT_SECRET` | OAuth Client Secret | — |
| `DIDA365_ACCESS_TOKEN` | Access Token（直接设置可跳过 OAuth） | — |
| `DIDA365_REDIRECT_URI` | OAuth 回调地址 | `http://localhost:8000/oauth/callback` |
| `DIDA365_V2_SESSION_TOKEN` | V2 Session Token（浏览器 cookie `t`，30 天有效） | — |
| `DIDA365_USERNAME` | V2 自动登录邮箱/手机（与 session token 二选一） | — |
| `DIDA365_PASSWORD` | V2 自动登录密码（不支持 2FA 账号） | — |
| `TRANSPORT` | `stdio`、`streamable-http` 或 `sse`（旧版兼容） | `stdio` |
| `HOST` | 绑定地址（http / sse 模式） | `0.0.0.0` |
| `PORT` | 端口（http / sse 模式） | `8000` |

## Token 生命周期

| 项目 | 说明 |
|------|------|
| 有效期 | 约 180 天 |
| 自动刷新 | 不支持（API 限制） |
| 过期检测 | 内置，到期前 24 小时预警 |
| 续期方式 | 重新运行 `dida365-oauth`（或 `uvx --from dida365-agent-mcp dida365-oauth`） |
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
│   ├── server.py        # FastMCP 服务 + 19 个 V1 tool 定义 + MCP Resource
│   ├── server_v2.py     # 21 个 V2 tool 定义（标签、搜索、习惯、文件夹）
│   ├── client.py        # V1 异步 API 客户端（httpx + OAuth）
│   ├── client_v2.py     # V2 异步 API 客户端（httpx + session cookie）
│   ├── auth.py          # OAuth2 授权 + Token 管理
│   ├── models.py        # Pydantic 数据模型（V1 + V2）
│   └── config.py        # 区域感知配置
├── scripts/
│   └── oauth_flow.py    # 一键 OAuth 授权脚本
├── tests/               # 62 个单元测试（respx）
├── Dockerfile           # 多阶段构建
└── docker-compose.yml
```

## 许可证

[MIT](LICENSE)

## 致谢

- [滴答清单](https://developer.dida365.com/docs#/openapi) / [TickTick](https://developer.ticktick.com/docs#/openapi) Open API
- [FastMCP](https://github.com/jlowin/fastmcp) — Python MCP 框架
- [Model Context Protocol](https://modelcontextprotocol.io/)
