# Data

`raw/` holds the [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), gzipped but otherwise unchanged. Olist released it on Kaggle under **CC BY-NC-SA 4.0** (attribution, non-commercial, share-alike). Thanks to Olist for making it public.

| File | Rows | What it is |
|---|---:|---|
| olist_orders_dataset | 99,441 | One row per order: status, purchase time, carrier handoff, delivery, promised date |
| olist_customers_dataset | 99,441 | Customer for each order. `customer_unique_id` is the real person |
| olist_order_items_dataset | 112,650 | Items in each order: product, seller, price, freight, ship-by deadline |
| olist_order_payments_dataset | 103,886 | Payments per order |
| olist_order_reviews_dataset | 99,224 | Review score (1 to 5) and comments |
| olist_products_dataset | 32,951 | Product category and size |
| olist_sellers_dataset | 3,095 | Seller location |
| product_category_name_translation | 71 | Portuguese to English category names |

The 1M-row geolocation file is left out because this analysis does not need it.

## Data quality notes
- 547 orders have more than one review. The warehouse keeps the latest answer per order.
- 1.3% of orders have items from more than one seller. Seller-level analysis uses single-seller orders only.
- 23 delivered orders show the carrier pickup after the delivery, and 160 show pickup before the purchase. They stay in the order counts but are left out of the seller vs carrier time split.
- The promised date has no time of day, so "late" is measured in calendar days: delivered on a later day than promised.
