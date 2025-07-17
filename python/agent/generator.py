import pandas as pd
import numpy as np
from datetime import timedelta
from sklearn.linear_model import LinearRegression

class TradingSignalGenerator:
    def __init__(self, data: pd.DataFrame):
        """
        Expected DataFrame columns:
        - 'date' (datetime)
        - 'coin' (e.g. BTC, ETH)
        - 'price'
        """
        self.data = data

    def forecast_prices(self, coin: str, days_ahead: int = 3):
        df = self.data[self.data['coin'] == coin].copy()
        df = df.sort_values(by='date')

        df['day_index'] = np.arange(len(df))
        X = df[['day_index']]
        y = df['price']

        model = LinearRegression()
        model.fit(X, y)

        future_days = np.arange(len(df), len(df) + days_ahead).reshape(-1, 1)
        future_prices = model.predict(future_days)

        return pd.DataFrame({
            'date': [df['date'].max() + timedelta(days=i+1) for i in range(days_ahead)],
            'coin': coin,
            'forecast_price': future_prices
        })

    def generate_signals(self, coin: str, threshold_pct: float = 5.0):
        df = self.data[self.data['coin'] == coin].copy()
        if df.empty:
            return None

        current_price = df.sort_values('date').iloc[-1]['price']
        forecast = self.forecast_prices(coin, days_ahead=3)
        max_forecast = forecast['forecast_price'].max()
        min_forecast = forecast['forecast_price'].min()

        take_profit = current_price + (threshold_pct / 100) * current_price
        stop_loss = current_price - (threshold_pct / 100) * current_price

        return {
            'coin': coin,
            'current_price': current_price,
            'forecast': forecast.to_dict(orient='records'),
            'take_profit': round(take_profit, 3),
            'stop_loss': round(stop_loss, 3)
        }

    def generate_all_signals(self):
        coins = self.data['coin'].unique()
        signals = []
        for coin in coins:
            signal = self.generate_signals(coin)
            if signal:
                signals.append(signal)
        return signals
