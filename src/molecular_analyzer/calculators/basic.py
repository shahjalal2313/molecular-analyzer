"""
Basic properties calculator implementation.

Provides OOP interface for calculating fundamental molecular properties
using RDKit with caching, error handling, and result formatting.
"""

from typing import Dict, Any, List, Optional, Union
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, Descriptors

from ..models.base import BaseCalculator, CalculationConfig
from ..models.models import MoleculeData, PropertyData
from ..models.exceptions import ComputationError, ValidationError


class BasicPropertiesCalculator(BaseCalculator[PropertyData]):
    """
    Calculator for basic molecular properties.
    
    Computes fundamental molecular descriptors including molecular weight,
    atom counts, ring information, and structural features using RDKit.
    """
    
    @property
    def calculator_name(self) -> str:
        """Return the name of this calculator."""
        return "BasicPropertiesCalculator"
    
    @property
    def supported_properties(self) -> List[str]:
        """Return list of properties this calculator can compute."""
        return [
            "molecular_weight",
            "formula", 
            "num_atoms",
            "num_bonds",
            "num_heavy_atoms",
            "num_rings",
            "num_aromatic_rings",
            "num_rotatable_bonds"
        ]
    
    def _calculate_properties(self, molecule: MoleculeData) -> PropertyData:
        """
        Calculate basic molecular properties using RDKit.
        
        Args:
            molecule: Validated molecule data
            
        Returns:
            PropertyData object with calculated properties
            
        Raises:
            ComputationError: If RDKit calculations fail
            ValidationError: If molecule cannot be processed
        """
        try:
            # Convert SMILES to RDKit molecule
            mol = Chem.MolFromSmiles(molecule.smiles)
            if mol is None:
                raise ValidationError(
                    f"RDKit cannot parse SMILES: {molecule.smiles}",
                    invalid_input=molecule.smiles,
                    validation_rule="Valid RDKit SMILES"
                )
            
            # Add explicit hydrogens for accurate calculations
            mol = Chem.AddHs(mol)
            
            # Calculate all basic properties
            properties = {}
            
            # Molecular weight and formula
            try:
                properties["molecular_weight"] = round(rdMolDescriptors.CalcExactMolWt(mol), 2)
                properties["formula"] = rdMolDescriptors.CalcMolFormula(mol)
            except Exception as e:
                raise ComputationError(
                    "Failed to calculate molecular weight or formula",
                    computation_type="molecular_weight_formula",
                    smiles=molecule.smiles
                ) from e
            
            # Atom and bond counts
            try:
                properties["num_atoms"] = mol.GetNumAtoms()
                properties["num_bonds"] = mol.GetNumBonds()
                properties["num_heavy_atoms"] = mol.GetNumHeavyAtoms()
            except Exception as e:
                raise ComputationError(
                    "Failed to calculate atom/bond counts",
                    computation_type="atom_bond_counts",
                    smiles=molecule.smiles
                ) from e
            
            # Ring information
            try:
                properties["num_rings"] = rdMolDescriptors.CalcNumRings(mol)
                properties["num_aromatic_rings"] = rdMolDescriptors.CalcNumAromaticRings(mol)
            except Exception as e:
                raise ComputationError(
                    "Failed to calculate ring information",
                    computation_type="ring_analysis",
                    smiles=molecule.smiles
                ) from e
            
            # Rotatable bonds
            try:
                properties["num_rotatable_bonds"] = rdMolDescriptors.CalcNumRotatableBonds(mol)
            except Exception as e:
                raise ComputationError(
                    "Failed to calculate rotatable bonds",
                    computation_type="rotatable_bonds",
                    smiles=molecule.smiles
                ) from e
            
            # Create PropertyData object
            property_data = PropertyData(
                properties=properties,
                calculation_method=self.calculator_name,
                metadata={
                    'rdkit_version': Chem.rdBase.rdkitVersion,
                    'smiles_input': molecule.smiles,
                    'explicit_hydrogens': True,
                    'precision': self.config.precision
                }
            )
            
            return property_data
            
        except (ValidationError, ComputationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Handle unexpected errors
            raise ComputationError(
                f"Unexpected error in basic properties calculation: {str(e)}",
                computation_type="basic_properties",
                smiles=molecule.smiles
            ) from e


class DrugLikePropertiesCalculator(BaseCalculator[PropertyData]):
    """
    Calculator for drug-likeness properties.
    
    Computes Lipinski's Rule of Five parameters and other drug-relevant
    molecular descriptors using RDKit.
    """
    
    @property
    def calculator_name(self) -> str:
        """Return the name of this calculator."""
        return "DrugLikePropertiesCalculator"
    
    @property
    def supported_properties(self) -> List[str]:
        """Return list of properties this calculator can compute."""
        return [
            "molecular_weight",
            "logP",
            "hbd",  # Hydrogen bond donors
            "hba",  # Hydrogen bond acceptors
            "tpsa", # Topological polar surface area
            "lipinski_violations",
            "drug_like"
        ]
    
    def _calculate_properties(self, molecule: MoleculeData) -> PropertyData:
        """
        Calculate drug-like properties using RDKit.
        
        Args:
            molecule: Validated molecule data
            
        Returns:
            PropertyData object with calculated drug-like properties
            
        Raises:
            ComputationError: If RDKit calculations fail
            ValidationError: If molecule cannot be processed
        """
        try:
            # Convert SMILES to RDKit molecule
            mol = Chem.MolFromSmiles(molecule.smiles)
            if mol is None:
                raise ValidationError(
                    f"RDKit cannot parse SMILES: {molecule.smiles}",
                    invalid_input=molecule.smiles,
                    validation_rule="Valid RDKit SMILES"
                )
            
            # Calculate drug-like properties
            properties = {}
            
            try:
                # Core Lipinski parameters
                mw = rdMolDescriptors.CalcExactMolWt(mol)
                logp = Descriptors.MolLogP(mol)
                hbd = rdMolDescriptors.CalcNumHBD(mol)
                hba = rdMolDescriptors.CalcNumHBA(mol)
                tpsa = rdMolDescriptors.CalcTPSA(mol)
                
                properties["molecular_weight"] = round(mw, 2)
                properties["logP"] = round(logp, 2)
                properties["hbd"] = hbd
                properties["hba"] = hba
                properties["tpsa"] = round(tpsa, 2)
                
            except Exception as e:
                raise ComputationError(
                    "Failed to calculate Lipinski parameters",
                    computation_type="lipinski_parameters",
                    smiles=molecule.smiles
                ) from e
            
            # Calculate Lipinski violations
            try:
                violations = 0
                if mw > 500: violations += 1
                if logp > 5: violations += 1
                if hbd > 5: violations += 1
                if hba > 10: violations += 1
                
                properties["lipinski_violations"] = violations
                properties["drug_like"] = violations <= 1
                
            except Exception as e:
                raise ComputationError(
                    "Failed to assess Lipinski violations",
                    computation_type="lipinski_assessment",
                    smiles=molecule.smiles
                ) from e
            
            # Create PropertyData object
            property_data = PropertyData(
                properties=properties,
                calculation_method=self.calculator_name,
                metadata={
                    'rdkit_version': Chem.rdBase.rdkitVersion,
                    'smiles_input': molecule.smiles,
                    'lipinski_rules': {
                        'mw_limit': 500,
                        'logp_limit': 5,
                        'hbd_limit': 5,
                        'hba_limit': 10
                    },
                    'precision': self.config.precision
                }
            )
            
            return property_data
            
        except (ValidationError, ComputationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Handle unexpected errors
            raise ComputationError(
                f"Unexpected error in drug-like properties calculation: {str(e)}",
                computation_type="drug_like_properties",
                smiles=molecule.smiles
            ) from e


class ComprehensivePropertiesCalculator(BaseCalculator[PropertyData]):
    """
    Calculator that combines basic and drug-like properties.
    
    Provides a unified interface for calculating all fundamental molecular
    properties in a single operation with optimized performance.
    """
    
    def __init__(self, config: Optional[CalculationConfig] = None):
        super().__init__(config)
        self._basic_calc = BasicPropertiesCalculator(config)
        self._drug_calc = DrugLikePropertiesCalculator(config)
    
    @property
    def calculator_name(self) -> str:
        """Return the name of this calculator."""
        return "ComprehensivePropertiesCalculator"
    
    @property
    def supported_properties(self) -> List[str]:
        """Return list of properties this calculator can compute."""
        # Combine properties from both calculators, removing duplicates
        basic_props = set(self._basic_calc.supported_properties)
        drug_props = set(self._drug_calc.supported_properties)
        all_props = basic_props.union(drug_props)
        return sorted(list(all_props))
    
    def _calculate_properties(self, molecule: MoleculeData) -> PropertyData:
        """
        Calculate comprehensive molecular properties.
        
        Args:
            molecule: Validated molecule data
            
        Returns:
            PropertyData object with all calculated properties
            
        Raises:
            ComputationError: If calculations fail
        """
        try:
            # Calculate basic properties
            basic_props = self._basic_calc._calculate_properties(molecule)
            
            # Calculate drug-like properties
            drug_props = self._drug_calc._calculate_properties(molecule)
            
            # Merge properties (drug-like properties take precedence for duplicates)
            combined_properties = {**basic_props.properties, **drug_props.properties}
            
            # Add derived properties
            if "num_atoms" in combined_properties and "molecular_weight" in combined_properties:
                if combined_properties["num_atoms"] > 0:
                    combined_properties["average_atomic_weight"] = round(
                        combined_properties["molecular_weight"] / combined_properties["num_atoms"], 2
                    )
            
            # Create combined PropertyData
            property_data = PropertyData(
                properties=combined_properties,
                calculation_method=self.calculator_name,
                metadata={
                    'rdkit_version': Chem.rdBase.rdkitVersion,
                    'smiles_input': molecule.smiles,
                    'calculation_components': [
                        self._basic_calc.calculator_name,
                        self._drug_calc.calculator_name
                    ],
                    'derived_properties': ['average_atomic_weight'],
                    'precision': self.config.precision
                }
            )
            
            return property_data
            
        except Exception as e:
            if isinstance(e, (ValidationError, ComputationError)):
                raise
            else:
                raise ComputationError(
                    f"Unexpected error in comprehensive properties calculation: {str(e)}",
                    computation_type="comprehensive_properties",
                    smiles=molecule.smiles
                ) from e


# Property assessment functions that work with PropertyData objects

def assess_drug_likeness(property_data: PropertyData) -> Dict[str, Any]:
    """
    Assess drug-likeness based on calculated properties.
    
    Args:
        property_data: PropertyData object with calculated properties
        
    Returns:
        Dictionary with drug-likeness assessment and recommendations
    """
    properties = property_data.properties
    
    assessment = {
        "overall": "Unknown",
        "molecular_weight": "Unknown",
        "lipophilicity": "Unknown", 
        "hydrogen_bonding": "Unknown",
        "recommendations": []
    }
    
    # Overall assessment based on Lipinski violations
    if "lipinski_violations" in properties:
        violations = properties["lipinski_violations"]
        if violations == 0:
            assessment["overall"] = "Excellent drug-likeness"
        elif violations == 1:
            assessment["overall"] = "Good drug-likeness"
        else:
            assessment["overall"] = "Poor drug-likeness"
    
    # Molecular weight assessment
    if "molecular_weight" in properties:
        mw = properties["molecular_weight"]
        if mw <= 500:
            assessment["molecular_weight"] = "Appropriate"
        else:
            assessment["molecular_weight"] = "Too high"
            assessment["recommendations"].append("Reduce molecular size")
    
    # LogP assessment
    if "logP" in properties:
        logp = properties["logP"]
        if logp <= 5:
            assessment["lipophilicity"] = "Appropriate"
        else:
            assessment["lipophilicity"] = "Too lipophilic"
            assessment["recommendations"].append("Reduce lipophilicity")
    
    # Hydrogen bonding assessment
    if "hbd" in properties and "hba" in properties:
        hbd = properties["hbd"]
        hba = properties["hba"]
        if hbd <= 5 and hba <= 10:
            assessment["hydrogen_bonding"] = "Appropriate"
        else:
            assessment["hydrogen_bonding"] = "Excessive"
            assessment["recommendations"].append("Optimize hydrogen bonding")
    
    return assessment


# Property categories for organization (compatible with legacy code)
BASIC_PROPERTIES = [
    "molecular_weight", "num_atoms", "num_bonds", 
    "num_heavy_atoms", "num_rings"
]

DRUG_LIKE_PROPERTIES = [
    "logP", "hbd", "hba", "tpsa", "lipinski_violations"
]

STRUCTURAL_PROPERTIES = [
    "num_aromatic_rings", "num_rotatable_bonds"
]


# Legacy compatibility functions that wrap the OOP calculators

def calculate_basic_properties(mol: Chem.Mol) -> Dict[str, Any]:
    """
    Legacy compatibility function for basic properties calculation.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Dictionary with basic properties (legacy format)
    """
    if mol is None:
        return {}
    
    try:
        # Convert RDKit mol to SMILES for our OOP system
        smiles = Chem.MolToSmiles(mol)
        molecule_data = MoleculeData(smiles=smiles)
        
        # Use OOP calculator
        calculator = BasicPropertiesCalculator()
        result = calculator.calculate(molecule_data)
        
        return result.properties
        
    except Exception as e:
        return {"error": str(e)}


def calculate_drug_like_properties(mol: Chem.Mol) -> Dict[str, Any]:
    """
    Legacy compatibility function for drug-like properties calculation.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Dictionary with drug-like properties (legacy format)
    """
    if mol is None:
        return {}
    
    try:
        # Convert RDKit mol to SMILES for our OOP system
        smiles = Chem.MolToSmiles(mol)
        molecule_data = MoleculeData(smiles=smiles)
        
        # Use OOP calculator
        calculator = DrugLikePropertiesCalculator()
        result = calculator.calculate(molecule_data)
        
        return result.properties
        
    except Exception as e:
        return {"error": str(e)}


def calculate_all_properties(mol: Chem.Mol) -> Dict[str, Any]:
    """
    Legacy compatibility function for comprehensive properties calculation.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Dictionary with all calculated properties (legacy format)
    """
    if mol is None:
        return {}
    
    try:
        # Convert RDKit mol to SMILES for our OOP system
        smiles = Chem.MolToSmiles(mol)
        molecule_data = MoleculeData(smiles=smiles)
        
        # Use OOP calculator
        calculator = ComprehensivePropertiesCalculator()
        result = calculator.calculate(molecule_data)
        
        return result.properties
        
    except Exception as e:
        return {"error": str(e)}