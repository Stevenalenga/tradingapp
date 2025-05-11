"""
Scrapers package for the Trading Information Scraper application.

This package contains modules for scraping financial data from various sources:
- Yahoo Finance: Stock prices, trading volume, market cap, etc.
- CNBC: Financial news, market summaries, etc.
- CoinTelegraph: Cryptocurrency prices, news, etc.
"""

from .yahoo_finance import YahooFinanceScraper
from .cnbc import CNBCScraper
from .cointelegraph import CoinTelegraphScraper

__all__ = ['YahooFinanceScraper', 'CNBCScraper', 'CoinTelegraphScraper']