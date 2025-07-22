"""
Models module for molecular analyzer OOP architecture.

This module provides the fundamental data models, base classes, and type system
for the molecular analyzer package.
"""

from .models import MoleculeData, PropertyData, AnalysisResult
from .exceptions import (
    MolecularAnalyzerException, 
    ValidationError, 
    AnalysisError, 
    ComputationError,
    ConfigurationError,
    DataExportError
)
from .base import (
    BaseCalculator,
    BaseRenderer,
    BaseParser,
    BaseFactory,
    CalculationConfig,
    CalculatorProtocol,
    RendererProtocol,
    ParserProtocol
)
from .protocols import (
    MolecularCalculatorProtocol,
    VisualizationRendererProtocol,
    DataParserProtocol,
    DataExporterProtocol,
    AnalysisWorkflowProtocol
)
from .config import (
    AnalysisConfig,
    ConfigurationManager,
    get_development_config,
    get_production_config,
    get_performance_config,
    get_research_config
)

__all__ = [
    # Data models
    'MoleculeData',
    'PropertyData', 
    'AnalysisResult',
    
    # Exceptions
    'MolecularAnalyzerException',
    'ValidationError',
    'AnalysisError',
    'ComputationError',
    'ConfigurationError',
    'DataExportError',
    
    # Base classes
    'BaseCalculator',
    'BaseRenderer',
    'BaseParser',
    'BaseFactory',
    'CalculationConfig',
    
    # Protocols (for type checking)
    'CalculatorProtocol',
    'RendererProtocol', 
    'ParserProtocol',
    'MolecularCalculatorProtocol',
    'VisualizationRendererProtocol',
    'DataParserProtocol',
    'DataExporterProtocol',
    'AnalysisWorkflowProtocol',
    
    # Configuration system
    'AnalysisConfig',
    'ConfigurationManager',
    'get_development_config',
    'get_production_config',
    'get_performance_config',
    'get_research_config'
]