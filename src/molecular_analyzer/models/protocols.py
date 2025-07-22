"""
Protocol definitions for molecular analyzer type checking.

Provides runtime-checkable protocols for defining interfaces without
requiring inheritance, supporting duck typing and flexible composition.
"""

from typing import Protocol, runtime_checkable, Any, Dict, List, Optional, Union
from .models import MoleculeData, PropertyData, AnalysisResult


@runtime_checkable
class MolecularCalculatorProtocol(Protocol):
    """Protocol for molecular property calculators."""
    
    def calculate(self, molecule: Union[str, MoleculeData]) -> PropertyData:
        """Calculate molecular properties."""
        ...
    
    def get_supported_properties(self) -> List[str]:
        """Get list of supported property names."""
        ...
    
    def validate_molecule(self, molecule: Union[str, MoleculeData]) -> bool:
        """Validate if molecule can be processed."""
        ...


@runtime_checkable
class VisualizationRendererProtocol(Protocol):
    """Protocol for visualization renderers."""
    
    def render(self, data: Any, **kwargs) -> Any:
        """Render data to visual output."""
        ...
    
    def set_style(self, style: Dict[str, Any]) -> None:
        """Set rendering style options."""
        ...
    
    def get_supported_formats(self) -> List[str]:
        """Get supported output formats."""
        ...


@runtime_checkable
class DataParserProtocol(Protocol):
    """Protocol for molecular data parsers."""
    
    def parse(self, content: str, format_hint: Optional[str] = None) -> List[MoleculeData]:
        """Parse molecular data from content."""
        ...
    
    def validate_format(self, content: str) -> bool:
        """Validate if content matches expected format."""
        ...
    
    def get_format_info(self) -> Dict[str, Any]:
        """Get information about supported format."""
        ...


@runtime_checkable
class DataExporterProtocol(Protocol):
    """Protocol for data export functionality."""
    
    def export(self, data: Any, file_path: str, format: str = "auto") -> bool:
        """Export data to file."""
        ...
    
    def export_string(self, data: Any, format: str) -> str:
        """Export data to string."""
        ...
    
    def get_supported_formats(self) -> List[str]:
        """Get supported export formats."""
        ...


@runtime_checkable
class AnalysisWorkflowProtocol(Protocol):
    """Protocol for analysis workflow orchestration."""
    
    def execute(self, molecules: List[Union[str, MoleculeData]], **options) -> List[AnalysisResult]:
        """Execute analysis workflow on molecules."""
        ...
    
    def configure(self, **config) -> None:
        """Configure workflow parameters."""
        ...
    
    def get_progress(self) -> Dict[str, Any]:
        """Get workflow execution progress."""
        ...


@runtime_checkable
class CacheProviderProtocol(Protocol):
    """Protocol for caching implementations."""
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value."""
        ...
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cached value with optional TTL."""
        ...
    
    def delete(self, key: str) -> bool:
        """Delete cached value."""
        ...
    
    def clear(self) -> None:
        """Clear all cached values."""
        ...


@runtime_checkable
class ConfigurationProtocol(Protocol):
    """Protocol for configuration management."""
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        ...
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        ...
    
    def load_from_file(self, file_path: str) -> None:
        """Load configuration from file."""
        ...
    
    def save_to_file(self, file_path: str) -> None:
        """Save configuration to file."""
        ...


@runtime_checkable
class ValidationProtocol(Protocol):
    """Protocol for data validation."""
    
    def validate(self, data: Any) -> bool:
        """Validate data."""
        ...
    
    def get_errors(self) -> List[str]:
        """Get validation errors."""
        ...
    
    def get_warnings(self) -> List[str]:
        """Get validation warnings."""
        ...


@runtime_checkable
class LoggingProtocol(Protocol):
    """Protocol for logging functionality."""
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        ...
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        ...
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        ...
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        ...


# Type aliases for common protocol combinations
AnyCalculator = MolecularCalculatorProtocol
AnyRenderer = VisualizationRendererProtocol  
AnyParser = DataParserProtocol
AnyExporter = DataExporterProtocol
AnyWorkflow = AnalysisWorkflowProtocol

# Protocol union types for flexibility
CalculatorOrRenderer = Union[MolecularCalculatorProtocol, VisualizationRendererProtocol]
ParserOrExporter = Union[DataParserProtocol, DataExporterProtocol]
DataHandler = Union[DataParserProtocol, DataExporterProtocol, CacheProviderProtocol]