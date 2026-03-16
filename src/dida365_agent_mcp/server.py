from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastmcp import FastMCP

from .client import Dida365Client
from .config import settings

logger = logging.getLogger(__name__)

_client: Dida365Client | None = None


def _get_client() -> Dida365Client:
    if _client is None:
        raise RuntimeError("Server not initialized. Client is not available.")
    return _client


@asynccontextmanager
async def lifespan(_app: Any):
    global _client
    _client = Dida365Client()
    yield
    await _client.close()


mcp = FastMCP(
    name="dida365-agent-mcp",
    instructions=(
        "Dida365/TickTick task management via Open API. "
        "Workflow: call dida365_list_projects to get project IDs, "
        "then operate on tasks within those projects. "
        "All task mutations require both project_id and task_id. "
        "Priority values: 0=None, 1=Low, 3=Medium, 5=High. "
        "Status values: 0=Normal, 2=Completed. "
        "Datetime format: yyyy-MM-dd'T'HH:mm:ssZ (e.g. 2025-03-15T09:00:00+0800)."
    ),
    lifespan=lifespan,
)


def _to_json(obj: Any) -> str:
    if hasattr(obj, "model_dump"):
        return json.dumps(obj.model_dump(exclude_none=True), ensure_ascii=False, indent=2)
    if isinstance(obj, list):
        items = [i.model_dump(exclude_none=True) if hasattr(i, "model_dump") else i for i in obj]
        return json.dumps(items, ensure_ascii=False, indent=2)
    return json.dumps(obj, ensure_ascii=False, indent=2)


def _handle_error(e: Exception, operation: str = "") -> str:
    import httpx

    logger.exception("Operation failed: %s", operation or "unknown")

    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        body = e.response.text
        messages = {
            401: (
                "Unauthorized. Token may have expired (~180 days). "
                "Re-run: uv run python scripts/oauth_flow.py"
            ),
            403: "Forbidden. Insufficient permission for this resource.",
            404: "Not found. Verify the project_id and task_id are valid.",
            429: "Rate limited. Wait 30-60s before retrying.",
        }
        msg = messages.get(status, f"API error (HTTP {status})")
        return f"Error: {msg}\nDetails: {body}"
    if isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. Try again."
    if isinstance(e, RuntimeError):
        return f"Error: {e}"
    return f"Error: {type(e).__name__}: {e}"


def _build_data(**kwargs: Any) -> dict[str, Any]:
    field_map = {
        "project_id": "projectId",
        "start_date": "startDate",
        "due_date": "dueDate",
        "is_all_day": "isAllDay",
        "time_zone": "timeZone",
        "repeat_flag": "repeatFlag",
        "view_mode": "viewMode",
        "sort_order": "sortOrder",
        "task_id": "id",
    }
    return {field_map.get(k, k): v for k, v in kwargs.items() if v is not None}


# ── Task Tools ──


@mcp.tool(
    annotations={
        "title": "Create Task",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    }
)
async def dida365_create_task(
    title: str,
    project_id: str,
    content: str | None = None,
    desc: str | None = None,
    start_date: str | None = None,
    due_date: str | None = None,
    priority: int | None = None,
    tags: list[str] | None = None,
    is_all_day: bool | None = None,
    time_zone: str | None = None,
    reminders: list[str] | None = None,
    repeat_flag: str | None = None,
    kind: str | None = None,
    sort_order: int | None = None,
    items: list[dict] | None = None,
) -> str:
    """Create a task. Requires title and project_id.

    Note: repeat_flag (RRULE) requires start_date to be set.

    Args:
        kind: TEXT (default), NOTE, or CHECKLIST. Set to CHECKLIST when passing items.
        sort_order: Display order; lower values appear first.
        items: Subtask list (for CHECKLIST kind). Each dict should contain at least
            "title" (required). Optional keys (camelCase): "status" (0=normal, 1=done),
            "sortOrder", "startDate", "isAllDay", "timeZone".
    """
    try:
        data = _build_data(
            title=title,
            project_id=project_id,
            content=content,
            desc=desc,
            start_date=start_date,
            due_date=due_date,
            priority=priority,
            tags=tags,
            is_all_day=is_all_day,
            time_zone=time_zone,
            reminders=reminders,
            repeat_flag=repeat_flag,
            kind=kind,
            sort_order=sort_order,
            items=items,
        )
        task = await _get_client().create_task(data)
        return _to_json(task)
    except Exception as e:
        return _handle_error(e, "create_task")


@mcp.tool(
    annotations={
        "title": "Batch Create Tasks",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    }
)
async def dida365_batch_create_tasks(tasks: list[dict]) -> str:
    """Batch create multiple tasks in one request.

    Each dict requires "title" and "projectId". Optional fields same as create_task.
    Returns {"id2etag": {...}, "id2error": {...}}.
    """
    try:
        result = await _get_client().batch_create_tasks(tasks)
        return _to_json(result)
    except Exception as e:
        return _handle_error(e, "batch_create_tasks")


@mcp.tool(
    annotations={
        "title": "Batch Update Tasks",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def dida365_batch_update_tasks(tasks: list[dict]) -> str:
    """Batch update multiple tasks in one request.

    Each dict requires "id" and "projectId". Only provided fields are changed.
    Returns {"id2etag": {...}, "id2error": {...}}.
    """
    try:
        result = await _get_client().batch_update_tasks(tasks)
        return _to_json(result)
    except Exception as e:
        return _handle_error(e, "batch_update_tasks")


@mcp.tool(
    annotations={
        "title": "Update Task",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def dida365_update_task(
    task_id: str,
    project_id: str,
    title: str | None = None,
    content: str | None = None,
    desc: str | None = None,
    start_date: str | None = None,
    due_date: str | None = None,
    priority: int | None = None,
    tags: list[str] | None = None,
    is_all_day: bool | None = None,
    time_zone: str | None = None,
    reminders: list[str] | None = None,
    repeat_flag: str | None = None,
    kind: str | None = None,
    sort_order: int | None = None,
    items: list[dict] | None = None,
) -> str:
    """Update a task. Only provided fields are changed; omitted fields remain unchanged.

    Args:
        kind: TEXT, NOTE, or CHECKLIST. Set to CHECKLIST when passing items.
        sort_order: Display order; lower values appear first.
        items: Subtask list (for CHECKLIST kind). Each dict should contain at least
            "title" (required). Optional keys (camelCase): "status" (0=normal, 1=done),
            "sortOrder", "startDate", "isAllDay", "timeZone".
    """
    try:
        data = _build_data(
            task_id=task_id,
            project_id=project_id,
            title=title,
            content=content,
            desc=desc,
            start_date=start_date,
            due_date=due_date,
            priority=priority,
            tags=tags,
            is_all_day=is_all_day,
            time_zone=time_zone,
            reminders=reminders,
            repeat_flag=repeat_flag,
            kind=kind,
            sort_order=sort_order,
            items=items,
        )
        task = await _get_client().update_task(task_id, data)
        return _to_json(task)
    except Exception as e:
        return _handle_error(e, "update_task")


@mcp.tool(
    annotations={
        "title": "Complete Task",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def dida365_complete_task(task_id: str, project_id: str) -> str:
    """Mark a task as completed."""
    try:
        await _get_client().complete_task(project_id, task_id)
        return f"Task {task_id} completed successfully."
    except Exception as e:
        return _handle_error(e, "complete_task")


@mcp.tool(
    annotations={
        "title": "Batch Complete Tasks",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def dida365_batch_complete_tasks(
    project_id: str, task_ids: list[str],
) -> str:
    """Mark multiple tasks in a project as completed."""
    try:
        await _get_client().batch_complete_tasks(project_id, task_ids)
        return f"Completed {len(task_ids)} tasks in project {project_id}."
    except Exception as e:
        return _handle_error(e, "batch_complete_tasks")


@mcp.tool(
    annotations={
        "title": "Delete Task",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def dida365_delete_task(task_id: str, project_id: str) -> str:
    """Permanently delete a task. This action cannot be undone."""
    try:
        await _get_client().delete_task(project_id, task_id)
        return f"Task {task_id} deleted successfully."
    except Exception as e:
        return _handle_error(e, "delete_task")


@mcp.tool(
    annotations={
        "title": "Get Task",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def dida365_get_task(task_id: str, project_id: str) -> str:
    """Get a single task by ID."""
    try:
        task = await _get_client().get_task(project_id, task_id)
        return _to_json(task)
    except Exception as e:
        return _handle_error(e, "get_task")


@mcp.tool(
    annotations={
        "title": "Get Task By ID",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def dida365_get_task_by_id(task_id: str) -> str:
    """Get a task by ID without needing project_id."""
    try:
        task = await _get_client().get_task_by_id(task_id)
        return _to_json(task)
    except Exception as e:
        return _handle_error(e, "get_task_by_id")


@mcp.tool(
    annotations={
        "title": "Move Task",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def dida365_move_task(task_id: str, from_project_id: str, to_project_id: str) -> str:
    """Move a task between projects."""
    try:
        result = await _get_client().move_task(task_id, from_project_id, to_project_id)
        return _to_json(result)
    except Exception as e:
        return _handle_error(e, "move_task")


# ── Query Tools ──


@mcp.tool(
    annotations={
        "title": "List Project Tasks",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def dida365_get_project_tasks(project_id: str) -> str:
    """Get all uncompleted tasks in a project."""
    try:
        data = await _get_client().get_project_with_data(project_id)
        return _to_json(data.tasks or [])
    except Exception as e:
        return _handle_error(e, "get_project_tasks")


@mcp.tool(
    annotations={
        "title": "Filter Tasks",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def dida365_filter_tasks(
    project_ids: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    priority: list[int] | None = None,
    tags: list[str] | None = None,
    status: list[int] | None = None,
) -> str:
    """Filter tasks across projects. All parameters are optional and combinable.

    Tags filter uses AND logic (tasks must match all specified tags).
    """
    try:
        tasks = await _get_client().filter_tasks(
            project_ids=project_ids,
            start_date=start_date,
            end_date=end_date,
            priority=priority,
            tags=tags,
            status=status,
        )
        return _to_json(tasks)
    except Exception as e:
        return _handle_error(e, "filter_tasks")


@mcp.tool(
    annotations={
        "title": "List Completed Tasks",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def dida365_get_completed_tasks(
    project_ids: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """Get completed tasks, optionally filtered by project and completion time range."""
    try:
        tasks = await _get_client().list_completed_tasks(
            project_ids=project_ids,
            start_date=start_date,
            end_date=end_date,
        )
        return _to_json(tasks)
    except Exception as e:
        return _handle_error(e, "get_completed_tasks")


@mcp.tool(
    annotations={
        "title": "List Undone Tasks",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def dida365_list_undone_tasks(
    start_date: str | None = None,
    end_date: str | None = None,
    project_ids: list[str] | None = None,
) -> str:
    """List undone tasks within a date range, optionally filtered by projects."""
    try:
        tasks = await _get_client().list_undone_tasks(
            start_date=start_date,
            end_date=end_date,
            project_ids=project_ids,
        )
        return _to_json(tasks)
    except Exception as e:
        return _handle_error(e, "list_undone_tasks")


# ── Project Tools ──


@mcp.tool(
    annotations={
        "title": "List Projects",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def dida365_list_projects() -> str:
    """List all projects. Call this first to discover project IDs for other operations."""
    try:
        projects = await _get_client().list_projects()
        return _to_json(projects)
    except Exception as e:
        return _handle_error(e, "list_projects")


@mcp.tool(
    annotations={
        "title": "Get Project",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def dida365_get_project(project_id: str) -> str:
    """Get project details by ID."""
    try:
        project = await _get_client().get_project(project_id)
        return _to_json(project)
    except Exception as e:
        return _handle_error(e, "get_project")


@mcp.tool(
    annotations={
        "title": "Create Project",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    }
)
async def dida365_create_project(
    name: str,
    color: str | None = None,
    view_mode: str | None = None,
    kind: str | None = None,
    sort_order: int | None = None,
) -> str:
    """Create a project. view_mode: list|kanban|timeline. kind: TASK|NOTE."""
    try:
        data = _build_data(
            name=name, color=color, view_mode=view_mode, kind=kind, sort_order=sort_order,
        )
        project = await _get_client().create_project(data)
        return _to_json(project)
    except Exception as e:
        return _handle_error(e, "create_project")


@mcp.tool(
    annotations={
        "title": "Update Project",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def dida365_update_project(
    project_id: str,
    name: str | None = None,
    color: str | None = None,
    view_mode: str | None = None,
    kind: str | None = None,
    sort_order: int | None = None,
) -> str:
    """Update a project. Only provided fields are changed."""
    try:
        data = _build_data(
            name=name, color=color, view_mode=view_mode, kind=kind, sort_order=sort_order,
        )
        project = await _get_client().update_project(project_id, data)
        return _to_json(project)
    except Exception as e:
        return _handle_error(e, "update_project")


@mcp.tool(
    annotations={
        "title": "Delete Project",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def dida365_delete_project(project_id: str) -> str:
    """Permanently delete a project and all its tasks. This action cannot be undone."""
    try:
        await _get_client().delete_project(project_id)
        return f"Project {project_id} deleted successfully."
    except Exception as e:
        return _handle_error(e, "delete_project")


# ── Entry point ──


def main() -> None:
    transport = settings.transport.lower()
    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.host, port=settings.port)
    elif transport == "sse":
        mcp.run(transport="sse", host=settings.host, port=settings.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
