# MVP-SWMVR

A NiceGUI-based supply chain intelligence MVP built for **The Swayamvar**, focused on multi-outlet apparel retail.

The project adapts concepts from the Vesper Supply Chain Intelligence platform into a lightweight front-end demo for apparel operations. It currently contains two core modules:

- **Network Intelligence**
- **Demand Exposure**

The application runs on deterministic synthetic data and does not currently use a production database or external ERP/POS integration.

---

## Overview

MVP-SWMVR is designed to demonstrate how a multi-outlet apparel business can monitor network performance and forecast demand at a granular SKU level.

The current demo models:

- 5 retail outlets
- 5 apparel categories
- 5 colors per category
- 4 sizes per category
- 100 unique SKUs
- 500 outlet-SKU demand positions
- 30-day and 60-day forecast horizons

### Product Categories

- Modi Coat
- Jodhpuri
- Sherwani
- Dhoti Kurta Set
- Indo Jacket

### Sizes

- 38
- 40
- 42
- 44

### Colors

- Beige
- Black
- Maroon
- Navy
- Olive

---

# Modules

## 1. Network Intelligence

Provides a portfolio-level view of the store network.

### Network KPIs

- Net Sales
- Gross Margin
- Sell-through
- Inventory Value
- Inventory Turns
- Sales / Sq Ft

### Selected Store KPIs

- Net Sales
- 30-Day Forecast
- Sales Growth
- Gross Margin
- ASP
- Average Basket Value
- Units / Transaction
- Sales / Sq Ft
- Inventory Value
- Inventory Turns
- Sell-through
- Stock Cover
- Aged Inventory
- SKU Availability
- At-Risk SKUs
- Top Category

### Features

- Interactive store map
- Store status classification
- State and performance filters
- Store search
- Store performance table
- Selected-store intelligence observations
- Recommended management actions

---

## 2. Demand Exposure

Provides granular demand visibility across:

```text
Outlet
  ↓
Category
  ↓
Color
  ↓
Size
  ↓
SKU
```

### Controls

- Forecast Horizon
  - 30 Days
  - 60 Days

- Matrix View
  - Forecast
  - Stock
  - Shortage

- Outlet selector
- Category selector

### Size × Color Matrix

For the selected outlet and category, the application displays a 4 × 5 matrix:

```text
              COLOR
        Beige Black Maroon Navy Olive
Size 38
Size 40
Size 42
Size 44
```

Each cell represents one exact SKU.

Clicking a cell updates:

- Selected SKU
- Forecast
- Current Stock
- Inbound Stock
- Shortage
- Unit Retail Value
- Forecast Value
- Product Visual

---

# Demand Signals

Each outlet/category forecast includes **5 demand signals**.

The signals are designed so that:

- changing the **outlet** changes the signal mix significantly
- changing the **category** changes the signals more subtly

The current demo combines:

- 4 outlet-specific signals
- 1 category-specific signal

Examples include:

- wedding-season demand
- festive demand
- weekend retail traffic
- local catchment behavior
- category-specific occasion demand

These signals contribute to the deterministic forecast multiplier used by the MVP.

---

# Product Visuals

Product images are loaded dynamically based on:

```text
Category + Color
```

The image does not change based on size.

Images should be placed under:

```text
app/static/
```

Current expected folder structure:

```text
app/static/
├── Dhoti_Kurta_Set/
│   ├── Dhoti_Kurta_Set_Beige.jpeg
│   ├── Dhoti_Kurta_Set_Black.jpeg
│   ├── Dhoti_Kurta_Set_Maroon.jpeg
│   ├── Dhoti_Kurta_Set_Navy.jpeg
│   └── Dhoti_Kurta_Set_Olive.jpeg
│
├── Indo_Jacket/
│   ├── Indo_Jacket_Beige.jpeg
│   ├── Indo_Jacket_Black.jpeg
│   ├── Indo_Jacket_Maroon.jpeg
│   ├── Indo_Jacket_Navy.jpeg
│   └── Indo_Jacket_Olive.jpeg
│
├── Jodhpuri/
│   ├── Jodhpuri_Beige.jpeg
│   ├── Jodhpuri_Black.jpeg
│   ├── Jodhpuri_Maroon.jpeg
│   ├── Jodhpuri_Navy.jpeg
│   └── Jodhpuri_Olive.jpeg
│
├── Modi_Coat/
│   ├── Modi_Coat_Beige.jpeg
│   ├── Modi_Coat_Black.jpeg
│   ├── Modi_Coat_Maroon.jpeg
│   ├── Modi_Coat_Navy.jpeg
│   └── Modi_Coat_Olive.jpeg
│
└── Sherwani/
    ├── Sherwani_Beige.jpeg
    ├── Sherwani_Black.jpeg
    ├── Sherwani_Maroon.jpeg
    ├── Sherwani_Navy.jpeg
    └── Sherwani_Olive.jpeg
```

---

# Replenishment Action Plan

Demand Exposure also includes a network-wide replenishment planner.

Click:

```text
Build Action Plan
```

The system analyzes shortages across all outlets and SKUs, then determines whether shortages should be resolved using:

- **Inter-store transfer**
- **Purchase order**

### Transfer Logic

For each shortage:

1. Find the same SKU at other outlets.
2. Calculate protected transferable surplus.
3. Measure inter-store distance.
4. If surplus exists within the configured transfer-distance threshold:
   - recommend a transfer
5. If not:
   - create a purchase-order recommendation

The planner supports mixed actions.

Example:

```text
Shortage = 20 units

Nearby transferable stock = 8 units

Plan:
Transfer 8
PO 12
```

### Transfer Threshold

The operator can change the maximum allowed transfer distance.

Example:

```text
250 km
```

Changing the threshold and recalculating the plan can change Transfer vs PO decisions.

### Master Plan Features

- Network-wide action table
- Transfer / PO filters
- Destination filters
- Category filters
- SKU/store search
- 24 rows per page
- Selected action details
- Recommendation explanation
- Manual action override
- Manual quantity override
- Manual transfer-source override
- Save Draft
- Approve Plan

---

# Architecture

Current project structure:

```text
MVP-SWMVR/
│
├── main.py
├── requirements.txt
│
└── app/
    ├── __init__.py
    ├── shell.py
    ├── theme.py
    │
    ├── data/
    │   ├── __init__.py
    │   ├── store_catalog.py
    │   ├── product_catalog.py
    │   └── demand_signal_catalog.py
    │
    ├── services/
    │   ├── __init__.py
    │   ├── network_service.py
    │   ├── demand_service.py
    │   └── replenishment_service.py
    │
    ├── pages/
    │   ├── __init__.py
    │   ├── network_intelligence.py
    │   └── demand_exposure.py
    │
    └── static/
        ├── inventide-logo.png
        ├── swayamvar-logo.png
        └── product image folders...
```

The application follows a simple separation:

```text
Data
 ↓
Services
 ↓
NiceGUI Pages
```

This keeps the MVP easy to extend later with:

- PostgreSQL
- ERP/POS integration
- warehouse/DC data
- real forecasting models
- production replenishment workflows

---

# Technology Stack

- Python
- NiceGUI
- Leaflet
- HTML/CSS
- Deterministic synthetic data

---

# Setup

## 1. Clone the repository

```bash
git clone <repository-url>
cd MVP-SWMVR
```

## 2. Create a virtual environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Start the application

```bash
python main.py
```

The app will be available at:

```text
http://127.0.0.1:8080
```

or the port configured in `main.py`.

---

# Current MVP Limitations

This version is intended for interface and workflow validation.

It does **not** currently include:

- production database
- ERP integration
- Genesis integration
- real POS data
- warehouse/DC integration
- live vendor integration
- real purchase-order creation
- real transfer execution
- trained production forecasting model
- user authentication or roles
- persistent approved plans

All business data is currently generated for demo purposes.

---

# Future Direction

Potential production evolution:

```text
ERP / POS / Inventory Systems
          ↓
Canonical Data Layer
          ↓
Forecasting + Demand Signal Engine
          ↓
Network Intelligence
          ↓
Demand Exposure
          ↓
Transfer / Purchase Optimization
          ↓
Planner Review & Approval
          ↓
ERP / Procurement Execution
```

---

# Branding

The application is presented as:

**VESPER | SUPPLY CHAIN INTELLIGENCE**

Powered by **Inventide**

Client-specific interface:

**The Swayamvar — Intelligence Suite**

---

## Status

Current state: **Front-end MVP / synthetic-data prototype**
