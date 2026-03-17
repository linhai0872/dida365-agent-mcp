from __future__ import annotations

import json
import logging
from typing import Any

from fastmcp import FastMCP

from .client_v2 import Dida365V2Client

logger = logging.getLogger(__name__)

_v2_client: Dida365V2Client | None = None


def _get_v2_client() -> Dida365V2Client:
    if _v2_client is None:
        raise RuntimeError("V2 client not initialized. Set DIDA365_V2_SESSION_TOKEN.")
    return _v2_client


def init_v2_client(client: Dida365V2Client) -> None:
    global _v2_client
    _v2_client = client


def _to_json(obj: Any) -> str:
    if hasattr(obj, "model_dump"):
        return json.dumps(obj.model_dump(exclude_none=True), ensure_ascii=False, indent=2)
    if isinstance(obj, list):
        items = [i.model_dump(exclude_none=True) if hasattr(i, "model_dump") else i for i in obj]
        return json.dumps(items, ensure_ascii=False, indent=2)
    return json.dumps(obj, ensure_ascii=False, indent=2)


def _handle_error(e: Exception, operation: str = "") -> str:
    import httpx

    logger.exception("V2 operation failed: %s", operation or "unknown")

    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        body = e.response.text
        messages = {
            401: "Unauthorized. V2 session token may have expired. Re-copy from browser DevTools.",
            403: "Forbidden. Insufficient permission for this resource.",
            404: "Not found. Verify the resource ID is valid.",
            429: "Rate limited. Wait 30-60s before retrying.",
        }
        msg = messages.get(status, f"API error (HTTP {status})")
        return f"Error: {msg}\nDetails: {body}"
    if isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. Try again."
    if isinstance(e, RuntimeError):
        return f"Error: {e}"
    return f"Error: {type(e).__name__}: {e}"


# ── Tag Tools ──


def register_v2_tools(mcp: FastMCP) -> None:

    @mcp.tool(
        annotations={
            "title": "List Tags (V2)",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def dida365_list_tags() -> str:
        """List all tags. Requires V2 session token."""
        try:
            tags = await _get_v2_client().list_tags()
            return _to_json(tags)
        except Exception as e:
            return _handle_error(e, "list_tags")

    @mcp.tool(
        annotations={
            "title": "Create Tags (V2)",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        }
    )
    async def dida365_create_tags(tags: list[dict]) -> str:
        """Batch create tags.

        Each dict should have "name" (required), optional: "label", "color",
        "sortOrder", "parent". Returns raw batch result.
        """
        try:
            result = await _get_v2_client().create_tags(tags)
            return _to_json(result)
        except Exception as e:
            return _handle_error(e, "create_tags")

    @mcp.tool(
        annotations={
            "title": "Update Tags (V2)",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def dida365_update_tags(tags: list[dict]) -> str:
        """Batch update tags. Each dict should have "name" (required) plus fields to update.

        Returns raw batch result.
        """
        try:
            result = await _get_v2_client().update_tags(tags)
            return _to_json(result)
        except Exception as e:
            return _handle_error(e, "update_tags")

    @mcp.tool(
        annotations={
            "title": "Delete Tags Batch (V2)",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def dida365_delete_tags(tags: list[dict]) -> str:
        """Batch delete tags. Each dict should have "name".

        Returns raw batch result.
        """
        try:
            result = await _get_v2_client().delete_tags(tags)
            return _to_json(result)
        except Exception as e:
            return _handle_error(e, "delete_tags")

    @mcp.tool(
        annotations={
            "title": "Delete Tag (V2)",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def dida365_delete_tag(name: str) -> str:
        """Delete a single tag by name."""
        try:
            await _get_v2_client().delete_tag(name)
            return f"Tag '{name}' deleted successfully."
        except Exception as e:
            return _handle_error(e, "delete_tag")

    # ── Parent/Child Task Tools ──

    @mcp.tool(
        annotations={
            "title": "Set Task Parent (V2)",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def dida365_set_task_parent(task_id: str, parent_id: str) -> str:
        """Set a task's parent to create a subtask relationship."""
        try:
            result = await _get_v2_client().set_task_parent(task_id, parent_id)
            return _to_json(result)
        except Exception as e:
            return _handle_error(e, "set_task_parent")

    @mcp.tool(
        annotations={
            "title": "Unset Task Parent (V2)",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def dida365_unset_task_parent(task_id: str) -> str:
        """Remove a task's parent, making it a top-level task."""
        try:
            result = await _get_v2_client().unset_task_parent(task_id)
            return _to_json(result)
        except Exception as e:
            return _handle_error(e, "unset_task_parent")

    @mcp.tool(
        annotations={
            "title": "Pin Task (V2)",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def dida365_pin_task(task_id: str, pinned: bool) -> str:
        """Pin or unpin a task."""
        try:
            client = await _get_v2_client()._get_client()
            resp = await client.request(
                "POST", f"/task/{task_id}", json={"pinned": pinned}
            )
            resp.raise_for_status()
            return _to_json(resp.json())
        except Exception as e:
            return _handle_error(e, "pin_task")

    # ── Habit Tools ──

    @mcp.tool(
        annotations={
            "title": "List Habits (V2)",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def dida365_list_habits() -> str:
        """List all habits. Requires V2 session token."""
        try:
            habits = await _get_v2_client().list_habits()
            return _to_json(habits)
        except Exception as e:
            return _handle_error(e, "list_habits")

    @mcp.tool(
        annotations={
            "title": "Create Habit (V2)",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        }
    )
    async def dida365_create_habit(habits: list[dict]) -> str:
        """Batch create habits. Each dict should have "name" (required).

        Optional fields: "color", "iconRes", "encouragement", "goal", "step", "unit",
        "repeatRule", "reminders", "sectionId", "sortOrder".
        Returns raw batch result.
        """
        try:
            result = await _get_v2_client().create_habit(habits)
            return _to_json(result)
        except Exception as e:
            return _handle_error(e, "create_habit")

    @mcp.tool(
        annotations={
            "title": "Update Habit (V2)",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def dida365_update_habit(habits: list[dict]) -> str:
        """Batch update habits. Each dict should have "id" (required) plus fields to update.

        Returns raw batch result.
        """
        try:
            result = await _get_v2_client().update_habit(habits)
            return _to_json(result)
        except Exception as e:
            return _handle_error(e, "update_habit")

    @mcp.tool(
        annotations={
            "title": "Delete Habit (V2)",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def dida365_delete_habit(habits: list[dict]) -> str:
        """Batch delete habits. Each dict should have "id".

        Returns raw batch result.
        """
        try:
            result = await _get_v2_client().delete_habit(habits)
            return _to_json(result)
        except Exception as e:
            return _handle_error(e, "delete_habit")

    @mcp.tool(
        annotations={
            "title": "Checkin Habit (V2)",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        }
    )
    async def dida365_checkin_habit(
        habit_id: str,
        checkin_stamp: str,
        status: int = 2,
        value: float | None = None,
        goal: int | None = None,
    ) -> str:
        """Check in a habit for a specific date.

        Args:
            habit_id: The habit ID.
            checkin_stamp: Date stamp in YYYYMMDD format (e.g. "20250315").
            status: 0=unchecked, 2=checked. Defaults to 2.
            value: Current value for measurable habits.
            goal: Target goal for this checkin.
        """
        try:
            data: dict[str, Any] = {
                "habitId": habit_id,
                "checkinStamp": checkin_stamp,
                "status": status,
            }
            if value is not None:
                data["value"] = value
            if goal is not None:
                data["goal"] = goal
            result = await _get_v2_client().checkin_habit(data)
            return _to_json(result)
        except Exception as e:
            return _handle_error(e, "checkin_habit")

    @mcp.tool(
        annotations={
            "title": "Undo Habit Checkin (V2)",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def dida365_undo_checkin(habit_id: str, checkin_stamp: str) -> str:
        """Undo a habit checkin for a specific date.

        Args:
            habit_id: The habit ID.
            checkin_stamp: Date stamp in YYYYMMDD format (e.g. "20250315").
        """
        try:
            await _get_v2_client().undo_checkin(habit_id, checkin_stamp)
            return f"Checkin for habit {habit_id} on {checkin_stamp} undone."
        except Exception as e:
            return _handle_error(e, "undo_checkin")

    @mcp.tool(
        annotations={
            "title": "List Habit Checkins (V2)",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def dida365_list_habit_checkins(
        habit_id: str, after_stamp: str | None = None,
    ) -> str:
        """List checkin records for a habit.

        Args:
            habit_id: The habit ID.
            after_stamp: Optional. Only return checkins after this stamp (YYYYMMDD).
        """
        try:
            checkins = await _get_v2_client().list_habit_checkins(habit_id, after_stamp)
            return _to_json(checkins)
        except Exception as e:
            return _handle_error(e, "list_habit_checkins")

    @mcp.tool(
        annotations={
            "title": "List Habit Sections (V2)",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def dida365_list_habit_sections() -> str:
        """List all habit sections/groups."""
        try:
            sections = await _get_v2_client().list_habit_sections()
            return _to_json(sections)
        except Exception as e:
            return _handle_error(e, "list_habit_sections")

    # ── Folder Tools ──

    @mcp.tool(
        annotations={
            "title": "List Folders (V2)",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def dida365_list_folders() -> str:
        """List all project folders (groups)."""
        try:
            folders = await _get_v2_client().list_folders()
            return _to_json(folders)
        except Exception as e:
            return _handle_error(e, "list_folders")

    @mcp.tool(
        annotations={
            "title": "Create Folder (V2)",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        }
    )
    async def dida365_create_folder(
        name: str, sort_order: int | None = None,
    ) -> str:
        """Create a project folder.

        Args:
            name: Folder name.
            sort_order: Display order; lower values appear first.
        """
        try:
            data: dict[str, Any] = {"name": name}
            if sort_order is not None:
                data["sortOrder"] = sort_order
            folder = await _get_v2_client().create_folder(data)
            return _to_json(folder)
        except Exception as e:
            return _handle_error(e, "create_folder")

    @mcp.tool(
        annotations={
            "title": "Update Folder (V2)",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def dida365_update_folder(
        folder_id: str,
        name: str | None = None,
        sort_order: int | None = None,
    ) -> str:
        """Update a project folder. Only provided fields are changed.

        Args:
            folder_id: The folder ID.
            name: New folder name.
            sort_order: New display order.
        """
        try:
            data: dict[str, Any] = {}
            if name is not None:
                data["name"] = name
            if sort_order is not None:
                data["sortOrder"] = sort_order
            folder = await _get_v2_client().update_folder(folder_id, data)
            return _to_json(folder)
        except Exception as e:
            return _handle_error(e, "update_folder")

    @mcp.tool(
        annotations={
            "title": "Delete Folder (V2)",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": True,
        }
    )
    async def dida365_delete_folder(folder_id: str) -> str:
        """Delete a project folder. Projects in the folder are not deleted."""
        try:
            await _get_v2_client().delete_folder(folder_id)
            return f"Folder {folder_id} deleted successfully."
        except Exception as e:
            return _handle_error(e, "delete_folder")
