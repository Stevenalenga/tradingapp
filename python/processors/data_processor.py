"""
Data processor module for the Trading Information Scraper application.

This module provides functionality for processing and transforming financial data.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Tuple, Iterable

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# -----------------------
# Trading data validation
# -----------------------

# Bounds per symbol with conservative sanity ranges
BOUNDS: Dict[str, Tuple[float, float]] = {
    "BTC": (10, 2_000_000),
    "ETH": (1, 200_000),
    "SOL": (0.001, 20_000),
    "XRP": (0.00001, 10_000),
    "BNB": (0.01, 100_000),
}
DEFAULT_BOUNDS: Tuple[float, float] = (1e-12, 1_000_000_000)


def parse_numeric(value: Any) -> Optional[float]:
    """
    Robust numeric parser.
    Accepts: "$42,001.25", "€3,100", "42k", "1.2M", "0.00000012", ints/floats, or None.
    Returns float or None on failure.
    """
    if value is None:
        return None
    import numpy as _np  # local import to avoid global if numpy missing at runtime
    if isinstance(value, (int, float)) or str(type(value)).endswith("numpy.float64'>"):
        try:
            return float(value)
        except Exception:
            return None

    s = str(value).strip()
    if not s:
        return None

    # Remove common currency and percent symbols
    s = s.replace(",", "").replace("$", "").replace("€", "").replace("£", "").replace("%", "")
    mult = 1.0
    if s and s[-1].upper() in ("K", "M", "B", "T"):
        suffix = s[-1].upper()
        s = s[:-1]
        mult = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}.get(suffix, 1.0)

    try:
        return float(s) * mult
    except Exception:
        # Last resort: strip any non-numeric except dot and sign
        s2 = re.sub(r"[^\d\.\-+eE]", "", s)
        try:
            return float(s2) * mult if s2 else None
        except Exception:
            return None


def in_bounds(symbol: str, price: float) -> bool:
    lo, hi = BOUNDS.get(symbol.upper(), DEFAULT_BOUNDS)
    return lo <= price <= hi


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DataProcessor:
    """
    Data processor for financial data.
    
    This class provides methods for cleaning, normalizing, and transforming
    financial data from various sources.
    """
    
    def __init__(self):
        """Initialize the data processor."""
        pass
    
    def validate_prices(self, rows: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, set, Dict[str, str]]:
        """
        Validate per-ticker rows with sanity checks.

        Input rows schema (flexible):
          - symbol (required)
          - price (required, raw or numeric)
          - volume (optional)
          - change_24h (optional)
          - currency (optional; prefer USD)
          - ts (optional; will be set to UTC now if missing)
          - source (optional)

        Returns:
          cleaned_df: rows that passed validation
          needs_fallback: set of symbols that failed validation or flagged as stale
          reasons: map symbol -> reason string (e.g., 'out_of_bounds', 'x_symbol_same_price', 'constant_price_last_5')
        """
        if not rows:
            return pd.DataFrame(columns=["symbol", "price", "volume", "change_24h", "currency", "ts", "source"]), set(), {}

        # Normalize rows into DataFrame
        df = pd.DataFrame(rows).copy()

        # Ensure required columns
        for col in ("symbol", "price"):
            if col not in df.columns:
                df[col] = np.nan

        # Normalize timestamp column
        if "ts" not in df.columns:
            df["ts"] = utc_now_iso()
        else:
            # Coerce to ISO strings
            df["ts"] = df["ts"].apply(lambda x: pd.to_datetime(x).isoformat() if pd.notna(x) else utc_now_iso())

        # Parse numerics
        for col in ("price", "volume", "change_24h"):
            if col in df.columns:
                df[col] = df[col].apply(parse_numeric)

        # Currency default
        if "currency" not in df.columns:
            df["currency"] = "USD"
        df["currency"] = df["currency"].fillna("USD")

        # Basic invalid reasons
        df["invalid_reason"] = None
        # NaN or non-positive
        df.loc[df["price"].isna(), "invalid_reason"] = "price_nan"
        df.loc[df["price"].notna() & (df["price"] <= 0), "invalid_reason"] = "price_nonpositive"

        # Out-of-bounds per ticker
        def _check_bounds(row):
            if row["invalid_reason"] is not None:
                return row["invalid_reason"]
            try:
                if not in_bounds(str(row.get("symbol", "")).upper(), float(row["price"])):
                    return "out_of_bounds"
            except Exception:
                return "bounds_eval_error"
            return None

        df["invalid_reason"] = df.apply(_check_bounds, axis=1)

        # Cross-symbol identical price at same timestamp
        try:
            ok = df[df["invalid_reason"].isna() & df["price"].notna()]
            if not ok.empty:
                grp = ok.groupby(["ts", "price"])["symbol"].nunique().reset_index(name="n")
                dup = grp[grp["n"] > 1][["ts", "price"]]
                if not dup.empty:
                    mark_idx = dup.merge(df, on=["ts", "price"], how="left").index
                    df.loc[mark_idx, "invalid_reason"] = df.loc[mark_idx, "invalid_reason"].fillna("x_symbol_same_price")
        except Exception:
            pass

        # Constant price sequences detection per symbol (last 5 samples identical)
        flagged_symbols: set = set()
        reasons: Dict[str, str] = {}
        try:
            df_sorted = df.sort_values(["symbol", "ts"])
            for sym, g in df_sorted.groupby("symbol"):
                prices = g["price"].dropna().values
                if len(prices) >= 5 and len(set(prices[-5:])) == 1:
                    flagged_symbols.add(sym)
                    reasons[sym] = "constant_price_last_5"
        except Exception:
            pass

        invalid = df[df["invalid_reason"].notna()]
        needs_fallback = set(invalid["symbol"].dropna().unique()).union(flagged_symbols)

        cleaned_df = df[df["invalid_reason"].isna()].copy()

        return cleaned_df, needs_fallback, reasons

    def get_fallback_prices(self, symbols: Iterable[str], prefer: str = "coingecko") -> List[Dict[str, Any]]:
        """
        Retrieve fallback prices for symbols from trusted feeds (CoinGecko/CoinMarketCap).
        Returns list of normalized rows with currency set to USD and ts in UTC ISO.
        """
        results: List[Dict[str, Any]] = []
        if not symbols:
            return results

        # Lazy imports to avoid circulars if any
        try:
            from python.scrapers.coingecko import CoinGeckoScraper  # type: ignore
        except Exception:
            try:
                from .scrapers.coingecko import CoinGeckoScraper  # type: ignore
            except Exception:
                CoinGeckoScraper = None  # type: ignore

        try:
            from python.scrapers.coinmarketcap import CoinMarketCapScraper  # type: ignore
        except Exception:
            try:
                from .scrapers.coinmarketcap import CoinMarketCapScraper  # type: ignore
            except Exception:
                CoinMarketCapScraper = None  # type: ignore

        providers = []
        if prefer == "coingecko":
            if CoinGeckoScraper:
                providers.append(("coingecko", CoinGeckoScraper()))
            if CoinMarketCapScraper:
                providers.append(("coinmarketcap", CoinMarketCapScraper()))
        else:
            if CoinMarketCapScraper:
                providers.append(("coinmarketcap", CoinMarketCapScraper()))
            if CoinGeckoScraper:
                providers.append(("coingecko", CoinGeckoScraper()))

        # Attempt to fetch from each provider
        for sym in set([str(s).upper() for s in symbols]):
            row = None
            for name, src in providers:
                try:
                    # Prefer structured APIs available
                    if hasattr(src, "scrape_simple_prices"):
                        data = src.scrape_simple_prices([sym])
                        rec = data.get(sym)
                        if rec:
                            row = {
                                "symbol": sym,
                                "price": parse_numeric(rec.get("price")),
                                "volume": parse_numeric(rec.get("volume_24h") or rec.get("usd_24h_vol")),
                                "change_24h": parse_numeric(rec.get("change_24h")),
                                "currency": "USD",
                                "ts": utc_now_iso(),
                                "source": f"{name}_fallback",
                            }
                            break
                    elif hasattr(src, "scrape"):
                        data = src.scrape([sym])
                        crypto = data.get("cryptocurrencies", {}).get(sym)
                        if crypto:
                            row = {
                                "symbol": sym,
                                "price": parse_numeric(crypto.get("price")),
                                "volume": parse_numeric(crypto.get("volume_24h")),
                                "change_24h": parse_numeric(crypto.get("change_24h")),
                                "currency": "USD",
                                "ts": utc_now_iso(),
                                "source": f"{name}_fallback",
                            }
                            break
                except Exception as e:
                    logger.debug(f"Fallback provider {name} failed for {sym}: {e}")
                    continue

            if row and row.get("price") is not None and row.get("price", 0) > 0:
                results.append(row)

        return results

    def process_trading_rows(self, raw_rows: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, set, Dict[str, str]]:
        """
        Entry point to validate rows and apply fallback substitution.
        Returns a cleaned DataFrame, blocked symbols set, and reasons map.
        """
        cleaned, needs_fallback, reasons = self.validate_prices(raw_rows)

        if needs_fallback:
            fb_rows = self.get_fallback_prices(needs_fallback, prefer="coingecko")
            if fb_rows:
                fb_cleaned, _, _ = self.validate_prices(fb_rows)
                cleaned = pd.concat([cleaned, fb_cleaned], ignore_index=True)

        # Block symbols that still have no valid row after fallback
        if not cleaned.empty:
            valid_syms = set(cleaned["symbol"].unique())
            still_blocked = set([s for s in needs_fallback if s not in valid_syms])
        else:
            still_blocked = needs_fallback.copy()

        blocked = set(still_blocked).union({s for s, r in reasons.items() if r.startswith("constant_price")})

        return cleaned, blocked, reasons

    def process(self, data: Dict) -> Dict:
        """
        Process data from various sources.
        
        Args:
            data: Dictionary containing data from different sources
            
        Returns:
            Processed data dictionary
        """
        processed_data = {}
        
        # Process data based on source
        for source, source_data in data.items():
            if source == "yahoo_finance":
                processed_data[source] = self.process_yahoo_finance(source_data)
            elif source == "cnbc":
                processed_data[source] = self.process_cnbc(source_data)
            elif source == "cointelegraph":
                processed_data[source] = self.process_cointelegraph(source_data)
            else:
                logger.warning(f"Unknown source: {source}")
                processed_data[source] = source_data
        
        return processed_data
    
    def process_yahoo_finance(self, data: Dict) -> Dict:
        """
        Process Yahoo Finance data.
        
        Args:
            data: Dictionary containing Yahoo Finance data
            
        Returns:
            Processed data dictionary
        """
        processed_data = {}
        
        for symbol, symbol_data in data.items():
            if "error" in symbol_data:
                processed_data[symbol] = symbol_data
                continue
                
            processed_symbol_data = {
                "symbol": symbol,
                "timestamp": self._normalize_timestamp(symbol_data.get("timestamp")),
                "price": self._normalize_numeric(symbol_data.get("price")),
                "change": self._normalize_numeric(symbol_data.get("change")),
                "change_percent": self._normalize_percent(symbol_data.get("change_percent")),
                "volume": self._normalize_numeric(symbol_data.get("volume")),
                "market_cap": self._normalize_numeric(symbol_data.get("market_cap")),
                "pe_ratio": self._normalize_numeric(symbol_data.get("pe_ratio")),
                "dividend_yield": self._normalize_percent(symbol_data.get("dividend_yield"))
            }
            
            # Remove None values
            processed_symbol_data = {k: v for k, v in processed_symbol_data.items() if v is not None}
            
            processed_data[symbol] = processed_symbol_data
        
        return processed_data
    
    def process_cnbc(self, data: Dict) -> Dict:
        """
        Process CNBC data.
        
        Args:
            data: Dictionary containing CNBC data
            
        Returns:
            Processed data dictionary
        """
        if "categories" not in data:
            return data
            
        processed_data = {
            "timestamp": self._normalize_timestamp(data.get("timestamp")),
            "source": data.get("source"),
            "categories": {}
        }
        
        for category, category_data in data["categories"].items():
            if "error" in category_data:
                processed_data["categories"][category] = category_data
                continue
                
            processed_articles = []
            
            for article in category_data.get("articles", []):
                processed_article = {
                    "headline": article.get("headline"),
                    "link": article.get("link"),
                    "timestamp": self._normalize_news_timestamp(article.get("timestamp")),
                    "summary": self._clean_text(article.get("summary")),
                    "image_url": article.get("image_url"),
                    "author": self._clean_text(article.get("author"))
                }
                
                # Remove None values
                processed_article = {k: v for k, v in processed_article.items() if v is not None}
                
                processed_articles.append(processed_article)
            
            processed_data["categories"][category] = {
                "total": len(processed_articles),
                "articles": processed_articles
            }
        
        return processed_data
    
    def process_cointelegraph(self, data: Dict) -> Dict:
        """
        Process CoinTelegraph data.
        
        Args:
            data: Dictionary containing CoinTelegraph data
            
        Returns:
            Processed data dictionary
        """
        processed_data = {
            "timestamp": self._normalize_timestamp(data.get("timestamp")),
            "source": data.get("source"),
            "cryptocurrencies": {}
        }
        
        # Process cryptocurrency data
        for symbol, crypto_data in data.get("cryptocurrencies", {}).items():
            if "error" in crypto_data:
                processed_data["cryptocurrencies"][symbol] = crypto_data
                continue
                
            processed_crypto_data = {
                "name": crypto_data.get("name"),
                "symbol": symbol,
                "price": self._normalize_numeric(crypto_data.get("price")),
                "market_cap": self._normalize_numeric(crypto_data.get("market_cap")),
                "volume_24h": self._normalize_numeric(crypto_data.get("volume_24h")),
                "change_24h": self._normalize_percent(crypto_data.get("change_24h")),
                "change_7d": self._normalize_percent(crypto_data.get("change_7d")),
                "last_updated": self._normalize_timestamp(crypto_data.get("last_updated"))
            }
            
            # Remove None values
            processed_crypto_data = {k: v for k, v in processed_crypto_data.items() if v is not None}
            
            processed_data["cryptocurrencies"][symbol] = processed_crypto_data
        
        # Process news data if present
        if "news" in data:
            processed_data["news"] = {
                "total": data["news"].get("total", 0),
                "tags": {}
            }
            
            for tag, tag_data in data["news"].get("tags", {}).items():
                if "error" in tag_data:
                    processed_data["news"]["tags"][tag] = tag_data
                    continue
                    
                processed_articles = []
                
                for article in tag_data.get("articles", []):
                    processed_article = {
                        "headline": article.get("headline"),
                        "link": article.get("link"),
                        "timestamp": self._normalize_news_timestamp(article.get("timestamp")),
                        "summary": self._clean_text(article.get("summary")),
                        "image_url": article.get("image_url"),
                        "author": self._clean_text(article.get("author")),
                        "tags": article.get("tags", [])
                    }
                    
                    # Remove None values
                    processed_article = {k: v for k, v in processed_article.items() if v is not None}
                    
                    processed_articles.append(processed_article)
                
                processed_data["news"]["tags"][tag] = {
                    "total": len(processed_articles),
                    "articles": processed_articles
                }
        
        return processed_data
    
    def normalize(self, data: Dict) -> Dict:
        """
        Normalize data formats across different sources.
        
        Args:
            data: Dictionary containing data from different sources
            
        Returns:
            Normalized data dictionary
        """
        # This is a simplified version of the process method
        # that only normalizes data formats without additional processing
        return self.process(data)
    
    def handle_missing_values(self, data: Dict, strategy: str = 'none') -> Dict:
        """
        Handle missing values in the data.
        
        Args:
            data: Dictionary containing data
            strategy: Strategy for handling missing values ('none', 'mean', 'median', 'zero')
            
        Returns:
            Data dictionary with missing values handled
        """
        if strategy == 'none':
            return data
            
        result = {}
        
        for source, source_data in data.items():
            if isinstance(source_data, dict):
                result[source] = self._handle_missing_values_dict(source_data, strategy)
            elif isinstance(source_data, list):
                result[source] = self._handle_missing_values_list(source_data, strategy)
            else:
                result[source] = source_data
        
        return result
    
    def _handle_missing_values_dict(self, data: Dict, strategy: str) -> Dict:
        """
        Handle missing values in a dictionary.
        
        Args:
            data: Dictionary containing data
            strategy: Strategy for handling missing values
            
        Returns:
            Dictionary with missing values handled
        """
        result = {}
        
        for key, value in data.items():
            if isinstance(value, dict):
                result[key] = self._handle_missing_values_dict(value, strategy)
            elif isinstance(value, list):
                result[key] = self._handle_missing_values_list(value, strategy)
            elif value is None:
                # Apply strategy for missing values
                if strategy == 'zero':
                    result[key] = 0
                else:
                    result[key] = value
            else:
                result[key] = value
        
        return result
    
    def _handle_missing_values_list(self, data: List, strategy: str) -> List:
        """
        Handle missing values in a list.
        
        Args:
            data: List containing data
            strategy: Strategy for handling missing values
            
        Returns:
            List with missing values handled
        """
        result = []
        
        for item in data:
            if isinstance(item, dict):
                result.append(self._handle_missing_values_dict(item, strategy))
            elif isinstance(item, list):
                result.append(self._handle_missing_values_list(item, strategy))
            else:
                result.append(item)
        
        return result
    
    def to_dataframe(self, data: Dict, source: str) -> pd.DataFrame:
        """
        Convert processed data to a pandas DataFrame.
        
        Args:
            data: Processed data dictionary
            source: Source of the data ('yahoo_finance', 'cnbc', 'cointelegraph')
            
        Returns:
            DataFrame with the data
        """
        if source == 'yahoo_finance':
            return self._yahoo_finance_to_dataframe(data)
        elif source == 'cnbc':
            return self._cnbc_to_dataframe(data)
        elif source == 'cointelegraph':
            return self._cointelegraph_to_dataframe(data)
        else:
            logger.warning(f"Unknown source: {source}")
            return pd.DataFrame()
    
    def _yahoo_finance_to_dataframe(self, data: Dict) -> pd.DataFrame:
        """Convert Yahoo Finance data to DataFrame."""
        rows = []
        
        for symbol, symbol_data in data.items():
            if "error" in symbol_data:
                continue
                
            row = {
                "symbol": symbol,
                "timestamp": symbol_data.get("timestamp"),
                "price": symbol_data.get("price"),
                "change": symbol_data.get("change"),
                "change_percent": symbol_data.get("change_percent"),
                "volume": symbol_data.get("volume"),
                "market_cap": symbol_data.get("market_cap"),
                "pe_ratio": symbol_data.get("pe_ratio"),
                "dividend_yield": symbol_data.get("dividend_yield")
            }
            
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def _cnbc_to_dataframe(self, data: Dict) -> pd.DataFrame:
        """Convert CNBC news data to DataFrame."""
        rows = []
        
        for category, category_data in data.get("categories", {}).items():
            if "error" in category_data:
                continue
                
            for article in category_data.get("articles", []):
                row = {
                    "category": category,
                    "headline": article.get("headline"),
                    "link": article.get("link"),
                    "timestamp": article.get("timestamp"),
                    "summary": article.get("summary"),
                    "author": article.get("author")
                }
                
                rows.append(row)
        
        return pd.DataFrame(rows)
    
    def _cointelegraph_to_dataframe(self, data: Dict) -> Dict[str, pd.DataFrame]:
        """
        Convert CoinTelegraph data to DataFrames.
        
        Returns a dictionary with two keys:
        - 'prices': DataFrame with cryptocurrency price data
        - 'news': DataFrame with news data
        """
        result = {}
        
        # Convert cryptocurrency data
        crypto_rows = []
        for symbol, crypto_data in data.get("cryptocurrencies", {}).items():
            if "error" in crypto_data:
                continue
                
            row = {
                "symbol": symbol,
                "name": crypto_data.get("name"),
                "price": crypto_data.get("price"),
                "market_cap": crypto_data.get("market_cap"),
                "volume_24h": crypto_data.get("volume_24h"),
                "change_24h": crypto_data.get("change_24h"),
                "change_7d": crypto_data.get("change_7d"),
                "last_updated": crypto_data.get("last_updated")
            }
            
            crypto_rows.append(row)
        
        result["prices"] = pd.DataFrame(crypto_rows)
        
        # Convert news data
        news_rows = []
        for tag, tag_data in data.get("news", {}).get("tags", {}).items():
            if "error" in tag_data:
                continue
                
            for article in tag_data.get("articles", []):
                row = {
                    "tag": tag,
                    "headline": article.get("headline"),
                    "link": article.get("link"),
                    "timestamp": article.get("timestamp"),
                    "summary": article.get("summary"),
                    "author": article.get("author")
                }
                
                news_rows.append(row)
        
        result["news"] = pd.DataFrame(news_rows)
        
        return result
    
    @staticmethod
    def _normalize_timestamp(timestamp: Optional[str]) -> Optional[str]:
        """
        Normalize timestamp to ISO format.
        
        Args:
            timestamp: Timestamp string
            
        Returns:
            Normalized timestamp string
        """
        if not timestamp:
            return datetime.now().isoformat()
            
        try:
            if isinstance(timestamp, str):
                # Try to parse the timestamp
                dt = pd.to_datetime(timestamp)
                return dt.isoformat()
            elif isinstance(timestamp, (int, float)):
                # Assume Unix timestamp
                dt = datetime.fromtimestamp(timestamp)
                return dt.isoformat()
            else:
                return str(timestamp)
        except Exception as e:
            logger.debug(f"Error normalizing timestamp {timestamp}: {e}")
            return datetime.now().isoformat()
    
    @staticmethod
    def _normalize_news_timestamp(timestamp: Optional[str]) -> Optional[str]:
        """
        Normalize news timestamp to ISO format.
        
        Args:
            timestamp: Timestamp string from news article
            
        Returns:
            Normalized timestamp string
        """
        if not timestamp:
            return None
            
        try:
            # Common formats in news articles
            formats = [
                "%b %d, %Y",  # Jan 01, 2023
                "%B %d, %Y",  # January 01, 2023
                "%m/%d/%Y",   # 01/01/2023
                "%Y-%m-%d",   # 2023-01-01
                "%d %b %Y",   # 01 Jan 2023
                "%d %B %Y",   # 01 January 2023
                "%a, %b %d",  # Mon, Jan 01
                "%A, %B %d"   # Monday, January 01
            ]
            
            # Try each format
            for fmt in formats:
                try:
                    dt = datetime.strptime(timestamp, fmt)
                    # If year is missing, add current year
                    if dt.year == 1900:
                        dt = dt.replace(year=datetime.now().year)
                    return dt.isoformat()
                except ValueError:
                    continue
            
            # If none of the formats match, try pandas
            dt = pd.to_datetime(timestamp)
            return dt.isoformat()
        except Exception as e:
            logger.debug(f"Error normalizing news timestamp {timestamp}: {e}")
            return None
    
    @staticmethod
    def _normalize_numeric(value: Any) -> Optional[float]:
        """
        Normalize numeric value.
        
        Args:
            value: Value to normalize
            
        Returns:
            Normalized numeric value
        """
        if value is None:
            return None
            
        try:
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, str):
                # Remove any non-numeric characters except for the decimal point and minus sign
                value = re.sub(r'[^\d.-]', '', value)
                return float(value)
            else:
                return float(value)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def _normalize_percent(value: Any) -> Optional[float]:
        """
        Normalize percentage value.
        
        Args:
            value: Value to normalize
            
        Returns:
            Normalized percentage value (as a decimal, e.g., 0.05 for 5%)
        """
        if value is None:
            return None
            
        try:
            if isinstance(value, (int, float)):
                # Assume it's already a decimal
                return float(value)
            elif isinstance(value, str):
                # Remove any non-numeric characters except for the decimal point and minus sign
                value = re.sub(r'[^\d.-]', '', value)
                # Convert to decimal
                return float(value) / 100
            else:
                return float(value)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def _clean_text(text: Optional[str]) -> Optional[str]:
        """
        Clean text by removing extra whitespace and normalizing.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return None
            
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text