-- 01_staging.sql
-- Load the raw Olist CSVs into typed, cleaned staging tables.
-- One staging table per source file. No business logic here, just types, names and dedupes.
-- {raw} is replaced with the path to data/raw by src/build_warehouse.py

create schema if not exists staging;

create or replace table staging.orders as
select
    order_id,
    customer_id,
    order_status,
    cast(order_purchase_timestamp as timestamp)       as purchased_at,
    cast(order_approved_at as timestamp)              as approved_at,
    cast(order_delivered_carrier_date as timestamp)   as handed_to_carrier_at,
    cast(order_delivered_customer_date as timestamp)  as delivered_at,
    cast(order_estimated_delivery_date as date)       as promised_date
from read_csv_auto('{raw}/olist_orders_dataset.csv.gz', header = true);

create or replace table staging.customers as
select
    customer_id,
    customer_unique_id,                -- the real person; customer_id is new for every order
    customer_zip_code_prefix as customer_zip_prefix,
    customer_city,
    customer_state
from read_csv_auto('{raw}/olist_customers_dataset.csv.gz', header = true);

create or replace table staging.order_items as
select
    order_id,
    order_item_id,
    product_id,
    seller_id,
    cast(shipping_limit_date as timestamp) as ship_by_at,   -- deadline for the seller to hand off to the carrier
    cast(price as double)                  as price,
    cast(freight_value as double)          as freight
from read_csv_auto('{raw}/olist_order_items_dataset.csv.gz', header = true);

create or replace table staging.payments as
select
    order_id,
    payment_sequential,
    payment_type,
    payment_installments,
    cast(payment_value as double) as payment_value
from read_csv_auto('{raw}/olist_order_payments_dataset.csv.gz', header = true);

-- Some orders have more than one review. Keep the most recent answer per order.
create or replace table staging.reviews as
with raw as (
    select
        review_id,
        order_id,
        cast(review_score as integer)            as review_score,
        cast(review_creation_date as timestamp)  as review_created_at,
        cast(review_answer_timestamp as timestamp) as review_answered_at,
        review_comment_message is not null       as has_comment
    from read_csv_auto('{raw}/olist_order_reviews_dataset.csv.gz', header = true)
),
ranked as (
    select *,
        row_number() over (
            partition by order_id
            order by review_answered_at desc, review_created_at desc, review_id
        ) as rn
    from raw
)
select review_id, order_id, review_score, review_created_at, review_answered_at, has_comment
from ranked
where rn = 1;

create or replace table staging.products as
select
    p.product_id,
    p.product_category_name                                           as category_pt,
    coalesce(t.product_category_name_english, p.product_category_name, 'unknown') as category,
    cast(p.product_weight_g as double)                                as weight_g
from read_csv_auto('{raw}/olist_products_dataset.csv.gz', header = true) p
left join read_csv_auto('{raw}/product_category_name_translation.csv.gz', header = true) t
    on p.product_category_name = t.product_category_name;

create or replace table staging.sellers as
select
    seller_id,
    seller_zip_code_prefix as seller_zip_prefix,
    seller_city,
    seller_state
from read_csv_auto('{raw}/olist_sellers_dataset.csv.gz', header = true);
