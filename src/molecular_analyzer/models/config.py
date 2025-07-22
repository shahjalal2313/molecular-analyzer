"""
Configuration system for molecular analyzer.

Provides flexible configuration management with validation, defaults,
and support for different configuration sources.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Union, Type
from pathlib import Path
import json
import os
from .exceptions import ConfigurationError


@dataclass
class AnalysisConfig:
    """
    Configuration for molecular analysis operations.
    
    Provides comprehensive configuration options for all analysis components
    with validation and sensible defaults.
    """
    
    # General settings
    precision: str = "standard"  # minimal, standard, high, maximum
    timeout: Optional[float] = None  # seconds, None = no timeout
    max_molecules: Optional[int] = None  # None = unlimited
    
    # Calculator settings
    use_cache: bool = True
    cache_size: int = 1000
    parallel_processing: bool = False
    num_workers: Optional[int] = None  # None = auto-detect
    
    # Validation settings
    validation_level: str = "normal"  # minimal, normal, strict
    skip_invalid: bool = True
    collect_warnings: bool = True
    
    # Output settings
    include_metadata: bool = True
    include_timing: bool = False
    decimal_places: int = 4
    
    # Analysis scope settings
    include_basic_properties: bool = True
    include_advanced_properties: bool = True
    include_3d_analysis: bool = False
    
    # Advanced settings
    rdkit_options: Dict[str, Any] = field(default_factory=dict)
    custom_properties: List[str] = field(default_factory=list)
    export_options: Dict[str, Any] = field(default_factory=dict)
    include_quantum_descriptors: bool = False  # Quantum calculations are computationally expensive
    
    # Environment settings
    temp_dir: Optional[str] = None
    log_level: str = "INFO"
    debug_mode: bool = False
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate configuration values."""
        # Validate precision level
        valid_precision = ["minimal", "standard", "high", "maximum"]
        if self.precision not in valid_precision:
            raise ConfigurationError(
                f"Invalid precision level: {self.precision}",
                config_key="precision",
                recovery_hint=f"Must be one of: {valid_precision}"
            )
        
        # Validate validation level
        valid_validation = ["minimal", "normal", "strict"]
        if self.validation_level not in valid_validation:
            raise ConfigurationError(
                f"Invalid validation level: {self.validation_level}",
                config_key="validation_level",
                recovery_hint=f"Must be one of: {valid_validation}"
            )
        
        # Validate numeric values
        if self.timeout is not None and self.timeout <= 0:
            raise ConfigurationError(
                "Timeout must be positive",
                config_key="timeout"
            )
        
        if self.max_molecules is not None and self.max_molecules <= 0:
            raise ConfigurationError(
                "max_molecules must be positive",
                config_key="max_molecules"
            )
        
        if self.cache_size <= 0:
            raise ConfigurationError(
                "cache_size must be positive",
                config_key="cache_size"
            )
        
        if self.num_workers is not None and self.num_workers <= 0:
            raise ConfigurationError(
                "num_workers must be positive",
                config_key="num_workers"
            )
        
        if self.decimal_places < 0:
            raise ConfigurationError(
                "decimal_places must be non-negative",
                config_key="decimal_places"
            )
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            raise ConfigurationError(
                f"Invalid log level: {self.log_level}",
                config_key="log_level",
                recovery_hint=f"Must be one of: {valid_log_levels}"
            )
    
    def merge(self, other: 'AnalysisConfig') -> 'AnalysisConfig':
        """
        Merge with another configuration, with other taking precedence.
        
        Args:
            other: Configuration to merge with
            
        Returns:
            New merged configuration
        """
        # Convert both to dictionaries
        self_dict = asdict(self)
        other_dict = asdict(other)
        
        # Merge dictionaries (other takes precedence)
        merged = {**self_dict, **other_dict}
        
        # Handle nested dictionaries specially
        for key in ['rdkit_options', 'export_options']:
            if key in self_dict and key in other_dict:
                merged[key] = {**self_dict[key], **other_dict[key]}
        
        # Handle lists specially (extend rather than replace)
        if 'custom_properties' in self_dict and 'custom_properties' in other_dict:
            merged['custom_properties'] = list(set(
                self_dict['custom_properties'] + other_dict['custom_properties']
            ))
        
        return AnalysisConfig(**merged)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisConfig':
        """Create configuration from dictionary."""
        return cls(**data)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AnalysisConfig':
        """Create configuration from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Save configuration to file."""
        file_path = Path(file_path)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception as e:
            raise ConfigurationError(
                f"Failed to save configuration to {file_path}: {str(e)}"
            )
    
    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> 'AnalysisConfig':
        """Load configuration from file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ConfigurationError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Invalid JSON in configuration file {file_path}: {str(e)}"
            )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load configuration from {file_path}: {str(e)}"
            )


class ConfigurationManager:
    """
    Manager for handling multiple configuration sources and inheritance.
    
    Supports loading configurations from files, environment variables,
    and programmatic sources with proper precedence handling.
    """
    
    def __init__(self, base_config: Optional[AnalysisConfig] = None):
        self.base_config = base_config or AnalysisConfig()
        self._config_stack: List[AnalysisConfig] = [self.base_config]
        self._environment_prefix = "MOLECULAR_ANALYZER_"
    
    def push_config(self, config: AnalysisConfig) -> None:
        """Push a configuration onto the stack."""
        self._config_stack.append(config)
    
    def pop_config(self) -> Optional[AnalysisConfig]:
        """Pop a configuration from the stack."""
        if len(self._config_stack) > 1:
            return self._config_stack.pop()
        return None
    
    def get_effective_config(self) -> AnalysisConfig:
        """
        Get the effective configuration by merging all configurations in the stack.
        
        Returns:
            Merged configuration with later configs taking precedence
        """
        if len(self._config_stack) == 1:
            return self._config_stack[0]
        
        # Start with base config and merge each subsequent config
        effective = self._config_stack[0]
        for config in self._config_stack[1:]:
            effective = effective.merge(config)
        
        return effective
    
    def load_from_environment(self) -> AnalysisConfig:
        """
        Load configuration from environment variables.
        
        Environment variables should be prefixed with MOLECULAR_ANALYZER_
        and use uppercase names. For example: MOLECULAR_ANALYZER_PRECISION=high
        
        Returns:
            Configuration from environment variables
        """
        env_config = {}
        
        # Map environment variable names to config field names
        env_mapping = {
            'PRECISION': 'precision',
            'TIMEOUT': 'timeout',
            'MAX_MOLECULES': 'max_molecules',
            'USE_CACHE': 'use_cache',
            'CACHE_SIZE': 'cache_size',
            'PARALLEL_PROCESSING': 'parallel_processing',
            'NUM_WORKERS': 'num_workers',
            'VALIDATION_LEVEL': 'validation_level',
            'SKIP_INVALID': 'skip_invalid',
            'COLLECT_WARNINGS': 'collect_warnings',
            'INCLUDE_METADATA': 'include_metadata',
            'INCLUDE_TIMING': 'include_timing',
            'DECIMAL_PLACES': 'decimal_places',
            'TEMP_DIR': 'temp_dir',
            'LOG_LEVEL': 'log_level',
            'DEBUG_MODE': 'debug_mode'
        }
        
        for env_key, config_key in env_mapping.items():
            full_env_key = f"{self._environment_prefix}{env_key}"
            if full_env_key in os.environ:
                value = os.environ[full_env_key]
                
                # Type conversion based on config field
                if config_key in ['timeout', 'max_molecules', 'cache_size', 'num_workers', 'decimal_places']:
                    try:
                        env_config[config_key] = int(value) if value != 'None' else None
                    except ValueError:
                        continue
                elif config_key in ['use_cache', 'parallel_processing', 'skip_invalid', 
                                  'collect_warnings', 'include_metadata', 'include_timing', 'debug_mode']:
                    env_config[config_key] = value.lower() in ['true', '1', 'yes', 'on']
                else:
                    env_config[config_key] = value
        
        return AnalysisConfig(**env_config) if env_config else AnalysisConfig()
    
    def load_from_file(self, file_path: Union[str, Path]) -> None:
        """Load and push configuration from file."""
        config = AnalysisConfig.load_from_file(file_path)
        self.push_config(config)
    
    def set_environment_prefix(self, prefix: str) -> None:
        """Set the prefix for environment variables."""
        self._environment_prefix = prefix.upper().rstrip('_') + '_'


# Pre-defined configuration profiles

def get_development_config() -> AnalysisConfig:
    """Get configuration optimized for development."""
    return AnalysisConfig(
        precision="standard",
        debug_mode=True,
        log_level="DEBUG",
        include_timing=True,
        validation_level="normal",
        use_cache=True,
        cache_size=100
    )


def get_production_config() -> AnalysisConfig:
    """Get configuration optimized for production."""
    return AnalysisConfig(
        precision="high",
        debug_mode=False,
        log_level="INFO",
        include_timing=False,
        validation_level="strict",
        use_cache=True,
        cache_size=10000,
        parallel_processing=True
    )


def get_performance_config() -> AnalysisConfig:
    """Get configuration optimized for performance."""
    return AnalysisConfig(
        precision="standard",
        debug_mode=False,
        log_level="WARNING",
        include_timing=False,
        validation_level="minimal",
        use_cache=True,
        cache_size=50000,
        parallel_processing=True,
        skip_invalid=True,
        include_metadata=False
    )


def get_research_config() -> AnalysisConfig:
    """Get configuration optimized for research use."""
    return AnalysisConfig(
        precision="maximum",
        debug_mode=True,
        log_level="DEBUG",
        include_timing=True,
        validation_level="strict",
        use_cache=True,
        cache_size=1000,
        include_metadata=True,
        collect_warnings=True,
        decimal_places=6
    )