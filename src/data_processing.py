import pandas as pd
from datetime import datetime, timedelta


class DataProcessor:
    def __init__(self, api_client):
        self.api_client = api_client

    @staticmethod
    def _settlement_period_to_datetime(period: int, settlement_date: str) -> str:
        """Map period 1-48 to datetimes from previous day 23:00 to settlement day 22:30."""
        base_date = datetime.strptime(settlement_date, "%Y-%m-%d")
        start_dt = (base_date - timedelta(days=1)).replace(hour=23, minute=0, second=0, microsecond=0)
        period_dt = start_dt + timedelta(minutes=(period - 1) * 30)
        return period_dt.strftime("%Y-%m-%d %H:%M")

    def process_data(self, output_format=None, settlement_date=None, additional_columns=None):
        settlement_date_str = settlement_date if settlement_date else self.api_client.get_settlement_date()
        response = self.api_client.fetch_indicative_imbalance_settlement(
            format=output_format,
            settlement_date=settlement_date_str,
        )
        data = response.json()['data']
        df = pd.DataFrame(data)

        # Filter columns
        columns_to_keep = ['settlementPeriod', 'systemSellPrice', 'systemBuyPrice', 'netImbalanceVolume']
        if additional_columns:
            columns_to_keep.extend(additional_columns)
        df = df[columns_to_keep]

        # Add missing data indicator which checks whether any of the key columns have missing data and sets the flag to True if so, otherwise False
        df['missingData'] = df.isnull().any(axis=1)

        # Convert data types
        df['settlementPeriod'] = df['settlementPeriod'].astype(int)
        df['systemSellPrice'] = df['systemSellPrice'].astype(float)
        df['systemBuyPrice'] = df['systemBuyPrice'].astype(float)
        df['netImbalanceVolume'] = df['netImbalanceVolume'].astype(float)

        # Check for duplicates and remove them
        df.drop_duplicates(inplace=True)

        # Check for missing periods and set them to 0 with missing flag
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

        df = df.sort_values('settlementPeriod').reset_index(drop=True)
        df['settlementPeriod'] = df['settlementPeriod'].astype(int).apply(
            lambda period: self._settlement_period_to_datetime(period, settlement_date_str)
        )

        # Save to CSV
        filename = f"indicative_imbalance_settlement_{settlement_date_str}.csv"
        df.to_csv(filename, index=False)
        return filename