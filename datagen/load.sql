-- DuckDB: create all tables from CSV output
-- Run with: duckdb mydb.duckdb < load.sql
-- or:        duckdb -c ".read load.sql"

-- ── User & Identity ──────────────────────────────────────────────────────────

CREATE TABLE customer AS
    SELECT * FROM read_csv('./output/customer.csv', header = true, auto_detect = true);

CREATE TABLE customer_address AS
    SELECT * FROM read_csv('./output/customer_address.csv', header = true, auto_detect = true);

CREATE TABLE device AS
    SELECT * FROM read_csv('./output/device.csv', header = true, auto_detect = true);

CREATE TABLE session AS
    SELECT * FROM read_csv('./output/session.csv', header = true, auto_detect = true);

-- ── Core E-Commerce ──────────────────────────────────────────────────────────

CREATE TABLE product_category AS
    SELECT * FROM read_csv('./output/product_category.csv', header = true, auto_detect = true);

CREATE TABLE product AS
    SELECT * FROM read_csv('./output/product.csv', header = true, auto_detect = true);

CREATE TABLE product_variant AS
    SELECT * FROM read_csv('./output/product_variant.csv', header = true, auto_detect = true);

CREATE TABLE product_attribute AS
    SELECT * FROM read_csv('./output/product_attribute.csv', header = true, auto_detect = true);

CREATE TABLE inventory AS
    SELECT * FROM read_csv('./output/inventory.csv', header = true, auto_detect = true);

CREATE TABLE "order" AS
    SELECT * FROM read_csv('./output/order.csv', header = true, auto_detect = true);

CREATE TABLE order_line AS
    SELECT * FROM read_csv('./output/order_line.csv', header = true, auto_detect = true);

CREATE TABLE payment AS
    SELECT * FROM read_csv('./output/payment.csv', header = true, auto_detect = true);

CREATE TABLE "return" AS
    SELECT * FROM read_csv('./output/return.csv', header = true, auto_detect = true);

CREATE TABLE return_line AS
    SELECT * FROM read_csv('./output/return_line.csv', header = true, auto_detect = true);

-- ── Fulfillment ───────────────────────────────────────────────────────────────

CREATE TABLE warehouse AS
    SELECT * FROM read_csv('./output/warehouse.csv', header = true, auto_detect = true);

CREATE TABLE shipment AS
    SELECT * FROM read_csv('./output/shipment.csv', header = true, auto_detect = true);

CREATE TABLE shipment_line AS
    SELECT * FROM read_csv('./output/shipment_line.csv', header = true, auto_detect = true);

-- ── Advertising ───────────────────────────────────────────────────────────────

CREATE TABLE advertiser AS
    SELECT * FROM read_csv('./output/advertiser.csv', header = true, auto_detect = true);

CREATE TABLE campaign AS
    SELECT * FROM read_csv('./output/campaign.csv', header = true, auto_detect = true);

CREATE TABLE ad_group AS
    SELECT * FROM read_csv('./output/ad_group.csv', header = true, auto_detect = true);

CREATE TABLE ad_creative AS
    SELECT * FROM read_csv('./output/ad_creative.csv', header = true, auto_detect = true);

CREATE TABLE keyword AS
    SELECT * FROM read_csv('./output/keyword.csv', header = true, auto_detect = true);

CREATE TABLE ad_group_keyword AS
    SELECT * FROM read_csv('./output/ad_group_keyword.csv', header = true, auto_detect = true);

CREATE TABLE ad_impression AS
    SELECT * FROM read_csv('./output/ad_impression.csv', header = true, auto_detect = true);

CREATE TABLE ad_click AS
    SELECT * FROM read_csv('./output/ad_click.csv', header = true, auto_detect = true);

CREATE TABLE ad_conversion AS
    SELECT * FROM read_csv('./output/ad_conversion.csv', header = true, auto_detect = true);
