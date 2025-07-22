"""
Base classes and abstract interfaces for molecular analyzer OOP architecture.

Provides abstract base classes that define common interfaces and functionality
for calculators, renderers, parsers, and other components.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Union, TypeVar, Generic
from dataclasses import dataclass
import time
from datetime import datetime

from .models import MoleculeData, PropertyData, AnalysisResult
from .exceptions import AnalysisError, ValidationError, ComputationError


T = TypeVar('T')
ResultType = TypeVar('ResultType')


@dataclass
class CalculationConfig:
    """Configuration for calculation operations."""
    timeout: Optional[float] = None
    precision: str = "standard"  # standard, high, maximum
    use_cache: bool = True
    validation_level: str = "normal"  # minimal, normal, strict
    include_quantum_descriptors: bool = False  # Expensive calculations
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseCalculator(ABC, Generic[ResultType]):
    """
    Abstract base class for all molecular calculators.
    
    Provides common functionality including error handling, caching, validation,
    and result formatting. All calculator classes should inherit from this.
    """
    
    def __init__(self, config: Optional[CalculationConfig] = None):
        self.config = config or CalculationConfig()
        self._cache: Dict[str, Any] = {}
        self._last_calculation_time: Optional[float] = None
        
    @property
    @abstractmethod
    def calculator_name(self) -> str:
        """Return the name of this calculator."""
        pass
    
    @property
    @abstractmethod
    def supported_properties(self) -> List[str]:
        """Return list of properties this calculator can compute."""
        pass
    
    @abstractmethod
    def _calculate_properties(self, molecule: MoleculeData) -> ResultType:
        """
        Core calculation method to be implemented by subclasses.
        
        Args:
            molecule: Validated molecule data
            
        Returns:
            Calculation results in the format specific to the calculator
            
        Raises:
            AnalysisError: If calculation fails
            ComputationError: If computational issues occur
        """
        pass
    
    def calculate(self, molecule: Union[str, MoleculeData]) -> ResultType:
        """
        Calculate properties for a molecule with full error handling and caching.
        
        Args:
            molecule: SMILES string or MoleculeData object
            
        Returns:
            Calculation results
            
        Raises:
            ValidationError: If molecule validation fails
            AnalysisError: If calculation fails
        """
        start_time = time.time()
        
        try:
            # Convert to MoleculeData if needed
            mol_data = self._prepare_molecule(molecule)
            
            # Check cache if enabled
            if self.config.use_cache:
                cache_key = self._get_cache_key(mol_data)
                if cache_key in self._cache:
                    return self._cache[cache_key]
            
            # Perform calculation
            result = self._calculate_properties(mol_data)
            
            # Cache result if enabled
            if self.config.use_cache and cache_key:
                self._cache[cache_key] = result
            
            self._last_calculation_time = time.time() - start_time
            return result
            
        except Exception as e:
            self._last_calculation_time = time.time() - start_time
            if isinstance(e, (ValidationError, AnalysisError, ComputationError)):
                raise
            else:
                raise AnalysisError(
                    f"Calculation failed in {self.calculator_name}",
                    operation=self.calculator_name,
                    smiles=str(molecule) if isinstance(molecule, str) else molecule.smiles
                ) from e
    
    def _prepare_molecule(self, molecule: Union[str, MoleculeData]) -> MoleculeData:
        """Convert input to validated MoleculeData object."""
        if isinstance(molecule, str):
            mol_data = MoleculeData(smiles=molecule)
        elif isinstance(molecule, MoleculeData):
            mol_data = molecule
            if not mol_data.validated:
                mol_data.validate()
        else:
            raise ValidationError(f"Invalid molecule type: {type(molecule)}")
        
        return mol_data
    
    def _get_cache_key(self, molecule: MoleculeData) -> str:
        """Generate cache key for a molecule."""
        return f"{self.calculator_name}:{molecule.smiles}:{hash(str(self.config))}"
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return calculator capabilities and metadata."""
        return {
            'name': self.calculator_name,
            'supported_properties': self.supported_properties,
            'cache_enabled': self.config.use_cache,
            'cache_size': len(self._cache),
            'last_calculation_time': self._last_calculation_time,
            'config': self.config
        }
    
    def clear_cache(self) -> None:
        """Clear the calculation cache."""
        self._cache.clear()


class BaseRenderer(ABC, Generic[T]):
    """
    Abstract base class for all visualization renderers.
    
    Provides common functionality for rendering molecular data, analysis results,
    and other visualization needs with different backends.
    """
    
    def __init__(self, backend: str = "default"):
        self.backend = backend
        self._render_config: Dict[str, Any] = {}
    
    @property
    @abstractmethod
    def renderer_name(self) -> str:
        """Return the name of this renderer."""
        pass
    
    @property
    @abstractmethod
    def supported_backends(self) -> List[str]:
        """Return list of supported rendering backends."""
        pass
    
    @abstractmethod
    def _render_content(self, data: T, **kwargs) -> Any:
        """
        Core rendering method to be implemented by subclasses.
        
        Args:
            data: Data to render
            **kwargs: Rendering options
            
        Returns:
            Rendered output (format depends on backend)
        """
        pass
    
    def render(self, data: T, **kwargs) -> Any:
        """
        Render data with error handling and backend validation.
        
        Args:
            data: Data to render
            **kwargs: Rendering options
            
        Returns:
            Rendered output
        """
        if self.backend not in self.supported_backends:
            raise ValidationError(
                f"Unsupported backend: {self.backend}",
                validation_rule=f"Must be one of: {self.supported_backends}"
            )
        
        return self._render_content(data, **kwargs)
    
    def set_config(self, **config) -> None:
        """Set rendering configuration options."""
        self._render_config.update(config)
    
    def get_config(self) -> Dict[str, Any]:
        """Get current rendering configuration."""
        return self._render_config.copy()


class BaseParser(ABC, Generic[T]):
    """
    Abstract base class for all molecular file parsers.
    
    Provides common functionality for parsing different molecular file formats
    with validation and error handling.
    """
    
    @property
    @abstractmethod
    def parser_name(self) -> str:
        """Return the name of this parser."""
        pass
    
    @property
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """Return list of supported file formats."""
        pass
    
    @abstractmethod
    def _parse_content(self, content: str, format_hint: Optional[str] = None) -> T:
        """
        Core parsing method to be implemented by subclasses.
        
        Args:
            content: File content to parse
            format_hint: Optional format hint
            
        Returns:
            Parsed data
        """
        pass
    
    def parse_file(self, file_path: str, format_hint: Optional[str] = None) -> T:
        """
        Parse a molecular file with error handling.
        
        Args:
            file_path: Path to the file
            format_hint: Optional format hint
            
        Returns:
            Parsed data
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self._parse_content(content, format_hint)
        except FileNotFoundError:
            raise ValidationError(f"File not found: {file_path}")
        except Exception as e:
            raise ValidationError(f"Failed to parse file {file_path}: {str(e)}")
    
    def parse_string(self, content: str, format_hint: Optional[str] = None) -> T:
        """
        Parse molecular data from string content.
        
        Args:
            content: String content to parse
            format_hint: Optional format hint
            
        Returns:
            Parsed data
        """
        return self._parse_content(content, format_hint)


# Protocol definitions for type checking and interface contracts

class CalculatorProtocol(Protocol):
    """Protocol defining the calculator interface."""
    
    def calculate(self, molecule: Union[str, MoleculeData]) -> Any:
        """Calculate properties for a molecule."""
        ...
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get calculator capabilities."""
        ...


class RendererProtocol(Protocol):
    """Protocol defining the renderer interface."""
    
    def render(self, data: Any, **kwargs) -> Any:
        """Render data to visual output."""
        ...
    
    def set_config(self, **config) -> None:
        """Set rendering configuration."""
        ...


class ParserProtocol(Protocol):
    """Protocol defining the parser interface."""
    
    def parse_file(self, file_path: str, format_hint: Optional[str] = None) -> Any:
        """Parse a molecular file."""
        ...
    
    def parse_string(self, content: str, format_hint: Optional[str] = None) -> Any:
        """Parse molecular data from string."""
        ...


# Factory base class for creating instances

class BaseFactory(ABC):
    """
    Abstract base class for factory patterns.
    
    Provides common functionality for creating and managing instances
    of calculators, renderers, and other components.
    """
    
    def __init__(self):
        self._registry: Dict[str, type] = {}
    
    def register(self, name: str, cls: type) -> None:
        """Register a class in the factory."""
        self._registry[name] = cls
    
    def get_available(self) -> List[str]:
        """Get list of available registered types."""
        return list(self._registry.keys())
    
    def is_available(self, name: str) -> bool:
        """Check if a type is available."""
        return name in self._registry
    
    @abstractmethod
    def create(self, name: str, **kwargs) -> Any:
        """Create an instance of the specified type."""
        pass