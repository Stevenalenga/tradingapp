"""
CryptoSlate scraper module for the Trading Information Scraper application.

This module provides functionality for scraping cryptocurrency news and data from CryptoSlate.
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Union

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class CryptoSlateScraper(BaseScraper):
    """
    Scraper for CryptoSlate.
    
    This class provides methods for scraping cryptocurrency news and insights from CryptoSlate.
    """
    
    BASE_URL = "https://cryptoslate.com"
    NEWS_URL = BASE_URL + "/news"
    COINS_URL = BASE_URL + "/coins"
    MARKETS_URL = BASE_URL + "/markets"
    
    def __init__(self, **kwargs):
        """Initialize the CryptoSlate scraper with base scraper parameters."""
        super().__init__(**kwargs)
    
    def scrape(self, include_news: bool = True, include_market_data: bool = True, max_articles: int = 30) -> Dict:
        """
        Scrape cryptocurrency news and market data from CryptoSlate.
        
        Args:
            include_news: Whether to include news articles
            include_market_data: Whether to include market data
            max_articles: Maximum number of news articles to scrape
            
        Returns:
            Dictionary with scraped news and market data
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "source": "CryptoSlate"
        }
        
        if include_news:
            result["news"] = self.scrape_crypto_news(max_articles)
        
        if include_market_data:
            result["market_data"] = self.scrape_market_data()
        
        return result
    
    def scrape_crypto_news(self, max_articles: int = 30) -> Dict:
        """
        Scrape cryptocurrency news articles from CryptoSlate.
        
        Args:
            max_articles: Maximum number of articles to scrape
            
        Returns:
            Dictionary with scraped news data
        """
        try:
            soup = self.get_html(self.NEWS_URL)
            
            articles = []
            
            # Look for article containers
            article_selectors = [
                'article',
                '.post-item',
                '.news-item',
                '.article-item',
                '[class*="article"]',
                '[class*="post"]'
            ]
            
            article_elements = []
            for selector in article_selectors:
                elements = soup.select(selector)
                if elements:
                    article_elements = elements
                    break
            
            # If no specific containers found, look for divs with article-like structure
            if not article_elements:
                article_elements = soup.find_all('div', class_=re.compile(r'.*article.*|.*post.*|.*news.*'))
            
            for article in article_elements[:max_articles]:
                try:
                    article_data = self._extract_article_data(article)
                    if article_data and article_data.get('title'):
                        articles.append(article_data)
                
                except Exception as e:
                    logger.warning(f"Error parsing article: {e}")
                    continue
            
            return {
                "articles": articles,
                "total_count": len(articles),
                "scraped_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error scraping news from CryptoSlate: {e}")
            return {"articles": [], "total_count": 0, "error": str(e)}
    
    def scrape_market_data(self) -> Dict:
        """
        Scrape market data from CryptoSlate.
        
        Returns:
            Dictionary with market data
        """
        try:
            soup = self.get_html(self.MARKETS_URL)
            
            market_data = {
                "cryptocurrencies": [],
                "market_stats": {}
            }
            
            # Look for cryptocurrency table or list
            table = soup.find('table')
            if table:
                market_data["cryptocurrencies"] = self._parse_crypto_table(table)
            
            # Look for market statistics
            stats = self._extract_market_stats(soup)
            if stats:
                market_data["market_stats"] = stats
            
            return market_data
        
        except Exception as e:
            logger.error(f"Error scraping market data from CryptoSlate: {e}")
            return {"error": str(e)}
    
    def _extract_article_data(self, article) -> Optional[Dict]:
        """
        Extract data from an article element.
        
        Args:
            article: BeautifulSoup element containing article data
            
        Returns:
            Dictionary with article data or None if extraction fails
        """
        try:
            # Extract title
            title_elem = article.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'.*title.*|.*headline.*'))
            if not title_elem:
                title_elem = article.find(['h1', 'h2', 'h3', 'h4'])
            
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            
            # Extract link
            link_elem = title_elem.find('a') if title_elem else article.find('a')
            link = ""
            if link_elem and link_elem.get('href'):
                href = link_elem.get('href')
                link = href if href.startswith('http') else self.BASE_URL + href
            
            # Extract date
            date_elem = article.find('time')
            if not date_elem:
                date_elem = article.find(class_=re.compile(r'.*date.*|.*time.*'))
            
            date = ""
            if date_elem:
                date = date_elem.get('datetime') or date_elem.get_text(strip=True)
            
            # Extract author
            author_elem = article.find(class_=re.compile(r'.*author.*|.*byline.*'))
            author = author_elem.get_text(strip=True) if author_elem else ""
            
            # Extract summary/excerpt
            summary_elem = article.find(['p'], class_=re.compile(r'.*summary.*|.*excerpt.*|.*description.*'))
            if not summary_elem:
                # Look for the first paragraph that's not part of metadata
                paragraphs = article.find_all('p')
                for p in paragraphs:
                    p_text = p.get_text(strip=True)
                    if len(p_text) > 50 and not any(keyword in p_text.lower() for keyword in ['by ', 'posted', 'published']):
                        summary_elem = p
                        break
            
            summary = summary_elem.get_text(strip=True) if summary_elem else ""
            
            # Extract tags/categories
            tags = []
            tag_elements = article.find_all(class_=re.compile(r'.*tag.*|.*category.*'))
            for tag_elem in tag_elements:
                tag_text = tag_elem.get_text(strip=True)
                if tag_text and len(tag_text) < 50:  # Avoid picking up long text as tags
                    tags.append(tag_text)
            
            return {
                "title": title,
                "link": link,
                "date": date,
                "author": author,
                "summary": summary[:500],  # Limit summary length
                "tags": tags[:5],  # Limit number of tags
                "source": "CryptoSlate"
            }
        
        except Exception as e:
            logger.warning(f"Error extracting article data: {e}")
            return None
    
    def _parse_crypto_table(self, table) -> List[Dict]:
        """
        Parse cryptocurrency data from a table.
        
        Args:
            table: BeautifulSoup table element
            
        Returns:
            List of cryptocurrency data dictionaries
        """
        cryptocurrencies = []
        
        try:
            rows = table.find_all('tr')
            header_row = rows[0] if rows else None
            
            # Try to identify column indices
            headers = []
            if header_row:
                headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
            
            # Common column mappings
            col_mapping = {
                'name': ['name', 'coin', 'cryptocurrency'],
                'symbol': ['symbol', 'ticker'],
                'price': ['price', 'value'],
                'change': ['change', '24h', 'change 24h', '24h change'],
                'volume': ['volume', '24h volume', 'volume 24h'],
                'market_cap': ['market cap', 'marketcap', 'cap']
            }
            
            # Find column indices
            col_indices = {}
            for field, keywords in col_mapping.items():
                for i, header in enumerate(headers):
                    if any(keyword in header for keyword in keywords):
                        col_indices[field] = i
                        break
            
            # Parse data rows
            for row in rows[1:]:  # Skip header row
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue
                
                crypto_data = {}
                
                # Extract data based on column indices
                if 'name' in col_indices and len(cells) > col_indices['name']:
                    crypto_data['name'] = cells[col_indices['name']].get_text(strip=True)
                
                if 'symbol' in col_indices and len(cells) > col_indices['symbol']:
                    crypto_data['symbol'] = cells[col_indices['symbol']].get_text(strip=True)
                
                if 'price' in col_indices and len(cells) > col_indices['price']:
                    price_text = cells[col_indices['price']].get_text(strip=True)
                    crypto_data['price'] = self._parse_price(price_text)
                
                if 'change' in col_indices and len(cells) > col_indices['change']:
                    change_text = cells[col_indices['change']].get_text(strip=True)
                    crypto_data['change_24h'] = self._parse_percentage(change_text)
                
                if 'volume' in col_indices and len(cells) > col_indices['volume']:
                    volume_text = cells[col_indices['volume']].get_text(strip=True)
                    crypto_data['volume_24h'] = self._parse_number(volume_text)
                
                if 'market_cap' in col_indices and len(cells) > col_indices['market_cap']:
                    cap_text = cells[col_indices['market_cap']].get_text(strip=True)
                    crypto_data['market_cap'] = self._parse_number(cap_text)
                
                # Only add if we have at least name or symbol
                if crypto_data.get('name') or crypto_data.get('symbol'):
                    crypto_data['source'] = 'CryptoSlate'
                    cryptocurrencies.append(crypto_data)
        
        except Exception as e:
            logger.error(f"Error parsing crypto table: {e}")
        
        return cryptocurrencies
    
    def _extract_market_stats(self, soup: BeautifulSoup) -> Dict:
        """
        Extract general market statistics from the page.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            Dictionary with market statistics
        """
        stats = {}
        
        try:
            # Look for market cap, volume, etc.
            stat_elements = soup.find_all(class_=re.compile(r'.*stat.*|.*metric.*|.*total.*'))
            
            for elem in stat_elements:
                text = elem.get_text(strip=True)
                
                # Try to extract total market cap
                if any(keyword in text.lower() for keyword in ['total market cap', 'market capitalization']):
                    number_match = re.search(r'[\d,]+\.?\d*', text)
                    if number_match:
                        stats['total_market_cap'] = self._parse_number(number_match.group())
                
                # Try to extract total volume
                elif any(keyword in text.lower() for keyword in ['total volume', '24h volume']):
                    number_match = re.search(r'[\d,]+\.?\d*', text)
                    if number_match:
                        stats['total_volume'] = self._parse_number(number_match.group())
                
                # Try to extract number of cryptocurrencies
                elif any(keyword in text.lower() for keyword in ['cryptocurrencies', 'coins']):
                    number_match = re.search(r'[\d,]+', text)
                    if number_match:
                        stats['active_cryptocurrencies'] = int(number_match.group().replace(',', ''))
        
        except Exception as e:
            logger.warning(f"Error extracting market stats: {e}")
        
        return stats
    
    def _parse_price(self, price_str: str) -> float:
        """Parse price string to float."""
        try:
            clean_price = re.sub(r'[^\d.-]', '', price_str.replace(',', ''))
            return float(clean_price) if clean_price else 0.0
        except (ValueError, AttributeError):
            return 0.0
    
    def _parse_percentage(self, percent_str: str) -> float:
        """Parse percentage string to float."""
        try:
            clean_percent = re.sub(r'[^\d.+-]', '', percent_str)
            return float(clean_percent) if clean_percent else 0.0
        except (ValueError, AttributeError):
            return 0.0
    
    def _parse_number(self, number_str: str) -> float:
        """Parse number string (possibly with K, M, B suffixes) to float."""
        try:
            # Remove currency symbols and spaces
            clean_str = re.sub(r'[^\d.KMBTkmbt+-]', '', number_str.upper())
            
            # Extract number part
            number_match = re.match(r'([+-]?[\d.]+)([KMBT]?)', clean_str)
            if not number_match:
                return 0.0
            
            number = float(number_match.group(1))
            suffix = number_match.group(2)
            
            # Apply multiplier based on suffix
            multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000, 'T': 1000000000000}
            if suffix in multipliers:
                number *= multipliers[suffix]
            
            return number
        except (ValueError, AttributeError):
            return 0.0
