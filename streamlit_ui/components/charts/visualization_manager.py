"""
Visualization Manager Component

Orchestrates different chart components and provides chart type selection logic.
Maintains module independence by using adapter pattern for external dependencies.
"""

import streamlit as st
import pandas as pd
from typing import Any, Dict, List, Optional, Union, Tuple
from enum import Enum

from ..base import BaseComponent

# Import chart components
from .bar_chart import BarChartComponent
from .scatter_plot import ScatterPlotComponent
from .line_plot import LinePlotComponent
from .histogram import HistogramComponent
from .correlation_matrix import CorrelationMatrixComponent
from .distribution_plot import DistributionPlotComponent
from .molecule_3d import Molecule3DComponent
from .molecule_3d_controls import Molecule3DControlsComponent


class ChartType(Enum):
    """Available chart types for visualization."""
    BAR_CHART = "bar_chart"
    SCATTER_PLOT = "scatter_plot"
    LINE_PLOT = "line_plot"
    HISTOGRAM = "histogram"
    CORRELATION_MATRIX = "correlation_matrix"
    DISTRIBUTION_PLOT = "distribution_plot"
    MOLECULE_3D = "molecule_3d"


class DataType(Enum):
    """Data types for chart recommendations."""
    NUMERICAL = "numerical"
    CATEGORICAL = "categorical"
    MOLECULAR = "molecular"
    TIME_SERIES = "time_series"
    CORRELATION = "correlation"


class VisualizationManagerComponent(BaseComponent):
    """
    Manages and orchestrates different chart components.
    
    Features:
    - Automatic chart type recommendation based on data
    - Chart component orchestration
    - Unified interface for all chart types
    - Data validation and preprocessing
    - Chart configuration management
    - Export and sharing capabilities
    """
    
    def __init__(self, name: str = "Visualization Manager", key_prefix: str = None):
        """
        Initialize the visualization manager.
        
        Args:
            name: Component display name
            key_prefix: Unique key prefix for Streamlit widgets
        """
        super().__init__(name, key_prefix)
        
        # Initialize chart components
        self.chart_components = {
            ChartType.BAR_CHART: BarChartComponent("Bar Chart", f"{self.key_prefix}_bar"),
            ChartType.SCATTER_PLOT: ScatterPlotComponent("Scatter Plot", f"{self.key_prefix}_scatter"),
            ChartType.LINE_PLOT: LinePlotComponent("Line Plot", f"{self.key_prefix}_line"),
            ChartType.HISTOGRAM: HistogramComponent("Histogram", f"{self.key_prefix}_hist"),
            ChartType.CORRELATION_MATRIX: CorrelationMatrixComponent("Correlation Matrix", f"{self.key_prefix}_corr"),
            ChartType.DISTRIBUTION_PLOT: DistributionPlotComponent("Distribution Plot", f"{self.key_prefix}_dist"),
            ChartType.MOLECULE_3D: Molecule3DComponent("3D Molecule", f"{self.key_prefix}_mol3d")
        }
        
        # Chart recommendations based on data characteristics
        self.chart_recommendations = {
            DataType.NUMERICAL: [ChartType.HISTOGRAM, ChartType.DISTRIBUTION_PLOT, ChartType.SCATTER_PLOT],
            DataType.CATEGORICAL: [ChartType.BAR_CHART, ChartType.HISTOGRAM],
            DataType.MOLECULAR: [ChartType.MOLECULE_3D, ChartType.BAR_CHART, ChartType.SCATTER_PLOT],
            DataType.TIME_SERIES: [ChartType.LINE_PLOT, ChartType.SCATTER_PLOT],
            DataType.CORRELATION: [ChartType.CORRELATION_MATRIX, ChartType.SCATTER_PLOT]
        }
        
        self.current_chart_type = None
        self.current_data = None
        self.current_config = {}
    
    def analyze_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze data to determine its characteristics and recommend chart types.
        
        Args:
            data: DataFrame to analyze
            
        Returns:
            Dictionary with data analysis results and recommendations
        """
        try:
            if data is None or data.empty:
                return {"error": "No data provided"}
            
            analysis = {
                "num_rows": len(data),
                "num_columns": len(data.columns),
                "columns": list(data.columns),
                "dtypes": data.dtypes.to_dict(),
                "numerical_columns": [],
                "categorical_columns": [],
                "has_missing": data.isnull().any().any(),
                "missing_counts": data.isnull().sum().to_dict()
            }
            
            # Classify columns
            for col in data.columns:
                if pd.api.types.is_numeric_dtype(data[col]):
                    analysis["numerical_columns"].append(col)
                else:
                    analysis["categorical_columns"].append(col)
            
            # Determine data type and recommendations
            analysis["data_type"] = self._determine_data_type(analysis)
            analysis["recommended_charts"] = self.chart_recommendations.get(
                analysis["data_type"], [ChartType.BAR_CHART]
            )
            
            return analysis
            
        except Exception as e:
            self.add_error(f"Error analyzing data: {str(e)}", e)
            return {"error": str(e)}
    
    def _determine_data_type(self, analysis: Dict[str, Any]) -> DataType:
        """
        Determine the primary data type based on analysis.
        
        Args:
            analysis: Data analysis results
            
        Returns:
            Primary data type
        """
        num_numerical = len(analysis["numerical_columns"])
        num_categorical = len(analysis["categorical_columns"])
        
        # Check for molecular data indicators
        molecular_indicators = ["smiles", "mol", "molecule", "compound", "structure"]
        has_molecular = any(
            indicator in col.lower() 
            for col in analysis["columns"] 
            for indicator in molecular_indicators
        )
        
        if has_molecular:
            return DataType.MOLECULAR
        
        # Check for correlation data (multiple numerical columns)
        if num_numerical >= 3:
            return DataType.CORRELATION
        
        # Check for time series indicators
        time_indicators = ["time", "date", "timestamp", "year", "month", "day"]
        has_time = any(
            indicator in col.lower() 
            for col in analysis["columns"] 
            for indicator in time_indicators
        )
        
        if has_time and num_numerical > 0:
            return DataType.TIME_SERIES
        
        # Default classification
        if num_numerical > num_categorical:
            return DataType.NUMERICAL
        else:
            return DataType.CATEGORICAL
    
    def recommend_chart_type(self, data: pd.DataFrame, target_column: str = None) -> List[ChartType]:
        """
        Recommend appropriate chart types for given data.
        
        Args:
            data: DataFrame to visualize
            target_column: Specific column to focus on (optional)
            
        Returns:
            List of recommended chart types in order of preference
        """
        try:
            analysis = self.analyze_data(data)
            
            if "error" in analysis:
                return [ChartType.BAR_CHART]  # Default fallback
            
            recommendations = analysis.get("recommended_charts", [ChartType.BAR_CHART])
            
            # Refine recommendations based on target column
            if target_column and target_column in data.columns:
                if pd.api.types.is_numeric_dtype(data[target_column]):
                    # Numeric target - prefer histogram and distribution plots
                    numeric_charts = [ChartType.HISTOGRAM, ChartType.DISTRIBUTION_PLOT, ChartType.SCATTER_PLOT]
                    recommendations = [c for c in numeric_charts if c in recommendations] + recommendations
                else:
                    # Categorical target - prefer bar charts
                    categorical_charts = [ChartType.BAR_CHART]
                    recommendations = categorical_charts + [c for c in recommendations if c not in categorical_charts]
            
            # Remove duplicates while preserving order
            seen = set()
            unique_recommendations = []
            for chart in recommendations:
                if chart not in seen:
                    seen.add(chart)
                    unique_recommendations.append(chart)
            
            return unique_recommendations
            
        except Exception as e:
            self.add_error(f"Error recommending chart type: {str(e)}", e)
            return [ChartType.BAR_CHART]
    
    def create_chart(self, 
                    chart_type: ChartType, 
                    data: pd.DataFrame, 
                    config: Dict[str, Any] = None) -> Any:
        """
        Create a chart of the specified type with given data and configuration.
        
        Args:
            chart_type: Type of chart to create
            data: Data to visualize
            config: Chart configuration options
            
        Returns:
            Chart component result
        """
        try:
            if chart_type not in self.chart_components:
                self.add_error(f"Unsupported chart type: {chart_type}")
                return None
            
            component = self.chart_components[chart_type]
            
            # Configure the component if config provided
            if config and hasattr(component, 'configure_chart'):
                component.configure_chart(**config)
            
            # Store current state
            self.current_chart_type = chart_type
            self.current_data = data
            self.current_config = config or {}
            
            # Create the chart
            result = component.render(data)
            
            # Handle any component errors
            if component.has_errors():
                for error in component._errors:
                    self.add_error(f"Chart error: {error}")
            
            if component.has_warnings():
                for warning in component._warnings:
                    self.add_warning(f"Chart warning: {warning}")
            
            return result
            
        except Exception as e:
            self.add_error(f"Error creating chart: {str(e)}", e)
            return None
    
    def render_chart_selector(self, data: pd.DataFrame, target_column: str = None) -> ChartType:
        """
        Render chart type selection interface.
        
        Args:
            data: Data to visualize
            target_column: Target column for analysis
            
        Returns:
            Selected chart type
        """
        try:
            # Get recommendations
            recommendations = self.recommend_chart_type(data, target_column)
            
            # Create options for selectbox
            chart_options = []
            chart_labels = []
            
            for chart_type in ChartType:
                label = chart_type.value.replace('_', ' ').title()
                if chart_type in recommendations:
                    label += " ⭐ (Recommended)"
                chart_options.append(chart_type)
                chart_labels.append(label)
            
            # Create selectbox
            selected_index = st.selectbox(
                "Select Chart Type",
                range(len(chart_options)),
                format_func=lambda i: chart_labels[i],
                key=self.get_key("chart_type_selector")
            )
            
            selected_chart_type = chart_options[selected_index]
            
            # Show data analysis info
            if st.checkbox("Show Data Analysis", key=self.get_key("show_analysis")):
                analysis = self.analyze_data(data)
                st.json(analysis)
            
            return selected_chart_type
            
        except Exception as e:
            self.add_error(f"Error rendering chart selector: {str(e)}", e)
            return ChartType.BAR_CHART
    
    def render_chart_configuration(self, chart_type: ChartType) -> Dict[str, Any]:
        """
        Render configuration interface for the selected chart type.
        
        Args:
            chart_type: Type of chart to configure
            
        Returns:
            Configuration dictionary
        """
        try:
            config = {}
            
            st.subheader("Chart Configuration")
            
            # Common configuration options
            with st.expander("General Settings"):
                config['title'] = st.text_input(
                    "Chart Title", 
                    value="", 
                    key=self.get_key("title")
                )
                config['width'] = st.slider(
                    "Chart Width", 
                    400, 1200, 800, 
                    key=self.get_key("width")
                )
                config['height'] = st.slider(
                    "Chart Height", 
                    300, 800, 500, 
                    key=self.get_key("height")
                )
            
            # Chart-specific configuration
            if chart_type == ChartType.BAR_CHART:
                with st.expander("Bar Chart Settings"):
                    config['orientation'] = st.selectbox(
                        "Orientation", 
                        ['vertical', 'horizontal'],
                        key=self.get_key("bar_orientation")
                    )
                    config['bar_mode'] = st.selectbox(
                        "Bar Mode", 
                        ['group', 'stack', 'overlay'],
                        key=self.get_key("bar_mode")
                    )
            
            elif chart_type == ChartType.SCATTER_PLOT:
                with st.expander("Scatter Plot Settings"):
                    config['size_column'] = st.text_input(
                        "Size Column (optional)", 
                        key=self.get_key("scatter_size")
                    )
                    config['color_column'] = st.text_input(
                        "Color Column (optional)", 
                        key=self.get_key("scatter_color")
                    )
            
            elif chart_type == ChartType.HISTOGRAM:
                with st.expander("Histogram Settings"):
                    config['bins'] = st.slider(
                        "Number of Bins", 
                        5, 100, 20, 
                        key=self.get_key("hist_bins")
                    )
                    config['density'] = st.checkbox(
                        "Show Density", 
                        key=self.get_key("hist_density")
                    )
            
            return config
            
        except Exception as e:
            self.add_error(f"Error rendering chart configuration: {str(e)}", e)
            return {}
    
    def render(self, data: pd.DataFrame = None, auto_recommend: bool = True) -> Any:
        """
        Render the complete visualization manager interface.
        
        Args:
            data: Data to visualize
            auto_recommend: Whether to automatically recommend chart types
            
        Returns:
            Visualization result
        """
        try:
            if data is None or data.empty:
                st.warning("No data provided for visualization")
                return None
            
            # Display current data info
            with st.expander("Data Overview"):
                st.write(f"Data shape: {data.shape}")
                st.write("Column types:")
                st.write(data.dtypes)
                
                if st.checkbox("Show data sample", key=self.get_key("show_sample")):
                    st.dataframe(data.head())
            
            # Chart type selection
            selected_chart_type = self.render_chart_selector(data)
            
            # Chart configuration
            chart_config = self.render_chart_configuration(selected_chart_type)
            
            # Create and display chart
            if st.button("Generate Chart", key=self.get_key("generate")):
                with st.spinner("Creating visualization..."):
                    chart_result = self.create_chart(selected_chart_type, data, chart_config)
                    
                    if chart_result is not None:
                        st.success("Chart created successfully!")
                        return chart_result
                    else:
                        st.error("Failed to create chart. Check the error messages above.")
            
            # Display any messages
            self.display_messages()
            
            return None
            
        except Exception as e:
            self.add_error(f"Error rendering visualization manager: {str(e)}", e)
            self.display_messages()
            return None
    
    def export_chart_config(self) -> Dict[str, Any]:
        """
        Export current chart configuration for saving/sharing.
        
        Returns:
            Configuration dictionary
        """
        return {
            "chart_type": self.current_chart_type.value if self.current_chart_type else None,
            "config": self.current_config,
            "component_name": self.name,
            "timestamp": st.session_state.get("timestamp", "unknown")
        }
    
    def load_chart_config(self, config: Dict[str, Any]) -> bool:
        """
        Load chart configuration from saved state.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            if "chart_type" in config and config["chart_type"]:
                self.current_chart_type = ChartType(config["chart_type"])
            
            if "config" in config:
                self.current_config = config["config"]
            
            return True
            
        except Exception as e:
            self.add_error(f"Error loading chart config: {str(e)}", e)
            return False