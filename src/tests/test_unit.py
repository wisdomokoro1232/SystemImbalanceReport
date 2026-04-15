"""Unit tests for the reporting pipeline.

"""

from __future__ import annotations

from datetime import datetime
import sys
from pathlib import Path
import pandas as pd
import pytest
import responses

# ---------------------------------------------------------------------------
# Path bootstrap — must happen before any local imports
# ---------------------------------------------------------------------------
_SRC_DIR = str(Path(__file__).parent.parent)
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)
    
from api_client import APIClient
from data_processing import DataProcessor
from generate_report import build_summary_table_html, build_visual_card_html
from imbalance_summary import (
    _exclude_missing_rows,
    build_missing_period_note_html,
    generate_imbalance_summary,
)
from imbalance_visualisation import ImbalanceVisualisation

SETTLEMENT_DATE = "2026-04-10"


# ---------------------------------------------------------------------------
# Settlement period → datetime mapping
# ---------------------------------------------------------------------------


class TestSettlementPeriodMapping:
    """DataProcessor._settlement_period_to_datetime maps periods to the correct
    cross-day datetimes: period 1 = T-1 23:00, period 48 = T 22:30."""

    def test_period_1_is_previous_day_2300(self):
        assert DataProcessor._settlement_period_to_datetime(1, SETTLEMENT_DATE) == datetime(2026, 4, 9, 23, 0)

    def test_period_2_is_previous_day_2330(self):
        assert DataProcessor._settlement_period_to_datetime(2, SETTLEMENT_DATE) == datetime(2026, 4, 9, 23, 30)

    def test_period_48_is_final_period_of_day(self):
        assert DataProcessor._settlement_period_to_datetime(48, SETTLEMENT_DATE) == datetime(2026, 4, 10, 22, 30)

    def test_output_is_a_datetime(self):
        result = DataProcessor._settlement_period_to_datetime(1, SETTLEMENT_DATE)
        assert isinstance(result, datetime)

    def test_consecutive_periods_are_30_minutes_apart(self):
        t1 = DataProcessor._settlement_period_to_datetime(10, SETTLEMENT_DATE)
        t2 = DataProcessor._settlement_period_to_datetime(11, SETTLEMENT_DATE)
        assert (t2 - t1).seconds == 1800


# ---------------------------------------------------------------------------
# Missing row exclusion
# ---------------------------------------------------------------------------


class TestExcludeMissingRows:
    def test_rows_flagged_as_missing_are_removed(self, df_with_missing):
        result = _exclude_missing_rows(df_with_missing)
        assert not result["missingData"].any()
        assert len(result) == 46

    def test_clean_dataframe_is_returned_unchanged(self, clean_df):
        result = _exclude_missing_rows(clean_df)
        assert len(result) == len(clean_df)

    def test_no_missingdata_column_returns_full_dataframe(self):
        df = pd.DataFrame({"value": [1, 2, 3]})
        result = _exclude_missing_rows(df)
        assert list(result["value"]) == [1, 2, 3]

    def test_returns_independent_copy(self, clean_df):
        result = _exclude_missing_rows(clean_df)
        result.iloc[0, result.columns.get_loc("systemSellPrice")] = 999.0
        assert clean_df.iloc[0]["systemSellPrice"] != 999.0

    def test_empty_dataframe_returns_empty(self):
        df = pd.DataFrame({"missingData": pd.Series([], dtype=bool)})
        assert len(_exclude_missing_rows(df)) == 0


# ---------------------------------------------------------------------------
# Summary metric calculations
# ---------------------------------------------------------------------------


class TestGenerateImbalanceSummary:
    """Protects the two required daily metrics: total cost and unit rate."""

    def test_returns_exactly_two_rows(self, clean_df):
        assert len(generate_imbalance_summary(clean_df)) == 2

    def test_total_cost_calculation(self, clean_df):
        """Total cost = sum(abs(NIV) * price).

        For clean_df: NIV[p] = (p-24)*5, price = 95.
        sum(abs(p-24) for p=1..48) = 576, so cost = 576 * 5 * 95 = 273 600.
        """
        summary = generate_imbalance_summary(clean_df)
        cost = float(summary.iloc[0]["Value"].replace(",", ""))
        assert cost == pytest.approx(273_600.0, rel=1e-6)

    def test_unit_rate_calculation(self, clean_df):
        """Unit rate = total cost / sum(abs(NIV))."""
        summary = generate_imbalance_summary(clean_df)
        rate = float(summary.iloc[1]["Value"].replace(",", ""))
        assert rate == pytest.approx(95.0, rel=1e-6)

    def test_missing_rows_are_excluded_from_cost(self, df_with_missing):
        """Imputed zero rows (missingData=True) must not affect the cost total."""
        mask = df_with_missing["missingData"].astype(bool)
        expected = generate_imbalance_summary(df_with_missing[~mask])
        actual = generate_imbalance_summary(df_with_missing)
        assert actual.iloc[0]["Value"] == expected.iloc[0]["Value"]

    def test_zero_total_volume_yields_zero_unit_rate_not_error(self):
        """Edge case: all NIV = 0 must not raise ZeroDivisionError."""
        df = pd.DataFrame(
            {
                "systemSellPrice": [100.0, 100.0],
                "systemBuyPrice": [100.0, 100.0],
                "netImbalanceVolume": [0.0, 0.0],
                "missingData": [False, False],
            },
            index=pd.to_datetime(["2026-04-10 00:00", "2026-04-10 00:30"]),
        )
        df.index.name = "settlementPeriod"
        summary = generate_imbalance_summary(df)
        unit_rate = float(summary.iloc[1]["Value"].replace(",", ""))
        assert unit_rate == pytest.approx(0.0, abs=1e-9)

    def test_all_missing_rows_yields_zero_metrics(self):
        """All periods imputed → clean_df is empty → both metrics are 0."""
        df = pd.DataFrame(
            {
                "systemSellPrice": [0.0],
                "systemBuyPrice": [0.0],
                "netImbalanceVolume": [0.0],
                "missingData": [True],
            },
            index=pd.to_datetime(["2026-04-10 00:00"]),
        )
        df.index.name = "settlementPeriod"
        summary = generate_imbalance_summary(df)
        cost = float(summary.iloc[0]["Value"].replace(",", ""))
        rate = float(summary.iloc[1]["Value"].replace(",", ""))
        assert cost == pytest.approx(0.0, abs=1e-9)
        assert rate == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# Missing period HTML note
# ---------------------------------------------------------------------------


class TestBuildMissingPeriodNoteHtml:
    def test_no_missing_periods_shows_safe_message(self, clean_df):
        note = build_missing_period_note_html(clean_df)
        assert "No missing" in note
        assert "missing-note-warning" not in note

    def test_with_missing_periods_adds_warning_class(self, df_with_missing):
        note = build_missing_period_note_html(df_with_missing)
        assert "missing-note-warning" in note

    def test_missing_missingdata_column_returns_fallback_not_exception(self):
        df = pd.DataFrame({"value": [1, 2]})
        note = build_missing_period_note_html(df)
        assert "missing-note" in note


# ---------------------------------------------------------------------------
# APIClient validation
# ---------------------------------------------------------------------------


class TestAPIClientValidation:
    def test_unsupported_format_raises_value_error(self):
        client = APIClient()
        with pytest.raises(ValueError, match="Invalid format"):
            client.fetch_indicative_imbalance_settlement(format="xlsx", settlement_date=SETTLEMENT_DATE)

    def test_malformed_date_raises_value_error(self):
        client = APIClient()
        with pytest.raises(ValueError, match="Invalid date format"):
            client.fetch_indicative_imbalance_settlement(format="json", settlement_date="10-04-2026")

    @responses.activate
    def test_empty_api_response_raises_value_error(self):
        client = APIClient()
        settlement_date_str = "2026-04-10"
        url = f"{client.base_url}{settlement_date_str}?format=json"

        responses.add(responses.GET, url, json={"data": []}, status=200)

        with pytest.raises(ValueError, match=f"Empty API response: no records returned for settlement date {settlement_date_str}."):
            client.fetch_indicative_imbalance_settlement(format="json", settlement_date=settlement_date_str)

    @responses.activate
    def test_valid_response_returns_data(self):
        client = APIClient()
        settlement_date_str = "2026-04-10"
        url = f"{client.base_url}{settlement_date_str}?format=json"
        mock_data = {"data": [{"settlementPeriod": 1, "systemSellPrice": 100.0, "systemBuyPrice": 100.0, "netImbalanceVolume": 10.0}]}

        responses.add(responses.GET, url, json=mock_data, status=200)

        response = client.fetch_indicative_imbalance_settlement(format="json", settlement_date=settlement_date_str)
        assert response.status_code == 200
        assert response.json() == mock_data

    @responses.activate
    def test_retry_on_server_error(self):
        client = APIClient()
        settlement_date_str = "2026-04-10"
        url = f"{client.base_url}{settlement_date_str}?format=json"
        
        # Add responses in order
        responses.add(responses.GET, url, status=500)
        responses.add(responses.GET, url, status=502)
        responses.add(responses.GET, url, status=503)
        responses.add(
            responses.GET, url,
            json={
                "data": [
                    {
                        "settlementPeriod": 1,
                        "systemSellPrice": 100.0,
                        "systemBuyPrice": 100.0,
                        "netImbalanceVolume": 10.0,
                    }
                ]
            },
            status=200
        )
        
        response = client.fetch_indicative_imbalance_settlement(format="json", settlement_date=settlement_date_str)
        assert response.status_code == 200  