-- 03 Same wait, different promise.
-- Hold the actual delivery time steady and compare orders that beat the promise with orders that missed it.
with b as (
    select
        review_score, is_late,
        case
            when actual_days <= 9  then '1) under 10 days'
            when actual_days <= 14 then '2) 10-14 days'
            when actual_days <= 19 then '3) 15-19 days'
            when actual_days <= 29 then '4) 20-29 days'
            else                        '5) 30+ days'
        end as actual_wait
    from mart.fct_orders
    where is_delivered and review_score is not null
)
select
    actual_wait,
    count(*) filter (where not is_late)                  as on_time_orders,
    count(*) filter (where is_late)                      as late_orders,
    avg(review_score) filter (where not is_late)         as avg_review_on_time,
    avg(review_score) filter (where is_late)             as avg_review_late
from b
group by actual_wait
order by actual_wait;
