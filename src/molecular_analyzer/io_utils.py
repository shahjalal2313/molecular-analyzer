"""
Input/Output utilities for molecular data.

This module provides functions for reading and writing molecular data
in various formats including CSV, SDF, and text files.
"""

from typing import List, Dict, Any, Tuple
import pandas as pd
import os
from pathlib import Path
from rdkit import Chem
from .core import create_molecule_from_smiles, validate_smiles
from .properties import calculate_all_properties


def read_smiles_file(filename: str, has_header: bool = True) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Read SMILES from a text file.

    Args:
        filename (str): Path to the file
        has_header (bool): Whether file has header line

    Returns:
        Tuple[List[Dict[str, Any]], List[str]]: (molecules_data, errors)
    """
    molecules = []
    errors = []

    try:
        with open(filename, 'r') as f:
            lines = f.readlines()

        start_idx = 1 if has_header else 0

        for i, line in enumerate(lines[start_idx:], start_idx + 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split('\t') if '\t' in line else line.split(',')

            if len(parts) >= 2:
                name, smiles = parts[0].strip(), parts[1].strip()
            else:
                name, smiles = f"molecule_{i}", parts[0].strip()

            if validate_smiles(smiles):
                molecules.append({"name": name, "smiles": smiles})
            else:
                errors.append(f"Line {i}: Invalid SMILES '{smiles}' for {name}")

    except FileNotFoundError:
        errors.append(f"File not found: {filename}")
    except Exception as e:
        errors.append(f"Error reading file: {str(e)}")

    return molecules, errors


def write_molecules_csv(molecules: List[Dict[str, Any]], filename: str, 
                       calculate_props: bool = True) -> bool:
    """
    Write molecules to CSV file with optional property calculation.

    Args:
        molecules (List[Dict[str, Any]]): List of molecule data
        filename (str): Output filename
        calculate_props (bool): Whether to calculate additional properties

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if calculate_props:
            # Add calculated properties
            for mol_data in molecules:
                if "smiles" in mol_data:
                    mol = create_molecule_from_smiles(mol_data["smiles"])
                    if mol:
                        props = calculate_all_properties(mol)
                        mol_data.update(props)

        df = pd.DataFrame(molecules)
        df.to_csv(filename, index=False)
        return True

    except Exception as e:
        print(f"Error writing CSV: {str(e)}")
        return False


def read_csv_molecules(filename: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Read molecules from CSV file.

    Args:
        filename (str): Path to CSV file

    Returns:
        Tuple[List[Dict[str, Any]], List[str]]: (molecules_data, errors)
    """
    molecules = []
    errors = []

    try:
        df = pd.read_csv(filename)

        if 'smiles' not in df.columns:
            errors.append("CSV must contain 'smiles' column")
            return molecules, errors

        for idx, row in df.iterrows():
            mol_data = row.to_dict()

            # Validate SMILES if present
            if pd.notna(mol_data.get('smiles')):
                if validate_smiles(str(mol_data['smiles'])):
                    molecules.append(mol_data)
                else:
                    errors.append(f"Row {idx + 2}: Invalid SMILES '{mol_data['smiles']}'")
            else:
                errors.append(f"Row {idx + 2}: Missing SMILES")

    except FileNotFoundError:
        errors.append(f"File not found: {filename}")
    except Exception as e:
        errors.append(f"Error reading CSV: {str(e)}")

    return molecules, errors


def create_sdf_file(molecules: List[Dict[str, Any]], filename: str) -> bool:
    """
    Create SDF file from molecules data.

    Args:
        molecules (List[Dict[str, Any]]): List of molecule data
        filename (str): Output SDF filename

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        writer = Chem.SDWriter(filename)

        for mol_data in molecules:
            if "smiles" in mol_data:
                mol = create_molecule_from_smiles(mol_data["smiles"])
                if mol:
                    # Set molecule name
                    if "name" in mol_data:
                        mol.SetProp("_Name", str(mol_data["name"]))

                    # Add other properties
                    for key, value in mol_data.items():
                        if key not in ["smiles", "name"] and pd.notna(value):
                            mol.SetProp(key, str(value))

                    writer.write(mol)

        writer.close()
        return True

    except Exception as e:
        print(f"Error creating SDF: {str(e)}")
        return False


def read_sdf_file(filename: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Read molecules from SDF file.

    Args:
        filename (str): Path to SDF file

    Returns:
        Tuple[List[Dict[str, Any]], List[str]]: (molecules_data, errors)
    """
    molecules = []
    errors = []

    try:
        suppl = Chem.SDMolSupplier(filename)

        for i, mol in enumerate(suppl):
            if mol is not None:
                mol_data = {
                    "smiles": Chem.MolToSmiles(mol),
                    "name": mol.GetProp("_Name") if mol.HasProp("_Name") else f"molecule_{i+1}"
                }

                # Add other properties
                for prop_name in mol.GetPropNames():
                    if prop_name != "_Name":
                        mol_data[prop_name] = mol.GetProp(prop_name)

                molecules.append(mol_data)
            else:
                errors.append(f"Failed to read molecule {i+1} from SDF")

    except FileNotFoundError:
        errors.append(f"File not found: {filename}")
    except Exception as e:
        errors.append(f"Error reading SDF: {str(e)}")

    return molecules, errors


def batch_process_files(file_list: List[str], output_dir: str = "output") -> Dict[str, Any]:
    """
    Process multiple molecular files and combine results.

    Args:
        file_list (List[str]): List of file paths to process
        output_dir (str): Directory for output files

    Returns:
        Dict[str, Any]: Processing summary
    """
    os.makedirs(output_dir, exist_ok=True)

    all_molecules = []
    processing_summary = {
        "files_processed": 0,
        "total_molecules": 0,
        "errors": []
    }

    for file_path in file_list:
        if not os.path.exists(file_path):
            processing_summary["errors"].append(f"File not found: {file_path}")
            continue

        file_ext = Path(file_path).suffix.lower()

        try:
            if file_ext == '.csv':
                molecules, errors = read_csv_molecules(file_path)
            elif file_ext == '.sdf':
                molecules, errors = read_sdf_file(file_path)
            else:
                molecules, errors = read_smiles_file(file_path)

            all_molecules.extend(molecules)
            processing_summary["files_processed"] += 1
            processing_summary["errors"].extend(errors)

        except Exception as e:
            processing_summary["errors"].append(f"Error processing {file_path}: {str(e)}")

    processing_summary["total_molecules"] = len(all_molecules)

    # Save combined results
    if all_molecules:
        output_file = os.path.join(output_dir, "combined_molecules.csv")
        success = write_molecules_csv(all_molecules, output_file)
        processing_summary["output_file"] = output_file if success else None

    return processing_summary


# Supported file formats
SUPPORTED_FORMATS = {
    '.csv': 'Comma-separated values',
    '.tsv': 'Tab-separated values', 
    '.txt': 'Text file with SMILES',
    '.smi': 'SMILES file',
    '.sdf': 'Structure Data Format'
}


if __name__ == "__main__":
    # Test the module
    print("Testing I/O utilities...")

    # Create test data
    test_molecules = [
        {"name": "ethanol", "smiles": "CCO"},
        {"name": "benzene", "smiles": "c1ccccc1"}
    ]

    # Test CSV writing
    success = write_molecules_csv(test_molecules, "test_output.csv")
    print(f"CSV write test: {'Success' if success else 'Failed'}")

    # Test CSV reading
    if success:
        molecules, errors = read_csv_molecules("test_output.csv")
        print(f"CSV read test: {len(molecules)} molecules, {len(errors)} errors")
