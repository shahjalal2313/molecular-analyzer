"""
Conformational analysis calculator implementation.

Provides OOP interface for conformational analysis including conformer generation,
energy calculations, and structural diversity analysis using RDKit.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolAlign, rdMolDescriptors

from ..models.base import BaseCalculator, CalculationConfig
from ..models.models import MoleculeData, PropertyData
from ..models.exceptions import ComputationError, ValidationError


class ConformationalCalculator(BaseCalculator[PropertyData]):
    """
    Calculator for conformational analysis and 3D structure generation.
    
    Generates multiple conformers, calculates energies, and analyzes structural
    diversity using RDKit's conformer generation and force field optimization.
    """
    
    def __init__(self, config: Optional[CalculationConfig] = None):
        """
        Initialize conformational calculator.
        
        Args:
            config: Optional calculation configuration
        """
        super().__init__(config)
        self.force_field: str = "UFF"  # Default force field
        self.max_conformers: int = 20
        self.energy_window: float = 10.0  # kcal/mol
        self.rmsd_threshold: float = 0.5  # Angstrom
        
    @property
    def calculator_name(self) -> str:
        """Return the name of this calculator."""
        return "ConformationalCalculator"
    
    @property
    def supported_properties(self) -> List[str]:
        """Return list of properties this calculator can compute."""
        return [
            "num_conformers",
            "lowest_energy_conformer_id",
            "lowest_energy",
            "energy_range",
            "mean_energy",
            "energy_std",
            "conformers_within_1kcal",
            "conformers_within_2kcal", 
            "conformers_within_3kcal",
            "mean_rmsd",
            "max_rmsd",
            "min_rmsd",
            "rmsd_std",
            "flexibility_index",
            "rotatable_bonds",
            "conformational_complexity",
            "flexibility_category"
        ]
    
    def _calculate_properties(self, molecule: MoleculeData) -> PropertyData:
        """
        Perform conformational analysis on the molecule.
        
        Args:
            molecule: Validated molecule data
            
        Returns:
            PropertyData object with conformational analysis results
            
        Raises:
            ComputationError: If conformer generation fails
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
            
            # Generate conformers
            mol_with_conformers = self._generate_conformers(mol)
            if mol_with_conformers is None:
                raise ComputationError(
                    "Failed to generate conformers",
                    calculation_step="conformer_generation",
                    input_data={"smiles": molecule.smiles}
                )
            
            # Perform conformational analysis
            analysis_results = self._analyze_conformational_diversity(mol_with_conformers)
            
            # Convert to PropertyData format
            all_properties = {
                # Basic properties
                "molecular_weight": rdMolDescriptors.CalcExactMolWt(mol),
                "formula": rdMolDescriptors.CalcMolFormula(mol),
                "num_atoms": mol.GetNumAtoms(),
                "num_bonds": mol.GetNumBonds(),
                "num_rings": rdMolDescriptors.CalcNumRings(mol),
                **analysis_results
            }
            
            properties = PropertyData(
                properties=all_properties,
                calculation_method="ConformationalCalculator"
            )
            
            return properties
            
        except ValidationError:
            raise
        except ComputationError:
            raise
        except Exception as e:
            raise ComputationError(
                f"Unexpected error in conformational analysis: {str(e)}",
                calculation_step="conformational_analysis",
                input_data={"smiles": molecule.smiles}
            )
    
    def _generate_conformers(self, mol: Chem.Mol) -> Optional[Chem.Mol]:
        """
        Generate multiple conformers for a molecule.
        
        Args:
            mol: RDKit molecule object
            
        Returns:
            Molecule with conformers or None if failed
        """
        try:
            # Add hydrogens
            mol = Chem.AddHs(mol)
            
            # Generate conformers
            conformer_ids = AllChem.EmbedMultipleConfs(
                mol,
                numConfs=self.max_conformers,
                randomSeed=42,
                pruneRmsThresh=self.rmsd_threshold,
                useExpTorsionAnglePrefs=True,
                useBasicKnowledge=True
            )
            
            if not conformer_ids:
                return None
            
            # Optimize conformers
            if self.force_field == 'UFF':
                for conf_id in conformer_ids:
                    try:
                        AllChem.UFFOptimizeMolecule(mol, confId=conf_id)
                    except:
                        continue  # Skip failed optimizations
            elif self.force_field == 'MMFF':
                for conf_id in conformer_ids:
                    try:
                        AllChem.MMFFOptimizeMolecule(mol, confId=conf_id)
                    except:
                        continue  # Skip failed optimizations
            
            return mol
            
        except Exception:
            return None
    
    def _calculate_conformer_energies(self, mol: Chem.Mol) -> List[float]:
        """
        Calculate energies for all conformers.
        
        Args:
            mol: Molecule with conformers
            
        Returns:
            List of conformer energies
        """
        energies = []
        
        try:
            if self.force_field == 'UFF':
                for conf_id in range(mol.GetNumConformers()):
                    try:
                        ff = AllChem.UFFGetMoleculeForceField(mol, confId=conf_id)
                        if ff:
                            energy = ff.CalcEnergy()
                            energies.append(energy)
                        else:
                            energies.append(float('inf'))
                    except:
                        energies.append(float('inf'))
            elif self.force_field == 'MMFF':
                for conf_id in range(mol.GetNumConformers()):
                    try:
                        ff = AllChem.MMFFGetMoleculeForceField(mol, confId=conf_id)
                        if ff:
                            energy = ff.CalcEnergy()
                            energies.append(energy)
                        else:
                            energies.append(float('inf'))
                    except:
                        energies.append(float('inf'))
                        
        except Exception:
            energies = [float('inf')] * mol.GetNumConformers()
            
        return energies
    
    def _calculate_rmsd_matrix(self, mol: Chem.Mol) -> np.ndarray:
        """
        Calculate RMSD matrix between all conformers.
        
        Args:
            mol: Molecule with conformers
            
        Returns:
            RMSD matrix
        """
        num_conformers = mol.GetNumConformers()
        rmsd_matrix = np.zeros((num_conformers, num_conformers))
        
        try:
            for i in range(num_conformers):
                for j in range(i + 1, num_conformers):
                    try:
                        rmsd = rdMolAlign.GetBestRMS(mol, mol, i, j)
                        rmsd_matrix[i, j] = rmsd
                        rmsd_matrix[j, i] = rmsd
                    except:
                        rmsd_matrix[i, j] = 0.0
                        rmsd_matrix[j, i] = 0.0
                        
        except Exception:
            pass
            
        return rmsd_matrix
    
    def _analyze_conformational_diversity(self, mol: Chem.Mol) -> Dict[str, Any]:
        """
        Analyze conformational diversity of generated conformers.
        
        Args:
            mol: Molecule with conformers
            
        Returns:
            Dictionary with diversity analysis results
        """
        try:
            num_conformers = mol.GetNumConformers()
            
            if num_conformers < 1:
                raise ComputationError(
                    "No conformers generated for analysis",
                    calculation_step="conformer_generation"
                )
            
            # Calculate energies
            energies = self._calculate_conformer_energies(mol)
            
            # Calculate RMSD matrix if multiple conformers
            if num_conformers > 1:
                rmsd_matrix = self._calculate_rmsd_matrix(mol)
                rmsd_values = rmsd_matrix[np.triu_indices_from(rmsd_matrix, k=1)]
            else:
                rmsd_values = np.array([0.0])
            
            # Find lowest energy conformer
            if energies and not all(np.isinf(energies)):
                lowest_energy_idx = int(np.argmin(energies))
                lowest_energy = float(energies[lowest_energy_idx])
                
                # Calculate relative energies
                relative_energies = np.array(energies) - lowest_energy
                
                # Count conformers within energy windows
                conformers_1kcal = int(np.sum(relative_energies <= 1.0))
                conformers_2kcal = int(np.sum(relative_energies <= 2.0))
                conformers_3kcal = int(np.sum(relative_energies <= 3.0))
            else:
                lowest_energy_idx = 0
                lowest_energy = float('inf')
                relative_energies = np.array([float('inf')] * num_conformers)
                conformers_1kcal = 0
                conformers_2kcal = 0
                conformers_3kcal = 0
            
            # Calculate rotatable bonds
            rotatable_bonds = rdMolDescriptors.CalcNumRotatableBonds(mol)
            
            # Determine flexibility category
            if rotatable_bonds == 0:
                flexibility = 'rigid'
            elif rotatable_bonds <= 3:
                flexibility = 'low'
            elif rotatable_bonds <= 7:
                flexibility = 'moderate'
            else:
                flexibility = 'high'
            
            # Determine conformational complexity
            mean_rmsd = float(np.mean(rmsd_values)) if len(rmsd_values) > 0 else 0.0
            conformational_complexity = 'high' if mean_rmsd > 2.0 else 'low'
            
            return {
                'num_conformers': num_conformers,
                'lowest_energy_conformer_id': lowest_energy_idx,
                'lowest_energy': lowest_energy,
                'energy_range': float(np.max(energies) - np.min(energies)) if energies else 0.0,
                'mean_energy': float(np.mean(energies)) if energies else 0.0,
                'energy_std': float(np.std(energies)) if energies else 0.0,
                'conformers_within_1kcal': conformers_1kcal,
                'conformers_within_2kcal': conformers_2kcal,
                'conformers_within_3kcal': conformers_3kcal,
                'mean_rmsd': mean_rmsd,
                'max_rmsd': float(np.max(rmsd_values)) if len(rmsd_values) > 0 else 0.0,
                'min_rmsd': float(np.min(rmsd_values)) if len(rmsd_values) > 0 else 0.0,
                'rmsd_std': float(np.std(rmsd_values)) if len(rmsd_values) > 0 else 0.0,
                'flexibility_index': mean_rmsd,
                'rotatable_bonds': rotatable_bonds,
                'conformational_complexity': conformational_complexity,
                'flexibility_category': flexibility
            }
            
        except Exception as e:
            raise ComputationError(
                f"Failed to analyze conformational diversity: {str(e)}",
                calculation_step="diversity_analysis"
            )


# Legacy compatibility functions for backwards compatibility
def perform_conformational_analysis(smiles: str, num_conformers: int = 20) -> Dict[str, Any]:
    """
    Legacy function for conformational analysis.
    
    Args:
        smiles: SMILES string of the molecule
        num_conformers: Number of conformers to generate
        
    Returns:
        Dictionary with complete conformational analysis
    """
    try:
        # Create calculator with configuration
        config = CalculationConfig()
        calculator = ConformationalCalculator(config)
        calculator.max_conformers = num_conformers
        
        # Create molecule data
        molecule = MoleculeData(smiles=smiles)
        
        # Calculate properties
        properties = calculator.calculate(molecule)
        
        # Convert to legacy format
        props = properties.properties
        return {
            'smiles': smiles,
            'input_parameters': {
                'requested_conformers': num_conformers,
                'force_field': calculator.force_field
            },
            'molecular_properties': {
                'rotatable_bonds': props.get('rotatable_bonds', 0),
                'heavy_atoms': props.get('num_atoms', 0)  # This is actually total atoms, close approximation
            },
            'conformational_analysis': {
                k: v for k, v in props.items() 
                if k in calculator.supported_properties
            },
            'interpretation': {
                'flexibility_category': props.get('flexibility_category', 'unknown'),
                'conformational_complexity': props.get('conformational_complexity', 'unknown')
            },
            'success': True
        }
            
    except Exception as e:
        return {
            'error': str(e),
            'success': False
        }


def generate_conformers(smiles: str, num_conformers: int = 10, 
                       random_seed: int = 42) -> Optional[Chem.Mol]:
    """
    Legacy function to generate conformers.
    
    Args:
        smiles: SMILES string of the molecule
        num_conformers: Number of conformers to generate
        random_seed: Random seed for reproducibility
        
    Returns:
        Molecule object with multiple conformers or None if failed
    """
    try:
        calculator = ConformationalCalculator()
        calculator.max_conformers = num_conformers
        
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
            
        return calculator._generate_conformers(mol)
        
    except Exception:
        return None