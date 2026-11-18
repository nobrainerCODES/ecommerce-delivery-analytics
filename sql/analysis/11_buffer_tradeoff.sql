-- 11 The promise trade-off. If Olist added b extra days to every promise in 2018, how many orders would still be late?
-- generate_series builds the 0 to 10 day grid; the cross join tests every order against every buffer.
with o as (
    select actual_days, promised_days
    from mart.fct_orders
    where is_delivered and purchase_date >= date '2018-01-01'
)
select
    b.buffer_days,
    count(*)                                                as orders,
    avg(o.promised_days + b.buffer_days)                    as avg_promised_days,
    sum((o.actual_days > o.promised_days + b.buffer_days)::int)  as late_orders,
    avg((o.actual_days > o.promised_days + b.buffer_days)::int)  as late_rate
from o
cross join (select unnest(generate_series(0, 10)) as buffer_days) b
group by b.buffer_days
order by b.buffer_days;
