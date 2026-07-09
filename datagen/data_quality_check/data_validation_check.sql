-- ============================================================
-- Master validation script — FK integrity + data quality
-- Expected: every row returns 0 violations / orphaned_rows
-- Run with: duckdb mydb.duckdb < validate_all.sql
-- ============================================================

-- ── FK Integrity: User & Identity ────────────────────────────────────────────

SELECT 'customer_address → customer'                        AS check_name,
       COUNT(*) AS violations
FROM customer_address
WHERE NOT EXISTS (SELECT 1 FROM customer WHERE customer_id = customer_address.customer_id)

UNION ALL
SELECT 'device → customer',                                  COUNT(*)
FROM device
WHERE NOT EXISTS (SELECT 1 FROM customer WHERE customer_id = device.customer_id)

UNION ALL
SELECT 'session → customer',                                 COUNT(*)
FROM session
WHERE NOT EXISTS (SELECT 1 FROM customer WHERE customer_id = session.customer_id)

UNION ALL
SELECT 'session → device',                                   COUNT(*)
FROM session
WHERE NOT EXISTS (SELECT 1 FROM device WHERE device_id = session.device_id)

-- ── FK Integrity: Core E-Commerce ────────────────────────────────────────────

UNION ALL
SELECT 'product_category → product_category (parent)',       COUNT(*)
FROM product_category
WHERE parent_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM product_category p WHERE p.category_id = product_category.parent_id)

UNION ALL
SELECT 'product → product_category',                         COUNT(*)
FROM product
WHERE NOT EXISTS (SELECT 1 FROM product_category WHERE category_id = product.category_id)

UNION ALL
SELECT 'product_variant → product',                          COUNT(*)
FROM product_variant
WHERE NOT EXISTS (SELECT 1 FROM product WHERE product_id = product_variant.product_id)

UNION ALL
SELECT 'product_attribute → product_variant',                COUNT(*)
FROM product_attribute
WHERE NOT EXISTS (SELECT 1 FROM product_variant WHERE variant_id = product_attribute.variant_id)

UNION ALL
SELECT 'inventory → product_variant',                        COUNT(*)
FROM inventory
WHERE NOT EXISTS (SELECT 1 FROM product_variant WHERE variant_id = inventory.variant_id)

UNION ALL
SELECT 'inventory → warehouse',                              COUNT(*)
FROM inventory
WHERE NOT EXISTS (SELECT 1 FROM warehouse WHERE warehouse_id = inventory.warehouse_id)

UNION ALL
SELECT 'order → customer',                                   COUNT(*)
FROM "order"
WHERE NOT EXISTS (SELECT 1 FROM customer WHERE customer_id = "order".customer_id)

UNION ALL
SELECT 'order → customer_address (shipping)',                COUNT(*)
FROM "order"
WHERE NOT EXISTS (SELECT 1 FROM customer_address WHERE address_id = "order".shipping_addr_id)

UNION ALL
SELECT 'order → customer_address (billing)',                 COUNT(*)
FROM "order"
WHERE NOT EXISTS (SELECT 1 FROM customer_address WHERE address_id = "order".billing_addr_id)

UNION ALL
SELECT 'order_line → order',                                 COUNT(*)
FROM order_line
WHERE NOT EXISTS (SELECT 1 FROM "order" WHERE order_id = order_line.order_id)

UNION ALL
SELECT 'order_line → product_variant',                       COUNT(*)
FROM order_line
WHERE NOT EXISTS (SELECT 1 FROM product_variant WHERE variant_id = order_line.variant_id)

UNION ALL
SELECT 'payment → order',                                    COUNT(*)
FROM payment
WHERE NOT EXISTS (SELECT 1 FROM "order" WHERE order_id = payment.order_id)

UNION ALL
SELECT 'return → order',                                     COUNT(*)
FROM "return"
WHERE NOT EXISTS (SELECT 1 FROM "order" WHERE order_id = "return".order_id)

UNION ALL
SELECT 'return_line → return',                               COUNT(*)
FROM return_line
WHERE NOT EXISTS (SELECT 1 FROM "return" WHERE return_id = return_line.return_id)

UNION ALL
SELECT 'return_line → order_line',                           COUNT(*)
FROM return_line
WHERE NOT EXISTS (SELECT 1 FROM order_line WHERE order_line_id = return_line.order_line_id)

-- ── FK Integrity: Fulfillment ─────────────────────────────────────────────────

UNION ALL
SELECT 'shipment → order',                                   COUNT(*)
FROM shipment
WHERE NOT EXISTS (SELECT 1 FROM "order" WHERE order_id = shipment.order_id)

UNION ALL
SELECT 'shipment → warehouse',                               COUNT(*)
FROM shipment
WHERE NOT EXISTS (SELECT 1 FROM warehouse WHERE warehouse_id = shipment.warehouse_id)

UNION ALL
SELECT 'shipment_line → shipment',                           COUNT(*)
FROM shipment_line
WHERE NOT EXISTS (SELECT 1 FROM shipment WHERE shipment_id = shipment_line.shipment_id)

UNION ALL
SELECT 'shipment_line → order_line',                         COUNT(*)
FROM shipment_line
WHERE NOT EXISTS (SELECT 1 FROM order_line WHERE order_line_id = shipment_line.order_line_id)

-- ── FK Integrity: Advertising ─────────────────────────────────────────────────

UNION ALL
SELECT 'campaign → advertiser',                              COUNT(*)
FROM campaign
WHERE NOT EXISTS (SELECT 1 FROM advertiser WHERE advertiser_id = campaign.advertiser_id)

UNION ALL
SELECT 'ad_group → campaign',                                COUNT(*)
FROM ad_group
WHERE NOT EXISTS (SELECT 1 FROM campaign WHERE campaign_id = ad_group.campaign_id)

UNION ALL
SELECT 'ad_creative → ad_group',                             COUNT(*)
FROM ad_creative
WHERE NOT EXISTS (SELECT 1 FROM ad_group WHERE ad_group_id = ad_creative.ad_group_id)

UNION ALL
SELECT 'ad_group_keyword → ad_group',                        COUNT(*)
FROM ad_group_keyword
WHERE NOT EXISTS (SELECT 1 FROM ad_group WHERE ad_group_id = ad_group_keyword.ad_group_id)

UNION ALL
SELECT 'ad_group_keyword → keyword',                         COUNT(*)
FROM ad_group_keyword
WHERE NOT EXISTS (SELECT 1 FROM keyword WHERE keyword_id = ad_group_keyword.keyword_id)

UNION ALL
SELECT 'ad_impression → ad_creative',                        COUNT(*)
FROM ad_impression
WHERE NOT EXISTS (SELECT 1 FROM ad_creative WHERE creative_id = ad_impression.creative_id)

UNION ALL
SELECT 'ad_impression → session',                            COUNT(*)
FROM ad_impression
WHERE NOT EXISTS (SELECT 1 FROM session WHERE session_id = ad_impression.session_id)

UNION ALL
SELECT 'ad_impression → customer',                           COUNT(*)
FROM ad_impression
WHERE NOT EXISTS (SELECT 1 FROM customer WHERE customer_id = ad_impression.customer_id)

UNION ALL
SELECT 'ad_click → ad_impression',                           COUNT(*)
FROM ad_click
WHERE NOT EXISTS (SELECT 1 FROM ad_impression WHERE impression_id = ad_click.impression_id)

UNION ALL
SELECT 'ad_click → session',                                 COUNT(*)
FROM ad_click
WHERE NOT EXISTS (SELECT 1 FROM session WHERE session_id = ad_click.session_id)

UNION ALL
SELECT 'ad_conversion → ad_click',                           COUNT(*)
FROM ad_conversion
WHERE NOT EXISTS (SELECT 1 FROM ad_click WHERE click_id = ad_conversion.click_id)

UNION ALL
SELECT 'ad_conversion → order',                              COUNT(*)
FROM ad_conversion
WHERE NOT EXISTS (SELECT 1 FROM "order" WHERE order_id = ad_conversion.order_id)

-- ── Data Quality: User & Identity ────────────────────────────────────────────

UNION ALL
SELECT 'customer: invalid status value',                     COUNT(*)
FROM customer
WHERE status NOT IN ('active', 'inactive', 'suspended')

UNION ALL
SELECT 'customer: non-active updated_at <= created_at',      COUNT(*)
FROM customer
WHERE status != 'active'
  AND updated_at <= created_at

UNION ALL
SELECT 'customer: active updated_at != created_at',          COUNT(*)
FROM customer
WHERE status = 'active'
  AND updated_at != created_at

UNION ALL
SELECT 'customer: zero or multiple default addresses',        COUNT(*)
FROM (
    SELECT customer_id
    FROM customer_address
    GROUP BY customer_id
    HAVING SUM(CAST(is_default AS INT)) != 1
)

UNION ALL
SELECT 'customer_address: created_at < customer.created_at', COUNT(*)
FROM customer_address ca
JOIN customer c ON c.customer_id = ca.customer_id
WHERE ca.created_at < c.created_at

UNION ALL
SELECT 'customer_address: updated_at < created_at',          COUNT(*)
FROM customer_address
WHERE updated_at < created_at

UNION ALL
SELECT 'device: created_at < customer.created_at',           COUNT(*)
FROM device d
JOIN customer c ON c.customer_id = d.customer_id
WHERE d.created_at < c.created_at

UNION ALL
SELECT 'session: started_at < customer.created_at',          COUNT(*)
FROM session s
JOIN customer c ON c.customer_id = s.customer_id
WHERE s.started_at < c.created_at

UNION ALL
SELECT 'session: started_at < device.created_at',            COUNT(*)
FROM session s
JOIN device d ON d.device_id = s.device_id
WHERE s.started_at < d.created_at

UNION ALL
SELECT 'session: updated_at != ended_at',                    COUNT(*)
FROM session
WHERE updated_at != ended_at

-- ── Data Quality: Core E-Commerce ────────────────────────────────────────────

UNION ALL
SELECT 'order: total_amount = 0',                            COUNT(*)
FROM "order"
WHERE total_amount = 0.0

UNION ALL
SELECT 'order: total_amount != sum of order_lines',          COUNT(*)
FROM (
    SELECT o.order_id
    FROM "order" o
    JOIN order_line ol ON ol.order_id = o.order_id
    GROUP BY o.order_id, o.total_amount
    HAVING o.total_amount != ROUND(SUM(ol.line_total), 2)
)

UNION ALL
SELECT 'order: invalid status value',                        COUNT(*)
FROM "order"
WHERE status NOT IN ('pending', 'confirmed', 'shipped', 'delivered')

UNION ALL
SELECT 'order: non-pending updated_at <= created_at',        COUNT(*)
FROM "order"
WHERE status != 'pending'
  AND updated_at <= created_at

UNION ALL
SELECT 'order: pending updated_at != created_at',            COUNT(*)
FROM "order"
WHERE status = 'pending'
  AND updated_at != created_at

UNION ALL
SELECT 'order: placed_at < customer.created_at',             COUNT(*)
FROM "order" o
JOIN customer c ON c.customer_id = o.customer_id
WHERE o.placed_at < c.created_at

UNION ALL
SELECT 'payment: non-pending updated_at <= created_at',      COUNT(*)
FROM payment
WHERE status != 'pending'
  AND updated_at <= created_at

UNION ALL
SELECT 'payment: pending updated_at != created_at',          COUNT(*)
FROM payment
WHERE status = 'pending'
  AND updated_at != created_at

UNION ALL
SELECT 'payment: refunded with no corresponding return',     COUNT(*)
FROM payment p
WHERE p.status = 'refunded'
  AND NOT EXISTS (SELECT 1 FROM "return" r WHERE r.order_id = p.order_id)

UNION ALL
SELECT 'return: terminal updated_at != resolved_at',         COUNT(*)
FROM "return"
WHERE status IN ('refunded', 'rejected')
  AND updated_at != resolved_at

UNION ALL
SELECT 'return: terminal resolved_at <= requested_at',       COUNT(*)
FROM "return"
WHERE status IN ('refunded', 'rejected')
  AND resolved_at <= requested_at

UNION ALL
SELECT 'return: open status has resolved_at set',            COUNT(*)
FROM "return"
WHERE status IN ('requested', 'approved', 'received')
  AND resolved_at IS NOT NULL

UNION ALL
SELECT 'return: open status updated_at != created_at',       COUNT(*)
FROM "return"
WHERE status IN ('requested', 'approved', 'received')
  AND updated_at != created_at

-- ── Data Quality: Fulfillment ─────────────────────────────────────────────────

UNION ALL
SELECT 'shipment: shipped_at < order.placed_at',             COUNT(*)
FROM shipment s
JOIN "order" o ON o.order_id = s.order_id
WHERE s.shipped_at < o.placed_at

UNION ALL
SELECT 'shipment: non-processing updated_at <= created_at',  COUNT(*)
FROM shipment
WHERE status != 'processing'
  AND updated_at <= created_at

UNION ALL
SELECT 'shipment: processing updated_at != created_at',      COUNT(*)
FROM shipment
WHERE status = 'processing'
  AND updated_at != created_at

-- ── Data Quality: Advertising ─────────────────────────────────────────────────

UNION ALL
SELECT 'campaign: start_date < created_at date',             COUNT(*)
FROM campaign
WHERE start_date < CAST(created_at AS DATE)

UNION ALL
SELECT 'campaign: end_date < start_date',                    COUNT(*)
FROM campaign
WHERE end_date < start_date

UNION ALL
SELECT 'ad_impression: has updated_at column',               COUNT(*)
FROM information_schema.columns
WHERE table_name = 'ad_impression'
  AND column_name = 'updated_at'

UNION ALL
SELECT 'ad_click: has updated_at column',                    COUNT(*)
FROM information_schema.columns
WHERE table_name = 'ad_click'
  AND column_name = 'updated_at'

UNION ALL
SELECT 'ad_conversion: has updated_at column',               COUNT(*)
FROM information_schema.columns
WHERE table_name = 'ad_conversion'
  AND column_name = 'updated_at'

UNION ALL
SELECT 'ad_impression: impressed_at < session.started_at',   COUNT(*)
FROM ad_impression ai
JOIN session s ON s.session_id = ai.session_id
WHERE ai.impressed_at < s.started_at

UNION ALL
SELECT 'ad_impression: impressed_at > session.ended_at',     COUNT(*)
FROM ad_impression ai
JOIN session s ON s.session_id = ai.session_id
WHERE ai.impressed_at > s.ended_at

UNION ALL
SELECT 'ad_click: clicked_at < impression.impressed_at',     COUNT(*)
FROM ad_click ac
JOIN ad_impression ai ON ai.impression_id = ac.impression_id
WHERE ac.clicked_at < ai.impressed_at

UNION ALL
SELECT 'ad_conversion: converted_at < click.clicked_at',     COUNT(*)
FROM ad_conversion ac
JOIN ad_click cl ON cl.click_id = ac.click_id
WHERE ac.converted_at < cl.clicked_at

ORDER BY check_name;
