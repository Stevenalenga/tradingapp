# Cryptocurrency Market Analysis

This folder contains HTML files that provide analysis of various cryptocurrencies, including:

- Bitcoin (BTC)
- Ethereum (ETH)
- XRP
- Solana (SOL)
- Other notable cryptocurrencies (SHIB, WIF, PEPE, BONK, DOGE, TAU)

## Files

- `index.html` - Main overview page with summary of all cryptocurrencies
- `btc.html` - Detailed analysis of Bitcoin
- `eth.html` - Detailed analysis of Ethereum
- `xrp.html` - Detailed analysis of XRP
- `sol.html` - Detailed analysis of Solana
- `update_crypto_analysis.py` - Python script to automatically update the analysis with latest data

## How to Use

### Viewing the Analysis

Simply open the `index.html` file in a web browser to view the cryptocurrency market analysis. From there, you can navigate to individual cryptocurrency pages for more detailed information.

### Updating the Analysis

The analysis can be automatically updated with the latest data by running the update script:

```bash
python update_crypto_analysis.py
```

This script will:
1. Find the latest cryptocurrency data CSV files in the `../data` directory
2. Extract relevant news and price information
3. Update all HTML files with the latest data
4. Update the generation date in all files

## Requirements for the Update Script

- Python 3.6+
- BeautifulSoup4 (`pip install beautifulsoup4`)

## Data Sources

The analysis is based on data from:
- CoinTelegraph news articles
- Market performance data
- Trading information

The data is automatically collected by the main trading application and stored in CSV files in the `../data` directory.