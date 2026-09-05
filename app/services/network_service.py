from __future__ import annotations

from typing import Iterable


def format_inr(value: float | int, compact: bool = True) -> str:
    value = float(value)

    if not compact:
        return f"₹{value:,.0f}"

    if abs(value) >= 10_000_000:
        return f"₹{value / 10_000_000:.2f} Cr"

    if abs(value) >= 100_000:
        return f"₹{value / 100_000:.1f} L"

    if abs(value) >= 1_000:
        return f"₹{value / 1_000:.1f} K"

    return f"₹{value:,.0f}"


def enrich_store_metrics(store: dict) -> dict:
    monthly_sales = float(store["monthly_sales"])
    units_sold = max(1, int(store["units_sold"]))
    transactions = max(1, int(store["transactions"]))
    floor_sq_ft = max(1, int(store["floor_sq_ft"]))
    stock_cover_weeks = max(0.1, float(store["stock_cover_weeks"]))

    return {
        **store,
        "asp": monthly_sales / units_sold,
        "average_basket_value": monthly_sales / transactions,
        "units_per_transaction": units_sold / transactions,
        "sales_per_sq_ft": monthly_sales / floor_sq_ft,
        "inventory_turns": 52.0 / stock_cover_weeks,
    }


def build_network_kpis(stores: Iterable[dict]) -> dict:
    stores = [
        enrich_store_metrics(store)
        for store in stores
    ]

    if not stores:
        return {
            "net_sales": 0.0,
            "gross_margin_pct": 0.0,
            "sell_through_pct": 0.0,
            "inventory_value": 0.0,
            "inventory_turns": 0.0,
            "sales_per_sq_ft": 0.0,
        }

    net_sales = sum(
        store["monthly_sales"]
        for store in stores
    )

    inventory_value = sum(
        store["inventory_value"]
        for store in stores
    )

    total_floor_sq_ft = sum(
        store["floor_sq_ft"]
        for store in stores
    )

    weighted_margin = (
        sum(
            store["monthly_sales"]
            * store["gross_margin_pct"]
            for store in stores
        )
        / net_sales
        if net_sales
        else 0.0
    )

    weighted_sell_through = (
        sum(
            store["inventory_value"]
            * store["sell_through_pct"]
            for store in stores
        )
        / inventory_value
        if inventory_value
        else 0.0
    )

    weighted_inventory_turns = (
        sum(
            store["inventory_value"]
            * store["inventory_turns"]
            for store in stores
        )
        / inventory_value
        if inventory_value
        else 0.0
    )

    network_sales_per_sq_ft = (
        net_sales / total_floor_sq_ft
        if total_floor_sq_ft
        else 0.0
    )

    return {
        "net_sales": net_sales,
        "gross_margin_pct": weighted_margin,
        "sell_through_pct": weighted_sell_through,
        "inventory_value": inventory_value,
        "inventory_turns": weighted_inventory_turns,
        "sales_per_sq_ft": network_sales_per_sq_ft,
    }


def build_table_rows(stores: Iterable[dict]) -> list[dict]:
    rows = []

    for raw_store in stores:
        store = enrich_store_metrics(raw_store)

        rows.append(
            {
                **store,
                "sales_display": format_inr(store["monthly_sales"]),
                "growth_display": f"{store['sales_growth_pct']:+.1f}%",
                "margin_display": f"{store['gross_margin_pct']:.1f}%",
                "sell_through_display": f"{store['sell_through_pct']:.1f}%",
                "availability_display": f"{store['sku_availability_pct']:.1f}%",
                "inventory_display": format_inr(store["inventory_value"]),
                "asp_display": format_inr(store["asp"]),
                "basket_display": format_inr(store["average_basket_value"]),
                "upt_display": f"{store['units_per_transaction']:.2f}",
                "sales_sqft_display": format_inr(store["sales_per_sq_ft"]),
                "turns_display": f"{store['inventory_turns']:.1f}x",
            }
        )

    return rows


def build_store_observation(store: dict) -> tuple[str, str]:
    if store["status"] == "At risk":
        observation = (
            f"{store['store_name']} has the network's highest inventory pressure: "
            f"{store['stock_cover_weeks']:.1f} weeks of cover, "
            f"{store['aged_inventory_pct']:.1f}% aged inventory and "
            f"{store['sales_growth_pct']:+.1f}% sales growth. "
            f"{store['at_risk_skus']} SKUs need attention."
        )
        action = (
            "Reduce replenishment on slow variants, identify transferable stock, "
            "and protect availability only for the fastest-moving size-color combinations."
        )
        return observation, action

    if store["status"] == "Watch":
        observation = (
            f"{store['store_name']} is stable but carrying "
            f"{store['stock_cover_weeks']:.1f} weeks of stock. "
            f"Sell-through is {store['sell_through_pct']:.1f}% while "
            f"{store['aged_inventory_pct']:.1f}% of inventory is ageing."
        )
        action = (
            "Review size and color mix before the next allocation cycle and "
            "move slow variants toward stores with stronger demand."
        )
        return observation, action

    observation = (
        f"{store['store_name']} is performing strongly with "
        f"{store['sell_through_pct']:.1f}% sell-through, "
        f"{store['sku_availability_pct']:.1f}% SKU availability and "
        f"{store['sales_growth_pct']:+.1f}% sales growth."
    )
    action = (
        f"Protect availability in {store['top_category']} and prioritize replenishment "
        "for high-velocity size-color variants before adding depth to slower SKUs."
    )
    return observation, action


TABLE_COLUMNS = [
    {
        "name": "store_name",
        "label": "Store",
        "field": "store_name",
        "align": "left",
        "sortable": True,
    },
    {
        "name": "city",
        "label": "City",
        "field": "city",
        "align": "left",
        "sortable": True,
    },
    {
        "name": "sales_display",
        "label": "Net Sales",
        "field": "sales_display",
        "align": "right",
    },
    {
        "name": "growth_display",
        "label": "Growth",
        "field": "growth_display",
        "align": "right",
    },
    {
        "name": "margin_display",
        "label": "Gross Margin",
        "field": "margin_display",
        "align": "right",
    },
    {
        "name": "sell_through_display",
        "label": "Sell-through",
        "field": "sell_through_display",
        "align": "right",
    },
    {
        "name": "availability_display",
        "label": "SKU Availability",
        "field": "availability_display",
        "align": "right",
    },
    {
        "name": "inventory_display",
        "label": "Inventory",
        "field": "inventory_display",
        "align": "right",
    },
    {
        "name": "status",
        "label": "Status",
        "field": "status",
        "align": "left",
        "sortable": True,
    },
]
