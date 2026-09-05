from __future__ import annotations

import os
import secrets
from typing import Any, MutableMapping


AUTH_STORAGE_KEY = "swmvr_mvp_auth_v1"


def _configured_credentials() -> tuple[str, str]:
    return (
        os.getenv("SWMVR_USERNAME", "").strip(),
        os.getenv("SWMVR_PASSWORD", ""),
    )


def credentials_configured() -> bool:
    username, password = _configured_credentials()
    return bool(username and password)


def authenticate_mvp_account(
    storage: MutableMapping[str, Any],
    username: str,
    password: str,
) -> bool:
    expected_username, expected_password = _configured_credentials()

    if not expected_username or not expected_password:
        return False

    supplied_username = str(username or "").strip()
    supplied_password = str(password or "")

    username_ok = secrets.compare_digest(
        supplied_username.casefold(),
        expected_username.casefold(),
    )

    password_ok = secrets.compare_digest(
        supplied_password,
        expected_password,
    )

    if not (username_ok and password_ok):
        return False

    storage[AUTH_STORAGE_KEY] = {
        "authenticated": True,
        "username": expected_username,
    }

    return True


def is_authenticated(
    storage: MutableMapping[str, Any],
) -> bool:
    session = storage.get(AUTH_STORAGE_KEY)

    return (
        isinstance(session, dict)
        and session.get("authenticated") is True
    )


def authenticated_username(
    storage: MutableMapping[str, Any],
) -> str | None:
    if not is_authenticated(storage):
        return None

    session = storage.get(AUTH_STORAGE_KEY, {})
    username = session.get("username")

    return (
        str(username)
        if username is not None
        else None
    )


def logout_mvp_account(
    storage: MutableMapping[str, Any],
) -> None:
    storage.pop(AUTH_STORAGE_KEY, None)
