"""
Streamlit UI Components Package

Standard component structure for molecular analyzer UI.

This package provides a clean, modular structure for UI components:
- base.py: BaseComponent class with common functionality
- charts/: Visualization components (bar, scatter, line charts)
- input/: Molecule input components (SMILES, file upload, selection)
- display/: Message display components (success, error, warning, info)

All components inherit from BaseComponent and follow consistent patterns.
"""

# Import base component
from .base import BaseComponent

# Import chart components
from .charts.bar_chart import BarChartComponent
from .charts.scatter_plot import ScatterPlotComponent
from .charts.line_plot import LinePlotComponent

# Import input components
from .input.molecule_input import MoleculeInputComponent

# Import display components
from .display.message_display import MessageDisplayComponent

__all__ = [
    'BaseComponent',
    'BarChartComponent', 
    'ScatterPlotComponent',
    'LinePlotComponent',
    'MoleculeInputComponent',
    'MessageDisplayComponent'
]

__version__ = '1.0.0'