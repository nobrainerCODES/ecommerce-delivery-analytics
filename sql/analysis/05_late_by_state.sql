-- 05 Late rate by customer state (Brazil has 26 states plus the Federal District).
select
    customer_state,
    count(*)                    as delivered_orders,
    sum(is_late::int)           as late_orders,
    avg(is_late::int)           as late_rate,
    avg(promised_days)          as avg_promised_days,
    avg(actual_days)            as avg_actual_days,
    avg(review_score)           as avg_review
from mart.fct_orders
where is_delivered
group by customer_state
order by late_rate desc;
