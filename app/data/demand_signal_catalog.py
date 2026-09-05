from __future__ import annotations


OUTLET_SIGNAL_PROFILES: dict[str, list[dict]] = {
    "SW-HYD-BAN": [
        {
            "name": "Premium conversion momentum",
            "description": (
                "Higher-value occasion shoppers in the Banjara Hills catchment "
                "support conversion into premium menswear categories."
            ),
            "impact_pct": 2.5,
            "confidence": "Medium",
        },
        {
            "name": "Premium wedding catchment",
            "description": (
                "Higher concentration of occasion-wear shopping around the "
                "Banjara Hills catchment supports premium ethnic demand."
            ),
            "impact_pct": 8.0,
            "confidence": "High",
        },
        {
            "name": "Weekend high-street traffic",
            "description": (
                "Weekend shopping intensity is modeled above weekday baseline "
                "for this location."
            ),
            "impact_pct": 5.0,
            "confidence": "Medium",
        },
        {
            "name": "Local festive shopping",
            "description": (
                "Current planning window includes a synthetic festive uplift "
                "for Hyderabad occasion wear."
            ),
            "impact_pct": 4.0,
            "confidence": "Medium",
        },
    ],
    "SW-HYD-HIM": [
        {
            "name": "Central-city accessibility",
            "description": (
                "Strong access from surrounding residential catchments supports "
                "steady occasion-wear shopping through the planning window."
            ),
            "impact_pct": 2.0,
            "confidence": "Medium",
        },
        {
            "name": "Family occasion shopping",
            "description": (
                "Himayatnagar is modeled with strong family-led wedding and "
                "festive shopping behavior."
            ),
            "impact_pct": 7.0,
            "confidence": "High",
        },
        {
            "name": "Weekend footfall uplift",
            "description": (
                "Weekend store traffic is modeled above the normal weekday run rate."
            ),
            "impact_pct": 4.0,
            "confidence": "Medium",
        },
        {
            "name": "Urban repeat-customer demand",
            "description": (
                "Synthetic repeat-shopping behavior adds modest support to "
                "core occasion categories."
            ),
            "impact_pct": 3.0,
            "confidence": "Medium",
        },
    ],
    "SW-WGL-HNK": [
        {
            "name": "Surrounding-district demand",
            "description": (
                "The Hanamkonda store draws modeled occasion-wear demand from "
                "nearby districts in addition to the immediate urban catchment."
            ),
            "impact_pct": 3.0,
            "confidence": "Medium",
        },
        {
            "name": "Regional wedding season",
            "description": (
                "The Warangal catchment is modeled with elevated wedding-season "
                "shopping during the selected horizon."
            ),
            "impact_pct": 8.0,
            "confidence": "High",
        },
        {
            "name": "Destination shopping weekends",
            "description": (
                "Weekend demand includes synthetic inflow from surrounding towns."
            ),
            "impact_pct": 4.0,
            "confidence": "Medium",
        },
        {
            "name": "Festive sensitivity",
            "description": (
                "The outlet is modeled as more responsive to festive demand "
                "than to ordinary weekday traffic."
            ),
            "impact_pct": 4.0,
            "confidence": "Medium",
        },
    ],
    "SW-VJA-MGR": [
        {
            "name": "Regional family-shopping demand",
            "description": (
                "Family-led occasion shopping from the wider Vijayawada catchment "
                "adds support to the store's core menswear demand."
            ),
            "impact_pct": 2.5,
            "confidence": "Medium",
        },
        {
            "name": "Wedding and festival shopping",
            "description": (
                "MG Road is modeled with a strong occasion-wear uplift in the "
                "current planning window."
            ),
            "impact_pct": 8.0,
            "confidence": "High",
        },
        {
            "name": "MG Road weekend traffic",
            "description": (
                "Weekend retail traffic contributes a synthetic uplift versus "
                "the base demand curve."
            ),
            "impact_pct": 5.0,
            "confidence": "Medium",
        },
        {
            "name": "Regional event demand",
            "description": (
                "Local event activity contributes a smaller secondary demand signal."
            ),
            "impact_pct": 3.0,
            "confidence": "Medium",
        },
    ],
    "SW-VSK-DWK": [
        {
            "name": "Celebration-weekend activity",
            "description": (
                "Weekend celebration and event shopping provides an additional "
                "modest demand lift for the Dwaraka Nagar outlet."
            ),
            "impact_pct": 2.0,
            "confidence": "Medium",
        },
        {
            "name": "Coastal wedding demand",
            "description": (
                "The Visakhapatnam catchment retains occasion-wear demand, "
                "but at a softer level than the strongest stores."
            ),
            "impact_pct": 5.0,
            "confidence": "Medium",
        },
        {
            "name": "Weekend high-street traffic",
            "description": (
                "Weekend traffic provides a modest synthetic uplift to store demand."
            ),
            "impact_pct": 3.0,
            "confidence": "Medium",
        },
        {
            "name": "Soft weekday momentum",
            "description": (
                "Recent synthetic weekday momentum is modeled below network average."
            ),
            "impact_pct": -3.0,
            "confidence": "Medium",
        },
    ],
}


CATEGORY_SIGNAL_PROFILES: dict[str, dict] = {
    "modi_coat": {
        "name": "Festive Modi Coat demand",
        "description": (
            "Modi Coat demand receives a broad uplift from festive, family and "
            "smart occasion-wear shopping."
        ),
        "impact_pct": 4.0,
        "confidence": "High",
        "affinity": 0.98,
    },
    "jodhpuri": {
        "name": "Formal wedding Jodhpuri demand",
        "description": (
            "Jodhpuri demand is supported by formal wedding, reception and "
            "celebration occasions."
        ),
        "impact_pct": 5.0,
        "confidence": "High",
        "affinity": 1.03,
    },
    "sherwani": {
        "name": "Ceremony-wear demand",
        "description": (
            "Sherwani demand receives the strongest category-specific lift "
            "from wedding ceremony requirements."
        ),
        "impact_pct": 7.0,
        "confidence": "High",
        "affinity": 1.10,
    },
    "dhoti_kurta_set": {
        "name": "Traditional ceremony demand",
        "description": (
            "Dhoti Kurta Set demand receives additional support from traditional "
            "ceremonies, festive occasions and family events."
        ),
        "impact_pct": 5.0,
        "confidence": "High",
        "affinity": 1.06,
    },
    "indo_jacket": {
        "name": "Contemporary occasion layering",
        "description": (
            "Indo Jacket demand is supported by sangeet, reception and modern "
            "festive styling occasions."
        ),
        "impact_pct": 4.0,
        "confidence": "Medium",
        "affinity": 1.01,
    },
}


def get_demand_signals(
    store_id: str,
    category_id: str,
) -> list[dict]:
    category_profile = CATEGORY_SIGNAL_PROFILES[category_id]
    affinity = category_profile["affinity"]

    signals: list[dict] = []

    for signal in OUTLET_SIGNAL_PROFILES[store_id]:
        signals.append(
            {
                **signal,
                "type": "Outlet signal",
                "impact_pct": round(
                    signal["impact_pct"] * affinity,
                    1,
                ),
            }
        )

    signals.append(
        {
            "name": category_profile["name"],
            "description": category_profile["description"],
            "impact_pct": category_profile["impact_pct"],
            "confidence": category_profile["confidence"],
            "type": "Category signal",
        }
    )

    return signals


def demand_signal_lift_pct(
    store_id: str,
    category_id: str,
) -> float:
    return sum(
        signal["impact_pct"]
        for signal in get_demand_signals(
            store_id,
            category_id,
        )
    )
