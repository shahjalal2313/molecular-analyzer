"""
Bar Chart Component for Molecular Analysis Visualization

Provides configurable bar chart visualization for molecular properties and analysis results.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Any, Dict, List, Optional, Union

from ..base import BaseComponent


class BarChartComponent(BaseComponent):
    """
    Bar chart component for displaying molecular analysis data.
    
    Features:
    - Multiple chart styles (grouped, stacked, horizontal)
    - Customizable colors and themes
    - Interactive hover information
    - Export capabilities
    - Error handling and validation
    """
    
    def __init__(self, name: str = "Bar Chart", key_prefix: str = None):
        """
        Initialize the bar chart component.
        
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
            'show_values': True,
            'orientation': 'vertical',
            'bar_mode': 'group'  # 'group', 'stack', 'overlay'
        }
    
    def configure_chart(self, 
                       title: str = '',
                       x_label: str = '',
                       y_label: str = '',
                       color_scheme: str = 'viridis',
                       show_values: bool = True,
                       orientation: str = 'vertical',
                       bar_mode: str = 'group') -> None:
        """
        Configure chart appearance and behavior.
        
        Args:
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            color_scheme: Plotly color scheme
            show_values: Whether to show values on bars
            orientation: 'vertical' or 'horizontal'
            bar_mode: 'group', 'stack', or 'overlay'
        """
        self.chart_config.update({
            'title': title,
            'x_label': x_label,
            'y_label': y_label,
            'color_scheme': color_scheme,
            'show_values': show_values,
            'orientation': orientation,
            'bar_mode': bar_mode
        })
    
    def validate_data(self, data: Union[pd.DataFrame, Dict, List]) -> bool:
        """
        Validate input data for bar chart.
        
        Args:
            data: Input data (DataFrame, dict, or list)
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            if data is None:
                self.add_error("No data provided for bar chart")
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
            
            if len(data.columns) < 1:
                self.add_error("Data must have at least one column")
                return False
            
            return True
            
        except Exception as e:
            self.add_error(f"Data validation error: {str(e)}", e)
            return False
    
    def create_chart(self, 
                    data: Union[pd.DataFrame, Dict, List],
                    x_column: str = None,
                    y_column: str = None,
                    color_column: str = None,
                    custom_config: Dict = None) -> Optional[go.Figure]:
        """
        Create bar chart from data.
        
        Args:
            data: Input data
            x_column: Column name for x-axis (if None, uses index)
            y_column: Column name for y-axis (if None, uses first numeric column)
            color_column: Column name for color grouping
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
            
            # Determine columns to use
            if x_column is None:
                x_values = data.index
                x_name = 'Index'
            else:
                if x_column not in data.columns:
                    self.add_error(f"X column '{x_column}' not found in data")
                    return None
                x_values = data[x_column]
                x_name = x_column
            
            if y_column is None:
                numeric_cols = data.select_dtypes(include=['number']).columns
                if len(numeric_cols) == 0:
                    self.add_error("No numeric columns found for y-axis")
                    return None
                y_column = numeric_cols[0]
            
            if y_column not in data.columns:
                self.add_error(f"Y column '{y_column}' not found in data")
                return None
            
            y_values = data[y_column]
            
            # Create figure
            if config['orientation'] == 'horizontal':
                if color_column and color_column in data.columns:
                    fig = px.bar(data, x=y_column, y=x_column, color=color_column,
                               orientation='h', color_discrete_sequence=px.colors.qualitative.Set3)
                else:
                    fig = go.Figure(data=[go.Bar(x=y_values, y=x_values, orientation='h')])
            else:
                if color_column and color_column in data.columns:
                    fig = px.bar(data, x=x_column, y=y_column, color=color_column,
                               barmode=config['bar_mode'], 
                               color_discrete_sequence=px.colors.qualitative.Set3)
                else:
                    fig = go.Figure(data=[go.Bar(x=x_values, y=y_values)])
            
            # Update layout
            fig.update_layout(
                title=config['title'],
                xaxis_title=config['x_label'] or x_name,
                yaxis_title=config['y_label'] or y_column,
                showlegend=bool(color_column),
                hovermode='x unified',
                template='plotly_white'
            )
            
            # Add value annotations if requested
            if config['show_values'] and not color_column:
                if config['orientation'] == 'horizontal':
                    fig.update_traces(texttemplate='%{x}', textposition='outside')
                else:
                    fig.update_traces(texttemplate='%{y}', textposition='outside')
            
            return fig
            
        except Exception as e:
            self.add_error(f"Error creating bar chart: {str(e)}", e)
            return None
    
    def render(self, 
              data: Union[pd.DataFrame, Dict, List],
              x_column: str = None,
              y_column: str = None,
              color_column: str = None,
              show_config: bool = False,
              height: int = 500) -> Optional[go.Figure]:
        """
        Render the bar chart component.
        
        Args:
            data: Input data for the chart
            x_column: Column name for x-axis
            y_column: Column name for y-axis  
            color_column: Column name for color grouping
            show_config: Whether to show configuration options
            height: Chart height in pixels
            
        Returns:
            Plotly figure object or None if error
        """
        try:
            self.clear_messages()
            
            # Show configuration options if requested
            if show_config:
                st.subheader("Bar Chart Configuration")
                
                col1, col2 = st.columns(2)
                with col1:
                    self.chart_config['title'] = st.text_input(
                        "Chart Title", 
                        value=self.chart_config['title'],
                        key=self.get_key('title')
                    )
                    
                    self.chart_config['orientation'] = st.selectbox(
                        "Orientation",
                        options=['vertical', 'horizontal'],
                        index=0 if self.chart_config['orientation'] == 'vertical' else 1,
                        key=self.get_key('orientation')
                    )
                
                with col2:
                    self.chart_config['bar_mode'] = st.selectbox(
                        "Bar Mode",
                        options=['group', 'stack', 'overlay'],
                        index=['group', 'stack', 'overlay'].index(self.chart_config['bar_mode']),
                        key=self.get_key('bar_mode')
                    )
                    
                    self.chart_config['show_values'] = st.checkbox(
                        "Show Values on Bars",
                        value=self.chart_config['show_values'],
                        key=self.get_key('show_values')
                    )
            
            # Create and display chart
            fig = self.create_chart(data, x_column, y_column, color_column)
            
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True, height=height)
                
                # Log interaction
                self.log_interaction('chart_rendered', {
                    'chart_type': 'bar',
                    'data_shape': getattr(data, 'shape', 'unknown') if hasattr(data, 'shape') else 'unknown',
                    'x_column': x_column,
                    'y_column': y_column,
                    'color_column': color_column
                })
                
                return fig
            else:
                self.display_messages()
                return None
            
        except Exception as e:
            self.add_error(f"Error rendering bar chart: {str(e)}", e)
            self.display_messages()
            return None