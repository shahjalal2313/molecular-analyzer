"""
Distribution Plot Component for Molecular Analysis Visualization

Provides configurable distribution plot visualization for molecular property analysis.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union

from ..base import BaseComponent


class DistributionPlotComponent(BaseComponent):
    """
    Distribution plot component for displaying molecular property distributions.
    
    Features:
    - Multiple plot types (violin, box, strip, swarm)
    - Kernel density estimation
    - Multiple group comparisons
    - Statistical annotations
    - Customizable styling
    - Interactive hover information
    """
    
    def __init__(self, name: str = "Distribution Plot", key_prefix: str = None):
        """
        Initialize the distribution plot component.
        
        Args:
            name: Component display name
            key_prefix: Unique key prefix for Streamlit widgets
        """
        super().__init__(name, key_prefix)
        self.chart_config = {
            'title': '',
            'x_label': '',
            'y_label': '',
            'plot_type': 'violin',  # 'violin', 'box', 'strip', 'histogram', 'kde', 'distplot'
            'color_scheme': 'Set3',
            'show_points': True,
            'show_kde': True,
            'show_hist': True,
            'show_rug': False,
            'show_stats': True,
            'orientation': 'vertical',
            'box_width': 0.3,
            'violin_width': 0.8,
            'jitter': 0.1,
            'alpha': 0.7
        }
    
    def configure_chart(self, 
                       title: str = '',
                       x_label: str = '',
                       y_label: str = '',
                       plot_type: str = 'violin',
                       color_scheme: str = 'Set3',
                       show_points: bool = True,
                       show_kde: bool = True,
                       show_hist: bool = True,
                       show_rug: bool = False,
                       show_stats: bool = True,
                       orientation: str = 'vertical',
                       box_width: float = 0.3,
                       violin_width: float = 0.8,
                       jitter: float = 0.1,
                       alpha: float = 0.7) -> None:
        """
        Configure distribution plot appearance and behavior.
        
        Args:
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            plot_type: Type of plot ('violin', 'box', 'strip', 'histogram', 'kde', 'distplot')
            color_scheme: Color scheme for plots
            show_points: Whether to show individual points
            show_kde: Whether to show kernel density estimation
            show_hist: Whether to show histogram
            show_rug: Whether to show rug plot
            show_stats: Whether to show statistical annotations
            orientation: Plot orientation ('vertical' or 'horizontal')
            box_width: Width of box plots
            violin_width: Width of violin plots
            jitter: Amount of jitter for strip plots
            alpha: Transparency level
        """
        self.chart_config.update({
            'title': title,
            'x_label': x_label,
            'y_label': y_label,
            'plot_type': plot_type,
            'color_scheme': color_scheme,
            'show_points': show_points,
            'show_kde': show_kde,
            'show_hist': show_hist,
            'show_rug': show_rug,
            'show_stats': show_stats,
            'orientation': orientation,
            'box_width': box_width,
            'violin_width': violin_width,
            'jitter': jitter,
            'alpha': alpha
        })
    
    def validate_data(self, data: Union[pd.DataFrame, pd.Series, List, np.ndarray]) -> bool:
        """
        Validate input data for distribution plot.
        
        Args:
            data: Input data
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            if data is None:
                self.add_error("No data provided for distribution plot")
                return False
            
            # Convert to DataFrame if needed
            if isinstance(data, list):
                data = pd.DataFrame({'values': data})
            elif isinstance(data, np.ndarray):
                data = pd.DataFrame({'values': data.flatten()})
            elif isinstance(data, pd.Series):
                data = pd.DataFrame({'values': data})
            
            if not isinstance(data, pd.DataFrame):
                self.add_error("Data must be a pandas DataFrame, Series, list, or numpy array")
                return False
            
            if data.empty:
                self.add_error("Data is empty")
                return False
            
            # Check for at least one numeric column
            numeric_cols = data.select_dtypes(include=['number']).columns
            if len(numeric_cols) == 0:
                self.add_error("No numeric columns found")
                return False
            
            return True
            
        except Exception as e:
            self.add_error(f"Data validation error: {str(e)}", e)
            return False
    
    def calculate_kde(self, data: np.ndarray) -> tuple:
        """
        Calculate kernel density estimation.
        
        Args:
            data: Numeric data array
            
        Returns:
            Tuple of (x_values, kde_values)
        """
        try:
            from scipy import stats
            
            # Remove NaN values
            clean_data = data[~np.isnan(data)]
            
            if len(clean_data) < 2:
                return np.array([]), np.array([])
            
            # Calculate KDE
            kde = stats.gaussian_kde(clean_data)
            x_range = np.linspace(clean_data.min(), clean_data.max(), 200)
            kde_values = kde(x_range)
            
            return x_range, kde_values
            
        except ImportError:
            self.add_warning("scipy not available for KDE calculation")
            return np.array([]), np.array([])
        except Exception as e:
            self.add_error(f"Error calculating KDE: {str(e)}", e)
            return np.array([]), np.array([])
    
    def calculate_group_stats(self, data: pd.DataFrame, value_col: str, group_col: str = None) -> Dict:
        """
        Calculate statistical measures for groups.
        
        Args:
            data: Input DataFrame
            value_col: Column with values
            group_col: Column with groups (optional)
            
        Returns:
            Dictionary of statistics
        """
        try:
            stats = {}
            
            if group_col and group_col in data.columns:
                # Calculate stats for each group
                for group in data[group_col].unique():
                    group_data = data[data[group_col] == group][value_col].dropna()
                    if len(group_data) > 0:
                        stats[group] = {
                            'mean': np.mean(group_data),
                            'median': np.median(group_data),
                            'std': np.std(group_data),
                            'min': np.min(group_data),
                            'max': np.max(group_data),
                            'q25': np.percentile(group_data, 25),
                            'q75': np.percentile(group_data, 75),
                            'count': len(group_data)
                        }
            else:
                # Calculate stats for entire dataset
                clean_data = data[value_col].dropna()
                if len(clean_data) > 0:
                    stats['overall'] = {
                        'mean': np.mean(clean_data),
                        'median': np.median(clean_data),
                        'std': np.std(clean_data),
                        'min': np.min(clean_data),
                        'max': np.max(clean_data),
                        'q25': np.percentile(clean_data, 25),
                        'q75': np.percentile(clean_data, 75),
                        'count': len(clean_data)
                    }
            
            return stats
            
        except Exception as e:
            self.add_error(f"Error calculating statistics: {str(e)}", e)
            return {}
    
    def create_violin_plot(self, data: pd.DataFrame, value_col: str, group_col: str = None) -> go.Figure:
        """Create violin plot."""
        fig = go.Figure()
        
        if group_col and group_col in data.columns:
            # Multiple violins by group
            groups = data[group_col].unique()
            colors = getattr(px.colors.qualitative, self.chart_config['color_scheme'], px.colors.qualitative.Set3)
            
            for i, group in enumerate(groups):
                group_data = data[data[group_col] == group][value_col].dropna()
                if len(group_data) > 0:
                    fig.add_trace(go.Violin(
                        y=group_data if self.chart_config['orientation'] == 'vertical' else None,
                        x=group_data if self.chart_config['orientation'] == 'horizontal' else None,
                        name=str(group),
                        box_visible=True,
                        meanline_visible=True,
                        fillcolor=colors[i % len(colors)],
                        opacity=self.chart_config['alpha'],
                        points="all" if self.chart_config['show_points'] else False,
                        width=self.chart_config['violin_width']
                    ))
        else:
            # Single violin
            clean_data = data[value_col].dropna()
            fig.add_trace(go.Violin(
                y=clean_data if self.chart_config['orientation'] == 'vertical' else None,
                x=clean_data if self.chart_config['orientation'] == 'horizontal' else None,
                name=value_col,
                box_visible=True,
                meanline_visible=True,
                fillcolor=px.colors.qualitative.Set3[0],
                opacity=self.chart_config['alpha'],
                points="all" if self.chart_config['show_points'] else False,
                width=self.chart_config['violin_width']
            ))
        
        return fig
    
    def create_box_plot(self, data: pd.DataFrame, value_col: str, group_col: str = None) -> go.Figure:
        """Create box plot."""
        fig = go.Figure()
        
        if group_col and group_col in data.columns:
            # Multiple boxes by group
            groups = data[group_col].unique()
            colors = getattr(px.colors.qualitative, self.chart_config['color_scheme'], px.colors.qualitative.Set3)
            
            for i, group in enumerate(groups):
                group_data = data[data[group_col] == group][value_col].dropna()
                if len(group_data) > 0:
                    fig.add_trace(go.Box(
                        y=group_data if self.chart_config['orientation'] == 'vertical' else None,
                        x=group_data if self.chart_config['orientation'] == 'horizontal' else None,
                        name=str(group),
                        marker_color=colors[i % len(colors)],
                        boxpoints="all" if self.chart_config['show_points'] else False,
                        jitter=self.chart_config['jitter'],
                        width=self.chart_config['box_width']
                    ))
        else:
            # Single box
            clean_data = data[value_col].dropna()
            fig.add_trace(go.Box(
                y=clean_data if self.chart_config['orientation'] == 'vertical' else None,
                x=clean_data if self.chart_config['orientation'] == 'horizontal' else None,
                name=value_col,
                marker_color=px.colors.qualitative.Set3[0],
                boxpoints="all" if self.chart_config['show_points'] else False,
                jitter=self.chart_config['jitter'],
                width=self.chart_config['box_width']
            ))
        
        return fig
    
    def create_strip_plot(self, data: pd.DataFrame, value_col: str, group_col: str = None) -> go.Figure:
        """Create strip plot."""
        fig = go.Figure()
        
        if group_col and group_col in data.columns:
            # Multiple strips by group
            groups = data[group_col].unique()
            colors = getattr(px.colors.qualitative, self.chart_config['color_scheme'], px.colors.qualitative.Set3)
            
            for i, group in enumerate(groups):
                group_data = data[data[group_col] == group][value_col].dropna()
                if len(group_data) > 0:
                    # Add jitter to x-axis for vertical orientation
                    if self.chart_config['orientation'] == 'vertical':
                        x_jitter = np.random.normal(i, self.chart_config['jitter'], len(group_data))
                        fig.add_trace(go.Scatter(
                            x=x_jitter,
                            y=group_data,
                            mode='markers',
                            name=str(group),
                            marker=dict(color=colors[i % len(colors)], opacity=self.chart_config['alpha'])
                        ))
                    else:
                        y_jitter = np.random.normal(i, self.chart_config['jitter'], len(group_data))
                        fig.add_trace(go.Scatter(
                            x=group_data,
                            y=y_jitter,
                            mode='markers',
                            name=str(group),
                            marker=dict(color=colors[i % len(colors)], opacity=self.chart_config['alpha'])
                        ))
        else:
            # Single strip
            clean_data = data[value_col].dropna()
            if self.chart_config['orientation'] == 'vertical':
                x_jitter = np.random.normal(0, self.chart_config['jitter'], len(clean_data))
                fig.add_trace(go.Scatter(
                    x=x_jitter,
                    y=clean_data,
                    mode='markers',
                    name=value_col,
                    marker=dict(color=px.colors.qualitative.Set3[0], opacity=self.chart_config['alpha'])
                ))
            else:
                y_jitter = np.random.normal(0, self.chart_config['jitter'], len(clean_data))
                fig.add_trace(go.Scatter(
                    x=clean_data,
                    y=y_jitter,
                    mode='markers',
                    name=value_col,
                    marker=dict(color=px.colors.qualitative.Set3[0], opacity=self.chart_config['alpha'])
                ))
        
        return fig
    
    def create_distplot(self, data: pd.DataFrame, value_col: str, group_col: str = None) -> go.Figure:
        """Create distribution plot with histogram and KDE."""
        if group_col and group_col in data.columns:
            # Create distplot for each group
            groups = data[group_col].unique()
            group_data = []
            group_labels = []
            
            for group in groups:
                group_values = data[data[group_col] == group][value_col].dropna()
                if len(group_values) > 0:
                    group_data.append(group_values.values)
                    group_labels.append(str(group))
            
            if group_data:
                fig = ff.create_distplot(
                    group_data,
                    group_labels,
                    show_hist=self.chart_config['show_hist'],
                    show_curve=self.chart_config['show_kde'],
                    show_rug=self.chart_config['show_rug']
                )
            else:
                fig = go.Figure()
        else:
            # Single distplot
            clean_data = data[value_col].dropna()
            if len(clean_data) > 0:
                fig = ff.create_distplot(
                    [clean_data.values],
                    [value_col],
                    show_hist=self.chart_config['show_hist'],
                    show_curve=self.chart_config['show_kde'],
                    show_rug=self.chart_config['show_rug']
                )
            else:
                fig = go.Figure()
        
        return fig
    
    def create_chart(self, 
                    data: Union[pd.DataFrame, pd.Series, List, np.ndarray],
                    value_column: str = None,
                    group_column: str = None,
                    custom_config: Dict = None) -> Optional[go.Figure]:
        """
        Create distribution plot from data.
        
        Args:
            data: Input data
            value_column: Column name for values
            group_column: Column name for grouping
            custom_config: Additional chart configuration
            
        Returns:
            Plotly figure object or None if error
        """
        try:
            # Validate data
            if not self.validate_data(data):
                return None
            
            # Convert to DataFrame if needed
            if isinstance(data, (list, np.ndarray)):
                data = pd.DataFrame({'values': np.array(data).flatten()})
            elif isinstance(data, pd.Series):
                data = pd.DataFrame({'values': data})
            
            # Apply custom configuration
            config = self.chart_config.copy()
            if custom_config:
                config.update(custom_config)
            
            # Determine value column
            if value_column and value_column in data.columns:
                value_col = value_column
            else:
                numeric_cols = data.select_dtypes(include=['number']).columns
                if len(numeric_cols) == 0:
                    self.add_error("No numeric columns found")
                    return None
                value_col = numeric_cols[0]
            
            # Create appropriate plot type
            if config['plot_type'] == 'violin':
                fig = self.create_violin_plot(data, value_col, group_column)
            elif config['plot_type'] == 'box':
                fig = self.create_box_plot(data, value_col, group_column)
            elif config['plot_type'] == 'strip':
                fig = self.create_strip_plot(data, value_col, group_column)
            elif config['plot_type'] == 'distplot':
                fig = self.create_distplot(data, value_col, group_column)
            else:
                self.add_error(f"Unknown plot type: {config['plot_type']}")
                return None
            
            # Update layout
            fig.update_layout(
                title=config['title'] or f"{config['plot_type'].capitalize()} Plot",
                xaxis_title=config['x_label'] or (group_column if group_column else value_col),
                yaxis_title=config['y_label'] or value_col,
                template='plotly_white',
                hovermode='closest'
            )
            
            return fig
            
        except Exception as e:
            self.add_error(f"Error creating distribution plot: {str(e)}", e)
            return None
    
    def render(self, 
              data: Union[pd.DataFrame, pd.Series, List, np.ndarray],
              value_column: str = None,
              group_column: str = None,
              show_config: bool = False,
              height: int = 500) -> Optional[go.Figure]:
        """
        Render the distribution plot component.
        
        Args:
            data: Input data for the plot
            value_column: Column name for values
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
                st.subheader("Distribution Plot Configuration")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    self.chart_config['title'] = st.text_input(
                        "Chart Title", 
                        value=self.chart_config['title'],
                        key=self.get_key('title')
                    )
                    
                    self.chart_config['plot_type'] = st.selectbox(
                        "Plot Type",
                        options=['violin', 'box', 'strip', 'distplot'],
                        index=['violin', 'box', 'strip', 'distplot'].index(self.chart_config['plot_type']),
                        key=self.get_key('plot_type')
                    )
                    
                    self.chart_config['orientation'] = st.selectbox(
                        "Orientation",
                        options=['vertical', 'horizontal'],
                        index=['vertical', 'horizontal'].index(self.chart_config['orientation']),
                        key=self.get_key('orientation')
                    )
                
                with col2:
                    self.chart_config['show_points'] = st.checkbox(
                        "Show Points",
                        value=self.chart_config['show_points'],
                        key=self.get_key('show_points')
                    )
                    
                    self.chart_config['show_stats'] = st.checkbox(
                        "Show Statistics",
                        value=self.chart_config['show_stats'],
                        key=self.get_key('show_stats')
                    )
                    
                    self.chart_config['alpha'] = st.slider(
                        "Transparency",
                        min_value=0.1,
                        max_value=1.0,
                        value=self.chart_config['alpha'],
                        step=0.1,
                        key=self.get_key('alpha')
                    )
                
                with col3:
                    if self.chart_config['plot_type'] == 'distplot':
                        self.chart_config['show_hist'] = st.checkbox(
                            "Show Histogram",
                            value=self.chart_config['show_hist'],
                            key=self.get_key('show_hist')
                        )
                        
                        self.chart_config['show_kde'] = st.checkbox(
                            "Show KDE",
                            value=self.chart_config['show_kde'],
                            key=self.get_key('show_kde')
                        )
                        
                        self.chart_config['show_rug'] = st.checkbox(
                            "Show Rug",
                            value=self.chart_config['show_rug'],
                            key=self.get_key('show_rug')
                        )
                    else:
                        self.chart_config['jitter'] = st.slider(
                            "Jitter Amount",
                            min_value=0.0,
                            max_value=0.5,
                            value=self.chart_config['jitter'],
                            step=0.05,
                            key=self.get_key('jitter')
                        )
            
            # Create and display chart
            fig = self.create_chart(data, value_column, group_column)
            
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True, height=height)
                
                # Show statistics if enabled
                if self.chart_config['show_stats']:
                    if isinstance(data, pd.DataFrame):
                        value_col = value_column or data.select_dtypes(include=['number']).columns[0]
                        stats = self.calculate_group_stats(data, value_col, group_column)
                        
                        if stats:
                            st.subheader("Distribution Statistics")
                            
                            if group_column and len(stats) > 1:
                                # Multiple groups
                                for group, group_stats in stats.items():
                                    st.write(f"**{group}**")
                                    col1, col2, col3, col4 = st.columns(4)
                                    with col1:
                                        st.metric("Mean", f"{group_stats['mean']:.3f}")
                                        st.metric("Std Dev", f"{group_stats['std']:.3f}")
                                    with col2:
                                        st.metric("Median", f"{group_stats['median']:.3f}")
                                        st.metric("Count", f"{group_stats['count']}")
                                    with col3:
                                        st.metric("Min", f"{group_stats['min']:.3f}")
                                        st.metric("Q25", f"{group_stats['q25']:.3f}")
                                    with col4:
                                        st.metric("Max", f"{group_stats['max']:.3f}")
                                        st.metric("Q75", f"{group_stats['q75']:.3f}")
                                    st.divider()
                            else:
                                # Single group
                                group_stats = list(stats.values())[0]
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Mean", f"{group_stats['mean']:.3f}")
                                    st.metric("Std Dev", f"{group_stats['std']:.3f}")
                                with col2:
                                    st.metric("Median", f"{group_stats['median']:.3f}")
                                    st.metric("Count", f"{group_stats['count']}")
                                with col3:
                                    st.metric("Min", f"{group_stats['min']:.3f}")
                                    st.metric("Q25", f"{group_stats['q25']:.3f}")
                                with col4:
                                    st.metric("Max", f"{group_stats['max']:.3f}")
                                    st.metric("Q75", f"{group_stats['q75']:.3f}")
                
                # Log interaction
                self.log_interaction('chart_rendered', {
                    'chart_type': 'distribution_plot',
                    'plot_type': self.chart_config['plot_type'],
                    'data_shape': getattr(data, 'shape', 'unknown') if hasattr(data, 'shape') else 'unknown',
                    'value_column': value_column,
                    'group_column': group_column
                })
                
                return fig
            else:
                self.display_messages()
                return None
            
        except Exception as e:
            self.add_error(f"Error rendering distribution plot: {str(e)}", e)
            self.display_messages()
            return None