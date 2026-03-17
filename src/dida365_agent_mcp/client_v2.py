from __future__ import annotations

import json as _json
import logging
import os
import time
from typing import Any

import httpx

from .models import (
    Habit,
    HabitCheckin,
    HabitSection,
    ProjectGroup,
    Tag,
)

logger = logging.getLogger(__name__)

_DEFAULT_USER_AGENT = "Mozilla/5.0 (rv:145.0) Firefox/145.0"


def _generate_device_id() -> str:
    timestamp = int(time.time()).to_bytes(4, "big")
    random_bytes = os.urandom(5)
    counter = os.urandom(3)
    return (timestamp + random_bytes + counter).hex()


async def signon(
    base_url: str,
    username: str,
    password: str,
) -> str:
    """Auto-login via username/password, returns session token.

    Raises httpx.HTTPStatusError on auth failure (wrong credentials, 2FA required, etc).
    """
    device_header = _json.dumps(
        {"platform": "web", "version": 6430, "id": _generate_device_id()}
    )
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{base_url}/user/signon",
            params={"wc": "true", "remember": "true"},
            json={"username": username, "password": password},
            headers={
                "User-Agent": _DEFAULT_USER_AGENT,
                "X-Device": device_header,
            },
        )
        resp.raise_for_status()
        data = resp.json()
    if "token" not in data:
        raise RuntimeError(
            "Login requires 2FA. Use DIDA365_V2_SESSION_TOKEN instead."
        )
    return data["token"]


class Dida365V2Client:
    def __init__(self, session_token: str, base_url: str) -> None:
        self._client: httpx.AsyncClient | None = None
        self._session_token = session_token
        self._base_url = base_url

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers={"Cookie": f"t={self._session_token}"},
                timeout=30.0,
            )
        return self._client

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        client = await self._get_client()
        resp = await client.request(method, path, **kwargs)
        resp.raise_for_status()
        return resp

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ── Tags ──

    async def list_tags(self) -> list[Tag]:
        resp = await self._request("GET", "/tags")
        return [Tag.model_validate(t) for t in resp.json()]

    async def create_tags(self, tags: list[dict[str, Any]]) -> dict:
        resp = await self._request("POST", "/batch/tag", json={"add": tags})
        return resp.json()

    async def update_tags(self, tags: list[dict[str, Any]]) -> dict:
        resp = await self._request("POST", "/batch/tag", json={"update": tags})
        return resp.json()

    async def delete_tags(self, tags: list[dict[str, Any]]) -> dict:
        resp = await self._request("POST", "/batch/tag", json={"delete": tags})
        return resp.json()

    async def delete_tag(self, name: str) -> None:
        await self._request("DELETE", f"/tag/{name}")

    # ── Parent/Child Tasks ──

    async def set_task_parent(self, task_id: str, parent_id: str) -> dict:
        resp = await self._request(
            "POST", f"/task/{task_id}/parent", json={"parentId": parent_id}
        )
        return resp.json()

    async def unset_task_parent(self, task_id: str) -> dict:
        resp = await self._request(
            "POST", f"/task/{task_id}/parent", json={"parentId": None}
        )
        return resp.json()

    # ── Habits ──

    async def list_habits(self) -> list[Habit]:
        resp = await self._request("GET", "/habits")
        return [Habit.model_validate(h) for h in resp.json()]

    async def create_habit(self, habits: list[dict[str, Any]]) -> dict:
        resp = await self._request("POST", "/batch/habit", json={"add": habits})
        return resp.json()

    async def update_habit(self, habits: list[dict[str, Any]]) -> dict:
        resp = await self._request("POST", "/batch/habit", json={"update": habits})
        return resp.json()

    async def delete_habit(self, habits: list[dict[str, Any]]) -> dict:
        resp = await self._request("POST", "/batch/habit", json={"delete": habits})
        return resp.json()

    async def checkin_habit(self, checkin: dict[str, Any]) -> dict:
        resp = await self._request("POST", "/habitCheckins", json=checkin)
        return resp.json()

    async def undo_checkin(self, habit_id: str, checkin_stamp: str) -> None:
        await self._request(
            "DELETE", "/habitCheckins",
            params={"habitId": habit_id, "stamp": checkin_stamp},
        )

    async def list_habit_checkins(
        self, habit_id: str, after_stamp: str | None = None,
    ) -> list[HabitCheckin]:
        params: dict[str, str] = {"habitId": habit_id}
        if after_stamp:
            params["afterStamp"] = after_stamp
        resp = await self._request("GET", "/habitCheckins", params=params)
        return [HabitCheckin.model_validate(c) for c in resp.json()]

    async def list_habit_sections(self) -> list[HabitSection]:
        resp = await self._request("GET", "/habitSections")
        return [HabitSection.model_validate(s) for s in resp.json()]

    # ── Pin ──

    async def pin_task(self, task_id: str, pinned: bool) -> dict:
        resp = await self._request("POST", f"/task/{task_id}", json={"pinned": pinned})
        if resp.text:
            return resp.json()
        return {"pinned": pinned}

    # ── Search ──

    async def search_tasks(
        self,
        keywords: str,
        *,
        project_ids: list[str] | None = None,
        tags: list[str] | None = None,
        statuses: list[int] | None = None,
        due_from: int | None = None,
        due_to: int | None = None,
    ) -> dict:
        params: list[tuple[str, str]] = [("keywords", keywords)]
        if project_ids:
            params.extend(("projectId", pid) for pid in project_ids)
        if tags:
            params.extend(("tags", t) for t in tags)
        if statuses is not None:
            params.extend(("status", str(s)) for s in statuses)
        if due_from is not None:
            params.append(("dueFrom", str(due_from)))
        if due_to is not None:
            params.append(("dueTo", str(due_to)))
        resp = await self._request("GET", "/search/all", params=params)
        return resp.json()

    # ── Folders (ProjectGroups) ──

    async def list_folders(self) -> list[ProjectGroup]:
        resp = await self._request("GET", "/projectGroups")
        return [ProjectGroup.model_validate(g) for g in resp.json()]

    async def create_folder(self, data: dict[str, Any]) -> ProjectGroup:
        resp = await self._request("POST", "/projectGroup", json=data)
        return ProjectGroup.model_validate(resp.json())

    async def update_folder(self, folder_id: str, data: dict[str, Any]) -> ProjectGroup:
        resp = await self._request("PUT", f"/projectGroup/{folder_id}", json=data)
        return ProjectGroup.model_validate(resp.json())

    async def delete_folder(self, folder_id: str) -> None:
        await self._request("DELETE", f"/projectGroup/{folder_id}")
