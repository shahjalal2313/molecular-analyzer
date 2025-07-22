"""
Calculator classes for molecular property calculations.

This module provides object-oriented calculator classes that inherit from
BaseCalculator and implement specific molecular property calculations.

Available Calculators:
    BasicPropertiesCalculator: Standard molecular descriptors
    AdvancedPropertiesCalculator: Drug-likeness and advanced properties
    ConformationalCalculator: 3D structure and conformational analysis
    ComparisonCalculator: Molecular similarity and statistical analysis
    
Factory:
    CalculatorFactory: Dynamic calculator creation and management
"""

# Import calculators as they become available
try:
    from .basic import (
        BasicPropertiesCalculator,
        DrugLikePropertiesCalculator,
        ComprehensivePropertiesCalculator,
        assess_drug_likeness,
        calculate_basic_properties,
        calculate_drug_like_properties,
        calculate_all_properties,
        BASIC_PROPERTIES,
        DRUG_LIKE_PROPERTIES,
        STRUCTURAL_PROPERTIES
    )
    __all__ = [
        'BasicPropertiesCalculator',
        'DrugLikePropertiesCalculator',
        'ComprehensivePropertiesCalculator',
        'assess_drug_likeness',
        'calculate_basic_properties',
        'calculate_drug_like_properties',
        'calculate_all_properties',
        'BASIC_PROPERTIES',
        'DRUG_LIKE_PROPERTIES',
        'STRUCTURAL_PROPERTIES'
    ]
except ImportError:
    __all__ = []

try:
    from .advanced import (
        AdvancedPropertiesCalculator,
        LipophilicityCalculator,
        assess_comprehensive_drug_likeness,
        calculate_lipophilicity_profile,
        calculate_admet_descriptors,
        assess_drug_likeness_rules,
        comprehensive_property_analysis,
        LIPOPHILICITY_DESCRIPTORS,
        ADMET_DESCRIPTORS,
        DRUG_LIKENESS_RULES,
        QUANTUM_DESCRIPTORS
    )
    __all__.extend([
        'AdvancedPropertiesCalculator',
        'LipophilicityCalculator', 
        'assess_comprehensive_drug_likeness',
        'calculate_lipophilicity_profile',
        'calculate_admet_descriptors',
        'assess_drug_likeness_rules',
        'comprehensive_property_analysis',
        'LIPOPHILICITY_DESCRIPTORS',
        'ADMET_DESCRIPTORS',
        'DRUG_LIKENESS_RULES',
        'QUANTUM_DESCRIPTORS'
    ])
except ImportError:
    pass

try:
    from .conformational import (
        ConformationalCalculator,
        perform_conformational_analysis,
        generate_conformers
    )
    __all__.extend([
        'ConformationalCalculator',
        'perform_conformational_analysis', 
        'generate_conformers'
    ])
except ImportError:
    pass

try:
    from .comparison import (
        ComparisonCalculator,
        calculate_similarity_matrix,
        find_most_similar_pairs,
        calculate_property_differences
    )
    __all__.extend([
        'ComparisonCalculator',
        'calculate_similarity_matrix',
        'find_most_similar_pairs', 
        'calculate_property_differences'
    ])
except ImportError:
    pass

try:
    from .factory import CalculatorFactory
    __all__.append('CalculatorFactory')
except ImportError:
    pass

# Version info
__version__ = "1.0.0"
__author__ = "Molecular Analyzer Team"