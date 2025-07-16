# Trading Information Scraper Documentation

This documentation provides comprehensive information about the Trading Information Scraper application, including installation instructions, usage guidelines, API reference, and development information.

## Table of Contents

1. [Installation](#installation)
2. [Usage](#usage)
3. [Configuration](#configuration)
4. [API Reference](#api-reference)
5. [Development](#development)
6. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (optional, for cloning the repository)

### Installation Steps

1. Clone the repository or download the source code:
   ```bash
   git clone https://github.com/yourusername/tradingapp.git
   cd tradingapp
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

To start the application with default settings:

```bash
python main.py
```

This will:
- Scrape data from all configured sources
- Process and store the data
- Generate basic visualizations

### Command-line Arguments

The application supports several command-line arguments:

```bash
python main.py --sources yahoo,cnbc --output csv --schedule daily
```

Available arguments:
- `--sources`: Comma-separated list of sources to scrape (default: all)
- `--output`: Output format (csv, sqlite, json) (default: csv)
- `--schedule`: Scheduling frequency (once, hourly, daily) (default: once)
- `--config`: Path to custom configuration file
- `--verbose`: Enable verbose logging

### Using as a Library

You can also use the components as a library in your own Python code:

```python
from tradingapp.scrapers import YahooFinanceScraper
from tradingapp.processors import DataProcessor
from tradingapp.storage import CSVStorage

# Initialize scraper
scraper = YahooFinanceScraper()

# Scrape data
data = scraper.scrape(symbols=['AAPL', 'MSFT', 'GOOGL'])

# Process data
processor = DataProcessor()
processed_data = processor.process(data)

# Store data
storage = CSVStorage(output_dir='./data')
storage.store(processed_data, filename='stock_data')
```

## Configuration

The application can be configured using a configuration file or environment variables.

### Configuration File

Create a `config.yaml` file in the root directory:

```yaml
sources:
  yahoo_finance:
    enabled: true
    symbols: ['AAPL', 'MSFT', 'GOOGL', 'AMZN']
    data_points: ['price', 'volume', 'market_cap', 'pe_ratio']
  
  cnbc:
    enabled: true
    categories: ['markets', 'business', 'investing']
    max_articles: 50
  
  cointelegraph:
    enabled: true
    cryptocurrencies: ['BTC', 'ETH', 'XRP', 'ADA']
    include_news: true

storage:
  type: 'sqlite'  # 'csv', 'sqlite', or 'json'
  path: './data'
  
scheduling:
  frequency: 'daily'  # 'once', 'hourly', 'daily'
  time: '09:00'  # For 'daily' frequency
  
logging:
  level: 'INFO'  # 'DEBUG', 'INFO', 'WARNING', 'ERROR'
  file: './logs/app.log'
```

### Environment Variables

You can also use environment variables to configure the application:

```bash
export TRADINGAPP_SOURCES=yahoo,cnbc
export TRADINGAPP_STORAGE_TYPE=sqlite
export TRADINGAPP_SCHEDULE=daily
```

## API Reference

### Scrapers

#### YahooFinanceScraper

```python
from tradingapp.scrapers import YahooFinanceScraper

scraper = YahooFinanceScraper()
data = scraper.scrape(symbols=['AAPL', 'MSFT'])
```

Methods:
- `scrape(symbols, data_points=None)`: Scrape data for the specified symbols
- `get_historical_data(symbol, start_date, end_date)`: Get historical data for a symbol

#### CNBCScraper

```python
from tradingapp.scrapers import CNBCScraper

scraper = CNBCScraper()
news = scraper.scrape_news(categories=['markets', 'investing'])
```

Methods:
- `scrape_news(categories=None, max_articles=50)`: Scrape news articles
- `scrape_market_data()`: Scrape market data

#### CoinTelegraphScraper

```python
from tradingapp.scrapers import CoinTelegraphScraper

scraper = CoinTelegraphScraper()
crypto_data = scraper.scrape(cryptocurrencies=['BTC', 'ETH'])
```

Methods:
- `scrape(cryptocurrencies, include_news=True)`: Scrape cryptocurrency data
- `scrape_news(tags=None, max_articles=50)`: Scrape cryptocurrency news

### Processors

#### DataProcessor

```python
from tradingapp.processors import DataProcessor

processor = DataProcessor()
processed_data = processor.process(data)
```

Methods:
- `process(data)`: Process and clean data
- `normalize(data)`: Normalize data formats
- `handle_missing_values(data, strategy='mean')`: Handle missing values

### Storage

#### CSVStorage

```python
from tradingapp.storage import CSVStorage

storage = CSVStorage(output_dir='./data')
storage.store(data, filename='stock_data')
```

Methods:
- `store(data, filename)`: Store data to a CSV file
- `load(filename)`: Load data from a CSV file

#### SQLiteStorage

```python
from tradingapp.storage import SQLiteStorage

storage = SQLiteStorage(db_path='./data/trading.db')
storage.store(data, table_name='stocks')
```

Methods:
- `store(data, table_name)`: Store data to a SQLite table
- `load(table_name, conditions=None)`: Load data from a SQLite table
- `execute_query(query, params=None)`: Execute a custom SQL query

### Visualization

#### DataVisualizer

```python
from tradingapp.visualization import DataVisualizer

visualizer = DataVisualizer()
visualizer.plot_time_series(data, x='date', y='price', title='Stock Price')
```

Methods:
- `plot_time_series(data, x, y, title=None)`: Plot time series data
- `plot_comparison(data, x, y_list, title=None)`: Plot comparison of multiple series
- `plot_distribution(data, column, title=None)`: Plot distribution of values
- `save_plot(filename, format='png')`: Save the current plot to a file

## Development

### Setting Up Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/tradingapp.git
   cd tradingapp
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

### Running Tests

Run the test suite:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=tradingapp
```

### Code Style

This project follows PEP 8 style guidelines. You can check your code style with:

```bash
flake8 tradingapp
```

Format your code with:

```bash
black tradingapp
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests: `pytest`
5. Commit your changes: `git commit -m 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

## Troubleshooting

### Common Issues

#### Rate Limiting

If you encounter rate limiting issues:

1. Reduce the frequency of requests
2. Implement proxy rotation
3. Use a delay between requests

#### Data Format Changes

If website data formats change:

1. Check the scraper implementation
2. Update the CSS selectors or XPath expressions
3. Adapt the data processing logic

#### Installation Issues

If you encounter installation issues:

1. Ensure you have the correct Python version
2. Check for any missing system dependencies
3. Try installing dependencies one by one to identify problematic packages

### Getting Help

If you need help:

1. Check the documentation
2. Look for similar issues in the issue tracker
3. Create a new issue with detailed information about your problem