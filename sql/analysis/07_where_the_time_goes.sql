-- 07 Where the time goes: seller side (purchase to carrier handoff) vs carrier side (handoff to doorstep).
select
    case when is_late then 'Late' else 'On time' end    as outcome,
    count(*)                                            as orders,
    avg(seller_days)                                    as avg_seller_days,
    avg(carrier_days)                                   as avg_carrier_days,
    avg(actual_days)                                    as avg_total_days,
    avg(missed_ship_by::int)                            as missed_ship_by_rate
from mart.fct_orders
where is_delivered and handed_to_carrier_at is not null and seller_id is not null
  and carrier_days >= 0
group by 1
order by 1 desc;
