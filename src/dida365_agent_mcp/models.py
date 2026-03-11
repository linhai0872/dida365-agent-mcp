from __future__ import annotations

from pydantic import BaseModel, Field


class ChecklistItem(BaseModel):
    id: str | None = None
    title: str | None = None
    status: int | None = Field(None, description="0=Normal, 1=Completed")
    completedTime: str | None = None
    isAllDay: bool | None = None
    sortOrder: int | None = None
    startDate: str | None = None
    timeZone: str | None = None


class Task(BaseModel):
    id: str | None = None
    projectId: str | None = None
    title: str | None = None
    content: str | None = None
    desc: str | None = None
    isAllDay: bool | None = None
    startDate: str | None = None
    dueDate: str | None = None
    timeZone: str | None = None
    reminders: list[str] | None = None
    repeatFlag: str | None = None
    priority: int | None = Field(None, description="0=None, 1=Low, 3=Medium, 5=High")
    status: int | None = Field(None, description="0=Normal, 2=Completed")
    completedTime: str | None = None
    sortOrder: int | None = None
    items: list[ChecklistItem] | None = None
    tags: list[str] | None = None
    kind: str | None = Field(None, description="TEXT, NOTE, or CHECKLIST")
    etag: str | None = None


class Project(BaseModel):
    id: str | None = None
    name: str | None = None
    color: str | None = None
    sortOrder: int | None = None
    closed: bool | None = None
    groupId: str | None = None
    viewMode: str | None = Field(None, description="list, kanban, or timeline")
    permission: str | None = Field(None, description="read, write, or comment")
    kind: str | None = Field(None, description="TASK or NOTE")


class Column(BaseModel):
    id: str | None = None
    projectId: str | None = None
    name: str | None = None
    sortOrder: int | None = None


class ProjectData(BaseModel):
    project: Project | None = None
    tasks: list[Task] | None = None
    columns: list[Column] | None = None
