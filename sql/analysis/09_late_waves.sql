-- 09 Late orders come in waves. Rank months by late orders and show the running share.
with m as (
    select purchase_month, count(*) as orders, sum(is_late::int) as late_orders
    from mart.fct_orders
    where is_delivered
    group by purchase_month
)
select
    purchase_month,
    orders,
    late_orders,
    late_orders * 1.0 / orders                                             as late_rate,
    rank() over (order by late_orders desc)                                as late_rank,
    sum(late_orders) over (order by late_orders desc rows unbounded preceding)
        * 1.0 / sum(late_orders) over ()                                   as cumulative_share_of_late
from m
order by late_rank;
