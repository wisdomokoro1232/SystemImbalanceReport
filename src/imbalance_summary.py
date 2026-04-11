from __future__ import annotations

import html
import pandas as pd


def _exclude_missing_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Return rows that are not marked as missing."""
    if "missingData" not in df.columns:
        return df.copy()
    return df.loc[~df["missingData"].fillna(False)].copy()


def generate_imbalance_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create daily summary metrics, excluding rows with missingData=True."""
    clean_df = _exclude_missing_rows(df)

    interval_cost = clean_df["netImbalanceVolume"] * clean_df["systemSellPrice"] 
    total_daily_cost = float(interval_cost.sum())
    total_absolute_volume = float(clean_df["netImbalanceVolume"].abs().sum())
    unit_rate = total_daily_cost / total_absolute_volume if total_absolute_volume else 0.0

    summary_rows = [
        {
            "Metric": "Total daily imbalance cost",
            "Value": f"{total_daily_cost:,.2f}",
            "Methodology": "Calculated on reported (non-missing) periods only: sum(netImbalanceVolume * systemSellPrice).",
        },
        {
            "Metric": "Daily imbalance unit rate",
            "Value": f"{unit_rate:,.4f}",
            "Methodology": "Calculated on reported (non-missing) periods only: total daily imbalance cost / sum(abs(netImbalanceVolume)).",
        },
    ]

    return pd.DataFrame(summary_rows)


