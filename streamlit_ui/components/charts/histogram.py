"""
Histogram Component for Molecular Analysis Visualization

Provides configurable histogram visualization for molecular property distributions.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union

from ..base import BaseComponent


class HistogramComponent(BaseComponent):
    """
    Histogram component for displaying molecular property distributions.
    
    Features:
    - Multiple histogram types (count, density, probability)
    - Customizable binning strategies
    - Statistical overlays (mean, median, std)
    - Multiple distributions comparison
    - Interactive hover information
    - Export capabilities
    """
    
    def __init__(self, name: str = "Histogram", key_prefix: str = None):
        """
        Initialize the histogram component.
        
        Args:
            name: Component display name
            key_prefix: Unique key prefix for Streamlit widgets
        """
        super().__init__(name, key_prefix)
        self.chart_config = {
            'title': '',
            'x_label': '',
            'y_label': '',
            'color_scheme': 'viridis',
            'bins': 'auto',
            'hist_type': 'count',  # 'count', 'density', 'probability'
            'show_stats': True,
            'opacity': 0.7,
            'show_kde': False,
            'cumulative': False
        }
    
    def configure_chart(self, 
                       title: str = '',
                       x_label: str = '',
                       y_label: str = '',
                       color_scheme: str = 'viridis',
                       bins: Union[int, str] = 'auto',
                       hist_type: str = 'count',
                       show_stats: bool = True,
                       opacity: float = 0.7,
                       show_kde: bool = False,
                       cumulative: bool = False) -> None:
        """
        Configure histogram appearance and behavior.
        
        Args:
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            color_scheme: Plotly color scheme
            bins: Number of bins or binning strategy
            hist_type: Type of histogram ('count', 'density', 'probability')
            show_stats: Whether to show statistical indicators
            opacity: Histogram opacity (0-1)
            show_kde: Whether to show kernel density estimation
            cumulative: Whether to show cumulative distribution
        """
        self.chart_config.update({
            'title': title,
            'x_label': x_label,
            'y_label': y_label,
            'color_scheme': color_scheme,
            'bins': bins,
            'hist_type': hist_type,
            'show_stats': show_stats,
            'opacity': opacity,
            'show_kde': show_kde,
            'cumulative': cumulative
        })
    
    def validate_data(self, data: Union[pd.DataFrame, pd.Series, List, np.ndarray]) -> bool:
        """
        Validate input data for histogram.
        
        Args:
            data: Input data
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            if data is None:
                self.add_error("No data provided for histogram")
                return False
            
            # Convert to numeric array/series
            if isinstance(data, list):
                data = np.array(data)
            elif isinstance(data, pd.DataFrame):
                if len(data.columns) == 0:
                    self.add_error("DataFrame is empty")
                    return False
                # Use first numeric column
                numeric_cols = data.select_dtypes(include=['number']).columns
                if len(numeric_cols) == 0:
                    self.add_error("No numeric columns found")
                    return False
                data = data[numeric_cols[0]]
            
            # Check if data is numeric
            if isinstance(data, pd.Series):
                if not pd.api.types.is_numeric_dtype(data):
                    self.add_error("Data must be numeric")
                    return False
                data = data.dropna()
            elif isinstance(data, np.ndarray):
                if not np.issubdtype(data.dtype, np.number):
                    self.add_error("Data must be numeric")
                    return False
                data = data[~np.isnan(data)]
            
            if len(data) == 0:
                self.add_error("No valid numeric data found")
                return False
            
            if len(data) < 2:
                self.add_error("Need at least 2 data points for histogram")
                return False
            
            return True
            
        except Exception as e:
            self.add_error(f"Data validation error: {str(e)}", e)
            return False
    
    def calculate_statistics(self, data: Union[pd.Series, np.ndarray]) -> Dict[str, float]:
        """
        Calculate statistical measures for the data.
        
        Args:
            data: Numeric data
            
        Returns:
            Dictionary of statistical measures
        """
        try:
            if isinstance(data, pd.Series):
                data = data.dropna()
            elif isinstance(data, np.ndarray):
                data = data[~np.isnan(data)]
            
            stats = {
                'mean': np.mean(data),
                'median': np.median(data),
                'std': np.std(data),
                'min': np.min(data),
                'max': np.max(data),
                'q25': np.percentile(data, 25),
                'q75': np.percentile(data, 75),
                'count': len(data)
            }
            
            return stats
            
        except Exception as e:
            self.add_error(f"Error calculating statistics: {str(e)}", e)
            return {}
    
    def create_chart(self, 
                    data: Union[pd.DataFrame, pd.Series, List, np.ndarray],
                    column: str = None,
                    group_column: str = None,
                    custom_config: Dict = None) -> Optional[go.Figure]:
        """
        Create histogram from data.
        
        Args:
            data: Input data
            column: Column name for histogram (if DataFrame)
            group_column: Column name for grouping (multiple histograms)
            custom_config: Additional chart configuration
            
        Returns:
            Plotly figure object or None if error
        """
        try:
            # Validate data
            if not self.validate_data(data):
                return None
            
            # Apply custom configuration
            config = self.chart_config.copy()
            if custom_config:
                config.update(custom_config)
            
            # Prepare data
            if isinstance(data, pd.DataFrame):
                if column and column in data.columns:
                    values = data[column].dropna()
                else:
                    numeric_cols = data.select_dtypes(include=['number']).columns
                    if len(numeric_cols) == 0:
                        self.add_error("No numeric columns found")
                        return None
                    values = data[numeric_cols[0]].dropna()
                    column = numeric_cols[0]
            elif isinstance(data, pd.Series):
                values = data.dropna()
                column = data.name or 'Values'
            else:
                values = np.array(data)
                values = values[~np.isnan(values)]
                column = 'Values'
            
            # Create figure
            fig = go.Figure()
            
            # Handle grouping
            if isinstance(data, pd.DataFrame) and group_column and group_column in data.columns:
                # Multiple histograms by group
                groups = data[group_column].unique()
                colors = px.colors.qualitative.Set3[:len(groups)]
                
                for i, group in enumerate(groups):
                    group_data = data[data[group_column] == group][column].dropna()
                    if len(group_data) > 0:
                        fig.add_trace(go.Histogram(
                            x=group_data,
                            name=str(group),
                            opacity=config['opacity'],
                            nbinsx=config['bins'] if isinstance(config['bins'], int) else None,
                            marker_color=colors[i % len(colors)],
                            histnorm=config['hist_type'] if config['hist_type'] != 'count' else None,
                            cumulative_enabled=config['cumulative']
                        ))
                
                fig.update_layout(barmode='overlay')
                
            else:
                # Single histogram
                fig.add_trace(go.Histogram(
                    x=values,
                    opacity=config['opacity'],
                    nbinsx=config['bins'] if isinstance(config['bins'], int) else None,
                    marker_color=px.colors.qualitative.Set3[0],
                    histnorm=config['hist_type'] if config['hist_type'] != 'count' else None,
                    cumulative_enabled=config['cumulative']
                ))
            
            # Add statistical lines if requested
            if config['show_stats'] and not (isinstance(data, pd.DataFrame) and group_column):
                stats = self.calculate_statistics(values)
                if stats:
                    # Add mean line
                    fig.add_vline(
                        x=stats['mean'],
                        line_dash="dash",
                        line_color="red",
                        annotation_text=f"Mean: {stats['mean']:.2f}",
                        annotation_position="top"
                    )
                    
                    # Add median line
                    fig.add_vline(
                        x=stats['median'],
                        line_dash="dot",
                        line_color="green",
                        annotation_text=f"Median: {stats['median']:.2f}",
                        annotation_position="bottom"
                    )
            
            # Add KDE if requested
            if config['show_kde'] and not config['cumulative']:
                try:
                    from scipy import stats as scipy_stats
                    kde = scipy_stats.gaussian_kde(values)
                    x_range = np.linspace(values.min(), values.max(), 100)
                    kde_values = kde(x_range)
                    
                    # Scale KDE to match histogram
                    if config['hist_type'] == 'count':
                        kde_values *= len(values) * (values.max() - values.min()) / len(x_range)
                    
                    fig.add_trace(go.Scatter(
                        x=x_range,
                        y=kde_values,
                        mode='lines',
                        name='KDE',
                        line=dict(color='orange', width=2)
                    ))
                except ImportError:
                    self.add_warning("scipy not available for KDE calculation")
            
            # Update layout
            y_label = config['y_label']
            if not y_label:
                if config['hist_type'] == 'count':
                    y_label = 'Count'
                elif config['hist_type'] == 'density':
                    y_label = 'Density'
                elif config['hist_type'] == 'probability':
                    y_label = 'Probability'
                else:
                    y_label = 'Frequency'
            
            fig.update_layout(
                title=config['title'],
                xaxis_title=config['x_label'] or column,
                yaxis_title=y_label,
                hovermode='x unified',
                template='plotly_white'
            )
            
            return fig
            
        except Exception as e:
            self.add_error(f"Error creating histogram: {str(e)}", e)
            return None
    
    def render(self, 
              data: Union[pd.DataFrame, pd.Series, List, np.ndarray],
              column: str = None,
              group_column: str = None,
              show_config: bool = False,
              height: int = 500) -> Optional[go.Figure]:
        """
        Render the histogram component.
        
        Args:
            data: Input data for the histogram
            column: Column name for histogram (if DataFrame)
            group_column: Column name for grouping
            show_config: Whether to show configuration options
            height: Chart height in pixels
            
        Returns:
            Plotly figure object or None if error
        """
        try:
            self.clear_messages()
            
            # Show configuration options if requested
            if show_config:
                st.subheader("Histogram Configuration")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    self.chart_config['title'] = st.text_input(
                        "Chart Title", 
                        value=self.chart_config['title'],
                        key=self.get_key('title')
                    )
                    
                    self.chart_config['hist_type'] = st.selectbox(
                        "Histogram Type",
                        options=['count', 'density', 'probability'],
                        index=['count', 'density', 'probability'].index(self.chart_config['hist_type']),
                        key=self.get_key('hist_type')
                    )
                
                with col2:
                    bins_input = st.text_input(
                        "Number of Bins",
                        value=str(self.chart_config['bins']),
                        key=self.get_key('bins')
                    )
                    
                    try:
                        self.chart_config['bins'] = int(bins_input)
                    except ValueError:
                        self.chart_config['bins'] = bins_input
                    
                    self.chart_config['opacity'] = st.slider(
                        "Opacity",
                        min_value=0.1,
                        max_value=1.0,
                        value=self.chart_config['opacity'],
                        step=0.1,
                        key=self.get_key('opacity')
                    )
                
                with col3:
                    self.chart_config['show_stats'] = st.checkbox(
                        "Show Statistics",
                        value=self.chart_config['show_stats'],
                        key=self.get_key('show_stats')
                    )
                    
                    self.chart_config['show_kde'] = st.checkbox(
                        "Show KDE",
                        value=self.chart_config['show_kde'],
                        key=self.get_key('show_kde')
                    )
                    
                    self.chart_config['cumulative'] = st.checkbox(
                        "Cumulative",
                        value=self.chart_config['cumulative'],
                        key=self.get_key('cumulative')
                    )
            
            # Create and display chart
            fig = self.create_chart(data, column, group_column)
            
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True, height=height)
                
                # Show statistics if enabled
                if self.chart_config['show_stats']:
                    if isinstance(data, pd.DataFrame) and column:
                        stats_data = data[column].dropna()
                    elif isinstance(data, pd.Series):
                        stats_data = data.dropna()
                    else:
                        stats_data = np.array(data)
                        stats_data = stats_data[~np.isnan(stats_data)]
                    
                    stats = self.calculate_statistics(stats_data)
                    if stats:
                        st.subheader("Statistics")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Mean", f"{stats['mean']:.3f}")
                            st.metric("Std Dev", f"{stats['std']:.3f}")
                        with col2:
                            st.metric("Median", f"{stats['median']:.3f}")
                            st.metric("Count", f"{stats['count']}")
                        with col3:
                            st.metric("Min", f"{stats['min']:.3f}")
                            st.metric("Q25", f"{stats['q25']:.3f}")
                        with col4:
                            st.metric("Max", f"{stats['max']:.3f}")
                            st.metric("Q75", f"{stats['q75']:.3f}")
                
                # Log interaction
                self.log_interaction('chart_rendered', {
                    'chart_type': 'histogram',
                    'data_shape': getattr(data, 'shape', 'unknown') if hasattr(data, 'shape') else 'unknown',
                    'column': column,
                    'group_column': group_column,
                    'bins': self.chart_config['bins'],
                    'hist_type': self.chart_config['hist_type']
                })
                
                return fig
            else:
                self.display_messages()
                return None
            
        except Exception as e:
            self.add_error(f"Error rendering histogram: {str(e)}", e)
            self.display_messages()
            return None