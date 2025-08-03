# Trading Information Scraper

A comprehensive Python application that scrapes trading and cryptocurrency information from multiple sources including Yahoo Finance, CNBC, CoinTelegraph, CoinDesk, CoinGecko, CryptoSlate, CoinMarketCap, CryptoPanic, and Alternative.me.

## Overview

This application provides a comprehensive solution for collecting, processing, storing, and visualizing financial data from multiple sources. It is designed to be modular, extensible, and configurable to meet various financial data collection needs.

### Key Features

- **Multi-source Data Collection**: Scrape data from 9 different financial and cryptocurrency sources
- **Comprehensive Crypto Coverage**: Access market data, news, sentiment analysis, and Fear & Greed Index
- **API Integration**: Use official APIs where available (CoinGecko, CryptoPanic, Alternative.me)
- **Flexible Data Processing**: Clean, normalize, and transform data from different sources
- **Multiple Storage Options**: Store data in CSV, SQLite, or JSON formats
- **Data Visualization**: Generate charts and graphs for data analysis
- **Scheduled Execution**: Automate data collection at configurable intervals
- **Robust Error Handling**: Gracefully handle network issues, rate limiting, and site changes
- **Coin Prices CSV Updater**: One-shot CLI to fetch and append CoinGecko USD prices for configured coins

## Supported Data Sources

### Stock Market Data
- **Yahoo Finance**: Stock prices, trading volume, market cap, PE ratios

### News Sources
- **CNBC**: Financial news and market analysis
- **CoinTelegraph**: Cryptocurrency news and market insights
- **CoinDesk**: Bitcoin and cryptocurrency news with official API integration
- **CryptoSlate**: Crypto news and market insights

### Cryptocurrency Market Data
- **CoinGecko**: Comprehensive crypto market data via free API (30 calls/min)
- **CoinMarketCap**: Crypto prices and market data (HTML scraping)
- **CryptoPanic**: Crypto news aggregation with sentiment analysis (API available)

### Market Sentiment
- **Alternative.me**: Crypto Fear & Greed Index with historical data and trend analysis

## Project Structure

```
tradingapp/
├── scrapers/         # Web scraping modules for different sources
├── processors/       # Data processing and transformation modules
├── storage/          # Data storage modules for different formats
├── visualization/    # Data visualization modules
├── utils/            # Utility functions and helpers
├── tests/            # Test modules and fixtures
├── docs/             # Documentation
├── scheduler.py      # Scheduling functionality
├── main.py           # Main application entry point
├── requirements.txt  # Project dependencies
└── README.md         # This file
```

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/tradingapp.git
cd tradingapp

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
# Run with default settings (includes Yahoo Finance, CNBC, CoinTelegraph)
python main.py

# Enable specific cryptocurrency sources
python main.py --sources coingecko,alternative_me --output csv

# Schedule daily execution with multiple crypto sources
python main.py --schedule daily
```

## Configuration

The application uses a YAML configuration file (`config.yaml`) to control which sources are enabled and their parameters:

```yaml
sources:
  # Enable/disable CoinGecko API (free, 30 calls/min)
  coingecko:
    enabled: true
    cryptocurrencies:
      - BTC
      - ETH
      - XRP
      - ADA
      - BNB
      - LTC
      - LINK
    include_market_data: true
    include_trending: false
storage:
  path: ./data
  type: csv
```

## CLI Help

Show available options and flags:
```bash
python -m python.main --help
```

## Update Coin Prices CSV (CoinGecko)

Fetch current USD prices for all coins declared in `sources.coingecko.cryptocurrencies` and append them to a CSV for downstream analysis.

Command:
```bash
python -m python.main --update-coin-prices --coin-prices-file coin_prices.csv
```

Behavior:
- Reads coins from config at `sources.coingecko.cryptocurrencies`
- Queries CoinGecko `/simple/price` in a single batched request
- Appends rows to `<storage.path>/coin_prices.csv` (default file name), creating it if missing
- CSV columns: `timestamp,symbol,coingecko_id,price_usd`

Notes:
- Only common symbols covered by the built-in static map are resolved:
  BTC, ETH, XRP, ADA, SOL, DOT, MATIC, AVAX, LINK, UNI, LTC, BCH, ALGO, ATOM, VET
- To add support for more symbols, extend the static map in [`python/scrapers/coingecko.py`](python/scrapers/coingecko.py:37).

## Documentation

For detailed documentation, please refer to:

- [User Guide](docs/README.md): Comprehensive usage documentation
- [Project Plan](project_plan.md): Detailed project architecture and implementation plan
- [Test Plan](tests/test_plan.md): Testing strategy and test cases

## Development

### Setting Up Development Environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Check code style
flake8 tradingapp

# Format code
black tradingapp
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.