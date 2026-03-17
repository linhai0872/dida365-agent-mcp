"""
Smoke test — runs against real Dida365 API.

Tests V1 and V2 tools end-to-end. Creates and cleans up test data.
Run: uv run python scripts/smoke_test.py
"""

import asyncio
import sys

from dida365_agent_mcp.client import Dida365Client
from dida365_agent_mcp.client_v2 import Dida365V2Client, signon
from dida365_agent_mcp.config import settings

PASS = "\033[32m✓\033[0m"
FAIL = "\033[31m✗\033[0m"
SKIP = "\033[33m-\033[0m"

results: list[tuple[str, bool, str]] = []


def ok(name: str, detail: str = "") -> None:
    results.append((name, True, detail))
    print(f"  {PASS} {name}" + (f"  ({detail})" if detail else ""))


def fail(name: str, err: str) -> None:
    results.append((name, False, err))
    print(f"  {FAIL} {name}  ERROR: {err}")


def skip(name: str, reason: str) -> None:
    results.append((name, None, reason))  # type: ignore[arg-type]
    print(f"  {SKIP} {name}  (skipped: {reason})")


# ── V1 ──────────────────────────────────────────────────────────────────────

async def test_v1(client: Dida365Client) -> None:
    print("\n[V1 — Official Open API]")
    task_id: str | None = None
    project_id: str | None = None

    # list projects
    try:
        projects = await client.list_projects()
        project_id = projects[0].id if projects else None
        ok("list_projects", f"{len(projects)} projects")
    except Exception as e:
        fail("list_projects", str(e))
        return

    # create task
    try:
        task = await client.create_task(
            {"title": "[smoke-test] delete me", "projectId": project_id}
        )
        task_id = task.id
        ok("create_task", f"id={task_id[:8]}...")
    except Exception as e:
        fail("create_task", str(e))

    # get task
    if task_id and project_id:
        try:
            t = await client.get_task(project_id, task_id)
            ok("get_task", t.title)
        except Exception as e:
            fail("get_task", str(e))

    # update task (always pass projectId so client can re-fetch on empty response)
    if task_id and project_id:
        try:
            await client.update_task(
                task_id, {"title": "[smoke-test] updated", "projectId": project_id}
            )
            ok("update_task")
        except Exception as e:
            fail("update_task", str(e))

    # get project tasks
    if project_id:
        try:
            data = await client.get_project_with_data(project_id)
            ok("get_project_with_data", f"{len(data.tasks)} tasks")
        except Exception as e:
            fail("get_project_with_data", str(e))

    # complete task (cleanup)
    if task_id and project_id:
        try:
            await client.complete_task(project_id, task_id)
            ok("complete_task (cleanup)")
        except Exception as e:
            fail("complete_task", str(e))


# ── V2 ──────────────────────────────────────────────────────────────────────

async def test_v2(client: Dida365V2Client) -> None:
    print("\n[V2 — Private API]")
    tag_name = "__smoke_test__"

    # list tags
    try:
        tags = await client.list_tags()
        ok("list_tags", f"{len(tags)} tags")
    except Exception as e:
        fail("list_tags", str(e))

    # create tag
    try:
        result = await client.create_tags([{"name": tag_name, "color": "#F18181"}])
        ok("create_tags", str(result))
    except Exception as e:
        fail("create_tags", str(e))

    # update tag
    try:
        result = await client.update_tags([{"name": tag_name, "color": "#81B1F1"}])
        ok("update_tags", str(result))
    except Exception as e:
        fail("update_tags", str(e))

    # delete tag (cleanup)
    try:
        await client.delete_tag(tag_name)
        ok("delete_tag (cleanup)")
    except Exception as e:
        fail("delete_tag", str(e))

    # search tasks
    try:
        result = await client.search_tasks("smoke")
        count = len(result.get("tasks", []))
        ok("search_tasks", f"{count} results")
    except Exception as e:
        fail("search_tasks", str(e))

    # list habits
    try:
        habits = await client.list_habits()
        ok("list_habits", f"{len(habits)} habits")
    except Exception as e:
        fail("list_habits", str(e))

    # list habit sections
    try:
        sections = await client.list_habit_sections()
        ok("list_habit_sections", f"{len(sections)} sections")
    except Exception as e:
        fail("list_habit_sections", str(e))

    # list folders
    try:
        folders = await client.list_folders()
        ok("list_folders", f"{len(folders)} folders")
    except Exception as e:
        fail("list_folders", str(e))


# ── Main ─────────────────────────────────────────────────────────────────────

async def main() -> None:
    print("=" * 50)
    print("dida365-agent-mcp smoke test")
    print("=" * 50)

    # V1
    if settings.dida365_access_token:
        v1 = Dida365Client()
        await test_v1(v1)
    else:
        print("\n[V1] skipped — DIDA365_ACCESS_TOKEN not set")

    # V2 — resolve token
    v2_token = settings.dida365_v2_session_token
    if not v2_token and settings.dida365_username and settings.dida365_password:
        print("\n[V2] auto-login...")
        try:
            v2_token = await signon(
                settings.v2_api_base_url,
                settings.dida365_username,
                settings.dida365_password,
            )
            print("  auto-login succeeded")
        except Exception as e:
            print(f"  auto-login failed: {e}")

    if v2_token:
        v2 = Dida365V2Client(session_token=v2_token, base_url=settings.v2_api_base_url)
        await test_v2(v2)
    else:
        print("\n[V2] skipped — no V2 credentials")

    # Summary
    passed = sum(1 for _, s, _ in results if s is True)
    failed = sum(1 for _, s, _ in results if s is False)
    skipped = sum(1 for _, s, _ in results if s is None)
    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
