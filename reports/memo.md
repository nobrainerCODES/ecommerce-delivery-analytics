# Memo: Fix the broken promise, not the slow delivery

**To:** Head of Marketplace Operations, Olist
**From:** Shraman Pandey
**Data:** 96,470 delivered orders, Sept 2016 to Aug 2018

## The problem

Late orders were only 6.8% of deliveries, but they drew **37% of all 1-star reviews**. Bad reviews hurt the sellers on the platform and the marketplace's reputation.

## What I found

1. **Customers grade the promise, not the wait.** At the same delivery time, a late order scored 1.38 stars lower. An extra day of waiting, while still on time, cost only 0.03 stars. Orders that took 20 to 29 days scored 4.00 when on time and 2.63 when late.
2. **Lateness comes in waves.** Nov 2017, Feb 2018 and Mar 2018 held 48% of all late orders. The holiday rush alone ran 12% late, versus 4% for the rest of 2017.
3. **Most of the delay is with the carrier, but sellers add to it.** Late orders spent about 28 days with the carrier, versus 8 days for on-time orders. When a seller missed the ship-by deadline (9% of orders), the order was late 21% of the time, versus 5% otherwise.
4. **Missing the ship-by deadline is a seller habit. Being late is not.** For 172 sellers active in both years, the ship-by miss rate repeated (r = 0.55) while the late rate barely did (r = 0.23).

## Recommendations

| Action | Expected impact (2-year data) | Effort |
|---|---|---|
| **1. Seller scorecard on the ship-by deadline.** Warn sellers who miss it often, then lower their search placement. | 811 fewer late orders (12%), about 380 fewer 1-star reviews | Low. The data already exists |
| **2. Holiday buffer.** Add 5 days to the promise from Black Friday week to Dec 31. | 450 fewer late orders in the 2017 rush (40% of that window's late orders). 30% more efficient than the same cost spread over the year | Low. One rule change |
| **3. Choose the everyday buffer on purpose.** Each extra promised day cuts the late rate by about 0.7 points. A new route-based formula did not beat the current estimate in a backtest. | Leadership picks a target late rate and accepts the trade-off | Low |

Together, actions 1 and 2 would have prevented about **1,223 late orders (19%)** and about **570 one-star reviews**.

## What I would not do

- **Do not rank sellers by late rate.** It mostly reflects carrier delays and luck, so it would punish the wrong sellers.
- **Do not count on fixing lateness to win back repeat buyers.** After controls, a late first order did not measurably change repeat buying (p = 0.28). Repeat buying is rare for everyone (2% within 180 days).

## Next steps

1. Pilot the scorecard with the 10% of sellers who miss the deadline most often.
2. A/B test proactive "your order is running late" messages with a new date. If customers grade the promise, resetting it early should protect the review.
3. Measure checkout conversion against promise length. This data cannot show what a longer promise costs in lost sales.

*Method details, SQL and code: see the [README](../README.md).*
