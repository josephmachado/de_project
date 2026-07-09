---
title: "datagen"
format:
  html:
    theme: flatly
    toc: true
    toc-depth: 3
    code-copy: true
    lightbox: true
---

Realistic OLTP data generator for an **E-Commerce + Advertising** platform schema.
Generates 25 interrelated tables with causally ordered timestamps and power-law distributed row counts.
 
---

## Setup and Run

**Prerequisites**

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) installed

```bash
cd datagen
uv sync
```

**Output to CSV files:**
```bash
uv run datagen \
  --customers 1000 \
  --start     2025-01-01 \
  --end       2025-12-08 \
  --output    ./output/
```

**Output to PostgreSQL:**
```bash
uv run datagen --customers 1000 --start 2025-01-01 --end 2025-12-08 --output postgres://dataengineer:datapipeline@postgres:5432/ecommerce

```

### CLI Options

| Option | Required | Default | Description |
|---|---|---|---|
| `--customers` | ✅ | — | Number of customers (drives all row counts) |
| `--start` | ✅ | — | Start date for all timestamps (`YYYY-MM-DD`) |
| `--end` | ✅ | — | End date for all timestamps (`YYYY-MM-DD`) |
| `--output` | ✅ | — | `postgres://...` connection string or folder path |
| `--seed` | ❌ | `42` | Random seed for reproducibility |
| `--batch-size` | ❌ | `1000` | Rows per write batch |

### Validate Data Generated 

```bash
rm -rf local.db
duckdb local.db < load.sql 
duckdb local.db -cmd ".mode line" < ./data_quality_check/data_validation_check.sql  # should return all 0's
```

---

## ERD

### Modules

The schema is organised into 4 domains:

```
👤 User & Identity     4 tables   customer, customer_address, device, session
🛒 Core E-Commerce    11 tables   product_category, product, product_variant,
                                  product_attribute, inventory, order, order_line,
                                  payment, return, return_line
📦 Fulfillment         3 tables   warehouse, shipment, shipment_line
📣 Advertising         8 tables   advertiser, campaign, ad_group, ad_creative,
                                  keyword, ad_group_keyword,
                                  ad_impression, ad_click, ad_conversion
```

### Relationship Overview

```
customer
  ├── customer_address  (1:N  ~2 per customer)
  ├── device            (1:N  ~1.5 per customer)
  ├── session           (1:N  ~20 per customer, lognormal)
  │     └── ad_impression  (1:N  ~5 per session, zipf)
  │           └── ad_click      (1:N  ~3% CTR, beta)
  │                 └── ad_conversion  (1:N  ~10% CVR → links to order)
  └── order             (1:N  ~3 per customer, negative binomial / 80-20)
        ├── order_line  (1:N  ~2.5 per order, zipf)
        ├── payment     (1:1)
        ├── shipment    (1:1  FK → warehouse)
        │     └── shipment_line  (mirrors order_lines)
        └── return      (1:0..1  ~10% of orders)
              └── return_line

warehouse
  ├── inventory         (1 row per variant × warehouse)
  └── shipment          (1:N  orders fulfilled from here)

product_category        (self-referencing, depth=0/1)
  └── product
        └── product_variant
              ├── product_attribute  (1:N  ~2 per variant)
              └── inventory          (1:N  → warehouse)

advertiser
  └── campaign
        └── ad_group
              ├── ad_creative       (1:N  ~4 per group)
              └── ad_group_keyword  (M:N junction → keyword)

keyword                 (referenced via ad_group_keyword)
```

### Table Reference

#### 👤 User & Identity

| Table | PK | Description |
|---|---|---|
| `customer` | `customer_id` | Core user account. **Grain:** one row per customer. |
| `customer_address` | `address_id` | Shipping and billing addresses per customer. **Grain:** one row per address per customer. |
| `device` | `device_id` | Known devices a customer has used. **Grain:** one row per device per customer.  |
| `session` | `session_id` | Web or app browsing sessions. **Grain:** one row per session. |


#### 🛒 Core E-Commerce

| Table | PK | Description |
|---|---|---|
| `product_category` | `category_id` | Hierarchical product taxonomy. **Grain:** one row per category.|
| `product` | `product_id` | Master product catalog. **Grain:** one row per product.|
| `product_variant` | `variant_id` | Purchasable SKUs per product. **Grain:** one row per size/color combination per product. |
| `product_attribute` | `attribute_id` | Key-value metadata for a variant. **Grain:** one row per attribute per variant. |
| `inventory` | `inventory_id` | Stock levels per SKU per warehouse. **Grain:** one row per variant per warehouse. |
| `order` | `order_id` | Purchase order header. **Grain:** one row per order per customer. |
| `order_line` | `order_line_id` | Line items within an order. **Grain:** one row per variant per order. |
| `payment` | `payment_id` | Payment transaction per order. **Grain:** one row per order. |
| `return` | `return_id` | Return request header. **Grain:** one row per return request per order. |
| `return_line` | `return_line_id` | Line items included in a return. **Grain:** one row per order line per return |

#### 📦 Fulfillment

| Table | PK | Description |
|---|---|---|
| `warehouse` | `warehouse_id` | Physical fulfillment center information. **Grain:** one row per warehouse |
| `shipment` | `shipment_id` | Outbound shipment per order. **Grain:** one row per order. |
| `shipment_line` | `shipment_line_id` | Line items within a shipment. **Grain:** one row per order line per shipment. |

#### 📣 Advertising

| Table | PK | Description |
|---|---|---|
| `advertiser` | `advertiser_id` | Brand or seller running ads. **Grain:** one row per advertiser |
| `campaign` | `campaign_id` | Ad campaign with budget and schedule. **Grain:** one row per campaign per advertiser.|
| `ad_group` | `ad_group_id` | Targeting group within a campaign. **Grain:** one row per ad group per campaign |
| `ad_creative` | `creative_id` | Ad asset with headline, image, and destination URL. **Grain:** one row per creative per ad group |
| `keyword` | `keyword_id` | Search keyword with match type. **Grain:** one row per keyword |
| `ad_group_keyword` | composite FK | Junction between ad groups and keywords. **Grain:** one row per keyword per ad group |
| `ad_impression` | `impression_id` | Ad display event. **Grain:** one row per impression per session. |
| `ad_click` | `click_id` | Click on an impression. **Grain:** one row per click per impression. |
| `ad_conversion` | `conversion_id` | Click-to-order attribution event. **Grain:** one row per conversion per click. |

### Timestamp Rules

Most tables have `created_at` and `updated_at`. Append-only event tables (`ad_impression`, `ad_click`, `ad_conversion`) only have `created_at`.

`updated_at` reflects the last state change on a row — it equals `created_at` for immutable rows and is strictly greater for rows that have transitioned status:

| Table | `updated_at` behaviour |
|---|---|
| `customer` | `> created_at` when status is `inactive` or `suspended` |
| `customer_address` | `> created_at` when a newer default address was added |
| `session` | always equals `ended_at` |
| `order` | `> created_at` for all non-`pending` statuses |
| `payment` | `> created_at` for all non-`pending` statuses |
| `shipment` | `> created_at` for all non-`processing` statuses |
| `return` | `> created_at` for terminal statuses; equals `resolved_at` |

All timestamps are causally ordered — a child row's timestamp is always ≥ its parent's:
```
customer.created_at
  → customer_address.created_at  ≥ customer.created_at
  → device.created_at            ≥ customer.created_at
  → session.started_at           ≥ max(customer.created_at, device.created_at)
  → order.placed_at              ≥ customer.created_at
  → payment.paid_at              ≥ order.placed_at           (+seconds)
  → shipment.shipped_at          ≥ order.placed_at           (+hours)
  → shipment_line.delivered_at   ≥ shipment.shipped_at       (+days)
  → return.requested_at          ≥ shipment_line.delivered_at (+days)
  → return.resolved_at           > return.requested_at       (+days, terminal only)
  → impression.impressed_at      ≥ session.started_at
  → click.clicked_at             ≥ impression.impressed_at   (+seconds)
  → conversion.converted_at      ≥ click.clicked_at          (+minutes)
```
