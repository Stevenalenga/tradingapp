import pandas as pd
from datetime import datetime
import numpy as np

# Sample thresholds per asset (can be made dynamic later)
RISK_PARAMS = {
    "BTC": {"sl_pct": 0.05, "tp_pct": 0.08},
    "SOL": {"sl_pct": 0.06, "tp_pct": 0.10},
    "WIF": {"sl_pct": 0.12, "tp_pct": 0.25},
    "XRP": {"sl_pct": 0.07, "tp_pct": 0.15},
    "BONK": {"sl_pct": 0.15, "tp_pct": 0.30},
    "BNB": {"sl_pct": 0.04, "tp_pct": 0.06}
}

def generate_trade_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Given a DataFrame with columns ['symbol', 'timestamp', 'price', 'forecast'],
    returns a DataFrame with stop-loss and take-profit recommendations.
    """
    results = []
    for symbol in df['symbol'].unique():
        asset_df = df[df['symbol'] == symbol].copy()
        asset_df.sort_values(by="timestamp", inplace=True)

        latest = asset_df.iloc[-1]
        price = latest["price"]
        forecast = latest.get("forecast", price)  # default to price if no forecast
        params = RISK_PARAMS.get(symbol.upper(), {"sl_pct": 0.05, "tp_pct": 0.10})

        stop_loss = round(price * (1 - params["sl_pct"]), 4)
        take_profit = round(price * (1 + params["tp_pct"]), 4)

        trend = "Bullish" if forecast > price else "Bearish"

        results.append({
            "symbol": symbol,
            "price": price,
            "forecast": forecast,
            "trend": trend,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "timestamp": datetime.utcnow().isoformat()
        })

    return pd.DataFrame(results)


if __name__ == "__main__":
    # Example usage (load historical/scraped data)
    df = pd.read_csv("data/latest_prices.csv")  # Contains columns: symbol, timestamp, price, forecast
    signals = generate_trade_signals(df)
    signals.to_json("outputs/signals.json", orient="records", indent=2)
    print(signals)
