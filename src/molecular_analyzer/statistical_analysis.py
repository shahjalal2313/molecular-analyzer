"""
Statistical Analysis Module

This module provides statistical analysis capabilities for molecular datasets,
including descriptive statistics, correlation analysis, and data visualization
for batch processing results.
"""

from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import pearsonr, spearmanr
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings


class MolecularStatisticalAnalyzer:
    """
    Statistical analyzer for molecular datasets.
    
    This class provides comprehensive statistical analysis capabilities for
    molecular property datasets including descriptive statistics, correlation
    analysis, outlier detection, and data visualization.
    
    Examples:
        >>> analyzer = MolecularStatisticalAnalyzer()
        >>> data = [{"molecular_weight": 180.2, "logP": 2.1, "tpsa": 40.5}]
        >>> stats = analyzer.calculate_descriptive_statistics(data)
        >>> print(stats["molecular_weight"]["mean"])
        180.2
    """
    
    def __init__(self, significance_level: float = 0.05):
        """
        Initialize the statistical analyzer.
        
        Args:
            significance_level (float): Significance level for statistical tests
        """
        self.significance_level = significance_level
        self.numeric_properties = [
            'molecular_weight', 'logP', 'tpsa', 'hbd', 'hba', 
            'num_atoms', 'num_bonds', 'num_heavy_atoms', 'num_rings',
            'num_aromatic_rings', 'num_rotatable_bonds', 'lipinski_violations'
        ]
    
    def calculate_descriptive_statistics(self, data: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """
        Calculate descriptive statistics for molecular properties.
        
        Args:
            data (List[Dict[str, Any]]): List of molecular property dictionaries
            
        Returns:
            Dict[str, Dict[str, float]]: Descriptive statistics for each property
            
        Examples:
            >>> analyzer = MolecularStatisticalAnalyzer()
            >>> data = [{"molecular_weight": 180.2, "logP": 2.1}]
            >>> stats = analyzer.calculate_descriptive_statistics(data)
            >>> "molecular_weight" in stats
            True
        """
        df = pd.DataFrame(data)
        statistics = {}
        
        for prop in self.numeric_properties:
            if prop in df.columns:
                values = df[prop].dropna()
                if len(values) > 0:
                    try:
                        statistics[prop] = {
                            'count': len(values),
                            'mean': float(np.mean(values)),
                            'median': float(np.median(values)),
                            'std': float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
                            'min': float(np.min(values)),
                            'max': float(np.max(values)),
                            'q25': float(np.percentile(values, 25)),
                            'q75': float(np.percentile(values, 75)),
                            'iqr': float(np.percentile(values, 75) - np.percentile(values, 25)),
                            'skewness': float(stats.skew(values)),
                            'kurtosis': float(stats.kurtosis(values)),
                            'cv': float(np.std(values, ddof=1) / np.mean(values)) if np.mean(values) != 0 else 0.0
                        }
                    except Exception as e:
                        statistics[prop] = {'error': str(e)}
        
        return statistics
    
    def calculate_correlation_matrix(self, data: List[Dict[str, Any]], 
                                   method: str = 'pearson') -> Dict[str, Any]:
        """
        Calculate correlation matrix for molecular properties.
        
        Args:
            data (List[Dict[str, Any]]): List of molecular property dictionaries
            method (str): Correlation method ('pearson', 'spearman', 'kendall')
            
        Returns:
            Dict[str, Any]: Correlation matrix and p-values
            
        Examples:
            >>> analyzer = MolecularStatisticalAnalyzer()
            >>> data = [{"molecular_weight": 180.2, "logP": 2.1}]
            >>> corr = analyzer.calculate_correlation_matrix(data)
            >>> "correlation_matrix" in corr
            True
        """
        df = pd.DataFrame(data)
        
        # Filter numeric columns that exist in the data
        numeric_cols = [col for col in self.numeric_properties if col in df.columns]
        
        if len(numeric_cols) < 2:
            return {'error': 'Need at least 2 numeric properties for correlation analysis'}
        
        # Get numeric data
        numeric_data = df[numeric_cols].dropna()
        
        if len(numeric_data) < 2:
            return {'error': 'Need at least 2 valid data points for correlation analysis'}
        
        try:
            # Calculate correlation matrix
            if method == 'pearson':
                corr_matrix = numeric_data.corr(method='pearson')
            elif method == 'spearman':
                corr_matrix = numeric_data.corr(method='spearman')
            elif method == 'kendall':
                corr_matrix = numeric_data.corr(method='kendall')
            else:
                return {'error': f'Unsupported correlation method: {method}'}
            
            # Calculate p-values
            p_values = pd.DataFrame(index=corr_matrix.index, columns=corr_matrix.columns)
            
            for i, col1 in enumerate(corr_matrix.columns):
                for j, col2 in enumerate(corr_matrix.columns):
                    if i != j:
                        if method == 'pearson':
                            _, p_val = pearsonr(numeric_data[col1], numeric_data[col2])
                        elif method == 'spearman':
                            _, p_val = spearmanr(numeric_data[col1], numeric_data[col2])
                        else:
                            # Kendall tau
                            _, p_val = stats.kendalltau(numeric_data[col1], numeric_data[col2])
                        p_values.loc[col1, col2] = p_val
                    else:
                        p_values.loc[col1, col2] = 0.0
            
            return {
                'correlation_matrix': corr_matrix.to_dict(),
                'p_values': p_values.to_dict(),
                'method': method,
                'n_samples': len(numeric_data),
                'properties': list(corr_matrix.columns)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def detect_outliers(self, data: List[Dict[str, Any]], 
                       method: str = 'iqr') -> Dict[str, Any]:
        """
        Detect outliers in molecular properties.
        
        Args:
            data (List[Dict[str, Any]]): List of molecular property dictionaries
            method (str): Outlier detection method ('iqr', 'zscore', 'modified_zscore')
            
        Returns:
            Dict[str, Any]: Outlier detection results
            
        Examples:
            >>> analyzer = MolecularStatisticalAnalyzer()
            >>> data = [{"molecular_weight": i} for i in [100, 200, 300, 1000]]
            >>> outliers = analyzer.detect_outliers(data)
            >>> "outlier_indices" in outliers
            True
        """
        df = pd.DataFrame(data)
        results = {}
        
        for prop in self.numeric_properties:
            if prop in df.columns:
                values = df[prop].dropna()
                if len(values) > 0:
                    try:
                        if method == 'iqr':
                            q1 = values.quantile(0.25)
                            q3 = values.quantile(0.75)
                            iqr = q3 - q1
                            lower_bound = q1 - 1.5 * iqr
                            upper_bound = q3 + 1.5 * iqr
                            outlier_mask = (values < lower_bound) | (values > upper_bound)
                            
                        elif method == 'zscore':
                            z_scores = np.abs(stats.zscore(values))
                            outlier_mask = z_scores > 3
                            lower_bound = values.mean() - 3 * values.std()
                            upper_bound = values.mean() + 3 * values.std()
                            
                        elif method == 'modified_zscore':
                            median = np.median(values)
                            mad = np.median(np.abs(values - median))
                            modified_z_scores = 0.6745 * (values - median) / mad
                            outlier_mask = np.abs(modified_z_scores) > 3.5
                            lower_bound = median - 3.5 * mad / 0.6745
                            upper_bound = median + 3.5 * mad / 0.6745
                            
                        else:
                            results[prop] = {'error': f'Unsupported method: {method}'}
                            continue
                        
                        outlier_indices = values[outlier_mask].index.tolist()
                        outlier_values = values[outlier_mask].tolist()
                        
                        results[prop] = {
                            'n_outliers': len(outlier_indices),
                            'outlier_indices': outlier_indices,
                            'outlier_values': outlier_values,
                            'outlier_percentage': len(outlier_indices) / len(values) * 100,
                            'method': method,
                            'lower_bound': float(lower_bound),
                            'upper_bound': float(upper_bound)
                        }
                        
                    except Exception as e:
                        results[prop] = {'error': str(e)}
        
        return results
    
    def create_distribution_plots(self, data: List[Dict[str, Any]], 
                                properties: Optional[List[str]] = None) -> Dict[str, go.Figure]:
        """
        Create distribution plots for molecular properties.
        
        Args:
            data (List[Dict[str, Any]]): List of molecular property dictionaries
            properties (List[str], optional): Properties to plot. If None, plots all numeric properties
            
        Returns:
            Dict[str, go.Figure]: Dictionary of Plotly figures
            
        Examples:
            >>> analyzer = MolecularStatisticalAnalyzer()
            >>> data = [{"molecular_weight": 180.2, "logP": 2.1}]
            >>> plots = analyzer.create_distribution_plots(data)
            >>> isinstance(plots.get("molecular_weight"), go.Figure)
            True
        """
        df = pd.DataFrame(data)
        plots = {}
        
        if properties is None:
            properties = [prop for prop in self.numeric_properties if prop in df.columns]
        
        for prop in properties:
            if prop in df.columns:
                values = df[prop].dropna()
                if len(values) > 0:
                    try:
                        # Create histogram with density curve
                        fig = px.histogram(
                            x=values, 
                            nbins=30,
                            title=f'Distribution of {prop}',
                            labels={'x': prop, 'y': 'Frequency'},
                            marginal='box'
                        )
                        
                        # Add mean and median lines
                        fig.add_vline(x=values.mean(), line_dash="dash", line_color="red", 
                                    annotation_text=f"Mean: {values.mean():.2f}")
                        fig.add_vline(x=values.median(), line_dash="dash", line_color="green", 
                                    annotation_text=f"Median: {values.median():.2f}")
                        
                        fig.update_layout(
                            showlegend=True,
                            height=500,
                            font=dict(size=12)
                        )
                        
                        plots[prop] = fig
                        
                    except Exception as e:
                        print(f"Error creating plot for {prop}: {e}")
        
        return plots
    
    def create_correlation_heatmap(self, data: List[Dict[str, Any]], 
                                 method: str = 'pearson') -> Optional[go.Figure]:
        """
        Create correlation heatmap for molecular properties.
        
        Args:
            data (List[Dict[str, Any]]): List of molecular property dictionaries
            method (str): Correlation method ('pearson', 'spearman', 'kendall')
            
        Returns:
            Optional[go.Figure]: Plotly heatmap figure or None if error
            
        Examples:
            >>> analyzer = MolecularStatisticalAnalyzer()
            >>> data = [{"molecular_weight": 180.2, "logP": 2.1}]
            >>> fig = analyzer.create_correlation_heatmap(data)
            >>> isinstance(fig, go.Figure)
            True
        """
        corr_result = self.calculate_correlation_matrix(data, method)
        
        if 'error' in corr_result:
            return None
        
        try:
            corr_matrix = pd.DataFrame(corr_result['correlation_matrix'])
            
            # Create heatmap
            fig = px.imshow(
                corr_matrix,
                color_continuous_scale='RdBu',
                aspect='auto',
                title=f'Correlation Matrix ({method.title()})',
                labels={'color': 'Correlation'}
            )
            
            # Add correlation values as text
            for i in range(len(corr_matrix.index)):
                for j in range(len(corr_matrix.columns)):
                    fig.add_annotation(
                        x=j, y=i,
                        text=f"{corr_matrix.iloc[i, j]:.2f}",
                        showarrow=False,
                        font=dict(color="white" if abs(corr_matrix.iloc[i, j]) > 0.5 else "black")
                    )
            
            fig.update_layout(
                height=600,
                width=600,
                font=dict(size=12)
            )
            
            return fig
            
        except Exception as e:
            print(f"Error creating correlation heatmap: {e}")
            return None
    
    def create_scatter_plot_matrix(self, data: List[Dict[str, Any]], 
                                 properties: Optional[List[str]] = None) -> Optional[go.Figure]:
        """
        Create scatter plot matrix for molecular properties.
        
        Args:
            data (List[Dict[str, Any]]): List of molecular property dictionaries
            properties (List[str], optional): Properties to include in matrix
            
        Returns:
            Optional[go.Figure]: Plotly scatter plot matrix or None if error
            
        Examples:
            >>> analyzer = MolecularStatisticalAnalyzer()
            >>> data = [{"molecular_weight": 180.2, "logP": 2.1}]
            >>> fig = analyzer.create_scatter_plot_matrix(data)
            >>> isinstance(fig, go.Figure)
            True
        """
        df = pd.DataFrame(data)
        
        if properties is None:
            properties = [prop for prop in self.numeric_properties if prop in df.columns]
        
        # Limit to first 6 properties for readability
        properties = properties[:6]
        
        if len(properties) < 2:
            return None
        
        try:
            numeric_data = df[properties].dropna()
            
            fig = px.scatter_matrix(
                numeric_data,
                dimensions=properties,
                title="Scatter Plot Matrix",
                height=800,
                width=800
            )
            
            fig.update_layout(
                font=dict(size=10)
            )
            
            return fig
            
        except Exception as e:
            print(f"Error creating scatter plot matrix: {e}")
            return None
    
    def perform_normality_tests(self, data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Perform normality tests on molecular properties.
        
        Args:
            data (List[Dict[str, Any]]): List of molecular property dictionaries
            
        Returns:
            Dict[str, Dict[str, Any]]: Normality test results
            
        Examples:
            >>> analyzer = MolecularStatisticalAnalyzer()
            >>> data = [{"molecular_weight": i} for i in range(100, 200)]
            >>> results = analyzer.perform_normality_tests(data)
            >>> "molecular_weight" in results
            True
        """
        df = pd.DataFrame(data)
        results = {}
        
        for prop in self.numeric_properties:
            if prop in df.columns:
                values = df[prop].dropna()
                if len(values) >= 3:  # Minimum sample size for normality tests
                    try:
                        # Shapiro-Wilk test (for small samples)
                        if len(values) <= 5000:
                            shapiro_stat, shapiro_p = stats.shapiro(values)
                        else:
                            shapiro_stat, shapiro_p = None, None
                        
                        # Kolmogorov-Smirnov test
                        ks_stat, ks_p = stats.kstest(values, 'norm', args=(values.mean(), values.std()))
                        
                        # Anderson-Darling test
                        ad_result = stats.anderson(values, dist='norm')
                        
                        results[prop] = {
                            'sample_size': len(values),
                            'shapiro_wilk': {
                                'statistic': float(shapiro_stat) if shapiro_stat else None,
                                'p_value': float(shapiro_p) if shapiro_p else None,
                                'is_normal': bool(shapiro_p > self.significance_level) if shapiro_p else None
                            },
                            'kolmogorov_smirnov': {
                                'statistic': float(ks_stat),
                                'p_value': float(ks_p),
                                'is_normal': bool(ks_p > self.significance_level)
                            },
                            'anderson_darling': {
                                'statistic': float(ad_result.statistic),
                                'critical_values': ad_result.critical_values.tolist(),
                                'significance_levels': ad_result.significance_level.tolist()
                            }
                        }
                        
                    except Exception as e:
                        results[prop] = {'error': str(e)}
        
        return results
    
    def generate_statistical_report(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive statistical report.
        
        Args:
            data (List[Dict[str, Any]]): List of molecular property dictionaries
            
        Returns:
            Dict[str, Any]: Comprehensive statistical report
            
        Examples:
            >>> analyzer = MolecularStatisticalAnalyzer()
            >>> data = [{"molecular_weight": 180.2, "logP": 2.1}]
            >>> report = analyzer.generate_statistical_report(data)
            >>> "descriptive_statistics" in report
            True
        """
        try:
            report = {
                'dataset_info': {
                    'n_samples': len(data),
                    'n_properties': len([prop for prop in self.numeric_properties 
                                       if prop in pd.DataFrame(data).columns])
                },
                'descriptive_statistics': self.calculate_descriptive_statistics(data),
                'correlation_analysis': self.calculate_correlation_matrix(data),
                'outlier_detection': self.detect_outliers(data),
                'normality_tests': self.perform_normality_tests(data)
            }
            
            # Add summary insights
            insights = []
            
            # Check for high correlations
            corr_result = report['correlation_analysis']
            if 'correlation_matrix' in corr_result:
                corr_df = pd.DataFrame(corr_result['correlation_matrix'])
                high_corr_pairs = []
                for i in range(len(corr_df.columns)):
                    for j in range(i + 1, len(corr_df.columns)):
                        corr_val = abs(corr_df.iloc[i, j])
                        if corr_val > 0.7:
                            high_corr_pairs.append((
                                corr_df.columns[i], 
                                corr_df.columns[j], 
                                corr_val
                            ))
                
                if high_corr_pairs:
                    insights.append({
                        'type': 'high_correlation',
                        'message': f'Found {len(high_corr_pairs)} highly correlated property pairs',
                        'pairs': high_corr_pairs
                    })
            
            # Check for properties with high outlier rates
            outlier_result = report['outlier_detection']
            high_outlier_props = []
            for prop, outlier_info in outlier_result.items():
                if isinstance(outlier_info, dict) and 'outlier_percentage' in outlier_info:
                    if outlier_info['outlier_percentage'] > 10:
                        high_outlier_props.append((prop, outlier_info['outlier_percentage']))
            
            if high_outlier_props:
                insights.append({
                    'type': 'high_outliers',
                    'message': 'Properties with high outlier rates (>10%)',
                    'properties': high_outlier_props
                })
            
            report['insights'] = insights
            
            return report
            
        except Exception as e:
            return {'error': str(e)}


def create_comprehensive_analysis_dashboard(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a comprehensive analysis dashboard with all statistical plots.
    
    Args:
        data (List[Dict[str, Any]]): List of molecular property dictionaries
        
    Returns:
        Dict[str, Any]: Dashboard components and data
        
    Examples:
        >>> data = [{"molecular_weight": 180.2, "logP": 2.1}]
        >>> dashboard = create_comprehensive_analysis_dashboard(data)
        >>> "statistical_report" in dashboard
        True
    """
    analyzer = MolecularStatisticalAnalyzer()
    
    dashboard = {
        'statistical_report': analyzer.generate_statistical_report(data),
        'distribution_plots': analyzer.create_distribution_plots(data),
        'correlation_heatmap': analyzer.create_correlation_heatmap(data),
        'scatter_plot_matrix': analyzer.create_scatter_plot_matrix(data)
    }
    
    return dashboard


if __name__ == "__main__":
    # Example usage and testing
    print("Testing MolecularStatisticalAnalyzer...")
    
    # Generate sample data
    np.random.seed(42)
    sample_data = []
    for i in range(100):
        sample_data.append({
            'molecular_weight': np.random.normal(300, 50),
            'logP': np.random.normal(2.5, 1.0),
            'tpsa': np.random.normal(70, 20),
            'hbd': np.random.poisson(2),
            'hba': np.random.poisson(4),
            'num_atoms': np.random.poisson(25),
            'drug_like': np.random.choice([True, False], p=[0.7, 0.3])
        })
    
    analyzer = MolecularStatisticalAnalyzer()
    
    # Test descriptive statistics
    try:
        desc_stats = analyzer.calculate_descriptive_statistics(sample_data)
        print(f"✓ Descriptive statistics calculated for {len(desc_stats)} properties")
    except Exception as e:
        print(f"✗ Descriptive statistics failed: {e}")
    
    # Test correlation analysis
    try:
        corr_analysis = analyzer.calculate_correlation_matrix(sample_data)
        if 'error' not in corr_analysis:
            print(f"✓ Correlation analysis successful")
        else:
            print(f"✗ Correlation analysis failed: {corr_analysis['error']}")
    except Exception as e:
        print(f"✗ Correlation analysis failed: {e}")
    
    # Test outlier detection
    try:
        outliers = analyzer.detect_outliers(sample_data)
        print(f"✓ Outlier detection completed for {len(outliers)} properties")
    except Exception as e:
        print(f"✗ Outlier detection failed: {e}")
    
    # Test comprehensive report
    try:
        report = analyzer.generate_statistical_report(sample_data)
        if 'error' not in report:
            print(f"✓ Statistical report generated successfully")
        else:
            print(f"✗ Statistical report failed: {report['error']}")
    except Exception as e:
        print(f"✗ Statistical report failed: {e}")
    
    print("MolecularStatisticalAnalyzer testing complete!")