# Project Dependencies

This document lists all the dependencies required for the Trading Information Scraper project. When implementing the project in Code mode, these dependencies should be added to a `requirements.txt` file.

## Core Dependencies

### Web Scraping
- **beautifulsoup4>=4.9.3**: For parsing HTML and XML documents
- **requests>=2.25.1**: For making HTTP requests
- **selenium>=4.0.0**: For browser automation (JavaScript-heavy sites)
- **lxml>=4.6.3**: For faster HTML parsing
- **html5lib>=1.1**: For parsing complex HTML5
- **webdriver-manager>=3.5.2**: For managing Selenium WebDriver

### Data Processing
- **pandas>=1.3.0**: For data manipulation and analysis
- **numpy>=1.20.0**: For numerical operations
- **python-dateutil>=2.8.2**: For date parsing and manipulation

### Data Storage
- **sqlalchemy>=1.4.0**: For database operations
- **pymysql>=1.0.2**: For MySQL connections (optional)
- **psycopg2-binary>=2.9.1**: For PostgreSQL connections (optional)

### Data Visualization
- **matplotlib>=3.4.0**: For creating static visualizations
- **seaborn>=0.11.1**: For statistical visualizations
- **plotly>=5.1.0**: For interactive visualizations (optional)

### Scheduling
- **apscheduler>=3.7.0**: For scheduling tasks
- **schedule>=1.1.0**: For simple scheduling (alternative)

### Utilities
- **pyyaml>=6.0**: For YAML configuration files
- **python-dotenv>=0.19.0**: For environment variable management
- **tqdm>=4.62.0**: For progress bars
- **colorama>=0.4.4**: For colored terminal output
- **click>=8.0.1**: For command-line interfaces

## Development Dependencies

### Testing
- **pytest>=6.2.5**: For unit and integration testing
- **pytest-cov>=2.12.1**: For test coverage reporting
- **vcrpy>=4.1.1**: For recording and replaying HTTP interactions
- **pytest-mock>=3.6.1**: For mocking in tests
- **pytest-benchmark>=3.4.1**: For performance testing

### Code Quality
- **flake8>=3.9.2**: For code style checking
- **black>=21.6b0**: For code formatting
- **isort>=5.9.2**: For import sorting
- **mypy>=0.910**: For static type checking
- **bandit>=1.7.0**: For security vulnerability checking

### Documentation
- **sphinx>=4.1.1**: For generating documentation
- **sphinx-rtd-theme>=0.5.2**: For documentation theme
- **sphinx-autodoc-typehints>=1.12.0**: For type hints in documentation

## Installation Instructions

When implementing the project, create a `requirements.txt` file with the appropriate version constraints. You may also want to create a separate `requirements-dev.txt` file for development dependencies.

Example installation:

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

## Version Management

It's recommended to use specific versions or version ranges to ensure reproducibility. The versions listed above are minimum recommended versions as of the project creation date.