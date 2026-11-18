-- 02 Review score by how early or late the order arrived versus the promised date.
-- This is the "cliff": scores hold steady while early, then drop the day the promise breaks.
with b as (
    select
        review_score,
        case
            when days_vs_promise <= -15 then 1
            when days_vs_promise <= -8  then 2
            when days_vs_promise <= -1  then 3
            when days_vs_promise = 0    then 4
            when days_vs_promise <= 3   then 5
            when days_vs_promise <= 7   then 6
            when days_vs_promise <= 14  then 7
            else 8
        end as bucket_order
    from mart.fct_orders
    where is_delivered and review_score is not null
)
select
    bucket_order,
    case bucket_order
        when 1 then '15+ days early' when 2 then '8-14 days early' when 3 then '1-7 days early'
        when 4 then 'On the day'     when 5 then '1-3 days late'   when 6 then '4-7 days late'
        when 7 then '8-14 days late' else '15+ days late'
    end                                 as arrival_vs_promise,
    bucket_order >= 5                   as is_late,
    count(*)                            as orders,
    avg(review_score)                   as avg_review,
    avg((review_score = 1)::int)        as one_star_rate,
    avg((review_score >= 4)::int)       as four_plus_rate
from b
group by bucket_order
order by bucket_order;
