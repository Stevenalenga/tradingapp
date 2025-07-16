"""
Scrapers package for the Trading Information Scraper application.

This package contains modules for scraping financial data from various sources:
- Yahoo Finance: Stock prices, trading volume, market cap, etc.
- CNBC: Financial news, market summaries, etc.
- CoinTelegraph: Cryptocurrency prices, news, etc.
- CoinDesk: Cryptocurrency news and Bitcoin price data
- CoinGecko: Cryptocurrency market data via API
- CryptoSlate: Cryptocurrency news and insights
- CoinMarketCap: Cryptocurrency prices and market data
- CryptoPanic: Cryptocurrency news aggregation with sentiment
- Alternative.me: Crypto Fear & Greed Index
"""

from .yahoo_finance import YahooFinanceScraper
from .cnbc import CNBCScraper
from .cointelegraph import CoinTelegraphScraper
from .coindesk import CoinDeskScraper
from .coingecko import CoinGeckoScraper
from .cryptoslate import CryptoSlateScraper
from .coinmarketcap import CoinMarketCapScraper
from .cryptopanic import CryptoPanicScraper
from .alternative_me import AlternativeMeScraper

__all__ = [
    'YahooFinanceScraper', 
    'CNBCScraper', 
    'CoinTelegraphScraper',
    'CoinDeskScraper',
    'CoinGeckoScraper',
    'CryptoSlateScraper',
    'CoinMarketCapScraper',
    'CryptoPanicScraper',
    'AlternativeMeScraper'
]