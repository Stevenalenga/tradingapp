"""
JSON storage module for the Trading Information Scraper application.

This module provides functionality for storing financial data in JSON files.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)


class JSONStorage:
    """
    Storage class for JSON files.
    
    This class provides methods for storing financial data in JSON files.
    """
    
    def __init__(self, output_dir: str = "./data"):
        """
        Initialize the JSON storage.
        
        Args:
            output_dir: Directory to store JSON files
        """
        self.output_dir = output_dir
        self._ensure_directory_exists()
    
    def store(self, data: Any, filename: Optional[str] = None) -> str:
        """
        Store data in a JSON file.
        
        Args:
            data: Data to store
            filename: Name of the JSON file (without extension)
            
        Returns:
            Path to the stored JSON file
        """
        if not filename:
            # Generate a filename based on the current timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_{timestamp}"
        
        # Ensure the filename has the .json extension
        if not filename.endswith(".json"):
            filename += ".json"
            
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # Convert data to a JSON-serializable format
            json_data = self._prepare_for_json(data)
                
            # Save data to JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Data stored in {filepath}")
            
            return filepath
        except Exception as e:
            logger.error(f"Error storing data in {filepath}: {e}")
            raise
    
    def store_multiple(self, data_dict: Dict[str, Any], prefix: Optional[str] = None) -> Dict[str, str]:
        """
        Store multiple datasets in separate JSON files.
        
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
                filename = f"{prefix}_{name}.json"
            else:
                filename = f"{name}.json"
                
            try:
                filepath = self.store(data, filename)
                result[name] = filepath
            except Exception as e:
                logger.error(f"Error storing {name} data: {e}")
                result[name] = str(e)
        
        return result
    
    def load(self, filename: str) -> Any:
        """
        Load data from a JSON file.
        
        Args:
            filename: Name of the JSON file (with or without extension)
            
        Returns:
            Loaded data
        """
        # Ensure the filename has the .json extension
        if not filename.endswith(".json"):
            filename += ".json"
            
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # Load JSON from file
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            logger.info(f"Data loaded from {filepath}")
            
            return data
        except Exception as e:
            logger.error(f"Error loading data from {filepath}: {e}")
            raise
    
    def append(self, data: Any, filename: str, key: Optional[str] = None) -> str:
        """
        Append data to an existing JSON file.
        
        Args:
            data: Data to append
            filename: Name of the JSON file (with or without extension)
            key: Key to append data under (for nested structures)
            
        Returns:
            Path to the JSON file
        """
        # Ensure the filename has the .json extension
        if not filename.endswith(".json"):
            filename += ".json"
            
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # Convert data to a JSON-serializable format
            json_data = self._prepare_for_json(data)
            
            # Check if the file exists
            if os.path.exists(filepath):
                # Load existing data
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                
                # Append new data
                if key:
                    # Append to a specific key
                    if key not in existing_data:
                        existing_data[key] = []
                        
                    if isinstance(existing_data[key], list):
                        if isinstance(json_data, list):
                            existing_data[key].extend(json_data)
                        else:
                            existing_data[key].append(json_data)
                    elif isinstance(existing_data[key], dict):
                        if isinstance(json_data, dict):
                            existing_data[key].update(json_data)
                        else:
                            logger.warning(f"Cannot append non-dict data to dict at key {key}")
                    else:
                        logger.warning(f"Cannot append to non-collection at key {key}")
                else:
                    # Append to the root level
                    if isinstance(existing_data, list):
                        if isinstance(json_data, list):
                            existing_data.extend(json_data)
                        else:
                            existing_data.append(json_data)
                    elif isinstance(existing_data, dict):
                        if isinstance(json_data, dict):
                            existing_data.update(json_data)
                        else:
                            logger.warning("Cannot append non-dict data to dict at root level")
                    else:
                        logger.warning("Cannot append to non-collection at root level")
                
                # Save updated data
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, indent=2, ensure_ascii=False)
                    
                logger.info(f"Data appended to {filepath}")
            else:
                # File doesn't exist, create it
                with open(filepath, 'w', encoding='utf-8') as f:
                    if key:
                        # Create a new structure with the key
                        root_data = {key: json_data}
                        json.dump(root_data, f, indent=2, ensure_ascii=False)
                    else:
                        # Just store the data directly
                        json.dump(json_data, f, indent=2, ensure_ascii=False)
                        
                logger.info(f"File {filepath} created with data")
            
            return filepath
        except Exception as e:
            logger.error(f"Error appending data to {filepath}: {e}")
            raise
    
    def list_files(self) -> List[str]:
        """
        List all JSON files in the output directory.
        
        Returns:
            List of JSON filenames
        """
        try:
            # Get all files in the output directory
            files = os.listdir(self.output_dir)
            
            # Filter for JSON files
            json_files = [f for f in files if f.endswith(".json")]
            
            return json_files
        except Exception as e:
            logger.error(f"Error listing JSON files: {e}")
            return []
    
    def to_dataframe(self, data: Any) -> pd.DataFrame:
        """
        Convert JSON data to a pandas DataFrame.
        
        Args:
            data: JSON data to convert
            
        Returns:
            DataFrame with the data
        """
        try:
            if isinstance(data, list):
                # List of records
                if all(isinstance(item, dict) for item in data):
                    return pd.DataFrame(data)
                else:
                    return pd.DataFrame({"value": data})
            elif isinstance(data, dict):
                # Check if it's a dictionary of records
                if all(isinstance(v, dict) for v in data.values()):
                    # Convert to list of dictionaries
                    records = [{"id": k, **v} for k, v in data.items()]
                    return pd.DataFrame(records)
                else:
                    # Simple dictionary
                    return pd.DataFrame([data])
            else:
                # Single value
                return pd.DataFrame({"value": [data]})
        except Exception as e:
            logger.error(f"Error converting JSON data to DataFrame: {e}")
            return pd.DataFrame()
    
    def _ensure_directory_exists(self):
        """Ensure the output directory exists."""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            logger.debug(f"Output directory {self.output_dir} ensured")
        except Exception as e:
            logger.error(f"Error ensuring output directory {self.output_dir}: {e}")
            raise
    
    def _prepare_for_json(self, data: Any) -> Any:
        """
        Prepare data for JSON serialization.
        
        Args:
            data: Data to prepare
            
        Returns:
            JSON-serializable data
        """
        if isinstance(data, pd.DataFrame):
            # Convert DataFrame to list of dictionaries
            return data.to_dict(orient='records')
        elif hasattr(data, 'to_dict'):
            # Handle objects with to_dict method
            return data.to_dict()
        elif isinstance(data, (list, tuple)):
            # Handle lists and tuples
            return [self._prepare_for_json(item) for item in data]
        elif isinstance(data, dict):
            # Handle dictionaries
            return {k: self._prepare_for_json(v) for k, v in data.items()}
        elif isinstance(data, (int, float, str, bool, type(None))):
            # Primitive types are already JSON-serializable
            return data
        elif hasattr(data, '__dict__'):
            # Handle objects with __dict__ attribute
            return self._prepare_for_json(data.__dict__)
        else:
            # Convert to string as a fallback
            return str(data)