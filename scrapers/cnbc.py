"""
CNBC scraper module for the Trading Information Scraper application.

This module provides functionality for scraping financial news from CNBC.
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Union

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class CNBCScraper(BaseScraper):
    """
    Scraper for CNBC.
    
    This class provides methods for scraping financial news and market data from CNBC.
    """
    
    BASE_URL = "https://www.cnbc.com"
    MARKETS_URL = BASE_URL + "/markets"
    NEWS_URL = BASE_URL + "/latest-news"
    CATEGORY_URL = BASE_URL + "/{category}"
    
    def __init__(self, **kwargs):
        """Initialize the CNBC scraper with base scraper parameters."""
        super().__init__(**kwargs)
    
    def scrape(self, categories: Optional[List[str]] = None, max_articles: int = 50) -> Dict:
        """
        Scrape news articles from CNBC.
        
        Args:
            categories: List of categories to scrape (default: ['markets', 'investing'])
            max_articles: Maximum number of articles to scrape
            
        Returns:
            Dictionary with scraped news data
        """
        categories = categories or ['markets', 'investing']
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "source": "CNBC",
            "categories": {}
        }
        
        for category in categories:
            try:
                logger.info(f"Scraping news for category: {category}")
                result["categories"][category] = self.scrape_category(category, max_articles)
            except Exception as e:
                logger.error(f"Error scraping category {category}: {e}")
                result["categories"][category] = {"error": str(e)}
        
        return result
    
    def scrape_category(self, category: str, max_articles: int) -> Dict:
        """
        Scrape news articles for a specific category.
        
        Args:
            category: Category to scrape
            max_articles: Maximum number of articles to scrape
            
        Returns:
            Dictionary with scraped news data for the category
        """
        url = self.CATEGORY_URL.format(category=category)
        soup = self.get_html(url)
        
        articles = []
        article_count = 0
        
        # Find all article cards/containers
        article_elements = soup.find_all(['div', 'article'], class_=re.compile('Card-container|Card-article|Card-standardBrick'))
        
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
    
    def scrape_news(self, categories: Optional[List[str]] = None, max_articles: int = 50) -> Dict:
        """
        Alias for scrape method to maintain API consistency.
        
        Args:
            categories: List of categories to scrape
            max_articles: Maximum number of articles to scrape
            
        Returns:
            Dictionary with scraped news data
        """
        return self.scrape(categories, max_articles)
    
    def scrape_market_data(self) -> Dict:
        """
        Scrape market data from CNBC Markets page.
        
        Returns:
            Dictionary with market indices and data
        """
        soup = self.get_html(self.MARKETS_URL)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "source": "CNBC",
            "indices": self._extract_market_indices(soup),
            "sectors": self._extract_market_sectors(soup),
            "commodities": self._extract_commodities(soup),
            "bonds": self._extract_bonds(soup),
            "currencies": self._extract_currencies(soup)
        }
        
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
        headline_element = article_element.find(['h2', 'h3', 'a'], class_=re.compile('Card-title|Card-headline'))
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
        timestamp_element = article_element.find(['time', 'span'], class_=re.compile('Card-time|Card-timestamp'))
        timestamp = timestamp_element.text.strip() if timestamp_element else None
        
        # Find summary
        summary_element = article_element.find(['p', 'div'], class_=re.compile('Card-description|Card-summary'))
        summary = summary_element.text.strip() if summary_element else None
        
        # Find image
        image_element = article_element.find('img')
        image_url = image_element['src'] if image_element and 'src' in image_element.attrs else None
        
        # Find author
        author_element = article_element.find(['span', 'div'], class_=re.compile('Card-author|Card-byline'))
        author = author_element.text.strip() if author_element else None
        
        return {
            "headline": headline_element.text.strip(),
            "link": link,
            "timestamp": timestamp,
            "summary": summary,
            "image_url": image_url,
            "author": author
        }
    
    def _extract_market_indices(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract market indices data from the soup.
        
        Args:
            soup: BeautifulSoup object with the parsed HTML
            
        Returns:
            List of dictionaries with market indices data
        """
        indices = []
        
        # Find the market indices section
        indices_section = soup.find('div', id=re.compile('market-indices|market-data-indices'))
        
        if not indices_section:
            logger.warning("Market indices section not found")
            return indices
            
        # Find all index elements
        index_elements = indices_section.find_all('tr', class_=re.compile('quote-table|index-row'))
        
        for index_element in index_elements:
            try:
                # Extract index name
                name_element = index_element.find(['td', 'div'], class_=re.compile('name|symbol'))
                if not name_element:
                    continue
                    
                # Extract index value
                value_element = index_element.find(['td', 'div'], class_=re.compile('value|last'))
                
                # Extract change
                change_element = index_element.find(['td', 'div'], class_=re.compile('change|net-change'))
                
                # Extract percent change
                percent_element = index_element.find(['td', 'div'], class_=re.compile('percent|percentage-change'))
                
                indices.append({
                    "name": name_element.text.strip(),
                    "value": float(value_element.text.strip().replace(',', '')) if value_element else None,
                    "change": float(change_element.text.strip().replace(',', '')) if change_element else None,
                    "percent_change": self._parse_percent(percent_element.text.strip()) if percent_element else None
                })
            except Exception as e:
                logger.debug(f"Error extracting index data: {e}")
        
        return indices
    
    def _extract_market_sectors(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract market sectors data from the soup."""
        # Implementation similar to _extract_market_indices
        return []  # Placeholder
    
    def _extract_commodities(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract commodities data from the soup."""
        # Implementation similar to _extract_market_indices
        return []  # Placeholder
    
    def _extract_bonds(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract bonds data from the soup."""
        # Implementation similar to _extract_market_indices
        return []  # Placeholder
    
    def _extract_currencies(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract currencies data from the soup."""
        # Implementation similar to _extract_market_indices
        return []  # Placeholder
    
    @staticmethod
    def _parse_percent(percent_text: str) -> Optional[float]:
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
        percent_text = re.sub(r'[^\d.-]', '', percent_text)
        
        try:
            return float(percent_text) / 100
        except ValueError:
            return None