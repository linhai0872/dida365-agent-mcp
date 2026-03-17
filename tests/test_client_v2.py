import httpx
import pytest
import respx

from dida365_agent_mcp.client_v2 import Dida365V2Client, signon
from dida365_agent_mcp.models import (
    Habit,
    HabitCheckin,
    HabitSection,
    ProjectGroup,
    Tag,
)

BASE_URL_CHINA = "https://api.dida365.com/api/v2"
BASE_URL_INTL = "https://api.ticktick.com/api/v2"

SAMPLE_TAG = {"name": "work", "label": "Work", "color": "#FF0000", "sortOrder": 0}
SAMPLE_HABIT = {"id": "h1", "name": "Read", "status": 0, "goal": 30, "unit": "min"}
SAMPLE_CHECKIN = {
    "id": "c1",
    "habitId": "h1",
    "checkinStamp": "20250315",
    "status": 2,
    "value": 30.0,
}
SAMPLE_SECTION = {"id": "s1", "name": "Morning", "sortOrder": 0}
SAMPLE_FOLDER = {"id": "g1", "name": "Personal", "sortOrder": 0}


@pytest.fixture
def client():
    return Dida365V2Client(session_token="test-token", base_url=BASE_URL_CHINA)


@pytest.fixture
def client_intl():
    return Dida365V2Client(session_token="test-token", base_url=BASE_URL_INTL)


# ── Tag tests ──


@respx.mock
@pytest.mark.asyncio
async def test_list_tags(client):
    # Arrange
    respx.get(f"{BASE_URL_CHINA}/tags").mock(
        return_value=httpx.Response(200, json=[SAMPLE_TAG])
    )

    # Act
    tags = await client.list_tags()

    # Assert
    assert len(tags) == 1
    assert isinstance(tags[0], Tag)
    assert tags[0].name == "work"


@respx.mock
@pytest.mark.asyncio
async def test_create_tags(client):
    # Arrange
    batch_resp = {"id2etag": {"work": "e1"}, "id2error": {}}
    route = respx.post(f"{BASE_URL_CHINA}/batch/tag").mock(
        return_value=httpx.Response(200, json=batch_resp)
    )

    # Act
    result = await client.create_tags([{"name": "work"}])

    # Assert
    assert result == batch_resp
    import json

    sent = json.loads(route.calls[0].request.content)
    assert "add" in sent


@respx.mock
@pytest.mark.asyncio
async def test_update_tags(client):
    # Arrange
    batch_resp = {"id2etag": {"work": "e2"}, "id2error": {}}
    route = respx.post(f"{BASE_URL_CHINA}/batch/tag").mock(
        return_value=httpx.Response(200, json=batch_resp)
    )

    # Act
    result = await client.update_tags([{"name": "work", "color": "#00FF00"}])

    # Assert
    assert result == batch_resp
    import json

    sent = json.loads(route.calls[0].request.content)
    assert "update" in sent


@respx.mock
@pytest.mark.asyncio
async def test_delete_tags(client):
    # Arrange
    batch_resp = {"id2etag": {}, "id2error": {}}
    route = respx.post(f"{BASE_URL_CHINA}/batch/tag").mock(
        return_value=httpx.Response(200, json=batch_resp)
    )

    # Act
    await client.delete_tags([{"name": "work"}])

    # Assert
    import json

    sent = json.loads(route.calls[0].request.content)
    assert "delete" in sent


@respx.mock
@pytest.mark.asyncio
async def test_delete_tag(client):
    # Arrange
    respx.delete(f"{BASE_URL_CHINA}/tag/work").mock(
        return_value=httpx.Response(200)
    )

    # Act & Assert (no exception)
    await client.delete_tag("work")


# ── Parent/Child tests ──


# ── Search tests ──


@respx.mock
@pytest.mark.asyncio
async def test_search_tasks_keywords_only(client):
    # Arrange
    search_resp = {"data": {"tasks": [{"id": "t1", "title": "Test"}], "comments": {}}}
    route = respx.get(f"{BASE_URL_CHINA}/search/all").mock(
        return_value=httpx.Response(200, json=search_resp)
    )

    # Act
    result = await client.search_tasks("Test")

    # Assert
    assert result == search_resp
    assert route.calls[0].request.url.params["keywords"] == "Test"


@respx.mock
@pytest.mark.asyncio
async def test_search_tasks_all_filters(client):
    # Arrange
    search_resp = {"data": {"tasks": [], "comments": {}}}
    route = respx.get(f"{BASE_URL_CHINA}/search/all").mock(
        return_value=httpx.Response(200, json=search_resp)
    )

    # Act
    result = await client.search_tasks(
        "meeting",
        project_ids=["p1", "p2"],
        tags=["work"],
        statuses=[0, 2],
        due_from=1000000,
        due_to=2000000,
    )

    # Assert
    assert result == search_resp
    params = str(route.calls[0].request.url)
    assert "keywords=meeting" in params
    assert "projectId=p1" in params
    assert "projectId=p2" in params
    assert "tags=work" in params
    assert "status=0" in params
    assert "status=2" in params
    assert "dueFrom=1000000" in params
    assert "dueTo=2000000" in params


# ── Parent/Child tests ──


@respx.mock
@pytest.mark.asyncio
async def test_set_task_parent(client):
    # Arrange
    respx.post(f"{BASE_URL_CHINA}/task/t1/parent").mock(
        return_value=httpx.Response(200, json={"id": "t1", "parentId": "p1"})
    )

    # Act
    result = await client.set_task_parent("t1", "p1")

    # Assert
    assert result["parentId"] == "p1"


@respx.mock
@pytest.mark.asyncio
async def test_unset_task_parent(client):
    # Arrange
    route = respx.post(f"{BASE_URL_CHINA}/task/t1/parent").mock(
        return_value=httpx.Response(200, json={"id": "t1", "parentId": None})
    )

    # Act
    result = await client.unset_task_parent("t1")

    # Assert
    assert result["parentId"] is None
    import json

    sent = json.loads(route.calls[0].request.content)
    assert sent["parentId"] is None


# ── Habit tests ──


@respx.mock
@pytest.mark.asyncio
async def test_list_habits(client):
    # Arrange
    respx.get(f"{BASE_URL_CHINA}/habits").mock(
        return_value=httpx.Response(200, json=[SAMPLE_HABIT])
    )

    # Act
    habits = await client.list_habits()

    # Assert
    assert len(habits) == 1
    assert isinstance(habits[0], Habit)
    assert habits[0].name == "Read"


@respx.mock
@pytest.mark.asyncio
async def test_create_habit(client):
    # Arrange
    batch_resp = {"id2etag": {"h1": "e1"}, "id2error": {}}
    route = respx.post(f"{BASE_URL_CHINA}/batch/habit").mock(
        return_value=httpx.Response(200, json=batch_resp)
    )

    # Act
    result = await client.create_habit([{"name": "Read"}])

    # Assert
    assert result == batch_resp
    import json

    sent = json.loads(route.calls[0].request.content)
    assert "add" in sent


@respx.mock
@pytest.mark.asyncio
async def test_delete_habit(client):
    # Arrange
    batch_resp = {"id2etag": {}, "id2error": {}}
    route = respx.post(f"{BASE_URL_CHINA}/batch/habit").mock(
        return_value=httpx.Response(200, json=batch_resp)
    )

    # Act
    await client.delete_habit([{"id": "h1"}])

    # Assert
    import json

    sent = json.loads(route.calls[0].request.content)
    assert "delete" in sent


@respx.mock
@pytest.mark.asyncio
async def test_checkin_habit(client):
    # Arrange
    respx.post(f"{BASE_URL_CHINA}/habitCheckins").mock(
        return_value=httpx.Response(200, json=SAMPLE_CHECKIN)
    )

    # Act
    result = await client.checkin_habit(
        {"habitId": "h1", "checkinStamp": "20250315", "status": 2}
    )

    # Assert
    assert result["habitId"] == "h1"


@respx.mock
@pytest.mark.asyncio
async def test_undo_checkin(client):
    # Arrange
    route = respx.delete(f"{BASE_URL_CHINA}/habitCheckins").mock(
        return_value=httpx.Response(200)
    )

    # Act & Assert
    await client.undo_checkin("h1", "20250315")

    assert route.calls[0].request.url.params["habitId"] == "h1"
    assert route.calls[0].request.url.params["stamp"] == "20250315"


@respx.mock
@pytest.mark.asyncio
async def test_list_habit_checkins(client):
    # Arrange
    respx.get(f"{BASE_URL_CHINA}/habitCheckins").mock(
        return_value=httpx.Response(200, json=[SAMPLE_CHECKIN])
    )

    # Act
    checkins = await client.list_habit_checkins("h1")

    # Assert
    assert len(checkins) == 1
    assert isinstance(checkins[0], HabitCheckin)


@respx.mock
@pytest.mark.asyncio
async def test_list_habit_sections(client):
    # Arrange
    respx.get(f"{BASE_URL_CHINA}/habitSections").mock(
        return_value=httpx.Response(200, json=[SAMPLE_SECTION])
    )

    # Act
    sections = await client.list_habit_sections()

    # Assert
    assert len(sections) == 1
    assert isinstance(sections[0], HabitSection)
    assert sections[0].name == "Morning"


# ── Folder tests ──


@respx.mock
@pytest.mark.asyncio
async def test_list_folders(client):
    # Arrange
    respx.get(f"{BASE_URL_CHINA}/projectGroups").mock(
        return_value=httpx.Response(200, json=[SAMPLE_FOLDER])
    )

    # Act
    folders = await client.list_folders()

    # Assert
    assert len(folders) == 1
    assert isinstance(folders[0], ProjectGroup)
    assert folders[0].name == "Personal"


@respx.mock
@pytest.mark.asyncio
async def test_create_folder(client):
    # Arrange
    respx.post(f"{BASE_URL_CHINA}/projectGroup").mock(
        return_value=httpx.Response(200, json=SAMPLE_FOLDER)
    )

    # Act
    folder = await client.create_folder({"name": "Personal"})

    # Assert
    assert isinstance(folder, ProjectGroup)
    assert folder.name == "Personal"


@respx.mock
@pytest.mark.asyncio
async def test_update_folder(client):
    # Arrange
    updated = {**SAMPLE_FOLDER, "name": "Work"}
    respx.put(f"{BASE_URL_CHINA}/projectGroup/g1").mock(
        return_value=httpx.Response(200, json=updated)
    )

    # Act
    folder = await client.update_folder("g1", {"name": "Work"})

    # Assert
    assert folder.name == "Work"


@respx.mock
@pytest.mark.asyncio
async def test_delete_folder(client):
    # Arrange
    respx.delete(f"{BASE_URL_CHINA}/projectGroup/g1").mock(
        return_value=httpx.Response(200)
    )

    # Act & Assert
    await client.delete_folder("g1")


# ── International region test ──


@respx.mock
@pytest.mark.asyncio
async def test_intl_list_tags(client_intl):
    # Arrange
    respx.get(f"{BASE_URL_INTL}/tags").mock(
        return_value=httpx.Response(200, json=[SAMPLE_TAG])
    )

    # Act
    tags = await client_intl.list_tags()

    # Assert
    assert len(tags) == 1
    assert tags[0].name == "work"


# ── Error handling ──


@respx.mock
@pytest.mark.asyncio
async def test_api_error_raises(client):
    # Arrange
    respx.get(f"{BASE_URL_CHINA}/tags").mock(
        return_value=httpx.Response(401, json={"error": "unauthorized"})
    )

    # Act & Assert
    with pytest.raises(httpx.HTTPStatusError):
        await client.list_tags()


# ── Signon tests ──


@respx.mock
@pytest.mark.asyncio
async def test_signon_success():
    # Arrange
    respx.post(f"{BASE_URL_CHINA}/user/signon").mock(
        return_value=httpx.Response(200, json={"token": "abc123", "userId": "u1"})
    )

    # Act
    token = await signon(BASE_URL_CHINA, "user@test.com", "pass")

    # Assert
    assert token == "abc123"


@respx.mock
@pytest.mark.asyncio
async def test_signon_2fa_raises():
    # Arrange
    respx.post(f"{BASE_URL_CHINA}/user/signon").mock(
        return_value=httpx.Response(200, json={"authId": "2fa-id"})
    )

    # Act & Assert
    with pytest.raises(RuntimeError, match="2FA"):
        await signon(BASE_URL_CHINA, "user@test.com", "pass")


@respx.mock
@pytest.mark.asyncio
async def test_signon_bad_credentials():
    # Arrange
    respx.post(f"{BASE_URL_CHINA}/user/signon").mock(
        return_value=httpx.Response(401, json={"error": "unauthorized"})
    )

    # Act & Assert
    with pytest.raises(httpx.HTTPStatusError):
        await signon(BASE_URL_CHINA, "user@test.com", "wrong")


# ── Cookie header test ──


@respx.mock
@pytest.mark.asyncio
async def test_cookie_header(client):
    # Arrange
    route = respx.get(f"{BASE_URL_CHINA}/tags").mock(
        return_value=httpx.Response(200, json=[])
    )

    # Act
    await client.list_tags()

    # Assert
    assert route.calls[0].request.headers["cookie"] == "t=test-token"
