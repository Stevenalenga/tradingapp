"""
CoinTelegraph scraper module for the Trading Information Scraper application.

This module provides functionality for scraping cryptocurrency data and news from CoinTelegraph.
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Union

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class CoinTelegraphScraper(BaseScraper):
    """
    Scraper for CoinTelegraph.
    
    This class provides methods for scraping cryptocurrency data and news from CoinTelegraph.
    """
    
    BASE_URL = "https://cointelegraph.com"
    PRICE_INDEX_URL = BASE_URL + "/price-index"
    NEWS_URL = BASE_URL + "/tags/{tag}"
    
    def __init__(self, **kwargs):
        """Initialize the CoinTelegraph scraper with base scraper parameters."""
        super().__init__(**kwargs)
    
    def scrape(self, cryptocurrencies: Optional[List[str]] = None, include_news: bool = True) -> Dict:
        """
        Scrape cryptocurrency data and optionally news from CoinTelegraph.
        
        Args:
            cryptocurrencies: List of cryptocurrency symbols to scrape (default: ['BTC', 'ETH', 'XRP', 'LTC', 'BCH'])
            include_news: Whether to include news articles
            
        Returns:
            Dictionary with scraped cryptocurrency data and news
        """
        cryptocurrencies = cryptocurrencies or ['BTC', 'ETH', 'XRP', 'LTC', 'BCH']
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "source": "CoinTelegraph",
            "cryptocurrencies": self.scrape_crypto_prices(cryptocurrencies)
        }
        
        if include_news:
            result["news"] = self.scrape_crypto_news(cryptocurrencies)
        
        return result
    
    def scrape_crypto_prices(self, cryptocurrencies: List[str]) -> Dict[str, Dict]:
        """
        Scrape cryptocurrency price data.
        
        Args:
            cryptocurrencies: List of cryptocurrency symbols to scrape
            
        Returns:
            Dictionary mapping cryptocurrency symbols to their data
        """
        soup = self.get_html(self.PRICE_INDEX_URL)
        
        # CoinTelegraph often loads price data via JavaScript
        # Look for a data script that contains the price information
        price_data = self._extract_price_data_from_script(soup)
        
        if not price_data:
            logger.warning("Could not extract price data from script, falling back to HTML parsing")
            return self._extract_price_data_from_html(soup, cryptocurrencies)
        
        # Filter for requested cryptocurrencies
        result = {}
        for crypto in cryptocurrencies:
            crypto_upper = crypto.upper()
            if crypto_upper in price_data:
                result[crypto_upper] = price_data[crypto_upper]
            else:
                logger.warning(f"Cryptocurrency {crypto_upper} not found in price data")
        
        return result
    
    def scrape_crypto_news(self, tags: Optional[List[str]] = None, max_articles: int = 50) -> Dict:
        """
        Scrape cryptocurrency news articles.
        
        Args:
            tags: List of tags/cryptocurrencies to scrape news for
            max_articles: Maximum number of articles to scrape
            
        Returns:
            Dictionary with scraped news data
        """
        tags = tags or ['bitcoin', 'ethereum', 'ripple', 'litecoin', 'bitcoin-cash']
        
        result = {
            "total": 0,
            "tags": {}
        }
        
        for tag in tags:
            try:
                logger.info(f"Scraping news for tag: {tag}")
                tag_news = self._scrape_tag_news(tag, max_articles // len(tags))
                result["tags"][tag] = tag_news
                result["total"] += tag_news["total"]
            except Exception as e:
                logger.error(f"Error scraping news for tag {tag}: {e}")
                result["tags"][tag] = {"error": str(e)}
        
        return result
    
    def _scrape_tag_news(self, tag: str, max_articles: int) -> Dict:
        """
        Scrape news articles for a specific tag.
        
        Args:
            tag: Tag to scrape news for
            max_articles: Maximum number of articles to scrape
            
        Returns:
            Dictionary with scraped news data for the tag
        """
        url = self.NEWS_URL.format(tag=tag)
        soup = self.get_html(url)
        
        articles = []
        article_count = 0
        
        # Find all article elements
        article_elements = soup.find_all(['article', 'div'], class_=re.compile('post|article|news-item'))
        
        for article_element in article_elements:
            if article_count >= max_articles:
                break
                
            try:
                article_data = self._extract_article_data(article_element)
                if article_data:
                    articles.append(article_data)
                    article_count += 1
            except Exception as e:
                logger.debug(f"Error extracting article data: {e}")
        
        return {
            "total": len(articles),
            "articles": articles
        }
    
    def _extract_price_data_from_script(self, soup: BeautifulSoup) -> Dict:
        """
        Extract cryptocurrency price data from script tags.
        
        Args:
            soup: BeautifulSoup object with the parsed HTML
            
        Returns:
            Dictionary with cryptocurrency price data
        """
        # Look for script tags that might contain price data
        script_tags = soup.find_all('script')
        
        for script in script_tags:
            script_content = script.string
            if not script_content:
                continue
                
            # Look for JSON data in the script
            try:
                # Find JSON-like structures in the script
                json_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', script_content, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(1))
                    
                    # Navigate through the data structure to find price information
                    if 'priceIndex' in data and 'data' in data['priceIndex']:
                        price_data = {}
                        
                        for crypto in data['priceIndex']['data']:
                            symbol = crypto.get('symbol', '').upper()
                            if not symbol:
                                continue
                                
                            price_data[symbol] = {
                                "name": crypto.get('name'),
                                "symbol": symbol,
                                "price": self._parse_value(crypto.get('price', {}).get('value')),
                                "market_cap": self._parse_value(crypto.get('marketCap', {}).get('value')),
                                "volume_24h": self._parse_value(crypto.get('volume24h', {}).get('value')),
                                "change_24h": self._parse_percent(crypto.get('change24h', {}).get('value')),
                                "change_7d": self._parse_percent(crypto.get('change7d', {}).get('value')),
                                "last_updated": crypto.get('lastUpdated')
                            }
                        
                        return price_data
            except (json.JSONDecodeError, AttributeError) as e:
                logger.debug(f"Error parsing JSON from script: {e}")
        
        return {}
    
    def _extract_price_data_from_html(self, soup: BeautifulSoup, cryptocurrencies: List[str]) -> Dict[str, Dict]:
        """
        Extract cryptocurrency price data from HTML elements.
        
        Args:
            soup: BeautifulSoup object with the parsed HTML
            cryptocurrencies: List of cryptocurrency symbols to extract
            
        Returns:
            Dictionary mapping cryptocurrency symbols to their data
        """
        result = {}
        
        # Find the price table
        price_table = soup.find('table', class_=re.compile('price-table|coin-table'))
        
        if not price_table:
            logger.warning("Price table not found in HTML")
            return result
            
        # Find all rows in the table
        rows = price_table.find_all('tr')
        
        for row in rows[1:]:  # Skip header row
            try:
                # Extract symbol
                symbol_element = row.find(['td', 'div'], class_=re.compile('symbol|coin-symbol'))
                if not symbol_element:
                    continue
                    
                symbol = symbol_element.text.strip().upper()
                
                # Check if this cryptocurrency is in the requested list
                if symbol not in [c.upper() for c in cryptocurrencies]:
                    continue
                    
                # Extract name
                name_element = row.find(['td', 'div'], class_=re.compile('name|coin-name'))
                
                # Extract price
                price_element = row.find(['td', 'div'], class_=re.compile('price|coin-price'))
                
                # Extract market cap
                market_cap_element = row.find(['td', 'div'], class_=re.compile('market-cap|coin-market-cap'))
                
                # Extract volume
                volume_element = row.find(['td', 'div'], class_=re.compile('volume|coin-volume'))
                
                # Extract change
                change_element = row.find(['td', 'div'], class_=re.compile('change|coin-change'))
                
                result[symbol] = {
                    "name": name_element.text.strip() if name_element else None,
                    "symbol": symbol,
                    "price": self._parse_value(price_element.text.strip()) if price_element else None,
                    "market_cap": self._parse_value(market_cap_element.text.strip()) if market_cap_element else None,
                    "volume_24h": self._parse_value(volume_element.text.strip()) if volume_element else None,
                    "change_24h": self._parse_percent(change_element.text.strip()) if change_element else None,
                    "last_updated": datetime.now().isoformat()
                }
            except Exception as e:
                logger.debug(f"Error extracting cryptocurrency data: {e}")
        
        return result
    
    def _extract_article_data(self, article_element) -> Optional[Dict]:
        """
        Extract data from an article element.
        
        Args:
            article_element: BeautifulSoup element containing article data
            
        Returns:
            Dictionary with article data or None if extraction fails
        """
        # Find headline
        headline_element = article_element.find(['h2', 'h3', 'a'], class_=re.compile('title|headline'))
        if not headline_element:
            return None
            
        # Find link
        link_element = headline_element if headline_element.name == 'a' else headline_element.find('a')
        if not link_element or not link_element.get('href'):
            return None
            
        link = link_element['href']
        if not link.startswith('http'):
            link = self.BASE_URL + link
            
        # Find timestamp
        timestamp_element = article_element.find(['time', 'span'], class_=re.compile('date|time|timestamp'))
        timestamp = timestamp_element.text.strip() if timestamp_element else None
        
        # Find summary
        summary_element = article_element.find(['p', 'div'], class_=re.compile('summary|description|excerpt'))
        summary = summary_element.text.strip() if summary_element else None
        
        # Find image
        image_element = article_element.find('img')
        image_url = None
        if image_element:
            for attr in ['src', 'data-src', 'data-lazy-src']:
                if attr in image_element.attrs:
                    image_url = image_element[attr]
                    break
        
        # Find author
        author_element = article_element.find(['span', 'div', 'a'], class_=re.compile('author|byline'))
        author = author_element.text.strip() if author_element else None
        
        # Find tags
        tags = []
        tags_container = article_element.find(['div', 'ul'], class_=re.compile('tags|categories'))
        if tags_container:
            tag_elements = tags_container.find_all('a')
            tags = [tag.text.strip() for tag in tag_elements]
        
        return {
            "headline": headline_element.text.strip(),
            "link": link,
            "timestamp": timestamp,
            "summary": summary,
            "image_url": image_url,
            "author": author,
            "tags": tags
        }
    
    @staticmethod
    def _parse_value(value_text: Optional[str]) -> Optional[Union[int, float]]:
        """
        Parse a value from text, handling suffixes like K, M, B, T.
        
        Args:
            value_text: Text value to parse
            
        Returns:
            Parsed numeric value
        """
        if not value_text:
            return None
            
        value_text = str(value_text).strip().replace(',', '')
        
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
        
        # Handle currency symbols
        value_text = re.sub(r'[^\d.-]', '', value_text)
        
        # No suffix, try to convert directly
        try:
            if '.' in value_text:
                return float(value_text)
            else:
                return int(value_text)
        except ValueError:
            return None
    
    @staticmethod
    def _parse_percent(percent_text: Optional[str]) -> Optional[float]:
        """
        Parse a percentage value from text.
        
        Args:
            percent_text: Text containing a percentage
            
        Returns:
            Float value of the percentage (e.g., 0.05 for 5%)
        """
        if not percent_text:
            return None
            
        # Remove any non-numeric characters except for the decimal point and minus sign
        percent_text = str(percent_text)
        percent_text = re.sub(r'[^\d.-]', '', percent_text)
        
        try:
            return float(percent_text) / 100
        except ValueError:
            return None