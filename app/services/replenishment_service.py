from __future__ import annotations

import math
from collections import defaultdict
from typing import Iterable

from app.services.demand_service import (
    horizon_forecast,
    shortage_units,
)


DEFAULT_TRANSFER_THRESHOLD_KM = 250.0
SAFETY_BUFFER_PCT = 0.10
SAFETY_BUFFER_MIN_UNITS = 1


def haversine_km(
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


def safety_buffer_units(
    record: dict,
    horizon: int,
) -> int:
    forecast = horizon_forecast(
        record,
        horizon,
    )

    return max(
        SAFETY_BUFFER_MIN_UNITS,
        round(forecast * SAFETY_BUFFER_PCT),
    )


def transferable_units(
    record: dict,
    horizon: int,
) -> int:
    return max(
        0,
        record["stock"]
        + record["inbound"]
        - horizon_forecast(record, horizon)
        - safety_buffer_units(record, horizon),
    )


def _store_maps(
    stores: Iterable[dict],
) -> tuple[dict[str, dict], dict[str, dict]]:
    stores = list(stores)

    by_id = {
        store["store_id"]: store
        for store in stores
    }

    by_name = {
        store["store_name"]: store
        for store in stores
    }

    return by_id, by_name


def _distance_between_stores(
    source_store: dict,
    destination_store: dict,
) -> float:
    return haversine_km(
        source_store["lat"],
        source_store["lon"],
        destination_store["lat"],
        destination_store["lon"],
    )


def build_replenishment_plan(
    records: Iterable[dict],
    stores: Iterable[dict],
    *,
    horizon: int,
    transfer_threshold_km: float = DEFAULT_TRANSFER_THRESHOLD_KM,
) -> dict:
    records = list(records)
    stores = list(stores)

    stores_by_id, _ = _store_maps(stores)

    record_by_position = {
        (
            record["store_id"],
            record["sku"],
        ): record
        for record in records
    }

    donor_capacity = {
        key: transferable_units(
            record,
            horizon,
        )
        for key, record in record_by_position.items()
    }

    shortages = [
        record
        for record in records
        if shortage_units(
            record,
            horizon,
        ) > 0
    ]

    # Deterministic prioritization:
    # largest shortage first, then destination, then SKU.
    shortages.sort(
        key=lambda record: (
            -shortage_units(
                record,
                horizon,
            ),
            record["store_name"],
            record["sku"],
        )
    )

    actions: list[dict] = []
    action_counter = 1

    for destination_record in shortages:
        destination_id = destination_record[
            "store_id"
        ]

        destination_store = stores_by_id[
            destination_id
        ]

        original_shortage = shortage_units(
            destination_record,
            horizon,
        )

        remaining = original_shortage

        donor_candidates: list[dict] = []

        for source_record in records:
            if (
                source_record["sku"]
                != destination_record["sku"]
            ):
                continue

            if (
                source_record["store_id"]
                == destination_id
            ):
                continue

            capacity_key = (
                source_record["store_id"],
                source_record["sku"],
            )

            available = donor_capacity.get(
                capacity_key,
                0,
            )

            if available <= 0:
                continue

            source_store = stores_by_id[
                source_record["store_id"]
            ]

            distance_km = _distance_between_stores(
                source_store,
                destination_store,
            )

            donor_candidates.append(
                {
                    "record": source_record,
                    "store": source_store,
                    "distance_km": distance_km,
                    "available": available,
                }
            )

        donor_candidates.sort(
            key=lambda candidate: (
                candidate["distance_km"],
                -candidate["available"],
            )
        )

        for donor in donor_candidates:
            if remaining <= 0:
                break

            if (
                donor["distance_km"]
                > transfer_threshold_km
            ):
                continue

            source_record = donor[
                "record"
            ]

            capacity_key = (
                source_record["store_id"],
                source_record["sku"],
            )

            available = donor_capacity[
                capacity_key
            ]

            if available <= 0:
                continue

            quantity = min(
                remaining,
                available,
            )

            donor_capacity[
                capacity_key
            ] -= quantity

            remaining -= quantity

            actions.append(
                {
                    "action_id": (
                        f"ACT-{action_counter:04d}"
                    ),
                    "action_type": "TRANSFER",
                    "destination_id": destination_id,
                    "destination_name": destination_record[
                        "store_name"
                    ],
                    "destination_city": destination_record[
                        "city"
                    ],
                    "source_id": source_record[
                        "store_id"
                    ],
                    "source_name": source_record[
                        "store_name"
                    ],
                    "source_city": source_record[
                        "city"
                    ],
                    "category_id": destination_record[
                        "category_id"
                    ],
                    "category_name": destination_record[
                        "category_name"
                    ],
                    "sku": destination_record[
                        "sku"
                    ],
                    "color": destination_record[
                        "color"
                    ],
                    "size": destination_record[
                        "size"
                    ],
                    "shortage_units": (
                        original_shortage
                    ),
                    "qty": quantity,
                    "distance_km": round(
                        donor["distance_km"],
                        1,
                    ),
                    "reason": (
                        "Exact SKU has protected surplus at "
                        f"{source_record['store_name']} and the "
                        f"{donor['distance_km']:.0f} km route is "
                        f"within the {transfer_threshold_km:.0f} km "
                        "transfer threshold."
                    ),
                    "overridden": False,
                }
            )

            action_counter += 1

        if remaining > 0:
            nearest_surplus_distance = None
            nearest_surplus_name = None

            for donor in donor_candidates:
                if (
                    nearest_surplus_distance
                    is None
                    or donor["distance_km"]
                    < nearest_surplus_distance
                ):
                    nearest_surplus_distance = donor[
                        "distance_km"
                    ]
                    nearest_surplus_name = donor[
                        "record"
                    ]["store_name"]

            if nearest_surplus_distance is None:
                reason = (
                    "No protected surplus for this exact SKU "
                    "is available at another outlet. Remaining "
                    "shortage is routed to purchase order."
                )
            elif (
                nearest_surplus_distance
                > transfer_threshold_km
            ):
                reason = (
                    "Nearest remaining protected surplus is at "
                    f"{nearest_surplus_name}, approximately "
                    f"{nearest_surplus_distance:.0f} km away, "
                    f"which exceeds the {transfer_threshold_km:.0f} km "
                    "transfer threshold."
                )
            else:
                reason = (
                    "Nearby transferable inventory is insufficient "
                    "to cover the full shortage. The uncovered "
                    "quantity is routed to purchase order."
                )

            actions.append(
                {
                    "action_id": (
                        f"ACT-{action_counter:04d}"
                    ),
                    "action_type": "PO",
                    "destination_id": destination_id,
                    "destination_name": destination_record[
                        "store_name"
                    ],
                    "destination_city": destination_record[
                        "city"
                    ],
                    "source_id": None,
                    "source_name": (
                        "Central Procurement"
                    ),
                    "source_city": "",
                    "category_id": destination_record[
                        "category_id"
                    ],
                    "category_name": destination_record[
                        "category_name"
                    ],
                    "sku": destination_record[
                        "sku"
                    ],
                    "color": destination_record[
                        "color"
                    ],
                    "size": destination_record[
                        "size"
                    ],
                    "shortage_units": (
                        original_shortage
                    ),
                    "qty": remaining,
                    "distance_km": None,
                    "reason": reason,
                    "overridden": False,
                }
            )

            action_counter += 1

    plan = {
        "horizon": horizon,
        "transfer_threshold_km": float(
            transfer_threshold_km
        ),
        "actions": actions,
        "approved": False,
    }

    summarize_plan(plan)

    return plan


def summarize_plan(
    plan: dict,
) -> dict:
    actions = plan.get(
        "actions",
        [],
    )

    transfer_actions = [
        action
        for action in actions
        if action["action_type"]
        == "TRANSFER"
    ]

    po_actions = [
        action
        for action in actions
        if action["action_type"]
        == "PO"
    ]

    # Shortage is counted once per destination-SKU,
    # even when the solution is split across transfer + PO.
    shortage_by_position: dict[
        tuple[str, str],
        int,
    ] = {}

    for action in actions:
        key = (
            action["destination_id"],
            action["sku"],
        )

        shortage_by_position[
            key
        ] = action["shortage_units"]

    total_shortage_units = sum(
        shortage_by_position.values()
    )

    transfer_units = sum(
        action["qty"]
        for action in transfer_actions
    )

    po_units = sum(
        action["qty"]
        for action in po_actions
    )

    total_planned_units = (
        transfer_units
        + po_units
    )

    coverage_pct = (
        min(
            100.0,
            (
                total_planned_units
                / total_shortage_units
                * 100
            ),
        )
        if total_shortage_units
        else 100.0
    )

    summary = {
        "shortage_units": (
            total_shortage_units
        ),
        "transfer_units": transfer_units,
        "po_units": po_units,
        "transfer_actions": len(
            transfer_actions
        ),
        "po_actions": len(
            po_actions
        ),
        "coverage_pct": coverage_pct,
        "overridden_actions": sum(
            1
            for action in actions
            if action.get(
                "overridden",
                False,
            )
        ),
    }

    plan["summary"] = summary

    return summary


def get_action(
    plan: dict,
    action_id: str,
) -> dict | None:
    return next(
        (
            action
            for action in plan.get(
                "actions",
                [],
            )
            if action["action_id"]
            == action_id
        ),
        None,
    )


def transfer_source_candidates(
    *,
    action: dict,
    records: Iterable[dict],
    stores: Iterable[dict],
    horizon: int,
) -> list[dict]:
    records = list(records)
    stores = list(stores)

    stores_by_id, _ = _store_maps(stores)

    destination_store = stores_by_id[
        action["destination_id"]
    ]

    candidates: list[dict] = []

    for record in records:
        if record["sku"] != action["sku"]:
            continue

        if (
            record["store_id"]
            == action["destination_id"]
        ):
            continue

        available = transferable_units(
            record,
            horizon,
        )

        if available <= 0:
            continue

        source_store = stores_by_id[
            record["store_id"]
        ]

        distance_km = _distance_between_stores(
            source_store,
            destination_store,
        )

        candidates.append(
            {
                "store_id": record[
                    "store_id"
                ],
                "store_name": record[
                    "store_name"
                ],
                "city": record["city"],
                "available": available,
                "distance_km": round(
                    distance_km,
                    1,
                ),
            }
        )

    candidates.sort(
        key=lambda candidate: (
            candidate["distance_km"],
            -candidate["available"],
        )
    )

    return candidates


def apply_manual_override(
    *,
    plan: dict,
    action_id: str,
    action_type: str,
    quantity: int,
    source_id: str | None,
    records: Iterable[dict],
    stores: Iterable[dict],
) -> dict:
    action = get_action(
        plan,
        action_id,
    )

    if action is None:
        raise KeyError(
            f"Unknown action: {action_id}"
        )

    quantity = max(
        1,
        int(quantity),
    )

    action["qty"] = quantity
    action["action_type"] = (
        action_type
    )
    action["overridden"] = True

    if action_type == "PO":
        action["source_id"] = None
        action["source_name"] = (
            "Central Procurement"
        )
        action["source_city"] = ""
        action["distance_km"] = None
        action["reason"] = (
            "Operator override: quantity is "
            "routed to purchase order."
        )

    else:
        stores_by_id, _ = _store_maps(
            stores
        )

        if source_id is None:
            raise ValueError(
                "A source outlet is required "
                "for a transfer override."
            )

        source_store = stores_by_id[
            source_id
        ]

        destination_store = stores_by_id[
            action["destination_id"]
        ]

        distance_km = _distance_between_stores(
            source_store,
            destination_store,
        )

        action["source_id"] = source_id
        action["source_name"] = (
            source_store["store_name"]
        )
        action["source_city"] = (
            source_store["city"]
        )
        action["distance_km"] = round(
            distance_km,
            1,
        )

        threshold = plan[
            "transfer_threshold_km"
        ]

        threshold_note = (
            "within"
            if distance_km <= threshold
            else "outside"
        )

        action["reason"] = (
            "Operator override: transfer from "
            f"{source_store['store_name']} "
            f"({distance_km:.0f} km), "
            f"{threshold_note} the current "
            f"{threshold:.0f} km threshold."
        )

    summarize_plan(plan)

    return action
