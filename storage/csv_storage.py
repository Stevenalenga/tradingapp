"""
CSV storage module for the Trading Information Scraper application.

This module provides functionality for storing financial data in CSV files.
"""

import csv
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)


class CSVStorage:
    """
    Storage class for CSV files.
    
    This class provides methods for storing financial data in CSV files.
    """
    
    def __init__(self, output_dir: str = "./data"):
        """
        Initialize the CSV storage.
        
        Args:
            output_dir: Directory to store CSV files
        """
        self.output_dir = output_dir
        self._ensure_directory_exists()
    
    def store(self, data: Dict, filename: Optional[str] = None) -> str:
        """
        Store data in a CSV file.
        
        Args:
            data: Data to store
            filename: Name of the CSV file (without extension)
            
        Returns:
            Path to the stored CSV file
        """
        if not filename:
            # Generate a filename based on the current timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_{timestamp}"
        
        # Ensure the filename has the .csv extension
        if not filename.endswith(".csv"):
            filename += ".csv"
            
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # Convert data to DataFrame if it's not already
            if isinstance(data, pd.DataFrame):
                df = data
            else:
                df = self._convert_to_dataframe(data)
                
            # Save DataFrame to CSV
            df.to_csv(filepath, index=False)
            logger.info(f"Data stored in {filepath}")
            
            return filepath
        except Exception as e:
            logger.error(f"Error storing data in {filepath}: {e}")
            raise
    
    def store_multiple(self, data_dict: Dict[str, Any], prefix: Optional[str] = None) -> Dict[str, str]:
        """
        Store multiple datasets in separate CSV files.
        
        Args:
            data_dict: Dictionary mapping names to datasets
            prefix: Prefix for filenames
            
        Returns:
            Dictionary mapping names to file paths
        """
        result = {}
        
        for name, data in data_dict.items():
            # Generate filename with prefix if provided
            if prefix:
                filename = f"{prefix}_{name}.csv"
            else:
                filename = f"{name}.csv"
                
            try:
                filepath = self.store(data, filename)
                result[name] = filepath
            except Exception as e:
                logger.error(f"Error storing {name} data: {e}")
                result[name] = str(e)
        
        return result
    
    def load(self, filename: str) -> pd.DataFrame:
        """
        Load data from a CSV file.
        
        Args:
            filename: Name of the CSV file (with or without extension)
            
        Returns:
            DataFrame with the loaded data
        """
        # Ensure the filename has the .csv extension
        if not filename.endswith(".csv"):
            filename += ".csv"
            
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # Load CSV into DataFrame
            df = pd.read_csv(filepath)
            logger.info(f"Data loaded from {filepath}")
            
            return df
        except Exception as e:
            logger.error(f"Error loading data from {filepath}: {e}")
            raise
    
    def append(self, data: Dict, filename: str) -> str:
        """
        Append data to an existing CSV file.
        
        Args:
            data: Data to append
            filename: Name of the CSV file (with or without extension)
            
        Returns:
            Path to the CSV file
        """
        # Ensure the filename has the .csv extension
        if not filename.endswith(".csv"):
            filename += ".csv"
            
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # Convert data to DataFrame if it's not already
            if isinstance(data, pd.DataFrame):
                df = data
            else:
                df = self._convert_to_dataframe(data)
                
            # Check if the file exists
            if os.path.exists(filepath):
                # Load existing data
                existing_df = pd.read_csv(filepath)
                
                # Append new data
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                
                # Save combined DataFrame
                combined_df.to_csv(filepath, index=False)
                logger.info(f"Data appended to {filepath}")
            else:
                # File doesn't exist, create it
                df.to_csv(filepath, index=False)
                logger.info(f"File {filepath} created with data")
            
            return filepath
        except Exception as e:
            logger.error(f"Error appending data to {filepath}: {e}")
            raise
    
    def list_files(self) -> List[str]:
        """
        List all CSV files in the output directory.
        
        Returns:
            List of CSV filenames
        """
        try:
            # Get all files in the output directory
            files = os.listdir(self.output_dir)
            
            # Filter for CSV files
            csv_files = [f for f in files if f.endswith(".csv")]
            
            return csv_files
        except Exception as e:
            logger.error(f"Error listing CSV files: {e}")
            return []
    
    def _ensure_directory_exists(self):
        """Ensure the output directory exists."""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            logger.debug(f"Output directory {self.output_dir} ensured")
        except Exception as e:
            logger.error(f"Error ensuring output directory {self.output_dir}: {e}")
            raise
    
    def _convert_to_dataframe(self, data: Any) -> pd.DataFrame:
        """
        Convert data to a pandas DataFrame.
        
        Args:
            data: Data to convert
            
        Returns:
            DataFrame with the data
        """
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, dict):
            # Check if it's a dictionary of records
            if all(isinstance(v, dict) for v in data.values()):
                # Convert to list of dictionaries
                records = [{"id": k, **v} for k, v in data.items()]
                return pd.DataFrame(records)
            else:
                # Simple dictionary
                return pd.DataFrame([data])
        elif isinstance(data, list):
            # List of dictionaries
            if all(isinstance(item, dict) for item in data):
                return pd.DataFrame(data)
            else:
                # List of values
                return pd.DataFrame({"value": data})
        else:
            # Single value
            return pd.DataFrame({"value": [data]})