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
3. **Daily summary metrics + visualisation**
   - Calculate and output:
     - **Total daily imbalance cost** (clearly define your methodology)
     - **Daily imbalance unit rate** (clearly define; e.g. cost / absolute volume, or another sensible definition)
   - Generate **at least one visualisation** that would enhance a trader’s post-trade analysis (justify briefly why you chose it).

Net Imbalance Volume (NIV): The net volume of energy actions (bids and offers) taken by the System Operator to balance the system in a given settlement period (usually 30 minutes).
Short System: NIV is positive (demand > generation).
Long System: NIV is negative (generation > demand)


Traders want to see the sign of the settlement operiod because this can signal when is best to buy (Long system) vs sell (short system)

Visualise: 1. Show when it is a long system and by how much 2. Show the prices during these periods - maybe better to voerlay these two together? 

4. **Developer best practices**
   - Include a small suite of **unit tests** to protect the codebase from accidental modification and regressions.
   - Tests should cover core logic (data parsing/cleaning, calculations, edge cases) and help ensure robustness to common errors (e.g. missing periods, empty API responses, unexpected values).
