"""
Scatter Plot Component for Molecular Analysis Visualization

Provides configurable scatter plot visualization for molecular properties correlation and analysis.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union

from ..base import BaseComponent


class ScatterPlotComponent(BaseComponent):
    """
    Scatter plot component for displaying molecular analysis correlations.
    
    Features:
    - Multiple marker styles and sizes
    - Color mapping by third variable
    - Trend line fitting
    - Interactive hover information
    - Statistical annotations
    - Export capabilities
    """
    
    def __init__(self, name: str = "Scatter Plot", key_prefix: str = None):
        """
        Initialize the scatter plot component.
        
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
            'marker_size': 8,
            'marker_style': 'circle',
            'show_trendline': False,
            'trendline_type': 'linear',
            'show_correlation': False,
            'opacity': 0.7
        }
    
    def configure_chart(self,
                       title: str = '',
                       x_label: str = '',
                       y_label: str = '',
                       color_scheme: str = 'viridis',
                       marker_size: int = 8,
                       marker_style: str = 'circle',
                       show_trendline: bool = False,
                       trendline_type: str = 'linear',
                       show_correlation: bool = False,
                       opacity: float = 0.7) -> None:
        """
        Configure scatter plot appearance and behavior.
        
        Args:
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            color_scheme: Plotly color scheme
            marker_size: Size of scatter points
            marker_style: Marker symbol style
            show_trendline: Whether to show trend line
            trendline_type: Type of trend line ('linear', 'polynomial', 'exponential')
            show_correlation: Whether to show correlation coefficient
            opacity: Marker opacity (0-1)
        """
        self.chart_config.update({
            'title': title,
            'x_label': x_label,
            'y_label': y_label,
            'color_scheme': color_scheme,
            'marker_size': marker_size,
            'marker_style': marker_style,
            'show_trendline': show_trendline,
            'trendline_type': trendline_type,
            'show_correlation': show_correlation,
            'opacity': opacity
        })
    
    def validate_data(self, data: Union[pd.DataFrame, Dict, List]) -> bool:
        """
        Validate input data for scatter plot.
        
        Args:
            data: Input data (DataFrame, dict, or list)
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            if data is None:
                self.add_error("No data provided for scatter plot")
                return False
            
            # Convert to DataFrame if needed
            if isinstance(data, (dict, list)):
                try:
                    data = pd.DataFrame(data)
                except Exception as e:
                    self.add_error(f"Cannot convert data to DataFrame: {str(e)}")
                    return False
            
            if not isinstance(data, pd.DataFrame):
                self.add_error("Data must be a pandas DataFrame, dict, or list")
                return False
            
            if data.empty:
                self.add_error("Data is empty")
                return False
            
            if len(data.columns) < 2:
                self.add_error("Data must have at least two columns for scatter plot")
                return False
            
            return True
            
        except Exception as e:
            self.add_error(f"Data validation error: {str(e)}", e)
            return False
    
    def calculate_correlation(self, x_data: pd.Series, y_data: pd.Series) -> Dict[str, float]:
        """
        Calculate correlation statistics.
        
        Args:
            x_data: X-axis data
            y_data: Y-axis data
            
        Returns:
            Dictionary with correlation statistics
        """
        try:
            # Remove NaN values
            valid_data = pd.DataFrame({'x': x_data, 'y': y_data}).dropna()
            
            if len(valid_data) < 2:
                return {'correlation': 0, 'r_squared': 0, 'p_value': 1}
            
            correlation = valid_data['x'].corr(valid_data['y'])
            r_squared = correlation ** 2
            
            # Simple p-value approximation (not exact)
            n = len(valid_data)
            t_stat = correlation * np.sqrt((n - 2) / (1 - r_squared)) if r_squared < 1 else 0
            p_value = 2 * (1 - abs(t_stat) / np.sqrt(n - 2)) if n > 2 else 1
            
            return {
                'correlation': correlation,
                'r_squared': r_squared,
                'p_value': min(p_value, 1.0),
                'n_points': n
            }
            
        except Exception as e:
            self.add_error(f"Error calculating correlation: {str(e)}")
            return {'correlation': 0, 'r_squared': 0, 'p_value': 1}
    
    def create_chart(self,
                    data: Union[pd.DataFrame, Dict, List],
                    x_column: str,
                    y_column: str,
                    color_column: str = None,
                    size_column: str = None,
                    hover_columns: List[str] = None,
                    custom_config: Dict = None) -> Optional[go.Figure]:
        """
        Create scatter plot from data.
        
        Args:
            data: Input data
            x_column: Column name for x-axis
            y_column: Column name for y-axis
            color_column: Column name for color mapping
            size_column: Column name for marker size mapping
            hover_columns: Additional columns to show in hover
            custom_config: Additional chart configuration
            
        Returns:
            Plotly figure object or None if error
        """
        try:
            # Validate data
            if not self.validate_data(data):
                return None
            
            # Convert to DataFrame if needed
            if isinstance(data, (dict, list)):
                data = pd.DataFrame(data)
            
            # Apply custom configuration
            config = self.chart_config.copy()
            if custom_config:
                config.update(custom_config)
            
            # Validate required columns
            required_cols = [x_column, y_column]
            missing_cols = [col for col in required_cols if col not in data.columns]
            if missing_cols:
                self.add_error(f"Missing required columns: {missing_cols}")
                return None
            
            # Prepare hover data
            hover_data = hover_columns or []
            if color_column and color_column not in hover_data:
                hover_data.append(color_column)
            if size_column and size_column not in hover_data:
                hover_data.append(size_column)
            
            # Create scatter plot
            if color_column and color_column in data.columns:
                fig = px.scatter(
                    data,
                    x=x_column,
                    y=y_column,
                    color=color_column,
                    size=size_column if size_column and size_column in data.columns else None,
                    hover_data=hover_data,
                    color_continuous_scale=config['color_scheme'],
                    opacity=config['opacity'],
                    title=config['title']
                )
            else:
                fig = go.Figure(data=go.Scatter(
                    x=data[x_column],
                    y=data[y_column],
                    mode='markers',
                    marker=dict(
                        size=config['marker_size'],
                        symbol=config['marker_style'],
                        opacity=config['opacity']
                    ),
                    name='Data Points'
                ))
            
            # Update layout
            fig.update_layout(
                title=config['title'],
                xaxis_title=config['x_label'] or x_column,
                yaxis_title=config['y_label'] or y_column,
                hovermode='closest',
                template='plotly_white'
            )
            
            # Add trend line if requested
            if config['show_trendline']:
                self.add_trendline(fig, data[x_column], data[y_column], config['trendline_type'])
            
            # Add correlation annotation if requested
            if config['show_correlation']:
                correlation_stats = self.calculate_correlation(data[x_column], data[y_column])
                correlation_text = f"r = {correlation_stats['correlation']:.3f}<br>r² = {correlation_stats['r_squared']:.3f}<br>n = {correlation_stats['n_points']}"
                
                fig.add_annotation(
                    x=0.02,
                    y=0.98,
                    xref='paper',
                    yref='paper',
                    text=correlation_text,
                    showarrow=False,
                    bgcolor='rgba(255,255,255,0.8)',
                    bordercolor='gray',
                    borderwidth=1
                )
            
            return fig
            
        except Exception as e:
            self.add_error(f"Error creating scatter plot: {str(e)}", e)
            return None
    
    def add_trendline(self, fig: go.Figure, x_data: pd.Series, y_data: pd.Series, trendline_type: str) -> None:
        """
        Add trend line to scatter plot.
        
        Args:
            fig: Plotly figure object
            x_data: X-axis data
            y_data: Y-axis data
            trendline_type: Type of trend line
        """
        try:
            # Remove NaN values
            valid_data = pd.DataFrame({'x': x_data, 'y': y_data}).dropna()
            if len(valid_data) < 2:
                return
            
            x_vals = valid_data['x'].values
            y_vals = valid_data['y'].values
            
            if trendline_type == 'linear':
                # Linear regression
                z = np.polyfit(x_vals, y_vals, 1)
                p = np.poly1d(z)
                trend_x = np.linspace(x_vals.min(), x_vals.max(), 100)
                trend_y = p(trend_x)
                
            elif trendline_type == 'polynomial':
                # Polynomial regression (degree 2)
                z = np.polyfit(x_vals, y_vals, 2)
                p = np.poly1d(z)
                trend_x = np.linspace(x_vals.min(), x_vals.max(), 100)
                trend_y = p(trend_x)
                
            elif trendline_type == 'exponential':
                # Exponential regression (log transformation)
                try:
                    y_positive = y_vals[y_vals > 0]
                    x_positive = x_vals[y_vals > 0]
                    if len(y_positive) > 1:
                        z = np.polyfit(x_positive, np.log(y_positive), 1)
                        trend_x = np.linspace(x_vals.min(), x_vals.max(), 100)
                        trend_y = np.exp(z[1]) * np.exp(z[0] * trend_x)
                    else:
                        return
                except:
                    return
            else:
                return
            
            # Add trend line to figure
            fig.add_trace(go.Scatter(
                x=trend_x,
                y=trend_y,
                mode='lines',
                name=f'{trendline_type.title()} Trend',
                line=dict(color='red', dash='dash')
            ))
            
        except Exception as e:
            self.add_error(f"Error adding trend line: {str(e)}")
    
    def render(self,
              data: Union[pd.DataFrame, Dict, List],
              x_column: str,
              y_column: str,
              color_column: str = None,
              size_column: str = None,
              hover_columns: List[str] = None,
              show_config: bool = False,
              height: int = 500) -> Optional[go.Figure]:
        """
        Render the scatter plot component.
        
        Args:
            data: Input data for the chart
            x_column: Column name for x-axis
            y_column: Column name for y-axis
            color_column: Column name for color mapping
            size_column: Column name for marker size mapping
            hover_columns: Additional columns to show in hover
            show_config: Whether to show configuration options
            height: Chart height in pixels
            
        Returns:
            Plotly figure object or None if error
        """
        try:
            self.clear_messages()
            
            # Show configuration options if requested
            if show_config:
                st.subheader("Scatter Plot Configuration")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    self.chart_config['title'] = st.text_input(
                        "Chart Title",
                        value=self.chart_config['title'],
                        key=self.get_key('title')
                    )
                    
                    self.chart_config['marker_size'] = st.slider(
                        "Marker Size",
                        min_value=3,
                        max_value=20,
                        value=self.chart_config['marker_size'],
                        key=self.get_key('marker_size')
                    )
                
                with col2:
                    self.chart_config['show_trendline'] = st.checkbox(
                        "Show Trend Line",
                        value=self.chart_config['show_trendline'],
                        key=self.get_key('show_trendline')
                    )
                    
                    if self.chart_config['show_trendline']:
                        self.chart_config['trendline_type'] = st.selectbox(
                            "Trend Line Type",
                            options=['linear', 'polynomial', 'exponential'],
                            index=['linear', 'polynomial', 'exponential'].index(self.chart_config['trendline_type']),
                            key=self.get_key('trendline_type')
                        )
                
                with col3:
                    self.chart_config['show_correlation'] = st.checkbox(
                        "Show Correlation",
                        value=self.chart_config['show_correlation'],
                        key=self.get_key('show_correlation')
                    )
                    
                    self.chart_config['opacity'] = st.slider(
                        "Marker Opacity",
                        min_value=0.1,
                        max_value=1.0,
                        value=self.chart_config['opacity'],
                        step=0.1,
                        key=self.get_key('opacity')
                    )
            
            # Create and display chart
            fig = self.create_chart(data, x_column, y_column, color_column, size_column, hover_columns)
            
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True, height=height)
                
                # Show correlation statistics if enabled
                if self.chart_config['show_correlation'] and isinstance(data, pd.DataFrame):
                    if x_column in data.columns and y_column in data.columns:
                        stats = self.calculate_correlation(data[x_column], data[y_column])
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Correlation (r)", f"{stats['correlation']:.3f}")
                        with col2:
                            st.metric("R-squared", f"{stats['r_squared']:.3f}")
                        with col3:
                            st.metric("P-value", f"{stats['p_value']:.3f}")
                        with col4:
                            st.metric("Data Points", stats['n_points'])
                
                # Log interaction
                self.log_interaction('chart_rendered', {
                    'chart_type': 'scatter',
                    'data_shape': getattr(data, 'shape', 'unknown') if hasattr(data, 'shape') else 'unknown',
                    'x_column': x_column,
                    'y_column': y_column,
                    'color_column': color_column,
                    'size_column': size_column
                })
                
                return fig
            else:
                self.display_messages()
                return None
            
        except Exception as e:
            self.add_error(f"Error rendering scatter plot: {str(e)}", e)
            self.display_messages()
            return None