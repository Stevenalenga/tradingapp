"""
CoinGecko scraper module for the Trading Information Scraper application.

This module provides functionality for scraping cryptocurrency data from CoinGecko API.
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Union

import requests

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class CoinGeckoScraper(BaseScraper):
    """
    Scraper for CoinGecko API.
    
    This class provides methods for scraping cryptocurrency data from CoinGecko's free API.
    Rate limit: 30 calls per minute.
    """
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    PING_URL = BASE_URL + "/ping"
    COINS_LIST_URL = BASE_URL + "/coins/list"
    SIMPLE_PRICE_URL = BASE_URL + "/simple/price"
    COINS_MARKETS_URL = BASE_URL + "/coins/markets"
    TRENDING_URL = BASE_URL + "/search/trending"
    GLOBAL_URL = BASE_URL + "/global"
    
    # Mapping of common symbols to CoinGecko IDs
    SYMBOL_TO_ID = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'XRP': 'ripple',
        'ADA': 'cardano',
        'SOL': 'solana',
        'DOT': 'polkadot',
        'MATIC': 'polygon',
        'AVAX': 'avalanche-2',
        'LINK': 'chainlink',
        'UNI': 'uniswap',
        'LTC': 'litecoin',
        'BCH': 'bitcoin-cash',
        'ALGO': 'algorand',
        'ATOM': 'cosmos',
        'VET': 'vechain'
    }
    
    def __init__(self, **kwargs):
        """Initialize the CoinGecko scraper with base scraper parameters."""
        super().__init__(**kwargs)
        self.last_request_time = 0
        self.min_request_interval = 2  # 2 seconds between requests to respect rate limit
    
    def _rate_limited_request(self, url: str, params: Optional[Dict] = None) -> requests.Response:
        """
        Make a rate-limited request to CoinGecko API.
        
        Args:
            url: URL to request
            params: Query parameters
            
        Returns:
            Response object
        """
        # Ensure we don't exceed rate limit
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        response = self._make_request(url + ('?' + '&'.join([f"{k}={v}" for k, v in params.items()]) if params else ''))
        self.last_request_time = time.time()
        
        return response
    
    def scrape(self, cryptocurrencies: Optional[List[str]] = None, include_market_data: bool = True, include_trending: bool = False) -> Dict:
        """
        Scrape cryptocurrency data from CoinGecko API.
        
        Args:
            cryptocurrencies: List of cryptocurrency symbols to scrape (default: ['BTC', 'ETH', 'XRP', 'ADA'])
            include_market_data: Whether to include detailed market data
            include_trending: Whether to include trending cryptocurrencies
            
        Returns:
            Dictionary with scraped cryptocurrency data
        """
        cryptocurrencies = cryptocurrencies or ['BTC', 'ETH', 'XRP', 'ADA']
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "source": "CoinGecko",
            "cryptocurrencies": {}
        }
        
        # Check API status
        if not self._check_api_status():
            logger.error("CoinGecko API is not available")
            return result
        
        # Get cryptocurrency data
        if include_market_data:
            market_data = self.scrape_market_data(cryptocurrencies)
            result["cryptocurrencies"].update(market_data)
        else:
            price_data = self.scrape_simple_prices(cryptocurrencies)
            result["cryptocurrencies"].update(price_data)
        
        # Get trending data if requested
        if include_trending:
            result["trending"] = self.scrape_trending()
        
        # Get global market data
        result["global_data"] = self.scrape_global_data()
        
        return result
    
    def _check_api_status(self) -> bool:
        """
        Check if CoinGecko API is available.
        
        Returns:
            True if API is available, False otherwise
        """
        try:
            response = self._rate_limited_request(self.PING_URL)
            data = response.json()
            return data.get('gecko_says') == '(V3) To the Moon!'
        except Exception as e:
            logger.error(f"Error checking CoinGecko API status: {e}")
            return False
    
    def scrape_simple_prices(self, cryptocurrencies: List[str]) -> Dict[str, Dict]:
        """
        Scrape simple price data for cryptocurrencies.
        
        Args:
            cryptocurrencies: List of cryptocurrency symbols
            
        Returns:
            Dictionary mapping cryptocurrency symbols to their price data
        """
        try:
            # Convert symbols to CoinGecko IDs
            coin_ids = []
            symbol_to_id_map = {}
            
            for symbol in cryptocurrencies:
                symbol_upper = symbol.upper()
                coin_id = self.SYMBOL_TO_ID.get(symbol_upper)
                if coin_id:
                    coin_ids.append(coin_id)
                    symbol_to_id_map[coin_id] = symbol_upper
                else:
                    logger.warning(f"Unknown cryptocurrency symbol: {symbol_upper}")
            
            if not coin_ids:
                return {}
            
            # Make API request
            params = {
                'ids': ','.join(coin_ids),
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_market_cap': 'true'
            }
            
            response = self._rate_limited_request(self.SIMPLE_PRICE_URL, params)
            data = response.json()
            
            result = {}
            for coin_id, price_data in data.items():
                symbol = symbol_to_id_map.get(coin_id)
                if symbol:
                    result[symbol] = {
                        "symbol": symbol,
                        "coin_id": coin_id,
                        "price": price_data.get('usd', 0),
                        "market_cap": price_data.get('usd_market_cap', 0),
                        "volume_24h": price_data.get('usd_24h_vol', 0),
                        "change_24h": price_data.get('usd_24h_change', 0),
                        "source": "CoinGecko API"
                    }
            
            return result
        
        except Exception as e:
            logger.error(f"Error scraping simple prices from CoinGecko: {e}")
            return {}
    
    def scrape_market_data(self, cryptocurrencies: List[str], limit: int = 250) -> Dict[str, Dict]:
        """
        Scrape detailed market data for cryptocurrencies.
        
        Args:
            cryptocurrencies: List of cryptocurrency symbols
            limit: Number of coins to fetch (max 250)
            
        Returns:
            Dictionary mapping cryptocurrency symbols to their market data
        """
        try:
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': str(min(limit, 250)),
                'page': '1',
                'sparkline': 'false',
                'price_change_percentage': '24h,7d'
            }
            
            response = self._rate_limited_request(self.COINS_MARKETS_URL, params)
            data = response.json()
            
            # Filter for requested cryptocurrencies
            requested_symbols = [c.upper() for c in cryptocurrencies]
            result = {}
            
            for coin in data:
                symbol = coin.get('symbol', '').upper()
                if symbol in requested_symbols:
                    result[symbol] = {
                        "symbol": symbol,
                        "coin_id": coin.get('id', ''),
                        "name": coin.get('name', ''),
                        "price": coin.get('current_price', 0),
                        "market_cap": coin.get('market_cap', 0),
                        "market_cap_rank": coin.get('market_cap_rank', 0),
                        "volume_24h": coin.get('total_volume', 0),
                        "change_24h": coin.get('price_change_percentage_24h', 0),
                        "change_7d": coin.get('price_change_percentage_7d_in_currency', 0),
                        "circulating_supply": coin.get('circulating_supply', 0),
                        "total_supply": coin.get('total_supply', 0),
                        "max_supply": coin.get('max_supply', 0),
                        "ath": coin.get('ath', 0),
                        "ath_change_percentage": coin.get('ath_change_percentage', 0),
                        "ath_date": coin.get('ath_date', ''),
                        "atl": coin.get('atl', 0),
                        "atl_change_percentage": coin.get('atl_change_percentage', 0),
                        "atl_date": coin.get('atl_date', ''),
                        "last_updated": coin.get('last_updated', ''),
                        "source": "CoinGecko API"
                    }
            
            return result
        
        except Exception as e:
            logger.error(f"Error scraping market data from CoinGecko: {e}")
            return {}
    
    def scrape_trending(self) -> Dict:
        """
        Scrape trending cryptocurrency data.
        
        Returns:
            Dictionary with trending cryptocurrencies
        """
        try:
            response = self._rate_limited_request(self.TRENDING_URL)
            data = response.json()
            
            trending_coins = []
            if 'coins' in data:
                for coin_data in data['coins']:
                    coin = coin_data.get('item', {})
                    trending_coins.append({
                        "id": coin.get('id', ''),
                        "name": coin.get('name', ''),
                        "symbol": coin.get('symbol', '').upper(),
                        "market_cap_rank": coin.get('market_cap_rank', 0),
                        "price_btc": coin.get('price_btc', 0),
                        "score": coin.get('score', 0)
                    })
            
            return {
                "coins": trending_coins,
                "scraped_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error scraping trending data from CoinGecko: {e}")
            return {"coins": [], "error": str(e)}
    
    def scrape_global_data(self) -> Dict:
        """
        Scrape global cryptocurrency market data.
        
        Returns:
            Dictionary with global market data
        """
        try:
            response = self._rate_limited_request(self.GLOBAL_URL)
            data = response.json()
            
            if 'data' not in data:
                return {}
            
            global_data = data['data']
            
            return {
                "active_cryptocurrencies": global_data.get('active_cryptocurrencies', 0),
                "upcoming_icos": global_data.get('upcoming_icos', 0),
                "ongoing_icos": global_data.get('ongoing_icos', 0),
                "ended_icos": global_data.get('ended_icos', 0),
                "markets": global_data.get('markets', 0),
                "total_market_cap": global_data.get('total_market_cap', {}).get('usd', 0),
                "total_volume": global_data.get('total_volume', {}).get('usd', 0),
                "market_cap_percentage": global_data.get('market_cap_percentage', {}),
                "market_cap_change_percentage_24h": global_data.get('market_cap_change_percentage_24h_usd', 0),
                "updated_at": global_data.get('updated_at', 0),
                "scraped_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error scraping global data from CoinGecko: {e}")
            return {"error": str(e)}
    
    def get_coin_id(self, symbol: str) -> Optional[str]:
        """
        Get CoinGecko coin ID for a given symbol.
        
        Args:
            symbol: Cryptocurrency symbol
            
        Returns:
            CoinGecko coin ID or None if not found
        """
        symbol_upper = symbol.upper()
        
        # Check our predefined mapping first
        if symbol_upper in self.SYMBOL_TO_ID:
            return self.SYMBOL_TO_ID[symbol_upper]
        
        # If not found, query the API (this uses a request)
        try:
            response = self._rate_limited_request(self.COINS_LIST_URL)
            coins = response.json()
            
            for coin in coins:
                if coin.get('symbol', '').upper() == symbol_upper:
                    # Cache the result for future use
                    self.SYMBOL_TO_ID[symbol_upper] = coin['id']
                    return coin['id']
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting coin ID for {symbol}: {e}")
            return None
