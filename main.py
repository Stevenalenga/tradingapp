
import argparse
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import numpy as np

from processors.data_processor import DataProcessor
from scrapers.cnbc import CNBCScraper
from scrapers.cointelegraph import CoinTelegraphScraper
from scrapers.yahoo_finance import YahooFinanceScraper
from scrapers.coindesk import CoinDeskScraper
from scrapers.coingecko import CoinGeckoScraper
from scrapers.cryptoslate import CryptoSlateScraper
from scrapers.coinmarketcap import CoinMarketCapScraper
from scrapers.cryptopanic import CryptoPanicScraper
from scrapers.alternative_me import AlternativeMeScraper
from scheduler import Scheduler
from storage.csv_storage import CSVStorage
from storage.json_storage import JSONStorage
from storage.sqlite_storage import SQLiteStorage
from utils.config import Config
from utils.logger import setup_logger
from visualization.data_visualizer import DataVisualizer


class TradingApp:
    """
    Main application class for the Trading Information Scraper.
    
    This class coordinates all components of the application.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the application.
        
        Args:
            config_path: Path to the configuration file
        """
        # Set up configuration
        self.config = Config(config_path)
        
        # If no configuration file was provided or found, create a default one
        if not self.config.config:
            default_config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
            self.config.create_default_config(default_config_path)
        
        # Set up logging
        log_level = self.config.get('logging.level', 'INFO')
        log_file = self.config.get('logging.file', './logs/app.log')
        self.logger = setup_logger('tradingapp', log_level, log_file)
        
        # Initialize components
        self._init_components()
        
        self.logger.info("Trading Information Scraper initialized")
    
    def _init_components(self):
        """Initialize application components."""
        # Initialize scrapers
        self.scrapers = {}
        if self.config.get('sources.yahoo_finance.enabled', True):
            self.scrapers['yahoo_finance'] = YahooFinanceScraper()
        
        if self.config.get('sources.cnbc.enabled', True):
            self.scrapers['cnbc'] = CNBCScraper()
        
        if self.config.get('sources.cointelegraph.enabled', True):
            self.scrapers['cointelegraph'] = CoinTelegraphScraper()
        
        if self.config.get('sources.coindesk.enabled', False):
            self.scrapers['coindesk'] = CoinDeskScraper()
        
        if self.config.get('sources.coingecko.enabled', False):
            self.scrapers['coingecko'] = CoinGeckoScraper()
        
        if self.config.get('sources.cryptoslate.enabled', False):
            self.scrapers['cryptoslate'] = CryptoSlateScraper()
        
        if self.config.get('sources.coinmarketcap.enabled', False):
            self.scrapers['coinmarketcap'] = CoinMarketCapScraper()
        
        if self.config.get('sources.cryptopanic.enabled', False):
            api_key = self.config.get('sources.cryptopanic.api_key')
            self.scrapers['cryptopanic'] = CryptoPanicScraper(api_key=api_key)
        
        if self.config.get('sources.alternative_me.enabled', False):
            self.scrapers['alternative_me'] = AlternativeMeScraper()
        
        # Initialize processor
        self.processor = DataProcessor()
        
        # Initialize storage
        storage_type = self.config.get('storage.type', 'csv')
        storage_path = self.config.get('storage.path', './data')
        
        if storage_type == 'csv':
            self.storage = CSVStorage(storage_path)
        elif storage_type == 'sqlite':
            self.storage = SQLiteStorage(os.path.join(storage_path, 'trading.db'))
        elif storage_type == 'json':
            self.storage = JSONStorage(storage_path)
        else:
            self.logger.warning(f"Unknown storage type: {storage_type}, using CSV")
            self.storage = CSVStorage(storage_path)
        
        # Initialize visualizer
        self.visualizer = DataVisualizer('./visualizations')
        
        # Initialize scheduler
        self.scheduler = Scheduler()
    
    def run(self, sources: Optional[List[str]] = None, schedule: str = 'once'):
        """
        Run the application.
        
        Args:
            sources: List of sources to scrape (if None, use all enabled sources)
            schedule: Scheduling frequency ('once', 'hourly', 'daily')
        """
        try:
            # Start the scheduler
            self.scheduler.start()
            
            # Determine which sources to scrape
            if not sources:
                sources = list(self.scrapers.keys())
            else:
                # Filter out sources that are not available
                sources = [s for s in sources if s in self.scrapers]
            
            if not sources:
                self.logger.warning("No valid sources specified")
                return
            
            # Schedule the scraping task
            self.scheduler.schedule_task(
                self.scrape_and_process,
                frequency=schedule,
                time=self.config.get('scheduling.time', '09:00'),
                sources=sources
            )
            
            # If running once, wait for the task to complete and then exit
            if schedule == 'once':
                # The task is scheduled to run immediately, so we just need to wait a bit
                import time
                time.sleep(5)
                self.scheduler.shutdown()
            else:
                # For scheduled tasks, keep the application running
                self.logger.info(f"Application running with {schedule} schedule. Press Ctrl+C to exit.")
                
                # Keep the main thread alive
                import threading
                event = threading.Event()
                try:
                    event.wait()
                except KeyboardInterrupt:
                    self.logger.info("Keyboard interrupt received, shutting down")
                    self.scheduler.shutdown()
        
        except Exception as e:
            self.logger.error(f"Error running application: {e}")
            self.scheduler.shutdown()
            raise
    
    def scrape_and_process(self, sources: List[str]) -> Dict:
        """
        Scrape data from sources, process it, and store it.
        
        Args:
            sources: List of sources to scrape
            
        Returns:
            Dictionary with results
        """
        self.logger.info(f"Scraping data from sources: {sources}")
        
        results = {}
        
        try:
            # Scrape data from each source
            scraped_data = {}
            
            for source in sources:
                try:
                    if source == 'yahoo_finance':
                        symbols = self.config.get('sources.yahoo_finance.symbols', ['AAPL', 'MSFT', 'GOOGL', 'AMZN'])
                        data_points = self.config.get('sources.yahoo_finance.data_points')
                        scraped_data[source] = self.scrapers[source].scrape(symbols, data_points)
                    
                    elif source == 'cnbc':
                        categories = self.config.get('sources.cnbc.categories', ['markets', 'business', 'investing'])
                        max_articles = self.config.get('sources.cnbc.max_articles', 50)
                        scraped_data[source] = self.scrapers[source].scrape(categories, max_articles)
                    
                    elif source == 'cointelegraph':
                        cryptocurrencies = self.config.get('sources.cointelegraph.cryptocurrencies', ['BTC', 'ETH', 'XRP', 'ADA'])
                        include_news = self.config.get('sources.cointelegraph.include_news', True)
                        scraped_data[source] = self.scrapers[source].scrape(cryptocurrencies, include_news)
                    
                    elif source == 'coindesk':
                        cryptocurrencies = self.config.get('sources.coindesk.cryptocurrencies', ['BTC'])
                        include_news = self.config.get('sources.coindesk.include_news', True)
                        max_articles = self.config.get('sources.coindesk.max_articles', 20)
                        scraped_data[source] = self.scrapers[source].scrape(cryptocurrencies, include_news, max_articles)
                    
                    elif source == 'coingecko':
                        cryptocurrencies = self.config.get('sources.coingecko.cryptocurrencies', ['BTC', 'ETH', 'XRP', 'ADA'])
                        include_market_data = self.config.get('sources.coingecko.include_market_data', True)
                        include_trending = self.config.get('sources.coingecko.include_trending', False)
                        scraped_data[source] = self.scrapers[source].scrape(cryptocurrencies, include_market_data, include_trending)
                    
                    elif source == 'cryptoslate':
                        include_news = self.config.get('sources.cryptoslate.include_news', True)
                        include_market_data = self.config.get('sources.cryptoslate.include_market_data', True)
                        max_articles = self.config.get('sources.cryptoslate.max_articles', 30)
                        scraped_data[source] = self.scrapers[source].scrape(include_news, include_market_data, max_articles)
                    
                    elif source == 'coinmarketcap':
                        cryptocurrencies = self.config.get('sources.coinmarketcap.cryptocurrencies')
                        max_coins = self.config.get('sources.coinmarketcap.max_coins', 100)
                        scraped_data[source] = self.scrapers[source].scrape(cryptocurrencies, max_coins)
                    
                    elif source == 'cryptopanic':
                        cryptocurrencies = self.config.get('sources.cryptopanic.cryptocurrencies')
                        kind = self.config.get('sources.cryptopanic.kind', 'news')
                        filter_sentiment = self.config.get('sources.cryptopanic.filter_sentiment')
                        max_posts = self.config.get('sources.cryptopanic.max_posts', 50)
                        scraped_data[source] = self.scrapers[source].scrape(cryptocurrencies, kind, filter_sentiment, max_posts)
                    
                    elif source == 'alternative_me':
                        days = self.config.get('sources.alternative_me.days', 30)
                        include_historical = self.config.get('sources.alternative_me.include_historical', True)
                        scraped_data[source] = self.scrapers[source].scrape(days, include_historical)
                    
                    self.logger.info(f"Successfully scraped data from {source}")
                except Exception as e:
                    self.logger.error(f"Error scraping data from {source}: {e}")
                    scraped_data[source] = {"error": str(e)}
            
            # Process the scraped data
            processed_data = self.processor.process(scraped_data)
            
            # Store the processed data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            for source, data in processed_data.items():
                try:
                    if source == 'yahoo_finance':
                        # Convert to DataFrame and store
                        df = self.processor.to_dataframe(data, source)
                        filename = f"stocks_{timestamp}"
                        filepath = self.storage.store(df, filename)
                        results[source] = {"status": "success", "filepath": filepath}
                        
                        # Create visualizations
                        if not df.empty:
                            # Plot stock prices
                            fig = self.visualizer.plot_bar(
                                df,
                                'symbol',
                                'price',
                                title='Stock Prices',
                                xlabel='Symbol',
                                ylabel='Price ($)'
                            )
                            self.visualizer.save_plot(fig, f"stock_prices_{timestamp}.png")
                            
                            # Plot market cap
                            if 'market_cap' in df.columns:
                                fig = self.visualizer.plot_bar(
                                    df,
                                    'symbol',
                                    'market_cap',
                                    title='Market Capitalization',
                                    xlabel='Symbol',
                                    ylabel='Market Cap ($)'
                                )
                                self.visualizer.save_plot(fig, f"market_cap_{timestamp}.png")
                    
                    elif source == 'cnbc':
                        # Store news data
                        filename = f"news_{timestamp}"
                        filepath = self.storage.store(data, filename)
                        results[source] = {"status": "success", "filepath": filepath}
                    
                    elif source == 'cointelegraph':
                        # Store cryptocurrency data
                        filename = f"crypto_{timestamp}"
                        filepath = self.storage.store(data, filename)
                        results[source] = {"status": "success", "filepath": filepath}
                        
                        # Create visualizations for cryptocurrency data
                        if 'cryptocurrencies' in data:
                            crypto_data = []
                            for symbol, crypto in data['cryptocurrencies'].items():
                                if isinstance(crypto, dict) and 'price' in crypto:
                                    crypto_data.append({
                                        'symbol': symbol,
                                        'price': crypto.get('price'),
                                        'market_cap': crypto.get('market_cap'),
                                        'volume_24h': crypto.get('volume_24h'),
                                        'change_24h': crypto.get('change_24h')
                                    })
                            
                            if crypto_data:
                                df = pd.DataFrame(crypto_data)
                                
                                # Plot cryptocurrency prices
                                fig = self.visualizer.plot_bar(
                                    df,
                                    'symbol',
                                    'price',
                                    title='Cryptocurrency Prices',
                                    xlabel='Symbol',
                                    ylabel='Price ($)'
                                )
                                self.visualizer.save_plot(fig, f"crypto_prices_{timestamp}.png")
                                
                                # Plot 24h change
                                if 'change_24h' in df.columns:
                                    fig = self.visualizer.plot_bar(
                                        df,
                                        'symbol',
                                        'change_24h',
                                        title='24h Price Change',
                                        xlabel='Symbol',
                                        ylabel='Change (%)'
                                    )
                                    self.visualizer.save_plot(fig, f"crypto_change_{timestamp}.png")
                
                    elif source in ['coindesk', 'coingecko', 'cryptoslate', 'coinmarketcap', 'cryptopanic', 'alternative_me']:
                        # Handle new cryptocurrency data sources
                        filename = f"{source}_{timestamp}"
                        filepath = self.storage.store(data, filename)
                        results[source] = {"status": "success", "filepath": filepath}
                        
                        # Create visualizations for cryptocurrency data
                        if source in ['coindesk', 'coingecko', 'coinmarketcap'] and 'cryptocurrencies' in data:
                            crypto_data = []
                            cryptocurrencies = data['cryptocurrencies']
                            
                            for symbol, crypto in cryptocurrencies.items():
                                if isinstance(crypto, dict) and ('price' in crypto or 'current_price' in crypto):
                                    price = crypto.get('price') or crypto.get('current_price', 0)
                                    crypto_data.append({
                                        'symbol': symbol,
                                        'price': price,
                                        'market_cap': crypto.get('market_cap', 0),
                                        'volume_24h': crypto.get('volume_24h') or crypto.get('total_volume', 0),
                                        'change_24h': crypto.get('change_24h') or crypto.get('price_change_percentage_24h', 0)
                                    })
                            
                            if crypto_data:
                                df = pd.DataFrame(crypto_data)
                                
                                # Plot cryptocurrency prices
                                fig = self.visualizer.plot_bar(
                                    df,
                                    'symbol',
                                    'price',
                                    title=f'Cryptocurrency Prices ({source.title()})',
                                    xlabel='Symbol',
                                    ylabel='Price ($)'
                                )
                                self.visualizer.save_plot(fig, f"{source}_prices_{timestamp}.png")
                                
                                # Plot 24h change if available
                                if 'change_24h' in df.columns and df['change_24h'].sum() != 0:
                                    fig = self.visualizer.plot_bar(
                                        df,
                                        'symbol',
                                        'change_24h',
                                        title=f'24h Price Change ({source.title()})',
                                        xlabel='Symbol',
                                        ylabel='Change (%)'
                                    )
                                    self.visualizer.save_plot(fig, f"{source}_change_{timestamp}.png")
                        
                        # Special handling for Alternative.me Fear & Greed Index
                        elif source == 'alternative_me' and 'fear_greed_index' in data:
                            fg_data = data['fear_greed_index']
                            if 'current' in fg_data and 'value' in fg_data['current']:
                                current_value = fg_data['current']['value']
                                classification = fg_data['current'].get('value_classification', '')
                                
                                # Create a simple visualization for Fear & Greed Index
                                import matplotlib.pyplot as plt
                                fig, ax = plt.subplots(figsize=(8, 6))
                                
                                # Create a gauge-like visualization
                                colors = ['red', 'orange', 'yellow', 'lightgreen', 'green']
                                values = [25, 25, 10, 15, 25]  # Segments for Extreme Fear, Fear, Neutral, Greed, Extreme Greed
                                labels = ['Extreme Fear', 'Fear', 'Neutral', 'Greed', 'Extreme Greed']
                                
                                wedges, texts = ax.pie(values, labels=labels, colors=colors, startangle=180, counterclock=False)
                                
                                # Add current value indicator
                                angle = 180 - (current_value / 100) * 180
                                ax.annotate('', xy=(0.7 * np.cos(np.radians(angle)), 0.7 * np.sin(np.radians(angle))), 
                                          xytext=(0, 0), arrowprops=dict(arrowstyle='->', lw=3, color='black'))
                                
                                ax.set_title(f'Fear & Greed Index: {current_value} ({classification})', fontsize=14, fontweight='bold')
                                
                                self.visualizer.save_plot(fig, f"fear_greed_index_{timestamp}.png")
                                plt.close(fig)
                
                except Exception as e:
                    self.logger.error(f"Error storing and visualizing data for {source}: {e}")
                    results[source] = {"status": "error", "error": str(e)}
            
            self.logger.info("Data scraping, processing, and storage completed")
            
            return results
        
        except Exception as e:
            self.logger.error(f"Error in scrape_and_process: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_available_sources(self) -> List[str]:
        """
        Get a list of available data sources.
        
        Returns:
            List of source names
        """
        return list(self.scrapers.keys())


def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Trading Information Scraper')
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--sources',
        type=str,
        help='Comma-separated list of sources to scrape (default: all)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        choices=['csv', 'sqlite', 'json'],
        help='Output format (default: from config)'
    )
    
    parser.add_argument(
        '--schedule',
        type=str,
        choices=['once', 'hourly', 'daily'],
        default='once',
        help='Scheduling frequency (default: once)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the application."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Set up logging level based on verbose flag
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger('tradingapp', log_level)
    
    try:
        # Initialize the application
        app = TradingApp(args.config)
        
        # Override configuration with command-line arguments
        if args.output:
            app.config.set('storage.type', args.output)
        
        # Parse sources if provided
        sources = None
        if args.sources:
            sources = [s.strip() for s in args.sources.split(',')]
        
        # Run the application
        app.run(sources, args.schedule)
    
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()