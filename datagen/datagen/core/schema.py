"""
Schema definitions — single source of truth for:
  - Python dataclasses (used by core generator)
  - DDL SQL strings (used by PostgresSink to create tables)
  - CSV headers (used by FilesystemSink)

Tables are defined in FK-safe creation order.
"""

from dataclasses import dataclass, fields
from typing import Any

# ---------------------------------------------------------------------------
# Dataclasses — one per table
# ---------------------------------------------------------------------------

# ── User & Identity ─────────────────────────────────────────────────────────


@dataclass
class Customer:
    customer_id: str
    email: str
    full_name: str
    phone: str
    status: str
    created_at: str
    updated_at: str


@dataclass
class CustomerAddress:
    address_id: str
    customer_id: str
    line1: str
    city: str
    state: str
    country: str
    is_default: bool
    created_at: str
    updated_at: str


@dataclass
class Device:
    device_id: str
    customer_id: str
    type: str
    os: str
    user_agent: str
    created_at: str
    updated_at: str


@dataclass
class Session:
    session_id: str
    customer_id: str
    device_id: str
    channel: str
    started_at: str
    ended_at: str
    created_at: str
    updated_at: str


# ── Core E-Commerce ──────────────────────────────────────────────────────────


@dataclass
class ProductCategory:
    category_id: str
    parent_id: str | None
    name: str
    slug: str
    depth: int
    created_at: str
    updated_at: str


@dataclass
class Product:
    product_id: str
    category_id: str
    name: str
    description: str
    brand: str
    base_price: float
    status: str
    created_at: str
    updated_at: str


@dataclass
class ProductVariant:
    variant_id: str
    product_id: str
    sku: str
    size: str
    color: str
    price_override: float | None
    weight_kg: float
    is_active: bool
    created_at: str
    updated_at: str


@dataclass
class ProductAttribute:
    attribute_id: str
    variant_id: str
    attr_key: str
    attr_value: str
    display_order: int
    created_at: str
    updated_at: str


@dataclass
class Warehouse:
    warehouse_id: str
    name: str
    country: str
    city: str
    is_active: bool
    timezone: str
    created_at: str
    updated_at: str


@dataclass
class Inventory:
    inventory_id: str
    variant_id: str
    warehouse_id: str
    qty_on_hand: int
    qty_reserved: int
    created_at: str
    updated_at: str


@dataclass
class Order:
    order_id: str
    customer_id: str
    shipping_addr_id: str
    billing_addr_id: str
    status: str
    total_amount: float
    placed_at: str
    created_at: str
    updated_at: str


@dataclass
class OrderLine:
    order_line_id: str
    order_id: str
    variant_id: str
    quantity: int
    unit_price: float
    discount_amt: float
    line_total: float
    created_at: str
    updated_at: str


@dataclass
class Payment:
    payment_id: str
    order_id: str
    method: str
    amount: float
    status: str
    provider_ref: str
    paid_at: str
    created_at: str
    updated_at: str


@dataclass
class Shipment:
    shipment_id: str
    order_id: str
    warehouse_id: str
    carrier: str
    tracking_no: str
    status: str
    shipped_at: str
    created_at: str
    updated_at: str


@dataclass
class ShipmentLine:
    shipment_line_id: str
    shipment_id: str
    order_line_id: str
    qty_shipped: int
    delivered_at: str | None
    created_at: str
    updated_at: str


@dataclass
class Return:
    return_id: str
    order_id: str
    reason: str
    status: str
    requested_at: str
    resolved_at: str | None
    created_at: str
    updated_at: str


@dataclass
class ReturnLine:
    return_line_id: str
    return_id: str
    order_line_id: str
    qty_returned: int
    refund_amount: float
    created_at: str
    updated_at: str


# ── Advertising ──────────────────────────────────────────────────────────────


@dataclass
class Advertiser:
    advertiser_id: str
    name: str
    billing_email: str
    status: str
    created_at: str
    updated_at: str


@dataclass
class Campaign:
    campaign_id: str
    advertiser_id: str
    name: str
    objective: str
    budget_total: float
    budget_daily: float
    start_date: str
    end_date: str
    created_at: str
    updated_at: str


@dataclass
class AdGroup:
    ad_group_id: str
    campaign_id: str
    name: str
    targeting_type: str
    bid_strategy: str
    max_cpc: float
    status: str
    created_at: str
    updated_at: str


@dataclass
class AdCreative:
    creative_id: str
    ad_group_id: str
    format: str
    headline: str
    image_url: str
    destination_url: str
    created_at: str
    updated_at: str


@dataclass
class Keyword:
    keyword_id: str
    term: str
    match_type: str
    language: str
    created_at: str
    updated_at: str


@dataclass
class AdGroupKeyword:
    ad_group_id: str
    keyword_id: str
    bid_override: float | None
    is_negative: bool
    created_at: str
    updated_at: str


@dataclass
class AdImpression:
    impression_id: str
    creative_id: str
    session_id: str
    customer_id: str
    placement: str
    cost: float
    impressed_at: str
    created_at: str


@dataclass
class AdClick:
    click_id: str
    impression_id: str
    session_id: str
    cost: float
    clicked_at: str
    created_at: str


@dataclass
class AdConversion:
    conversion_id: str
    click_id: str
    order_id: str
    revenue: float
    converted_at: str
    attribution: str
    created_at: str


# ---------------------------------------------------------------------------
# Table registry — ordered for FK-safe creation and truncation
# ---------------------------------------------------------------------------

# Maps table name → dataclass
TABLE_REGISTRY: dict[str, type] = {
    # Fixed catalog
    "warehouse": Warehouse,
    "product_category": ProductCategory,
    "product": Product,
    "product_variant": ProductVariant,
    "product_attribute": ProductAttribute,
    "inventory": Inventory,
    "advertiser": Advertiser,
    "campaign": Campaign,
    "ad_group": AdGroup,
    "ad_creative": AdCreative,
    "keyword": Keyword,
    "ad_group_keyword": AdGroupKeyword,
    # Customer-driven
    "customer": Customer,
    "customer_address": CustomerAddress,
    "device": Device,
    "session": Session,
    "order": Order,
    "order_line": OrderLine,
    "payment": Payment,
    "shipment": Shipment,
    "shipment_line": ShipmentLine,
    "return": Return,
    "return_line": ReturnLine,
    # Events
    "ad_impression": AdImpression,
    "ad_click": AdClick,
    "ad_conversion": AdConversion,
}

# FK-safe drop order (reverse of creation order)
DROP_ORDER = list(reversed(TABLE_REGISTRY.keys()))


def get_columns(table_name: str) -> list[str]:
    """Return ordered column names for a table (used for CSV headers)."""
    dc = TABLE_REGISTRY[table_name]
    return [f.name for f in fields(dc)]


def row_to_dict(row: Any) -> dict:
    """Convert a dataclass instance to an ordered dict."""
    return {f.name: getattr(row, f.name) for f in fields(row)}


# ---------------------------------------------------------------------------
# DDL — CREATE TABLE statements
# ---------------------------------------------------------------------------

DDL: dict[str, str] = {
    "warehouse": """
        CREATE TABLE warehouse (
            warehouse_id  UUID        PRIMARY KEY,
            name          VARCHAR     NOT NULL,
            country       CHAR(2)     NOT NULL,
            city          VARCHAR     NOT NULL,
            is_active     BOOLEAN     NOT NULL DEFAULT TRUE,
            timezone      VARCHAR     NOT NULL,
            created_at    TIMESTAMPTZ NOT NULL,
            updated_at    TIMESTAMPTZ NOT NULL
        )
    """,
    "product_category": """
        CREATE TABLE product_category (
            category_id   UUID        PRIMARY KEY,
            parent_id     UUID        REFERENCES product_category(category_id),
            name          VARCHAR     NOT NULL,
            slug          VARCHAR     NOT NULL UNIQUE,
            depth         INT         NOT NULL DEFAULT 0,
            created_at    TIMESTAMPTZ NOT NULL,
            updated_at    TIMESTAMPTZ NOT NULL
        )
    """,
    "product": """
        CREATE TABLE product (
            product_id    UUID        PRIMARY KEY,
            category_id   UUID        NOT NULL REFERENCES product_category(category_id),
            name          VARCHAR     NOT NULL,
            description   TEXT,
            brand         VARCHAR,
            base_price    NUMERIC(12,2) NOT NULL,
            status        VARCHAR     NOT NULL DEFAULT 'active',
            created_at    TIMESTAMPTZ NOT NULL,
            updated_at    TIMESTAMPTZ NOT NULL
        )
    """,
    "product_variant": """
        CREATE TABLE product_variant (
            variant_id      UUID          PRIMARY KEY,
            product_id      UUID          NOT NULL REFERENCES product(product_id),
            sku             VARCHAR       NOT NULL UNIQUE,
            size            VARCHAR,
            color           VARCHAR,
            price_override  NUMERIC(12,2),
            weight_kg       NUMERIC(8,3)  NOT NULL,
            is_active       BOOLEAN       NOT NULL DEFAULT TRUE,
            created_at      TIMESTAMPTZ   NOT NULL,
            updated_at      TIMESTAMPTZ   NOT NULL
        )
    """,
    "product_attribute": """
        CREATE TABLE product_attribute (
            attribute_id   UUID        PRIMARY KEY,
            variant_id     UUID        NOT NULL REFERENCES product_variant(variant_id),
            attr_key       VARCHAR     NOT NULL,
            attr_value     VARCHAR     NOT NULL,
            display_order  INT         NOT NULL DEFAULT 0,
            created_at     TIMESTAMPTZ NOT NULL,
            updated_at     TIMESTAMPTZ NOT NULL
        )
    """,
    "inventory": """
        CREATE TABLE inventory (
            inventory_id   UUID        PRIMARY KEY,
            variant_id     UUID        NOT NULL REFERENCES product_variant(variant_id),
            warehouse_id   UUID        NOT NULL REFERENCES warehouse(warehouse_id),
            qty_on_hand    INT         NOT NULL DEFAULT 0,
            qty_reserved   INT         NOT NULL DEFAULT 0,
            created_at     TIMESTAMPTZ NOT NULL,
            updated_at     TIMESTAMPTZ NOT NULL,
            UNIQUE (variant_id, warehouse_id)
        )
    """,
    "advertiser": """
        CREATE TABLE advertiser (
            advertiser_id   UUID        PRIMARY KEY,
            name            VARCHAR     NOT NULL,
            billing_email   VARCHAR     NOT NULL,
            status          VARCHAR     NOT NULL DEFAULT 'active',
            created_at      TIMESTAMPTZ NOT NULL,
            updated_at      TIMESTAMPTZ NOT NULL
        )
    """,
    "campaign": """
        CREATE TABLE campaign (
            campaign_id     UUID          PRIMARY KEY,
            advertiser_id   UUID          NOT NULL REFERENCES advertiser(advertiser_id),
            name            VARCHAR       NOT NULL,
            objective       VARCHAR       NOT NULL,
            budget_total    NUMERIC(14,2) NOT NULL,
            budget_daily    NUMERIC(14,2) NOT NULL,
            start_date      DATE          NOT NULL,
            end_date        DATE          NOT NULL,
            created_at      TIMESTAMPTZ   NOT NULL,
            updated_at      TIMESTAMPTZ   NOT NULL
        )
    """,
    "ad_group": """
        CREATE TABLE ad_group (
            ad_group_id      UUID          PRIMARY KEY,
            campaign_id      UUID          NOT NULL REFERENCES campaign(campaign_id),
            name             VARCHAR       NOT NULL,
            targeting_type   VARCHAR       NOT NULL,
            bid_strategy     VARCHAR       NOT NULL,
            max_cpc          NUMERIC(10,4) NOT NULL,
            status           VARCHAR       NOT NULL DEFAULT 'active',
            created_at       TIMESTAMPTZ   NOT NULL,
            updated_at       TIMESTAMPTZ   NOT NULL
        )
    """,
    "ad_creative": """
        CREATE TABLE ad_creative (
            creative_id       UUID        PRIMARY KEY,
            ad_group_id       UUID        NOT NULL REFERENCES ad_group(ad_group_id),
            format            VARCHAR     NOT NULL,
            headline          VARCHAR     NOT NULL,
            image_url         VARCHAR,
            destination_url   VARCHAR     NOT NULL,
            created_at        TIMESTAMPTZ NOT NULL,
            updated_at        TIMESTAMPTZ NOT NULL
        )
    """,
    "keyword": """
        CREATE TABLE keyword (
            keyword_id   UUID        PRIMARY KEY,
            term         VARCHAR     NOT NULL,
            match_type   VARCHAR     NOT NULL,
            language     CHAR(2)     NOT NULL DEFAULT 'en',
            created_at   TIMESTAMPTZ NOT NULL,
            updated_at   TIMESTAMPTZ NOT NULL
        )
    """,
    "ad_group_keyword": """
        CREATE TABLE ad_group_keyword (
            ad_group_id    UUID          NOT NULL REFERENCES ad_group(ad_group_id),
            keyword_id     UUID          NOT NULL REFERENCES keyword(keyword_id),
            bid_override   NUMERIC(10,4),
            is_negative    BOOLEAN       NOT NULL DEFAULT FALSE,
            created_at     TIMESTAMPTZ   NOT NULL,
            updated_at     TIMESTAMPTZ   NOT NULL,
            PRIMARY KEY (ad_group_id, keyword_id)
        )
    """,
    "customer": """
        CREATE TABLE customer (
            customer_id   UUID        PRIMARY KEY,
            email         VARCHAR     NOT NULL UNIQUE,
            full_name     VARCHAR     NOT NULL,
            phone         VARCHAR,
            status        VARCHAR     NOT NULL DEFAULT 'active',
            created_at    TIMESTAMPTZ NOT NULL,
            updated_at    TIMESTAMPTZ NOT NULL
        )
    """,
    "customer_address": """
        CREATE TABLE customer_address (
            address_id    UUID        PRIMARY KEY,
            customer_id   UUID        NOT NULL REFERENCES customer(customer_id),
            line1         VARCHAR     NOT NULL,
            city          VARCHAR     NOT NULL,
            state         VARCHAR,
            country       CHAR(2)     NOT NULL,
            is_default    BOOLEAN     NOT NULL DEFAULT FALSE,
            created_at    TIMESTAMPTZ NOT NULL,
            updated_at    TIMESTAMPTZ NOT NULL
        )
    """,
    "device": """
        CREATE TABLE device (
            device_id     UUID        PRIMARY KEY,
            customer_id   UUID        NOT NULL REFERENCES customer(customer_id),
            type          VARCHAR     NOT NULL,
            os            VARCHAR     NOT NULL,
            user_agent    TEXT,
            created_at    TIMESTAMPTZ NOT NULL,
            updated_at    TIMESTAMPTZ NOT NULL
        )
    """,
    "session": """
        CREATE TABLE session (
            session_id    UUID        PRIMARY KEY,
            customer_id   UUID        NOT NULL REFERENCES customer(customer_id),
            device_id     UUID        NOT NULL REFERENCES device(device_id),
            channel       VARCHAR     NOT NULL,
            started_at    TIMESTAMPTZ NOT NULL,
            ended_at      TIMESTAMPTZ NOT NULL,
            created_at    TIMESTAMPTZ NOT NULL,
            updated_at    TIMESTAMPTZ NOT NULL
        )
    """,
    "order": """
        CREATE TABLE "order" (
            order_id           UUID          PRIMARY KEY,
            customer_id        UUID          NOT NULL REFERENCES customer(customer_id),
            shipping_addr_id   UUID          NOT NULL REFERENCES customer_address(address_id),
            billing_addr_id    UUID          NOT NULL REFERENCES customer_address(address_id),
            status             VARCHAR       NOT NULL,
            total_amount       NUMERIC(14,2) NOT NULL,
            placed_at          TIMESTAMPTZ   NOT NULL,
            created_at         TIMESTAMPTZ   NOT NULL,
            updated_at         TIMESTAMPTZ   NOT NULL
        )
    """,
    "order_line": """
        CREATE TABLE order_line (
            order_line_id   UUID          PRIMARY KEY,
            order_id        UUID          NOT NULL REFERENCES "order"(order_id),
            variant_id      UUID          NOT NULL REFERENCES product_variant(variant_id),
            quantity        INT           NOT NULL,
            unit_price      NUMERIC(12,2) NOT NULL,
            discount_amt    NUMERIC(12,2) NOT NULL DEFAULT 0,
            line_total      NUMERIC(12,2) NOT NULL,
            created_at      TIMESTAMPTZ   NOT NULL,
            updated_at      TIMESTAMPTZ   NOT NULL
        )
    """,
    "payment": """
        CREATE TABLE payment (
            payment_id     UUID          PRIMARY KEY,
            order_id       UUID          NOT NULL REFERENCES "order"(order_id),
            method         VARCHAR       NOT NULL,
            amount         NUMERIC(14,2) NOT NULL,
            status         VARCHAR       NOT NULL,
            provider_ref   VARCHAR,
            paid_at        TIMESTAMPTZ   NOT NULL,
            created_at     TIMESTAMPTZ   NOT NULL,
            updated_at     TIMESTAMPTZ   NOT NULL
        )
    """,
    "shipment": """
        CREATE TABLE shipment (
            shipment_id    UUID        PRIMARY KEY,
            order_id       UUID        NOT NULL REFERENCES "order"(order_id),
            warehouse_id   UUID        NOT NULL REFERENCES warehouse(warehouse_id),
            carrier        VARCHAR     NOT NULL,
            tracking_no    VARCHAR     NOT NULL,
            status         VARCHAR     NOT NULL,
            shipped_at     TIMESTAMPTZ NOT NULL,
            created_at     TIMESTAMPTZ NOT NULL,
            updated_at     TIMESTAMPTZ NOT NULL
        )
    """,
    "shipment_line": """
        CREATE TABLE shipment_line (
            shipment_line_id   UUID        PRIMARY KEY,
            shipment_id        UUID        NOT NULL REFERENCES shipment(shipment_id),
            order_line_id      UUID        NOT NULL REFERENCES order_line(order_line_id),
            qty_shipped        INT         NOT NULL,
            delivered_at       TIMESTAMPTZ,
            created_at         TIMESTAMPTZ NOT NULL,
            updated_at         TIMESTAMPTZ NOT NULL
        )
    """,
    "return": """
        CREATE TABLE "return" (
            return_id       UUID        PRIMARY KEY,
            order_id        UUID        NOT NULL REFERENCES "order"(order_id),
            reason          VARCHAR     NOT NULL,
            status          VARCHAR     NOT NULL,
            requested_at    TIMESTAMPTZ NOT NULL,
            resolved_at     TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL,
            updated_at      TIMESTAMPTZ NOT NULL
        )
    """,
    "return_line": """
        CREATE TABLE return_line (
            return_line_id   UUID          PRIMARY KEY,
            return_id        UUID          NOT NULL REFERENCES "return"(return_id),
            order_line_id    UUID          NOT NULL REFERENCES order_line(order_line_id),
            qty_returned     INT           NOT NULL,
            refund_amount    NUMERIC(12,2) NOT NULL,
            created_at       TIMESTAMPTZ   NOT NULL,
            updated_at       TIMESTAMPTZ   NOT NULL
        )
    """,
    "ad_impression": """
        CREATE TABLE ad_impression (
            impression_id   UUID          PRIMARY KEY,
            creative_id     UUID          NOT NULL REFERENCES ad_creative(creative_id),
            session_id      UUID          NOT NULL REFERENCES session(session_id),
            customer_id     UUID          NOT NULL REFERENCES customer(customer_id),
            placement       VARCHAR       NOT NULL,
            cost            NUMERIC(10,6) NOT NULL,
            impressed_at    TIMESTAMPTZ   NOT NULL,
            created_at      TIMESTAMPTZ   NOT NULL
        )
    """,
    "ad_click": """
        CREATE TABLE ad_click (
            click_id        UUID          PRIMARY KEY,
            impression_id   UUID          NOT NULL REFERENCES ad_impression(impression_id),
            session_id      UUID          NOT NULL REFERENCES session(session_id),
            cost            NUMERIC(10,6) NOT NULL,
            clicked_at      TIMESTAMPTZ   NOT NULL,
            created_at      TIMESTAMPTZ   NOT NULL
        )
    """,
    "ad_conversion": """
        CREATE TABLE ad_conversion (
            conversion_id   UUID          PRIMARY KEY,
            click_id        UUID          NOT NULL REFERENCES ad_click(click_id),
            order_id        UUID          NOT NULL REFERENCES "order"(order_id),
            revenue         NUMERIC(14,2) NOT NULL,
            converted_at    TIMESTAMPTZ   NOT NULL,
            attribution     VARCHAR       NOT NULL,
            created_at      TIMESTAMPTZ   NOT NULL
        )
    """,
}
