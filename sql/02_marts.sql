-- 02_marts.sql
-- Build the analysis tables from staging.
--   mart.fct_orders     one row per order, with every delivery and review metric used in the analysis
--   mart.dim_customers  one row per real customer (customer_unique_id)
--   mart.dim_sellers    one row per seller

create schema if not exists mart;

-- Item-level rollup per order. Most orders have one seller; 1.3% have more than one.
create or replace temp table order_item_rollup as
with items as (
    select i.*, p.category
    from staging.order_items i
    left join staging.products p using (product_id)
),
category_rank as (
    -- main category = the category with the most item value in the order
    select order_id, category,
        row_number() over (partition by order_id order by sum(price) desc, category) as rn
    from items
    group by order_id, category
)
select
    i.order_id,
    count(*)                         as n_items,
    count(distinct i.seller_id)      as n_sellers,
    case when count(distinct i.seller_id) = 1 then any_value(i.seller_id) end as seller_id,
    max(i.ship_by_at)                as ship_by_at,
    sum(i.price)                     as items_value,
    sum(i.freight)                   as freight_value,
    any_value(c.category)            as main_category
from items i
left join category_rank c on c.order_id = i.order_id and c.rn = 1
group by i.order_id;

create or replace table mart.fct_orders as
with pay as (
    select order_id, sum(payment_value) as payment_value
    from staging.payments
    group by order_id
)
select
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    c.customer_state,
    o.order_status,
    o.purchased_at,
    cast(o.purchased_at as date)                           as purchase_date,
    cast(date_trunc('month', o.purchased_at) as date)      as purchase_month,
    o.approved_at,
    o.handed_to_carrier_at,
    o.delivered_at,
    o.promised_date,

    r.n_items,
    r.n_sellers,
    r.seller_id,
    s.seller_state,
    s.seller_state || '>' || c.customer_state              as route,
    r.ship_by_at,
    r.items_value,
    r.freight_value,
    p.payment_value,
    r.main_category,
    rv.review_score,

    -- delivery metrics, all in whole calendar days because the promise is a calendar date
    (o.order_status = 'delivered' and o.delivered_at is not null)                  as is_delivered,
    date_diff('day', cast(o.purchased_at as date), cast(o.delivered_at as date))    as actual_days,
    date_diff('day', cast(o.purchased_at as date), o.promised_date)                 as promised_days,
    date_diff('day', o.promised_date, cast(o.delivered_at as date))                 as days_vs_promise,  -- > 0 means late
    cast(o.delivered_at as date) > o.promised_date                                  as is_late,

    -- where the time went: seller side (until handoff) and carrier side (after handoff)
    date_diff('minute', o.purchased_at, o.handed_to_carrier_at) / 1440.0           as seller_days,
    date_diff('minute', o.handed_to_carrier_at, o.delivered_at) / 1440.0           as carrier_days,
    o.handed_to_carrier_at > r.ship_by_at                                           as missed_ship_by,
    greatest(0, date_diff('minute', r.ship_by_at, o.handed_to_carrier_at) / 1440.0) as days_past_ship_by,

    -- customer history (window functions over the real customer id)
    row_number() over (partition by c.customer_unique_id order by o.purchased_at, o.order_id) as customer_order_seq
from staging.orders o
join staging.customers c using (customer_id)
left join order_item_rollup r using (order_id)
left join staging.sellers s on s.seller_id = r.seller_id
left join pay p using (order_id)
left join staging.reviews rv using (order_id);

create or replace table mart.dim_customers as
select
    customer_unique_id,
    any_value(customer_state)          as customer_state,
    count(*)                           as n_orders,
    min(purchased_at)                  as first_order_at,
    max(purchased_at)                  as last_order_at
from mart.fct_orders
group by customer_unique_id;

create or replace table mart.dim_sellers as
select
    s.seller_id,
    s.seller_state,
    count(f.order_id)                                   as n_orders,
    count(f.order_id) filter (where f.is_delivered)     as n_delivered
from staging.sellers s
left join mart.fct_orders f using (seller_id)
group by s.seller_id, s.seller_state;
