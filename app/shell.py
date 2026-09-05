from contextlib import contextmanager
from pathlib import Path

from nicegui import app, ui

from app.session_ui import sign_out
from app.theme import apply_theme


_STATIC_DIR = Path(__file__).resolve().parent / "static"
app.add_static_files("/swmvr-static", str(_STATIC_DIR))


def _nav_item(
    label: str,
    icon: str,
    route: str,
    active: bool = False,
) -> None:
    css_class = "nav-item nav-item-active" if active else "nav-item"

    with ui.row().classes(
        f"{css_class} items-center gap-3 no-wrap"
    ).on(
        "click",
        lambda: ui.navigate.to(route),
    ):
        ui.icon(icon).style("font-size: 20px;")
        ui.label(label).style("font-size: 13px; font-weight: 500;")


@contextmanager
def app_shell(
    active_page: str,
    title: str,
    subtitle: str,
):
    apply_theme()

    with ui.header().classes(
        "app-header items-center justify-between px-6"
    ):
        with ui.row().classes("items-center gap-3"):
            ui.image(
                "/swmvr-static/inventide-logo.png"
            ).style(
                "width:38px;"
                "height:38px;"
                "object-fit:contain;"
            )

            with ui.column().classes("gap-0"):
                ui.label(
                    "VESPER | SUPPLY CHAIN INTELLIGENCE"
                ).style(
                    "font-size:15px;"
                    "font-weight:800;"
                    "letter-spacing:0.35px;"
                    "color:var(--sw-text);"
                )

                ui.label(
                    "Powered by Inventide"
                ).style(
                    "font-size:10px;"
                    "color:var(--sw-text-soft);"
                    "margin-top:1px;"
                )

        with ui.row().classes("items-center gap-2"):
            ui.label("MVP v0.3").classes("version-badge")

            ui.button(
                icon="logout",
                on_click=sign_out,
            ).props(
                "flat round dense"
            ).style(
                "color:var(--sw-burgundy);"
            ).tooltip(
                "Sign out"
            )

    with ui.left_drawer(value=True).props(
        "width=245 bordered=false"
    ).classes("app-drawer"):

        with ui.column().classes("w-full px-4 pt-5 gap-0"):
            with ui.column().classes("w-full items-center gap-0 mb-1"):
                ui.image(
                    "/swmvr-static/swayamvar-logo.png"
                ).style(
                    "width:178px;"
                    "height:72px;"
                    "object-fit:contain;"
                    "display:block;"
                    "margin:0 auto;"
                )

                ui.label("Intelligence Suite").style(
                    "font-size:11px;"
                    "letter-spacing:1.6px;"
                    "text-transform:uppercase;"
                    "color:rgba(255,255,255,0.82);"
                    "margin-top:-2px;"
                    "text-align:center;"
                )

            ui.separator().style(
                "margin-top: 22px;"
                "margin-bottom: 8px;"
                "opacity: 0.15;"
            )

            ui.label("Intelligence").classes("nav-section-label")

            _nav_item(
                label="Network Intelligence",
                icon="hub",
                route="/network-intelligence",
                active=active_page == "network",
            )

            _nav_item(
                label="Demand Exposure",
                icon="query_stats",
                route="/demand-exposure",
                active=active_page == "demand",
            )

            ui.space()


    with ui.column().classes("page-wrapper gap-0"):
        ui.label(
            "SWAYAMVAR · SUPPLY CHAIN INTELLIGENCE"
        ).classes("eyebrow")

        ui.label(title).classes("page-title")
        ui.label(subtitle).classes("page-subtitle")

        ui.element("div").style("height: 28px;")

        yield
