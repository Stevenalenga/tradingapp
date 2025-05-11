"""
Base scraper module for the Trading Information Scraper application.

This module provides a base class for all scrapers with common functionality.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Base class for all scrapers.
    
    This class provides common functionality for web scraping, such as making HTTP requests,
    parsing HTML, handling errors, and implementing rate limiting.
    
    Attributes:
        headers (Dict[str, str]): Default HTTP headers for requests
        timeout (int): Default timeout for HTTP requests in seconds
        retry_count (int): Number of retries for failed requests
        retry_delay (int): Delay between retries in seconds
    """
    
    def __init__(
        self,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        retry_count: int = 3,
        retry_delay: int = 2
    ):
        """
        Initialize the base scraper.
        
        Args:
            headers: Custom HTTP headers for requests
            timeout: Timeout for HTTP requests in seconds
            retry_count: Number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_html(self, url: str) -> BeautifulSoup:
        """
        Get HTML content from a URL and parse it with BeautifulSoup.
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object with the parsed HTML
            
        Raises:
            requests.RequestException: If the request fails after retries
        """
        response = self._make_request(url)
        return BeautifulSoup(response.text, 'html.parser')
    
    def _make_request(self, url: str) -> requests.Response:
        """
        Make an HTTP request with retry logic.
        
        Args:
            url: URL to fetch
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: If the request fails after retries
        """
        for attempt in range(self.retry_count + 1):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                if attempt == self.retry_count:
                    logger.error(f"Failed to fetch {url} after {self.retry_count} retries: {e}")
                    raise
                logger.warning(f"Attempt {attempt + 1}/{self.retry_count + 1} failed for {url}: {e}")
                time.sleep(self.retry_delay)
    
    @abstractmethod
    def scrape(self, *args, **kwargs) -> Any:
        """
        Scrape data from the source.
        
        This method must be implemented by subclasses.
        
        Returns:
            Scraped data in a format specific to the subclass
        """
        pass
    
    def __del__(self):
        """Close the session when the scraper is deleted."""
        if hasattr(self, 'session'):
            self.session.close()