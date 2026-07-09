"""
Configuration and distribution parameters for the data generator.
All distribution params are tunable here without touching generation logic.
"""

from datetime import date
from pydantic import BaseModel, field_validator, model_validator


# ---------------------------------------------------------------------------
# Distribution parameters
# ---------------------------------------------------------------------------

DISTRIBUTIONS = {
    # How many addresses per customer
    "addresses_per_customer": {
        "dist": "negative_binomial",
        "n": 2,
        "p": 0.6,
        "min": 1,
        "max": 5,
    },
    # How many devices per customer
    "devices_per_customer": {
        "dist": "negative_binomial",
        "n": 1,
        "p": 0.6,
        "min": 1,
        "max": 4,
    },
    # How many sessions per customer
    "sessions_per_customer": {
        "dist": "lognormal",
        "mean": 2.5,
        "sigma": 1.0,
        "min": 1,
        "max": 200,
    },
    # How many orders per customer (80/20 skew)
    "orders_per_customer": {
        "dist": "negative_binomial",
        "n": 1,
        "p": 0.25,
        "min": 0,
        "max": 50,
    },
    # How many lines per order
    "lines_per_order": {
        "dist": "zipf",
        "a": 2.0,
        "min": 1,
        "max": 20,
    },
    # How many impressions per session
    "impressions_per_session": {
        "dist": "zipf",
        "a": 1.5,
        "min": 0,
        "max": 50,
    },
    # Click-through rate (per impression)
    "ctr": {
        "dist": "beta",
        "a": 1.5,
        "b": 50.0,  # ~3% mean CTR
    },
    # Conversion rate (per click)
    "cvr": {
        "dist": "beta",
        "a": 1.5,
        "b": 13.0,  # ~10% mean CVR
    },
    # Return rate (per order)
    "return_rate": {
        "dist": "beta",
        "a": 1.0,
        "b": 9.0,  # ~10% mean return rate
    },
    # Lines per return
    "lines_per_return": {
        "dist": "zipf",
        "a": 2.5,
        "min": 1,
        "max": 5,
    },
}

# ---------------------------------------------------------------------------
# Fixed catalog sizes (not driven by --customers)
# ---------------------------------------------------------------------------

CATALOG = {
    "num_warehouses": 5,
    "num_categories": 50,
    "num_products": 500,
    "num_variants": 1500,  # ~3 variants per product
    "num_advertisers": 10,
    "num_campaigns": 50,  # ~5 per advertiser
    "num_ad_groups": 150,  # ~3 per campaign
    "num_creatives": 600,  # ~4 per ad_group
    "num_keywords": 500,
    "keywords_per_group": 5,  # for ad_group_keyword junction
}

# ---------------------------------------------------------------------------
# Time deltas for causal ordering
# ---------------------------------------------------------------------------

CAUSAL_DELTAS = {
    # How many days after customer.created_at a status change occurs
    "customer_status_change_min_d": 7,
    "customer_status_change_max_d": 180,
    # Payment happens this many seconds after order placed
    "payment_delay_min_s": 30,
    "payment_delay_max_s": 600,
    # Payment status change happens this many minutes after payment created
    "payment_status_change_min_m": 1,
    "payment_status_change_max_m": 60,
    # Order status change happens this many hours after order placed
    "order_status_change_min_h": 1,
    "order_status_change_max_h": 72,
    # Shipment goes out this many hours after order
    "shipment_delay_min_h": 4,
    "shipment_delay_max_h": 72,
    # Shipment status change happens this many hours after shipment created
    "shipment_status_change_min_h": 1,
    "shipment_status_change_max_h": 48,
    # Delivery happens this many days after shipment
    "delivery_delay_min_d": 2,
    "delivery_delay_max_d": 7,
    # Return requested this many days after delivery
    "return_delay_min_d": 1,
    "return_delay_max_d": 30,
    # Return resolution happens this many days after requested
    "return_resolution_min_d": 1,
    "return_resolution_max_d": 14,
    # Ad click happens this many seconds after impression
    "click_delay_min_s": 1,
    "click_delay_max_s": 30,
    # Conversion happens this many minutes after click
    "conversion_delay_min_m": 1,
    "conversion_delay_max_m": 120,
    # Session duration in minutes
    "session_duration_min_m": 1,
    "session_duration_max_m": 60,
}

# ---------------------------------------------------------------------------
# Status weights
# ---------------------------------------------------------------------------

# Customer status: 80% active, 15% inactive, 5% suspended
CUSTOMER_STATUSES = ["active"] * 80 + ["inactive"] * 15 + ["suspended"] * 5

# Order lifecycle (no cancelled): pending is initial state
ORDER_STATUSES = ["pending", "confirmed", "shipped", "delivered"]

# Payment lifecycle: pending is initial state
PAYMENT_STATUSES = ["pending", "captured", "failed", "refunded"]

# Shipment lifecycle: processing is initial state
SHIPMENT_STATUSES = ["processing", "shipped", "in_transit", "delivered", "returned"]

# ---------------------------------------------------------------------------
# Pydantic config model
# ---------------------------------------------------------------------------


class ScaleConfig(BaseModel):
    customers: int
    start: date
    end: date
    output: str
    seed: int = 42
    batch_size: int = 1000

    @field_validator("customers")
    @classmethod
    def customers_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("--customers must be at least 1")
        return v

    @field_validator("batch_size")
    @classmethod
    def batch_size_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("--batch-size must be at least 1")
        return v

    @model_validator(mode="after")
    def start_before_end(self) -> "ScaleConfig":
        if self.start >= self.end:
            raise ValueError("--start must be before --end")
        return self

