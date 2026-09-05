from __future__ import annotations


SIZES = [38, 40, 42, 44]


# Five Swayamvar menswear categories used in the MVP.
# Each category uses five colors × four sizes = 20 SKUs.
PRODUCTS: list[dict] = [
    {
        "category_id": "modi_coat",
        "category_name": "Modi Coat",
        "style_code": "MDC",
        "colors": ["Beige", "Black", "Maroon", "Navy", "Olive"],
        "image_folder": "Modi_Coat",
        "image_prefix": "Modi_Coat",
        "avg_price": 6_990,
        "demand_factor": 1.05,
    },
    {
        "category_id": "jodhpuri",
        "category_name": "Jodhpuri",
        "style_code": "JDP",
        "colors": ["Beige", "Black", "Maroon", "Navy", "Olive"],
        "image_folder": "Jodhpuri",
        "image_prefix": "Jodhpuri",
        "avg_price": 10_990,
        "demand_factor": 0.92,
    },
    {
        "category_id": "sherwani",
        "category_name": "Sherwani",
        "style_code": "SHR",
        "colors": ["Beige", "Black", "Maroon", "Navy", "Olive"],
        "image_folder": "Sherwani",
        "image_prefix": "Sherwani",
        "avg_price": 14_990,
        "demand_factor": 0.78,
    },
    {
        "category_id": "dhoti_kurta_set",
        "category_name": "Dhoti Kurta Set",
        "style_code": "DKS",
        "colors": ["Beige", "Black", "Maroon", "Navy", "Olive"],
        "image_folder": "Dhoti_Kurta_Set",
        "image_prefix": "Dhoti_Kurta_Set",
        "avg_price": 7_990,
        "demand_factor": 1.18,
    },
    {
        "category_id": "indo_jacket",
        "category_name": "Indo Jacket",
        "style_code": "INJ",
        "colors": ["Beige", "Black", "Maroon", "Navy", "Olive"],
        "image_folder": "Indo_Jacket",
        "image_prefix": "Indo_Jacket",
        "avg_price": 8_990,
        "demand_factor": 1.08,
    },
]


PRODUCTS_BY_ID = {
    product["category_id"]: product
    for product in PRODUCTS
}
