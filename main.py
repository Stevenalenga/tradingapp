#!/usr/bin/env python3
"""
Main module for the Trading Information Scraper application.

This module provides the entry point for the application and ties all components together.
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from processors.data_processor import DataProcessor
from scrapers.cnbc import CNBCScraper
from scrapers.cointelegraph import CoinTelegraphScraper
from scrapers.yahoo_finance import YahooFinanceScraper
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