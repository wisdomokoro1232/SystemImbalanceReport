import pandas as pd
import numpy as np
import requests
import datetime


# Step 1: Configure the API endpoint and parameters
class APIClient:
    # Initialization method sets up base default url and headers for API requests
    def __init__(self, base_url=None):
        self.base_url = base_url or "https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/system-prices/"
        self.formats = ['json', 'csv', 'xml']  # Supported formats

    @staticmethod
    def get_settlement_date():
        # Get yesterday's date
        settlement_date = datetime.datetime.today() - datetime.timedelta(days=1)
        return settlement_date.strftime('%Y-%m-%d')

    def fetch_indicative_imbalance_settlement(self, format = None, settlement_date = None):
        if settlement_date is None:
            settlement_date = self.get_settlement_date()  # Get yesterday's date
        else:
            try:
                settlement_date = datetime.datetime.strptime(settlement_date, '%Y-%m-%d').strftime('%Y-%m-%d')
            except ValueError:
                raise ValueError("Invalid date format. Please use 'YYYY-MM-DD'.")

        if format != None and format not in self.formats:
            raise ValueError(f"Invalid format. Supported formats are: {self.formats}")
        try:
            response = requests.get(f"{self.base_url}{settlement_date}?format={format}", timeout=10)
            response.raise_for_status()  # Raise an error for HTTP errors
            return response
        except requests.RequestException as e:
            raise SystemExit(e)


