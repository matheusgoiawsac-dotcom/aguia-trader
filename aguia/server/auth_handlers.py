"""Auth HTTP handlers."""

from __future__ import annotations

import json
from http.cookies import SimpleCookie
from typing import Any, Dict, Optional

from aguia.auth.service import AuthService


auth_service = AuthService()


COOKIE_NAME = "aguia_session"


def _parse_cookies(handler) -> Dict[str, str]:
    cookie_header = handler.headers.get("Cookie") or ""
    c = SimpleCookie()
    try:
        c.load(cookie_header)
    except Exception:
        return {}
    out = {}
    for k, m in c.items():
        out[k] = m.value
    return out


def _get_session_token(handler) -> Optional[str]:
    cookies = _parse_cookies(handler)
    return cookies.get(COOKIE_NAME)


def set_session_cookie(handler, token: str, expires_at: str = None):
    # Build cookie
    parts = [f"{COOKIE_NAME}={token}", "Path=/", "HttpOnly", "SameSite=Lax"]
    # Try to set Secure in prod-like env? keep flexible
    handler.send_header("Set-Cookie", "; ".join(parts))


def clear_session_cookie(handler):
    parts = [f"{COOKIE_NAME}=", "Path=/", "HttpOnly", "SameSite=Lax", "Max-Age=0"]
    handler.send_header("Set-Cookie", "; ".join(parts))
