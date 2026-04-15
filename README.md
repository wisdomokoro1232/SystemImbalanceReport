# Daily System Imbalance Report

A daily report generator for system imbalance price and volume data from the [Elexon BMRS API](https://bmrs.elexon.co.uk/api-documentation), designed to support a trader's post-trade analysis.

The tool fetches settlement system prices for a given day, cleans and aligns the data into a half-hourly time series, calculates daily summary metrics, and produces a styled HTML + PDF report with an embedded chart.

---

## Quick start (recommended for traders)

From the repository root:

```powershell
.\install.ps1
.\run_report.ps1
```

This performs full setup once (venv + dependencies + Playwright Chromium) and then generates the daily report in one line.

If you get an error similar to the following: 
#### " .venv\Scripts\Activate.ps1 cannot be loaded  because running scripts is disabled on this system ...'

Run the command below before the quick start commands:
```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

---

## Manual setup

### 1. Create a virtual environment

```bash
python -m venv .venv
```

### 2. Activate it

```powershell
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt   # includes pytest
```

### 4. Install Playwright's Chromium browser (required for PDF export)

```bash
playwright install chromium
```

---

## Running the report

From the repository root (`SystemImbalanceReport/`):

```bash
python src/imbalance_report.py
```

Or on Windows (recommended after quick start setup):

```powershell
.\run_report.ps1
```

This fetches yesterday's settlement data by default, generates the report, and opens it in your browser.

To generate a report for a specific date:

```python
# In a Python shell / script
from src.imbalance_report import build_imbalance_report

build_imbalance_report(settlement_date="2026-04-10")
```

Output files are written to `src/output/`:

| File | Description |
|------|-------------|
| `imbalance_report_YYYY-MM-DD.html` | Styled HTML report |
| `imbalance_report_YYYY-MM-DD.pdf`  | PDF snapshot (A4, via Playwright Chromium) |
| `indicative_imbalance_settlement_YYYY-MM-DD.csv` | Raw time-series data export |
| `assets/combined_volume_price.png` | Chart image embedded in the report |

---

## Running the tests

From the repository root (`SystemImbalanceReport/`):

```bash
python -m pytest
```

`pytest.ini` is pre-configured so no extra flags are needed. The suite runs the tests in ~2 seconds with no network access required.

| File | Scope | What it covers |
|------|-------|----------------|
| `src/tests/test_unit.py` | Unit (no I/O) | Settlement period mapping, metric calculations, HTML escaping, label logic, input validation |
| `src/tests/conftest.py` | Fixtures | Shared DataFrames, fake API responses, matplotlib backend override |

---

## Project structure

```
SystemImbalanceReport/
├── README.md
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt
├── logs # Location for persisted logging
└── src/
    ├── api_client.py              # Reusable Elexon BMRS API client
    ├── data_processing.py         # Fetch, clean, align half-hourly time series
    ├── imbalance_summary.py       # Daily cost & unit rate metrics
    ├── imbalance_visualisation.py # Combined NIV bar + price overlay chart
    ├── generate_report.py         # HTML rendering & Playwright PDF export
    ├── imbalance_report.py        # Main entrypoint — orchestrates the pipeline
    ├── main/
    │   └── report_template.html   # HTML template with CSS variables
    ├── output/                    # Generated reports (git-ignored)
    └── tests/
        ├── conftest.py
        └── test_unit.py
```

---

## Key assumptions and trade-offs

- **Single imbalance price**: Since P305 (Nov 2015), `systemBuyPrice == systemSellPrice`. The report uses `systemSellPrice` as the single price, with `systemBuyPrice` retained in the data for completeness.
- **Missing periods**: Any of the 48 half-hourly periods absent from the API response are injected as zero-value rows with a `missingData` flag. These are excluded from metric calculations and visually flagged on the chart, because estimating volatile imbalance values would mislead traders.
- **Settlement period timing**: Period 1 maps to T-1 23:00 and Period 48 maps to T 22:30, following the GB electricity settlement day convention.
- **PDF rendering**: Uses Playwright (Chromium) rather than `xhtml2pdf` for full CSS fidelity (CSS variables, grid layout, modern styling).
- **Purpose of Total Imbalance Cost**: To identify the cost of balancing the system irrespective of direction - can signal whether some days experienced more volatility/unexpected pressures on demand and supply side. Can help refine trading strategy for next day where total imbalance costs were high.
- **Purpose of Daily Imbalance Unit rate**: Average cost of balancing actions shows traders the average price paid in/out per unit of energy. This can help traders in quantifying risk for future contracting based on the amount their assets could be imbalancing the system by. 
- **Purpose of NIV Analysis**: Understand Market Sentiment and  Direction, Identify Patterns, Refine Trade strategies amd Habits, Manage Institutional Risk and . With the first three reasons in mind the visualisation was produced to indicate both long/short systems as well as corresponding price changes. Traders can better anticipate when the grid will be "short" (shortage) or "long" (surplus) to position their assets to benefit from higher imbalance prices. It also helps with the fourth where traders can align their orders with market movements to identify correlation.

---

## Extending the project

- **More data sources**: The `APIClient` class can be extended with additional methods for other BMRS endpoints (e.g. BOD, PHYBM) without changing the downstream pipeline.
- **Multiple settlement days**: `process_data()` and `build_imbalance_report()` accept a `settlement_date` parameter — batch runs can loop over a date range.
- **Additional metrics**: New metrics can be added to `generate_imbalance_summary()` by appending rows to the summary DataFrame. The HTML template and tests will pick them up automatically.
- **Scheduling**: The CLI entrypoint (`imbalance_report.py`) can be wrapped in a cron job or Windows Task Scheduler for automated daily generation.
- **Integration Tests**: Due to lack of understanding of the integration tests framework in python they were not implemented but they are essential for any production ready project.