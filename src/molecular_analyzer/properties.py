"""
Molecular properties calculation module.

This module provides functions for calculating various molecular descriptors
and properties including molecular weight, drug-likeness, and structural features.
"""

from typing import Dict, Any
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, Descriptors


def calculate_basic_properties(mol: Chem.Mol) -> Dict[str, Any]:
    """
    Calculate basic molecular properties.

    Args:
        mol (Chem.Mol): RDKit molecule object

    Returns:
        Dict[str, Any]: Dictionary with basic properties
    """
    if mol is None:
        return {}

    try:
        # Calculate molecular formula
        formula = rdMolDescriptors.CalcMolFormula(mol)
        
        return {
            "molecular_weight": round(rdMolDescriptors.CalcExactMolWt(mol), 2),
            "formula": formula,
            "num_atoms": mol.GetNumAtoms(),
            "num_bonds": mol.GetNumBonds(),
            "num_heavy_atoms": mol.GetNumHeavyAtoms(),
            "num_rings": rdMolDescriptors.CalcNumRings(mol),
            "num_aromatic_rings": rdMolDescriptors.CalcNumAromaticRings(mol),
            "num_rotatable_bonds": rdMolDescriptors.CalcNumRotatableBonds(mol)
        }
    except Exception as e:
        return {"error": str(e)}


def calculate_drug_like_properties(mol: Chem.Mol) -> Dict[str, Any]:
    """
    Calculate drug-likeness properties (Lipinski's Rule of Five).

    Args:
        mol (Chem.Mol): RDKit molecule object

    Returns:
        Dict[str, Any]: Dictionary with drug-like properties
    """
    if mol is None:
        return {}

    try:
        mw = rdMolDescriptors.CalcExactMolWt(mol)
        logp = Descriptors.MolLogP(mol)
        hbd = rdMolDescriptors.CalcNumHBD(mol)
        hba = rdMolDescriptors.CalcNumHBA(mol)
        tpsa = rdMolDescriptors.CalcTPSA(mol)

        # Count Lipinski violations
        violations = 0
        if mw > 500: violations += 1
        if logp > 5: violations += 1
        if hbd > 5: violations += 1
        if hba > 10: violations += 1

        return {
            "molecular_weight": round(mw, 2),
            "logP": round(logp, 2),
            "hbd": hbd,
            "hba": hba,
            "tpsa": round(tpsa, 2),
            "lipinski_violations": violations,
            "drug_like": violations <= 1
        }
    except Exception as e:
        return {"error": str(e)}


def calculate_all_properties(mol: Chem.Mol) -> Dict[str, Any]:
    """
    Calculate comprehensive molecular properties.

    Args:
        mol (Chem.Mol): RDKit molecule object

    Returns:
        Dict[str, Any]: Dictionary with all calculated properties
    """
    if mol is None:
        return {}

    basic_props = calculate_basic_properties(mol)
    drug_props = calculate_drug_like_properties(mol)

    # Combine dictionaries
    all_props = {**basic_props, **drug_props}

    # Add derived properties
    if "num_atoms" in all_props and "molecular_weight" in all_props:
        if all_props["num_atoms"] > 0:
            all_props["average_atomic_weight"] = round(
                all_props["molecular_weight"] / all_props["num_atoms"], 2
            )

    return all_props


def assess_drug_likeness(properties: Dict[str, Any]) -> Dict[str, str]:
    """
    Assess drug-likeness based on calculated properties.

    Args:
        properties (Dict[str, Any]): Properties dictionary

    Returns:
        Dict[str, str]: Assessment with recommendations
    """
    assessment = {
        "overall": "Unknown",
        "molecular_weight": "Unknown",
        "lipophilicity": "Unknown", 
        "hydrogen_bonding": "Unknown",
        "recommendations": []
    }

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


# Property categories for organization
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


if __name__ == "__main__":
    # Test the module
    from rdkit import Chem

    test_smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"  # Aspirin
    mol = Chem.MolFromSmiles(test_smiles)

    if mol:
        mol = Chem.AddHs(mol)  # Add explicit hydrogens
        props = calculate_all_properties(mol)
        assessment = assess_drug_likeness(props)

        print("Molecular Properties:")
        for key, value in props.items():
            print(f"  {key}: {value}")

        print("\nDrug-likeness Assessment:")
        print(f"  Overall: {assessment['overall']}")
        if assessment["recommendations"]:
            print("  Recommendations:")
            for rec in assessment["recommendations"]:
                print(f"    - {rec}")
