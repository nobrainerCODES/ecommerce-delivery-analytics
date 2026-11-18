"""Data quality checks on the warehouse. If the raw data or the SQL changes in a way that breaks
an assumption the analysis relies on, these fail."""


def one(con, sql):
    return con.execute(sql).fetchone()[0]


def test_fact_table_has_one_row_per_order(con):
    assert one(con, "select count(*) from mart.fct_orders") == one(con, "select count(*) from staging.orders")
    assert one(con, "select count(*) - count(distinct order_id) from mart.fct_orders") == 0


def test_one_review_per_order_after_dedupe(con):
    assert one(con, "select count(*) - count(distinct order_id) from staging.reviews") == 0
    assert one(con, "select count(*) from staging.reviews where review_score not between 1 and 5") == 0


def test_every_order_has_a_customer(con):
    assert one(con, "select count(*) from mart.fct_orders where customer_unique_id is null") == 0


def test_delivered_orders_have_dates(con):
    assert one(con, """select count(*) from mart.fct_orders
                       where is_delivered and (delivered_at is null or promised_date is null)""") == 0
    assert one(con, "select count(*) from mart.fct_orders where is_delivered and actual_days < 0") == 0
    assert one(con, "select count(*) from mart.fct_orders where is_delivered and promised_days <= 0") == 0


def test_late_flag_matches_days_vs_promise(con):
    assert one(con, """select count(*) from mart.fct_orders
                       where is_delivered and is_late <> (days_vs_promise > 0)""") == 0


def test_single_seller_orders_have_seller_state(con):
    assert one(con, "select count(*) from mart.fct_orders where seller_id is not null and seller_state is null") == 0


def test_customer_order_sequence_starts_at_one(con):
    assert one(con, "select min(customer_order_seq) from mart.fct_orders") == 1
    assert one(con, "select count(*) from mart.fct_orders where customer_order_seq = 1") == \
        one(con, "select count(*) from mart.dim_customers")


def test_known_totals_from_the_raw_data(con):
    # Guards against a silent change in the source files or the filters.
    assert one(con, "select count(*) from mart.fct_orders where is_delivered") == 96_470
    assert one(con, "select sum(is_late::int) from mart.fct_orders where is_delivered") == 6_534
