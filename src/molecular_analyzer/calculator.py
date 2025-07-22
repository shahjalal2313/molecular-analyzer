"""
Molecular Analyzer Calculator Module

This module provides the main MolecularAnalyzer class that serves as the primary
interface for molecular analysis operations. It combines functionality from
all other modules to provide a unified API for molecular property calculations.
"""

from typing import Dict, Any, List, Optional, Union
import pandas as pd
from rdkit import Chem

from .core import create_molecule_from_smiles, validate_smiles, get_basic_info
from .properties import calculate_all_properties, assess_drug_likeness
from .advanced_properties import comprehensive_property_analysis
from .conformational import perform_conformational_analysis
from .io_utils import read_smiles_file, write_molecules_csv


class MolecularAnalyzer:
    """
    Main molecular analysis class providing comprehensive molecular property calculations.
    
    This class serves as the primary interface for all molecular analysis operations,
    combining functionality from multiple modules to provide a unified API.
    
    Attributes:
        enable_advanced (bool): Whether to include advanced properties by default
        enable_quantum (bool): Whether to include quantum descriptors by default
        enable_conformational (bool): Whether to include conformational analysis by default
        
    Examples:
        >>> analyzer = MolecularAnalyzer()
        >>> results = analyzer.calculate_properties("CCO")
        >>> print(results['molecular_weight'])
        46.07
        
        >>> # Batch analysis
        >>> smiles_list = ["CCO", "CCC", "CCCC"]
        >>> batch_results = analyzer.batch_analyze(smiles_list)
        >>> len(batch_results)
        3
    """
    
    def __init__(self, enable_advanced: bool = True, enable_quantum: bool = False, 
                 enable_conformational: bool = False):
        """
        Initialize the MolecularAnalyzer.
        
        Args:
            enable_advanced (bool): Enable advanced properties calculation by default
            enable_quantum (bool): Enable quantum descriptors calculation by default
            enable_conformational (bool): Enable conformational analysis by default
        """
        self.enable_advanced = enable_advanced
        self.enable_quantum = enable_quantum
        self.enable_conformational = enable_conformational
        
    def validate_input(self, smiles: str) -> tuple[bool, str]:
        """
        Validate a SMILES string input.
        
        Args:
            smiles (str): SMILES string to validate
            
        Returns:
            tuple[bool, str]: (is_valid, error_message)
            
        Examples:
            >>> analyzer = MolecularAnalyzer()
            >>> valid, error = analyzer.validate_input("CCO")
            >>> valid
            True
            >>> valid, error = analyzer.validate_input("invalid")
            >>> valid
            False
        """
        if not smiles or not isinstance(smiles, str):
            return False, "SMILES must be a non-empty string"
        
        smiles = smiles.strip()
        if not smiles:
            return False, "SMILES string cannot be empty"
        
        if not validate_smiles(smiles):
            return False, "Invalid SMILES structure"
        
        return True, ""
    
    def calculate_properties(self, smiles: str, include_advanced: Optional[bool] = None,
                           include_quantum: Optional[bool] = None,
                           include_conformational: Optional[bool] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive molecular properties for a single molecule.
        
        Args:
            smiles (str): SMILES string of the molecule
            include_advanced (bool, optional): Override default advanced properties setting
            include_quantum (bool, optional): Override default quantum descriptors setting
            include_conformational (bool, optional): Override default conformational setting
            
        Returns:
            Dict[str, Any]: Dictionary containing all calculated properties
            
        Raises:
            ValueError: If SMILES string is invalid
            
        Examples:
            >>> analyzer = MolecularAnalyzer()
            >>> props = analyzer.calculate_properties("CCO")
            >>> 'molecular_weight' in props
            True
            >>> 'drug_like' in props
            True
        """
        # Validate input
        is_valid, error_msg = self.validate_input(smiles)
        if not is_valid:
            raise ValueError(f"Invalid SMILES: {error_msg}")
        
        # Create molecule
        mol = create_molecule_from_smiles(smiles)
        if mol is None:
            raise ValueError("Failed to create molecule from SMILES")
        
        # Use override values or default settings
        use_advanced = include_advanced if include_advanced is not None else self.enable_advanced
        use_quantum = include_quantum if include_quantum is not None else self.enable_quantum
        use_conformational = include_conformational if include_conformational is not None else self.enable_conformational
        
        # Calculate basic properties
        results = calculate_all_properties(mol)
        results['smiles'] = smiles
        
        # Add assessment
        results['assessment'] = assess_drug_likeness(results)
        
        # Add advanced properties if enabled
        if use_advanced:
            try:
                advanced_results = comprehensive_property_analysis(mol, smiles)
                results['advanced_properties'] = advanced_results
            except Exception as e:
                results['advanced_properties_error'] = str(e)
        
        # Add quantum descriptors if enabled
        if use_quantum:
            try:
                from .advanced_properties import calculate_quantum_descriptors
                quantum_results = calculate_quantum_descriptors(mol)
                results['quantum_descriptors'] = quantum_results
            except Exception as e:
                results['quantum_descriptors_error'] = str(e)
        
        # Add conformational analysis if enabled
        if use_conformational:
            try:
                conf_results = perform_conformational_analysis(smiles)
                results['conformational_analysis'] = conf_results
            except Exception as e:
                results['conformational_analysis_error'] = str(e)
        
        return results
    
    def batch_analyze(self, smiles_list: List[str], 
                     include_advanced: Optional[bool] = None,
                     include_quantum: Optional[bool] = None,
                     include_conformational: Optional[bool] = None,
                     skip_invalid: bool = True) -> List[Dict[str, Any]]:
        """
        Perform batch analysis on multiple SMILES strings.
        
        Args:
            smiles_list (List[str]): List of SMILES strings to analyze
            include_advanced (bool, optional): Override default advanced properties setting
            include_quantum (bool, optional): Override default quantum descriptors setting
            include_conformational (bool, optional): Override default conformational setting
            skip_invalid (bool): Whether to skip invalid SMILES or raise errors
            
        Returns:
            List[Dict[str, Any]]: List of results for each molecule
            
        Examples:
            >>> analyzer = MolecularAnalyzer()
            >>> smiles_list = ["CCO", "CCC", "CCCC"]
            >>> results = analyzer.batch_analyze(smiles_list)
            >>> len(results)
            3
            >>> all('molecular_weight' in r for r in results)
            True
        """
        results = []
        
        for i, smiles in enumerate(smiles_list):
            try:
                result = self.calculate_properties(
                    smiles, 
                    include_advanced=include_advanced,
                    include_quantum=include_quantum,
                    include_conformational=include_conformational
                )
                result['batch_index'] = i
                results.append(result)
                
            except Exception as e:
                if skip_invalid:
                    error_result = {
                        'smiles': smiles,
                        'batch_index': i,
                        'error': str(e),
                        'valid': False
                    }
                    results.append(error_result)
                else:
                    raise ValueError(f"Error processing SMILES '{smiles}' at index {i}: {e}")
        
        return results
    
    def analyze_from_file(self, file_path: str, smiles_column: str = "smiles",
                         include_advanced: Optional[bool] = None,
                         include_quantum: Optional[bool] = None,
                         include_conformational: Optional[bool] = None) -> pd.DataFrame:
        """
        Analyze molecules from a file containing SMILES strings.
        
        Args:
            file_path (str): Path to the input file
            smiles_column (str): Name of the column containing SMILES strings
            include_advanced (bool, optional): Override default advanced properties setting
            include_quantum (bool, optional): Override default quantum descriptors setting
            include_conformational (bool, optional): Override default conformational setting
            
        Returns:
            pd.DataFrame: DataFrame with analysis results
            
        Raises:
            FileNotFoundError: If the input file doesn't exist
            ValueError: If the specified column doesn't exist
            
        Examples:
            >>> analyzer = MolecularAnalyzer()
            >>> df = analyzer.analyze_from_file("molecules.csv", "smiles")
            >>> 'molecular_weight' in df.columns
            True
        """
        try:
            # Read file based on extension
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.txt'):
                # Assume simple text file with SMILES
                molecules_data, errors = read_smiles_file(file_path)
                smiles_list = [mol['smiles'] for mol in molecules_data]
                df = pd.DataFrame({smiles_column: smiles_list})
            else:
                raise ValueError("Unsupported file format. Use .csv or .txt files.")
            
            # Check if column exists
            if smiles_column not in df.columns:
                raise ValueError(f"Column '{smiles_column}' not found in file")
            
            # Perform batch analysis
            smiles_list = df[smiles_column].tolist()
            results = self.batch_analyze(
                smiles_list,
                include_advanced=include_advanced,
                include_quantum=include_quantum,
                include_conformational=include_conformational
            )
            
            # Convert results to DataFrame
            results_df = pd.DataFrame(results)
            
            # Merge with original DataFrame
            final_df = pd.concat([df, results_df], axis=1)
            
            return final_df
            
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except Exception as e:
            raise ValueError(f"Error processing file: {e}")
    
    def compare_molecules(self, molecules: Dict[str, str]) -> pd.DataFrame:
        """
        Compare properties of multiple molecules.
        
        Args:
            molecules (Dict[str, str]): Dictionary mapping molecule names to SMILES
            
        Returns:
            pd.DataFrame: Comparison results as a DataFrame
            
        Examples:
            >>> analyzer = MolecularAnalyzer()
            >>> molecules = {"ethanol": "CCO", "methanol": "CO"}
            >>> comparison = analyzer.compare_molecules(molecules)
            >>> len(comparison)
            2
        """
        results = []
        
        for name, smiles in molecules.items():
            try:
                props = self.calculate_properties(smiles)
                props['name'] = name
                results.append(props)
            except Exception as e:
                error_result = {
                    'name': name,
                    'smiles': smiles,
                    'error': str(e),
                    'valid': False
                }
                results.append(error_result)
        
        return pd.DataFrame(results)
    
    def get_summary_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate summary statistics for batch analysis results.
        
        Args:
            results (List[Dict[str, Any]]): Results from batch analysis
            
        Returns:
            Dict[str, Any]: Summary statistics
            
        Examples:
            >>> analyzer = MolecularAnalyzer()
            >>> results = analyzer.batch_analyze(["CCO", "CCC", "CCCC"])
            >>> stats = analyzer.get_summary_statistics(results)
            >>> 'total_molecules' in stats
            True
        """
        if not results:
            return {}
        
        # Filter valid results
        valid_results = [r for r in results if r.get('valid', True) and 'error' not in r]
        
        if not valid_results:
            return {
                'total_molecules': len(results),
                'valid_molecules': 0,
                'invalid_molecules': len(results),
                'success_rate': 0.0
            }
        
        # Extract numeric properties
        numeric_props = ['molecular_weight', 'logP', 'tpsa', 'hbd', 'hba', 'num_atoms']
        stats = {
            'total_molecules': len(results),
            'valid_molecules': len(valid_results),
            'invalid_molecules': len(results) - len(valid_results),
            'success_rate': len(valid_results) / len(results) * 100
        }
        
        # Calculate statistics for each numeric property
        for prop in numeric_props:
            values = [r.get(prop) for r in valid_results if prop in r and r[prop] is not None]
            if values:
                stats[f'{prop}_mean'] = sum(values) / len(values)
                stats[f'{prop}_min'] = min(values)
                stats[f'{prop}_max'] = max(values)
                stats[f'{prop}_std'] = (sum((x - stats[f'{prop}_mean'])**2 for x in values) / len(values))**0.5
        
        # Drug-likeness statistics
        drug_like_count = sum(1 for r in valid_results if r.get('drug_like', False))
        stats['drug_like_percentage'] = drug_like_count / len(valid_results) * 100 if valid_results else 0
        
        return stats
    
    def export_results(self, results: Union[List[Dict[str, Any]], pd.DataFrame], 
                      output_path: str, format: str = 'csv') -> None:
        """
        Export analysis results to a file.
        
        Args:
            results: Results to export (list of dicts or DataFrame)
            output_path (str): Path for the output file
            format (str): Output format ('csv', 'json', 'excel')
            
        Raises:
            ValueError: If format is not supported
            
        Examples:
            >>> analyzer = MolecularAnalyzer()
            >>> results = analyzer.batch_analyze(["CCO", "CCC"])
            >>> analyzer.export_results(results, "output.csv")
        """
        if isinstance(results, list):
            df = pd.DataFrame(results)
        else:
            df = results
        
        if format.lower() == 'csv':
            df.to_csv(output_path, index=False)
        elif format.lower() == 'json':
            df.to_json(output_path, orient='records', indent=2)
        elif format.lower() == 'excel':
            df.to_excel(output_path, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'csv', 'json', or 'excel'")
    
    def get_analyzer_info(self) -> Dict[str, Any]:
        """
        Get information about the analyzer configuration.
        
        Returns:
            Dict[str, Any]: Analyzer configuration information
            
        Examples:
            >>> analyzer = MolecularAnalyzer()
            >>> info = analyzer.get_analyzer_info()
            >>> 'enable_advanced' in info
            True
        """
        return {
            'enable_advanced': self.enable_advanced,
            'enable_quantum': self.enable_quantum,
            'enable_conformational': self.enable_conformational,
            'version': '1.0.0',
            'supported_formats': ['csv', 'txt', 'json', 'excel'],
            'available_properties': [
                'molecular_weight', 'logP', 'tpsa', 'hbd', 'hba', 
                'num_atoms', 'num_bonds', 'drug_like', 'lipinski_violations'
            ]
        }


# Convenience function for quick analysis
def analyze_molecule(smiles: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function for quick molecule analysis.
    
    Args:
        smiles (str): SMILES string to analyze
        **kwargs: Additional arguments passed to MolecularAnalyzer
        
    Returns:
        Dict[str, Any]: Analysis results
        
    Examples:
        >>> result = analyze_molecule("CCO")
        >>> 'molecular_weight' in result
        True
    """
    analyzer = MolecularAnalyzer()
    return analyzer.calculate_properties(smiles, **kwargs)


if __name__ == "__main__":
    # Example usage and testing
    print("Testing MolecularAnalyzer...")
    
    # Initialize analyzer
    analyzer = MolecularAnalyzer(enable_advanced=True)
    
    # Test single molecule analysis
    test_smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"  # Aspirin
    try:
        result = analyzer.calculate_properties(test_smiles)
        print(f"✓ Single molecule analysis successful")
        print(f"  Molecular weight: {result.get('molecular_weight', 'N/A')}")
        print(f"  Drug-like: {result.get('drug_like', 'N/A')}")
    except Exception as e:
        print(f"✗ Single molecule analysis failed: {e}")
    
    # Test batch analysis
    test_molecules = ["CCO", "CCC", "CCCC", "invalid_smiles"]
    try:
        batch_results = analyzer.batch_analyze(test_molecules)
        print(f"✓ Batch analysis successful ({len(batch_results)} molecules)")
        
        # Test summary statistics
        stats = analyzer.get_summary_statistics(batch_results)
        print(f"  Success rate: {stats.get('success_rate', 0):.1f}%")
        print(f"  Average MW: {stats.get('molecular_weight_mean', 0):.2f}")
    except Exception as e:
        print(f"✗ Batch analysis failed: {e}")
    
    # Test comparison
    molecules = {
        "Ethanol": "CCO",
        "Methanol": "CO",
        "Propanol": "CCCO"
    }
    try:
        comparison = analyzer.compare_molecules(molecules)
        print(f"✓ Molecular comparison successful ({len(comparison)} molecules)")
    except Exception as e:
        print(f"✗ Molecular comparison failed: {e}")
    
    print("MolecularAnalyzer testing complete!")