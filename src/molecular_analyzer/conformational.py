"""
Conformational Analysis Module

This module provides conformational analysis capabilities including
conformer generation, energy calculations, and structural diversity analysis.
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolAlign, rdForceFieldHelpers
from rdkit.Chem.rdMolDescriptors import CalcNumRotatableBonds
import math


class ConformerGenerator:
    """Generate and analyze molecular conformers."""
    
    def __init__(self, force_field: str = 'UFF'):
        """
        Initialize conformer generator.
        
        Args:
            force_field: Force field to use ('UFF' or 'MMFF')
        """
        self.force_field = force_field
        
    def generate_conformers(self, smiles: str, num_conformers: int = 10, 
                          random_seed: int = 42) -> Optional[Chem.Mol]:
        """
        Generate multiple conformers for a molecule.
        
        Args:
            smiles: SMILES string of the molecule
            num_conformers: Number of conformers to generate
            random_seed: Random seed for reproducibility
            
        Returns:
            Molecule object with multiple conformers or None if failed
        """
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return None
                
            # Add hydrogens
            mol = Chem.AddHs(mol)
            
            # Generate conformers with multiple attempts
            conformer_ids = []
            
            # First attempt with standard parameters
            try:
                conformer_ids = AllChem.EmbedMultipleConfs(
                    mol, 
                    numConfs=num_conformers,
                    randomSeed=random_seed,
                    pruneRmsThresh=0.5,  # Remove similar conformers
                    useExpTorsionAnglePrefs=True,
                    useBasicKnowledge=True
                )
            except:
                conformer_ids = []
            
            # If we didn't get enough conformers, try with looser constraints
            if len(conformer_ids) < min(num_conformers, 3):
                try:
                    conformer_ids = AllChem.EmbedMultipleConfs(
                        mol, 
                        numConfs=num_conformers * 2,
                        randomSeed=random_seed,
                        pruneRmsThresh=0.1,  # Less aggressive pruning
                        useExpTorsionAnglePrefs=False,  # Disable torsion preferences
                        useBasicKnowledge=False
                    )
                except:
                    pass
            
            # Final attempt with very loose constraints
            if len(conformer_ids) < 2:
                try:
                    conformer_ids = AllChem.EmbedMultipleConfs(
                        mol, 
                        numConfs=num_conformers * 3,
                        randomSeed=random_seed,
                        pruneRmsThresh=-1,  # No pruning
                        useExpTorsionAnglePrefs=False,
                        useBasicKnowledge=False
                    )
                except:
                    pass
            
            if not conformer_ids:
                return None
            
            # Optimize conformers
            if self.force_field == 'UFF':
                for conf_id in conformer_ids:
                    AllChem.UFFOptimizeMolecule(mol, confId=conf_id)
            elif self.force_field == 'MMFF':
                for conf_id in conformer_ids:
                    AllChem.MMFFOptimizeMolecule(mol, confId=conf_id)
            
            return mol
            
        except Exception:
            return None
    
    def calculate_conformer_energies(self, mol: Chem.Mol) -> List[float]:
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
                    ff = AllChem.UFFGetMoleculeForceField(mol, confId=conf_id)
                    if ff:
                        energy = ff.CalcEnergy()
                        energies.append(energy)
                    else:
                        energies.append(float('inf'))
            elif self.force_field == 'MMFF':
                for conf_id in range(mol.GetNumConformers()):
                    ff = AllChem.MMFFGetMoleculeForceField(mol, confId=conf_id)
                    if ff:
                        energy = ff.CalcEnergy()
                        energies.append(energy)
                    else:
                        energies.append(float('inf'))
                        
        except Exception:
            energies = [float('inf')] * mol.GetNumConformers()
            
        return energies
    
    def find_lowest_energy_conformer(self, mol: Chem.Mol) -> Tuple[int, float]:
        """
        Find the conformer with the lowest energy.
        
        Args:
            mol: Molecule with conformers
            
        Returns:
            Tuple of (conformer_id, energy)
        """
        energies = self.calculate_conformer_energies(mol)
        
        if not energies:
            return -1, float('inf')
            
        min_energy_idx = np.argmin(energies)
        return min_energy_idx, energies[min_energy_idx]
    
    def calculate_rmsd_matrix(self, mol: Chem.Mol) -> np.ndarray:
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
                    rmsd = rdMolAlign.GetBestRMS(mol, mol, i, j)
                    rmsd_matrix[i, j] = rmsd
                    rmsd_matrix[j, i] = rmsd
                    
        except Exception:
            pass
            
        return rmsd_matrix
    
    def analyze_conformational_diversity(self, mol: Chem.Mol) -> Dict[str, Any]:
        """
        Analyze conformational diversity of generated conformers.
        
        Args:
            mol: Molecule with conformers
            
        Returns:
            Dictionary with diversity analysis
        """
        try:
            num_conformers = mol.GetNumConformers()
            
            if num_conformers < 2:
                return {'error': 'Need at least 2 conformers for diversity analysis'}
            
            # Calculate energies
            energies = self.calculate_conformer_energies(mol)
            
            # Calculate RMSD matrix
            rmsd_matrix = self.calculate_rmsd_matrix(mol)
            
            # Remove diagonal elements for statistics
            rmsd_values = rmsd_matrix[np.triu_indices_from(rmsd_matrix, k=1)]
            
            # Find lowest energy conformer
            lowest_energy_idx, lowest_energy = self.find_lowest_energy_conformer(mol)
            
            # Calculate relative energies
            relative_energies = np.array(energies) - lowest_energy
            
            # Count conformers within energy windows
            conformers_1kcal = np.sum(relative_energies <= 1.0)
            conformers_2kcal = np.sum(relative_energies <= 2.0)
            conformers_3kcal = np.sum(relative_energies <= 3.0)
            
            return {
                'num_conformers': num_conformers,
                'lowest_energy_conformer': lowest_energy_idx,
                'lowest_energy': lowest_energy,
                'energy_range': float(np.max(energies) - np.min(energies)),
                'mean_energy': float(np.mean(energies)),
                'energy_std': float(np.std(energies)),
                'conformers_within_1kcal': int(conformers_1kcal),
                'conformers_within_2kcal': int(conformers_2kcal),
                'conformers_within_3kcal': int(conformers_3kcal),
                'rmsd_statistics': {
                    'mean_rmsd': float(np.mean(rmsd_values)),
                    'max_rmsd': float(np.max(rmsd_values)),
                    'min_rmsd': float(np.min(rmsd_values)),
                    'rmsd_std': float(np.std(rmsd_values))
                },
                'flexibility_index': float(np.mean(rmsd_values)),
                'rotatable_bonds': CalcNumRotatableBonds(mol),
                'energies': energies,
                'relative_energies': relative_energies.tolist(),
                'rmsd_matrix': rmsd_matrix.tolist()
            }
            
        except Exception as e:
            return {'error': str(e)}


def perform_conformational_analysis(smiles: str, num_conformers: int = 20) -> Dict[str, Any]:
    """
    Perform comprehensive conformational analysis.
    
    Args:
        smiles: SMILES string of the molecule
        num_conformers: Number of conformers to generate
        
    Returns:
        Dictionary with complete conformational analysis
    """
    try:
        generator = ConformerGenerator()
        
        # Generate conformers
        mol = generator.generate_conformers(smiles, num_conformers)
        
        if mol is None or mol.GetNumConformers() < 2:
            return {'error': 'Failed to generate at least 2 conformers for analysis', 'success': False}
        
        # Analyze diversity
        diversity_analysis = generator.analyze_conformational_diversity(mol)
        
        # Basic molecular properties
        basic_mol = Chem.MolFromSmiles(smiles)
        if basic_mol:
            basic_mol = Chem.AddHs(basic_mol)  # Add explicit hydrogens
        rotatable_bonds = CalcNumRotatableBonds(basic_mol) if basic_mol else 0
        
        # Compile results
        results = {
            'smiles': smiles,
            'input_parameters': {
                'requested_conformers': num_conformers,
                'force_field': generator.force_field
            },
            'molecular_properties': {
                'rotatable_bonds': rotatable_bonds,
                'heavy_atoms': basic_mol.GetNumHeavyAtoms() if basic_mol else 0
            },
            'conformational_analysis': diversity_analysis,
            'success': True
        }
        
        # Add interpretation
        if rotatable_bonds == 0:
            flexibility = 'Rigid'
        elif rotatable_bonds <= 3:
            flexibility = 'Low flexibility'
        elif rotatable_bonds <= 7:
            flexibility = 'Moderate flexibility'
        else:
            flexibility = 'High flexibility'
            
        results['interpretation'] = {
            'flexibility_category': flexibility,
            'conformational_complexity': 'High' if diversity_analysis.get('rmsd_statistics', {}).get('mean_rmsd', 0) > 2.0 else 'Low'
        }
        
        return results
        
    except Exception as e:
        return {'error': str(e), 'success': False}


class ConformationalChangeAnalyzer:
    """Analyze conformational changes between different conformers."""
    
    def __init__(self, angle_threshold: float = 15.0, distance_threshold: float = 1.0):
        """
        Initialize conformational change analyzer.
        
        Args:
            angle_threshold: Minimum torsion angle change to consider significant (degrees)
            distance_threshold: Minimum atom displacement to consider significant (Angstroms)
        """
        self.angle_threshold = angle_threshold
        self.distance_threshold = distance_threshold
    
    def calculate_torsion_angle(self, mol: Chem.Mol, conformer_id: int, atom_indices: Tuple[int, int, int, int]) -> float:
        """
        Calculate torsion angle for given atom indices in a specific conformer.
        
        Args:
            mol: Molecule object
            conformer_id: Conformer ID
            atom_indices: Tuple of 4 atom indices for torsion
            
        Returns:
            Torsion angle in degrees
        """
        try:
            conf = mol.GetConformer(conformer_id)
            pos1 = conf.GetAtomPosition(atom_indices[0])
            pos2 = conf.GetAtomPosition(atom_indices[1])
            pos3 = conf.GetAtomPosition(atom_indices[2])
            pos4 = conf.GetAtomPosition(atom_indices[3])
            
            # Calculate torsion angle using cross products
            v1 = np.array([pos1.x - pos2.x, pos1.y - pos2.y, pos1.z - pos2.z])
            v2 = np.array([pos3.x - pos2.x, pos3.y - pos2.y, pos3.z - pos2.z])
            v3 = np.array([pos4.x - pos3.x, pos4.y - pos3.y, pos4.z - pos3.z])
            
            cross1 = np.cross(v1, v2)
            cross2 = np.cross(v2, v3)
            
            # Normalize cross products
            cross1_norm = cross1 / (np.linalg.norm(cross1) + 1e-10)
            cross2_norm = cross2 / (np.linalg.norm(cross2) + 1e-10)
            
            # Calculate angle
            dot_product = np.clip(np.dot(cross1_norm, cross2_norm), -1.0, 1.0)
            angle = math.degrees(math.acos(abs(dot_product)))
            
            # Determine sign using scalar triple product
            triple_product = np.dot(cross1, v3)
            if triple_product < 0:
                angle = -angle
                
            return angle
            
        except Exception:
            return 0.0
    
    def find_rotatable_bonds(self, mol: Chem.Mol) -> List[Tuple[int, int, int, int]]:
        """
        Find rotatable bonds and their associated torsion angles.
        
        Args:
            mol: Molecule object
            
        Returns:
            List of torsion angle atom tuples
        """
        torsions = []
        
        try:
            for bond in mol.GetBonds():
                if bond.GetBondType() == Chem.rdchem.BondType.SINGLE and not bond.IsInRing():
                    begin_atom = bond.GetBeginAtom()
                    end_atom = bond.GetEndAtom()
                    
                    # Find neighbors for torsion calculation
                    begin_neighbors = [n.GetIdx() for n in begin_atom.GetNeighbors() if n.GetIdx() != end_atom.GetIdx()]
                    end_neighbors = [n.GetIdx() for n in end_atom.GetNeighbors() if n.GetIdx() != begin_atom.GetIdx()]
                    
                    if begin_neighbors and end_neighbors:
                        # Use first available neighbor for each end
                        torsion = (begin_neighbors[0], begin_atom.GetIdx(), end_atom.GetIdx(), end_neighbors[0])
                        torsions.append(torsion)
                        
        except Exception:
            pass
            
        return torsions
    
    def calculate_atom_displacements(self, mol: Chem.Mol, conf1_id: int, conf2_id: int) -> Dict[int, float]:
        """
        Calculate atom displacement distances between two conformers.
        
        Args:
            mol: Molecule object
            conf1_id: First conformer ID
            conf2_id: Second conformer ID
            
        Returns:
            Dictionary mapping atom index to displacement distance
        """
        displacements = {}
        
        try:
            conf1 = mol.GetConformer(conf1_id)
            conf2 = mol.GetConformer(conf2_id)
            
            for atom_idx in range(mol.GetNumAtoms()):
                pos1 = conf1.GetAtomPosition(atom_idx)
                pos2 = conf2.GetAtomPosition(atom_idx)
                
                # Calculate Euclidean distance
                dx = pos1.x - pos2.x
                dy = pos1.y - pos2.y
                dz = pos1.z - pos2.z
                
                distance = math.sqrt(dx*dx + dy*dy + dz*dz)
                displacements[atom_idx] = distance
                
        except Exception:
            pass
            
        return displacements
    
    def analyze_conformational_changes(self, mol: Chem.Mol, conf1_id: int, conf2_id: int) -> Dict[str, Any]:
        """
        Analyze conformational changes between two conformers.
        
        Args:
            mol: Molecule object with conformers
            conf1_id: First conformer ID
            conf2_id: Second conformer ID
            
        Returns:
            Dictionary with change analysis
        """
        try:
            # Find rotatable bonds
            rotatable_bonds = self.find_rotatable_bonds(mol)
            
            # Analyze torsion angle changes
            torsion_changes = []
            for torsion in rotatable_bonds:
                angle1 = self.calculate_torsion_angle(mol, conf1_id, torsion)
                angle2 = self.calculate_torsion_angle(mol, conf2_id, torsion)
                
                angle_diff = abs(angle1 - angle2)
                # Handle angle wrapping
                if angle_diff > 180:
                    angle_diff = 360 - angle_diff
                
                if angle_diff >= self.angle_threshold:
                    torsion_changes.append({
                        'atoms': torsion,
                        'angle_conf1': angle1,
                        'angle_conf2': angle2,
                        'angle_change': angle_diff,
                        'bond_atoms': (torsion[1], torsion[2]),
                        'change_type': 'major' if angle_diff > 30 else 'minor'
                    })
            
            # Calculate atom displacements
            displacements = self.calculate_atom_displacements(mol, conf1_id, conf2_id)
            
            # Find atoms with significant displacement
            displaced_atoms = []
            for atom_idx, displacement in displacements.items():
                if displacement >= self.distance_threshold:
                    atom = mol.GetAtomWithIdx(atom_idx)
                    displaced_atoms.append({
                        'atom_idx': atom_idx,
                        'element': atom.GetSymbol(),
                        'displacement': displacement,
                        'change_type': 'major' if displacement > 2.0 else 'minor'
                    })
            
            # Classify overall change magnitude
            max_displacement = max(displacements.values()) if displacements else 0
            max_angle_change = max([change['angle_change'] for change in torsion_changes], default=0)
            
            if max_displacement > 2.0 or max_angle_change > 30:
                change_magnitude = 'major'
            elif max_displacement > 1.0 or max_angle_change > 15:
                change_magnitude = 'moderate'
            else:
                change_magnitude = 'minor'
            
            return {
                'conformer_pair': (conf1_id, conf2_id),
                'torsion_changes': torsion_changes,
                'displaced_atoms': displaced_atoms,
                'change_magnitude': change_magnitude,
                'max_displacement': max_displacement,
                'max_angle_change': max_angle_change,
                'num_torsion_changes': len(torsion_changes),
                'num_displaced_atoms': len(displaced_atoms),
                'atom_displacements': displacements
            }
            
        except Exception as e:
            return {'error': f'Change analysis failed: {str(e)}'}
    
    def compare_all_conformers(self, mol: Chem.Mol) -> Dict[str, Any]:
        """
        Compare all conformers and identify changes between each pair.
        
        Args:
            mol: Molecule object with multiple conformers
            
        Returns:
            Dictionary with comprehensive change analysis
        """
        try:
            num_conformers = mol.GetNumConformers()
            if num_conformers < 2:
                return {'error': 'Need at least 2 conformers for comparison'}
            
            all_comparisons = []
            change_summary = {'major': 0, 'moderate': 0, 'minor': 0}
            
            # Compare each pair of conformers
            for i in range(num_conformers):
                for j in range(i + 1, num_conformers):
                    comparison = self.analyze_conformational_changes(mol, i, j)
                    
                    if 'error' not in comparison:
                        all_comparisons.append(comparison)
                        change_summary[comparison['change_magnitude']] += 1
            
            # Find most flexible regions (atoms that move frequently)
            atom_flexibility = {}
            for atom_idx in range(mol.GetNumAtoms()):
                atom = mol.GetAtomWithIdx(atom_idx)
                displacements = []
                
                for comparison in all_comparisons:
                    if atom_idx in comparison['atom_displacements']:
                        displacements.append(comparison['atom_displacements'][atom_idx])
                
                if displacements:
                    atom_flexibility[atom_idx] = {
                        'element': atom.GetSymbol(),
                        'avg_displacement': np.mean(displacements),
                        'max_displacement': max(displacements),
                        'flexibility_score': np.mean(displacements) * len(displacements)
                    }
            
            # Sort atoms by flexibility
            most_flexible_atoms = sorted(
                atom_flexibility.items(),
                key=lambda x: x[1]['flexibility_score'],
                reverse=True
            )[:10]  # Top 10 most flexible atoms
            
            return {
                'num_conformers': num_conformers,
                'num_comparisons': len(all_comparisons),
                'change_summary': change_summary,
                'all_comparisons': all_comparisons,
                'most_flexible_atoms': most_flexible_atoms,
                'atom_flexibility': atom_flexibility
            }
            
        except Exception as e:
            return {'error': f'Multi-conformer comparison failed: {str(e)}'}


# Example usage and testing
if __name__ == "__main__":
    # Test with a flexible molecule
    test_smiles = "CCC(C)C(C)C(=O)O"  # A branched carboxylic acid
    
    analysis = perform_conformational_analysis(test_smiles, num_conformers=10)
    
    if analysis.get('success'):
        print(f"Conformational Analysis Results for {test_smiles}:")
        print(f"Generated {analysis['conformational_analysis']['num_conformers']} conformers")
        print(f"Flexibility: {analysis['interpretation']['flexibility_category']}")
        print(f"Energy range: {analysis['conformational_analysis']['energy_range']:.2f} kcal/mol")
        print(f"Mean RMSD: {analysis['conformational_analysis']['rmsd_statistics']['mean_rmsd']:.2f} Å")
    else:
        print(f"Analysis failed: {analysis.get('error', 'Unknown error')}")