"""
Exception hierarchy for molecular analyzer.

Provides a clear exception hierarchy for different types of errors that can occur
during molecular analysis operations.
"""

from typing import Optional, Dict, Any


class MolecularAnalyzerException(Exception):
    """
    Base exception for all molecular analyzer errors.
    
    Provides consistent error handling with context information and recovery hints.
    """
    
    def __init__(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        recovery_hint: Optional[str] = None
    ):
        super().__init__(message)
        self.context = context or {}
        self.recovery_hint = recovery_hint
        
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.recovery_hint:
            return f"{base_msg}\nRecovery hint: {self.recovery_hint}"
        return base_msg


class ValidationError(MolecularAnalyzerException):
    """
    Raised when input validation fails.
    
    Common cases:
    - Invalid SMILES strings
    - Malformed molecular data
    - Configuration validation errors
    """
    
    def __init__(
        self, 
        message: str, 
        invalid_input: Optional[str] = None,
        validation_rule: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if invalid_input:
            context['invalid_input'] = invalid_input
        if validation_rule:
            context['validation_rule'] = validation_rule
            
        super().__init__(
            message, 
            context=context,
            recovery_hint=kwargs.get('recovery_hint', "Check input format and try again")
        )


class AnalysisError(MolecularAnalyzerException):
    """
    Raised when molecular analysis operations fail.
    
    Common cases:
    - Property calculation failures
    - 3D structure generation errors
    - Conformer optimization issues
    """
    
    def __init__(
        self, 
        message: str, 
        operation: Optional[str] = None,
        smiles: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if operation:
            context['operation'] = operation
        if smiles:
            context['smiles'] = smiles
            
        super().__init__(
            message,
            context=context, 
            recovery_hint=kwargs.get('recovery_hint', "Try with a different molecule or check input validity")
        )


class ComputationError(MolecularAnalyzerException):
    """
    Raised when computational chemistry calculations fail.
    
    Common cases:
    - RDKit computation errors
    - Memory issues with large molecules
    - Timeout in optimization procedures
    """
    
    def __init__(
        self, 
        message: str,
        computation_type: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if computation_type:
            context['computation_type'] = computation_type
            
        super().__init__(
            message,
            context=context,
            recovery_hint=kwargs.get('recovery_hint', "Try reducing molecule complexity or adjusting computation parameters")
        )


class ConfigurationError(MolecularAnalyzerException):
    """
    Raised when configuration-related errors occur.
    
    Common cases:
    - Invalid configuration values
    - Missing required configuration
    - Incompatible configuration combinations
    """
    
    def __init__(
        self, 
        message: str,
        config_key: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if config_key:
            context['config_key'] = config_key
            
        super().__init__(
            message,
            context=context,
            recovery_hint=kwargs.get('recovery_hint', "Check configuration documentation and update settings")
        )


class DataExportError(MolecularAnalyzerException):
    """
    Raised when data export operations fail.
    
    Common cases:
    - File permission issues
    - Invalid export format
    - Data serialization errors
    """
    
    def __init__(
        self, 
        message: str,
        export_format: Optional[str] = None,
        file_path: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if export_format:
            context['export_format'] = export_format
        if file_path:
            context['file_path'] = file_path
            
        super().__init__(
            message,
            context=context,
            recovery_hint=kwargs.get('recovery_hint', "Check file permissions and export format compatibility")
        )


class FileIOError(MolecularAnalyzerException):
    """
    Raised when file I/O operations fail.
    
    Common cases:
    - File not found
    - Permission denied
    - Invalid file format
    - Corrupted file data
    """
    
    def __init__(
        self, 
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if file_path:
            context['file_path'] = file_path
        if operation:
            context['operation'] = operation
            
        super().__init__(
            message,
            context=context,
            recovery_hint=kwargs.get('recovery_hint', "Check file path, permissions, and format")
        )