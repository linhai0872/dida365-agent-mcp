import httpx
import pytest
import respx

from dida365_agent_mcp.client import Dida365Client
from dida365_agent_mcp.models import Project, ProjectData, Task

BASE_URL_CHINA = "https://api.dida365.com/open/v1"
BASE_URL_INTL = "https://api.ticktick.com/open/v1"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("DIDA365_ACCESS_TOKEN", "test-token")
    monkeypatch.setenv("DIDA365_REGION", "china")
    from dida365_agent_mcp import config

    config.settings = config.Settings()
    return Dida365Client()


@pytest.fixture
def client_intl(monkeypatch):
    monkeypatch.setenv("DIDA365_ACCESS_TOKEN", "test-token")
    monkeypatch.setenv("DIDA365_REGION", "international")
    from dida365_agent_mcp import config

    config.settings = config.Settings()
    return Dida365Client()


SAMPLE_TASK = {
    "id": "task123",
    "projectId": "proj456",
    "title": "Test Task",
    "priority": 1,
    "status": 0,
}

SAMPLE_PROJECT = {
    "id": "proj456",
    "name": "Test Project",
    "color": "#F18181",
    "viewMode": "list",
    "kind": "TASK",
}


# ── Task tests ──


@respx.mock
@pytest.mark.asyncio
async def test_get_task(client):
    # Arrange
    respx.get(f"{BASE_URL_CHINA}/project/proj456/task/task123").mock(
        return_value=httpx.Response(200, json=SAMPLE_TASK)
    )

    # Act
    task = await client.get_task("proj456", "task123")

    # Assert
    assert isinstance(task, Task)
    assert task.id == "task123"
    assert task.title == "Test Task"


@respx.mock
@pytest.mark.asyncio
async def test_create_task(client):
    # Arrange
    respx.post(f"{BASE_URL_CHINA}/task").mock(return_value=httpx.Response(200, json=SAMPLE_TASK))

    # Act
    task = await client.create_task({"title": "Test Task", "projectId": "proj456"})

    # Assert
    assert task.title == "Test Task"
    assert task.projectId == "proj456"


@respx.mock
@pytest.mark.asyncio
async def test_update_task(client):
    # Arrange
    updated = {**SAMPLE_TASK, "title": "Updated Title"}
    respx.post(f"{BASE_URL_CHINA}/task/task123").mock(
        return_value=httpx.Response(200, json=updated)
    )

    # Act
    task = await client.update_task(
        "task123", {"id": "task123", "projectId": "proj456", "title": "Updated Title"}
    )

    # Assert
    assert task.title == "Updated Title"


@respx.mock
@pytest.mark.asyncio
async def test_complete_task(client):
    # Arrange
    respx.post(f"{BASE_URL_CHINA}/project/proj456/task/task123/complete").mock(
        return_value=httpx.Response(200)
    )

    # Act & Assert (no exception)
    await client.complete_task("proj456", "task123")


@respx.mock
@pytest.mark.asyncio
async def test_delete_task(client):
    # Arrange
    respx.delete(f"{BASE_URL_CHINA}/project/proj456/task/task123").mock(
        return_value=httpx.Response(200)
    )

    # Act & Assert
    await client.delete_task("proj456", "task123")


@respx.mock
@pytest.mark.asyncio
async def test_move_task(client):
    # Arrange
    respx.post(f"{BASE_URL_CHINA}/task/move").mock(
        return_value=httpx.Response(200, json=[{"id": "task123", "etag": "abc"}])
    )

    # Act
    result = await client.move_task("task123", "proj1", "proj2")

    # Assert
    assert result[0]["id"] == "task123"


@respx.mock
@pytest.mark.asyncio
async def test_filter_tasks(client):
    # Arrange
    respx.post(f"{BASE_URL_CHINA}/task/filter").mock(
        return_value=httpx.Response(200, json=[SAMPLE_TASK])
    )

    # Act
    tasks = await client.filter_tasks(project_ids=["proj456"], priority=[1])

    # Assert
    assert len(tasks) == 1
    assert tasks[0].priority == 1


@respx.mock
@pytest.mark.asyncio
async def test_list_completed_tasks(client):
    # Arrange
    completed_task = {
        **SAMPLE_TASK,
        "status": 2,
        "completedTime": "2025-03-01T00:00:00+0000",
    }
    respx.post(f"{BASE_URL_CHINA}/task/completed").mock(
        return_value=httpx.Response(200, json=[completed_task])
    )

    # Act
    tasks = await client.list_completed_tasks(project_ids=["proj456"])

    # Assert
    assert len(tasks) == 1
    assert tasks[0].status == 2


@respx.mock
@pytest.mark.asyncio
async def test_get_task_by_id(client):
    # Arrange
    route = respx.post(f"{BASE_URL_CHINA}/task/filter").mock(
        return_value=httpx.Response(200, json=[SAMPLE_TASK])
    )

    # Act
    task = await client.get_task_by_id("task123")

    # Assert
    assert isinstance(task, Task)
    assert task.id == "task123"
    import json

    sent = json.loads(route.calls[0].request.content)
    assert sent == {"ids": ["task123"]}


@respx.mock
@pytest.mark.asyncio
async def test_list_undone_tasks(client):
    # Arrange
    route = respx.post(f"{BASE_URL_CHINA}/task/undone").mock(
        return_value=httpx.Response(200, json=[SAMPLE_TASK])
    )

    # Act
    tasks = await client.list_undone_tasks(
        start_date="2025-03-01T00:00:00+0000",
        end_date="2025-03-15T00:00:00+0000",
    )

    # Assert
    assert len(tasks) == 1
    assert isinstance(tasks[0], Task)
    import json

    sent = json.loads(route.calls[0].request.content)
    assert "startDate" in sent
    assert "endDate" in sent


@respx.mock
@pytest.mark.asyncio
async def test_batch_create_tasks(client):
    # Arrange
    batch_resp = {"id2etag": {"t1": "e1"}, "id2error": {}}
    route = respx.post(f"{BASE_URL_CHINA}/task/batch").mock(
        return_value=httpx.Response(200, json=batch_resp)
    )

    # Act
    result = await client.batch_create_tasks(
        [{"title": "Task 1", "projectId": "proj456"}]
    )

    # Assert
    assert result == batch_resp
    import json

    sent = json.loads(route.calls[0].request.content)
    assert "add" in sent


@respx.mock
@pytest.mark.asyncio
async def test_batch_update_tasks(client):
    # Arrange
    batch_resp = {"id2etag": {"t1": "e1"}, "id2error": {}}
    route = respx.post(f"{BASE_URL_CHINA}/task/batch").mock(
        return_value=httpx.Response(200, json=batch_resp)
    )

    # Act
    result = await client.batch_update_tasks(
        [{"id": "task123", "projectId": "proj456", "title": "Updated"}]
    )

    # Assert
    assert result == batch_resp
    import json

    sent = json.loads(route.calls[0].request.content)
    assert "update" in sent


@respx.mock
@pytest.mark.asyncio
async def test_batch_complete_tasks(client):
    # Arrange
    route = respx.post(f"{BASE_URL_CHINA}/task/complete").mock(
        return_value=httpx.Response(200)
    )

    # Act & Assert (no exception)
    await client.batch_complete_tasks("proj456", ["task1", "task2"])

    import json

    sent = json.loads(route.calls[0].request.content)
    assert sent["projectId"] == "proj456"
    assert sent["taskIds"] == ["task1", "task2"]


# ── Project tests ──


@respx.mock
@pytest.mark.asyncio
async def test_list_projects(client):
    # Arrange
    respx.get(f"{BASE_URL_CHINA}/project").mock(
        return_value=httpx.Response(200, json=[SAMPLE_PROJECT])
    )

    # Act
    projects = await client.list_projects()

    # Assert
    assert len(projects) == 1
    assert projects[0].name == "Test Project"


@respx.mock
@pytest.mark.asyncio
async def test_get_project(client):
    # Arrange
    respx.get(f"{BASE_URL_CHINA}/project/proj456").mock(
        return_value=httpx.Response(200, json=SAMPLE_PROJECT)
    )

    # Act
    project = await client.get_project("proj456")

    # Assert
    assert isinstance(project, Project)
    assert project.id == "proj456"


@respx.mock
@pytest.mark.asyncio
async def test_get_project_with_data(client):
    # Arrange
    project_data = {
        "project": SAMPLE_PROJECT,
        "tasks": [SAMPLE_TASK],
        "columns": [],
    }
    respx.get(f"{BASE_URL_CHINA}/project/proj456/data").mock(
        return_value=httpx.Response(200, json=project_data)
    )

    # Act
    data = await client.get_project_with_data("proj456")

    # Assert
    assert isinstance(data, ProjectData)
    assert data.project.name == "Test Project"
    assert len(data.tasks) == 1


@respx.mock
@pytest.mark.asyncio
async def test_create_project(client):
    # Arrange
    respx.post(f"{BASE_URL_CHINA}/project").mock(
        return_value=httpx.Response(200, json=SAMPLE_PROJECT)
    )

    # Act
    project = await client.create_project({"name": "Test Project"})

    # Assert
    assert project.name == "Test Project"


@respx.mock
@pytest.mark.asyncio
async def test_delete_project(client):
    # Arrange
    respx.delete(f"{BASE_URL_CHINA}/project/proj456").mock(return_value=httpx.Response(200))

    # Act & Assert
    await client.delete_project("proj456")


# ── Error handling ──


@respx.mock
@pytest.mark.asyncio
async def test_api_error_raises(client):
    # Arrange
    respx.get(f"{BASE_URL_CHINA}/project").mock(
        return_value=httpx.Response(401, json={"error": "unauthorized"})
    )

    # Act & Assert
    with pytest.raises(httpx.HTTPStatusError):
        await client.list_projects()


# ── International region tests ──


@respx.mock
@pytest.mark.asyncio
async def test_intl_list_projects(client_intl):
    # Arrange
    respx.get(f"{BASE_URL_INTL}/project").mock(
        return_value=httpx.Response(200, json=[SAMPLE_PROJECT])
    )

    # Act
    projects = await client_intl.list_projects()

    # Assert
    assert len(projects) == 1
    assert projects[0].name == "Test Project"


@respx.mock
@pytest.mark.asyncio
async def test_create_task_with_items(client):
    # Arrange
    subtasks = [{"title": "Step 1", "status": 0, "sortOrder": 0}]
    response_data = {**SAMPLE_TASK, "kind": "CHECKLIST", "items": subtasks}
    route = respx.post(f"{BASE_URL_CHINA}/task").mock(
        return_value=httpx.Response(200, json=response_data)
    )

    # Act
    task = await client.create_task(
        {"title": "Test Task", "projectId": "proj456", "kind": "CHECKLIST", "items": subtasks}
    )

    # Assert
    assert task.kind == "CHECKLIST"
    assert len(task.items) == 1
    assert task.items[0].title == "Step 1"
    sent_body = route.calls[0].request.content
    import json

    sent = json.loads(sent_body)
    assert sent["kind"] == "CHECKLIST"
    assert sent["items"] == subtasks


@respx.mock
@pytest.mark.asyncio
async def test_create_task_with_sort_order(client):
    # Arrange
    response_data = {**SAMPLE_TASK, "sortOrder": 99}
    route = respx.post(f"{BASE_URL_CHINA}/task").mock(
        return_value=httpx.Response(200, json=response_data)
    )

    # Act
    task = await client.create_task(
        {"title": "Test Task", "projectId": "proj456", "sortOrder": 99}
    )

    # Assert
    assert task.sortOrder == 99
    import json

    sent = json.loads(route.calls[0].request.content)
    assert sent["sortOrder"] == 99


@respx.mock
@pytest.mark.asyncio
async def test_intl_create_task(client_intl):
    # Arrange
    respx.post(f"{BASE_URL_INTL}/task").mock(return_value=httpx.Response(200, json=SAMPLE_TASK))

    # Act
    task = await client_intl.create_task({"title": "Test Task", "projectId": "proj456"})

    # Assert
    assert task.title == "Test Task"
