"""
Molecular comparison calculator implementation.

Provides OOP interface for comparing multiple molecules including similarity
calculations, clustering, statistical analysis, and comprehensive comparisons.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Union, Tuple
from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem
from datetime import datetime

from ..models.base import BaseCalculator, CalculationConfig
from ..models.models import MoleculeData, PropertyData
from ..models.exceptions import ComputationError, ValidationError, AnalysisError


class ComparisonCalculator(BaseCalculator[Dict[str, Any]]):
    """
    Calculator for molecular comparison and similarity analysis.
    
    Provides comprehensive molecular comparison capabilities including fingerprint
    similarity, property comparisons, clustering, and statistical analysis.
    """
    
    def __init__(self, config: Optional[CalculationConfig] = None):
        super().__init__(config)
        self.fingerprint_type = "morgan"
        self.fingerprint_radius = 2
        self.fingerprint_bits = 2048
    
    @property
    def calculator_name(self) -> str:
        """Return the name of this calculator."""
        return "ComparisonCalculator"
    
    @property
    def supported_properties(self) -> List[str]:
        """Return list of properties this calculator can compute."""
        return [
            "morgan_fingerprint", "similarity_metrics", "clustering_data",
            "comparison_statistics", "property_differences", "similarity_matrix",
            "most_similar_pairs", "diversity_metrics", "fingerprint_data"
        ]
    
    def _calculate_properties(self, molecule: MoleculeData) -> Dict[str, Any]:
        """
        Calculate fingerprint and comparison-ready data for a single molecule.
        
        Args:
            molecule: Validated molecule data
            
        Returns:
            Dictionary containing fingerprint data and comparison metrics
        """
        try:
            # Convert SMILES to RDKit molecule
            mol = Chem.MolFromSmiles(molecule.smiles)
            if mol is None:
                raise ValidationError(f"Invalid molecule structure: {molecule.smiles}")
            
            # Generate molecular fingerprint
            mol = Chem.AddHs(mol)
            fingerprint = AllChem.GetMorganFingerprintAsBitVect(
                mol, self.fingerprint_radius, nBits=self.fingerprint_bits
            )
            
            # Convert fingerprint to numpy array for easier manipulation
            fp_array = np.zeros((self.fingerprint_bits,))
            DataStructs.ConvertToNumpyArray(fingerprint, fp_array)
            
            # Calculate descriptor vector for additional similarity measures
            descriptor_vector = self._calculate_descriptor_vector(mol)
            
            return {
                "morgan_fingerprint": fingerprint,
                "fingerprint_array": fp_array,
                "descriptor_vector": descriptor_vector,
                "fingerprint_bits": self.fingerprint_bits,
                "fingerprint_radius": self.fingerprint_radius,
                "ready_for_comparison": True,
                "molecule_name": molecule.name or "Unknown",
                "smiles": molecule.smiles
            }
            
        except Exception as e:
            raise ComputationError(f"Failed to calculate comparison properties: {str(e)}")
    
    def _calculate_descriptor_vector(self, mol: Chem.Mol) -> np.ndarray:
        """Calculate descriptor vector for additional similarity measures."""
        try:
            from rdkit.Chem import rdMolDescriptors, Descriptors
            
            descriptors = [
                Descriptors.MolWt(mol),
                Descriptors.MolLogP(mol),
                rdMolDescriptors.CalcTPSA(mol),
                rdMolDescriptors.CalcNumHBD(mol),
                rdMolDescriptors.CalcNumHBA(mol),
                rdMolDescriptors.CalcNumRotatableBonds(mol),
                mol.GetNumAtoms(),
                mol.GetNumBonds(),
                rdMolDescriptors.CalcNumRings(mol),
                rdMolDescriptors.CalcNumAromaticRings(mol)
            ]
            
            return np.array(descriptors, dtype=float)
            
        except Exception as e:
            # Return zero vector if descriptor calculation fails
            return np.zeros(10, dtype=float)
    
    def calculate_similarity(self, 
                           mol1: Union[str, MoleculeData], 
                           mol2: Union[str, MoleculeData],
                           method: str = "tanimoto") -> float:
        """
        Calculate similarity between two molecules.
        
        Args:
            mol1: First molecule (SMILES string or MoleculeData)
            mol2: Second molecule (SMILES string or MoleculeData)
            method: Similarity method ("tanimoto", "dice", "cosine")
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        try:
            # Convert to MoleculeData if needed
            if isinstance(mol1, str):
                mol1 = MoleculeData(smiles=mol1)
            if isinstance(mol2, str):
                mol2 = MoleculeData(smiles=mol2)
            
            # Calculate fingerprints
            props1 = self.calculate(mol1)
            props2 = self.calculate(mol2)
            
            fp1 = props1["morgan_fingerprint"]
            fp2 = props2["morgan_fingerprint"]
            
            # Calculate similarity based on method
            if method.lower() == "tanimoto":
                similarity = DataStructs.TanimotoSimilarity(fp1, fp2)
            elif method.lower() == "dice":
                similarity = DataStructs.DiceSimilarity(fp1, fp2)
            elif method.lower() == "cosine":
                # Use descriptor vectors for cosine similarity
                vec1 = props1["descriptor_vector"]
                vec2 = props2["descriptor_vector"]
                
                # Normalize vectors
                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)
                
                if norm1 == 0 or norm2 == 0:
                    similarity = 0.0
                else:
                    similarity = np.dot(vec1, vec2) / (norm1 * norm2)
            else:
                # Default to Tanimoto
                similarity = DataStructs.TanimotoSimilarity(fp1, fp2)
            
            return float(max(0.0, min(1.0, similarity)))  # Ensure valid range
            
        except Exception as e:
            raise ComputationError(f"Failed to calculate similarity: {str(e)}")
    
    def calculate_similarity_matrix(self, 
                                   molecules: List[Union[str, MoleculeData]],
                                   method: str = "tanimoto") -> pd.DataFrame:
        """
        Calculate similarity matrix for multiple molecules.
        
        Args:
            molecules: List of molecules (SMILES strings or MoleculeData)
            method: Similarity method ("tanimoto", "dice", "cosine")
            
        Returns:
            DataFrame with similarity matrix
        """
        try:
            if len(molecules) < 2:
                raise ValidationError("At least 2 molecules required for similarity matrix")
            
            # Convert to MoleculeData and calculate fingerprints
            mol_data = []
            mol_names = []
            
            for i, mol in enumerate(molecules):
                if isinstance(mol, str):
                    mol_obj = MoleculeData(smiles=mol, name=f"Molecule_{i+1}")
                else:
                    mol_obj = mol
                
                mol_data.append(self.calculate(mol_obj))
                mol_names.append(mol_obj.name or f"Molecule_{i+1}")
            
            # Create similarity matrix
            n_mols = len(mol_data)
            similarity_matrix = np.zeros((n_mols, n_mols))
            
            for i in range(n_mols):
                for j in range(n_mols):
                    if i == j:
                        similarity_matrix[i, j] = 1.0
                    else:
                        # Calculate similarity using stored fingerprints
                        fp1 = mol_data[i]["morgan_fingerprint"]
                        fp2 = mol_data[j]["morgan_fingerprint"]
                        
                        if method.lower() == "tanimoto":
                            sim = DataStructs.TanimotoSimilarity(fp1, fp2)
                        elif method.lower() == "dice":
                            sim = DataStructs.DiceSimilarity(fp1, fp2)
                        elif method.lower() == "cosine":
                            vec1 = mol_data[i]["descriptor_vector"]
                            vec2 = mol_data[j]["descriptor_vector"]
                            
                            norm1 = np.linalg.norm(vec1)
                            norm2 = np.linalg.norm(vec2)
                            
                            if norm1 == 0 or norm2 == 0:
                                sim = 0.0
                            else:
                                sim = np.dot(vec1, vec2) / (norm1 * norm2)
                        else:
                            sim = DataStructs.TanimotoSimilarity(fp1, fp2)
                        
                        similarity_matrix[i, j] = max(0.0, min(1.0, sim))
            
            return pd.DataFrame(similarity_matrix, index=mol_names, columns=mol_names)
            
        except Exception as e:
            raise ComputationError(f"Failed to calculate similarity matrix: {str(e)}")
    
    def find_most_similar_pairs(self, 
                               similarity_matrix: pd.DataFrame,
                               n_pairs: int = 3) -> List[Dict[str, Any]]:
        """
        Find the most similar molecule pairs from similarity matrix.
        
        Args:
            similarity_matrix: Similarity matrix DataFrame
            n_pairs: Number of top pairs to return
            
        Returns:
            List of dictionaries with pair information
        """
        try:
            similarities = []
            molecules = similarity_matrix.index.tolist()
            
            for i, mol1 in enumerate(molecules):
                for j, mol2 in enumerate(molecules):
                    if i < j:  # Avoid duplicates and self-comparisons
                        sim = similarity_matrix.iloc[i, j]
                        similarities.append({
                            'molecule1': mol1,
                            'molecule2': mol2,
                            'similarity': float(sim),
                            'rank': None  # Will be filled after sorting
                        })
            
            # Sort by similarity (highest first)
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Add rank information
            for i, pair in enumerate(similarities[:n_pairs]):
                pair['rank'] = i + 1
            
            return similarities[:n_pairs]
            
        except Exception as e:
            raise ComputationError(f"Failed to find similar pairs: {str(e)}")
    
    def cluster_molecules(self, 
                         molecules: List[Union[str, MoleculeData]],
                         method: str = "kmeans",
                         n_clusters: Optional[int] = None) -> Dict[str, Any]:
        """
        Cluster molecules based on similarity.
        
        Args:
            molecules: List of molecules to cluster
            method: Clustering method ("kmeans", "hierarchical")
            n_clusters: Number of clusters (auto-determined if None)
            
        Returns:
            Dictionary with clustering results
        """
        try:
            if len(molecules) < 2:
                raise ValidationError("At least 2 molecules required for clustering")
            
            # Calculate fingerprint matrix
            fingerprints = []
            mol_names = []
            
            for i, mol in enumerate(molecules):
                if isinstance(mol, str):
                    mol_obj = MoleculeData(smiles=mol, name=f"Molecule_{i+1}")
                else:
                    mol_obj = mol
                
                props = self.calculate(mol_obj)
                fingerprints.append(props["fingerprint_array"])
                mol_names.append(mol_obj.name or f"Molecule_{i+1}")
            
            fp_matrix = np.array(fingerprints)
            
            # Determine number of clusters if not specified
            if n_clusters is None:
                n_clusters = min(len(molecules) // 2, 5)  # Reasonable default
                n_clusters = max(2, n_clusters)  # At least 2 clusters
            
            # Perform clustering
            if method.lower() == "kmeans":
                from sklearn.cluster import KMeans
                clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                cluster_labels = clusterer.fit_predict(fp_matrix)
                
                # Calculate cluster centers in similarity space
                cluster_centers = clusterer.cluster_centers_
                
            elif method.lower() == "hierarchical":
                from sklearn.cluster import AgglomerativeClustering
                clusterer = AgglomerativeClustering(n_clusters=n_clusters)
                cluster_labels = clusterer.fit_predict(fp_matrix)
                cluster_centers = None
                
            else:
                raise ValidationError(f"Unsupported clustering method: {method}")
            
            # Organize results
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append({
                    'name': mol_names[i],
                    'index': i,
                    'molecule': molecules[i] if isinstance(molecules[i], str) else molecules[i].smiles
                })
            
            # Calculate cluster statistics
            cluster_stats = {}
            for cluster_id, members in clusters.items():
                # Calculate within-cluster similarity
                member_indices = [m['index'] for m in members]
                if len(member_indices) > 1:
                    similarities = []
                    for i in range(len(member_indices)):
                        for j in range(i + 1, len(member_indices)):
                            idx1, idx2 = member_indices[i], member_indices[j]
                            fp1 = fp_matrix[idx1]
                            fp2 = fp_matrix[idx2]
                            
                            # Calculate Tanimoto similarity from fingerprint arrays
                            intersection = np.sum(fp1 * fp2)
                            union = np.sum((fp1 + fp2) > 0)
                            sim = intersection / union if union > 0 else 0.0
                            similarities.append(sim)
                    
                    avg_similarity = np.mean(similarities) if similarities else 1.0
                else:
                    avg_similarity = 1.0
                
                cluster_stats[cluster_id] = {
                    'size': len(members),
                    'avg_intra_similarity': float(avg_similarity),
                    'members': [m['name'] for m in members]
                }
            
            return {
                'method': method,
                'n_clusters': n_clusters,
                'cluster_labels': cluster_labels.tolist(),
                'clusters': clusters,
                'cluster_statistics': cluster_stats,
                'cluster_centers': cluster_centers.tolist() if cluster_centers is not None else None,
                'silhouette_score': self._calculate_silhouette_score(fp_matrix, cluster_labels)
            }
            
        except ImportError:
            raise ComputationError("Clustering requires scikit-learn. Install with: pip install scikit-learn")
        except Exception as e:
            raise ComputationError(f"Failed to perform clustering: {str(e)}")
    
    def _calculate_silhouette_score(self, X: np.ndarray, labels: np.ndarray) -> float:
        """Calculate silhouette score for clustering quality assessment."""
        try:
            from sklearn.metrics import silhouette_score
            if len(np.unique(labels)) > 1:
                return float(silhouette_score(X, labels))
            else:
                return 0.0
        except:
            return 0.0  # Return 0 if calculation fails
    
    def compare_molecular_properties(self, 
                                   molecules: Dict[str, Union[str, MoleculeData]],
                                   reference_molecule: Optional[str] = None) -> pd.DataFrame:
        """
        Compare molecular properties across multiple molecules.
        
        Args:
            molecules: Dictionary mapping molecule names to SMILES/MoleculeData
            reference_molecule: Reference molecule name for difference calculations
            
        Returns:
            DataFrame with property comparison data
        """
        try:
            from ..calculator import MolecularAnalyzer
            
            analyzer = MolecularAnalyzer()
            properties_data = []
            
            # Calculate properties for all molecules
            for name, mol in molecules.items():
                try:
                    if isinstance(mol, str):
                        smiles = mol
                    else:
                        smiles = mol.smiles
                    
                    props = analyzer.calculate_properties(smiles)
                    props['molecule_name'] = name
                    props['smiles'] = smiles
                    properties_data.append(props)
                    
                except Exception as e:
                    properties_data.append({
                        'molecule_name': name,
                        'smiles': smiles if 'smiles' in locals() else 'Unknown',
                        'error': str(e)
                    })
            
            df = pd.DataFrame(properties_data)
            
            # Calculate differences from reference molecule if specified
            if reference_molecule and reference_molecule in molecules:
                ref_row = df[df['molecule_name'] == reference_molecule]
                if not ref_row.empty:
                    numeric_cols = [
                        'molecular_weight', 'logP', 'tpsa', 'hbd', 'hba', 
                        'num_atoms', 'num_bonds', 'num_rings', 'num_rotatable_bonds'
                    ]
                    
                    for col in numeric_cols:
                        if col in df.columns:
                            ref_value = ref_row[col].iloc[0]
                            if pd.notnull(ref_value):
                                df[f'{col}_diff'] = df[col] - ref_value
                                # Avoid division by zero
                                if ref_value != 0:
                                    df[f'{col}_pct_diff'] = ((df[col] - ref_value) / ref_value * 100).round(2)
                                else:
                                    df[f'{col}_pct_diff'] = 0.0
            
            return df
            
        except Exception as e:
            raise ComputationError(f"Failed to compare molecular properties: {str(e)}")


# Legacy compatibility functions for backwards compatibility
def calculate_similarity_matrix(molecules_dict: Dict[str, str], 
                              method: str = "tanimoto") -> pd.DataFrame:
    """Legacy function for calculating similarity matrix."""
    calculator = ComparisonCalculator()
    molecules = [MoleculeData(smiles=smiles, name=name) for name, smiles in molecules_dict.items()]
    return calculator.calculate_similarity_matrix(molecules, method)


def find_most_similar_pairs(similarity_matrix: pd.DataFrame, 
                           n_pairs: int = 3) -> List[Dict[str, Any]]:
    """Legacy function for finding most similar pairs."""
    calculator = ComparisonCalculator()
    return calculator.find_most_similar_pairs(similarity_matrix, n_pairs)


def calculate_property_differences(molecules_dict: Dict[str, str], 
                                 reference_molecule: Optional[str] = None) -> pd.DataFrame:
    """Legacy function for calculating property differences."""
    calculator = ComparisonCalculator()
    return calculator.compare_molecular_properties(molecules_dict, reference_molecule)


# Export list for module
__all__ = [
    'ComparisonCalculator',
    'calculate_similarity_matrix',
    'find_most_similar_pairs', 
    'calculate_property_differences'
]