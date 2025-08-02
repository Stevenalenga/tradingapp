"""
Data visualizer module for the Trading Information Scraper application.

This module provides functionality for visualizing financial data.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

logger = logging.getLogger(__name__)


class DataVisualizer:
    """
    Data visualizer for financial data.
    
    This class provides methods for creating visualizations of financial data.
    """
    
    def __init__(self, output_dir: str = "./visualizations"):
        """
        Initialize the data visualizer.
        
        Args:
            output_dir: Directory to store visualizations
        """
        self.output_dir = output_dir
        self._ensure_directory_exists()
        
        # Set up the visualization style
        self._setup_style()
    
    def plot_time_series(
        self,
        data: pd.DataFrame,
        x: str,
        y: str,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        figsize: Tuple[int, int] = (10, 6),
        color: str = '#1f77b4',
        grid: bool = True,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot a time series chart.
        
        Args:
            data: DataFrame containing the data
            x: Column name for the x-axis (typically a date/time column)
            y: Column name for the y-axis
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            figsize: Figure size as (width, height) in inches
            color: Line color
            grid: Whether to show grid lines
            save_path: Path to save the figure (if None, the figure is not saved)
            
        Returns:
            Matplotlib figure object
        """
        try:
            # Create figure and axis
            fig, ax = plt.subplots(figsize=figsize)
            
            # Plot the data
            ax.plot(data[x], data[y], color=color, linewidth=2)
            
            # Set title and labels
            if title:
                ax.set_title(title, fontsize=14)
            ax.set_xlabel(xlabel or x, fontsize=12)
            ax.set_ylabel(ylabel or y, fontsize=12)
            
            # Set grid
            ax.grid(grid)
            
            # Format the x-axis for dates if applicable
            if pd.api.types.is_datetime64_any_dtype(data[x]):
                fig.autofmt_xdate()
            
            # Tight layout
            fig.tight_layout()
            
            # Save the figure if a path is provided
            if save_path:
                self._save_figure(fig, save_path)
            
            return fig
        except Exception as e:
            logger.error(f"Error plotting time series: {e}")
            # Return an empty figure in case of error
            return plt.figure()
    
    def plot_comparison(
        self,
        data: pd.DataFrame,
        x: str,
        y_list: List[str],
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        figsize: Tuple[int, int] = (12, 6),
        colors: Optional[List[str]] = None,
        grid: bool = True,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot a comparison chart with multiple series.
        
        Args:
            data: DataFrame containing the data
            x: Column name for the x-axis
            y_list: List of column names for the y-axis
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            figsize: Figure size as (width, height) in inches
            colors: List of colors for each series
            grid: Whether to show grid lines
            save_path: Path to save the figure (if None, the figure is not saved)
            
        Returns:
            Matplotlib figure object
        """
        try:
            # Create figure and axis
            fig, ax = plt.subplots(figsize=figsize)
            
            # Plot each series
            for i, y in enumerate(y_list):
                color = colors[i] if colors and i < len(colors) else None
                ax.plot(data[x], data[y], label=y, linewidth=2, color=color)
            
            # Set title and labels
            if title:
                ax.set_title(title, fontsize=14)
            ax.set_xlabel(xlabel or x, fontsize=12)
            ax.set_ylabel(ylabel or ', '.join(y_list), fontsize=12)
            
            # Set grid
            ax.grid(grid)
            
            # Add legend
            ax.legend()
            
            # Format the x-axis for dates if applicable
            if pd.api.types.is_datetime64_any_dtype(data[x]):
                fig.autofmt_xdate()
            
            # Tight layout
            fig.tight_layout()
            
            # Save the figure if a path is provided
            if save_path:
                self._save_figure(fig, save_path)
            
            return fig
        except Exception as e:
            logger.error(f"Error plotting comparison: {e}")
            # Return an empty figure in case of error
            return plt.figure()
    
    def plot_distribution(
        self,
        data: pd.DataFrame,
        column: str,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = "Frequency",
        figsize: Tuple[int, int] = (10, 6),
        color: str = '#1f77b4',
        kde: bool = True,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot a distribution chart (histogram with optional KDE).
        
        Args:
            data: DataFrame containing the data
            column: Column name for the distribution
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            figsize: Figure size as (width, height) in inches
            color: Histogram color
            kde: Whether to show the kernel density estimate
            save_path: Path to save the figure (if None, the figure is not saved)
            
        Returns:
            Matplotlib figure object
        """
        try:
            # Create figure and axis
            fig, ax = plt.subplots(figsize=figsize)
            
            # Plot the distribution
            sns.histplot(data[column], kde=kde, color=color, ax=ax)
            
            # Set title and labels
            if title:
                ax.set_title(title, fontsize=14)
            ax.set_xlabel(xlabel or column, fontsize=12)
            ax.set_ylabel(ylabel, fontsize=12)
            
            # Tight layout
            fig.tight_layout()
            
            # Save the figure if a path is provided
            if save_path:
                self._save_figure(fig, save_path)
            
            return fig
        except Exception as e:
            logger.error(f"Error plotting distribution: {e}")
            # Return an empty figure in case of error
            return plt.figure()
    
    def plot_bar(
        self,
        data: pd.DataFrame,
        x: str,
        y: str,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        figsize: Tuple[int, int] = (10, 6),
        color: str = '#1f77b4',
        horizontal: bool = False,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot a bar chart.
        
        Args:
            data: DataFrame containing the data
            x: Column name for the x-axis
            y: Column name for the y-axis
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            figsize: Figure size as (width, height) in inches
            color: Bar color
            horizontal: Whether to create a horizontal bar chart
            save_path: Path to save the figure (if None, the figure is not saved)
            
        Returns:
            Matplotlib figure object
        """
        try:
            # Coerce y column to numeric and drop NaNs to avoid type errors during plotting
            safe = data.copy()
            if y in safe.columns:
                safe[y] = pd.to_numeric(safe[y], errors='coerce')
                before = len(safe)
                safe = safe.dropna(subset=[y])
                dropped = before - len(safe)
                if dropped > 0:
                    logger.warning(f"plot_bar: dropped {dropped} rows with non-numeric or missing values in '{y}'")
            else:
                logger.error(f"plot_bar: column '{y}' not found in DataFrame")
                return plt.figure()

            # Create figure and axis
            fig, ax = plt.subplots(figsize=figsize)
            
            # Plot the bar chart
            if horizontal:
                ax.barh(safe[x], safe[y], color=color)
            else:
                ax.bar(safe[x], safe[y], color=color)
            
            # Set title and labels
            if title:
                ax.set_title(title, fontsize=14)
            ax.set_xlabel(xlabel or x, fontsize=12)
            ax.set_ylabel(ylabel or y, fontsize=12)
            
            # Rotate x-axis labels for better readability if not horizontal
            if not horizontal and len(safe) > 5:
                plt.xticks(rotation=45, ha='right')
            
            # Tight layout
            fig.tight_layout()
            
            # Save the figure if a path is provided
            if save_path:
                self._save_figure(fig, save_path)
            
            return fig
        except Exception as e:
            logger.error(f"Error plotting bar chart: {e}")
            # Return an empty figure in case of error
            return plt.figure()
    
    def plot_scatter(
        self,
        data: pd.DataFrame,
        x: str,
        y: str,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        figsize: Tuple[int, int] = (10, 6),
        color: str = '#1f77b4',
        alpha: float = 0.7,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot a scatter chart.
        
        Args:
            data: DataFrame containing the data
            x: Column name for the x-axis
            y: Column name for the y-axis
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            figsize: Figure size as (width, height) in inches
            color: Point color
            alpha: Point transparency
            save_path: Path to save the figure (if None, the figure is not saved)
            
        Returns:
            Matplotlib figure object
        """
        try:
            # Create figure and axis
            fig, ax = plt.subplots(figsize=figsize)
            
            # Plot the scatter chart
            ax.scatter(data[x], data[y], color=color, alpha=alpha)
            
            # Set title and labels
            if title:
                ax.set_title(title, fontsize=14)
            ax.set_xlabel(xlabel or x, fontsize=12)
            ax.set_ylabel(ylabel or y, fontsize=12)
            
            # Tight layout
            fig.tight_layout()
            
            # Save the figure if a path is provided
            if save_path:
                self._save_figure(fig, save_path)
            
            return fig
        except Exception as e:
            logger.error(f"Error plotting scatter chart: {e}")
            # Return an empty figure in case of error
            return plt.figure()
    
    def plot_pie(
        self,
        data: pd.DataFrame,
        values: str,
        labels: str,
        title: Optional[str] = None,
        figsize: Tuple[int, int] = (8, 8),
        colors: Optional[List[str]] = None,
        autopct: str = '%1.1f%%',
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot a pie chart.
        
        Args:
            data: DataFrame containing the data
            values: Column name for the values
            labels: Column name for the labels
            title: Chart title
            figsize: Figure size as (width, height) in inches
            colors: List of colors for the pie slices
            autopct: Format string for the percentage labels
            save_path: Path to save the figure (if None, the figure is not saved)
            
        Returns:
            Matplotlib figure object
        """
        try:
            # Create figure and axis
            fig, ax = plt.subplots(figsize=figsize)
            
            # Plot the pie chart
            ax.pie(
                data[values],
                labels=data[labels],
                autopct=autopct,
                colors=colors,
                shadow=False,
                startangle=90
            )
            
            # Equal aspect ratio ensures that pie is drawn as a circle
            ax.axis('equal')
            
            # Set title
            if title:
                ax.set_title(title, fontsize=14)
            
            # Tight layout
            fig.tight_layout()
            
            # Save the figure if a path is provided
            if save_path:
                self._save_figure(fig, save_path)
            
            return fig
        except Exception as e:
            logger.error(f"Error plotting pie chart: {e}")
            # Return an empty figure in case of error
            return plt.figure()
    
    def plot_heatmap(
        self,
        data: pd.DataFrame,
        title: Optional[str] = None,
        figsize: Tuple[int, int] = (10, 8),
        cmap: str = 'viridis',
        annot: bool = True,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot a heatmap of a correlation matrix or other 2D data.
        
        Args:
            data: DataFrame containing the data (should be a correlation matrix or similar)
            title: Chart title
            figsize: Figure size as (width, height) in inches
            cmap: Colormap name
            annot: Whether to annotate cells with values
            save_path: Path to save the figure (if None, the figure is not saved)
            
        Returns:
            Matplotlib figure object
        """
        try:
            # Create figure and axis
            fig, ax = plt.subplots(figsize=figsize)
            
            # Plot the heatmap
            sns.heatmap(data, annot=annot, cmap=cmap, ax=ax)
            
            # Set title
            if title:
                ax.set_title(title, fontsize=14)
            
            # Tight layout
            fig.tight_layout()
            
            # Save the figure if a path is provided
            if save_path:
                self._save_figure(fig, save_path)
            
            return fig
        except Exception as e:
            logger.error(f"Error plotting heatmap: {e}")
            # Return an empty figure in case of error
            return plt.figure()
    
    def plot_multiple(
        self,
        data: pd.DataFrame,
        plot_specs: List[Dict],
        title: Optional[str] = None,
        figsize: Tuple[int, int] = (12, 10),
        layout: Optional[Tuple[int, int]] = None,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Create a figure with multiple subplots.
        
        Args:
            data: DataFrame containing the data
            plot_specs: List of dictionaries specifying each subplot
                Each dict should have:
                - 'type': Plot type ('line', 'bar', 'scatter', 'hist', etc.)
                - 'x': Column name for x-axis (if applicable)
                - 'y': Column name for y-axis (if applicable)
                - 'title': Subplot title
                - Other plot-specific parameters
            title: Figure title
            figsize: Figure size as (width, height) in inches
            layout: Tuple of (rows, cols) for the subplot layout
                If None, a layout is automatically determined
            save_path: Path to save the figure (if None, the figure is not saved)
            
        Returns:
            Matplotlib figure object
        """
        try:
            # Determine layout if not provided
            if not layout:
                n_plots = len(plot_specs)
                cols = min(3, n_plots)
                rows = (n_plots + cols - 1) // cols
                layout = (rows, cols)
            
            # Create figure and axes
            fig, axes = plt.subplots(layout[0], layout[1], figsize=figsize)
            
            # Flatten axes array for easier indexing
            if isinstance(axes, np.ndarray):
                axes = axes.flatten()
            else:
                axes = [axes]
            
            # Create each subplot
            for i, (spec, ax) in enumerate(zip(plot_specs, axes)):
                plot_type = spec.get('type', 'line')
                
                if plot_type == 'line':
                    x = spec.get('x')
                    y = spec.get('y')
                    ax.plot(data[x], data[y], color=spec.get('color', '#1f77b4'))
                    ax.set_xlabel(spec.get('xlabel', x))
                    ax.set_ylabel(spec.get('ylabel', y))
                
                elif plot_type == 'bar':
                    x = spec.get('x')
                    y = spec.get('y')
                    ax.bar(data[x], data[y], color=spec.get('color', '#1f77b4'))
                    ax.set_xlabel(spec.get('xlabel', x))
                    ax.set_ylabel(spec.get('ylabel', y))
                
                elif plot_type == 'scatter':
                    x = spec.get('x')
                    y = spec.get('y')
                    ax.scatter(data[x], data[y], color=spec.get('color', '#1f77b4'), alpha=spec.get('alpha', 0.7))
                    ax.set_xlabel(spec.get('xlabel', x))
                    ax.set_ylabel(spec.get('ylabel', y))
                
                elif plot_type == 'hist':
                    column = spec.get('column')
                    ax.hist(data[column], bins=spec.get('bins', 10), color=spec.get('color', '#1f77b4'))
                    ax.set_xlabel(spec.get('xlabel', column))
                    ax.set_ylabel(spec.get('ylabel', 'Frequency'))
                
                # Set subplot title
                if 'title' in spec:
                    ax.set_title(spec['title'])
                
                # Set grid
                ax.grid(spec.get('grid', True))
            
            # Hide any unused subplots
            for j in range(len(plot_specs), len(axes)):
                axes[j].axis('off')
            
            # Set figure title
            if title:
                fig.suptitle(title, fontsize=16)
            
            # Tight layout
            fig.tight_layout()
            if title:
                fig.subplots_adjust(top=0.9)
            
            # Save the figure if a path is provided
            if save_path:
                self._save_figure(fig, save_path)
            
            return fig
        except Exception as e:
            logger.error(f"Error plotting multiple charts: {e}")
            # Return an empty figure in case of error
            return plt.figure()
    
    def save_plot(self, fig: plt.Figure, filename: str, format: str = 'png', dpi: int = 300) -> str:
        """
        Save a plot to a file.
        
        Args:
            fig: Matplotlib figure object
            filename: Name of the file (without extension)
            format: File format ('png', 'jpg', 'svg', 'pdf')
            dpi: Resolution in dots per inch
            
        Returns:
            Path to the saved file
        """
        # Ensure the filename has the correct extension
        if not filename.endswith(f".{format}"):
            filename += f".{format}"
            
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            fig.savefig(filepath, format=format, dpi=dpi, bbox_inches='tight')
            logger.info(f"Plot saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving plot to {filepath}: {e}")
            raise
    
    def _save_figure(self, fig: plt.Figure, save_path: str, dpi: int = 300):
        """
        Save a figure to a file.
        
        Args:
            fig: Matplotlib figure object
            save_path: Path to save the figure
            dpi: Resolution in dots per inch
        """
        try:
            # If save_path is just a filename, prepend the output directory
            if not os.path.dirname(save_path):
                save_path = os.path.join(self.output_dir, save_path)
                
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
                
            # Save the figure
            fig.savefig(save_path, dpi=dpi, bbox_inches='tight')
            logger.info(f"Figure saved to {save_path}")
        except Exception as e:
            logger.error(f"Error saving figure to {save_path}: {e}")
    
    def _ensure_directory_exists(self):
        """Ensure the output directory exists."""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            logger.debug(f"Output directory {self.output_dir} ensured")
        except Exception as e:
            logger.error(f"Error ensuring output directory {self.output_dir}: {e}")
            raise
    
    def _setup_style(self):
        """Set up the visualization style."""
        try:
            # Use seaborn style
            sns.set_style("whitegrid")
            
            # Set up matplotlib parameters
            plt.rcParams['figure.figsize'] = (10, 6)
            plt.rcParams['font.size'] = 12
            plt.rcParams['axes.titlesize'] = 14
            plt.rcParams['axes.labelsize'] = 12
            plt.rcParams['xtick.labelsize'] = 10
            plt.rcParams['ytick.labelsize'] = 10
            plt.rcParams['legend.fontsize'] = 10
            plt.rcParams['figure.titlesize'] = 16
        except Exception as e:
            logger.error(f"Error setting up visualization style: {e}")