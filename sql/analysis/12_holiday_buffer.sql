-- 12 Holiday buffer what-if. The 2017 holiday rush (Black Friday week, Nov 20, through Dec 31)
-- is on the calendar every year. What if Olist had added b days to promises only in that window?
with o as (
    select actual_days, promised_days,
           purchase_date between date '2017-11-20' and date '2017-12-31' as in_window
    from mart.fct_orders
    where is_delivered and purchase_date between date '2017-01-01' and date '2017-12-31'
)
select
    b.buffer_days,
    count(*) filter (where in_window)                                                       as window_orders,
    avg((actual_days > promised_days + b.buffer_days)::int) filter (where in_window)        as window_late_rate,
    sum((actual_days > promised_days + b.buffer_days)::int) filter (where in_window)        as window_late_orders,
    avg((actual_days > promised_days)::int) filter (where not in_window)                    as rest_of_2017_late_rate,
    avg(case when in_window then promised_days + b.buffer_days else promised_days end)      as avg_promised_days_2017
from o
cross join (select unnest([0, 3, 5, 7, 10]) as buffer_days) b
group by b.buffer_days
order by b.buffer_days;
