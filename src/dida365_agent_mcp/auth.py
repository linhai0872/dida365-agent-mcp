from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from urllib.parse import urlencode

import httpx

from . import config

logger = logging.getLogger(__name__)

TOKEN_FILE = Path.home() / ".dida365-agent-mcp" / "token.json"
SCOPES = "tasks:read tasks:write"


def _check_credentials() -> None:
    missing = []
    if not config.settings.dida365_client_id:
        missing.append("DIDA365_CLIENT_ID")
    if not config.settings.dida365_client_secret:
        missing.append("DIDA365_CLIENT_SECRET")
    if missing:
        dev_url = config.settings.developer_url
        raise RuntimeError(
            f"Missing required config: {', '.join(missing)}.\n"
            f"Steps:\n"
            f"  1. Create an app at {dev_url}\n"
            f"  2. Copy Client ID and Client Secret\n"
            f"  3. Set them in .env (see .env.example)"
        )


def get_authorize_url(state: str = "state") -> str:
    _check_credentials()
    params = {
        "client_id": config.settings.dida365_client_id,
        "scope": SCOPES,
        "state": state,
        "redirect_uri": config.settings.dida365_redirect_uri,
        "response_type": "code",
    }
    return f"{config.settings.authorize_url}?{urlencode(params)}"


async def exchange_code_for_token(code: str) -> dict:
    _check_credentials()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            config.settings.token_url,
            data={
                "code": code,
                "grant_type": "authorization_code",
                "scope": SCOPES,
                "redirect_uri": config.settings.dida365_redirect_uri,
            },
            auth=(
                config.settings.dida365_client_id,
                config.settings.dida365_client_secret,
            ),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        token_data = resp.json()
        token_data["obtained_at"] = int(time.time())
        _save_token(token_data)
        return token_data


def _save_token(token_data: dict) -> None:
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(json.dumps(token_data, indent=2))
    logger.info("Token saved to %s", TOKEN_FILE)


def _load_token() -> dict | None:
    if TOKEN_FILE.exists():
        return json.loads(TOKEN_FILE.read_text())
    return None


def _is_token_expired(token_data: dict) -> bool:
    obtained_at = token_data.get("obtained_at")
    expires_in = token_data.get("expires_in")
    if not obtained_at or not expires_in:
        return False
    return time.time() > obtained_at + expires_in - 86400


def get_access_token() -> str:
    if config.settings.dida365_access_token:
        return config.settings.dida365_access_token

    token_data = _load_token()
    if token_data and token_data.get("access_token"):
        if _is_token_expired(token_data):
            raise RuntimeError(
                "Access token has expired (~180 days). "
                "Re-run: uv run python scripts/oauth_flow.py "
                "(opens browser → authorize → new token auto-saved)"
            )
        return token_data["access_token"]

    has_credentials = config.settings.dida365_client_id and config.settings.dida365_client_secret
    if has_credentials:
        raise RuntimeError(
            "No access token found. Run the OAuth flow:\n  uv run python scripts/oauth_flow.py"
        )

    dev_url = config.settings.developer_url
    raise RuntimeError(
        "No access token and no OAuth credentials configured.\n"
        "Setup steps:\n"
        f"  1. Create an app at {dev_url}\n"
        "  2. Copy .env.example to .env and fill in credentials\n"
        "  3. Run: uv run python scripts/oauth_flow.py"
    )
