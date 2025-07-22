"""
Advanced properties calculator implementation.

Provides OOP interface for calculating comprehensive molecular properties
including ADMET descriptors, drug-likeness assessment, and quantum descriptors.
"""

from typing import Dict, Any, List, Optional, Union
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, Descriptors, rdPartialCharges, AllChem
from rdkit.Chem.GraphDescriptors import BalabanJ, BertzCT, Chi0, Chi0n, Chi0v, Chi1

from ..models.base import BaseCalculator, CalculationConfig
from ..models.models import MoleculeData, PropertyData
from ..models.exceptions import ComputationError, ValidationError


class AdvancedPropertiesCalculator(BaseCalculator[PropertyData]):
    """
    Calculator for advanced molecular properties.
    
    Computes comprehensive molecular descriptors including ADMET properties,
    drug-likeness assessment, lipophilicity profiles, and quantum descriptors.
    """
    
    @property
    def calculator_name(self) -> str:
        """Return the name of this calculator."""
        return "AdvancedPropertiesCalculator"
    
    @property
    def supported_properties(self) -> List[str]:
        """Return list of properties this calculator can compute."""
        return [
            # Lipophilicity descriptors
            "LogP_Crippen", "MolMR", "BalabanJ", "BertzCT", 
            "Chi0", "Chi0n", "Chi0v", "Chi1",
            # ADMET descriptors
            "TPSA", "LabuteASA", "HBD", "HBA", "RotatableBonds",
            "FractionCsp3", "BioavailabilityScore", "CNS_Score",
            # Drug-likeness rules
            "lipinski_violations", "veber_violations", "ghose_violations",
            "drug_like", "quality_score", "qed_score",
            # Functional groups
            "functional_groups",
            # Quantum descriptors (approximate)
            "partial_charges", "dipole_moment", "homo_lumo_gap"
        ]
    
    def _calculate_properties(self, molecule: MoleculeData) -> PropertyData:
        """
        Calculate advanced molecular properties using RDKit.
        
        Args:
            molecule: Validated molecule data
            
        Returns:
            PropertyData object with calculated advanced properties
            
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
            
            # Calculate all advanced properties
            properties = {}
            
            # Lipophilicity profile
            try:
                lipophilicity = self._calculate_lipophilicity_profile(mol)
                properties.update(lipophilicity)
            except Exception as e:
                raise ComputationError(
                    "Failed to calculate lipophilicity profile",
                    computation_type="lipophilicity_profile",
                    smiles=molecule.smiles
                ) from e
            
            # ADMET descriptors
            try:
                admet = self._calculate_admet_descriptors(mol)
                properties.update(admet)
            except Exception as e:
                raise ComputationError(
                    "Failed to calculate ADMET descriptors",
                    computation_type="admet_descriptors", 
                    smiles=molecule.smiles
                ) from e
            
            # Drug-likeness assessment
            try:
                drug_likeness = self._assess_drug_likeness_rules(mol)
                properties.update(drug_likeness)
            except Exception as e:
                raise ComputationError(
                    "Failed to assess drug-likeness",
                    computation_type="drug_likeness_assessment",
                    smiles=molecule.smiles
                ) from e
            
            # QED score (with fallback if not available)
            try:
                # Try modern RDKit first
                if hasattr(rdMolDescriptors, 'CalcQED'):
                    properties["qed_score"] = round(rdMolDescriptors.CalcQED(mol), 3)
                else:
                    # Fallback: simplified QED estimation based on drug-likeness rules
                    properties["qed_score"] = self._estimate_qed_score(mol)
            except Exception as e:
                # If all fails, provide a simple estimation
                properties["qed_score"] = self._estimate_qed_score(mol)
            
            # Functional group analysis
            try:
                functional_groups = self._functional_group_analysis(mol)
                properties["functional_groups"] = functional_groups
            except Exception as e:
                raise ComputationError(
                    "Failed to analyze functional groups",
                    computation_type="functional_group_analysis",
                    smiles=molecule.smiles
                ) from e
            
            # Quantum descriptors (if enabled in config)
            if self.config.include_quantum_descriptors:
                try:
                    quantum = self._calculate_quantum_descriptors(mol)
                    properties.update(quantum)
                except Exception as e:
                    # Quantum calculations are optional, log but don't fail
                    properties["quantum_descriptors_warning"] = str(e)
            
            # Create PropertyData object
            property_data = PropertyData(
                properties=properties,
                calculation_method=self.calculator_name,
                metadata={
                    'rdkit_version': Chem.rdBase.rdkitVersion,
                    'smiles_input': molecule.smiles,
                    'explicit_hydrogens': True,
                    'precision': self.config.precision,
                    'quantum_descriptors_included': self.config.include_quantum_descriptors,
                    'property_categories': [
                        'lipophilicity', 'admet', 'drug_likeness', 
                        'functional_groups', 'qed_score'
                    ]
                }
            )
            
            return property_data
            
        except (ValidationError, ComputationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Handle unexpected errors
            raise ComputationError(
                f"Unexpected error in advanced properties calculation: {str(e)}",
                computation_type="advanced_properties",
                smiles=molecule.smiles
            ) from e
    
    def _calculate_lipophilicity_profile(self, mol: Chem.Mol) -> Dict[str, float]:
        """Calculate comprehensive lipophilicity descriptors."""
        return {
            'LogP_Crippen': round(Descriptors.MolLogP(mol), 3),
            'MolMR': round(Descriptors.MolMR(mol), 3),
            'BalabanJ': round(BalabanJ(mol), 3),
            'BertzCT': round(BertzCT(mol), 3),
            'Chi0': round(Chi0(mol), 3),
            'Chi0n': round(Chi0n(mol), 3),
            'Chi0v': round(Chi0v(mol), 3),
            'Chi1': round(Chi1(mol), 3),
        }
    
    def _calculate_admet_descriptors(self, mol: Chem.Mol) -> Dict[str, Any]:
        """Calculate ADMET-related molecular descriptors."""
        mw = rdMolDescriptors.CalcExactMolWt(mol)
        tpsa = rdMolDescriptors.CalcTPSA(mol)
        hbd = rdMolDescriptors.CalcNumHBD(mol)
        hba = rdMolDescriptors.CalcNumHBA(mol)
        rotatable_bonds = rdMolDescriptors.CalcNumRotatableBonds(mol)
        
        # Bioavailability score (5-parameter rule)
        bioavailability_score = 0
        if mw <= 500: bioavailability_score += 1
        if hbd <= 5: bioavailability_score += 1
        if hba <= 10: bioavailability_score += 1
        if 20 <= tpsa <= 140: bioavailability_score += 1
        if rotatable_bonds <= 10: bioavailability_score += 1
        
        # CNS penetration score
        cns_score = 0
        if tpsa <= 90: cns_score += 1
        if mw <= 450: cns_score += 1
        if hbd <= 3: cns_score += 1
        if hba <= 7: cns_score += 1
        
        return {
            'TPSA': round(tpsa, 2),
            'LabuteASA': round(rdMolDescriptors.CalcLabuteASA(mol), 2),
            'HBD': hbd,
            'HBA': hba,
            'RotatableBonds': rotatable_bonds,
            'RingCount': rdMolDescriptors.CalcNumRings(mol),
            'AromaticRings': rdMolDescriptors.CalcNumAromaticRings(mol),
            'FractionCsp3': round(rdMolDescriptors.CalcFractionCSP3(mol), 3),
            'MolecularWeight': round(mw, 2),
            'HeavyAtomCount': mol.GetNumHeavyAtoms(),
            'BioavailabilityScore': bioavailability_score,
            'CNS_Score': cns_score
        }
    
    def _assess_drug_likeness_rules(self, mol: Chem.Mol) -> Dict[str, Any]:
        """Assess drug-likeness using multiple rule sets."""
        mw = rdMolDescriptors.CalcExactMolWt(mol)
        logp = Descriptors.MolLogP(mol)
        hbd = rdMolDescriptors.CalcNumHBD(mol)
        hba = rdMolDescriptors.CalcNumHBA(mol)
        tpsa = rdMolDescriptors.CalcTPSA(mol)
        rotatable_bonds = rdMolDescriptors.CalcNumRotatableBonds(mol)
        
        # Lipinski's Rule of Five
        lipinski_violations = 0
        if mw > 500: lipinski_violations += 1
        if logp > 5: lipinski_violations += 1
        if hbd > 5: lipinski_violations += 1
        if hba > 10: lipinski_violations += 1
        
        # Veber's Rule
        veber_violations = 0
        if tpsa > 140: veber_violations += 1
        if rotatable_bonds > 10: veber_violations += 1
        
        # Ghose Filter
        ghose_violations = 0
        if not (160 <= mw <= 480): ghose_violations += 1
        if not (-0.4 <= logp <= 5.6): ghose_violations += 1
        if not (20 <= Descriptors.MolMR(mol) <= 130): ghose_violations += 1
        atom_count = mol.GetNumAtoms()
        if not (20 <= atom_count <= 70): ghose_violations += 1
        
        # Overall assessment
        total_rules_passed = 0
        if lipinski_violations <= 1: total_rules_passed += 1
        if veber_violations == 0: total_rules_passed += 1
        if ghose_violations <= 1: total_rules_passed += 1
        
        return {
            'lipinski_violations': lipinski_violations,
            'lipinski_compliant': lipinski_violations <= 1,
            'veber_violations': veber_violations,
            'veber_compliant': veber_violations == 0,
            'ghose_violations': ghose_violations,
            'ghose_compliant': ghose_violations <= 1,
            'drug_like': total_rules_passed >= 2,
            'rules_passed': total_rules_passed,
            'quality_score': round((total_rules_passed / 3) * 100, 1)
        }
    
    def _functional_group_analysis(self, mol: Chem.Mol) -> Dict[str, int]:
        """Analyze functional groups in the molecule."""
        functional_groups = {
            'carboxylic_acid': '[CX3](=O)[OX1H0-,OX2H1]',
            'ester': '[CX3](=O)[OX2H0]',
            'ether': '[OD2]([#6])[#6]',
            'alcohol': '[OX2H]',
            'phenol': '[OX2H][cX3]:[c]',
            'ketone': '[CX3]=[OX1]',
            'aldehyde': '[CX3H1](=O)[#6]',
            'amide': '[CX3](=[OX1])[NX3]',
            'amine_primary': '[NX3;H2;!$(NC=[!#6]);!$(NC#[!#6])][#6]',
            'amine_secondary': '[NX3;H1;!$(NC=[!#6]);!$(NC#[!#6])]([#6])[#6]',
            'amine_tertiary': '[NX3;H0;!$(NC=[!#6]);!$(NC#[!#6])]([#6])([#6])[#6]',
            'aromatic_amine': '[nX3]',
            'halogen': '[F,Cl,Br,I]',
            'benzene_ring': 'c1ccccc1'
        }
        
        group_counts = {}
        for group_name, smarts in functional_groups.items():
            pattern = Chem.MolFromSmarts(smarts)
            if pattern:
                matches = mol.GetSubstructMatches(pattern)
                group_counts[f'count_{group_name}'] = len(matches)
        
        return group_counts
    
    def _calculate_quantum_descriptors(self, mol: Chem.Mol) -> Dict[str, Any]:
        """Calculate quantum chemical descriptors (approximate)."""
        descriptors = {}
        
        # Partial charges
        partial_charges = self._calculate_partial_charges(mol)
        if partial_charges:
            descriptors.update(partial_charges)
        
        # Dipole moment
        dipole_moment = self._calculate_dipole_moment(mol)
        if dipole_moment:
            descriptors.update(dipole_moment)
        
        # HOMO-LUMO gap estimation
        homo_lumo = self._estimate_homo_lumo_gap(mol)
        if homo_lumo:
            descriptors.update(homo_lumo)
        
        return descriptors
    
    def _calculate_partial_charges(self, mol: Chem.Mol) -> Dict[str, Any]:
        """Calculate partial charges for atoms in the molecule."""
        try:
            # Make a copy to avoid modifying the original
            mol_copy = Chem.Mol(mol)
            
            # Calculate Gasteiger charges
            rdPartialCharges.ComputeGasteigerCharges(mol_copy)
            
            charges = []
            for atom in mol_copy.GetAtoms():
                charge = atom.GetDoubleProp('_GasteigerCharge')
                if np.isnan(charge) or np.isinf(charge):
                    charge = 0.0
                charges.append(charge)
            
            if not charges:
                return {}
                
            return {
                'total_charge': round(sum(charges), 3),
                'max_positive_charge': round(max(charges), 3) if charges else 0.0,
                'max_negative_charge': round(min(charges), 3) if charges else 0.0,
                'charge_spread': round(max(charges) - min(charges), 3) if charges else 0.0,
                'mean_absolute_charge': round(np.mean(np.abs(charges)), 3) if charges else 0.0,
                'charge_variance': round(np.var(charges), 3) if charges else 0.0
            }
        except Exception:
            return {}
    
    def _calculate_dipole_moment(self, mol: Chem.Mol) -> Dict[str, float]:
        """Calculate molecular dipole moment components."""
        try:
            # Ensure 3D coordinates are available
            mol_copy = Chem.Mol(mol)
            if mol_copy.GetNumConformers() == 0:
                AllChem.EmbedMolecule(mol_copy, randomSeed=42)
                AllChem.UFFOptimizeMolecule(mol_copy)
            
            # Calculate partial charges
            rdPartialCharges.ComputeGasteigerCharges(mol_copy)
            
            # Get atomic positions and charges
            conformer = mol_copy.GetConformer()
            dipole_x, dipole_y, dipole_z = 0.0, 0.0, 0.0
            
            for atom in mol_copy.GetAtoms():
                charge = atom.GetDoubleProp('_GasteigerCharge')
                if np.isnan(charge) or np.isinf(charge):
                    charge = 0.0
                
                pos = conformer.GetAtomPosition(atom.GetIdx())
                dipole_x += charge * pos.x
                dipole_y += charge * pos.y
                dipole_z += charge * pos.z
            
            # Calculate total dipole moment
            dipole_magnitude = np.sqrt(dipole_x**2 + dipole_y**2 + dipole_z**2)
            
            return {
                'dipole_x': round(dipole_x, 3),
                'dipole_y': round(dipole_y, 3),
                'dipole_z': round(dipole_z, 3),
                'dipole_magnitude': round(dipole_magnitude, 3),
                'dipole_moment_debye': round(dipole_magnitude * 4.803, 3)  # Convert to Debye units
            }
        except Exception:
            return {}
    
    def _estimate_homo_lumo_gap(self, mol: Chem.Mol) -> Dict[str, float]:
        """Estimate HOMO-LUMO gap using simple approximations."""
        try:
            # This is a simplified estimation based on molecular properties
            # For accurate HOMO-LUMO calculations, quantum chemistry software is needed
            
            num_aromatic_rings = rdMolDescriptors.CalcNumAromaticRings(mol)
            
            # Simple empirical estimation (not accurate for real calculations)
            if num_aromatic_rings > 0:
                # Aromatic systems typically have smaller gaps
                estimated_gap = max(2.0 - (num_aromatic_rings * 0.5), 0.5)
            else:
                # Saturated systems have larger gaps
                estimated_gap = 6.0
            
            # Adjust based on heteroatoms
            heteroatoms = mol.GetNumHeavyAtoms() - sum(1 for atom in mol.GetAtoms() if atom.GetSymbol() == 'C')
            if heteroatoms > 0:
                estimated_gap += heteroatoms * 0.2
            
            return {
                'estimated_homo_lumo_gap_eV': round(estimated_gap, 2),
                'estimated_homo_eV': round(-5.0 - (estimated_gap / 2), 2),  # Rough estimate
                'estimated_lumo_eV': round(-5.0 + (estimated_gap / 2), 2),  # Rough estimate
                'num_aromatic_rings': num_aromatic_rings,
                'homo_lumo_warning': 'Rough approximations - use quantum chemistry software for accurate values'
            }
        except Exception:
            return {}
    
    def _estimate_qed_score(self, mol: Chem.Mol) -> float:
        """
        Estimate QED score based on drug-likeness rules when CalcQED is not available.
        
        This is a simplified approximation based on Lipinski, Veber, and other rules.
        """
        try:
            # Get basic descriptors
            mw = rdMolDescriptors.CalcExactMolWt(mol)
            logp = Descriptors.MolLogP(mol)
            hbd = rdMolDescriptors.CalcNumHBD(mol)
            hba = rdMolDescriptors.CalcNumHBA(mol)
            tpsa = rdMolDescriptors.CalcTPSA(mol)
            rotatable_bonds = rdMolDescriptors.CalcNumRotatableBonds(mol)
            
            # Simple scoring based on drug-likeness criteria
            score = 1.0
            
            # Molecular weight penalty
            if mw > 500:
                score *= 0.5
            elif mw > 400:
                score *= 0.8
            
            # LogP penalty
            if logp > 5:
                score *= 0.5
            elif logp < -1:
                score *= 0.7
            elif logp > 3:
                score *= 0.9
            
            # Hydrogen bonding penalty
            if hbd > 5:
                score *= 0.6
            if hba > 10:
                score *= 0.6
            
            # TPSA penalty
            if tpsa > 140:
                score *= 0.7
            elif tpsa < 20:
                score *= 0.8
            
            # Rotatable bonds penalty
            if rotatable_bonds > 10:
                score *= 0.7
            
            # Ring penalty (too few or too many rings)
            num_rings = rdMolDescriptors.CalcNumRings(mol)
            if num_rings == 0:
                score *= 0.8  # No rings might be less drug-like
            elif num_rings > 4:
                score *= 0.7  # Too many rings
            
            return round(max(min(score, 1.0), 0.0), 3)
            
        except Exception:
            return 0.5  # Default neutral score


class LipophilicityCalculator(BaseCalculator[PropertyData]):
    """
    Specialized calculator for lipophilicity descriptors.
    
    Focuses specifically on lipophilicity-related molecular descriptors
    for solubility and permeability predictions.
    """
    
    @property
    def calculator_name(self) -> str:
        """Return the name of this calculator."""
        return "LipophilicityCalculator"
    
    @property
    def supported_properties(self) -> List[str]:
        """Return list of properties this calculator can compute."""
        return [
            "LogP_Crippen", "MolMR", "BalabanJ", "BertzCT",
            "Chi0", "Chi0n", "Chi0v", "Chi1"
        ]
    
    def _calculate_properties(self, molecule: MoleculeData) -> PropertyData:
        """
        Calculate lipophilicity properties using RDKit.
        
        Args:
            molecule: Validated molecule data
            
        Returns:
            PropertyData object with calculated lipophilicity properties
            
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
            
            # Calculate lipophilicity descriptors
            try:
                properties = {
                    'LogP_Crippen': round(Descriptors.MolLogP(mol), 3),
                    'MolMR': round(Descriptors.MolMR(mol), 3),
                    'BalabanJ': round(BalabanJ(mol), 3),
                    'BertzCT': round(BertzCT(mol), 3),
                    'Chi0': round(Chi0(mol), 3),
                    'Chi0n': round(Chi0n(mol), 3),
                    'Chi0v': round(Chi0v(mol), 3),
                    'Chi1': round(Chi1(mol), 3),
                }
            except Exception as e:
                raise ComputationError(
                    "Failed to calculate lipophilicity descriptors",
                    computation_type="lipophilicity_descriptors",
                    smiles=molecule.smiles
                ) from e
            
            # Create PropertyData object
            property_data = PropertyData(
                properties=properties,
                calculation_method=self.calculator_name,
                metadata={
                    'rdkit_version': Chem.rdBase.rdkitVersion,
                    'smiles_input': molecule.smiles,
                    'precision': self.config.precision,
                    'descriptor_types': ['connectivity', 'topological', 'electronic'],
                    'interpretation': {
                        'LogP_Crippen': 'Partition coefficient (octanol/water)',
                        'MolMR': 'Molecular refractivity',
                        'BalabanJ': 'Balaban J index (connectivity)',
                        'BertzCT': 'Bertz CT complexity index',
                        'Chi0-Chi1': 'Connectivity indices'
                    }
                }
            )
            
            return property_data
            
        except (ValidationError, ComputationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Handle unexpected errors
            raise ComputationError(
                f"Unexpected error in lipophilicity calculation: {str(e)}",
                computation_type="lipophilicity_properties",
                smiles=molecule.smiles
            ) from e


# Property assessment functions that work with PropertyData objects

def assess_comprehensive_drug_likeness(property_data: PropertyData) -> Dict[str, Any]:
    """
    Comprehensive drug-likeness assessment based on calculated properties.
    
    Args:
        property_data: PropertyData object with calculated properties
        
    Returns:
        Dictionary with comprehensive drug-likeness assessment and recommendations
    """
    properties = property_data.properties
    
    assessment = {
        "overall_score": 0.0,
        "category": "Unknown",
        "rule_assessments": {},
        "recommendations": [],
        "warnings": [],
        "strengths": []
    }
    
    score = 0.0
    
    # Lipinski Rule assessment
    if "lipinski_violations" in properties:
        violations = properties["lipinski_violations"]
        if violations == 0:
            assessment["rule_assessments"]["lipinski"] = "Excellent"
            score += 30
            assessment["strengths"].append("Excellent Lipinski compliance")
        elif violations == 1:
            assessment["rule_assessments"]["lipinski"] = "Good"
            score += 20
            assessment["strengths"].append("Good Lipinski compliance")
        else:
            assessment["rule_assessments"]["lipinski"] = "Poor"
            assessment["warnings"].append("Multiple Lipinski violations")
            assessment["recommendations"].append("Reduce molecular weight, LogP, or hydrogen bonding")
    
    # Veber Rule assessment
    if "veber_violations" in properties:
        violations = properties["veber_violations"]
        if violations == 0:
            assessment["rule_assessments"]["veber"] = "Excellent"
            score += 20
            assessment["strengths"].append("Excellent Veber compliance")
        else:
            assessment["rule_assessments"]["veber"] = "Poor"
            assessment["warnings"].append("Veber rule violations")
            assessment["recommendations"].append("Reduce TPSA or rotatable bonds")
    
    # QED Score assessment
    if "qed_score" in properties:
        qed = properties["qed_score"]
        if qed > 0.7:
            assessment["rule_assessments"]["qed"] = "Excellent"
            score += 25
            assessment["strengths"].append(f"High QED score ({qed:.3f})")
        elif qed > 0.5:
            assessment["rule_assessments"]["qed"] = "Good"
            score += 15
        elif qed > 0.3:
            assessment["rule_assessments"]["qed"] = "Moderate"
            score += 10
        else:
            assessment["rule_assessments"]["qed"] = "Poor"
            assessment["warnings"].append(f"Low QED score ({qed:.3f})")
            assessment["recommendations"].append("Consider structural modifications for better drug-likeness")
    
    # Bioavailability assessment
    if "BioavailabilityScore" in properties:
        bioavail = properties["BioavailabilityScore"]
        if bioavail >= 4:
            assessment["rule_assessments"]["bioavailability"] = "Excellent"
            score += 15
            assessment["strengths"].append("High bioavailability potential")
        elif bioavail >= 3:
            assessment["rule_assessments"]["bioavailability"] = "Good"
            score += 10
        else:
            assessment["rule_assessments"]["bioavailability"] = "Poor"
            assessment["warnings"].append("Low bioavailability potential")
            assessment["recommendations"].append("Optimize ADMET properties")
    
    # CNS penetration assessment
    if "CNS_Score" in properties:
        cns = properties["CNS_Score"]
        if cns >= 3:
            assessment["rule_assessments"]["cns_penetration"] = "High"
            assessment["strengths"].append("Good CNS penetration potential")
        elif cns >= 2:
            assessment["rule_assessments"]["cns_penetration"] = "Moderate"
        else:
            assessment["rule_assessments"]["cns_penetration"] = "Low"
    
    # Overall score and category
    assessment["overall_score"] = min(score, 100.0)
    
    if score >= 80:
        assessment["category"] = "Excellent drug-like properties"
    elif score >= 60:
        assessment["category"] = "Good drug-like properties"
    elif score >= 40:
        assessment["category"] = "Moderate drug-like properties"
    elif score >= 20:
        assessment["category"] = "Poor drug-like properties"
    else:
        assessment["category"] = "Very poor drug-like properties"
    
    # Add general recommendations if none specific
    if not assessment["recommendations"] and score < 60:
        assessment["recommendations"].append("Consider lead optimization to improve drug-likeness")
        assessment["recommendations"].append("Focus on reducing molecular complexity while maintaining activity")
    
    return assessment


# Property categories for organization (compatible with legacy code)
LIPOPHILICITY_DESCRIPTORS = [
    'LogP_Crippen', 'MolMR', 'BalabanJ', 'BertzCT', 'Chi0', 'Chi0n', 'Chi0v', 'Chi1'
]

ADMET_DESCRIPTORS = [
    'TPSA', 'LabuteASA', 'HBD', 'HBA', 'RotatableBonds', 'RingCount',
    'AromaticRings', 'FractionCsp3', 'BioavailabilityScore', 'CNS_Score'
]

DRUG_LIKENESS_RULES = ['lipinski', 'veber', 'ghose']

QUANTUM_DESCRIPTORS = [
    'total_charge', 'dipole_magnitude', 'estimated_homo_lumo_gap_eV'
]


# Legacy compatibility functions that wrap the OOP calculators

def calculate_lipophilicity_profile(mol: Chem.Mol) -> Dict[str, float]:
    """
    Legacy compatibility function for lipophilicity calculation.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Dictionary with lipophilicity descriptors (legacy format)
    """
    if mol is None:
        return {}
    
    try:
        # Convert RDKit mol to SMILES for our OOP system
        smiles = Chem.MolToSmiles(mol)
        molecule_data = MoleculeData(smiles=smiles)
        
        # Use OOP calculator
        calculator = LipophilicityCalculator()
        result = calculator.calculate(molecule_data)
        
        return result.properties
        
    except Exception as e:
        return {"error": str(e)}


def calculate_admet_descriptors(mol: Chem.Mol) -> Dict[str, Any]:
    """
    Legacy compatibility function for ADMET descriptors calculation.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Dictionary with ADMET descriptors (legacy format)
    """
    if mol is None:
        return {}
    
    try:
        # Convert RDKit mol to SMILES for our OOP system
        smiles = Chem.MolToSmiles(mol)
        molecule_data = MoleculeData(smiles=smiles)
        
        # Use OOP calculator
        calculator = AdvancedPropertiesCalculator()
        result = calculator.calculate(molecule_data)
        
        # Extract only ADMET descriptors
        admet_props = {}
        for prop in ADMET_DESCRIPTORS:
            if prop in result.properties:
                admet_props[prop] = result.properties[prop]
        
        return admet_props
        
    except Exception as e:
        return {"error": str(e)}


def assess_drug_likeness_rules(mol: Chem.Mol) -> Dict[str, Any]:
    """
    Legacy compatibility function for drug-likeness rules assessment.
    
    Args:
        mol: RDKit molecule object
        
    Returns:
        Dictionary with drug-likeness assessment (legacy format)
    """
    if mol is None:
        return {}
    
    try:
        # Convert RDKit mol to SMILES for our OOP system
        smiles = Chem.MolToSmiles(mol)
        molecule_data = MoleculeData(smiles=smiles)
        
        # Use OOP calculator
        calculator = AdvancedPropertiesCalculator()
        result = calculator.calculate(molecule_data)
        
        # Extract drug-likeness related properties
        drug_like_props = {}
        for key, value in result.properties.items():
            if any(rule in key for rule in DRUG_LIKENESS_RULES) or key in ['drug_like', 'quality_score']:
                drug_like_props[key] = value
        
        return drug_like_props
        
    except Exception as e:
        return {"error": str(e)}


def comprehensive_property_analysis(mol: Chem.Mol, smiles: str) -> Dict[str, Any]:
    """
    Legacy compatibility function for comprehensive analysis.
    
    Args:
        mol: RDKit molecule object
        smiles: SMILES string
        
    Returns:
        Dictionary with comprehensive analysis (legacy format)
    """
    if mol is None:
        return {}
    
    try:
        # Convert to our OOP system
        molecule_data = MoleculeData(smiles=smiles)
        
        # Use OOP calculator
        calculator = AdvancedPropertiesCalculator()
        result = calculator.calculate(molecule_data)
        
        # Format as legacy structure
        analysis = {
            'smiles': smiles,
            'basic_descriptors': {
                'molecular_weight': result.properties.get('MolecularWeight', 0),
                'num_atoms': mol.GetNumAtoms(),
                'num_heavy_atoms': result.properties.get('HeavyAtomCount', 0),
                'num_rings': result.properties.get('RingCount', 0),
                'molecular_formula': rdMolDescriptors.CalcMolFormula(mol)
            },
            'lipophilicity': {k: v for k, v in result.properties.items() if k in LIPOPHILICITY_DESCRIPTORS},
            'admet': {k: v for k, v in result.properties.items() if k in ADMET_DESCRIPTORS},
            'drug_likeness': {k: v for k, v in result.properties.items() 
                             if any(rule in k for rule in DRUG_LIKENESS_RULES) or k in ['drug_like', 'quality_score']},
            'functional_groups': result.properties.get('functional_groups', {}),
            'qed_score': result.properties.get('qed_score', 0.0)
        }
        
        # Overall assessment
        drug_like = analysis['drug_likeness'].get('drug_like', False)
        qed = analysis['qed_score']
        bioavail_score = analysis['admet'].get('BioavailabilityScore', 0)
        
        if drug_like and qed > 0.5 and bioavail_score >= 4:
            overall_assessment = "Excellent"
        elif drug_like and qed > 0.3:
            overall_assessment = "Good"
        elif qed > 0.2:
            overall_assessment = "Moderate"
        else:
            overall_assessment = "Poor"
        
        analysis['overall_assessment'] = overall_assessment
        
        return analysis
        
    except Exception as e:
        return {'error': str(e)}