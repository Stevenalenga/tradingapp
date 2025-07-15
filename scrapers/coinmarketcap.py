"""
CoinMarketCap scraper module for the Trading Information Scraper application.

This module provides functionality for scraping cryptocurrency data from CoinMarketCap.
Note: CoinMarketCap has anti-bot measures, so this scraper focuses on basic data extraction.
For production use, consider using their official API.
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Union

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class CoinMarketCapScraper(BaseScraper):
    """
    Scraper for CoinMarketCap.
    
    This class provides methods for scraping cryptocurrency data from CoinMarketCap.
    Note: This site has anti-bot measures, so use with caution and consider rate limiting.
    """
    
    BASE_URL = "https://coinmarketcap.com"
    RANKINGS_URL = BASE_URL + "/rankings"
    CURRENCIES_URL = BASE_URL + "/currencies"
    GLOBAL_METRICS_URL = BASE_URL + "/charts"
    
    def __init__(self, **kwargs):
        """Initialize the CoinMarketCap scraper with enhanced headers for anti-bot measures."""
        # Enhanced headers to appear more like a real browser
        enhanced_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        kwargs['headers'] = enhanced_headers
        kwargs['retry_delay'] = 5  # Longer delay between retries
        super().__init__(**kwargs)
    
    def scrape(self, cryptocurrencies: Optional[List[str]] = None, max_coins: int = 100) -> Dict:
        """
        Scrape cryptocurrency data from CoinMarketCap.
        
        Args:
            cryptocurrencies: List of cryptocurrency symbols to scrape (if None, gets top coins)
            max_coins: Maximum number of coins to scrape from rankings
            
        Returns:
            Dictionary with scraped cryptocurrency data
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "source": "CoinMarketCap",
            "cryptocurrencies": {},
            "global_metrics": {}
        }
        
        try:
            # Get cryptocurrency data from rankings page
            market_data = self.scrape_market_rankings(max_coins)
            
            if cryptocurrencies:
                # Filter for specific cryptocurrencies
                requested_symbols = [c.upper() for c in cryptocurrencies]
                filtered_data = {}
                for symbol, data in market_data.items():
                    if symbol.upper() in requested_symbols:
                        filtered_data[symbol] = data
                result["cryptocurrencies"] = filtered_data
            else:
                result["cryptocurrencies"] = market_data
            
            # Get global metrics
            result["global_metrics"] = self.scrape_global_metrics()
            
        except Exception as e:
            logger.error(f"Error scraping from CoinMarketCap: {e}")
            result["error"] = str(e)
        
        return result
    
    def scrape_market_rankings(self, max_coins: int = 100) -> Dict[str, Dict]:
        """
        Scrape cryptocurrency market rankings.
        
        Args:
            max_coins: Maximum number of coins to scrape
            
        Returns:
            Dictionary mapping cryptocurrency symbols to their data
        """
        try:
            soup = self.get_html(self.BASE_URL)
            
            cryptocurrencies = {}
            
            # Look for the main cryptocurrency table
            table = soup.find('table')
            if not table:
                # Try to find div-based layout
                return self._scrape_div_based_layout(soup, max_coins)
            
            rows = table.find('tbody').find_all('tr') if table.find('tbody') else table.find_all('tr')
            
            for i, row in enumerate(rows[:max_coins]):
                try:
                    crypto_data = self._parse_table_row(row)
                    if crypto_data and crypto_data.get('symbol'):
                        cryptocurrencies[crypto_data['symbol']] = crypto_data
                
                except Exception as e:
                    logger.warning(f"Error parsing row {i}: {e}")
                    continue
            
            return cryptocurrencies
        
        except Exception as e:
            logger.error(f"Error scraping market rankings: {e}")
            return {}
    
    def scrape_global_metrics(self) -> Dict:
        """
        Scrape global cryptocurrency market metrics.
        
        Returns:
            Dictionary with global market data
        """
        try:
            soup = self.get_html(self.BASE_URL)
            
            metrics = {}
            
            # Look for global stats section
            stats_section = soup.find('div', class_=re.compile(r'.*stats.*|.*global.*|.*metrics.*'))
            if stats_section:
                metrics = self._extract_global_stats(stats_section)
            
            # Also try to extract from script tags
            script_metrics = self._extract_metrics_from_scripts(soup)
            metrics.update(script_metrics)
            
            metrics['scraped_at'] = datetime.now().isoformat()
            
            return metrics
        
        except Exception as e:
            logger.error(f"Error scraping global metrics: {e}")
            return {"error": str(e)}
    
    def _parse_table_row(self, row) -> Optional[Dict]:
        """
        Parse a table row containing cryptocurrency data.
        
        Args:
            row: BeautifulSoup tr element
            
        Returns:
            Dictionary with cryptocurrency data or None if parsing fails
        """
        try:
            cells = row.find_all('td')
            if len(cells) < 5:
                return None
            
            # Typical CoinMarketCap table structure:
            # [rank, name/symbol, price, 24h%, 7d%, market cap, volume, circulating supply]
            
            # Extract rank
            rank_text = cells[0].get_text(strip=True)
            rank = self._parse_int(rank_text)
            
            # Extract name and symbol (usually in the same cell)
            name_cell = cells[1] if len(cells) > 1 else cells[0]
            name_data = self._extract_name_and_symbol(name_cell)
            
            # Extract price
            price_cell = cells[2] if len(cells) > 2 else None
            price = self._parse_price(price_cell.get_text(strip=True)) if price_cell else 0
            
            # Extract 24h change
            change_24h_cell = cells[3] if len(cells) > 3 else None
            change_24h = self._parse_percentage(change_24h_cell.get_text(strip=True)) if change_24h_cell else 0
            
            # Extract 7d change
            change_7d_cell = cells[4] if len(cells) > 4 else None
            change_7d = self._parse_percentage(change_7d_cell.get_text(strip=True)) if change_7d_cell else 0
            
            # Extract market cap
            market_cap_cell = cells[5] if len(cells) > 5 else None
            market_cap = self._parse_number(market_cap_cell.get_text(strip=True)) if market_cap_cell else 0
            
            # Extract volume
            volume_cell = cells[6] if len(cells) > 6 else None
            volume_24h = self._parse_number(volume_cell.get_text(strip=True)) if volume_cell else 0
            
            # Extract circulating supply
            supply_cell = cells[7] if len(cells) > 7 else None
            circulating_supply = self._parse_number(supply_cell.get_text(strip=True)) if supply_cell else 0
            
            return {
                "rank": rank,
                "name": name_data.get('name', ''),
                "symbol": name_data.get('symbol', ''),
                "price": price,
                "change_24h": change_24h,
                "change_7d": change_7d,
                "market_cap": market_cap,
                "volume_24h": volume_24h,
                "circulating_supply": circulating_supply,
                "source": "CoinMarketCap"
            }
        
        except Exception as e:
            logger.warning(f"Error parsing table row: {e}")
            return None
    
    def _scrape_div_based_layout(self, soup: BeautifulSoup, max_coins: int) -> Dict[str, Dict]:
        """
        Scrape cryptocurrency data from div-based layout (fallback method).
        
        Args:
            soup: BeautifulSoup object
            max_coins: Maximum number of coins to scrape
            
        Returns:
            Dictionary mapping cryptocurrency symbols to their data
        """
        cryptocurrencies = {}
        
        try:
            # Look for cryptocurrency cards or rows
            crypto_elements = soup.find_all('div', class_=re.compile(r'.*coin.*|.*crypto.*|.*row.*'))
            
            for i, element in enumerate(crypto_elements[:max_coins]):
                try:
                    crypto_data = self._extract_crypto_from_div(element)
                    if crypto_data and crypto_data.get('symbol'):
                        cryptocurrencies[crypto_data['symbol']] = crypto_data
                
                except Exception as e:
                    logger.warning(f"Error parsing crypto div {i}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error in div-based scraping: {e}")
        
        return cryptocurrencies
    
    def _extract_crypto_from_div(self, element) -> Optional[Dict]:
        """
        Extract cryptocurrency data from a div element.
        
        Args:
            element: BeautifulSoup div element
            
        Returns:
            Dictionary with cryptocurrency data or None if extraction fails
        """
        try:
            # Look for symbol and name
            name_elem = element.find(class_=re.compile(r'.*name.*|.*title.*'))
            symbol_elem = element.find(class_=re.compile(r'.*symbol.*|.*ticker.*'))
            
            if not name_elem and not symbol_elem:
                return None
            
            name = name_elem.get_text(strip=True) if name_elem else ""
            symbol = symbol_elem.get_text(strip=True) if symbol_elem else ""
            
            # Look for price
            price_elem = element.find(class_=re.compile(r'.*price.*'))
            price = self._parse_price(price_elem.get_text(strip=True)) if price_elem else 0
            
            # Look for change percentage
            change_elem = element.find(class_=re.compile(r'.*change.*|.*percent.*'))
            change_24h = self._parse_percentage(change_elem.get_text(strip=True)) if change_elem else 0
            
            # Look for market cap
            cap_elem = element.find(class_=re.compile(r'.*cap.*|.*market.*'))
            market_cap = self._parse_number(cap_elem.get_text(strip=True)) if cap_elem else 0
            
            return {
                "name": name,
                "symbol": symbol.upper(),
                "price": price,
                "change_24h": change_24h,
                "market_cap": market_cap,
                "source": "CoinMarketCap"
            }
        
        except Exception as e:
            logger.warning(f"Error extracting crypto from div: {e}")
            return None
    
    def _extract_name_and_symbol(self, cell) -> Dict[str, str]:
        """
        Extract cryptocurrency name and symbol from a table cell.
        
        Args:
            cell: BeautifulSoup td element containing name and symbol
            
        Returns:
            Dictionary with name and symbol
        """
        try:
            text = cell.get_text(strip=True)
            
            # Try to find symbol in parentheses or separate elements
            symbol_match = re.search(r'\(([A-Z]+)\)', text)
            if symbol_match:
                symbol = symbol_match.group(1)
                name = text.replace(f'({symbol})', '').strip()
            else:
                # Look for separate elements
                name_elem = cell.find(class_=re.compile(r'.*name.*'))
                symbol_elem = cell.find(class_=re.compile(r'.*symbol.*'))
                
                name = name_elem.get_text(strip=True) if name_elem else text
                symbol = symbol_elem.get_text(strip=True) if symbol_elem else ""
            
            return {"name": name, "symbol": symbol.upper()}
        
        except Exception as e:
            logger.warning(f"Error extracting name and symbol: {e}")
            return {"name": "", "symbol": ""}
    
    def _extract_global_stats(self, stats_section) -> Dict:
        """
        Extract global statistics from a stats section.
        
        Args:
            stats_section: BeautifulSoup element containing stats
            
        Returns:
            Dictionary with global stats
        """
        stats = {}
        
        try:
            # Look for stat items
            stat_items = stats_section.find_all(['div', 'span'], class_=re.compile(r'.*stat.*|.*metric.*|.*value.*'))
            
            for item in stat_items:
                text = item.get_text(strip=True)
                
                if 'market cap' in text.lower():
                    number = self._extract_number_from_text(text)
                    if number:
                        stats['total_market_cap'] = number
                
                elif 'volume' in text.lower():
                    number = self._extract_number_from_text(text)
                    if number:
                        stats['total_volume'] = number
                
                elif 'cryptocurrencies' in text.lower() or 'coins' in text.lower():
                    number = self._extract_number_from_text(text)
                    if number:
                        stats['active_cryptocurrencies'] = number
                
                elif 'dominance' in text.lower():
                    number = self._extract_number_from_text(text)
                    if number:
                        stats['btc_dominance'] = number
        
        except Exception as e:
            logger.warning(f"Error extracting global stats: {e}")
        
        return stats
    
    def _extract_metrics_from_scripts(self, soup: BeautifulSoup) -> Dict:
        """
        Extract metrics from JavaScript/JSON in script tags.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Dictionary with extracted metrics
        """
        metrics = {}
        
        try:
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Look for JSON data in scripts
                    json_matches = re.findall(r'\{[^{}]*"marketCap"[^{}]*\}', script.string)
                    for match in json_matches:
                        try:
                            data = json.loads(match)
                            if 'marketCap' in data:
                                metrics['total_market_cap'] = data['marketCap']
                            if 'volume' in data:
                                metrics['total_volume'] = data['volume']
                        except json.JSONDecodeError:
                            continue
        
        except Exception as e:
            logger.warning(f"Error extracting metrics from scripts: {e}")
        
        return metrics
    
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
            clean_str = re.sub(r'[^\d.KMBTkmbt+-]', '', number_str.upper())
            number_match = re.match(r'([+-]?[\d.]+)([KMBT]?)', clean_str)
            
            if not number_match:
                return 0.0
            
            number = float(number_match.group(1))
            suffix = number_match.group(2)
            
            multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000, 'T': 1000000000000}
            if suffix in multipliers:
                number *= multipliers[suffix]
            
            return number
        except (ValueError, AttributeError):
            return 0.0
    
    def _parse_int(self, int_str: str) -> int:
        """Parse integer string."""
        try:
            clean_int = re.sub(r'[^\d]', '', int_str)
            return int(clean_int) if clean_int else 0
        except (ValueError, AttributeError):
            return 0
    
    def _extract_number_from_text(self, text: str) -> Optional[float]:
        """Extract the first number from text."""
        try:
            # Look for patterns like $1.23T, 1,234.56M, etc.
            number_match = re.search(r'[\d,]+\.?\d*[KMBT]?', text)
            if number_match:
                return self._parse_number(number_match.group())
            return None
        except Exception:
            return None
