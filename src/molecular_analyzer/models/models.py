"""
Core data models for molecular analysis.

Provides type-safe data classes for representing molecules, properties, and analysis results
with comprehensive validation and serialization support.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime
import json
import re

from .exceptions import ValidationError


@dataclass
class MoleculeData:
    """
    Represents a molecule with validation and metadata.
    
    Core data structure for all molecular analysis operations.
    Provides SMILES validation, metadata tracking, and serialization.
    """
    
    smiles: str
    name: Optional[str] = None
    source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    validated: bool = False
    validation_timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate SMILES and set validation timestamp."""
        if not self.validated:
            self.validate()
    
    def validate(self) -> bool:
        """
        Validate the SMILES string and mark as validated.
        
        Returns:
            True if validation passes
            
        Raises:
            ValidationError: If SMILES is invalid
        """
        if not self.smiles:
            raise ValidationError("SMILES string cannot be empty")
        
        # Basic SMILES format validation
        if not isinstance(self.smiles, str):
            raise ValidationError("SMILES must be a string")
        
        # Check for basic SMILES patterns
        if not re.match(r'^[A-Za-z0-9\[\]()=#@\-+\\/\\.:]+$', self.smiles):
            raise ValidationError(
                f"Invalid SMILES format: {self.smiles}",
                invalid_input=self.smiles,
                validation_rule="SMILES character set"
            )
        
        # Additional RDKit validation would go here in production
        try:
            # Placeholder for RDKit validation
            # from rdkit import Chem
            # mol = Chem.MolFromSmiles(self.smiles)
            # if mol is None:
            #     raise ValidationError(f"RDKit cannot parse SMILES: {self.smiles}")
            pass
        except Exception as e:
            raise ValidationError(f"SMILES validation failed: {str(e)}")
        
        self.validated = True
        self.validation_timestamp = datetime.now()
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        if self.validation_timestamp:
            data['validation_timestamp'] = self.validation_timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MoleculeData':
        """Create instance from dictionary."""
        if 'validation_timestamp' in data and data['validation_timestamp']:
            data['validation_timestamp'] = datetime.fromisoformat(data['validation_timestamp'])
        return cls(**data)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MoleculeData':
        """Create instance from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class PropertyData:
    """
    Represents calculated molecular properties with metadata.
    
    Stores property values with calculation metadata, validation status,
    and uncertainty information where available.
    """
    
    properties: Dict[str, Union[float, int, str, bool]] = field(default_factory=dict)
    calculation_method: Optional[str] = None
    calculation_timestamp: Optional[datetime] = None
    uncertainty: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Set calculation timestamp if not provided."""
        if self.calculation_timestamp is None:
            self.calculation_timestamp = datetime.now()
    
    def add_property(
        self, 
        name: str, 
        value: Union[float, int, str, bool], 
        uncertainty: Optional[float] = None
    ) -> None:
        """Add a property with optional uncertainty."""
        self.properties[name] = value
        if uncertainty is not None:
            self.uncertainty[name] = uncertainty
    
    def get_property(self, name: str, default: Any = None) -> Any:
        """Get property value with optional default."""
        return self.properties.get(name, default)
    
    def has_property(self, name: str) -> bool:
        """Check if property exists."""
        return name in self.properties
    
    def get_numeric_properties(self) -> Dict[str, Union[float, int]]:
        """Get only numeric properties."""
        return {
            k: v for k, v in self.properties.items() 
            if isinstance(v, (int, float))
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        if self.calculation_timestamp:
            data['calculation_timestamp'] = self.calculation_timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PropertyData':
        """Create instance from dictionary."""
        if 'calculation_timestamp' in data and data['calculation_timestamp']:
            data['calculation_timestamp'] = datetime.fromisoformat(data['calculation_timestamp'])
        return cls(**data)


@dataclass
class AnalysisResult:
    """
    Complete analysis result containing molecule, properties, and metadata.
    
    Top-level container for all analysis information including source molecule,
    calculated properties, analysis configuration, and execution metadata.
    """
    
    molecule: MoleculeData
    properties: PropertyData
    analysis_config: Dict[str, Any] = field(default_factory=dict)
    execution_time: Optional[float] = None
    success: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    analysis_timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        """Set analysis timestamp if not provided."""
        if self.analysis_timestamp is None:
            self.analysis_timestamp = datetime.now()
    
    def add_error(self, error: str) -> None:
        """Add an error message and mark as failed."""
        self.errors.append(error)
        self.success = False
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
    
    def is_successful(self) -> bool:
        """Check if analysis was successful."""
        return self.success and len(self.errors) == 0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the analysis result."""
        return {
            'smiles': self.molecule.smiles,
            'molecule_name': self.molecule.name,
            'success': self.success,
            'property_count': len(self.properties.properties),
            'execution_time': self.execution_time,
            'errors': len(self.errors),
            'warnings': len(self.warnings),
            'timestamp': self.analysis_timestamp.isoformat() if self.analysis_timestamp else None
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'molecule': self.molecule.to_dict(),
            'properties': self.properties.to_dict(),
            'analysis_config': self.analysis_config,
            'execution_time': self.execution_time,
            'success': self.success,
            'errors': self.errors,
            'warnings': self.warnings,
            'analysis_timestamp': self.analysis_timestamp.isoformat() if self.analysis_timestamp else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        """Create instance from dictionary."""
        molecule_data = data.pop('molecule')
        properties_data = data.pop('properties')
        
        if 'analysis_timestamp' in data and data['analysis_timestamp']:
            data['analysis_timestamp'] = datetime.fromisoformat(data['analysis_timestamp'])
        
        return cls(
            molecule=MoleculeData.from_dict(molecule_data),
            properties=PropertyData.from_dict(properties_data),
            **data
        )
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AnalysisResult':
        """Create instance from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


# Type aliases for common use cases
MoleculeInput = Union[str, MoleculeData]
PropertyValue = Union[float, int, str, bool]
PropertyDict = Dict[str, PropertyValue]
AnalysisResultList = List[AnalysisResult]