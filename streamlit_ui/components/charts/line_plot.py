"""
Line Plot Component for Molecular Analysis Visualization

Provides configurable line plot visualization for time series and sequential molecular data.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union

from ..base import BaseComponent


class LinePlotComponent(BaseComponent):
    """
    Line plot component for displaying sequential molecular analysis data.
    
    Features:
    - Multiple line styles and markers
    - Multi-series support
    - Smoothing options
    - Area fill options
    - Interactive hover information
    - Statistical annotations
    - Export capabilities
    """
    
    def __init__(self, name: str = "Line Plot", key_prefix: str = None):
        """
        Initialize the line plot component.
        
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
            'line_width': 2,
            'marker_size': 6,
            'show_markers': True,
            'line_style': 'solid',
            'fill_area': False,
            'show_grid': True,
            'smooth_lines': False,
            'connect_gaps': True
        }
    
    def configure_chart(self,
                       title: str = '',
                       x_label: str = '',
                       y_label: str = '',
                       color_scheme: str = 'viridis',
                       line_width: int = 2,
                       marker_size: int = 6,
                       show_markers: bool = True,
                       line_style: str = 'solid',
                       fill_area: bool = False,
                       show_grid: bool = True,
                       smooth_lines: bool = False,
                       connect_gaps: bool = True) -> None:
        """
        Configure line plot appearance and behavior.
        
        Args:
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            color_scheme: Plotly color scheme
            line_width: Width of lines
            marker_size: Size of markers
            show_markers: Whether to show markers on lines
            line_style: Line style ('solid', 'dash', 'dot', 'dashdot')
            fill_area: Whether to fill area under lines
            show_grid: Whether to show grid lines
            smooth_lines: Whether to apply smoothing
            connect_gaps: Whether to connect across missing data
        """
        self.chart_config.update({
            'title': title,
            'x_label': x_label,
            'y_label': y_label,
            'color_scheme': color_scheme,
            'line_width': line_width,
            'marker_size': marker_size,
            'show_markers': show_markers,
            'line_style': line_style,
            'fill_area': fill_area,
            'show_grid': show_grid,
            'smooth_lines': smooth_lines,
            'connect_gaps': connect_gaps
        })
    
    def validate_data(self, data: Union[pd.DataFrame, Dict, List]) -> bool:
        """
        Validate input data for line plot.
        
        Args:
            data: Input data (DataFrame, dict, or list)
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            if data is None:
                self.add_error("No data provided for line plot")
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
                self.add_error("Data must have at least two columns for line plot")
                return False
            
            return True
            
        except Exception as e:
            self.add_error(f"Data validation error: {str(e)}", e)
            return False
    
    def apply_smoothing(self, x_data: pd.Series, y_data: pd.Series, method: str = 'moving_average', window: int = 5) -> tuple:
        """
        Apply smoothing to line data.
        
        Args:
            x_data: X-axis data
            y_data: Y-axis data
            method: Smoothing method ('moving_average', 'exponential', 'polynomial')
            window: Window size for smoothing
            
        Returns:
            Tuple of (smoothed_x, smoothed_y)
        """
        try:
            # Combine and sort data
            df = pd.DataFrame({'x': x_data, 'y': y_data}).dropna().sort_values('x')
            
            if len(df) < window:
                return x_data, y_data
            
            if method == 'moving_average':
                df['y_smooth'] = df['y'].rolling(window=window, center=True).mean()
            elif method == 'exponential':
                df['y_smooth'] = df['y'].ewm(span=window).mean()
            elif method == 'polynomial':
                # Polynomial smoothing (degree 3)
                x_vals = np.arange(len(df))
                z = np.polyfit(x_vals, df['y'].values, min(3, len(df)-1))
                p = np.poly1d(z)
                df['y_smooth'] = p(x_vals)
            else:
                df['y_smooth'] = df['y']
            
            return df['x'], df['y_smooth'].fillna(df['y'])
            
        except Exception as e:
            self.add_error(f"Error applying smoothing: {str(e)}")
            return x_data, y_data
    
    def create_chart(self,
                    data: Union[pd.DataFrame, Dict, List],
                    x_column: str,
                    y_columns: Union[str, List[str]],
                    group_column: str = None,
                    hover_columns: List[str] = None,
                    custom_config: Dict = None) -> Optional[go.Figure]:
        """
        Create line plot from data.
        
        Args:
            data: Input data
            x_column: Column name for x-axis
            y_columns: Column name(s) for y-axis (can be list for multiple lines)
            group_column: Column name for grouping lines
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
            if x_column not in data.columns:
                self.add_error(f"X column '{x_column}' not found in data")
                return None
            
            # Handle multiple y columns
            if isinstance(y_columns, str):
                y_columns = [y_columns]
            
            missing_y_cols = [col for col in y_columns if col not in data.columns]
            if missing_y_cols:
                self.add_error(f"Missing Y columns: {missing_y_cols}")
                return None
            
            # Create figure
            fig = go.Figure()
            
            # Determine line mode
            if config['show_markers']:
                mode = 'lines+markers'
            else:
                mode = 'lines'
            
            # Color palette
            colors = px.colors.qualitative.Set1
            
            if group_column and group_column in data.columns:
                # Group by specified column
                groups = data[group_column].unique()
                for i, group in enumerate(groups):
                    group_data = data[data[group_column] == group]
                    
                    for j, y_col in enumerate(y_columns):
                        x_vals = group_data[x_column]
                        y_vals = group_data[y_col]
                        
                        # Apply smoothing if requested
                        if config['smooth_lines']:
                            x_vals, y_vals = self.apply_smoothing(x_vals, y_vals)
                        
                        line_name = f"{group} - {y_col}" if len(y_columns) > 1 else str(group)
                        color = colors[(i * len(y_columns) + j) % len(colors)]
                        
                        fig.add_trace(go.Scatter(
                            x=x_vals,
                            y=y_vals,
                            mode=mode,
                            name=line_name,
                            line=dict(
                                color=color,
                                width=config['line_width'],
                                dash=config['line_style']
                            ),
                            marker=dict(size=config['marker_size']),
                            fill='tonexty' if config['fill_area'] and i > 0 else None,
                            connectgaps=config['connect_gaps']
                        ))
            else:
                # No grouping, plot each y column as separate line
                for i, y_col in enumerate(y_columns):
                    x_vals = data[x_column]
                    y_vals = data[y_col]
                    
                    # Apply smoothing if requested
                    if config['smooth_lines']:
                        x_vals, y_vals = self.apply_smoothing(x_vals, y_vals)
                    
                    color = colors[i % len(colors)]
                    
                    fig.add_trace(go.Scatter(
                        x=x_vals,
                        y=y_vals,
                        mode=mode,
                        name=y_col,
                        line=dict(
                            color=color,
                            width=config['line_width'],
                            dash=config['line_style']
                        ),
                        marker=dict(size=config['marker_size']),
                        fill='tonexty' if config['fill_area'] and i > 0 else None,
                        connectgaps=config['connect_gaps']
                    ))
            
            # Update layout
            fig.update_layout(
                title=config['title'],
                xaxis_title=config['x_label'] or x_column,
                yaxis_title=config['y_label'] or ', '.join(y_columns),
                hovermode='x unified',
                template='plotly_white',
                showlegend=len(y_columns) > 1 or group_column is not None,
                xaxis=dict(showgrid=config['show_grid']),
                yaxis=dict(showgrid=config['show_grid'])
            )
            
            return fig
            
        except Exception as e:
            self.add_error(f"Error creating line plot: {str(e)}", e)
            return None
    
    def render(self,
              data: Union[pd.DataFrame, Dict, List],
              x_column: str,
              y_columns: Union[str, List[str]],
              group_column: str = None,
              hover_columns: List[str] = None,
              show_config: bool = False,
              show_stats: bool = False,
              height: int = 500) -> Optional[go.Figure]:
        """
        Render the line plot component.
        
        Args:
            data: Input data for the chart
            x_column: Column name for x-axis
            y_columns: Column name(s) for y-axis
            group_column: Column name for grouping lines
            hover_columns: Additional columns to show in hover
            show_config: Whether to show configuration options
            show_stats: Whether to show statistical annotations
            height: Chart height in pixels
            
        Returns:
            Plotly figure object or None if error
        """
        try:
            self.clear_messages()
            
            # Show configuration options if requested
            if show_config:
                st.subheader("Line Plot Configuration")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    self.chart_config['title'] = st.text_input(
                        "Chart Title",
                        value=self.chart_config['title'],
                        key=self.get_key('title')
                    )
                    
                    self.chart_config['line_width'] = st.slider(
                        "Line Width",
                        min_value=1,
                        max_value=5,
                        value=self.chart_config['line_width'],
                        key=self.get_key('line_width')
                    )
                    
                    self.chart_config['show_markers'] = st.checkbox(
                        "Show Markers",
                        value=self.chart_config['show_markers'],
                        key=self.get_key('show_markers')
                    )
                
                with col2:
                    self.chart_config['line_style'] = st.selectbox(
                        "Line Style",
                        options=['solid', 'dash', 'dot', 'dashdot'],
                        index=['solid', 'dash', 'dot', 'dashdot'].index(self.chart_config['line_style']),
                        key=self.get_key('line_style')
                    )
                    
                    self.chart_config['fill_area'] = st.checkbox(
                        "Fill Area",
                        value=self.chart_config['fill_area'],
                        key=self.get_key('fill_area')
                    )
                    
                    self.chart_config['smooth_lines'] = st.checkbox(
                        "Smooth Lines",
                        value=self.chart_config['smooth_lines'],
                        key=self.get_key('smooth_lines')
                    )
                
                with col3:
                    self.chart_config['show_grid'] = st.checkbox(
                        "Show Grid",
                        value=self.chart_config['show_grid'],
                        key=self.get_key('show_grid')
                    )
                    
                    self.chart_config['connect_gaps'] = st.checkbox(
                        "Connect Gaps",
                        value=self.chart_config['connect_gaps'],
                        key=self.get_key('connect_gaps')
                    )
                    
                    if self.chart_config['show_markers']:
                        self.chart_config['marker_size'] = st.slider(
                            "Marker Size",
                            min_value=3,
                            max_value=15,
                            value=self.chart_config['marker_size'],
                            key=self.get_key('marker_size')
                        )
            
            # Create and display chart
            fig = self.create_chart(data, x_column, y_columns, group_column, hover_columns)
            
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True, height=height)
                
                # Show data summary if requested
                if show_stats and isinstance(data, pd.DataFrame):
                    st.subheader("Data Summary")
                    y_cols = y_columns if isinstance(y_columns, list) else [y_columns]
                    summary_data = data[y_cols].describe()
                    st.dataframe(summary_data)
                
                # Log interaction
                self.log_interaction('chart_rendered', {
                    'chart_type': 'line',
                    'data_shape': getattr(data, 'shape', 'unknown') if hasattr(data, 'shape') else 'unknown',
                    'x_column': x_column,
                    'y_columns': y_columns,
                    'group_column': group_column
                })
                
                return fig
            else:
                self.display_messages()
                return None
            
        except Exception as e:
            self.add_error(f"Error rendering line plot: {str(e)}", e)
            self.display_messages()
            return None