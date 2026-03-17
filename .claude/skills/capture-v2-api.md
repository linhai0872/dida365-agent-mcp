---
name: capture-v2-api
description: >
  逆向发现和验证 Dida365/TickTick V2 私有 API 端点。当需要探索新的 V2 端点、
  验证已知端点是否仍然可用、排查 V2 API 调用失败（401/500）、或更新 client_v2.py
  中的端点路径时，使用此 skill。也适用于竞品报告了新端点需要验证的场景。
  触发关键词：V2 API、抓包、逆向、端点发现、私有 API、session token、
  网络请求捕获、API 变动。
---

# 逆向 Dida365/TickTick V2 私有 API

通过 Playwright 浏览器自动化，在真实登录会话中抓包和探测 V2 端点。
三阶段流程：被动抓包 → 主动探测 → JS Bundle 补充。

## 前置条件

- Playwright MCP 工具可用（browser_navigate, browser_network_requests, browser_evaluate）
- 用户的滴答清单/TickTick 账号密码（用于在 Playwright 中登录）

## Phase 1: 被动抓包 — 登录 + 浏览页面捕获读端点

登录后 Web App 初始化会批量加载数据，仅这一步就能抓到 20+ 个端点。

1. 打开登录页：`browser_navigate → https://dida365.com/signin`
2. 让用户在 Playwright 浏览器窗口输入账号密码，等用户确认登录完成
3. 捕获登录后的网络请求：`browser_network_requests(includeStatic=false)`
4. 触发更多页面以收集更多端点：

```
browser_navigate → https://dida365.com/webapp/#q/all/habit    # 习惯
browser_navigate → https://dida365.com/webapp/#focus           # 专注
browser_navigate → https://dida365.com/webapp/#s               # 搜索
browser_navigate → https://dida365.com/webapp/#countdown       # 倒计时
browser_navigate → https://dida365.com/webapp/#p/settings/account  # 设置
```

每次导航后 `browser_network_requests` 抓取新增请求。

5. 汇总去重：提取所有 `api.dida365.com/api/v2/` 和 `/api/v3/` 的请求，去重排序。

## Phase 2: 主动探测 — 用页面内 fetch 测试端点

登录后页面自动持有 session cookie，用 `browser_evaluate` 在页面上下文中发请求，无需手动提取或传递 cookie。

**单端点测试：**

```javascript
browser_evaluate → async () => {
  const r = await fetch('/api/v2/tags');
  return { status: r.status, body: await r.text() };
}
```

**批量测试：**

```javascript
browser_evaluate → async () => {
  const tests = [
    { name: 'GET /api/v2/tags', method: 'GET', url: '/api/v2/tags' },
    { name: 'POST /api/v2/batch/tag add', method: 'POST', url: '/api/v2/batch/tag',
      body: JSON.stringify({ add: [{ name: "test", color: "#F18181" }] }) },
  ];
  const results = [];
  for (const t of tests) {
    const opts = { method: t.method };
    if (t.body) { opts.body = t.body; opts.headers = { 'Content-Type': 'application/json' }; }
    const r = await fetch(t.url, opts);
    const text = await r.text();
    const isHtml = text.includes('<!DOCTYPE');
    results.push({ name: t.name, status: r.status, body: isHtml ? '(HTML 404)' : text.slice(0, 300) });
  }
  return results;
}
```

**状态码含义：**

| 状态码 | 含义 |
|--------|------|
| 200 | 端点存在且请求格式正确 |
| 405 | 端点存在，HTTP 方法不对（换 GET↔POST↔PUT↔DELETE） |
| 500 + `no_project_permission` | 端点存在，请求体缺少必填字段 |
| 500 + `unknown_exception` | 端点存在，请求体格式有误 |
| 404 HTML 页面 | 端点不存在 |

## Phase 3: 从 JS Bundle 补充（可选）

Web App 的业务 JS 在 CDN 上，路径通常被压缩拼接，grep 完整路径命中率低。搜索路径关键词片段更有效（如 `batch/tag`、`pomodoros`、`habitCheckins`）。

```javascript
browser_evaluate → () => Array.from(document.querySelectorAll('script[src]'))
  .map(s => s.src).filter(u => u.includes('/app/'))
```

## 已验证端点速查

### 标签 — `POST /api/v2/batch/tag`

```json
{"add": [{"name": "标签名", "color": "#F18181", "sortOrder": 0, "sortType": "project"}]}
{"update": [{"name": "标签名", "color": "#新颜色"}]}
{"delete": [{"name": "标签名"}]}
```

- 字段名用 `name`（不是 `label`）
- 返回 `{"id2etag": {"标签名": "etag值"}, "id2error": {}}`
- 列表：`GET /api/v2/tags`
- 单删：`DELETE /api/v2/tag/{name}`
- 重命名：无专用端点，delete 旧 + add 新

### 全量同步 — `GET /api/v3/batch/check/0`

返回 12 个顶级 key：syncTaskBean, projectProfiles, projectGroups, filters, tags, syncTaskOrderBean, syncOrderBean, syncOrderBeanV3, inboxId, checks, remindChanges, checkPoint。
增量同步：`GET /api/v3/batch/check/{checkPoint_timestamp}`

### 其他已验证读端点

```
GET /api/v2/habits               → 习惯列表
GET /api/v2/habitSections        → 习惯分组
GET /api/v2/pomodoros/timeline   → 专注会话列表
GET /api/v2/user/profile         → 用户资料
GET /api/v2/user/status          → Pro 状态、收件箱 ID
GET /api/v2/column?from=0        → 看板列
GET /api/v2/countdown/list       → 倒计时
GET /api/v2/templates            → 模板
GET /api/v2/notification/unread  → 未读通知
GET /api/v2/calendar/third/accounts → 第三方日历
GET /api/v2/calendar/subscription   → 订阅日历
```

### 搜索 — `GET /api/v2/search/all` ✅ 已实现

**重要经验：** `POST /api/v2/task/search` 是移动端用的端点（500 `no_project_permission`），
Web 端实际使用的是完全不同的 `GET /api/v2/search/all`。
这个发现来自逆向 Web App 的 JS Bundle（`2977094657/DidaAPI` 项目中的 `web.ap-*.js`），
所有开源竞品（ticktick-sdk、ticktick-py、karbassi/ticktick-mcp）都没有实现服务端搜索，
它们全部使用客户端内存过滤。

```
GET /api/v2/search/all?keywords=关键词&projectId=p1&tags=work&status=0&dueFrom=ts&dueTo=ts
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `keywords` | string (URL encoded) | 搜索关键词（必填） |
| `projectId` | string（可多个） | 按项目过滤 |
| `tags` | string（可多个） | 按标签过滤 |
| `status` | int（可多个） | 0=未完成, 2=已完成 |
| `dueFrom` | ms timestamp | 截止日期起始 |
| `dueTo` | ms timestamp | 截止日期结束 |

响应（实测确认，与 JS Bundle 分析的 `{data:{tasks,comments}}` 不同）：
```json
{"hits": [...], "tasks": [...], "comments": []}
```
- `tasks` — 完整任务对象数组（含 id, projectId, title, content, status 等）
- `hits` — 搜索命中记录（与 tasks 数量一致）
- `comments` — 空数组（关联评论）

**逆向方法论总结：**
1. 当 Phase 2 主动探测某个端点持续返回 500 时，不要死磕请求体格式。
   优先用 Phase 3 从 JS Bundle 中搜索相关关键词（如 `search`），往往能发现 Web 端
   使用的是完全不同的端点路径。移动端和 Web 端的 API 路由可能不同。
2. JS Bundle 中的响应解析代码（如 `e.data.tasks`）可能包含 axios 的 `.data` 解包，
   不代表 API 原始响应有 `data` 包装层。**务必用 Phase 2 实际请求验证响应格式。**

### 待探索

| 端点 | 现状 | 思路 |
|------|------|------|
| `POST /api/v2/task/search` | 500 `no_project_permission` | 移动端端点，Web 端不用。如需探索，需抓 Android/iOS 网络请求 |
| 回收站 | 404 on `/api/v2/trash/tasks` | 路径可能不同，尝试 JS Bundle 搜索 `trash`/`delete` |

## 注意事项

- **不需要 `X-Device` header** — 纯 cookie 认证即可
- **写操作测试后务必清理** — 创建标签后记得删除，避免污染用户数据
- **session 会过期** — 返回 401 时需要用户重新登录
- **dida365.com vs ticktick.com** — 端点路径相同，只是域名不同
