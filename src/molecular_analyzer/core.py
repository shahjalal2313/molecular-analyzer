"""
Core molecular operations module.

This module provides basic molecular manipulation functions including
SMILES validation, molecule creation, and basic property access.
"""

from typing import Optional, Dict, Any
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors


def create_molecule_from_smiles(smiles: str) -> Optional[Chem.Mol]:
    """
    Create an RDKit molecule object from SMILES string.

    Args:
        smiles (str): SMILES string representation of the molecule

    Returns:
        Optional[Chem.Mol]: RDKit molecule object or None if invalid

    Example:
        >>> mol = create_molecule_from_smiles("CCO")
        >>> mol is not None
        True
    """
    if not smiles or not isinstance(smiles, str):
        return None

    smiles = smiles.strip()
    if not smiles:
        return None

    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            mol = Chem.AddHs(mol)  # Add explicit hydrogens
        return mol
    except Exception:
        return None


def validate_smiles(smiles: str) -> bool:
    """
    Validate if a SMILES string is chemically valid.

    Args:
        smiles (str): SMILES string to validate

    Returns:
        bool: True if valid, False otherwise

    Example:
        >>> validate_smiles("CCO")
        True
        >>> validate_smiles("XYZ")
        False
    """
    mol = create_molecule_from_smiles(smiles)
    return mol is not None


def get_basic_info(mol: Chem.Mol) -> Dict[str, Any]:
    """
    Get basic information about a molecule.

    Args:
        mol (Chem.Mol): RDKit molecule object

    Returns:
        Dict[str, Any]: Dictionary with basic molecular information

    Example:
        >>> mol = create_molecule_from_smiles("CCO")
        >>> info = get_basic_info(mol)
        >>> info["num_atoms"] > 0
        True
    """
    if mol is None:
        return {}

    try:
        return {
            "smiles": Chem.MolToSmiles(mol),
            "formula": rdMolDescriptors.CalcMolFormula(mol),
            "num_atoms": mol.GetNumAtoms(),
            "num_bonds": mol.GetNumBonds(),
            "num_heavy_atoms": mol.GetNumHeavyAtoms()
        }
    except Exception:
        return {}


def smiles_to_formula(smiles: str) -> Optional[str]:
    """
    Convert SMILES string directly to molecular formula.

    Args:
        smiles (str): SMILES string

    Returns:
        Optional[str]: Molecular formula or None if invalid

    Example:
        >>> smiles_to_formula("CCO")
        'C2H6O'
    """
    mol = create_molecule_from_smiles(smiles)
    if mol:
        try:
            return rdMolDescriptors.CalcMolFormula(mol)
        except Exception:
            return None
    return None


# Module constants
COMMON_MOLECULES = {
    "water": "O",
    "methane": "C", 
    "ethanol": "CCO",
    "benzene": "c1ccccc1",
    "aspirin": "CC(=O)OC1=CC=CC=C1C(=O)O"
}


if __name__ == "__main__":
    # Test the module
    print("Testing core module...")

    for name, smiles in COMMON_MOLECULES.items():
        is_valid = validate_smiles(smiles)
        print(f"{name}: {smiles} - Valid: {is_valid}")

        if is_valid:
            mol = create_molecule_from_smiles(smiles)
            info = get_basic_info(mol)
            print(f"  Formula: {info.get('formula', 'N/A')}")
            print(f"  Atoms: {info.get('num_atoms', 'N/A')}")
