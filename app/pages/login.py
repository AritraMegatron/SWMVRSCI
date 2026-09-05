from __future__ import annotations

from nicegui import app, ui

from app.services.auth_service import (
    authenticate_mvp_account,
    credentials_configured,
    is_authenticated,
)
from app.theme import apply_theme


@ui.page("/login")
def login_page() -> None:
    if is_authenticated(app.storage.user):
        ui.navigate.to("/network-intelligence")
        return

    apply_theme()

    ui.add_css(
        """
        .sw-login-page {
            min-height: 100vh;
            width: 100%;
            background:
                radial-gradient(
                    circle at 12% 10%,
                    rgba(197, 154, 84, 0.16),
                    transparent 28%
                ),
                radial-gradient(
                    circle at 90% 88%,
                    rgba(101, 29, 50, 0.12),
                    transparent 30%
                ),
                #F7F3EE;
        }

        .sw-login-banner {
            background: white;
            border-bottom: 1px solid #E7DED5;
            min-height: 70px;
        }

        .sw-login-card {
            width: min(450px, calc(100vw - 32px));
            border-radius: 22px;
            border: 1px solid rgba(255,255,255,0.10);
            background:
                linear-gradient(
                    145deg,
                    #40101F,
                    #651D32
                );
            color: white;
            box-shadow: 0 28px 70px rgba(64,16,31,0.22);
        }

        .sw-login-card .q-field__label,
        .sw-login-card .q-field__native,
        .sw-login-card .q-field__input {
            color: #1F1A1C !important;
        }

        .sw-login-card .q-field__control {
            background: #F4F5F7 !important;
            border-radius: 10px;
            overflow: hidden;
        }

        .sw-login-card .q-field__control-container {
            background: transparent !important;
        }

        .sw-login-card .q-field__native,
        .sw-login-card .q-field__input {
            background: transparent !important;
        }

        .sw-login-card .q-field__append,
        .sw-login-card .q-field__prepend {
            background: transparent !important;
        }

        .sw-login-card .q-field--outlined .q-field__control:before {
            border-color: rgba(64,16,31,0.28);
        }

        .sw-login-card .q-field--outlined.q-field--focused .q-field__control:after {
            border-color: #C59A54;
        }

        .sw-login-card .q-icon {
            color: #5A4E52 !important;
        }

        .sw-login-brand {
            background:
                linear-gradient(
                    145deg,
                    #40101F,
                    #651D32
                );
            color: white;
            border-radius: 22px;
            box-shadow: 0 28px 80px rgba(64,16,31,0.22);
        }

        .sw-login-swayamvar-logo {
            width: 220px;
            height: 90px;
            object-fit: contain;
            display: block;
            margin: 0 auto;
        }
        """
    )

    with ui.element("div").classes(
        "sw-login-page flex flex-col"
    ):
        # ---------------------------------------------------------
        # Top banner
        # ---------------------------------------------------------
        with ui.row().classes(
            "sw-login-banner w-full items-center px-5 py-3"
        ):
            ui.image(
                "/swmvr-static/inventide-logo.png"
            ).style(
                "width:38px;"
                "height:38px;"
                "object-fit:contain;"
                "flex:0 0 auto;"
            )

            with ui.column().classes("gap-0 ml-3"):
                ui.label(
                    "VESPER | SUPPLY CHAIN INTELLIGENCE"
                ).style(
                    "font-size:15px;"
                    "font-weight:800;"
                    "letter-spacing:0.35px;"
                    "color:#2B2527;"
                )

                ui.label(
                    "Powered by Inventide"
                ).style(
                    "font-size:10px;"
                    "color:#776D70;"
                    "margin-top:1px;"
                )

        # ---------------------------------------------------------
        # Login workspace
        # ---------------------------------------------------------
        with ui.element("div").classes(
            "flex-1 w-full flex items-center justify-center p-4 md:p-8"
        ):
            with ui.row().classes(
                "w-full max-w-6xl items-stretch justify-center gap-7"
            ):
                # Left brand/intro panel
                with ui.card().classes(
                    "sw-login-brand hidden lg:flex flex-1 max-w-xl p-10 border-0"
                ):
                    with ui.column().classes(
                        "w-full h-full gap-5"
                    ):
                        ui.space()

                        ui.label(
                            "The Swayamvar Intelligence Suite"
                        ).classes(
                            "text-4xl font-black leading-tight text-white"
                        )

                        ui.label(
                            "Network performance, granular demand forecasting "
                            "and replenishment planning in one decision workspace."
                        ).classes(
                            "text-base leading-relaxed text-white/75 max-w-lg"
                        )

                        ui.space()

                        ui.label(
                            "MVP ACCESS"
                        ).classes(
                            "text-xs font-bold tracking-[0.16em] text-white/45"
                        )

                # Login panel
                with ui.card().classes(
                    "sw-login-card p-7 md:p-9"
                ):
                    with ui.column().classes(
                        "w-full gap-5"
                    ):
                        # Swayamvar logo above login section
                        with ui.column().classes(
                            "w-full items-center gap-1"
                        ):
                            ui.image(
                                "/swmvr-static/swayamvar-logo.png"
                            ).classes(
                                "sw-login-swayamvar-logo"
                            )

                            ui.label(
                                "INTELLIGENCE SUITE"
                            ).style(
                                "font-size:10px;"
                                "font-weight:700;"
                                "letter-spacing:1.8px;"
                                "color:rgba(255,255,255,0.90);"
                            )

                        with ui.column().classes("gap-1"):
                            ui.label(
                                "Sign in"
                            ).classes(
                                "text-3xl font-bold tracking-tight text-white"
                            ).style(
                                "font-family:'Playfair Display',serif;"
                                "color:white;"
                            )

                        username = ui.input(
                            label="Username",
                            placeholder="Enter username",
                        ).props(
                            "outlined autocomplete=username"
                        ).classes(
                            "w-full"
                        )

                        password = ui.input(
                            label="Password",
                            password=True,
                            password_toggle_button=True,
                        ).props(
                            "outlined autocomplete=current-password"
                        ).classes(
                            "w-full"
                        )

                        error_label = ui.label("").classes(
                            "text-sm font-semibold min-h-[20px]"
                        ).style(
                            "color:#FFD0D3;"
                        )

                        def attempt_login() -> None:
                            error_label.set_text("")

                            if not credentials_configured():
                                error_label.set_text(
                                    "MVP credentials are not configured in the .env file."
                                )
                                return

                            success = authenticate_mvp_account(
                                app.storage.user,
                                username.value or "",
                                password.value or "",
                            )

                            if not success:
                                error_label.set_text(
                                    "Username or password is incorrect."
                                )
                                password.value = ""
                                return

                            ui.navigate.to(
                                "/network-intelligence"
                            )

                        password.on(
                            "keydown.enter",
                            attempt_login,
                        )

                        ui.button(
                            "Sign in",
                            icon="login",
                            on_click=attempt_login,
                        ).props(
                            "unelevated no-caps"
                        ).classes(
                            "w-full h-12 rounded-xl text-base font-bold"
                        ).style(
                            "background:#C59A54;"
                            "color:#40101F;"
                        )

                        ui.separator().classes("my-1 opacity-20")

                        ui.label(
                            "MVP authentication only. Production identity, roles "
                            "and password management are not implemented."
                        ).classes(
                            "text-xs leading-relaxed"
                        ).style(
                            "color:rgba(255,255,255,0.66);"
                        )
