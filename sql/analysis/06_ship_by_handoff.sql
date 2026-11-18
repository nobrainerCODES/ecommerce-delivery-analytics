-- 06 Seller handoff. Every order has a ship-by deadline for the seller to hand the package to the carrier.
-- Compare orders where the seller missed it, and estimate how many late orders an on-time handoff would have saved.
-- Counterfactual: move the delivery earlier by the time the seller ran past the deadline, carrier time unchanged.
with o as (
    select
        *,
        case when missed_ship_by
             then cast(delivered_at - (handed_to_carrier_at - ship_by_at) as date)
             else cast(delivered_at as date)
        end as delivered_date_if_on_time_handoff
    from mart.fct_orders
    where is_delivered
      and seller_id is not null              -- single-seller orders (98.7%)
      and handed_to_carrier_at is not null
)
select
    missed_ship_by,
    count(*)                                                        as orders,
    sum(is_late::int)                                               as late_orders,
    avg(is_late::int)                                               as late_rate,
    median(days_past_ship_by) filter (where missed_ship_by)         as median_days_past_deadline,
    sum((delivered_date_if_on_time_handoff > promised_date)::int)   as late_orders_if_on_time_handoff
from o
group by missed_ship_by
order by missed_ship_by;
