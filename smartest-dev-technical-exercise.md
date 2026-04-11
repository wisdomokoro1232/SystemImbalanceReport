# Associate Trading Developer — Technical Exercise

The objective of this task is to demonstrate how you would deliver a typical trading-developer task end-to-end.  
The problem is deliberately open so we can assess your structure, assumptions, and engineering judgement.

---

## What we evaluate
- **Defensibility:** be prepared to explain your design decisions in the interview  
- **Production readiness:** validation/error handling, sensible logging, tests encouraged  
- **Maintainability:** easy to read/extend, short README/usage guide + documented assumptions  
- **Code quality:** clean structure, clear naming, docstrings/comments, reusable patterns where sensible  
- **Scalability:** brief note on how you’d extend it (more data/features/complexity) without a rewrite  

---

## Submission format
- Submit a **Git repository link** containing your solution.
- You may deliver the solution as either:
  - a **Python package / script**, or  
  - a **Jupyter Notebook**  
- In all cases, the solution should run end-to-end from a clean environment using the instructions in your README.

---

## Guidelines
- Use Git and commit regularly. Share a link to the final repository.
- Include a README covering:
  - setup and execution steps
  - how to run tests (if included)
  - key assumptions and trade-offs
- Maintain consistent, clean style throughout.
- Ensure your code runs without errors. If tests are included, they should run and pass.
- Use publicly available libraries only, and justify any non-standard dependencies.
- If you don’t have time to complete everything, clearly document what you would do next (and why).

---

## Requirements

### Context

We need a **daily report** of system imbalance price and cost for the **previous settlement day**, to support a trader’s **post-trade analysis**.  
The report should be generated using data collected from the **Elexon Insights (BMRS) API**.

Traders analyze system imbalances—often referred to as Fair Value Gaps (FVGs), inefficient pricing, or order imbalances—to identify areas where market supply and demand are not in equilibrium, suggesting future price movements and potential trading opportunities. These imbalances occur when large institutional buying or selling creates rapid price moves, leaving behind an "open" price range that the market tends to revisit to fill, making them crucial for predicting pullbacks and optimal trade entries.

- **Documentation:** https://bmrs.elexon.co.uk/api-documentation/introduction
- **Endpoint:** https://bmrs.elexon.co.uk/api-documentation/endpoint/balancing/settlement/system-prices/%7BsettlementDate%7D
<!-- Insert two column table -->
|                     | Imbalance price positive | Imbalance price negative| 
| -------  | ------- | -------| 
| Positive imbalance  | Payment from TSO to BRP  | Payment from BRP to TSO | 
| Negative imbalance  |Payment from BRP to TSO   | Payment from TSO to BRP |  


---
### Deliverables
1. **API client**
   - Implement a small, reusable API caller for:
     - BMRS Imbalance Prices (System Prices)
     - Indicated Imbalance Volumes (IIV)
   - Handle common production concerns (timeouts, retries/backoff, basic validation, helpful errors).

2. **Data cleaning + time series**
   - Clean and align the raw data into half-hourly time series for the settlement date:
     - prices: `systemBuyPrice` and `systemSellPrice`
     - volumes: `netImbalanceVolume` (or the appropriate IIV field if separate)
   - Ensure the index is correct for settlement periods (typically 48) and handle missing/duplicate periods sensibly.

System buy price usually equals system sell price
Since November 2015 (modification P305), the UK has used a single imbalance pricing mechanism. This means the System Buy Price (SBP) and System Sell Price (SSP) are equal in each settlement period. Both parties with energy deficits and those with energy surpluses are charged or paid at the same price.


3. **Daily summary metrics + visualisation**
   - Calculate and output:
     - **Total daily imbalance cost** (clearly define your methodology)
     - **Daily imbalance unit rate** (clearly define; e.g. cost / absolute volume, or another sensible definition)
   - Generate **at least one visualisation** that would enhance a trader’s post-trade analysis (justify briefly why you chose it).

What is Volume Imbalance?
Volume imbalance refers to a situation where there is a significant difference between the buying and selling volumes in the market. In other words, it measures the disparity between demand (buyers) and supply (sellers). This imbalance can indicate potential market moves, as a higher buying volume could signal bullish sentiment, while a higher selling volume might indicate bearish sentiment.


Net Imbalance Volume (NIV): The net volume of energy actions (bids and offers) taken by the System Operator to balance the system in a given settlement period (usually 30 minutes).
Short System: NIV is positive (demand > generation).
Long System: NIV is negative (generation > demand)

Traders want to see the sign of the settlement operiod because this can signal when was best to buy (Long system) vs sell (short system)?

What is Price Imbalance?

Price imbalance, on the other hand, occurs when there is a disparity between the current market price and its fair value or equilibrium price. This imbalance can be caused by various factors such as news events, economic data releases, or sudden shifts in market sentiment. Price imbalance often leads to increased volatility as the market attempts to correct itself and return to equilibrium.

Why would we monitor these post trade?

Evaluating Execution Quality : Post-trade analysis helps traders determine if they paid too much for a trade due to liquidity voids. By reviewing if a trade was executed during an extreme imbalance, they can assess if the market maker or algorithm provided the best possible price, or if the trade suffered from high implementation shortfall.

Understanding Market Sentiment and Direction: Imbalances are interpreted as a signal of aggressive buying or selling activity. Post-trade analysis allows traders to confirm if the imbalance was a real shift in market sentiment or just "noise" (a false breakout), which helps in predicting future price direction.

Identifying Future Support and Resistance Levels: Areas of significant imbalance often represent "thin" liquidity where price can move rapidly. By marking these areas, traders can identify high-probability zones where the market is likely to return in the future to "fill" the imbalance (i.e., return to equilibrium).

Refining Trading Strategies and Habits: Post-trade review (such as "Walk-A-Away" analysis) helps traders see if they are entering or exiting positions prematurely due to panic or in response to temporary imbalance, allowing them to improve their discipline and profitability.

Managing Institutional Risk: Large institutional traders analyze imbalances to see how their meta-orders (large, split-up orders) have influenced the market, helping them understand if their own activity created temporary price volatility

Visualise: 1. Show when it is a long system and by how much 2. Show the prices during these periods - maybe better to voerlay these two together? 

As a result visualisation definitely should not estimate imbalance volumes or prices where missing as this can lead to wrong conclusions, aslo due to teh volatility of these values it is unreliable to use the last known value or an average

4. **Developer best practices**
   - Include a small suite of **unit tests** to protect the codebase from accidental modification and regressions.
   - Tests should cover core logic (data parsing/cleaning, calculations, edge cases) and help ensure robustness to common errors (e.g. missing periods, empty API responses, unexpected values).
