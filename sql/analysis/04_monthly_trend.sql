-- 04 Monthly trend: what Olist promised, what it delivered, and how often it was late.
-- 2016 has under 300 delivered orders, so the trend starts in Jan 2017. Aug 2018 is the last full month.
select
    purchase_month,
    count(*)                         as delivered_orders,
    sum(is_late::int)                as late_orders,
    avg(is_late::int)                as late_rate,
    avg(promised_days)               as avg_promised_days,
    avg(actual_days)                 as avg_actual_days,
    avg(review_score)                as avg_review,
    avg(missed_ship_by::int)         as missed_ship_by_rate
from mart.fct_orders
where is_delivered
  and purchase_month between date '2017-01-01' and date '2018-08-01'
group by purchase_month
order by purchase_month;
