"""
Base Component Class for Streamlit UI Components

Provides common functionality for all UI components including error handling,
validation, and state management integration.
"""

import streamlit as st
import traceback
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from datetime import datetime


class BaseComponent(ABC):
    """
    Abstract base class for all Streamlit UI components.
    
    Provides:
    - Common error handling patterns
    - State management integration
    - Validation methods
    - Consistent interface for all components
    """
    
    def __init__(self, name: str, key_prefix: str = None):
        """
        Initialize the base component.
        
        Args:
            name: Human-readable name for the component
            key_prefix: Prefix for Streamlit widget keys (defaults to component name)
        """
        self.name = name
        self.key_prefix = key_prefix or name.lower().replace(" ", "_")
        self._errors: List[str] = []
        self._warnings: List[str] = []
        
    def get_key(self, suffix: str) -> str:
        """
        Generate a unique key for Streamlit widgets.
        
        Args:
            suffix: Unique suffix for this widget
            
        Returns:
            Formatted key string
        """
        return f"{self.key_prefix}_{suffix}"
    
    def add_error(self, message: str, exception: Exception = None) -> None:
        """
        Add an error message to the component.
        
        Args:
            message: Error message to display
            exception: Optional exception object for detailed logging
        """
        self._errors.append(message)
        
        # Log detailed error for debugging
        if exception:
            error_details = f"{message}\nException: {type(exception).__name__}: {str(exception)}"
            if hasattr(st, 'logger'):
                st.logger.error(error_details)
            else:
                print(f"[ERROR] {error_details}")
    
    def add_warning(self, message: str) -> None:
        """
        Add a warning message to the component.
        
        Args:
            message: Warning message to display
        """
        self._warnings.append(message)
    
    def clear_messages(self) -> None:
        """Clear all error and warning messages."""
        self._errors.clear()
        self._warnings.clear()
    
    def has_errors(self) -> bool:
        """Check if component has any errors."""
        return len(self._errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if component has any warnings."""
        return len(self._warnings) > 0
    
    def display_messages(self) -> None:
        """Display all accumulated error and warning messages."""
        for error in self._errors:
            st.error(error)
        
        for warning in self._warnings:
            st.warning(warning)
    
    def safe_execute(self, func, *args, **kwargs) -> Any:
        """
        Safely execute a function with error handling.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Function result or None if error occurred
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = f"Error in {self.name}: {str(e)}"
            self.add_error(error_msg, e)
            return None
    
    def validate_input(self, value: Any, validation_rules: Dict[str, Any]) -> bool:
        """
        Validate input against provided rules.
        
        Args:
            value: Value to validate
            validation_rules: Dictionary containing validation parameters
                - required: bool - Whether value is required
                - type: type - Expected type
                - min_length: int - Minimum string length
                - max_length: int - Maximum string length
                - min_value: float - Minimum numeric value
                - max_value: float - Maximum numeric value
                - allowed_values: list - List of allowed values
        
        Returns:
            True if validation passes, False otherwise
        """
        try:
            # Check if required
            if validation_rules.get('required', False) and not value:
                self.add_error(f"{self.name}: This field is required")
                return False
            
            # Skip other validations if value is empty and not required
            if not value and not validation_rules.get('required', False):
                return True
            
            # Type validation
            expected_type = validation_rules.get('type')
            if expected_type and not isinstance(value, expected_type):
                self.add_error(f"{self.name}: Expected {expected_type.__name__}, got {type(value).__name__}")
                return False
            
            # String length validation
            if isinstance(value, str):
                min_len = validation_rules.get('min_length')
                max_len = validation_rules.get('max_length')
                
                if min_len is not None and len(value) < min_len:
                    self.add_error(f"{self.name}: Minimum length is {min_len} characters")
                    return False
                
                if max_len is not None and len(value) > max_len:
                    self.add_error(f"{self.name}: Maximum length is {max_len} characters")
                    return False
            
            # Numeric value validation
            if isinstance(value, (int, float)):
                min_val = validation_rules.get('min_value')
                max_val = validation_rules.get('max_value')
                
                if min_val is not None and value < min_val:
                    self.add_error(f"{self.name}: Minimum value is {min_val}")
                    return False
                
                if max_val is not None and value > max_val:
                    self.add_error(f"{self.name}: Maximum value is {max_val}")
                    return False
            
            # Allowed values validation
            allowed_values = validation_rules.get('allowed_values')
            if allowed_values and value not in allowed_values:
                self.add_error(f"{self.name}: Value must be one of {allowed_values}")
                return False
            
            return True
            
        except Exception as e:
            self.add_error(f"Validation error in {self.name}: {str(e)}", e)
            return False
    
    def get_session_state(self, key: str, default: Any = None) -> Any:
        """
        Get value from Streamlit session state.
        
        Args:
            key: Session state key
            default: Default value if key doesn't exist
            
        Returns:
            Session state value or default
        """
        return st.session_state.get(key, default)
    
    def set_session_state(self, key: str, value: Any) -> None:
        """
        Set value in Streamlit session state.
        
        Args:
            key: Session state key
            value: Value to set
        """
        st.session_state[key] = value
    
    def log_interaction(self, action: str, details: Dict[str, Any] = None) -> None:
        """
        Log user interaction for analytics/debugging.
        
        Args:
            action: Action performed
            details: Additional details about the interaction
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'component': self.name,
            'action': action,
            'details': details or {}
        }
        
        # Store in session state for debugging
        if 'interaction_log' not in st.session_state:
            st.session_state.interaction_log = []
        
        st.session_state.interaction_log.append(log_entry)
        
        # Keep only last 100 entries to prevent memory issues
        if len(st.session_state.interaction_log) > 100:
            st.session_state.interaction_log = st.session_state.interaction_log[-100:]
    
    @abstractmethod
    def render(self) -> Any:
        """
        Render the component UI.
        
        This method must be implemented by all concrete components.
        
        Returns:
            Component output (varies by component type)
        """
        pass
    
    def __str__(self) -> str:
        """String representation of the component."""
        return f"{self.__class__.__name__}(name='{self.name}')"
    
    def __repr__(self) -> str:
        """Detailed string representation of the component."""
        return f"{self.__class__.__name__}(name='{self.name}', key_prefix='{self.key_prefix}')"


class ComponentFactory:
    """
    Factory class for creating and managing components.
    """
    
    _components: Dict[str, BaseComponent] = {}
    
    @classmethod
    def register_component(cls, name: str, component: BaseComponent) -> None:
        """
        Register a component instance.
        
        Args:
            name: Unique name for the component
            component: Component instance
        """
        cls._components[name] = component
    
    @classmethod
    def get_component(cls, name: str) -> Optional[BaseComponent]:
        """
        Get a registered component by name.
        
        Args:
            name: Component name
            
        Returns:
            Component instance or None if not found
        """
        return cls._components.get(name)
    
    @classmethod
    def clear_components(cls) -> None:
        """Clear all registered components."""
        cls._components.clear()
    
    @classmethod
    def list_components(cls) -> List[str]:
        """Get list of all registered component names."""
        return list(cls._components.keys())