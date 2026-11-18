-- 10 Do late first orders stop customers from coming back?
-- First orders placed Jan 2017 to Feb 2018, so every customer has a full 180 days to buy again before the data ends.
-- Repeat = another order (not canceled or unavailable) placed 1 to 180 days after the first one.
with real_orders as (
    select customer_unique_id, order_id, purchased_at
    from mart.fct_orders
    where order_status not in ('canceled', 'unavailable')
),
first_orders as (
    select *
    from mart.fct_orders
    where customer_order_seq = 1
      and is_delivered
      and purchase_date between date '2017-01-01' and date '2018-02-28'
),
repeats as (
    select f.order_id, count(r.order_id) > 0 as repeated
    from first_orders f
    left join real_orders r
        on r.customer_unique_id = f.customer_unique_id
       and r.order_id <> f.order_id
       and r.purchased_at >= f.purchased_at + interval 1 day
       and r.purchased_at <= f.purchased_at + interval 180 day
    group by f.order_id
)
select
    f.order_id,
    f.customer_unique_id,
    f.customer_state,
    strftime(f.purchase_month, '%Y-%m')     as purchase_month,
    f.items_value,
    f.is_late::int                          as late,
    f.review_score,
    r.repeated::int                         as repeated_180d
from first_orders f
join repeats r using (order_id);
