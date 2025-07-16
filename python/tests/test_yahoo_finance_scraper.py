"""
Test module for the Yahoo Finance scraper.

This module contains tests for the Yahoo Finance scraper functionality.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the application modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scrapers.yahoo_finance import YahooFinanceScraper


class TestYahooFinanceScraper(unittest.TestCase):
    """Test cases for the Yahoo Finance scraper."""
    
    def setUp(self):
        """Set up the test environment."""
        self.scraper = YahooFinanceScraper()
    
    def tearDown(self):
        """Clean up after the tests."""
        pass
    
    @patch('scrapers.yahoo_finance.YahooFinanceScraper.get_html')
    def test_scrape_symbol(self, mock_get_html):
        """Test scraping a single symbol."""
        # Create a mock BeautifulSoup object
        mock_soup = MagicMock()
        
        # Mock the _extract methods to return test values
        self.scraper._extract_price = MagicMock(return_value=150.25)
        self.scraper._extract_change = MagicMock(return_value=(2.5, 0.0169))
        self.scraper._extract_volume = MagicMock(return_value=1000000)
        self.scraper._extract_market_cap = MagicMock(return_value=2000000000)
        self.scraper._extract_pe_ratio = MagicMock(return_value=25.5)
        self.scraper._extract_dividend_yield = MagicMock(return_value=0.015)
        
        # Set the return value for get_html
        mock_get_html.return_value = mock_soup
        
        # Call the method being tested
        result = self.scraper.scrape_symbol('AAPL', ['price', 'change', 'change_percent', 'volume', 'market_cap', 'pe_ratio', 'dividend_yield'])
        
        # Verify the result
        self.assertEqual(result['symbol'], 'AAPL')
        self.assertEqual(result['price'], 150.25)
        self.assertEqual(result['change'], 2.5)
        self.assertEqual(result['change_percent'], 0.0169)
        self.assertEqual(result['volume'], 1000000)
        self.assertEqual(result['market_cap'], 2000000000)
        self.assertEqual(result['pe_ratio'], 25.5)
        self.assertEqual(result['dividend_yield'], 0.015)
        
        # Verify that get_html was called with the correct URL
        mock_get_html.assert_called_once_with(self.scraper.QUOTE_URL.format(symbol='AAPL'))
    
    @patch('scrapers.yahoo_finance.YahooFinanceScraper.scrape_symbol')
    def test_scrape_multiple_symbols(self, mock_scrape_symbol):
        """Test scraping multiple symbols."""
        # Set up the mock to return different values for different symbols
        def side_effect(symbol, data_points):
            if symbol == 'AAPL':
                return {'symbol': 'AAPL', 'price': 150.25}
            elif symbol == 'MSFT':
                return {'symbol': 'MSFT', 'price': 250.75}
            else:
                return {'symbol': symbol, 'error': 'Symbol not found'}
        
        mock_scrape_symbol.side_effect = side_effect
        
        # Call the method being tested
        result = self.scraper.scrape(['AAPL', 'MSFT', 'UNKNOWN'], ['price'])
        
        # Verify the result
        self.assertEqual(len(result), 3)
        self.assertEqual(result['AAPL']['price'], 150.25)
        self.assertEqual(result['MSFT']['price'], 250.75)
        self.assertIn('error', result['UNKNOWN'])
        
        # Verify that scrape_symbol was called for each symbol
        self.assertEqual(mock_scrape_symbol.call_count, 3)
    
    def test_parse_value(self):
        """Test parsing values with different formats."""
        # Test parsing regular numbers
        self.assertEqual(self.scraper._parse_value('123'), 123)
        self.assertEqual(self.scraper._parse_value('123.45'), 123.45)
        
        # Test parsing values with commas
        self.assertEqual(self.scraper._parse_value('1,234'), 1234)
        self.assertEqual(self.scraper._parse_value('1,234.56'), 1234.56)
        
        # Test parsing values with suffixes
        self.assertEqual(self.scraper._parse_value('1.2K'), 1200)
        self.assertEqual(self.scraper._parse_value('1.5M'), 1500000)
        self.assertEqual(self.scraper._parse_value('2.5B'), 2500000000)
        self.assertEqual(self.scraper._parse_value('3.7T'), 3700000000000)
        
        # Test parsing invalid values
        self.assertIsNone(self.scraper._parse_value('N/A'))
        self.assertIsNone(self.scraper._parse_value(''))
        self.assertIsNone(self.scraper._parse_value(None))


if __name__ == '__main__':
    unittest.main()