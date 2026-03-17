import pytest

from dida365_agent_mcp.server_v2 import _handle_error, _to_json, init_v2_client


def test_to_json_list():
    # Arrange
    from dida365_agent_mcp.models import Tag

    tags = [Tag(name="work", color="#FF0000")]

    # Act
    result = _to_json(tags)

    # Assert
    import json

    parsed = json.loads(result)
    assert len(parsed) == 1
    assert parsed[0]["name"] == "work"


def test_to_json_dict():
    # Arrange
    data = {"id2etag": {"t1": "e1"}, "id2error": {}}

    # Act
    result = _to_json(data)

    # Assert
    import json

    assert json.loads(result) == data


def test_to_json_model():
    # Arrange
    from dida365_agent_mcp.models import ProjectGroup

    folder = ProjectGroup(id="g1", name="Personal")

    # Act
    result = _to_json(folder)

    # Assert
    import json

    parsed = json.loads(result)
    assert parsed["id"] == "g1"
    assert parsed["name"] == "Personal"


def test_handle_error_runtime():
    # Arrange
    err = RuntimeError("V2 client not initialized")

    # Act
    result = _handle_error(err, "test_op")

    # Assert
    assert "Error:" in result
    assert "V2 client not initialized" in result


def test_handle_error_generic():
    # Arrange
    err = ValueError("bad value")

    # Act
    result = _handle_error(err, "test_op")

    # Assert
    assert "ValueError" in result
    assert "bad value" in result


def test_init_v2_client():
    from dida365_agent_mcp.client_v2 import Dida365V2Client
    from dida365_agent_mcp.server_v2 import _get_v2_client

    # Arrange
    client = Dida365V2Client(session_token="t", base_url="http://test")

    # Act
    init_v2_client(client)

    # Assert
    assert _get_v2_client() is client


def test_get_v2_client_not_initialized():
    from dida365_agent_mcp.server_v2 import _get_v2_client

    # Arrange - reset
    init_v2_client(None)  # type: ignore[arg-type]

    # Act & Assert
    with pytest.raises(RuntimeError, match="V2 client not initialized"):
        _get_v2_client()
