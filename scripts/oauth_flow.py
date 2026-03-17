"""One-time OAuth flow: local server, browser auth, code exchange."""

from __future__ import annotations

import asyncio
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, "src")

from dida365_agent_mcp.auth import exchange_code_for_token, get_authorize_url
from dida365_agent_mcp.config import settings

_code: str | None = None
_server: HTTPServer | None = None


def _preflight_check() -> None:
    errors = []
    dev_url = settings.developer_url

    env_file = Path(".env")
    if not env_file.exists():
        errors.append(
            "No .env file found.\n"
            "  Run: cp .env.example .env\n"
            "  Then fill in DIDA365_CLIENT_ID and DIDA365_CLIENT_SECRET"
        )

    if not settings.dida365_client_id:
        errors.append(f"DIDA365_CLIENT_ID is not set.\n  Get it from: {dev_url}")

    if not settings.dida365_client_secret:
        errors.append(f"DIDA365_CLIENT_SECRET is not set.\n  Get it from: {dev_url}")

    if errors:
        print("=" * 60)
        print("SETUP REQUIRED")
        print("=" * 60)
        for i, err in enumerate(errors, 1):
            print(f"\n{i}. {err}")
        print(f"\nDeveloper Center: {dev_url}")
        print("=" * 60)
        sys.exit(1)


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _code, _server
        qs = parse_qs(urlparse(self.path).query)
        _code = qs.get("code", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        if _code:
            self.wfile.write(b"<h1>Authorization successful! You can close this tab.</h1>")
        else:
            self.wfile.write(b"<h1>No code received. Please try again.</h1>")

        if _server:
            threading.Thread(target=_server.shutdown, daemon=True).start()

    def log_message(self, format: str, /, *args: object) -> None:  # noqa: A002
        pass


def main():
    global _server

    _preflight_check()

    port = 8000
    try:
        _server = HTTPServer(("localhost", port), CallbackHandler)
    except OSError as e:
        print(f"Error: Cannot start server on port {port}: {e}")
        print("  Is another process using this port?")
        print("  Try: lsof -i :8000")
        sys.exit(1)

    url = get_authorize_url()
    region_label = "Dida365" if settings.dida365_region == "china" else "TickTick"
    print("=" * 60)
    print(f"{region_label.upper()} OAUTH AUTHORIZATION")
    print("=" * 60)
    redirect_hint = (
        f"Make sure the Redirect URI in your {region_label} app settings matches:\n"
        f"  {settings.dida365_redirect_uri}\n"
        f"  Configure at: {settings.developer_url}"
    )
    print(f"\n{redirect_hint}\n")
    print(f"Opening browser...\n{url}\n")
    webbrowser.open(url)

    print(f"Waiting for callback on http://localhost:{port}/oauth/callback ...")
    _server.serve_forever()

    if not _code:
        print("Error: No authorization code received.")
        sys.exit(1)

    print(f"Got code: {_code[:8]}...")
    token_data = asyncio.run(exchange_code_for_token(_code))
    access_token = token_data.get("access_token", "")
    expires_in = token_data.get("expires_in", 0)
    expires_days = expires_in // 86400

    print("\n" + "=" * 60)
    print("SUCCESS")
    print("=" * 60)
    print(f"  Access token:  {access_token[:16]}...")
    print(f"  Expires in:    ~{expires_days} days")
    print("  Saved to:      ~/.dida365-agent-mcp/token.json")
    print("\n  Or set in .env:")
    print(f"  DIDA365_ACCESS_TOKEN={access_token}")
    print("=" * 60)


if __name__ == "__main__":
    main()
