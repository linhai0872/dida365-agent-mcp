from __future__ import annotations

import logging
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
