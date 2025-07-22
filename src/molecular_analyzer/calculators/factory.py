"""
Calculator Factory for dynamic calculator creation and management.

Provides a factory pattern implementation for creating calculator instances
and managing calculator registry with plugin support.
"""

from typing import Dict, Type, Optional, List, Any, Union
from abc import ABC
import inspect

from ..models.base import BaseCalculator, CalculationConfig
from ..models.exceptions import ValidationError, AnalysisError
from ..models.models import MoleculeData


class CalculatorFactory:
    """
    Factory class for creating and managing molecular calculator instances.
    
    Provides dynamic calculator creation, registry management, and plugin support
    for extending the calculator ecosystem.
    
    Example:
        >>> factory = CalculatorFactory()
        >>> calc = factory.create_calculator('basic')
        >>> result = calc.calculate('CCO')
        
        >>> # Register custom calculator
        >>> factory.register_calculator('custom', MyCustomCalculator)
        >>> custom_calc = factory.create_calculator('custom')
    """
    
    _instance: Optional['CalculatorFactory'] = None
    _registry: Dict[str, Type[BaseCalculator]] = {}
    _aliases: Dict[str, str] = {}
    
    def __new__(cls) -> 'CalculatorFactory':
        """Singleton pattern to ensure single registry across application."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_default_calculators()
        return cls._instance
    
    def _initialize_default_calculators(self) -> None:
        """Initialize the registry with default calculator classes."""
        try:
            # Import and register basic calculators
            from .basic import (
                BasicPropertiesCalculator,
                DrugLikePropertiesCalculator, 
                ComprehensivePropertiesCalculator
            )
            self._registry.update({
                'basic': BasicPropertiesCalculator,
                'drug_like': DrugLikePropertiesCalculator,
                'comprehensive': ComprehensivePropertiesCalculator
            })
            
            # Add aliases for convenience
            self._aliases.update({
                'simple': 'basic',
                'standard': 'basic',
                'drug': 'drug_like',
                'full': 'comprehensive',
                'complete': 'comprehensive'
            })
            
        except ImportError:
            pass
        
        try:
            # Import and register advanced calculators
            from .advanced import AdvancedPropertiesCalculator, LipophilicityCalculator
            self._registry.update({
                'advanced': AdvancedPropertiesCalculator,
                'lipophilicity': LipophilicityCalculator
            })
            
            # Add aliases
            self._aliases.update({
                'admet': 'advanced',
                'lipo': 'lipophilicity'
            })
            
        except ImportError:
            pass
        
        try:
            # Import and register conformational calculator
            from .conformational import ConformationalCalculator
            self._registry['conformational'] = ConformationalCalculator
            
            # Add aliases
            self._aliases.update({
                'conformation': 'conformational',
                '3d': 'conformational',
                'structure': 'conformational'
            })
            
        except ImportError:
            pass
        
        try:
            # Import and register comparison calculator
            from .comparison import ComparisonCalculator
            self._registry['comparison'] = ComparisonCalculator
            
            # Add aliases
            self._aliases.update({
                'similarity': 'comparison',
                'compare': 'comparison'
            })
            
        except ImportError:
            pass
    
    def register_calculator(
        self, 
        name: str, 
        calculator_class: Type[BaseCalculator],
        aliases: Optional[List[str]] = None
    ) -> None:
        """
        Register a calculator class in the factory.
        
        Args:
            name: Unique name for the calculator
            calculator_class: Calculator class that inherits from BaseCalculator
            aliases: Optional list of alias names for the calculator
            
        Raises:
            ValidationError: If name already exists or calculator is invalid
        """
        if not inspect.isclass(calculator_class):
            raise ValidationError(f"Calculator must be a class, got {type(calculator_class)}")
        
        if not issubclass(calculator_class, BaseCalculator):
            raise ValidationError(
                f"Calculator {calculator_class.__name__} must inherit from BaseCalculator"
            )
        
        if name in self._registry:
            raise ValidationError(f"Calculator '{name}' is already registered")
        
        # Register the calculator
        self._registry[name] = calculator_class
        
        # Register aliases if provided
        if aliases:
            for alias in aliases:
                if alias in self._aliases:
                    raise ValidationError(f"Alias '{alias}' is already taken")
                self._aliases[alias] = name
    
    def unregister_calculator(self, name: str) -> None:
        """
        Unregister a calculator from the factory.
        
        Args:
            name: Name of the calculator to unregister
            
        Raises:
            ValidationError: If calculator doesn't exist
        """
        if name not in self._registry:
            raise ValidationError(f"Calculator '{name}' is not registered")
        
        # Remove calculator
        del self._registry[name]
        
        # Remove any aliases pointing to this calculator
        aliases_to_remove = [
            alias for alias, target in self._aliases.items() 
            if target == name
        ]
        for alias in aliases_to_remove:
            del self._aliases[alias]
    
    def create_calculator(
        self, 
        calculator_type: str,
        config: Optional[CalculationConfig] = None,
        **kwargs
    ) -> BaseCalculator:
        """
        Create a calculator instance of the specified type.
        
        Args:
            calculator_type: Type of calculator to create
            config: Optional configuration for the calculator
            **kwargs: Additional arguments passed to calculator constructor
            
        Returns:
            Calculator instance
            
        Raises:
            ValidationError: If calculator type is not registered
            AnalysisError: If calculator creation fails
        """
        # Resolve alias if needed
        resolved_type = self._aliases.get(calculator_type, calculator_type)
        
        if resolved_type not in self._registry:
            available_types = list(self._registry.keys()) + list(self._aliases.keys())
            raise ValidationError(
                f"Calculator type '{calculator_type}' not found. "
                f"Available types: {', '.join(sorted(available_types))}"
            )
        
        calculator_class = self._registry[resolved_type]
        
        try:
            # Create calculator instance
            if config is not None:
                return calculator_class(config=config, **kwargs)
            else:
                return calculator_class(**kwargs)
                
        except Exception as e:
            raise AnalysisError(
                f"Failed to create calculator '{calculator_type}': {str(e)}"
            ) from e
    
    def get_available_calculators(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all available calculators.
        
        Returns:
            Dictionary with calculator information including supported properties
        """
        info = {}
        
        for name, calculator_class in self._registry.items():
            try:
                # Create temporary instance to get properties
                temp_calc = calculator_class()
                info[name] = {
                    'class': calculator_class.__name__,
                    'module': calculator_class.__module__,
                    'supported_properties': temp_calc.supported_properties,
                    'calculator_name': temp_calc.calculator_name,
                    'aliases': [
                        alias for alias, target in self._aliases.items() 
                        if target == name
                    ]
                }
            except Exception:
                # If can't instantiate, provide basic info
                info[name] = {
                    'class': calculator_class.__name__,
                    'module': calculator_class.__module__,
                    'supported_properties': 'unknown',
                    'calculator_name': 'unknown',
                    'aliases': [
                        alias for alias, target in self._aliases.items() 
                        if target == name
                    ]
                }
        
        return info
    
    def get_calculator_for_property(self, property_name: str) -> List[str]:
        """
        Find calculators that support a specific property.
        
        Args:
            property_name: Name of the property to search for
            
        Returns:
            List of calculator names that support the property
        """
        supporting_calculators = []
        
        for name, calculator_class in self._registry.items():
            try:
                temp_calc = calculator_class()
                if property_name.lower() in [prop.lower() for prop in temp_calc.supported_properties]:
                    supporting_calculators.append(name)
            except Exception:
                continue
        
        return supporting_calculators
    
    def create_batch_calculators(
        self, 
        calculator_types: List[str],
        config: Optional[CalculationConfig] = None
    ) -> Dict[str, BaseCalculator]:
        """
        Create multiple calculator instances at once.
        
        Args:
            calculator_types: List of calculator types to create
            config: Optional shared configuration for all calculators
            
        Returns:
            Dictionary mapping calculator types to instances
            
        Raises:
            ValidationError: If any calculator type is invalid
        """
        calculators = {}
        
        for calc_type in calculator_types:
            calculators[calc_type] = self.create_calculator(calc_type, config)
        
        return calculators
    
    def validate_calculator_type(self, calculator_type: str) -> bool:
        """
        Check if a calculator type is valid/registered.
        
        Args:
            calculator_type: Type to validate
            
        Returns:
            True if valid, False otherwise
        """
        resolved_type = self._aliases.get(calculator_type, calculator_type)
        return resolved_type in self._registry
    
    def get_calculator_class(self, calculator_type: str) -> Type[BaseCalculator]:
        """
        Get the calculator class for a given type.
        
        Args:
            calculator_type: Type of calculator
            
        Returns:
            Calculator class
            
        Raises:
            ValidationError: If calculator type is not registered
        """
        resolved_type = self._aliases.get(calculator_type, calculator_type)
        
        if resolved_type not in self._registry:
            raise ValidationError(f"Calculator type '{calculator_type}' not found")
        
        return self._registry[resolved_type]
    
    def reset_registry(self) -> None:
        """Reset the registry and reload default calculators."""
        self._registry.clear()
        self._aliases.clear()
        self._initialize_default_calculators()


# Convenience functions for easy access
def create_calculator(
    calculator_type: str, 
    config: Optional[CalculationConfig] = None,
    **kwargs
) -> BaseCalculator:
    """
    Convenience function to create a calculator using the default factory.
    
    Args:
        calculator_type: Type of calculator to create
        config: Optional configuration
        **kwargs: Additional arguments
        
    Returns:
        Calculator instance
    """
    factory = CalculatorFactory()
    return factory.create_calculator(calculator_type, config, **kwargs)


def get_available_calculators() -> Dict[str, Dict[str, Any]]:
    """
    Convenience function to get available calculators.
    
    Returns:
        Dictionary with calculator information
    """
    factory = CalculatorFactory()
    return factory.get_available_calculators()


def register_calculator(
    name: str, 
    calculator_class: Type[BaseCalculator],
    aliases: Optional[List[str]] = None
) -> None:
    """
    Convenience function to register a calculator.
    
    Args:
        name: Calculator name
        calculator_class: Calculator class
        aliases: Optional aliases
    """
    factory = CalculatorFactory()
    factory.register_calculator(name, calculator_class, aliases)