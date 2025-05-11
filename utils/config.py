"""
Configuration module for the Trading Information Scraper application.

This module provides functionality for loading and managing configuration settings.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

import yaml

logger = logging.getLogger(__name__)


class Config:
    """
    Configuration manager for the application.
    
    This class provides methods for loading and accessing configuration settings
    from various sources (YAML, JSON, environment variables).
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file (YAML or JSON)
        """
        self.config_path = config_path
        self.config = {}
        
        if config_path:
            self.load_config(config_path)
        
        # Load environment variables
        self._load_env_vars()
    
    def load_config(self, config_path: str) -> bool:
        """
        Load configuration from a file.
        
        Args:
            config_path: Path to the configuration file (YAML or JSON)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.config_path = config_path
            
            if not os.path.exists(config_path):
                logger.warning(f"Configuration file not found: {config_path}")
                return False
                
            # Determine file type based on extension
            _, ext = os.path.splitext(config_path)
            
            if ext.lower() in ['.yaml', '.yml']:
                with open(config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
            elif ext.lower() == '.json':
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
            else:
                logger.warning(f"Unsupported configuration file format: {ext}")
                return False
                
            logger.info(f"Configuration loaded from {config_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            return False
    
    def save_config(self, config_path: Optional[str] = None) -> bool:
        """
        Save configuration to a file.
        
        Args:
            config_path: Path to save the configuration file (if None, use the current path)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            config_path = config_path or self.config_path
            
            if not config_path:
                logger.warning("No configuration path specified")
                return False
                
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
                
            # Determine file type based on extension
            _, ext = os.path.splitext(config_path)
            
            if ext.lower() in ['.yaml', '.yml']:
                with open(config_path, 'w') as f:
                    yaml.dump(self.config, f, default_flow_style=False)
            elif ext.lower() == '.json':
                with open(config_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
            else:
                logger.warning(f"Unsupported configuration file format: {ext}")
                return False
                
            logger.info(f"Configuration saved to {config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration to {config_path}: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key (can use dot notation for nested keys)
            default: Default value if the key is not found
            
        Returns:
            Configuration value or default
        """
        try:
            # Handle nested keys with dot notation
            if '.' in key:
                parts = key.split('.')
                value = self.config
                
                for part in parts:
                    if isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        return default
                        
                return value
            else:
                return self.config.get(key, default)
        except Exception as e:
            logger.debug(f"Error getting configuration value for {key}: {e}")
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key (can use dot notation for nested keys)
            value: Value to set
        """
        try:
            # Handle nested keys with dot notation
            if '.' in key:
                parts = key.split('.')
                config = self.config
                
                # Navigate to the nested dictionary
                for part in parts[:-1]:
                    if part not in config:
                        config[part] = {}
                    elif not isinstance(config[part], dict):
                        config[part] = {}
                        
                    config = config[part]
                    
                # Set the value in the nested dictionary
                config[parts[-1]] = value
            else:
                self.config[key] = value
        except Exception as e:
            logger.error(f"Error setting configuration value for {key}: {e}")
    
    def get_all(self) -> Dict:
        """
        Get the entire configuration.
        
        Returns:
            Configuration dictionary
        """
        return self.config
    
    def update(self, config: Dict) -> None:
        """
        Update the configuration with new values.
        
        Args:
            config: Dictionary with new configuration values
        """
        try:
            self._update_dict(self.config, config)
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
    
    def _update_dict(self, target: Dict, source: Dict) -> None:
        """
        Recursively update a dictionary with values from another dictionary.
        
        Args:
            target: Target dictionary to update
            source: Source dictionary with new values
        """
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                # Recursively update nested dictionaries
                self._update_dict(target[key], value)
            else:
                # Update or add the value
                target[key] = value
    
    def _load_env_vars(self) -> None:
        """Load configuration from environment variables."""
        try:
            # Look for environment variables with the TRADINGAPP_ prefix
            prefix = 'TRADINGAPP_'
            
            for key, value in os.environ.items():
                if key.startswith(prefix):
                    # Remove the prefix and convert to lowercase
                    config_key = key[len(prefix):].lower()
                    
                    # Handle nested keys with underscore notation
                    if '_' in config_key:
                        parts = config_key.split('_')
                        config = self.config
                        
                        # Navigate to the nested dictionary
                        for part in parts[:-1]:
                            if part not in config:
                                config[part] = {}
                            elif not isinstance(config[part], dict):
                                config[part] = {}
                                
                            config = config[part]
                            
                        # Set the value in the nested dictionary
                        config[parts[-1]] = self._parse_env_value(value)
                    else:
                        self.config[config_key] = self._parse_env_value(value)
        except Exception as e:
            logger.error(f"Error loading environment variables: {e}")
    
    @staticmethod
    def _parse_env_value(value: str) -> Any:
        """
        Parse an environment variable value.
        
        Args:
            value: String value from environment variable
            
        Returns:
            Parsed value (bool, int, float, or string)
        """
        # Convert to boolean if it's a boolean string
        if value.lower() in ['true', 'yes', '1']:
            return True
        elif value.lower() in ['false', 'no', '0']:
            return False
            
        # Convert to integer if it's an integer string
        try:
            return int(value)
        except ValueError:
            pass
            
        # Convert to float if it's a float string
        try:
            return float(value)
        except ValueError:
            pass
            
        # Return as string
        return value
    
    def create_default_config(self, config_path: str) -> bool:
        """
        Create a default configuration file.
        
        Args:
            config_path: Path to save the configuration file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create default configuration
            default_config = {
                'sources': {
                    'yahoo_finance': {
                        'enabled': True,
                        'symbols': ['AAPL', 'MSFT', 'GOOGL', 'AMZN'],
                        'data_points': ['price', 'volume', 'market_cap', 'pe_ratio']
                    },
                    'cnbc': {
                        'enabled': True,
                        'categories': ['markets', 'business', 'investing'],
                        'max_articles': 50
                    },
                    'cointelegraph': {
                        'enabled': True,
                        'cryptocurrencies': ['BTC', 'ETH', 'XRP', 'ADA'],
                        'include_news': True
                    }
                },
                'storage': {
                    'type': 'csv',  # 'csv', 'sqlite', or 'json'
                    'path': './data'
                },
                'scheduling': {
                    'frequency': 'once',  # 'once', 'hourly', 'daily'
                    'time': '09:00'  # For 'daily' frequency
                },
                'logging': {
                    'level': 'INFO',  # 'DEBUG', 'INFO', 'WARNING', 'ERROR'
                    'file': './logs/app.log'
                }
            }
            
            # Update the configuration
            self.config = default_config
            
            # Save the configuration
            return self.save_config(config_path)
        except Exception as e:
            logger.error(f"Error creating default configuration: {e}")
            return False