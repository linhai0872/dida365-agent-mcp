from dida365_agent_mcp.config import Settings


def test_china_region_urls(monkeypatch):
    monkeypatch.setenv("DIDA365_REGION", "china")
    s = Settings()

    assert s.api_base_url == "https://api.dida365.com/open/v1"
    assert s.authorize_url == "https://dida365.com/oauth/authorize"
    assert s.token_url == "https://dida365.com/oauth/token"
    assert s.developer_url == "https://developer.dida365.com/manage"


def test_international_region_urls(monkeypatch):
    monkeypatch.setenv("DIDA365_REGION", "international")
    s = Settings()

    assert s.api_base_url == "https://api.ticktick.com/open/v1"
    assert s.authorize_url == "https://ticktick.com/oauth/authorize"
    assert s.token_url == "https://ticktick.com/oauth/token"
    assert s.developer_url == "https://developer.ticktick.com/manage"


def test_default_region_is_china():
    s = Settings()

    assert s.dida365_region == "china"
    assert "dida365.com" in s.api_base_url
