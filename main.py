from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from nicegui import app, ui


BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

# Load local MVP credentials when a .env file is present.
# On Render, environment variables configured in the dashboard are used.
load_dotenv(
    dotenv_path=ENV_FILE,
    override=False,
)


# Importing page modules registers the routes.
from app.pages import network_intelligence  # noqa: E402,F401
from app.pages import demand_exposure  # noqa: E402,F401
from app.pages import login  # noqa: E402,F401
from app.services.auth_service import is_authenticated  # noqa: E402


@ui.page("/")
def index() -> None:
    ui.navigate.to(
        "/network-intelligence"
        if is_authenticated(app.storage.user)
        else "/login"
    )


storage_secret = os.getenv(
    "NICEGUI_STORAGE_SECRET",
    "swmvr-local-mvp-storage-secret-change-me",
)

is_render = os.getenv("RENDER", "").lower() == "true"


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="Vesper | Swayamvar Intelligence Suite",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8090")),
        reload=not is_render,
        show=False,
        storage_secret=storage_secret,
    )
