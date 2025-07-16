"""
CryptoPanic scraper module for the Trading Information Scraper application.

This module provides functionality for scraping cryptocurrency news from CryptoPanic API.
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Union

import requests

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class CryptoPanicScraper(BaseScraper):
    """
    Scraper for CryptoPanic API.
    
    This class provides methods for scraping cryptocurrency news from CryptoPanic.
    Requires an API key for full functionality.
    """
    
    BASE_URL = "https://cryptopanic.com/api/v1"
    NEWS_URL = BASE_URL + "/posts"
    FREE_NEWS_URL = BASE_URL + "/posts/?public=true"
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the CryptoPanic scraper.
        
        Args:
            api_key: CryptoPanic API key (optional, but recommended for full access)
        """
        super().__init__(**kwargs)
        self.api_key = api_key
        self.last_request_time = 0
        self.min_request_interval = 1  # 1 second between requests to be respectful
    
    def _rate_limited_request(self, url: str, params: Optional[Dict] = None) -> requests.Response:
        """
        Make a rate-limited request to CryptoPanic API.
        
        Args:
            url: URL to request
            params: Query parameters
            
        Returns:
            Response object
        """
        # Ensure we don't make requests too quickly
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        # Add API key to params if available
        if self.api_key:
            params = params or {}
            params['auth_token'] = self.api_key
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()]) if params else ''
        full_url = url + ('&' + query_string if '?' in url and query_string else '?' + query_string if query_string else '')
        
        response = self._make_request(full_url)
        self.last_request_time = time.time()
        
        return response
    
    def scrape(self, 
               cryptocurrencies: Optional[List[str]] = None, 
               kind: str = 'news',
               filter_sentiment: Optional[str] = None,
               max_posts: int = 50) -> Dict:
        """
        Scrape cryptocurrency news from CryptoPanic API.
        
        Args:
            cryptocurrencies: List of cryptocurrency symbols to filter by
            kind: Type of posts ('news', 'media', 'all')
            filter_sentiment: Filter by sentiment ('rising', 'hot', 'bullish', 'bearish', 'important', 'saved')
            max_posts: Maximum number of posts to scrape
            
        Returns:
            Dictionary with scraped news data
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "source": "CryptoPanic",
            "posts": [],
            "metadata": {}
        }
        
        try:
            # Get news posts
            posts = self.scrape_news_posts(
                cryptocurrencies=cryptocurrencies,
                kind=kind,
                filter_sentiment=filter_sentiment,
                max_posts=max_posts
            )
            
            result["posts"] = posts
            result["metadata"] = {
                "total_posts": len(posts),
                "filter_applied": {
                    "cryptocurrencies": cryptocurrencies,
                    "kind": kind,
                    "sentiment": filter_sentiment
                },
                "has_api_key": self.api_key is not None
            }
            
        except Exception as e:
            logger.error(f"Error scraping from CryptoPanic: {e}")
            result["error"] = str(e)
        
        return result
    
    def scrape_news_posts(self,
                         cryptocurrencies: Optional[List[str]] = None,
                         kind: str = 'news',
                         filter_sentiment: Optional[str] = None,
                         max_posts: int = 50) -> List[Dict]:
        """
        Scrape news posts from CryptoPanic API.
        
        Args:
            cryptocurrencies: List of cryptocurrency symbols to filter by
            kind: Type of posts ('news', 'media', 'all')
            filter_sentiment: Filter by sentiment
            max_posts: Maximum number of posts to scrape
            
        Returns:
            List of news posts
        """
        try:
            params = {
                'public': 'true'  # Use public endpoint by default
            }
            
            # Add filters
            if kind and kind != 'all':
                params['kind'] = kind
            
            if filter_sentiment:
                params['filter'] = filter_sentiment
            
            if cryptocurrencies:
                # CryptoPanic uses comma-separated currency codes
                params['currencies'] = ','.join([c.upper() for c in cryptocurrencies])
            
            # Use authenticated endpoint if API key is available
            url = self.NEWS_URL if self.api_key else self.FREE_NEWS_URL
            
            posts = []
            page = 1
            posts_per_page = min(max_posts, 20)  # API typically returns 20 posts per page
            
            while len(posts) < max_posts:
                params['page'] = str(page)
                
                try:
                    response = self._rate_limited_request(url, params)
                    data = response.json()
                    
                    if 'results' not in data:
                        logger.warning("No results found in API response")
                        break
                    
                    page_posts = data['results']
                    if not page_posts:
                        break  # No more posts
                    
                    for post in page_posts:
                        if len(posts) >= max_posts:
                            break
                        
                        processed_post = self._process_post(post)
                        if processed_post:
                            posts.append(processed_post)
                    
                    # Check if there are more pages
                    if not data.get('next'):
                        break
                    
                    page += 1
                
                except Exception as e:
                    logger.error(f"Error fetching page {page}: {e}")
                    break
            
            return posts
        
        except Exception as e:
            logger.error(f"Error scraping news posts: {e}")
            return []
    
    def _process_post(self, post: Dict) -> Optional[Dict]:
        """
        Process a single post from the API response.
        
        Args:
            post: Raw post data from API
            
        Returns:
            Processed post data or None if processing fails
        """
        try:
            # Extract basic information
            processed = {
                "id": post.get('id'),
                "title": post.get('title', ''),
                "url": post.get('url', ''),
                "created_at": post.get('created_at', ''),
                "kind": post.get('kind', ''),
                "domain": post.get('domain', ''),
                "source": "CryptoPanic"
            }
            
            # Extract votes (sentiment indicators)
            votes = post.get('votes', {})
            processed["votes"] = {
                "negative": votes.get('negative', 0),
                "positive": votes.get('positive', 0),
                "important": votes.get('important', 0),
                "liked": votes.get('liked', 0),
                "disliked": votes.get('disliked', 0),
                "lol": votes.get('lol', 0),
                "toxic": votes.get('toxic', 0),
                "saved": votes.get('saved', 0)
            }
            
            # Calculate sentiment score
            total_votes = sum(processed["votes"].values())
            if total_votes > 0:
                positive_score = (votes.get('positive', 0) + votes.get('important', 0) + votes.get('liked', 0)) / total_votes
                negative_score = (votes.get('negative', 0) + votes.get('disliked', 0) + votes.get('toxic', 0)) / total_votes
                processed["sentiment_score"] = positive_score - negative_score
            else:
                processed["sentiment_score"] = 0
            
            # Extract currencies mentioned
            currencies = post.get('currencies', [])
            processed["currencies"] = []
            for currency in currencies:
                if isinstance(currency, dict):
                    processed["currencies"].append({
                        "code": currency.get('code', ''),
                        "title": currency.get('title', ''),
                        "slug": currency.get('slug', ''),
                        "url": currency.get('url', '')
                    })
                else:
                    processed["currencies"].append({"code": str(currency)})
            
            # Extract metadata
            metadata = post.get('metadata', {})
            if metadata:
                processed["metadata"] = {
                    "description": metadata.get('description', ''),
                    "twitter_account": metadata.get('twitter_account', ''),
                    "image": metadata.get('image', '')
                }
            
            return processed
        
        except Exception as e:
            logger.warning(f"Error processing post: {e}")
            return None
    
    def get_trending_news(self, max_posts: int = 20) -> List[Dict]:
        """
        Get trending cryptocurrency news.
        
        Args:
            max_posts: Maximum number of posts to return
            
        Returns:
            List of trending news posts
        """
        return self.scrape_news_posts(
            filter_sentiment='rising',
            max_posts=max_posts
        )
    
    def get_important_news(self, max_posts: int = 20) -> List[Dict]:
        """
        Get important cryptocurrency news.
        
        Args:
            max_posts: Maximum number of posts to return
            
        Returns:
            List of important news posts
        """
        return self.scrape_news_posts(
            filter_sentiment='important',
            max_posts=max_posts
        )
    
    def get_sentiment_analysis(self, cryptocurrencies: Optional[List[str]] = None) -> Dict:
        """
        Get sentiment analysis for cryptocurrencies.
        
        Args:
            cryptocurrencies: List of cryptocurrency symbols
            
        Returns:
            Dictionary with sentiment analysis
        """
        try:
            # Get recent posts for sentiment analysis
            posts = self.scrape_news_posts(
                cryptocurrencies=cryptocurrencies,
                max_posts=100
            )
            
            # Analyze sentiment
            sentiment_data = {}
            
            if cryptocurrencies:
                for crypto in cryptocurrencies:
                    crypto_upper = crypto.upper()
                    crypto_posts = [
                        post for post in posts 
                        if any(c.get('code', '').upper() == crypto_upper for c in post.get('currencies', []))
                    ]
                    
                    if crypto_posts:
                        sentiment_scores = [post.get('sentiment_score', 0) for post in crypto_posts]
                        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                        
                        sentiment_data[crypto_upper] = {
                            "average_sentiment": avg_sentiment,
                            "total_posts": len(crypto_posts),
                            "sentiment_distribution": self._calculate_sentiment_distribution(crypto_posts)
                        }
            else:
                # Overall sentiment
                if posts:
                    sentiment_scores = [post.get('sentiment_score', 0) for post in posts]
                    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                    
                    sentiment_data["overall"] = {
                        "average_sentiment": avg_sentiment,
                        "total_posts": len(posts),
                        "sentiment_distribution": self._calculate_sentiment_distribution(posts)
                    }
            
            return {
                "sentiment_data": sentiment_data,
                "analyzed_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting sentiment analysis: {e}")
            return {"error": str(e)}
    
    def _calculate_sentiment_distribution(self, posts: List[Dict]) -> Dict:
        """
        Calculate sentiment distribution from posts.
        
        Args:
            posts: List of posts
            
        Returns:
            Dictionary with sentiment distribution
        """
        try:
            total_posts = len(posts)
            if total_posts == 0:
                return {"positive": 0, "neutral": 0, "negative": 0}
            
            positive = sum(1 for post in posts if post.get('sentiment_score', 0) > 0.1)
            negative = sum(1 for post in posts if post.get('sentiment_score', 0) < -0.1)
            neutral = total_posts - positive - negative
            
            return {
                "positive": positive / total_posts,
                "neutral": neutral / total_posts,
                "negative": negative / total_posts
            }
        
        except Exception:
            return {"positive": 0, "neutral": 0, "negative": 0}
