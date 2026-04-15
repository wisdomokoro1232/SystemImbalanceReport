"""Shared fixtures for the SystemImbalanceReport test suite.

Adds ``/src/`` to ``sys.path`` so every test file can import
production modules by their plain name (``from api_client import …``),
regardless of whether pytest is launched from ``SystemImbalanceReport/`` or a parent folder.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib
# Force non-interactive backend before any test imports matplotlib via production code.
matplotlib.use("Agg")

import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Path bootstrap — must happen before any local imports
# ---------------------------------------------------------------------------
_SRC_DIR = str(Path(__file__).parent.parent)
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

# ---------------------------------------------------------------------------
# Constants shared across test modules
# ---------------------------------------------------------------------------
SETTLEMENT_DATE = "2026-04-10"
PRICE = 95.0


# ---------------------------------------------------------------------------
# Helper — not a fixture, safe to import directly
# ---------------------------------------------------------------------------

def period_to_dt_str(period: int, settlement_date: str = SETTLEMENT_DATE) -> str:
    """Reference implementation of the settlement period → datetime mapping.

    Period 1 = T-1 23:00, Period 48 = T 22:30.
    Intentionally duplicates the production logic so test fixtures have an
    independent baseline; if the two diverge a test will catch it.
    """
    base = datetime.strptime(settlement_date, "%Y-%m-%d")
    start = (base - timedelta(days=1)).replace(hour=23, minute=0, second=0, microsecond=0)
    return (start + timedelta(minutes=(period - 1) * 30)).strftime("%Y-%m-%d %H:%M")


def build_raw_api_records(periods: list[int] | None = None) -> list[dict]:
    """Return fake API-style record dicts for *periods* (default: 1-48)."""
    if periods is None:
        periods = list(range(1, 49))
    return [
        {
            "settlementPeriod": p,
            "systemSellPrice": PRICE,
            "systemBuyPrice": PRICE,
            "netImbalanceVolume": float((p - 24) * 5),
        }
        for p in periods
    ]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def api_response_full() -> dict:
    """Full 48-period raw API response dict."""
    return {"data": build_raw_api_records()}


@pytest.fixture
def api_response_missing_periods() -> dict:
    """46-period API response — periods 3 and 25 are absent."""
    return {"data": build_raw_api_records([p for p in range(1, 49) if p not in (3, 25)])}


@pytest.fixture
def clean_df() -> pd.DataFrame:
    """Fully-processed 48-period DataFrame with DatetimeIndex; no imputed rows."""
    rows = [
        {
            "systemSellPrice": PRICE,
            "systemBuyPrice": PRICE,
            "netImbalanceVolume": float((p - 24) * 5),
            "missingData": False,
        }
        for p in range(1, 49)
    ]
    df = pd.DataFrame(rows)
    df.index = pd.to_datetime([period_to_dt_str(p) for p in range(1, 49)])
    df.index.name = "settlementPeriod"
    return df


@pytest.fixture
def df_with_missing(clean_df: pd.DataFrame) -> pd.DataFrame:
    """DataFrame where periods 3 and 25 (0-based indices 2 and 24) are imputed."""
    df = clean_df.copy()
    for idx in (2, 24):
        df.iloc[idx, df.columns.get_loc("missingData")] = True
        for col in ("systemSellPrice", "systemBuyPrice", "netImbalanceVolume"):
            df.iloc[idx, df.columns.get_loc(col)] = 0.0
    return df
