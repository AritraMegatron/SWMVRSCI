from __future__ import annotations

import math
from typing import Any

from nicegui import events, ui

from app.data.store_catalog import STORES
from app.services.network_service import (
    TABLE_COLUMNS,
    build_network_kpis,
    build_store_observation,
    build_table_rows,
    format_inr,
)
from app.session_ui import require_login
from app.shell import app_shell
from app.theme import BURGUNDY, GOLD, STATUS_COLORS


MAP_CENTER = (17.45, 80.30)
MAP_ZOOM = 6


def _haversine_km(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> float:
    radius_km = 6371.0

    phi_1 = math.radians(latitude_1)
    phi_2 = math.radians(latitude_2)

    delta_phi = math.radians(latitude_2 - latitude_1)
    delta_lambda = math.radians(longitude_2 - longitude_1)

    calculation = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi_1)
        * math.cos(phi_2)
        * math.sin(delta_lambda / 2) ** 2
    )

    return (
        2
        * radius_km
        * math.atan2(
            math.sqrt(calculation),
            math.sqrt(1 - calculation),
        )
    )


def _metric_card(
    title: str,
    value: str,
    subtitle: str,
    icon: str,
) -> tuple[Any, Any]:
    with ui.card().classes("metric-card p-4 w-full"):
        with ui.row().classes(
            "w-full items-start justify-between no-wrap"
        ):
            with ui.column().classes("gap-1"):
                ui.label(title).classes(
                    "text-[10px] font-bold tracking-wider muted"
                )

                value_label = ui.label(value).classes(
                    "text-2xl font-bold tracking-tight"
                )

                subtitle_label = ui.label(subtitle).classes(
                    "text-[11px] muted"
                )

            with ui.element("div").classes("metric-icon"):
                ui.icon(icon).classes("text-xl")

    return value_label, subtitle_label


@ui.page("/network-intelligence")
def network_intelligence_page():
    if not require_login():
        return

    stores = build_table_rows(STORES)
    stores_by_id = {
        store["store_id"]: store
        for store in stores
    }

    state: dict[str, Any] = {
        "selected_id": stores[0]["store_id"],
        "state_filter": "All states",
        "status_filter": "All statuses",
        "search": "",
    }

    refs: dict[str, Any] = {}

    def filtered_rows() -> list[dict]:
        query = state["search"].strip().lower()

        return [
            store
            for store in stores
            if (
                state["state_filter"] == "All states"
                or store["state"] == state["state_filter"]
            )
            and (
                state["status_filter"] == "All statuses"
                or store["status"] == state["status_filter"]
            )
            and (
                not query
                or query in store["store_name"].lower()
                or query in store["city"].lower()
                or query in store["state"].lower()
            )
        ]

    def replace_table_rows(rows: list[dict]) -> None:
        refs["table"].rows.clear()
        refs["table"].rows.extend(rows)
        refs["table"].update()

    def update_kpis(rows: list[dict]) -> None:
        kpis = build_network_kpis(rows)

        refs["net_sales"].set_text(
            format_inr(kpis["net_sales"])
        )
        refs["net_sales_sub"].set_text(
            f"{len(rows)} stores in view"
        )

        refs["gross_margin"].set_text(
            f"{kpis['gross_margin_pct']:.1f}%"
        )

        refs["sell_through"].set_text(
            f"{kpis['sell_through_pct']:.1f}%"
        )

        refs["inventory_value"].set_text(
            format_inr(kpis["inventory_value"])
        )

        refs["inventory_turns"].set_text(
            f"{kpis['inventory_turns']:.1f}x"
        )

        refs["sales_per_sq_ft"].set_text(
            format_inr(kpis["sales_per_sq_ft"])
        )

    def update_detail(store: dict) -> None:
        observation, action = build_store_observation(store)

        values = {
            "selected_name": store["store_name"],
            "selected_location": (
                f"{store['city']} · {store['state']} · {store['format']}"
            ),
            "selected_address": store["address"],
            "selected_sales": format_inr(store["monthly_sales"]),
            "selected_forecast": format_inr(
                store["forecast_30d_sales"]
            ),
            "selected_inventory": format_inr(
                store["inventory_value"]
            ),
            "selected_sell_through": (
                f"{store['sell_through_pct']:.1f}%"
            ),
            "selected_growth": (
                f"{store['sales_growth_pct']:+.1f}%"
            ),
            "selected_margin": (
                f"{store['gross_margin_pct']:.1f}%"
            ),
            "selected_stock_cover": (
                f"{store['stock_cover_weeks']:.1f} weeks"
            ),
            "selected_availability": (
                f"{store['sku_availability_pct']:.1f}%"
            ),
            "selected_aged": (
                f"{store['aged_inventory_pct']:.1f}%"
            ),
            "selected_asp": format_inr(store["asp"]),
            "selected_basket": format_inr(
                store["average_basket_value"]
            ),
            "selected_upt": (
                f"{store['units_per_transaction']:.2f}"
            ),
            "selected_sales_sqft": format_inr(
                store["sales_per_sq_ft"]
            ),
            "selected_turns": (
                f"{store['inventory_turns']:.1f}x"
            ),
            "selected_risk_skus": str(store["at_risk_skus"]),
            "selected_top_category": store["top_category"],
            "selected_observation": observation,
            "selected_action": action,
        }

        for ref_name, value in values.items():
            refs[ref_name].set_text(value)

        refs["selected_status"].set_text(
            store["status"].upper()
        )

        refs["selected_status"].style(
            f"background:{STATUS_COLORS[store['status']]};"
            "color:white;"
        )

    def select_store(
        store_id: str,
        move_to_top: bool = False,
        notify: bool = False,
    ) -> None:
        if store_id not in stores_by_id:
            return

        selected = stores_by_id[store_id]
        state["selected_id"] = store_id

        rows = filtered_rows()

        if selected not in rows:
            state["state_filter"] = "All states"
            state["status_filter"] = "All statuses"
            state["search"] = ""

            refs["state_select"].value = "All states"
            refs["status_select"].value = "All statuses"
            refs["search_input"].value = ""

            rows = filtered_rows()
            update_kpis(rows)

        if move_to_top:
            rows = [
                selected,
                *[
                    row
                    for row in rows
                    if row["store_id"] != store_id
                ],
            ]

        replace_table_rows(rows)

        refs["table"].selected.clear()
        refs["table"].selected.append(selected)
        refs["table"].update()

        update_detail(selected)

        refs["highlight_layer"].run_method(
            "setLatLng",
            [
                selected["lat"],
                selected["lon"],
            ],
        )

        if notify:
            ui.notify(
                f"Selected {selected['store_name']}, {selected['city']}",
                type="info",
                position="top",
            )

    def apply_filters(_: Any = None) -> None:
        state["state_filter"] = refs["state_select"].value
        state["status_filter"] = refs["status_select"].value
        state["search"] = refs["search_input"].value or ""

        rows = filtered_rows()
        update_kpis(rows)

        refs["filter_result"].set_text(
            f"{len(rows)} stores shown"
            if rows
            else "No matching stores"
        )

        if not rows:
            replace_table_rows([])
            refs["table"].selected.clear()
            refs["table"].update()
            return

        visible_ids = {
            row["store_id"]
            for row in rows
        }

        if state["selected_id"] not in visible_ids:
            state["selected_id"] = rows[0]["store_id"]

        select_store(state["selected_id"])

    def clear_filters() -> None:
        refs["state_select"].value = "All states"
        refs["status_select"].value = "All statuses"
        refs["search_input"].value = ""
        apply_filters()

    def handle_table_click(
        event: events.GenericEventArguments,
    ) -> None:
        arguments = (
            event.args
            if isinstance(event.args, list)
            else [event.args]
        )

        for argument in arguments:
            if (
                isinstance(argument, dict)
                and argument.get("store_id")
            ):
                select_store(argument["store_id"])
                return

    def handle_map_click(
        event: events.GenericEventArguments,
    ) -> None:
        latlng = (
            event.args.get("latlng", {})
            if isinstance(event.args, dict)
            else {}
        )

        if "lat" not in latlng or "lng" not in latlng:
            return

        nearest = min(
            stores,
            key=lambda store: _haversine_km(
                latlng["lat"],
                latlng["lng"],
                store["lat"],
                store["lon"],
            ),
        )

        distance = _haversine_km(
            latlng["lat"],
            latlng["lng"],
            nearest["lat"],
            nearest["lon"],
        )

        if distance <= 85:
            select_store(
                nearest["store_id"],
                move_to_top=True,
                notify=True,
            )

    network_kpis = build_network_kpis(stores)
    selected = stores[0]

    with app_shell(
        active_page="network",
        title="Network Intelligence",
        subtitle=(
            "A single operating view of store performance, assortment health "
            "and inventory pressure across a five-location Swayamvar demo network."
        ),
    ):
        with ui.row().classes(
            "w-full items-end justify-between gap-4 mb-4"
        ):
            with ui.row().classes(
                "items-end gap-3 flex-wrap"
            ):
                refs["state_select"] = ui.select(
                    options=[
                        "All states",
                        "Telangana",
                        "Andhra Pradesh",
                    ],
                    value="All states",
                    label="State",
                    on_change=apply_filters,
                ).props(
                    "outlined dense options-dense"
                ).classes("w-52")

                refs["status_select"] = ui.select(
                    options=[
                        "All statuses",
                        "Strong",
                        "Watch",
                        "At risk",
                    ],
                    value="All statuses",
                    label="Performance",
                    on_change=apply_filters,
                ).props(
                    "outlined dense options-dense"
                ).classes("w-48")

                refs["search_input"] = ui.input(
                    label="Search store or city",
                    placeholder="e.g. Hyderabad",
                    on_change=apply_filters,
                ).props(
                    "outlined dense clearable debounce=250"
                ).classes("w-64")

                ui.button(
                    "Clear",
                    icon="restart_alt",
                    on_click=clear_filters,
                ).props(
                    "flat no-caps"
                ).style(
                    "color: var(--sw-burgundy);"
                )

            refs["filter_result"] = ui.label(
                "5 stores shown"
            ).classes("text-xs muted")

        with ui.grid(columns=6).classes(
            "w-full gap-4 "
            "max-[1350px]:grid-cols-3 "
            "max-[900px]:grid-cols-2 "
            "max-[620px]:grid-cols-1"
        ):
            (
                refs["net_sales"],
                refs["net_sales_sub"],
            ) = _metric_card(
                "NET SALES",
                format_inr(network_kpis["net_sales"]),
                "5 stores in view",
                "payments",
            )

            (
                refs["gross_margin"],
                refs["gross_margin_sub"],
            ) = _metric_card(
                "GROSS MARGIN",
                f"{network_kpis['gross_margin_pct']:.1f}%",
                "Sales-weighted network margin",
                "percent",
            )

            (
                refs["sell_through"],
                refs["sell_through_sub"],
            ) = _metric_card(
                "SELL-THROUGH",
                f"{network_kpis['sell_through_pct']:.1f}%",
                "Inventory-weighted",
                "speed",
            )

            (
                refs["inventory_value"],
                refs["inventory_value_sub"],
            ) = _metric_card(
                "INVENTORY VALUE",
                format_inr(network_kpis["inventory_value"]),
                "Current stock at retail",
                "inventory_2",
            )

            (
                refs["inventory_turns"],
                refs["inventory_turns_sub"],
            ) = _metric_card(
                "INVENTORY TURNS",
                f"{network_kpis['inventory_turns']:.1f}x",
                "Annualized from stock cover",
                "autorenew",
            )

            (
                refs["sales_per_sq_ft"],
                refs["sales_per_sq_ft_sub"],
            ) = _metric_card(
                "SALES / SQ FT",
                format_inr(network_kpis["sales_per_sq_ft"]),
                "Monthly store productivity",
                "square_foot",
            )

        ui.element("div").style("height: 18px;")

        with ui.grid(columns=12).classes(
            "network-pair-grid w-full gap-4 max-[1120px]:grid-cols-1"
        ):
            with ui.card().classes(
                "surface-card col-span-8 p-5 w-full h-full flex flex-col "
                "max-[1120px]:col-span-1"
            ):
                with ui.row().classes(
                    "w-full items-start justify-between gap-4"
                ):
                    with ui.column().classes("gap-0"):
                        ui.label(
                            "Store Network"
                        ).classes("section-title")

                        ui.label(
                            "Five real Swayamvar retail locations. "
                            "Click a store dot to open its operating profile."
                        ).classes("text-xs muted")

                    with ui.row().classes(
                        "gap-3 items-center flex-wrap"
                    ):
                        for status, color in STATUS_COLORS.items():
                            with ui.row().classes(
                                "gap-1 items-center no-wrap"
                            ):
                                ui.element("span").style(
                                    "width:9px;"
                                    "height:9px;"
                                    "border-radius:50%;"
                                    f"background:{color};"
                                    "display:inline-block;"
                                )
                                ui.label(status).classes(
                                    "text-[10px] muted"
                                )

                refs["map"] = ui.leaflet(
                    center=MAP_CENTER,
                    zoom=MAP_ZOOM,
                ).classes(
                    "network-map w-full mt-4 flex-1 min-h-0"
                ).style(
                    "flex: 1 1 0; min-height: 0; height: auto !important;"
                )

                refs["map"].on(
                    "map-click",
                    handle_map_click,
                )

                for store in stores:
                    refs["map"].generic_layer(
                        name="circleMarker",
                        args=[
                            (
                                store["lat"],
                                store["lon"],
                            ),
                            {
                                "radius": 8,
                                "color": "#FFFFFF",
                                "weight": 2,
                                "fillColor": STATUS_COLORS[
                                    store["status"]
                                ],
                                "fillOpacity": 0.94,
                                "bubblingMouseEvents": True,
                            },
                        ],
                    )

                refs["highlight_layer"] = refs["map"].generic_layer(
                    name="circleMarker",
                    args=[
                        (
                            selected["lat"],
                            selected["lon"],
                        ),
                        {
                            "radius": 14,
                            "color": BURGUNDY,
                            "weight": 4,
                            "fillColor": GOLD,
                            "fillOpacity": 0.35,
                            "bubblingMouseEvents": True,
                        },
                    ],
                )

            with ui.card().classes(
                "network-detail network-detail-card col-span-4 p-5 w-full "
                "max-[1120px]:col-span-1"
            ):
                with ui.row().classes(
                    "w-full items-start justify-between gap-3"
                ):
                    with ui.column().classes("gap-0 min-w-0"):
                        refs["selected_name"] = ui.label(
                            selected["store_name"]
                        ).classes(
                            "text-xl font-extrabold leading-tight"
                        )

                        refs["selected_location"] = ui.label(
                            f"{selected['city']} · "
                            f"{selected['state']} · "
                            f"{selected['format']}"
                        ).classes(
                            "text-xs text-white/65"
                        )

                    refs["selected_status"] = ui.badge(
                        selected["status"].upper()
                    ).style(
                        f"background:"
                        f"{STATUS_COLORS[selected['status']]};"
                        "color:white;"
                    )

                refs["selected_address"] = ui.label(
                    selected["address"]
                ).classes(
                    "text-[11px] leading-relaxed "
                    "text-white/55 mt-2"
                )

                ui.separator().classes("opacity-20 my-4")

                with ui.grid(columns=2).classes(
                    "w-full gap-3"
                ):
                    summary_metrics = [
                        (
                            "NET SALES",
                            "selected_sales",
                            format_inr(selected["monthly_sales"]),
                        ),
                        (
                            "30-DAY FORECAST",
                            "selected_forecast",
                            format_inr(
                                selected["forecast_30d_sales"]
                            ),
                        ),
                        (
                            "INVENTORY VALUE",
                            "selected_inventory",
                            format_inr(
                                selected["inventory_value"]
                            ),
                        ),
                        (
                            "SELL-THROUGH",
                            "selected_sell_through",
                            f"{selected['sell_through_pct']:.1f}%",
                        ),
                    ]

                    for title, ref_name, value in summary_metrics:
                        with ui.column().classes("gap-0"):
                            ui.label(title).classes(
                                "text-[9px] tracking-wider "
                                "text-white/50"
                            )

                            refs[ref_name] = ui.label(
                                value
                            ).classes(
                                "text-lg font-bold"
                            )

                ui.separator().classes("opacity-20 my-4")

                detail_metrics = [
                    (
                        "Sales growth",
                        "selected_growth",
                        f"{selected['sales_growth_pct']:+.1f}%",
                    ),
                    (
                        "Gross margin",
                        "selected_margin",
                        f"{selected['gross_margin_pct']:.1f}%",
                    ),
                    (
                        "ASP",
                        "selected_asp",
                        format_inr(selected["asp"]),
                    ),
                    (
                        "Avg basket value",
                        "selected_basket",
                        format_inr(
                            selected["average_basket_value"]
                        ),
                    ),
                    (
                        "Units / transaction",
                        "selected_upt",
                        f"{selected['units_per_transaction']:.2f}",
                    ),
                    (
                        "Sales / sq ft",
                        "selected_sales_sqft",
                        format_inr(
                            selected["sales_per_sq_ft"]
                        ),
                    ),
                    (
                        "Inventory turns",
                        "selected_turns",
                        f"{selected['inventory_turns']:.1f}x",
                    ),
                    (
                        "Aged inventory",
                        "selected_aged",
                        f"{selected['aged_inventory_pct']:.1f}%",
                    ),
                    (
                        "Stock cover",
                        "selected_stock_cover",
                        f"{selected['stock_cover_weeks']:.1f} weeks",
                    ),
                    (
                        "SKU availability",
                        "selected_availability",
                        f"{selected['sku_availability_pct']:.1f}%",
                    ),
                    (
                        "At-risk SKUs",
                        "selected_risk_skus",
                        str(selected["at_risk_skus"]),
                    ),
                    (
                        "Top category",
                        "selected_top_category",
                        selected["top_category"],
                    ),
                ]

                with ui.grid(columns=2).classes(
                    "w-full gap-x-4 gap-y-3"
                ):
                    for label, ref_name, value in detail_metrics:
                        with ui.column().classes("gap-0"):
                            ui.label(label.upper()).classes(
                                "text-[9px] tracking-wider "
                                "text-white/45"
                            )

                            refs[ref_name] = ui.label(
                                value
                            ).classes(
                                "text-sm font-semibold"
                            )

                observation, action = build_store_observation(
                    selected
                )

                ui.separator().classes("opacity-20 my-4")

                ui.label(
                    "INTELLIGENCE OBSERVATION"
                ).classes(
                    "text-[10px] font-bold tracking-wider "
                    "text-amber-200"
                )

                refs["selected_observation"] = ui.label(
                    observation
                ).classes(
                    "text-sm leading-relaxed text-white/75 mt-2"
                )

                ui.label(
                    "RECOMMENDED ACTION"
                ).classes(
                    "text-[10px] font-bold tracking-wider "
                    "text-amber-200 mt-4"
                )

                refs["selected_action"] = ui.label(
                    action
                ).classes(
                    "text-sm leading-relaxed text-white/80 mt-1"
                )

        ui.element("div").style("height: 18px;")

        with ui.card().classes(
            "surface-card w-full p-5 network-table"
        ):
            with ui.row().classes(
                "w-full items-start justify-between gap-4"
            ):
                with ui.column().classes("gap-0"):
                    ui.label(
                        "Store Performance"
                    ).classes("section-title")

                    ui.label(
                        "Click any row to synchronize the map and "
                        "selected-store intelligence panel."
                    ).classes("text-xs muted")

                ui.badge(
                    "MONTHLY VIEW"
                ).props("outline").style(
                    "color: var(--sw-burgundy);"
                )

            refs["table"] = ui.table(
                columns=TABLE_COLUMNS,
                rows=stores.copy(),
                row_key="store_id",
                selection="single",
                pagination={
                    "rowsPerPage": 10,
                },
            ).props(
                "flat bordered dense "
                "separator=horizontal "
                "hide-selected-banner"
            ).classes(
                "w-full mt-4"
            )

            refs["table"].on(
                "rowClick",
                handle_table_click,
                [
                    [],
                    ["store_id"],
                    None,
                ],
            )

            refs["table"].selected.append(selected)
            refs["table"].update()

        with ui.row().classes(
            "w-full items-center justify-between mt-3 px-1 gap-3"
        ):
            ui.label(
                "Store geography · Network performance view."
            ).classes(
                "text-[11px] muted"
            )

            ui.label(
                "MVP-SWMVR · Network Intelligence v0.2"
            ).classes(
                "text-[11px] font-bold"
            ).style(
                "color: var(--sw-burgundy);"
            )
