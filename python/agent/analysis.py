# ai_agent/analysis_engine.py

import pandas as pd

def analyze_trends(data: pd.DataFrame, coin: str, risk_level='medium'):
    """
    Analyze the coin price trend and suggest take-profit and stop-loss points.

    Args:
        data (pd.DataFrame): DataFrame with 'price' and 'forecast' columns
        coin (str): Coin symbol e.g., 'BTC', 'XRP'
        risk_level (str): Risk preference - 'low', 'medium', or 'high'

    Returns:
        dict: Strategy with stop_loss and take_profit
    """
    if coin not in data.columns:
        raise ValueError(f"{coin} data not found in input DataFrame")

    price_now = data[coin].iloc[-1]
    forecast = data[f"{coin}_forecast"].iloc[-1]

    # Risk-adjusted factors
    risk_multipliers = {
        'low': 0.01,
        'medium': 0.03,
        'high': 0.05
    }
    multiplier = risk_multipliers.get(risk_level, 0.03)

    stop_loss = round(price_now * (1 - multiplier), 4)
    take_profit = round(price_now * (1 + multiplier), 4)

    return {
        'coin': coin,
        'current_price': price_now,
        'forecast_price': forecast,
        'stop_loss': stop_loss,
        'take_profit': take_profit,
        'risk_level': risk_level
    }
