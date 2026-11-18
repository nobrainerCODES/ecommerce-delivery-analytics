-- 01 Headline numbers for delivered orders.
-- Late = delivered on a calendar day after the promised date shown to the customer.
select
    count(*)                                                     as delivered_orders,
    sum(is_late::int)                                            as late_orders,
    avg(is_late::int)                                            as late_rate,
    avg(promised_days)                                           as avg_promised_days,
    avg(actual_days)                                             as avg_actual_days,
    median(promised_days)                                        as median_promised_days,
    median(actual_days)                                          as median_actual_days,
    avg(-days_vs_promise) filter (where not is_late)             as avg_days_early_when_on_time,
    count(review_score)                                          as reviewed_orders,
    avg(review_score)                                            as avg_review,
    avg(review_score) filter (where not is_late)                 as avg_review_on_time,
    avg(review_score) filter (where is_late)                     as avg_review_late,
    avg((review_score = 1)::int) filter (where not is_late)      as one_star_rate_on_time,
    avg((review_score = 1)::int) filter (where is_late)          as one_star_rate_late,
    count(*) filter (where review_score = 1)                     as one_star_reviews,
    count(*) filter (where review_score = 1 and is_late)         as one_star_reviews_from_late,
    count(*) filter (where review_score = 1 and is_late) * 1.0
        / count(*) filter (where review_score = 1)               as share_of_one_stars_from_late,
    sum(items_value)                                             as gmv_brl,
    min(purchase_date)                                           as first_purchase,
    max(purchase_date)                                           as last_purchase
from mart.fct_orders
where is_delivered;
