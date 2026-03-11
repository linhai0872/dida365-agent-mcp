from __future__ import annotations

import logging
from typing import Any

import httpx

from . import config
from .auth import get_access_token
from .models import Project, ProjectData, Task

logger = logging.getLogger(__name__)


class Dida365Client:
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            token = get_access_token()
            self._client = httpx.AsyncClient(
                base_url=config.settings.api_base_url,
                headers={"Authorization": f"Bearer {token}"},
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

    # ── Task endpoints ──

    async def get_task(self, project_id: str, task_id: str) -> Task:
        resp = await self._request("GET", f"/project/{project_id}/task/{task_id}")
        return Task.model_validate(resp.json())

    async def create_task(self, data: dict[str, Any]) -> Task:
        resp = await self._request("POST", "/task", json=data)
        return Task.model_validate(resp.json())

    async def update_task(self, task_id: str, data: dict[str, Any]) -> Task:
        resp = await self._request("POST", f"/task/{task_id}", json=data)
        return Task.model_validate(resp.json())

    async def complete_task(self, project_id: str, task_id: str) -> None:
        await self._request("POST", f"/project/{project_id}/task/{task_id}/complete")

    async def delete_task(self, project_id: str, task_id: str) -> None:
        await self._request("DELETE", f"/project/{project_id}/task/{task_id}")

    async def move_task(
        self, task_id: str, from_project_id: str, to_project_id: str
    ) -> list[dict]:
        resp = await self._request(
            "POST",
            "/task/move",
            json=[
                {
                    "taskId": task_id,
                    "fromProjectId": from_project_id,
                    "toProjectId": to_project_id,
                }
            ],
        )
        return resp.json()

    async def list_completed_tasks(
        self,
        project_ids: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[Task]:
        body: dict[str, Any] = {}
        if project_ids:
            body["projectIds"] = project_ids
        if start_date:
            body["startDate"] = start_date
        if end_date:
            body["endDate"] = end_date
        resp = await self._request("POST", "/task/completed", json=body)
        return [Task.model_validate(t) for t in resp.json()]

    async def filter_tasks(
        self,
        project_ids: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        priority: list[int] | None = None,
        tags: list[str] | None = None,
        status: list[int] | None = None,
    ) -> list[Task]:
        body: dict[str, Any] = {}
        if project_ids:
            body["projectIds"] = project_ids
        if start_date:
            body["startDate"] = start_date
        if end_date:
            body["endDate"] = end_date
        if priority is not None:
            body["priority"] = priority
        if tags:
            body["tag"] = tags
        if status is not None:
            body["status"] = status
        resp = await self._request("POST", "/task/filter", json=body)
        return [Task.model_validate(t) for t in resp.json()]

    # ── Project endpoints ──

    async def list_projects(self) -> list[Project]:
        resp = await self._request("GET", "/project")
        return [Project.model_validate(p) for p in resp.json()]

    async def get_project(self, project_id: str) -> Project:
        resp = await self._request("GET", f"/project/{project_id}")
        return Project.model_validate(resp.json())

    async def get_project_with_data(self, project_id: str) -> ProjectData:
        resp = await self._request("GET", f"/project/{project_id}/data")
        return ProjectData.model_validate(resp.json())

    async def create_project(self, data: dict[str, Any]) -> Project:
        resp = await self._request("POST", "/project", json=data)
        return Project.model_validate(resp.json())

    async def update_project(self, project_id: str, data: dict[str, Any]) -> Project:
        resp = await self._request("POST", f"/project/{project_id}", json=data)
        return Project.model_validate(resp.json())

    async def delete_project(self, project_id: str) -> None:
        await self._request("DELETE", f"/project/{project_id}")
