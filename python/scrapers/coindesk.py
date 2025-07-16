"""
CoinDesk scraper module for the Trading Information Scraper application.

This module provides functionality for scraping cryptocurrency data and news from CoinDesk.
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Union

import requests
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class CoinDeskScraper(BaseScraper):
    """
    Scraper for CoinDesk.
    
    This class provides methods for scraping cryptocurrency data and news from CoinDesk.
    """
    
    BASE_URL = "https://coindesk.com"
    API_URL = "https://api.coindesk.com/v1/bpi/currentprice.json"
    NEWS_URL = BASE_URL + "/news"
    MARKET_DATA_URL = BASE_URL + "/coindesk20"
    
    def __init__(self, **kwargs):
        """Initialize the CoinDesk scraper with base scraper parameters."""
        super().__init__(**kwargs)
    
    def scrape(self, cryptocurrencies: Optional[List[str]] = None, include_news: bool = True, max_articles: int = 20) -> Dict:
        """
        Scrape cryptocurrency data and optionally news from CoinDesk.
        
        Args:
            cryptocurrencies: List of cryptocurrency symbols to scrape (default: ['BTC'])
            include_news: Whether to include news articles
            max_articles: Maximum number of news articles to scrape
            
        Returns:
            Dictionary with scraped cryptocurrency data and news
        """
        cryptocurrencies = cryptocurrencies or ['BTC']
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "source": "CoinDesk",
            "cryptocurrencies": {}
        }
        
        # Get Bitcoin price from CoinDesk API
        if 'BTC' in [c.upper() for c in cryptocurrencies]:
            btc_data = self.scrape_bitcoin_price()
            if btc_data:
                result["cryptocurrencies"]["BTC"] = btc_data
        
        # Get additional crypto data from CoinDesk 20 page
        additional_data = self.scrape_market_data(cryptocurrencies)
        result["cryptocurrencies"].update(additional_data)
        
        if include_news:
            result["news"] = self.scrape_crypto_news(max_articles)
        
        return result
    
    def scrape_bitcoin_price(self) -> Optional[Dict]:
        """
        Scrape Bitcoin price data from CoinDesk API.
        
        Returns:
            Dictionary with Bitcoin price data or None if failed
        """
        try:
            response = self._make_request(self.API_URL)
            data = response.json()
            
            bpi = data.get('bpi', {})
            usd_data = bpi.get('USD', {})
            
            return {
                "symbol": "BTC",
                "name": "Bitcoin",
                "price": self._parse_price(usd_data.get('rate', '0')),
                "currency": "USD",
                "last_updated": data.get('time', {}).get('updated', ''),
                "source": "CoinDesk API"
            }
        except Exception as e:
            logger.error(f"Error scraping Bitcoin price from CoinDesk API: {e}")
            return None
    
    def scrape_market_data(self, cryptocurrencies: List[str]) -> Dict[str, Dict]:
        """
        Scrape cryptocurrency market data from CoinDesk 20 page.
        
        Args:
            cryptocurrencies: List of cryptocurrency symbols to scrape
            
        Returns:
            Dictionary mapping cryptocurrency symbols to their data
        """
        try:
            soup = self.get_html(self.MARKET_DATA_URL)
            
            # Look for the CoinDesk 20 data table or JSON data
            crypto_data = {}
            
            # Try to find script tags with market data
            scripts = soup.find_all('script', type='application/json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if 'props' in data and 'pageProps' in data['props']:
                        market_data = data['props']['pageProps']
                        if 'coindesk20' in market_data:
                            cd20_data = market_data['coindesk20']
                            crypto_data.update(self._parse_coindesk20_data(cd20_data, cryptocurrencies))
                except json.JSONDecodeError:
                    continue
            
            # Fallback to HTML parsing if JSON parsing fails
            if not crypto_data:
                crypto_data = self._parse_market_data_html(soup, cryptocurrencies)
            
            return crypto_data
        
        except Exception as e:
            logger.error(f"Error scraping market data from CoinDesk: {e}")
            return {}
    
    def scrape_crypto_news(self, max_articles: int = 20) -> Dict:
        """
        Scrape cryptocurrency news articles from CoinDesk.
        
        Args:
            max_articles: Maximum number of articles to scrape
            
        Returns:
            Dictionary with scraped news data
        """
        try:
            soup = self.get_html(self.NEWS_URL)
            
            articles = []
            article_elements = soup.find_all('article', limit=max_articles)
            
            for article in article_elements:
                try:
                    # Extract article title
                    title_elem = article.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'.*title.*|.*headline.*'))
                    if not title_elem:
                        title_elem = article.find(['h1', 'h2', 'h3', 'h4'])
                    
                    title = title_elem.get_text(strip=True) if title_elem else "No title"
                    
                    # Extract article link
                    link_elem = title_elem.find('a') if title_elem else article.find('a')
                    link = ""
                    if link_elem and link_elem.get('href'):
                        href = link_elem.get('href')
                        link = href if href.startswith('http') else self.BASE_URL + href
                    
                    # Extract publication date
                    date_elem = article.find('time')
                    if not date_elem:
                        date_elem = article.find(class_=re.compile(r'.*date.*|.*time.*'))
                    
                    date = ""
                    if date_elem:
                        date = date_elem.get('datetime') or date_elem.get_text(strip=True)
                    
                    # Extract summary
                    summary_elem = article.find(['p'], class_=re.compile(r'.*summary.*|.*excerpt.*|.*description.*'))
                    if not summary_elem:
                        summary_elem = article.find('p')
                    
                    summary = summary_elem.get_text(strip=True) if summary_elem else ""
                    
                    if title and title != "No title":
                        articles.append({
                            "title": title,
                            "link": link,
                            "date": date,
                            "summary": summary,
                            "source": "CoinDesk"
                        })
                
                except Exception as e:
                    logger.warning(f"Error parsing article: {e}")
                    continue
            
            return {
                "articles": articles,
                "total_count": len(articles),
                "scraped_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error scraping news from CoinDesk: {e}")
            return {"articles": [], "total_count": 0, "error": str(e)}
    
    def _parse_coindesk20_data(self, cd20_data: Dict, cryptocurrencies: List[str]) -> Dict[str, Dict]:
        """
        Parse CoinDesk 20 data from JSON.
        
        Args:
            cd20_data: CoinDesk 20 data from JSON
            cryptocurrencies: List of cryptocurrencies to filter
            
        Returns:
            Dictionary mapping cryptocurrency symbols to their data
        """
        result = {}
        
        if 'assets' in cd20_data:
            for asset in cd20_data['assets']:
                symbol = asset.get('symbol', '').upper()
                if symbol in [c.upper() for c in cryptocurrencies]:
                    result[symbol] = {
                        "symbol": symbol,
                        "name": asset.get('name', ''),
                        "price": asset.get('price', 0),
                        "change_24h": asset.get('change_24h', 0),
                        "market_cap": asset.get('market_cap', 0),
                        "volume_24h": asset.get('volume_24h', 0),
                        "source": "CoinDesk 20"
                    }
        
        return result
    
    def _parse_market_data_html(self, soup: BeautifulSoup, cryptocurrencies: List[str]) -> Dict[str, Dict]:
        """
        Parse market data from HTML when JSON parsing fails.
        
        Args:
            soup: BeautifulSoup object of the page
            cryptocurrencies: List of cryptocurrencies to filter
            
        Returns:
            Dictionary mapping cryptocurrency symbols to their data
        """
        result = {}
        
        # Look for table rows with crypto data
        rows = soup.find_all('tr')
        for row in rows:
            try:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:
                    # Try to extract symbol from first cell
                    symbol_text = cells[0].get_text(strip=True).upper()
                    if any(crypto.upper() in symbol_text for crypto in cryptocurrencies):
                        # Extract the cryptocurrency symbol
                        symbol = next((c.upper() for c in cryptocurrencies if c.upper() in symbol_text), None)
                        if symbol:
                            price_text = cells[1].get_text(strip=True) if len(cells) > 1 else "0"
                            change_text = cells[2].get_text(strip=True) if len(cells) > 2 else "0"
                            
                            result[symbol] = {
                                "symbol": symbol,
                                "price": self._parse_price(price_text),
                                "change_24h": self._parse_percentage(change_text),
                                "source": "CoinDesk HTML"
                            }
            except Exception as e:
                logger.warning(f"Error parsing table row: {e}")
                continue
        
        return result
    
    def _parse_price(self, price_str: str) -> float:
        """
        Parse price string to float.
        
        Args:
            price_str: Price string (e.g., "$1,234.56", "1234.56")
            
        Returns:
            Price as float
        """
        try:
            # Remove currency symbols, commas, and other non-numeric characters except decimal point
            clean_price = re.sub(r'[^\d.-]', '', price_str.replace(',', ''))
            return float(clean_price) if clean_price else 0.0
        except (ValueError, AttributeError):
            return 0.0
    
    def _parse_percentage(self, percent_str: str) -> float:
        """
        Parse percentage string to float.
        
        Args:
            percent_str: Percentage string (e.g., "+1.23%", "-2.45%")
            
        Returns:
            Percentage as float
        """
        try:
            # Remove % sign and other non-numeric characters except +, -, and decimal point
            clean_percent = re.sub(r'[^\d.+-]', '', percent_str)
            return float(clean_percent) if clean_percent else 0.0
        except (ValueError, AttributeError):
            return 0.0
