-- 08 Which seller metrics are habits? For sellers with 30+ delivered orders in both 2017 and 2018,
-- compare each seller's 2017 rate with their own 2018 rate. A metric that repeats is fair to score sellers on.
with s as (
    select
        seller_id,
        year(purchase_date)                 as yr,
        count(*)                            as orders,
        avg(is_late::int)                   as late_rate,
        avg(missed_ship_by::int)            as missed_ship_by_rate
    from mart.fct_orders
    where is_delivered and seller_id is not null and handed_to_carrier_at is not null
      and year(purchase_date) in (2017, 2018)
    group by seller_id, yr
)
select
    a.seller_id,
    a.orders                as orders_2017,
    b.orders                as orders_2018,
    a.late_rate             as late_rate_2017,
    b.late_rate             as late_rate_2018,
    a.missed_ship_by_rate   as missed_ship_by_2017,
    b.missed_ship_by_rate   as missed_ship_by_2018
from s a
join s b on a.seller_id = b.seller_id and a.yr = 2017 and b.yr = 2018
where a.orders >= 30 and b.orders >= 30
order by a.orders + b.orders desc;
