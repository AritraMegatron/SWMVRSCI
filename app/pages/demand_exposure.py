from __future__ import annotations

import asyncio
from typing import Any

from nicegui import events, ui

from app.data.demand_signal_catalog import (
    demand_signal_lift_pct,
    get_demand_signals,
)
from app.data.product_catalog import (
    PRODUCTS,
    PRODUCTS_BY_ID,
    SIZES,
)
from app.data.store_catalog import STORES
from app.services.demand_service import (
    build_demand_records,
    shortage_units,
    find_record,
    horizon_forecast,
    network_summary,
    variant_matrix,
)
from app.services.network_service import format_inr
from app.services.replenishment_service import (
    DEFAULT_TRANSFER_THRESHOLD_KM,
    apply_manual_override,
    build_replenishment_plan,
    get_action,
    summarize_plan,
    transfer_source_candidates,
)
from app.session_ui import require_login
from app.shell import app_shell


def _metric_cell_style(
    value: int,
    metric: str,
    max_abs_value: int,
    *,
    selected: bool = False,
) -> str:
    max_abs_value = max(1, max_abs_value)
    intensity = min(
        1.0,
        abs(value) / max_abs_value,
    )

    if metric == "Shortage":
        if value > 0:
            background = (
                f"rgba(163, 61, 69, {0.10 + intensity * 0.30:.3f})"
            )
            text_color = "#7D1F2A"
        else:
            background = (
                f"rgba(46, 113, 86, {0.08 + intensity * 0.24:.3f})"
            )
            text_color = "#245943"
    elif metric == "Stock":
        background = (
            f"rgba(197, 154, 84, {0.08 + intensity * 0.28:.3f})"
        )
        text_color = "#6F4A12"
    else:
        background = (
            f"rgba(101, 29, 50, {0.07 + intensity * 0.24:.3f})"
        )
        text_color = "#541629"

    border = (
        "2px solid #651D32"
        if selected
        else "1px solid #E7DED5"
    )

    return (
        f"background:{background};"
        f"color:{text_color};"
        f"border:{border};"
        "border-radius:9px;"
        "min-height:58px;"
        "transition:all .15s ease;"
    )


def _dashboard_metric_card(
    title: str,
    value: str,
    subtitle: str,
    icon: str,
) -> None:
    with ui.card().classes(
        "metric-card p-4 w-full"
    ):
        with ui.row().classes(
            "w-full items-start justify-between no-wrap"
        ):
            with ui.column().classes("gap-1"):
                ui.label(title).classes(
                    "text-[10px] font-bold tracking-wider muted"
                )

                ui.label(value).classes(
                    "text-2xl font-bold tracking-tight"
                )

                ui.label(subtitle).classes(
                    "text-[11px] muted"
                )

            with ui.element("div").classes("metric-icon"):
                ui.icon(icon).classes("text-xl")


@ui.page("/demand-exposure")
def demand_exposure_page():
    if not require_login():
        return

    records = build_demand_records(
        STORES,
        PRODUCTS,
    )

    state: dict[str, Any] = {
        "horizon": 30,
        "metric": "Forecast",
        "store_id": STORES[0]["store_id"],
        "category_id": PRODUCTS[0]["category_id"],
        "color": PRODUCTS[0]["colors"][0],
        "size": 42,
    }

    plan_state: dict[str, Any] = {
        "plan": None,
        "threshold_km": DEFAULT_TRANSFER_THRESHOLD_KM,
        "selected_action_id": None,
        "action_filter": "ALL",
        "destination_filter": "ALL",
        "category_filter": "ALL",
        "search": "",
    }

    stores_by_id = {
        store["store_id"]: store
        for store in STORES
    }

    def set_horizon(event: Any) -> None:
        state["horizon"] = int(event.value)
        dashboard.refresh()

    def set_metric(event: Any) -> None:
        state["metric"] = str(event.value)
        dashboard.refresh()

    def set_store(event: Any) -> None:
        state["store_id"] = str(event.value)
        dashboard.refresh()

    def set_category(event: Any) -> None:
        state["category_id"] = str(event.value)

        selected_product = PRODUCTS_BY_ID[
            state["category_id"]
        ]

        if state["color"] not in selected_product["colors"]:
            state["color"] = selected_product["colors"][0]

        dashboard.refresh()

    def select_variant(
        color: str,
        size: int,
    ) -> None:
        state["color"] = color
        state["size"] = size
        dashboard.refresh()

    @ui.refreshable
    def dashboard() -> None:
        horizon = state["horizon"]
        metric = state["metric"]

        selected_store = stores_by_id[
            state["store_id"]
        ]

        selected_product = PRODUCTS_BY_ID[
            state["category_id"]
        ]

        selected_record = find_record(
            records,
            store_id=state["store_id"],
            category_id=state["category_id"],
            color=state["color"],
            size=state["size"],
        )

        selected_forecast = horizon_forecast(
            selected_record,
            horizon,
        )

        selected_shortage = shortage_units(
            selected_record,
            horizon,
        )

        pair_matrix = variant_matrix(
            records,
            store_id=state["store_id"],
            category_id=state["category_id"],
            horizon=horizon,
            metric=metric,
        )

        matrix_values = [
            cell["display_value"]
            for cell in pair_matrix.values()
        ]

        matrix_max = max(
            1,
            max(abs(value) for value in matrix_values),
        )

        with ui.grid(columns=12).classes(
            "w-full gap-4 items-stretch max-[1150px]:grid-cols-1"
        ):
            with ui.card().classes(
                "surface-card col-span-8 p-5 w-full h-full "
                "max-[1150px]:col-span-1"
            ):
                with ui.row().classes(
                    "w-full items-start justify-between gap-4"
                ):
                    with ui.column().classes("gap-0"):
                        ui.label(
                            f"{selected_product['category_name']} "
                            f"· {selected_store['store_name']}"
                        ).classes("section-title")

                        ui.label(
                            f"Size × color {metric.lower()} matrix · "
                            f"{selected_store['city']} · next {horizon} days"
                        ).classes("text-xs muted")

                    ui.badge(
                        "20 SKUs"
                    ).style(
                        "background:#F5EEE4;"
                        "color:#651D32;"
                    )

                ui.element("div").style(
                    "height:14px;"
                )

                colors = selected_product[
                    "colors"
                ]

                with ui.grid(columns=6).classes(
                    "w-full gap-2"
                ):
                    ui.label("SIZE").classes(
                        "text-[10px] font-bold "
                        "tracking-wider muted self-end pb-2"
                    )

                    for color in colors:
                        ui.label(color).classes(
                            "text-[10px] font-bold "
                            "text-center self-end pb-2"
                        )

                    for size in SIZES:
                        ui.label(str(size)).classes(
                            "text-sm font-bold self-center"
                        )

                        for color in colors:
                            cell = pair_matrix[
                                (
                                    size,
                                    color,
                                )
                            ]

                            value = cell[
                                "display_value"
                            ]

                            is_selected = (
                                state["color"] == color
                                and state["size"] == size
                            )

                            display = (
                                f"{value:+d}"
                                if metric == "Shortage"
                                else str(value)
                            )

                            with ui.column().classes(
                                "w-full items-center justify-center "
                                "gap-0 cursor-pointer p-2"
                            ).style(
                                _metric_cell_style(
                                    value,
                                    metric,
                                    matrix_max,
                                    selected=is_selected,
                                )
                            ).on(
                                "click",
                                lambda
                                c=color,
                                s=size:
                                select_variant(c, s),
                            ):
                                ui.label(
                                    display
                                ).classes(
                                    "text-base font-extrabold"
                                )

                                ui.label(
                                    cell["sku"]
                                ).classes(
                                    "text-[8px] opacity-60"
                                )

            with ui.card().classes(
                "network-detail col-span-4 p-5 w-full "
                "max-[1150px]:col-span-1"
            ):
                ui.label(
                    "SELECTED SKU"
                ).classes(
                    "text-[10px] font-bold "
                    "tracking-wider text-amber-200"
                )

                ui.label(
                    selected_record["sku"]
                ).classes(
                    "text-2xl font-extrabold mt-1"
                )

                ui.label(
                    f"{selected_product['category_name']} · "
                    f"{selected_record['color']} · "
                    f"Size {selected_record['size']}"
                ).classes(
                    "text-xs text-white/65"
                )

                ui.label(
                    f"{selected_store['store_name']} · "
                    f"{selected_store['city']}"
                ).classes(
                    "text-xs text-white/55 mt-1"
                )

                ui.separator().classes(
                    "opacity-20 my-4"
                )

                with ui.grid(columns=2).classes(
                    "w-full gap-x-4 gap-y-4"
                ):
                    details = [
                        (
                            f"{horizon}-DAY FORECAST",
                            f"{selected_forecast} units",
                        ),
                        (
                            "CURRENT STOCK",
                            f"{selected_record['stock']} units",
                        ),
                        (
                            "INBOUND",
                            f"{selected_record['inbound']} units",
                        ),
                        (
                            "SHORTAGE",
                            f"{selected_shortage:+d} units",
                        ),
                        (
                            "UNIT RETAIL",
                            format_inr(
                                selected_record["price"]
                            ),
                        ),
                        (
                            "FORECAST VALUE",
                            format_inr(
                                selected_forecast
                                * selected_record["price"]
                            ),
                        ),
                    ]

                    for label, value in details:
                        with ui.column().classes("gap-0"):
                            ui.label(label).classes(
                                "text-[9px] tracking-wider "
                                "text-white/45"
                            )

                            ui.label(value).classes(
                                "text-sm font-bold"
                            )

                ui.separator().classes(
                    "opacity-20 my-4"
                )

                if selected_shortage > 0:
                    status = "SHORTAGE RISK"
                    status_color = "#F3C0C4"
                    narrative = (
                        f"Demand exceeds current stock plus inbound by "
                        f"{selected_shortage} units. This exact "
                        "size-color combination is at risk of stocking out."
                    )
                elif selected_shortage <= -max(
                    2,
                    round(
                        selected_forecast
                        * 0.65
                    ),
                ):
                    status = "SURPLUS STOCK"
                    status_color = "#F5D78E"
                    narrative = (
                        f"This SKU carries {abs(selected_shortage)} units "
                        "above forecast need. It is a candidate for "
                        "reduced replenishment or transfer."
                    )
                else:
                    status = "BALANCED"
                    status_color = "#BCE4CF"
                    narrative = (
                        "Available plus inbound stock is broadly "
                        "aligned with expected demand for this "
                        "planning horizon."
                    )

                ui.label(status).style(
                    f"color:{status_color};"
                ).classes(
                    "text-[10px] font-bold tracking-wider"
                )

                ui.label(narrative).classes(
                    "text-sm leading-relaxed "
                    "text-white/80 mt-2"
                )

        ui.element("div").style(
            "height:18px;"
        )

        demand_signals = get_demand_signals(
            state["store_id"],
            state["category_id"],
        )

        with ui.grid(columns=12).classes(
            "w-full gap-4 max-[1150px]:grid-cols-1"
        ):
            with ui.card().classes(
                "surface-card col-span-8 p-5 w-full "
                "max-[1150px]:col-span-1"
            ):
                with ui.row().classes(
                    "w-full items-start justify-between gap-4"
                ):
                    with ui.column().classes("gap-0"):
                        ui.label(
                            "Demand Signals"
                        ).classes(
                            "section-title"
                        )

                        ui.label(
                            f"Signals used to shape the "
                            f"{selected_product['category_name']} forecast "
                            f"for {selected_store['store_name']}."
                        ).classes(
                            "text-xs muted"
                        )

                    ui.badge(
                        f"NET SIGNAL {demand_signal_lift_pct(state['store_id'], state['category_id']):+.1f}%"
                    ).style(
                        "background:#F5EEE4;"
                        "color:#651D32;"
                    )

                with ui.column().classes(
                    "w-full gap-3 mt-4"
                ):
                    for signal in demand_signals:
                        with ui.row().classes(
                            "w-full items-center gap-4 "
                            "rounded-xl p-4 no-wrap"
                        ).style(
                            "border:1px solid #E7DED5;"
                            "background:#FCF9F5;"
                        ):
                            with ui.element("div").style(
                                "width:42px;"
                                "height:42px;"
                                "border-radius:10px;"
                                "background:rgba(101,29,50,.08);"
                                "display:flex;"
                                "align-items:center;"
                                "justify-content:center;"
                                "flex:0 0 auto;"
                            ):
                                ui.icon(
                                    "location_on"
                                    if signal["type"] == "Outlet signal"
                                    else "checkroom"
                                ).style(
                                    "color:#651D32;"
                                    "font-size:21px;"
                                )

                            with ui.column().classes(
                                "gap-1 flex-1 min-w-0"
                            ):
                                with ui.row().classes(
                                    "items-center gap-2 flex-wrap"
                                ):
                                    ui.label(
                                        signal["name"]
                                    ).classes(
                                        "text-sm font-bold"
                                    )

                                    ui.badge(
                                        signal["type"].upper()
                                    ).props(
                                        "outline"
                                    ).style(
                                        "color:#651D32;"
                                        "font-size:8px;"
                                    )

                                ui.label(
                                    signal["description"]
                                ).classes(
                                    "text-[11px] muted leading-relaxed"
                                )

                            with ui.column().classes(
                                "gap-0 items-end"
                            ):
                                impact = signal[
                                    "impact_pct"
                                ]

                                ui.label(
                                    f"{impact:+.1f}%"
                                ).classes(
                                    "text-base font-extrabold"
                                ).style(
                                    "color:"
                                    + (
                                        "#2E7156"
                                        if impact >= 0
                                        else "#A33D45"
                                    )
                                    + ";"
                                )

                                ui.label(
                                    signal["confidence"]
                                ).classes(
                                    "text-[9px] muted"
                                )

            with ui.card().classes(
                "surface-card col-span-4 p-5 w-full h-full flex flex-col "
                "max-[1150px]:col-span-1"
            ):
                with ui.row().classes(
                    "w-full items-start justify-between"
                ):
                    with ui.column().classes("gap-0"):
                        ui.label(
                            "Product Visual"
                        ).classes(
                            "section-title"
                        )

                        ui.label(
                            f"{selected_product['category_name']} · "
                            f"{selected_record['color']}"
                        ).classes(
                            "text-xs muted"
                        )

                image_url = (
                    f"/swmvr-static/"
                    f"{selected_product['image_folder']}/"
                    f"{selected_product['image_prefix']}_"
                    f"{selected_record['color']}.jpeg"
                )

                with ui.element("div").classes(
                    "w-full mt-4 rounded-xl flex-1 min-h-[360px] "
                    "overflow-hidden flex items-center justify-center"
                ).style(
                    "background:#F7F3EE;"
                    "border:1px solid #E7DED5;"
                ):
                    ui.image(
                        image_url
                    ).props(
                        "fit=contain"
                    ).classes(
                        "w-full h-full"
                    ).style(
                        "width:100%;"
                        "height:100%;"
                        "object-fit:contain;"
                        "display:block;"
                    )


    def _filtered_plan_actions() -> list[dict]:
        plan = plan_state["plan"]

        if not plan:
            return []

        search = (
            plan_state["search"]
            .strip()
            .lower()
        )

        actions = []

        for action in plan["actions"]:
            if (
                plan_state["action_filter"]
                != "ALL"
                and action["action_type"]
                != plan_state["action_filter"]
            ):
                continue

            if (
                plan_state["destination_filter"]
                != "ALL"
                and action["destination_id"]
                != plan_state["destination_filter"]
            ):
                continue

            if (
                plan_state["category_filter"]
                != "ALL"
                and action["category_id"]
                != plan_state["category_filter"]
            ):
                continue

            searchable = " ".join(
                [
                    action["sku"],
                    action["category_name"],
                    action["destination_name"],
                    action["destination_city"],
                    action["source_name"],
                ]
            ).lower()

            if (
                search
                and search not in searchable
            ):
                continue

            actions.append(action)

        return actions

    def _select_plan_action(
        action_id: str,
    ) -> None:
        plan_state[
            "selected_action_id"
        ] = action_id

        plan_workspace.refresh()

    def _handle_plan_row_click(
        event: events.GenericEventArguments,
    ) -> None:
        arguments = (
            event.args
            if isinstance(
                event.args,
                list,
            )
            else [event.args]
        )

        for argument in arguments:
            if (
                isinstance(
                    argument,
                    dict,
                )
                and argument.get(
                    "action_id"
                )
            ):
                _select_plan_action(
                    argument[
                        "action_id"
                    ]
                )
                return

    def _set_plan_action_filter(
        event: Any,
    ) -> None:
        plan_state[
            "action_filter"
        ] = str(event.value)

        plan_workspace.refresh()

    def _set_plan_destination_filter(
        event: Any,
    ) -> None:
        plan_state[
            "destination_filter"
        ] = str(event.value)

        plan_workspace.refresh()

    def _set_plan_category_filter(
        event: Any,
    ) -> None:
        plan_state[
            "category_filter"
        ] = str(event.value)

        plan_workspace.refresh()

    def _set_plan_search(
        event: Any,
    ) -> None:
        plan_state[
            "search"
        ] = str(
            event.value or ""
        )

        plan_workspace.refresh()

    def _recalculate_plan(
        threshold_value: float | int | None,
    ) -> None:
        threshold = float(
            threshold_value
            or DEFAULT_TRANSFER_THRESHOLD_KM
        )

        threshold = max(
            10.0,
            threshold,
        )

        plan_state[
            "threshold_km"
        ] = threshold

        plan = build_replenishment_plan(
            records,
            STORES,
            horizon=state["horizon"],
            transfer_threshold_km=threshold,
        )

        plan_state[
            "plan"
        ] = plan

        plan_state[
            "selected_action_id"
        ] = (
            plan["actions"][0][
                "action_id"
            ]
            if plan["actions"]
            else None
        )

        plan_workspace.refresh()

        ui.notify(
            (
                "Plan recalculated with "
                f"{threshold:.0f} km "
                "transfer threshold."
            ),
            type="positive",
            position="top",
        )

    def _apply_override(
        action_type_input: Any,
        quantity_input: Any,
        source_input: Any,
    ) -> None:
        plan = plan_state["plan"]

        if not plan:
            return

        action_id = plan_state[
            "selected_action_id"
        ]

        if not action_id:
            return

        action_type = str(
            action_type_input.value
        )

        quantity = int(
            quantity_input.value
            or 1
        )

        source_id = (
            str(source_input.value)
            if source_input.value
            else None
        )

        try:
            apply_manual_override(
                plan=plan,
                action_id=action_id,
                action_type=action_type,
                quantity=quantity,
                source_id=source_id,
                records=records,
                stores=STORES,
            )
        except ValueError as error:
            ui.notify(
                str(error),
                type="warning",
                position="top",
            )
            return

        summarize_plan(plan)
        plan_workspace.refresh()

        ui.notify(
            "Manual override applied.",
            type="positive",
            position="top",
        )

    @ui.refreshable
    def plan_workspace() -> None:
        plan = plan_state["plan"]

        if not plan:
            with ui.column().classes(
                "w-full items-center "
                "justify-center py-20 gap-2"
            ):
                ui.icon(
                    "inventory_2"
                ).classes(
                    "text-4xl"
                ).style(
                    "color:#651D32;"
                )

                ui.label(
                    "No action plan generated yet."
                ).classes(
                    "text-lg font-bold"
                )

            return

        summary = summarize_plan(plan)

        with ui.row().classes(
            "w-full items-end "
            "justify-between gap-4 flex-wrap"
        ):
            with ui.row().classes(
                "items-end gap-3 flex-wrap"
            ):
                with ui.column().classes(
                    "gap-1"
                ):
                    ui.label(
                        "TRANSFER DISTANCE THRESHOLD"
                    ).classes(
                        "text-[9px] font-bold "
                        "tracking-wider muted"
                    )

                    threshold_input = ui.number(
                        value=plan[
                            "transfer_threshold_km"
                        ],
                        min=10,
                        max=1000,
                        step=10,
                        suffix=" km",
                    ).props(
                        "outlined dense"
                    ).classes(
                        "w-44"
                    )

                ui.button(
                    "Recalculate Plan",
                    icon="refresh",
                    on_click=lambda:
                    _recalculate_plan(
                        threshold_input.value
                    ),
                ).props(
                    "unelevated no-caps"
                ).style(
                    "background:#651D32;"
                    "color:white;"
                )

            ui.label(
                (
                    f"Network-wide · {plan['horizon']}-day horizon · "
                    f"{len(plan['actions'])} planned actions"
                )
            ).classes(
                "text-[11px] muted"
            )

        with ui.grid(columns=5).classes(
            "w-full gap-3 mt-4 "
            "max-[1100px]:grid-cols-2 "
            "max-[700px]:grid-cols-1"
        ):
            _dashboard_metric_card(
                "SHORTAGE UNITS",
                f"{summary['shortage_units']:,}",
                "Across all outlet-SKU positions",
                "warning_amber",
            )

            _dashboard_metric_card(
                "TRANSFER UNITS",
                f"{summary['transfer_units']:,}",
                (
                    f"{summary['transfer_actions']} "
                    "transfer actions"
                ),
                "swap_horiz",
            )

            _dashboard_metric_card(
                "PO UNITS",
                f"{summary['po_units']:,}",
                (
                    f"{summary['po_actions']} "
                    "purchase-order actions"
                ),
                "shopping_cart_checkout",
            )

            _dashboard_metric_card(
                "UNITS COVERED",
                f"{summary['coverage_pct']:.0f}%",
                "Shortage covered by plan",
                "task_alt",
            )

            _dashboard_metric_card(
                "OVERRIDES",
                str(
                    summary[
                        "overridden_actions"
                    ]
                ),
                "Operator-edited actions",
                "edit_note",
            )

        with ui.row().classes(
            "w-full items-end gap-3 "
            "mt-4 flex-wrap"
        ):
            ui.toggle(
                {
                    "ALL": "All Actions",
                    "TRANSFER": "Transfers",
                    "PO": "Purchase Orders",
                },
                value=plan_state[
                    "action_filter"
                ],
                on_change=_set_plan_action_filter,
            ).props(
                "no-caps unelevated"
            ).style(
                "color:#651D32;"
            )

            ui.select(
                options={
                    "ALL": "All destinations",
                    **{
                        store["store_id"]:
                        f"{store['store_name']} · {store['city']}"
                        for store in STORES
                    },
                },
                value=plan_state[
                    "destination_filter"
                ],
                label="Destination",
                on_change=_set_plan_destination_filter,
            ).props(
                "outlined dense options-dense"
            ).classes(
                "w-60"
            )

            ui.select(
                options={
                    "ALL": "All categories",
                    **{
                        product["category_id"]:
                        product["category_name"]
                        for product in PRODUCTS
                    },
                },
                value=plan_state[
                    "category_filter"
                ],
                label="Category",
                on_change=_set_plan_category_filter,
            ).props(
                "outlined dense options-dense"
            ).classes(
                "w-52"
            )

            ui.input(
                value=plan_state[
                    "search"
                ],
                label="Search SKU / store",
                on_change=_set_plan_search,
            ).props(
                "outlined dense clearable "
                "debounce=250"
            ).classes(
                "w-60"
            )

        visible_actions = (
            _filtered_plan_actions()
        )

        with ui.grid(columns=12).classes(
            "w-full gap-4 mt-2 "
            "max-[1200px]:grid-cols-1"
        ):
            with ui.card().classes(
                "surface-card col-span-8 "
                "p-4 w-full "
                "max-[1200px]:col-span-1"
            ):
                columns = [
                    {
                        "name": "destination_name",
                        "label": "Destination",
                        "field": "destination_name",
                        "align": "left",
                    },
                    {
                        "name": "sku",
                        "label": "SKU",
                        "field": "sku",
                        "align": "left",
                    },
                    {
                        "name": "category_name",
                        "label": "Category",
                        "field": "category_name",
                        "align": "left",
                    },
                    {
                        "name": "shortage_units",
                        "label": "Need",
                        "field": "shortage_units",
                        "align": "right",
                    },
                    {
                        "name": "action_type",
                        "label": "Action",
                        "field": "action_type",
                        "align": "left",
                    },
                    {
                        "name": "source_name",
                        "label": "Source / Vendor",
                        "field": "source_name",
                        "align": "left",
                    },
                    {
                        "name": "distance_display",
                        "label": "Distance",
                        "field": "distance_display",
                        "align": "right",
                    },
                    {
                        "name": "qty",
                        "label": "Qty",
                        "field": "qty",
                        "align": "right",
                    },
                    {
                        "name": "override_display",
                        "label": "Status",
                        "field": "override_display",
                        "align": "left",
                    },
                ]

                table_rows = [
                    {
                        **action,
                        "distance_display": (
                            f"{action['distance_km']:.0f} km"
                            if action[
                                "distance_km"
                            ] is not None
                            else "—"
                        ),
                        "override_display": (
                            "Overridden"
                            if action.get(
                                "overridden",
                                False,
                            )
                            else "Recommended"
                        ),
                    }
                    for action in visible_actions
                ]

                table = ui.table(
                    columns=columns,
                    rows=table_rows,
                    row_key="action_id",
                    pagination={
                        "rowsPerPage": 24,
                    },
                ).props(
                    "flat bordered dense "
                    "separator=horizontal"
                ).classes(
                    "w-full"
                )

                table.on(
                    "rowClick",
                    _handle_plan_row_click,
                    [
                        [],
                        ["action_id"],
                        None,
                    ],
                )

                ui.label(
                    (
                        f"{len(table_rows)} actions shown. "
                        "Click a row to review or override."
                    )
                ).classes(
                    "text-[10px] muted mt-2"
                )

            with ui.card().classes(
                "network-detail col-span-4 "
                "p-5 w-full "
                "max-[1200px]:col-span-1"
            ):
                selected_action = get_action(
                    plan,
                    plan_state[
                        "selected_action_id"
                    ],
                )

                if not selected_action:
                    ui.label(
                        "SELECT AN ACTION"
                    ).classes(
                        "text-[10px] font-bold "
                        "tracking-wider "
                        "text-amber-200"
                    )

                    ui.label(
                        "Choose a row to inspect "
                        "the recommendation."
                    ).classes(
                        "text-sm text-white/70 mt-2"
                    )

                else:
                    ui.label(
                        "SELECTED ACTION"
                    ).classes(
                        "text-[10px] font-bold "
                        "tracking-wider "
                        "text-amber-200"
                    )

                    ui.label(
                        selected_action[
                            "sku"
                        ]
                    ).classes(
                        "text-2xl "
                        "font-extrabold mt-1"
                    )

                    ui.label(
                        (
                            f"{selected_action['category_name']} · "
                            f"{selected_action['color']} · "
                            f"Size {selected_action['size']}"
                        )
                    ).classes(
                        "text-xs text-white/65"
                    )

                    ui.label(
                        (
                            f"Destination: "
                            f"{selected_action['destination_name']} · "
                            f"{selected_action['destination_city']}"
                        )
                    ).classes(
                        "text-xs text-white/55 mt-1"
                    )

                    ui.separator().classes(
                        "opacity-20 my-4"
                    )

                    with ui.grid(
                        columns=2
                    ).classes(
                        "w-full gap-x-4 gap-y-3"
                    ):
                        detail_values = [
                            (
                                "SHORTAGE",
                                (
                                    f"{selected_action['shortage_units']} "
                                    "units"
                                ),
                            ),
                            (
                                "PLANNED QTY",
                                (
                                    f"{selected_action['qty']} "
                                    "units"
                                ),
                            ),
                            (
                                "ACTION",
                                (
                                    "Transfer"
                                    if selected_action[
                                        "action_type"
                                    ] == "TRANSFER"
                                    else "Purchase Order"
                                ),
                            ),
                            (
                                "DISTANCE",
                                (
                                    f"{selected_action['distance_km']:.0f} km"
                                    if selected_action[
                                        "distance_km"
                                    ] is not None
                                    else "—"
                                ),
                            ),
                        ]

                        for (
                            label,
                            value,
                        ) in detail_values:
                            with ui.column().classes(
                                "gap-0"
                            ):
                                ui.label(
                                    label
                                ).classes(
                                    "text-[9px] "
                                    "tracking-wider "
                                    "text-white/45"
                                )

                                ui.label(
                                    value
                                ).classes(
                                    "text-sm "
                                    "font-bold"
                                )

                    ui.separator().classes(
                        "opacity-20 my-4"
                    )

                    ui.label(
                        "WHY THIS ACTION?"
                    ).classes(
                        "text-[10px] font-bold "
                        "tracking-wider "
                        "text-amber-200"
                    )

                    ui.label(
                        selected_action[
                            "reason"
                        ]
                    ).classes(
                        "text-sm leading-relaxed "
                        "text-white/75 mt-2"
                    )

                    candidates = (
                        transfer_source_candidates(
                            action=selected_action,
                            records=records,
                            stores=STORES,
                            horizon=plan[
                                "horizon"
                            ],
                        )
                    )

                    candidate_options = {
                        candidate[
                            "store_id"
                        ]: (
                            f"{candidate['store_name']} · "
                            f"{candidate['distance_km']:.0f} km · "
                            f"surplus {candidate['available']}"
                        )
                        for candidate in candidates
                    }

                    ui.separator().classes(
                        "opacity-20 my-4"
                    )

                    ui.label(
                        "OPERATOR OVERRIDE"
                    ).classes(
                        "text-[10px] font-bold "
                        "tracking-wider "
                        "text-amber-200"
                    )

                    action_type_input = (
                        ui.select(
                            options={
                                "TRANSFER": "Transfer",
                                "PO": "Purchase Order",
                            },
                            value=selected_action[
                                "action_type"
                            ],
                            label="Action",
                        )
                        .props(
                            "outlined dense "
                            "options-dense "
                            "dark"
                        )
                        .classes(
                            "w-full mt-3"
                        )
                    )

                    quantity_input = (
                        ui.number(
                            value=selected_action[
                                "qty"
                            ],
                            min=1,
                            max=max(
                                1,
                                selected_action[
                                    "shortage_units"
                                ],
                            ),
                            step=1,
                            label="Quantity",
                        )
                        .props(
                            "outlined dense dark"
                        )
                        .classes(
                            "w-full mt-2"
                        )
                    )

                    source_default = (
                        selected_action[
                            "source_id"
                        ]
                        if selected_action[
                            "source_id"
                        ]
                        in candidate_options
                        else (
                            next(
                                iter(
                                    candidate_options
                                ),
                                None,
                            )
                        )
                    )

                    source_input = (
                        ui.select(
                            options=candidate_options,
                            value=source_default,
                            label="Transfer source",
                        )
                        .props(
                            "outlined dense "
                            "options-dense dark"
                        )
                        .classes(
                            "w-full mt-2"
                        )
                    )

                    if candidates:
                        nearest = candidates[
                            0
                        ]

                        threshold_note = (
                            "within threshold"
                            if nearest[
                                "distance_km"
                            ]
                            <= plan[
                                "transfer_threshold_km"
                            ]
                            else "outside threshold"
                        )

                        ui.label(
                            (
                                f"Nearest available source: "
                                f"{nearest['store_name']} · "
                                f"{nearest['distance_km']:.0f} km · "
                                f"{threshold_note}"
                            )
                        ).classes(
                            "text-[10px] "
                            "text-white/55 mt-2"
                        )
                    else:
                        ui.label(
                            "No protected surplus source "
                            "is available for this exact SKU."
                        ).classes(
                            "text-[10px] "
                            "text-white/55 mt-2"
                        )

                    ui.button(
                        "Apply Override",
                        icon="edit",
                        on_click=lambda:
                        _apply_override(
                            action_type_input,
                            quantity_input,
                            source_input,
                        ),
                    ).props(
                        "unelevated no-caps"
                    ).classes(
                        "w-full mt-4"
                    ).style(
                        "background:#C59A54;"
                        "color:#40101F;"
                        "font-weight:700;"
                    )

    progress_refs: dict[
        str,
        Any,
    ] = {}

    with ui.dialog().props(
        "persistent"
    ) as generating_dialog:
        with ui.card().classes(
            "w-[560px] max-w-[92vw] "
            "p-8 rounded-2xl"
        ):
            with ui.column().classes(
                "w-full items-center "
                "gap-3 text-center"
            ):
                with ui.element(
                    "div"
                ).style(
                    "width:56px;"
                    "height:56px;"
                    "border-radius:14px;"
                    "background:rgba(101,29,50,.08);"
                    "display:flex;"
                    "align-items:center;"
                    "justify-content:center;"
                ):
                    ui.icon(
                        "auto_awesome"
                    ).style(
                        "font-size:28px;"
                        "color:#651D32;"
                    )

                ui.label(
                    "Generating Replenishment Action Plan"
                ).classes(
                    "text-xl font-extrabold"
                ).style(
                    "font-family:'Playfair Display',serif;"
                    "color:#40101F;"
                )

                progress_refs[
                    "stage"
                ] = ui.label(
                    "Analyzing network demand..."
                ).classes(
                    "text-sm muted"
                )

                progress_refs[
                    "bar"
                ] = ui.linear_progress(
                    value=0,
                ).props(
                    "rounded size=12px"
                ).classes(
                    "w-full mt-3"
                ).style(
                    "color:#651D32;"
                )

                progress_refs[
                    "detail"
                ] = ui.label(
                    "Scanning all SKU × outlet positions"
                ).classes(
                    "text-[11px] muted"
                )

    with ui.dialog().props(
        "maximized"
    ) as plan_dialog:
        with ui.card().classes(
            "w-full h-full rounded-none p-0"
        ).style(
            "height:100vh;"
            "display:flex;"
            "flex-direction:column;"
        ):
            with ui.row().classes(
                "w-full items-center "
                "justify-between px-6 py-4"
            ).style(
                "background:#40101F;"
                "color:white;"
            ):
                with ui.column().classes(
                    "gap-0"
                ):
                    ui.label(
                        "REPLENISHMENT ACTION PLAN"
                    ).classes(
                        "text-[10px] font-bold "
                        "tracking-[0.18em] "
                        "text-amber-200"
                    )

                    ui.label(
                        "Network-wide Transfer + Purchase Order Planner"
                    ).classes(
                        "text-xl font-extrabold"
                    )

                ui.button(
                    icon="close",
                    on_click=plan_dialog.close,
                ).props(
                    "flat round"
                ).style(
                    "color:white;"
                )

            with ui.scroll_area().classes(
                "w-full flex-1"
            ):
                plan_workspace()

            with ui.row().classes(
                "w-full items-center "
                "justify-end gap-3 px-6 py-4"
            ).style(
                "border-top:1px solid #E7DED5;"
                "background:white;"
            ):
                ui.button(
                    "Close",
                    on_click=plan_dialog.close,
                ).props(
                    "flat no-caps"
                ).style(
                    "color:#651D32;"
                )

                ui.button(
                    "Save Draft",
                    icon="save",
                    on_click=lambda:
                    ui.notify(
                        "Draft saved in this MVP session.",
                        type="info",
                        position="top",
                    ),
                ).props(
                    "outline no-caps"
                ).style(
                    "color:#651D32;"
                )

                def _approve_plan() -> None:
                    if plan_state[
                        "plan"
                    ]:
                        plan_state[
                            "plan"
                        ][
                            "approved"
                        ] = True

                    ui.notify(
                        "Replenishment action plan approved.",
                        type="positive",
                        position="top",
                    )

                    plan_dialog.close()

                ui.button(
                    "Approve Plan",
                    icon="task_alt",
                    on_click=_approve_plan,
                ).props(
                    "unelevated no-caps"
                ).style(
                    "background:#651D32;"
                    "color:white;"
                )

    async def build_action_plan() -> None:
        stages = [
            (
                "Analyzing network demand",
                "Scanning all SKU × outlet positions",
            ),
            (
                "Calculating shortages",
                "Comparing forecast, stock and inbound units",
            ),
            (
                "Finding transferable inventory",
                "Protecting source-store forecast and safety buffer",
            ),
            (
                "Evaluating transfer routes",
                (
                    f"Applying the "
                    f"{plan_state['threshold_km']:.0f} km "
                    "distance threshold"
                ),
            ),
            (
                "Resolving Transfer vs PO",
                "Building the network-wide replenishment plan",
            ),
        ]

        progress_refs[
            "bar"
        ].value = 0

        progress_refs[
            "bar"
        ].update()

        generating_dialog.open()

        for step in range(10):
            stage_index = min(
                4,
                step // 2,
            )

            title, detail = stages[
                stage_index
            ]

            progress_refs[
                "stage"
            ].set_text(title)

            progress_refs[
                "detail"
            ].set_text(detail)

            progress_refs[
                "bar"
            ].value = (
                step + 1
            ) / 10

            progress_refs[
                "bar"
            ].update()

            await asyncio.sleep(
                0.5
            )

        plan = build_replenishment_plan(
            records,
            STORES,
            horizon=state["horizon"],
            transfer_threshold_km=plan_state[
                "threshold_km"
            ],
        )

        plan_state[
            "plan"
        ] = plan

        plan_state[
            "selected_action_id"
        ] = (
            plan["actions"][0][
                "action_id"
            ]
            if plan["actions"]
            else None
        )

        plan_state[
            "action_filter"
        ] = "ALL"

        plan_state[
            "destination_filter"
        ] = "ALL"

        plan_state[
            "category_filter"
        ] = "ALL"

        plan_state[
            "search"
        ] = ""

        plan_workspace.refresh()

        generating_dialog.close()
        plan_dialog.open()

    summary = network_summary(
        records,
        state["horizon"],
    )

    with app_shell(
        active_page="demand",
        title="Demand Exposure",
        subtitle=(
            "Granular demand visibility across 100 size-color SKUs "
            "and five stores, designed to expose where the next "
            "30 or 60 days create shortage or excess inventory risk."
        ),
    ):
        with ui.row().classes(
            "w-full items-end justify-between gap-4 mb-4 flex-wrap"
        ):
            with ui.row().classes(
                "items-end gap-4 flex-wrap"
            ):
                with ui.column().classes("gap-1"):
                    ui.label(
                        "FORECAST HORIZON"
                    ).classes(
                        "text-[9px] font-bold "
                        "tracking-wider muted"
                    )

                    ui.toggle(
                        {
                            30: "30 DAYS",
                            60: "60 DAYS",
                        },
                        value=30,
                        on_change=set_horizon,
                    ).props(
                        "no-caps unelevated"
                    ).style(
                        "color:var(--sw-burgundy);"
                    )

                with ui.column().classes("gap-1"):
                    ui.label(
                        "MATRIX VIEW"
                    ).classes(
                        "text-[9px] font-bold "
                        "tracking-wider muted"
                    )

                    ui.toggle(
                        [
                            "Forecast",
                            "Stock",
                            "Shortage",
                        ],
                        value="Forecast",
                        on_change=set_metric,
                    ).props(
                        "no-caps unelevated"
                    ).style(
                        "color:var(--sw-burgundy);"
                    )

                with ui.column().classes(
                    "gap-1"
                ):
                    ui.label(
                        "OUTLET"
                    ).classes(
                        "text-[9px] font-bold "
                        "tracking-wider muted"
                    )

                    ui.select(
                        options={
                            store["store_id"]:
                            f"{store['store_name']} · {store['city']}"
                            for store in STORES
                        },
                        value=state["store_id"],
                        on_change=set_store,
                    ).props(
                        "outlined dense options-dense"
                    ).classes(
                        "w-64"
                    )

                with ui.column().classes(
                    "gap-1"
                ):
                    ui.label(
                        "CATEGORY"
                    ).classes(
                        "text-[9px] font-bold "
                        "tracking-wider muted"
                    )

                    ui.select(
                        options={
                            product["category_id"]:
                            product["category_name"]
                            for product in PRODUCTS
                        },
                        value=state["category_id"],
                        on_change=set_category,
                    ).props(
                        "outlined dense options-dense"
                    ).classes(
                        "w-56"
                    )

                with ui.column().classes(
                    "gap-1"
                ):
                    ui.label(
                        "ACTION PLAN"
                    ).classes(
                        "text-[9px] font-bold "
                        "tracking-wider muted"
                    )

                    ui.button(
                        "Build Action Plan",
                        icon="auto_awesome",
                        on_click=build_action_plan,
                    ).props(
                        "unelevated no-caps"
                    ).style(
                        "background:#651D32;"
                        "color:white;"
                        "height:40px;"
                        "font-weight:700;"
                    )


        with ui.grid(columns=5).classes(
            "w-full gap-4 "
            "max-[1200px]:grid-cols-2 "
            "max-[700px]:grid-cols-1"
        ):
            _dashboard_metric_card(
                "FORECAST UNITS",
                f"{summary['forecast_units']:,}",
                "Network · next 30 days",
                "inventory",
            )

            _dashboard_metric_card(
                "FORECAST SALES",
                format_inr(
                    summary["forecast_sales"]
                ),
                "Projected retail demand value",
                "payments",
            )

            _dashboard_metric_card(
                "DEMAND UPLIFT",
                f"{summary['uplift_pct']:+.1f}%",
                "Versus comparable prior period",
                "trending_up",
            )

            _dashboard_metric_card(
                "AT-RISK POSITIONS",
                str(
                    summary[
                        "at_risk_positions"
                    ]
                ),
                "SKU × store shortages",
                "warning_amber",
            )

            _dashboard_metric_card(
                "EXCESS POSITIONS",
                str(
                    summary[
                        "excess_positions"
                    ]
                ),
                "SKU × store overstock",
                "inventory_2",
            )

        ui.element("div").style(
            "height:18px;"
        )

        dashboard()
