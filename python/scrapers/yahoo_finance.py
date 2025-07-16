"""
Yahoo Finance scraper module for the Trading Information Scraper application.

This module provides functionality for scraping financial data from Yahoo Finance.
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Union

import pandas as pd
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class YahooFinanceScraper(BaseScraper):
    """
    Scraper for Yahoo Finance.
    
    This class provides methods for scraping stock data from Yahoo Finance,
    including current prices, historical data, and company information.
    """
    
    BASE_URL = "https://finance.yahoo.com"
    QUOTE_URL = BASE_URL + "/quote/{symbol}"
    HISTORICAL_URL = BASE_URL + "/quote/{symbol}/history"
    
    def __init__(self, **kwargs):
        """Initialize the Yahoo Finance scraper with base scraper parameters."""
        super().__init__(**kwargs)
    
    def scrape(self, symbols: List[str], data_points: Optional[List[str]] = None) -> Dict[str, Dict]:
        """
        Scrape data for multiple symbols.
        
        Args:
            symbols: List of stock symbols to scrape
            data_points: List of data points to include (default: all)
            
        Returns:
            Dictionary mapping symbols to their data
        """
        data_points = data_points or [
            "price", "change", "change_percent", "volume", 
            "market_cap", "pe_ratio", "dividend_yield"
        ]
        
        result = {}
        for symbol in symbols:
            try:
                logger.info(f"Scraping data for {symbol}")
                result[symbol] = self.scrape_symbol(symbol, data_points)
            except Exception as e:
                logger.error(f"Error scraping {symbol}: {e}")
                result[symbol] = {"error": str(e)}
        
        return result
    
    def scrape_symbol(self, symbol: str, data_points: List[str]) -> Dict:
        """
        Scrape data for a single symbol.
        
        Args:
            symbol: Stock symbol to scrape
            data_points: List of data points to include
            
        Returns:
            Dictionary with the scraped data
        """
        url = self.QUOTE_URL.format(symbol=symbol)
        soup = self.get_html(url)
        
        result = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat()
        }
        
        # Extract data based on requested data points
        if "price" in data_points:
            result["price"] = self._extract_price(soup)
        
        if "change" in data_points or "change_percent" in data_points:
            change, change_percent = self._extract_change(soup)
            if "change" in data_points:
                result["change"] = change
            if "change_percent" in data_points:
                result["change_percent"] = change_percent
        
        if "volume" in data_points:
            result["volume"] = self._extract_volume(soup)
        
        if "market_cap" in data_points:
            result["market_cap"] = self._extract_market_cap(soup)
        
        if "pe_ratio" in data_points:
            result["pe_ratio"] = self._extract_pe_ratio(soup)
        
        if "dividend_yield" in data_points:
            result["dividend_yield"] = self._extract_dividend_yield(soup)
        
        return result
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Get historical data for a symbol.
        
        Args:
            symbol: Stock symbol
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            DataFrame with historical data
        """
        # Convert dates to Unix timestamps
        start_timestamp = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        end_timestamp = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
        
        # Yahoo Finance uses a different URL for historical data with query parameters
        url = f"{self.BASE_URL}/quote/{symbol}/history?period1={start_timestamp}&period2={end_timestamp}&interval=1d"
        
        soup = self.get_html(url)
        
        # Extract data from the table
        data = []
        table = soup.find('table', {'data-test': 'historical-prices'})
        
        if not table:
            logger.warning(f"No historical data found for {symbol}")
            return pd.DataFrame()
        
        rows = table.find_all('tr')
        for row in rows[1:]:  # Skip header row
            cols = row.find_all('td')
            if len(cols) >= 6:  # Ensure we have enough columns
                date_str = cols[0].text.strip()
                try:
                    date = datetime.strptime(date_str, "%b %d, %Y")
                    open_price = self._parse_value(cols[1].text)
                    high_price = self._parse_value(cols[2].text)
                    low_price = self._parse_value(cols[3].text)
                    close_price = self._parse_value(cols[4].text)
                    adj_close = self._parse_value(cols[5].text)
                    volume = self._parse_value(cols[6].text)
                    
                    data.append({
                        'date': date,
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'close': close_price,
                        'adj_close': adj_close,
                        'volume': volume
                    })
                except (ValueError, IndexError) as e:
                    logger.debug(f"Error parsing row: {e}")
        
        return pd.DataFrame(data)
    
    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract the current price from the soup."""
        try:
            price_element = soup.find('fin-streamer', {'data-field': 'regularMarketPrice'})
            if price_element:
                return float(price_element.text.replace(',', ''))
        except (ValueError, AttributeError) as e:
            logger.debug(f"Error extracting price: {e}")
        return None
    
    def _extract_change(self, soup: BeautifulSoup) -> tuple:
        """Extract the price change and change percentage from the soup."""
        try:
            change_element = soup.find('fin-streamer', {'data-field': 'regularMarketChange'})
            change_percent_element = soup.find('fin-streamer', {'data-field': 'regularMarketChangePercent'})
            
            change = float(change_element.text.replace(',', '')) if change_element else None
            
            if change_percent_element:
                change_percent_text = change_percent_element.text.strip('()')
                change_percent = float(change_percent_text.rstrip('%')) / 100
            else:
                change_percent = None
                
            return change, change_percent
        except (ValueError, AttributeError) as e:
            logger.debug(f"Error extracting change: {e}")
        return None, None
    
    def _extract_volume(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract the trading volume from the soup."""
        try:
            volume_row = soup.find('td', text=re.compile('Volume'))
            if volume_row:
                volume_value = volume_row.find_next_sibling('td')
                if volume_value:
                    return self._parse_value(volume_value.text)
        except (ValueError, AttributeError) as e:
            logger.debug(f"Error extracting volume: {e}")
        return None
    
    def _extract_market_cap(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract the market cap from the soup."""
        try:
            market_cap_row = soup.find('td', text=re.compile('Market Cap'))
            if market_cap_row:
                market_cap_value = market_cap_row.find_next_sibling('td')
                if market_cap_value:
                    return self._parse_value(market_cap_value.text)
        except (ValueError, AttributeError) as e:
            logger.debug(f"Error extracting market cap: {e}")
        return None
    
    def _extract_pe_ratio(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract the P/E ratio from the soup."""
        try:
            pe_row = soup.find('td', text=re.compile('PE Ratio'))
            if pe_row:
                pe_value = pe_row.find_next_sibling('td')
                if pe_value:
                    return float(pe_value.text.replace(',', ''))
        except (ValueError, AttributeError) as e:
            logger.debug(f"Error extracting P/E ratio: {e}")
        return None
    
    def _extract_dividend_yield(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract the dividend yield from the soup."""
        try:
            dividend_row = soup.find('td', text=re.compile('Forward Dividend & Yield'))
            if dividend_row:
                dividend_value = dividend_row.find_next_sibling('td')
                if dividend_value and '(' in dividend_value.text and ')' in dividend_value.text:
                    yield_text = dividend_value.text.split('(')[1].split(')')[0]
                    return float(yield_text.rstrip('%')) / 100
        except (ValueError, AttributeError, IndexError) as e:
            logger.debug(f"Error extracting dividend yield: {e}")
        return None
    
    @staticmethod
    def _parse_value(value_text: str) -> Optional[Union[int, float]]:
        """
        Parse a value from text, handling suffixes like K, M, B, T.
        
        Args:
            value_text: Text value to parse
            
        Returns:
            Parsed numeric value
        """
        if not value_text or value_text.strip() == 'N/A':
            return None
            
        value_text = value_text.strip().replace(',', '')
        
        # Handle suffixes
        multipliers = {
            'K': 1_000,
            'M': 1_000_000,
            'B': 1_000_000_000,
            'T': 1_000_000_000_000
        }
        
        for suffix, multiplier in multipliers.items():
            if value_text.endswith(suffix):
                try:
                    return float(value_text[:-1]) * multiplier
                except ValueError:
                    return None
        
        # No suffix, try to convert directly
        try:
            if '.' in value_text:
                return float(value_text)
            else:
                return int(value_text)
        except ValueError:
            return None