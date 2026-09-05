from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Iterable

from app.data.demand_signal_catalog import demand_signal_lift_pct
from app.data.product_catalog import PRODUCTS, SIZES


SIZE_FACTORS = {
    38: 0.78,
    40: 1.08,
    42: 1.22,
    44: 0.92,
}


def _stable_ratio(key: str, low: float, high: float) -> float:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    bucket = int(digest[:10], 16) / int("f" * 10, 16)
    return low + (high - low) * bucket


def build_demand_records(
    stores: Iterable[dict],
    products: Iterable[dict] = PRODUCTS,
) -> list[dict]:
    stores = list(stores)
    products = list(products)

    max_store_sales = max(
        store["monthly_sales"]
        for store in stores
    )

    records: list[dict] = []

    for store in stores:
        store_factor = 0.78 + (
            store["monthly_sales"] / max_store_sales
        ) * 0.55

        for product in products:
            colors = product["colors"]

            for color_index, color in enumerate(colors):
                color_factor = 0.82 + (
                    (len(colors) - color_index) * 0.055
                )

                for size in SIZES:
                    key = (
                        f"{store['store_id']}|"
                        f"{product['category_id']}|"
                        f"{color}|{size}"
                    )

                    jitter = _stable_ratio(
                        key + "|forecast30",
                        0.84,
                        1.19,
                    )

                    signal_multiplier = 1 + (
                        demand_signal_lift_pct(
                            store["store_id"],
                            product["category_id"],
                        )
                        / 100
                    )

                    base_units = (
                        2.65
                        * store_factor
                        * product["demand_factor"]
                        * SIZE_FACTORS[size]
                        * color_factor
                        * jitter
                        * signal_multiplier
                    )

                    forecast_30 = max(
                        1,
                        round(base_units),
                    )

                    seasonal_60 = _stable_ratio(
                        key + "|forecast60",
                        1.78,
                        2.08,
                    )

                    forecast_60 = max(
                        forecast_30 + 1,
                        round(forecast_30 * seasonal_60),
                    )

                    prior_ratio = _stable_ratio(
                        key + "|prior",
                        0.83,
                        1.10,
                    )

                    prior_30 = max(
                        1,
                        round(forecast_30 * prior_ratio),
                    )

                    stock_ratio = _stable_ratio(
                        key + "|stock",
                        0.58,
                        1.48,
                    )

                    stock = max(
                        0,
                        round(forecast_30 * stock_ratio),
                    )

                    inbound_ratio = _stable_ratio(
                        key + "|inbound",
                        0.00,
                        0.52,
                    )

                    inbound = max(
                        0,
                        round(forecast_30 * inbound_ratio),
                    )

                    sku = (
                        f"{product['style_code']}-"
                        f"{color[:3].upper().replace(' ', '')}-"
                        f"{size}"
                    )

                    records.append(
                        {
                            "store_id": store["store_id"],
                            "store_name": store["store_name"],
                            "city": store["city"],
                            "category_id": product["category_id"],
                            "category_name": product["category_name"],
                            "style_code": product["style_code"],
                            "color": color,
                            "size": size,
                            "sku": sku,
                            "price": product["avg_price"],
                            "forecast_30": forecast_30,
                            "forecast_60": forecast_60,
                            "prior_30": prior_30,
                            "stock": stock,
                            "inbound": inbound,
                        }
                    )

    return records


def horizon_forecast(record: dict, horizon: int) -> int:
    return (
        record["forecast_30"]
        if horizon == 30
        else record["forecast_60"]
    )


def shortage_units(record: dict, horizon: int) -> int:
    """Positive = shortage, negative = surplus."""
    return (
        horizon_forecast(record, horizon)
        - record["stock"]
        - record["inbound"]
    )


def record_metric(
    record: dict,
    horizon: int,
    metric: str,
) -> int:
    if metric == "Stock":
        return record["stock"]

    if metric == "Shortage":
        return shortage_units(record, horizon)

    return horizon_forecast(record, horizon)


def filtered_records(
    records: Iterable[dict],
    *,
    store_id: str | None = None,
    category_id: str | None = None,
) -> list[dict]:
    return [
        record
        for record in records
        if (
            store_id is None
            or record["store_id"] == store_id
        )
        and (
            category_id is None
            or record["category_id"] == category_id
        )
    ]


def aggregate_metric(
    records: Iterable[dict],
    horizon: int,
    metric: str,
) -> int:
    return sum(
        record_metric(record, horizon, metric)
        for record in records
    )


def network_summary(
    records: Iterable[dict],
    horizon: int,
) -> dict:
    records = list(records)

    forecast_units = sum(
        horizon_forecast(record, horizon)
        for record in records
    )

    forecast_sales = sum(
        horizon_forecast(record, horizon)
        * record["price"]
        for record in records
    )

    at_risk_positions = sum(
        1
        for record in records
        if shortage_units(record, horizon) > 0
    )

    excess_positions = sum(
        1
        for record in records
        if shortage_units(record, horizon) <= -max(
            2,
            round(horizon_forecast(record, horizon) * 0.65),
        )
    )

    prior_units = sum(
        record["prior_30"]
        for record in records
    )

    if horizon == 60:
        prior_units *= 2

    uplift_pct = (
        ((forecast_units / prior_units) - 1) * 100
        if prior_units
        else 0.0
    )

    return {
        "forecast_units": forecast_units,
        "forecast_sales": forecast_sales,
        "at_risk_positions": at_risk_positions,
        "excess_positions": excess_positions,
        "uplift_pct": uplift_pct,
    }


def category_store_matrix(
    records: Iterable[dict],
    horizon: int,
    metric: str,
) -> dict[tuple[str, str], int]:
    grouped: defaultdict[tuple[str, str], list[dict]] = defaultdict(list)

    for record in records:
        grouped[
            (
                record["category_id"],
                record["store_id"],
            )
        ].append(record)

    return {
        key: aggregate_metric(
            group,
            horizon,
            metric,
        )
        for key, group in grouped.items()
    }


def variant_matrix(
    records: Iterable[dict],
    *,
    store_id: str,
    category_id: str,
    horizon: int,
    metric: str,
) -> dict[tuple[int, str], dict]:
    subset = filtered_records(
        records,
        store_id=store_id,
        category_id=category_id,
    )

    return {
        (
            record["size"],
            record["color"],
        ): {
            **record,
            "display_value": record_metric(
                record,
                horizon,
                metric,
            ),
            "shortage": shortage_units(
                record,
                horizon,
            ),
            "forecast": horizon_forecast(
                record,
                horizon,
            ),
        }
        for record in subset
    }


def pair_insight(
    records: Iterable[dict],
    *,
    store_id: str,
    category_id: str,
    horizon: int,
) -> dict:
    subset = filtered_records(
        records,
        store_id=store_id,
        category_id=category_id,
    )

    hottest = max(
        subset,
        key=lambda record: horizon_forecast(
            record,
            horizon,
        ),
    )

    tightest = min(
        subset,
        key=lambda record: shortage_units(
            record,
            horizon,
        ),
    )

    slowest = min(
        subset,
        key=lambda record: shortage_units(
            record,
            horizon,
        ),
    )

    return {
        "hottest": hottest,
        "tightest": tightest,
        "slowest": slowest,
    }


def find_record(
    records: Iterable[dict],
    *,
    store_id: str,
    category_id: str,
    color: str,
    size: int,
) -> dict:
    for record in records:
        if (
            record["store_id"] == store_id
            and record["category_id"] == category_id
            and record["color"] == color
            and record["size"] == size
        ):
            return record

    raise KeyError(
        f"No record for {store_id} / {category_id} / {color} / {size}"
    )
