"""
Advanced Molecular Properties Module

This module provides comprehensive advanced property calculations including
ADMET properties, drug-likeness assessment, pharmaceutical profiling,
and quantum chemical descriptors.
"""

from typing import Dict, Any, Optional, List
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, Descriptors, rdPartialCharges
from rdkit.Chem.GraphDescriptors import BalabanJ, BertzCT, Chi0, Chi0n, Chi0v, Chi1
from rdkit.Chem import rdForceFieldHelpers, AllChem


def calculate_lipophilicity_profile(mol: Chem.Mol) -> Dict[str, float]:
    """Calculate comprehensive lipophilicity descriptors."""
    if mol is None:
        return {}

    try:
        return {
            'LogP_Crippen': Descriptors.MolLogP(mol),
            'MolMR': Descriptors.MolMR(mol),
            'BalabanJ': BalabanJ(mol),
            'BertzCT': BertzCT(mol),
            'Chi0': Chi0(mol),
            'Chi0n': Chi0n(mol),
            'Chi0v': Chi0v(mol),
            'Chi1': Chi1(mol),
        }
    except Exception:
        return {}


def calculate_admet_descriptors(mol: Chem.Mol) -> Dict[str, Any]:
    """Calculate ADMET-related molecular descriptors."""
    if mol is None:
        return {}

    try:
        mw = rdMolDescriptors.CalcExactMolWt(mol)
        tpsa = rdMolDescriptors.CalcTPSA(mol)
        hbd = rdMolDescriptors.CalcNumHBD(mol)
        hba = rdMolDescriptors.CalcNumHBA(mol)
        rotatable_bonds = rdMolDescriptors.CalcNumRotatableBonds(mol)

        # Bioavailability score
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
            'TPSA': tpsa,
            'LabuteASA': rdMolDescriptors.CalcLabuteASA(mol),
            'HBD': hbd,
            'HBA': hba,
            'RotatableBonds': rotatable_bonds,
            'RingCount': rdMolDescriptors.CalcNumRings(mol),
            'AromaticRings': rdMolDescriptors.CalcNumAromaticRings(mol),
            'FractionCsp3': rdMolDescriptors.CalcFractionCSP3(mol),
            'MolecularWeight': mw,
            'HeavyAtomCount': mol.GetNumHeavyAtoms(),
            'BioavailabilityScore': bioavailability_score,
            'CNS_Score': cns_score
        }
    except Exception:
        return {}


def assess_drug_likeness_rules(mol: Chem.Mol) -> Dict[str, Any]:
    """Assess drug-likeness using multiple rule sets."""
    if mol is None:
        return {}

    try:
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
            'quality_score': (total_rules_passed / 3) * 100
        }
    except Exception:
        return {}


def calculate_qed_score(mol: Chem.Mol) -> float:
    """Calculate Quantitative Estimate of Drug-likeness (QED)."""
    if mol is None:
        return 0.0

    try:
        # Try modern RDKit first
        if hasattr(rdMolDescriptors, 'CalcQED'):
            return rdMolDescriptors.CalcQED(mol)
        else:
            # Fallback: simplified QED estimation
            return _estimate_qed_score_legacy(mol)
    except Exception:
        return _estimate_qed_score_legacy(mol)


def _estimate_qed_score_legacy(mol: Chem.Mol) -> float:
    """Estimate QED score for legacy compatibility."""
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
        
        # Ring penalty
        num_rings = rdMolDescriptors.CalcNumRings(mol)
        if num_rings == 0:
            score *= 0.8
        elif num_rings > 4:
            score *= 0.7
        
        return round(max(min(score, 1.0), 0.0), 3)
        
    except Exception:
        return 0.5


def functional_group_analysis(mol: Chem.Mol) -> Dict[str, int]:
    """Analyze functional groups in the molecule."""
    if mol is None:
        return {}

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

    try:
        group_counts = {}
        for group_name, smarts in functional_groups.items():
            pattern = Chem.MolFromSmarts(smarts)
            if pattern:
                matches = mol.GetSubstructMatches(pattern)
                group_counts[f'count_{group_name}'] = len(matches)
        return group_counts
    except Exception:
        return {}


def calculate_partial_charges(mol: Chem.Mol) -> Dict[str, Any]:
    """Calculate partial charges for atoms in the molecule."""
    if mol is None:
        return {}
    
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
            'partial_charges': charges,
            'total_charge': sum(charges),
            'max_positive_charge': max(charges) if charges else 0.0,
            'max_negative_charge': min(charges) if charges else 0.0,
            'charge_spread': max(charges) - min(charges) if charges else 0.0,
            'mean_absolute_charge': np.mean(np.abs(charges)) if charges else 0.0,
            'charge_variance': np.var(charges) if charges else 0.0
        }
    except Exception:
        return {}


def calculate_dipole_moment(mol: Chem.Mol) -> Dict[str, float]:
    """Calculate molecular dipole moment components."""
    if mol is None:
        return {}
    
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
            'dipole_x': dipole_x,
            'dipole_y': dipole_y,
            'dipole_z': dipole_z,
            'dipole_magnitude': dipole_magnitude,
            'dipole_moment_debye': dipole_magnitude * 4.803  # Convert to Debye units
        }
    except Exception:
        return {}


def estimate_homo_lumo_gap(mol: Chem.Mol) -> Dict[str, float]:
    """Estimate HOMO-LUMO gap using simple approximations."""
    if mol is None:
        return {}
    
    try:
        # This is a simplified estimation based on molecular properties
        # For accurate HOMO-LUMO calculations, quantum chemistry software is needed
        
        # Calculate some basic descriptors that correlate with HOMO-LUMO gap
        num_pi_electrons = 0
        num_aromatic_rings = rdMolDescriptors.CalcNumAromaticRings(mol)
        num_conjugated_bonds = 0
        
        # Count π electrons in aromatic systems
        for ring in mol.GetRingInfo().AtomRings():
            if len(ring) == 6:  # Assume benzene-like rings
                num_pi_electrons += 6
        
        # Simple empirical estimation (not accurate for real calculations)
        # These are rough approximations based on typical organic molecules
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
            'estimated_homo_lumo_gap_eV': estimated_gap,
            'estimated_homo_eV': -5.0 - (estimated_gap / 2),  # Rough estimate
            'estimated_lumo_eV': -5.0 + (estimated_gap / 2),  # Rough estimate
            'num_pi_electrons': num_pi_electrons,
            'num_aromatic_rings': num_aromatic_rings,
            'warning': 'These are rough approximations. Use quantum chemistry software for accurate values.'
        }
    except Exception:
        return {}


def calculate_quantum_descriptors(mol: Chem.Mol) -> Dict[str, Any]:
    """Calculate quantum chemical descriptors and electronic properties."""
    if mol is None:
        return {}
    
    try:
        descriptors = {}
        
        # Partial charges
        charges = calculate_partial_charges(mol)
        if charges:
            descriptors['partial_charges'] = charges
        
        # Dipole moment
        dipole = calculate_dipole_moment(mol)
        if dipole:
            descriptors['dipole_moment'] = dipole
        
        # HOMO-LUMO gap estimation
        homo_lumo = estimate_homo_lumo_gap(mol)
        if homo_lumo:
            descriptors['homo_lumo'] = homo_lumo
        
        # Additional electronic descriptors
        descriptors['electronic_properties'] = {
            'num_valence_electrons': sum(atom.GetTotalValence() for atom in mol.GetAtoms()),
            'num_radical_electrons': sum(atom.GetNumRadicalElectrons() for atom in mol.GetAtoms()),
            'formal_charge': sum(atom.GetFormalCharge() for atom in mol.GetAtoms()),
            'num_heteroatoms': sum(1 for atom in mol.GetAtoms() if atom.GetSymbol() != 'C'),
            'aromaticity_index': rdMolDescriptors.CalcNumAromaticRings(mol) / max(rdMolDescriptors.CalcNumRings(mol), 1)
        }
        
        return descriptors
    except Exception:
        return {}


def generate_optimization_recommendations(analysis: Dict[str, Any]) -> List[str]:
    """Generate optimization recommendations based on analysis results."""
    recommendations = []
    
    try:
        # Drug-likeness recommendations
        if 'drug_likeness' in analysis:
            drug_like = analysis['drug_likeness']
            
            if drug_like.get('lipinski_violations', 0) > 1:
                recommendations.append("🔴 **Lipinski violations**: Consider reducing molecular weight, LogP, or hydrogen bond donors/acceptors")
            
            if drug_like.get('veber_violations', 0) > 0:
                recommendations.append("🟡 **Veber violations**: Reduce TPSA below 140 Ų or rotatable bonds below 10")
            
            if drug_like.get('ghose_violations', 0) > 1:
                recommendations.append("🟡 **Ghose violations**: Optimize molecular weight (160-480), LogP (-0.4 to 5.6), or molar refractivity")
        
        # ADMET recommendations
        if 'admet' in analysis:
            admet = analysis['admet']
            
            bioavail_score = admet.get('BioavailabilityScore', 0)
            if bioavail_score < 4:
                recommendations.append("🔴 **Poor bioavailability**: Optimize TPSA, molecular weight, and flexibility")
            
            cns_score = admet.get('CNS_Score', 0)
            if cns_score < 2:
                recommendations.append("🟡 **Limited CNS penetration**: For CNS drugs, reduce TPSA and molecular weight")
            
            if admet.get('TPSA', 0) > 140:
                recommendations.append("🟡 **High TPSA**: Reduce polar surface area for better permeability")
            
            if admet.get('FractionCsp3', 0) < 0.25:
                recommendations.append("🟡 **Low Fsp3**: Add sp3 carbons to reduce flatness and improve drug-likeness")
        
        # QED recommendations
        qed_score = analysis.get('qed_score', 0)
        if qed_score < 0.3:
            recommendations.append("🔴 **Low QED score**: Consider major structural modifications for drug-likeness")
        elif qed_score < 0.5:
            recommendations.append("🟡 **Moderate QED score**: Fine-tune molecular properties for better drug-likeness")
        
        # Overall assessment recommendations
        overall = analysis.get('overall_assessment', '')
        if overall == 'Poor':
            recommendations.append("🔴 **Overall assessment poor**: Consider significant structural modifications or scaffold hopping")
        elif overall == 'Moderate':
            recommendations.append("🟡 **Moderate potential**: Focus on optimizing key ADMET properties")
        
        # Quantum descriptor recommendations
        if 'quantum_descriptors' in analysis:
            quantum = analysis['quantum_descriptors']
            
            if 'dipole_moment' in quantum:
                dipole = quantum['dipole_moment'].get('dipole_moment_debye', 0)
                if dipole > 5.0:
                    recommendations.append("🟡 **High dipole moment**: May affect membrane permeability")
            
            if 'partial_charges' in quantum:
                charges = quantum['partial_charges']
                if charges.get('charge_spread', 0) > 2.0:
                    recommendations.append("🟡 **High charge polarization**: May affect selectivity and binding")
        
        # If no specific issues, provide positive feedback
        if not recommendations:
            recommendations.append("✅ **Excellent properties**: This molecule shows good drug-like characteristics")
            recommendations.append("💡 **Suggestion**: Consider additional ADMET testing and synthetic accessibility")
        
        return recommendations
        
    except Exception:
        return ["⚠️ Unable to generate recommendations due to incomplete analysis"]


def comprehensive_property_analysis(mol: Chem.Mol, smiles: str) -> Dict[str, Any]:
    """Perform comprehensive advanced property analysis."""
    if mol is None:
        return {}

    try:
        analysis = {
            'smiles': smiles,
            'basic_descriptors': {
                'molecular_weight': rdMolDescriptors.CalcExactMolWt(mol),
                'num_atoms': mol.GetNumAtoms(),
                'num_heavy_atoms': mol.GetNumHeavyAtoms(),
                'num_rings': rdMolDescriptors.CalcNumRings(mol),
                'molecular_formula': rdMolDescriptors.CalcMolFormula(mol)
            }
        }

        # Add all property categories
        analysis['lipophilicity'] = calculate_lipophilicity_profile(mol)
        analysis['admet'] = calculate_admet_descriptors(mol)
        analysis['drug_likeness'] = assess_drug_likeness_rules(mol)
        analysis['functional_groups'] = functional_group_analysis(mol)
        analysis['qed_score'] = calculate_qed_score(mol)
        analysis['quantum_descriptors'] = calculate_quantum_descriptors(mol)

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


# Property categories for organization
LIPOPHILICITY_DESCRIPTORS = [
    'LogP_Crippen', 'MolMR', 'BalabanJ', 'BertzCT', 'Chi0', 'Chi0n', 'Chi0v', 'Chi1'
]

ADMET_DESCRIPTORS = [
    'TPSA', 'LabuteASA', 'HBD', 'HBA', 'RotatableBonds', 'RingCount',
    'AromaticRings', 'FractionCsp3', 'BioavailabilityScore', 'CNS_Score'
]

DRUG_LIKENESS_RULES = ['lipinski', 'veber', 'ghose', 'muegge', 'egan']

if __name__ == "__main__":
    # Test the module
    from rdkit import Chem

    test_smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"  # Aspirin
    mol = Chem.MolFromSmiles(test_smiles)

    if mol:
        mol = Chem.AddHs(mol)  # Add explicit hydrogens
        analysis = comprehensive_property_analysis(mol, test_smiles)
        print("Advanced Properties Analysis:")
        print(f"Overall Assessment: {analysis.get('overall_assessment', 'Unknown')}")
        print(f"QED Score: {analysis.get('qed_score', 0):.3f}")
        print(f"Drug-like: {analysis.get('drug_likeness', {}).get('drug_like', False)}")
