from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

_DOMAINS: dict[str, dict[str, str]] = {
    "china": {
        "api": "https://api.dida365.com/open/v1",
        "v2_api": "https://api.dida365.com/api/v2",
        "auth": "https://dida365.com/oauth/authorize",
        "token": "https://dida365.com/oauth/token",
        "developer": "https://developer.dida365.com/manage",
    },
    "international": {
        "api": "https://api.ticktick.com/open/v1",
        "v2_api": "https://api.ticktick.com/api/v2",
        "auth": "https://ticktick.com/oauth/authorize",
        "token": "https://ticktick.com/oauth/token",
        "developer": "https://developer.ticktick.com/manage",
    },
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    dida365_client_id: str = ""
    dida365_client_secret: str = ""
    dida365_access_token: str = ""
    dida365_redirect_uri: str = "http://localhost:8000/oauth/callback"
    dida365_region: Literal["china", "international"] = "china"
    dida365_v2_session_token: str = ""
    dida365_username: str = ""
    dida365_password: str = ""

    transport: str = "stdio"
    host: str = "0.0.0.0"
    port: int = 8000

    @computed_field  # type: ignore[prop-decorator]
    @property
    def api_base_url(self) -> str:
        return _DOMAINS[self.dida365_region]["api"]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def authorize_url(self) -> str:
        return _DOMAINS[self.dida365_region]["auth"]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def token_url(self) -> str:
        return _DOMAINS[self.dida365_region]["token"]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def developer_url(self) -> str:
        return _DOMAINS[self.dida365_region]["developer"]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def v2_api_base_url(self) -> str:
        return _DOMAINS[self.dida365_region]["v2_api"]


settings = Settings()
