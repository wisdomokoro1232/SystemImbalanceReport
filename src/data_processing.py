from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta
from typing import Tuple
from logging_config import logger 
import pandas as pd


class DataProcessor:
    def __init__(self, api_client):
        self.api_client = api_client

    @staticmethod
    def _settlement_period_to_datetime(period: int, settlement_date: str) -> datetime:
        """Map period 1-48 to datetimes from previous day 23:00 to settlement day 22:30."""
        base_date = datetime.strptime(settlement_date, "%Y-%m-%d")
        start_dt = (base_date - timedelta(days=1)).replace(hour=23, minute=0, second=0, microsecond=0)
        logger.debug(f"Mapping settlement period {period} to datetime starting from {start_dt}")
        return start_dt + timedelta(minutes=(period - 1) * 30)

    def process_data(
        self,
        output_format=None,
        settlement_date=None,
        additional_columns=None,
        output_dir: str | Path | None = None,
    ) -> Tuple[pd.DataFrame, str]:
        """Fetch, clean, and align raw API data into a half-hourly time series.

        Returns
        -------
        (df, csv_path) : tuple[pd.DataFrame, str]
            The cleaned DataFrame (with a DatetimeIndex named 'settlementPeriod')
            and the path to the exported CSV file.
        """
        settlement_date_str = settlement_date if settlement_date else self.api_client.get_settlement_date()
        response = self.api_client.fetch_indicative_imbalance_settlement(
            format=output_format,
            settlement_date=settlement_date_str,
        )
        data = response.json()['data']
        if not data:
            raise ValueError(
                f"Empty API response: no records returned for settlement date {settlement_date_str}."
            )
        df = pd.DataFrame(data)

        # Filter columns
        columns_to_keep = ['settlementPeriod', 'systemSellPrice', 'systemBuyPrice', 'netImbalanceVolume']
        if additional_columns:
            columns_to_keep.extend(additional_columns)
        df = df[columns_to_keep]

        # Add missing data indicator
        df['missingData'] = df.isnull().any(axis=1)
        logger.debug(f"Added missing data indicator. Missing data rows: {df['missingData'].sum()}")

        # Convert data types
        df['settlementPeriod'] = df['settlementPeriod'].astype(int)
        df['systemSellPrice'] = df['systemSellPrice'].astype(float)
        df['systemBuyPrice'] = df['systemBuyPrice'].astype(float)
        df['netImbalanceVolume'] = df['netImbalanceVolume'].astype(float)

        # Remove duplicates
        df.drop_duplicates(inplace=True)

        # Inject missing periods as zero with missing flag
        all_periods = set(range(1, 49))
        existing_periods = set(df['settlementPeriod'])
        missing_periods = all_periods - existing_periods

        if missing_periods:
            missing_rows = pd.DataFrame(
                [
                    {
                        'settlementPeriod': period,
                        'systemSellPrice': 0.0,
                        'systemBuyPrice': 0.0,
                        'netImbalanceVolume': 0.0,
                        'missingData': True,
                    }
                    for period in sorted(missing_periods)
                ]
            )
            df = pd.concat([df, missing_rows], ignore_index=True)
            logger.debug(f"Injected missing periods as zero with missing flag. Missing periods: {sorted(missing_periods)}")
        df = df.sort_values('settlementPeriod').reset_index(drop=True)

        # Convert integer periods to proper datetime objects
        df['settlementPeriod'] = df['settlementPeriod'].astype(int).apply(
            lambda period: self._settlement_period_to_datetime(period, settlement_date_str)
        )
        df['settlementPeriod'] = pd.to_datetime(df['settlementPeriod'])
        df = df.set_index('settlementPeriod')

        # Export CSV
        if output_dir is None:
            output_dir = Path(__file__).parent / "output"
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        csv_file = output_path / f"indicative_imbalance_settlement_{settlement_date_str}.csv"
        df.to_csv(csv_file)
        logger.info(f"Processed data for settlement date {settlement_date_str} and exported to {csv_file}")
        return df, str(csv_file)