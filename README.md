# Trading Information Scraper

A Python application that scrapes trading information from Yahoo Finance, CNBC, and CoinTelegraph for stock and cryptocurrency data.

## Overview

This application provides a comprehensive solution for collecting, processing, storing, and visualizing financial data from multiple sources. It is designed to be modular, extensible, and configurable to meet various financial data collection needs.

### Key Features

- **Multi-source Data Collection**: Scrape data from Yahoo Finance, CNBC, and CoinTelegraph
- **Flexible Data Processing**: Clean, normalize, and transform data from different sources
- **Multiple Storage Options**: Store data in CSV, SQLite, or JSON formats
- **Data Visualization**: Generate charts and graphs for data analysis
- **Scheduled Execution**: Automate data collection at configurable intervals
- **Robust Error Handling**: Gracefully handle network issues, rate limiting, and site changes

## Project Structure

```
tradingapp/
├── scrapers/         # Web scraping modules for different sources
├── processors/       # Data processing and transformation modules
├── storage/          # Data storage modules for different formats
├── visualization/    # Data visualization modules
├── utils/            # Utility functions and helpers
├── tests/            # Test modules and fixtures
├── docs/             # Documentation
├── scheduler.py      # Scheduling functionality
├── main.py           # Main application entry point
├── requirements.txt  # Project dependencies
└── README.md         # This file
```

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/tradingapp.git
cd tradingapp

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
# Run with default settings
python main.py

# Specify sources and output format
python main.py --sources yahoo,cnbc --output csv

# Schedule daily execution
python main.py --schedule daily
```

## Documentation

For detailed documentation, please refer to:

- [User Guide](docs/README.md): Comprehensive usage documentation
- [Project Plan](project_plan.md): Detailed project architecture and implementation plan
- [Test Plan](tests/test_plan.md): Testing strategy and test cases

## Development

### Setting Up Development Environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Check code style
flake8 tradingapp

# Format code
black tradingapp
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.