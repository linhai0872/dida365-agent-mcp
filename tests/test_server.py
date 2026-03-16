from dida365_agent_mcp.server import _build_data


def test_build_data_sort_order():
    # Arrange & Act
    result = _build_data(sort_order=12345)

    # Assert
    assert result == {"sortOrder": 12345}


def test_build_data_items_passthrough():
    # Arrange
    subtasks = [{"title": "Buy milk", "status": 0}]

    # Act
    result = _build_data(kind="CHECKLIST", items=subtasks)

    # Assert
    assert result == {"kind": "CHECKLIST", "items": subtasks}


def test_build_data_none_excluded():
    # Arrange & Act
    result = _build_data(title="Hello", items=None, sort_order=None, kind=None)

    # Assert
    assert result == {"title": "Hello"}
