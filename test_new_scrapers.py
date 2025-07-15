#!/usr/bin/env python3
"""
Test script for the new cryptocurrency scrapers.

This script tests each new scraper individually to ensure they work correctly.
"""

import sys
import os
import logging
from datetime import datetime

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.coindesk import CoinDeskScraper
from scrapers.coingecko import CoinGeckoScraper
from scrapers.cryptoslate import CryptoSlateScraper
from scrapers.coinmarketcap import CoinMarketCapScraper
from scrapers.cryptopanic import CryptoPanicScraper
from scrapers.alternative_me import AlternativeMeScraper

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_scraper(scraper_class, name, *args, **kwargs):
    """Test a scraper and return results."""
    logger.info(f"Testing {name}...")
    
    try:
        scraper = scraper_class()
        data = scraper.scrape(*args, **kwargs)
        
        if data and 'error' not in data:
            logger.info(f"✓ {name} - Success!")
            logger.info(f"  Data keys: {list(data.keys())}")
            return True
        else:
            logger.warning(f"✗ {name} - Failed or returned error")
            if 'error' in data:
                logger.warning(f"  Error: {data['error']}")
            return False
    
    except Exception as e:
        logger.error(f"✗ {name} - Exception: {e}")
        return False

def main():
    """Run tests for all new scrapers."""
    logger.info("Starting cryptocurrency scraper tests...")
    logger.info("=" * 60)
    
    results = {}
    
    # Test CoinDesk
    results['CoinDesk'] = test_scraper(
        CoinDeskScraper, 
        "CoinDesk", 
        cryptocurrencies=['BTC'], 
        include_news=True, 
        max_articles=5
    )
    
    # Test CoinGecko
    results['CoinGecko'] = test_scraper(
        CoinGeckoScraper, 
        "CoinGecko", 
        cryptocurrencies=['BTC', 'ETH'], 
        include_market_data=True, 
        include_trending=False
    )
    
    # Test CryptoSlate
    results['CryptoSlate'] = test_scraper(
        CryptoSlateScraper, 
        "CryptoSlate", 
        include_news=True, 
        include_market_data=True, 
        max_articles=5
    )
    
    # Test CoinMarketCap (may fail due to anti-bot measures)
    results['CoinMarketCap'] = test_scraper(
        CoinMarketCapScraper, 
        "CoinMarketCap", 
        cryptocurrencies=['BTC', 'ETH'], 
        max_coins=10
    )
    
    # Test CryptoPanic (without API key)
    results['CryptoPanic'] = test_scraper(
        CryptoPanicScraper, 
        "CryptoPanic", 
        cryptocurrencies=['BTC'], 
        kind='news', 
        filter_sentiment=None, 
        max_posts=5
    )
    
    # Test Alternative.me
    results['Alternative.me'] = test_scraper(
        AlternativeMeScraper, 
        "Alternative.me", 
        days=7, 
        include_historical=True
    )
    
    # Summary
    logger.info("=" * 60)
    logger.info("Test Results Summary:")
    
    successful = 0
    total = len(results)
    
    for scraper, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"  {scraper:<15} {status}")
        if success:
            successful += 1
    
    logger.info(f"\nOverall: {successful}/{total} scrapers working correctly")
    
    if successful == total:
        logger.info("🎉 All scrapers are working!")
    elif successful > 0:
        logger.info(f"⚠️  {total - successful} scrapers need attention")
    else:
        logger.error("❌ No scrapers are working - check network connection and dependencies")
    
    return successful == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
