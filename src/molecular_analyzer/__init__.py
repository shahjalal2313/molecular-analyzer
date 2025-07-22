"""
Molecular Analyzer Package

A comprehensive toolkit for molecular analysis including property calculation,
conformational analysis, comparison studies, and file I/O operations for 
computational chemistry applications.

Core Modules:
    core: Basic molecular operations, validation, and utilities
    calculator: Main analysis engine and molecular analyzer class
    properties: Basic molecular property calculations
    advanced_properties: Advanced property calculations and drug-likeness
    conformational: 3D structure generation and conformational analysis
    comparison: Molecular similarity and statistical analysis
    io_utils: File input/output utilities and format support

Example:
    >>> from molecular_analyzer import MolecularAnalyzer
    >>> analyzer = MolecularAnalyzer()
    >>> result = analyzer.analyze("CCO")
    >>> print(result["properties"]["molecular_weight"])
    46.07
"""

# Legacy core functions (backwards compatibility)
from .core import (
    create_molecule_from_smiles,
    validate_smiles,
    get_basic_info,
    smiles_to_formula,
    COMMON_MOLECULES
)

# New OOP models (optional for advanced usage)
# These will be added to __all__ at the end if available
_OOP_MODELS = []
try:
    from .models.models import MoleculeData, PropertyData, AnalysisResult
    from .models.exceptions import MolecularAnalyzerException, ValidationError
    _OOP_MODELS = ['MoleculeData', 'PropertyData', 'AnalysisResult', 'MolecularAnalyzerException', 'ValidationError']
except ImportError:
    # OOP models not available yet, skip for now
    pass

# New OOP calculators (optional for advanced usage)
_OOP_CALCULATORS = []
try:
    from .calculators import (
        BasicPropertiesCalculator,
        DrugLikePropertiesCalculator,
        ComprehensivePropertiesCalculator,
        AdvancedPropertiesCalculator,
        ConformationalCalculator,
        ComparisonCalculator,
        CalculatorFactory
    )
    _OOP_CALCULATORS = [
        'BasicPropertiesCalculator', 
        'DrugLikePropertiesCalculator', 
        'ComprehensivePropertiesCalculator',
        'AdvancedPropertiesCalculator',
        'ConformationalCalculator',
        'ComparisonCalculator',
        'CalculatorFactory'
    ]
except ImportError:
    # OOP calculators not available yet, skip for now
    pass

# New OOP workflows (optional for advanced usage)
_OOP_WORKFLOWS = []
try:
    from .workflows import (
        MolecularAnalysisWorkflow,
        BatchAnalysisWorkflow
    )
    _OOP_WORKFLOWS = [
        'MolecularAnalysisWorkflow',
        'BatchAnalysisWorkflow'
    ]
except ImportError:
    # OOP workflows not available yet, skip for now
    pass

# New OOP visualization (optional for advanced usage)
_OOP_VISUALIZATION = []
try:
    from .visualization import (
        Chart2DRenderer,
        Molecule3DRenderer,
        ReportGenerator
    )
    _OOP_VISUALIZATION = [
        'Chart2DRenderer',
        'Molecule3DRenderer',
        'ReportGenerator'
    ]
except ImportError:
    # OOP visualization not available yet, skip for now
    pass

# Main analyzer class (primary interface)
from .calculator import (
    MolecularAnalyzer,
    analyze_molecule
)

# Core property calculations
from .properties import (
    calculate_basic_properties,
    calculate_drug_like_properties,
    calculate_all_properties,
    assess_drug_likeness,
    BASIC_PROPERTIES,
    DRUG_LIKE_PROPERTIES
)

# Advanced property calculations
from .advanced_properties import (
    calculate_lipophilicity_profile,
    calculate_admet_descriptors,
    assess_drug_likeness_rules,
    comprehensive_property_analysis
)

# Conformational analysis
from .conformational import (
    ConformerGenerator,
    perform_conformational_analysis
)

# Molecular comparison and statistics  
from .comparison import (
    calculate_similarity_matrix,
    compare_molecules,
    compare_drug_likeness,
    create_comparison_dashboard
)

# File I/O operations
from .io_utils import (
    read_smiles_file,
    write_molecules_csv,
    read_csv_molecules,
    create_sdf_file,
    read_sdf_file,
    batch_process_files,
    SUPPORTED_FORMATS
)

__version__ = "1.0.0"
__author__ = "SHAH MD. JALAL UDDIN"
__email__ = "shahjalal2313@gmail.com"
__description__ = "Molecular analysis toolkit for computational chemistry"


def quick_analysis(smiles: str) -> dict:
    """
    Perform quick analysis of a molecule from SMILES.

    Args:
        smiles (str): SMILES string

    Returns:
        dict: Complete analysis results

    Example:
        >>> result = quick_analysis("CCO")
        >>> print(result["valid"])
        True
    """
    result = {
        "smiles": smiles,
        "valid": False,
        "properties": {},
        "assessment": {}
    }

    mol = create_molecule_from_smiles(smiles)
    if mol:
        result["valid"] = True
        result["properties"] = calculate_all_properties(mol)
        result["assessment"] = assess_drug_likeness(result["properties"])

    return result


def get_package_info() -> dict:
    """
    Get package information and capabilities.

    Returns:
        dict: Package information
    """
    return {
        "name": "molecular_analyzer",
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "modules": ["core", "calculator", "properties", "advanced_properties", "conformational", "comparison", "io_utils"],
        "supported_formats": list(SUPPORTED_FORMATS.keys()),
        "common_molecules": len(COMMON_MOLECULES),
        "oop_capabilities": {
            "models": len(_OOP_MODELS) > 0,
            "calculators": len(_OOP_CALCULATORS) > 0,
            "workflows": len(_OOP_WORKFLOWS) > 0,
            "visualization": len(_OOP_VISUALIZATION) > 0
        }
    }


# OOP convenience functions for easy instantiation
def create_analyzer_workflow(config=None):
    """
    Create a MolecularAnalysisWorkflow with optional configuration.
    
    Args:
        config: Optional AnalysisConfig or dict
        
    Returns:
        MolecularAnalysisWorkflow instance
        
    Example:
        >>> workflow = create_analyzer_workflow()
        >>> result = workflow.analyze_smiles("CCO")
    """
    if 'MolecularAnalysisWorkflow' in globals():
        if config is None:
            return MolecularAnalysisWorkflow()
        else:
            return MolecularAnalysisWorkflow(config=config)
    else:
        raise ImportError("MolecularAnalysisWorkflow not available. OOP structure may not be fully initialized.")


def create_calculator_factory():
    """
    Create a CalculatorFactory for dynamic calculator management.
    
    Returns:
        CalculatorFactory instance
        
    Example:
        >>> factory = create_calculator_factory()
        >>> basic_calc = factory.create_calculator('basic')
    """
    if 'CalculatorFactory' in globals():
        return CalculatorFactory()
    else:
        raise ImportError("CalculatorFactory not available. OOP structure may not be fully initialized.")


def create_basic_calculator(config=None):
    """
    Create a BasicPropertiesCalculator with optional configuration.
    
    Args:
        config: Optional AnalysisConfig or dict
        
    Returns:
        BasicPropertiesCalculator instance
    """
    if 'BasicPropertiesCalculator' in globals():
        if config is None:
            return BasicPropertiesCalculator()
        else:
            return BasicPropertiesCalculator(config=config)
    else:
        raise ImportError("BasicPropertiesCalculator not available. OOP structure may not be fully initialized.")


# Package metadata
__all__ = [
    # Main interface
    "MolecularAnalyzer",
    "analyze_molecule",
    "quick_analysis",
    
    # Core functions
    "create_molecule_from_smiles",
    "validate_smiles", 
    "get_basic_info",
    "smiles_to_formula",

    # Property calculations
    "calculate_basic_properties",
    "calculate_drug_like_properties",
    "calculate_all_properties",
    "assess_drug_likeness",
    
    # Advanced property calculations
    "calculate_lipophilicity_profile",
    "calculate_admet_descriptors",
    "assess_drug_likeness_rules",
    "comprehensive_property_analysis",

    # Conformational analysis
    "ConformerGenerator",
    "perform_conformational_analysis",

    # Comparison and similarity
    "calculate_similarity_matrix",
    "compare_molecules", 
    "compare_drug_likeness",
    "create_comparison_dashboard",

    # I/O functions
    "read_smiles_file",
    "write_molecules_csv",
    "read_csv_molecules",
    "create_sdf_file",
    "read_sdf_file",
    "batch_process_files",

    # Utility functions
    "get_package_info",
    
    # OOP convenience functions
    "create_analyzer_workflow",
    "create_calculator_factory", 
    "create_basic_calculator",

    # Constants
    "COMMON_MOLECULES",
    "BASIC_PROPERTIES",
    "DRUG_LIKE_PROPERTIES",
    "SUPPORTED_FORMATS"
]

# Add OOP models, calculators, workflows, and visualization if available
__all__.extend(_OOP_MODELS)
__all__.extend(_OOP_CALCULATORS)
__all__.extend(_OOP_WORKFLOWS)
__all__.extend(_OOP_VISUALIZATION)
