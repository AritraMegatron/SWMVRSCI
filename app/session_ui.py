from __future__ import annotations

from nicegui import app, ui

from app.services.auth_service import (
    is_authenticated,
    logout_mvp_account,
)


def require_login() -> bool:
    if is_authenticated(app.storage.user):
        return True

    ui.navigate.to("/login")
    return False


def sign_out() -> None:
    logout_mvp_account(app.storage.user)
    ui.navigate.to("/login")
