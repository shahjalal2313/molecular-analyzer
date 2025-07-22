"""
Correlation Matrix Component for Molecular Analysis Visualization

Provides configurable correlation matrix visualization for molecular property relationships.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union

from ..base import BaseComponent


class CorrelationMatrixComponent(BaseComponent):
    """
    Correlation matrix component for displaying relationships between molecular properties.
    
    Features:
    - Multiple correlation methods (Pearson, Spearman, Kendall)
    - Customizable color scales and themes
    - Interactive hover information
    - Hierarchical clustering option
    - Significance testing
    - Export capabilities
    """
    
    def __init__(self, name: str = "Correlation Matrix", key_prefix: str = None):
        """
        Initialize the correlation matrix component.
        
        Args:
            name: Component display name
            key_prefix: Unique key prefix for Streamlit widgets
        """
        super().__init__(name, key_prefix)
        self.chart_config = {
            'title': '',
            'color_scale': 'RdBu_r',
            'method': 'pearson',  # 'pearson', 'spearman', 'kendall'
            'show_values': True,
            'show_dendrograms': False,
            'cluster_rows': False,
            'cluster_cols': False,
            'mask_diagonal': False,
            'mask_upper': False,
            'min_periods': 1,
            'significance_level': 0.05
        }
    
    def configure_chart(self, 
                       title: str = '',
                       color_scale: str = 'RdBu_r',
                       method: str = 'pearson',
                       show_values: bool = True,
                       show_dendrograms: bool = False,
                       cluster_rows: bool = False,
                       cluster_cols: bool = False,
                       mask_diagonal: bool = False,
                       mask_upper: bool = False,
                       min_periods: int = 1,
                       significance_level: float = 0.05) -> None:
        """
        Configure correlation matrix appearance and behavior.
        
        Args:
            title: Chart title
            color_scale: Plotly color scale
            method: Correlation method ('pearson', 'spearman', 'kendall')
            show_values: Whether to show correlation values
            show_dendrograms: Whether to show dendrograms (requires clustering)
            cluster_rows: Whether to cluster rows
            cluster_cols: Whether to cluster columns
            mask_diagonal: Whether to mask diagonal values
            mask_upper: Whether to mask upper triangle
            min_periods: Minimum number of observations for correlation
            significance_level: Significance level for statistical tests
        """
        self.chart_config.update({
            'title': title,
            'color_scale': color_scale,
            'method': method,
            'show_values': show_values,
            'show_dendrograms': show_dendrograms,
            'cluster_rows': cluster_rows,
            'cluster_cols': cluster_cols,
            'mask_diagonal': mask_diagonal,
            'mask_upper': mask_upper,
            'min_periods': min_periods,
            'significance_level': significance_level
        })
    
    def validate_data(self, data: Union[pd.DataFrame, np.ndarray]) -> bool:
        """
        Validate input data for correlation matrix.
        
        Args:
            data: Input data
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            if data is None:
                self.add_error("No data provided for correlation matrix")
                return False
            
            # Convert to DataFrame if needed
            if isinstance(data, np.ndarray):
                data = pd.DataFrame(data)
            
            if not isinstance(data, pd.DataFrame):
                self.add_error("Data must be a pandas DataFrame or numpy array")
                return False
            
            if data.empty:
                self.add_error("Data is empty")
                return False
            
            # Check for numeric columns
            numeric_cols = data.select_dtypes(include=['number']).columns
            if len(numeric_cols) < 2:
                self.add_error("Need at least 2 numeric columns for correlation matrix")
                return False
            
            # Check for sufficient data
            if len(data) < 2:
                self.add_error("Need at least 2 observations for correlation")
                return False
            
            return True
            
        except Exception as e:
            self.add_error(f"Data validation error: {str(e)}", e)
            return False
    
    def calculate_correlation(self, data: pd.DataFrame, method: str = 'pearson') -> pd.DataFrame:
        """
        Calculate correlation matrix.
        
        Args:
            data: Input DataFrame
            method: Correlation method
            
        Returns:
            Correlation matrix DataFrame
        """
        try:
            # Select only numeric columns
            numeric_data = data.select_dtypes(include=['number'])
            
            # Calculate correlation
            if method == 'pearson':
                corr_matrix = numeric_data.corr(method='pearson', min_periods=self.chart_config['min_periods'])
            elif method == 'spearman':
                corr_matrix = numeric_data.corr(method='spearman', min_periods=self.chart_config['min_periods'])
            elif method == 'kendall':
                corr_matrix = numeric_data.corr(method='kendall', min_periods=self.chart_config['min_periods'])
            else:
                self.add_error(f"Unknown correlation method: {method}")
                return pd.DataFrame()
            
            return corr_matrix
            
        except Exception as e:
            self.add_error(f"Error calculating correlation: {str(e)}", e)
            return pd.DataFrame()
    
    def calculate_significance(self, data: pd.DataFrame, method: str = 'pearson') -> pd.DataFrame:
        """
        Calculate p-values for correlation coefficients.
        
        Args:
            data: Input DataFrame
            method: Correlation method
            
        Returns:
            P-values matrix DataFrame
        """
        try:
            from scipy.stats import pearsonr, spearmanr, kendalltau
            
            numeric_data = data.select_dtypes(include=['number'])
            n_vars = len(numeric_data.columns)
            p_values = np.ones((n_vars, n_vars))
            
            for i in range(n_vars):
                for j in range(i+1, n_vars):
                    col1, col2 = numeric_data.columns[i], numeric_data.columns[j]
                    
                    # Remove NaN values
                    valid_data = numeric_data[[col1, col2]].dropna()
                    
                    if len(valid_data) >= self.chart_config['min_periods']:
                        if method == 'pearson':
                            _, p_val = pearsonr(valid_data[col1], valid_data[col2])
                        elif method == 'spearman':
                            _, p_val = spearmanr(valid_data[col1], valid_data[col2])
                        elif method == 'kendall':
                            _, p_val = kendalltau(valid_data[col1], valid_data[col2])
                        else:
                            p_val = 1.0
                        
                        p_values[i, j] = p_val
                        p_values[j, i] = p_val
            
            return pd.DataFrame(p_values, index=numeric_data.columns, columns=numeric_data.columns)
            
        except ImportError:
            self.add_warning("scipy not available for significance testing")
            return pd.DataFrame()
        except Exception as e:
            self.add_error(f"Error calculating significance: {str(e)}", e)
            return pd.DataFrame()
    
    def cluster_matrix(self, corr_matrix: pd.DataFrame) -> tuple:
        """
        Perform hierarchical clustering on correlation matrix.
        
        Args:
            corr_matrix: Correlation matrix
            
        Returns:
            Tuple of (clustered_matrix, row_order, col_order)
        """
        try:
            from scipy.cluster.hierarchy import dendrogram, linkage
            from scipy.spatial.distance import squareform
            
            # Convert correlation to distance
            distance_matrix = 1 - np.abs(corr_matrix)
            
            # Perform clustering
            row_linkage = linkage(squareform(distance_matrix), method='ward')
            col_linkage = linkage(squareform(distance_matrix.T), method='ward')
            
            # Get dendrogram order
            row_dendro = dendrogram(row_linkage, no_plot=True)
            col_dendro = dendrogram(col_linkage, no_plot=True)
            
            row_order = row_dendro['leaves']
            col_order = col_dendro['leaves']
            
            # Reorder matrix
            clustered_matrix = corr_matrix.iloc[row_order, col_order]
            
            return clustered_matrix, row_order, col_order
            
        except ImportError:
            self.add_warning("scipy not available for clustering")
            return corr_matrix, list(range(len(corr_matrix))), list(range(len(corr_matrix.columns)))
        except Exception as e:
            self.add_error(f"Error clustering matrix: {str(e)}", e)
            return corr_matrix, list(range(len(corr_matrix))), list(range(len(corr_matrix.columns)))
    
    def create_chart(self, 
                    data: Union[pd.DataFrame, np.ndarray],
                    columns: List[str] = None,
                    custom_config: Dict = None) -> Optional[go.Figure]:
        """
        Create correlation matrix heatmap.
        
        Args:
            data: Input data
            columns: Specific columns to include
            custom_config: Additional chart configuration
            
        Returns:
            Plotly figure object or None if error
        """
        try:
            # Validate data
            if not self.validate_data(data):
                return None
            
            # Convert to DataFrame if needed
            if isinstance(data, np.ndarray):
                data = pd.DataFrame(data)
            
            # Apply custom configuration
            config = self.chart_config.copy()
            if custom_config:
                config.update(custom_config)
            
            # Select columns
            if columns:
                available_cols = [col for col in columns if col in data.columns]
                if not available_cols:
                    self.add_error("None of the specified columns found in data")
                    return None
                data = data[available_cols]
            
            # Calculate correlation matrix
            corr_matrix = self.calculate_correlation(data, config['method'])
            if corr_matrix.empty:
                return None
            
            # Calculate significance if requested
            p_values = pd.DataFrame()
            if config['significance_level'] > 0:
                p_values = self.calculate_significance(data, config['method'])
            
            # Apply clustering if requested
            if config['cluster_rows'] or config['cluster_cols']:
                corr_matrix, row_order, col_order = self.cluster_matrix(corr_matrix)
                if not p_values.empty:
                    p_values = p_values.iloc[row_order, col_order]
            
            # Apply masking
            display_matrix = corr_matrix.copy()
            
            if config['mask_diagonal']:
                np.fill_diagonal(display_matrix.values, np.nan)
            
            if config['mask_upper']:
                mask = np.triu(np.ones_like(display_matrix.values, dtype=bool))
                display_matrix.values[mask] = np.nan
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=display_matrix.values,
                x=display_matrix.columns,
                y=display_matrix.index,
                colorscale=config['color_scale'],
                zmid=0,
                zmin=-1,
                zmax=1,
                showscale=True,
                hovertemplate='<b>%{y}</b> vs <b>%{x}</b><br>' +
                             'Correlation: %{z:.3f}<br>' +
                             '<extra></extra>',
                colorbar=dict(
                    title=f"{config['method'].capitalize()} Correlation",
                    titleside="right"
                )
            ))
            
            # Add text annotations if requested
            if config['show_values']:
                annotations = []
                for i, row in enumerate(display_matrix.index):
                    for j, col in enumerate(display_matrix.columns):
                        value = display_matrix.iloc[i, j]
                        if not np.isnan(value):
                            # Color text based on correlation strength
                            text_color = 'white' if abs(value) > 0.6 else 'black'
                            
                            # Add significance indicator
                            text = f'{value:.2f}'
                            if not p_values.empty:
                                p_val = p_values.iloc[i, j]
                                if p_val < config['significance_level']:
                                    text += '*'
                                elif p_val < config['significance_level'] * 2:
                                    text += '†'
                            
                            annotations.append(
                                dict(
                                    x=col,
                                    y=row,
                                    text=text,
                                    showarrow=False,
                                    font=dict(color=text_color, size=10)
                                )
                            )
                
                fig.update_layout(annotations=annotations)
            
            # Update layout
            fig.update_layout(
                title=config['title'] or f"{config['method'].capitalize()} Correlation Matrix",
                xaxis_title="",
                yaxis_title="",
                template='plotly_white',
                height=max(400, len(display_matrix) * 40),
                width=max(400, len(display_matrix.columns) * 40)
            )
            
            # Adjust axis to show all labels
            fig.update_xaxes(side="bottom", tickangle=45)
            fig.update_yaxes(side="left")
            
            return fig
            
        except Exception as e:
            self.add_error(f"Error creating correlation matrix: {str(e)}", e)
            return None
    
    def render(self, 
              data: Union[pd.DataFrame, np.ndarray],
              columns: List[str] = None,
              show_config: bool = False,
              height: int = None) -> Optional[go.Figure]:
        """
        Render the correlation matrix component.
        
        Args:
            data: Input data for the correlation matrix
            columns: Specific columns to include
            show_config: Whether to show configuration options
            height: Chart height in pixels
            
        Returns:
            Plotly figure object or None if error
        """
        try:
            self.clear_messages()
            
            # Show configuration options if requested
            if show_config:
                st.subheader("Correlation Matrix Configuration")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    self.chart_config['title'] = st.text_input(
                        "Chart Title", 
                        value=self.chart_config['title'],
                        key=self.get_key('title')
                    )
                    
                    self.chart_config['method'] = st.selectbox(
                        "Correlation Method",
                        options=['pearson', 'spearman', 'kendall'],
                        index=['pearson', 'spearman', 'kendall'].index(self.chart_config['method']),
                        key=self.get_key('method')
                    )
                    
                    self.chart_config['color_scale'] = st.selectbox(
                        "Color Scale",
                        options=['RdBu_r', 'RdYlBu_r', 'viridis', 'plasma', 'coolwarm'],
                        index=['RdBu_r', 'RdYlBu_r', 'viridis', 'plasma', 'coolwarm'].index(self.chart_config['color_scale']),
                        key=self.get_key('color_scale')
                    )
                
                with col2:
                    self.chart_config['show_values'] = st.checkbox(
                        "Show Values",
                        value=self.chart_config['show_values'],
                        key=self.get_key('show_values')
                    )
                    
                    self.chart_config['mask_diagonal'] = st.checkbox(
                        "Mask Diagonal",
                        value=self.chart_config['mask_diagonal'],
                        key=self.get_key('mask_diagonal')
                    )
                    
                    self.chart_config['mask_upper'] = st.checkbox(
                        "Mask Upper Triangle",
                        value=self.chart_config['mask_upper'],
                        key=self.get_key('mask_upper')
                    )
                
                with col3:
                    self.chart_config['cluster_rows'] = st.checkbox(
                        "Cluster Rows",
                        value=self.chart_config['cluster_rows'],
                        key=self.get_key('cluster_rows')
                    )
                    
                    self.chart_config['cluster_cols'] = st.checkbox(
                        "Cluster Columns",
                        value=self.chart_config['cluster_cols'],
                        key=self.get_key('cluster_cols')
                    )
                    
                    self.chart_config['significance_level'] = st.slider(
                        "Significance Level",
                        min_value=0.001,
                        max_value=0.1,
                        value=self.chart_config['significance_level'],
                        step=0.001,
                        key=self.get_key('significance_level')
                    )
            
            # Create and display chart
            fig = self.create_chart(data, columns)
            
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True, height=height)
                
                # Show correlation statistics
                if isinstance(data, pd.DataFrame):
                    numeric_data = data.select_dtypes(include=['number'])
                    if len(numeric_data.columns) > 1:
                        corr_matrix = self.calculate_correlation(data, self.chart_config['method'])
                        
                        if not corr_matrix.empty:
                            st.subheader("Correlation Statistics")
                            
                            # Get upper triangle correlations (excluding diagonal)
                            upper_triangle = corr_matrix.where(
                                np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
                            )
                            correlations = upper_triangle.stack().dropna()
                            
                            if len(correlations) > 0:
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Highest Correlation", f"{correlations.max():.3f}")
                                    st.metric("Lowest Correlation", f"{correlations.min():.3f}")
                                with col2:
                                    st.metric("Mean |Correlation|", f"{np.abs(correlations).mean():.3f}")
                                    st.metric("Std |Correlation|", f"{np.abs(correlations).std():.3f}")
                                with col3:
                                    strong_corr = (np.abs(correlations) > 0.7).sum()
                                    st.metric("Strong Correlations (>0.7)", f"{strong_corr}")
                                    moderate_corr = ((np.abs(correlations) > 0.3) & (np.abs(correlations) <= 0.7)).sum()
                                    st.metric("Moderate Correlations (0.3-0.7)", f"{moderate_corr}")
                                with col4:
                                    # Find strongest correlation pair
                                    max_corr_idx = np.abs(correlations).idxmax()
                                    st.metric("Strongest Pair", f"{max_corr_idx[0]} - {max_corr_idx[1]}")
                                    st.metric("Value", f"{correlations.loc[max_corr_idx]:.3f}")
                
                # Log interaction
                self.log_interaction('chart_rendered', {
                    'chart_type': 'correlation_matrix',
                    'data_shape': getattr(data, 'shape', 'unknown') if hasattr(data, 'shape') else 'unknown',
                    'method': self.chart_config['method'],
                    'columns': columns,
                    'n_variables': len(data.select_dtypes(include=['number']).columns) if isinstance(data, pd.DataFrame) else 'unknown'
                })
                
                return fig
            else:
                self.display_messages()
                return None
            
        except Exception as e:
            self.add_error(f"Error rendering correlation matrix: {str(e)}", e)
            self.display_messages()
            return None