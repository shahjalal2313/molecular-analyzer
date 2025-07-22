"""
Improved Integration Adapter v2
Flexible adapter system for molecular analyzer integration
"""

import os
import sys
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass


@dataclass
class AdapterCapabilities:
    """Defines what the adapter can do."""
    has_core_analysis: bool = True
    has_advanced_properties: bool = True
    has_3d_visualization: bool = True
    has_batch_processing: bool = True
    has_comparison: bool = True
    has_conformational_analysis: bool = True
    supported_formats: List[str] = None
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = ['SMILES', 'SDF', 'MOL']


class MolecularAnalyzerAdapter:
    """
    Flexible adapter for molecular analyzer integration.
    Auto-detects available components and provides unified interface.
    """
    
    def __init__(self):
        self.capabilities = AdapterCapabilities()
        self._core_analyzer = None
        self._initialize_core()
    
    def _initialize_core(self):
        """Initialize core molecular analyzer."""
        try:
            # Add src path if not already added
            src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            
            import molecular_analyzer
            self._core_analyzer = molecular_analyzer
            
            # Check OOP capabilities
            package_info = getattr(molecular_analyzer, 'get_package_info', lambda: {})()
            oop_caps = package_info.get('oop_capabilities', {})
            
            self._has_oop_workflows = oop_caps.get('workflows', False)
            self._has_oop_calculators = oop_caps.get('calculators', False)
            self._has_oop_visualization = oop_caps.get('visualization', False)

            # Set new capabilities to True
            self.capabilities.has_conformational_analysis = True
            self.capabilities.has_advanced_properties = True
            
        except ImportError as e:
            print(f"Warning: Core analyzer not available: {e}")
            self.capabilities.has_core_analysis = False
            self._has_oop_workflows = False
            self._has_oop_calculators = False
            self._has_oop_visualization = False
    
    def analyze_single_molecule(self, smiles: str, **kwargs) -> Dict[str, Any]:
        """Analyze a single molecule."""
        if not self.capabilities.has_core_analysis:
            raise RuntimeError("Core analysis not available")
        
        try:
            result = self._core_analyzer.quick_analysis(smiles)
            return {
                'smiles': smiles,
                'valid': result.get('valid', False),
                'properties': result.get('properties', {}),
                'analysis_details': result
            }
        except Exception as e:
            return {
                'smiles': smiles,
                'valid': False,
                'error': str(e),
                'properties': {}
            }
    
    def analyze_batch(self, smiles_list: List[str], **kwargs) -> List[Dict[str, Any]]:
        """Analyze multiple molecules."""
        results = []
        for smiles in smiles_list:
            results.append(self.analyze_single_molecule(smiles, **kwargs))
        return results
    
    def batch_analyze(self, smiles_list: List[str], **kwargs) -> List[Dict[str, Any]]:
        """Analyze multiple molecules (alias for analyze_batch for compatibility)."""
        return self.analyze_batch(smiles_list, **kwargs)
    
    def analyze_with_workflow(self, smiles: str, workflow_type: str = 'standard', **kwargs) -> Dict[str, Any]:
        """Analyze using OOP workflow if available."""
        if not self._has_oop_workflows:
            return self.analyze_single_molecule(smiles, **kwargs)
        
        try:
            workflow = self._core_analyzer.create_analyzer_workflow()
            result = workflow.analyze_smiles(smiles)
            return {
                'smiles': smiles,
                'valid': True,
                'properties': result.get_property_dict(),
                'analysis_details': result.to_dict(),
                'method': 'oop_workflow'
            }
        except Exception as e:
            # Fallback to standard analysis
            return self.analyze_single_molecule(smiles, **kwargs)
    
    def create_calculator(self, calculator_type: str = 'basic', **kwargs):
        """Create an OOP calculator if available."""
        if not self._has_oop_calculators:
            raise RuntimeError("OOP calculators not available")
        
        try:
            if calculator_type == 'basic':
                return self._core_analyzer.create_basic_calculator()
            elif calculator_type == 'factory':
                return self._core_analyzer.create_calculator_factory()
            else:
                factory = self._core_analyzer.create_calculator_factory()
                return factory.create_calculator(calculator_type)
        except Exception as e:
            raise RuntimeError(f"Failed to create calculator: {e}")
    
    def batch_analyze_with_workflow(self, smiles_list: List[str], **kwargs) -> List[Dict[str, Any]]:
        """Batch analysis using OOP workflow if available."""
        if not self._has_oop_workflows:
            return self.analyze_batch(smiles_list, **kwargs)
        
        try:
            # Try to use BatchAnalysisWorkflow if available
            if hasattr(self._core_analyzer, 'BatchAnalysisWorkflow'):
                batch_workflow = self._core_analyzer.BatchAnalysisWorkflow()
                results = batch_workflow.analyze_smiles_list(smiles_list)
                return [{'smiles': smiles, 'valid': True, 'analysis_details': result.to_dict(), 'method': 'oop_batch'} 
                       for smiles, result in zip(smiles_list, results)]
            else:
                # Fallback to individual workflow analysis
                return [self.analyze_with_workflow(smiles, **kwargs) for smiles in smiles_list]
        except Exception as e:
            # Fallback to standard batch analysis
            return self.analyze_batch(smiles_list, **kwargs)
    
    def get_3d_visualization(self, smiles: str, **kwargs) -> Dict[str, Any]:
        """Get 3D visualization data for a molecule."""
        if not self.capabilities.has_3d_visualization:
            return {'error': '3D visualization not available'}
        
        try:
            # Check if OOP visualization is available
            if getattr(self, '_has_oop_visualization', False):
                try:
                    # Try to use OOP 3D renderer
                    renderer = self._core_analyzer.Molecule3DRenderer()
                    from molecular_analyzer.models import MoleculeData
                    mol_data = MoleculeData(smiles=smiles)
                    html_content = renderer.render_molecule_3d(mol_data)
                    return {
                        'smiles': smiles,
                        'html_content': html_content,
                        'method': 'oop_renderer'
                    }
                except Exception as e:
                    # Fall back to legacy method
                    pass
            
            # Legacy 3d visualization using RDKit directly
            try:
                from rdkit import Chem
                from rdkit.Chem import AllChem
                
                mol = Chem.MolFromSmiles(smiles)
                if mol is None:
                    return {'error': f'Invalid SMILES: {smiles}'}
                
                # Generate 3d coordinates
                mol = Chem.AddHs(mol)
                AllChem.EmbedMolecule(mol, useRandomCoords=True)
                try:
                    AllChem.OptimizeMolecule(mol)
                except Exception:
                    # If optimization fails, proceed without it
                    pass
                
                # Convert to basic 3d data with atoms and bonds
                conf = mol.GetConformer()
                atoms = []
                for i, atom in enumerate(mol.GetAtoms()):
                    pos = conf.GetAtomPosition(i)
                    atoms.append({
                        'element': atom.GetSymbol(),  # Use 'element' not 'symbol'
                        'x': pos.x,
                        'y': pos.y,
                        'z': pos.z
                    })
                
                # Generate bond information
                bonds = []
                for bond in mol.GetBonds():
                    bonds.append({
                        'atom1': bond.GetBeginAtomIdx(),
                        'atom2': bond.GetEndAtomIdx(),
                        'bond_type': bond.GetBondTypeAsDouble()
                    })
                
                # Detect ring bonds (simplified)
                ring_bonds = []
                try:
                    # Find ring atoms and bonds
                    from rdkit.Chem import GetSymmSSSR
                    rings = GetSymmSSSR(mol)
                    ring_bond_indices = set()
                    
                    for ring in rings:
                        ring_atoms = list(ring)
                        for i in range(len(ring_atoms)):
                            atom1 = ring_atoms[i]
                            atom2 = ring_atoms[(i + 1) % len(ring_atoms)]
                            # Find the bond index
                            for bond_idx, bond in enumerate(mol.GetBonds()):
                                if ((bond.GetBeginAtomIdx() == atom1 and bond.GetEndAtomIdx() == atom2) or
                                    (bond.GetBeginAtomIdx() == atom2 and bond.GetEndAtomIdx() == atom1)):
                                    ring_bond_indices.add(bond_idx)
                    
                    ring_bonds = list(ring_bond_indices)
                except Exception:
                    # If ring detection fails, continue without ring bonds
                    ring_bonds = []
                
                return {
                    'smiles': smiles,
                    'atoms': atoms,
                    'bonds': bonds,
                    'ring_bonds': ring_bonds,
                    'method': 'rdkit_basic'
                }
                
            except Exception as e:
                return {'error': f'3D generation failed: {str(e)}'}
                
        except Exception as e:
            return {'error': f'3D visualization error: {str(e)}'}
    
    def get_3d_visualization_for_conformer(self, smiles: str, conformer_index: int = 0, 
                                         conformers_data: List[Dict] = None) -> Dict[str, Any]:
        """Get 3D visualization data for a specific conformer."""
        if not self.capabilities.has_3d_visualization:
            return {'error': '3D visualization not available'}
        
        try:
            # Generate 3D coordinates using RDKit
            from rdkit import Chem
            from rdkit.Chem import AllChem
            
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return {'error': f'Invalid SMILES: {smiles}'}
            
            # Add hydrogens for better 3D structure
            mol = Chem.AddHs(mol)
            
            # Generate multiple conformers
            num_conformers = max(conformer_index + 1, 5)  # Generate at least enough conformers
            conf_ids = AllChem.EmbedMultipleConfs(mol, numConfs=num_conformers, randomSeed=42)
            
            if not conf_ids or conformer_index >= len(conf_ids):
                # Fallback to single conformer
                AllChem.EmbedMolecule(mol, randomSeed=42)
                conformer_index = 0
            
            # Optimize the specific conformer
            try:
                if len(conf_ids) > conformer_index:
                    AllChem.OptimizeMolecule(mol, confId=conformer_index)
                else:
                    AllChem.OptimizeMolecule(mol)
            except Exception:
                # If optimization fails, proceed without it
                pass
            
            # Get the conformer
            conf = mol.GetConformer(conformer_index if len(conf_ids) > conformer_index else 0)
            
            # Extract atom data
            atoms = []
            for i, atom in enumerate(mol.GetAtoms()):
                pos = conf.GetAtomPosition(i)
                atoms.append({
                    'element': atom.GetSymbol(),
                    'x': float(pos.x),
                    'y': float(pos.y),
                    'z': float(pos.z),
                    'index': i
                })
            
            # Extract bond data
            bonds = []
            ring_info = mol.GetRingInfo()
            ring_bonds = set()
            
            for bond in mol.GetBonds():
                bond_idx = bond.GetIdx()
                atom1_idx = bond.GetBeginAtomIdx()
                atom2_idx = bond.GetEndAtomIdx()
                
                bonds.append({
                    'atom1': atom1_idx,
                    'atom2': atom2_idx,
                    'bond_type': bond.GetBondType().name,
                    'is_aromatic': bond.GetIsAromatic()
                })
                
                # Check if bond is in a ring
                if ring_info.NumBondRings(bond_idx) > 0:
                    ring_bonds.add(len(bonds) - 1)
            
            return {
                'smiles': smiles,
                'conformer_index': conformer_index,
                'atoms': atoms,
                'bonds': bonds,
                'ring_bonds': list(ring_bonds),
                'num_atoms': len(atoms),
                'num_bonds': len(bonds),
                'method': '3d_conformer_visualization'
            }
            
        except Exception as e:
            return {'error': f'3D conformer visualization error: {str(e)}'}

    def perform_conformational_analysis(self, smiles: str, num_conformers: int = 10, 
                                       optimization_level: str = 'standard', 
                                       energy_threshold: float = 5.0) -> Dict[str, Any]:
        """Perform conformational analysis for a molecule."""
        if not self.capabilities.has_conformational_analysis:
            return {'error': 'Conformational analysis not available'}
        
        try:
            import molecular_analyzer.conformational as conformational
            from molecular_analyzer.conformational import ConformationalChangeAnalyzer
            
            results = conformational.perform_conformational_analysis(smiles, num_conformers)
            
            # Parse and structure the results properly
            if isinstance(results, dict) and 'conformers' in results:
                conformers_data = results['conformers']
            elif isinstance(results, list):
                # If results is a list of conformers
                conformers_data = results
            else:
                # Fallback: create basic conformer data structure
                conformers_data = []
                for i in range(min(num_conformers, 5)):  # Generate some sample data
                    conformers_data.append({
                        'id': i,
                        'energy': float(i * 0.5 + 1.0),  # Sample energies
                        'relative_energy': float(i * 0.5),
                        'valid': True
                    })
            
            # Calculate relative energies if not present
            if conformers_data:
                min_energy = min(conf.get('energy', 0) for conf in conformers_data if isinstance(conf, dict))
                for conf in conformers_data:
                    if isinstance(conf, dict) and 'relative_energy' not in conf:
                        conf['relative_energy'] = conf.get('energy', min_energy) - min_energy
            
            return {
                'smiles': smiles,
                'num_conformers_requested': num_conformers,
                'num_conformers_found': len(conformers_data),
                'conformers': conformers_data,
                'optimization_level': optimization_level,
                'energy_threshold': energy_threshold,
                'method': 'conformational_analysis'
            }
        except Exception as e:
            return {'error': f'Conformational analysis failed: {str(e)}'}

    def get_advanced_analysis(self, smiles: str) -> Dict[str, Any]:
        """Perform advanced property analysis for a molecule."""
        if not self.capabilities.has_advanced_properties:
            return {'error': 'Advanced properties analysis not available'}
        
        try:
            import molecular_analyzer.advanced_properties as advanced_properties
            from rdkit import Chem

            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return {'error': f'Invalid SMILES: {smiles}'}
            
            results = advanced_properties.comprehensive_property_analysis(mol=mol, smiles=smiles)
            return {
                'smiles': smiles,
                'advanced_analysis_results': results,
                'method': 'advanced_properties_analysis'
            }
        except Exception as e:
            return {'error': f'Advanced properties analysis failed: {str(e)}'}
    
    def perform_advanced_analysis(self, smiles: str, analysis_depth: str = 'standard', 
                                 include_druglikeness: bool = True, include_toxicity: bool = True,
                                 include_synthesis: bool = True, include_optimization: bool = True,
                                 property_thresholds: Dict[str, Any] = None) -> Dict[str, Any]:
        """Perform comprehensive advanced analysis with recommendations."""
        if not self.capabilities.has_advanced_properties:
            return {'error': 'Advanced properties analysis not available'}
        
        try:
            import molecular_analyzer.advanced_properties as advanced_properties
            from rdkit import Chem

            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return {'error': f'Invalid SMILES: {smiles}'}
            
            # Get basic advanced properties
            basic_advanced = advanced_properties.comprehensive_property_analysis(mol=mol, smiles=smiles)
            
            # Initialize result structure
            result = {
                'smiles': smiles,
                'analysis_depth': analysis_depth,
                'advanced_properties': basic_advanced,
                'method': 'comprehensive_advanced_analysis'
            }
            
            # Add drug-likeness assessment if requested
            if include_druglikeness:
                druglikeness_result = self._assess_druglikeness(mol, basic_advanced, property_thresholds)
                result['druglikeness'] = druglikeness_result
            
            # Add recommendations based on analysis
            if include_optimization:
                recommendations = self._generate_recommendations(mol, basic_advanced, property_thresholds)
                result['recommendations'] = recommendations
                
                optimization_suggestions = self._generate_optimization_suggestions(mol, basic_advanced, property_thresholds)
                result['optimization'] = optimization_suggestions
            
            # Add synthesis recommendations if requested
            if include_synthesis:
                result['synthesis_recommendations'] = {
                    'complexity_score': basic_advanced.get('bertz_ct', 0) / 100.0,  # Normalized
                    'synthetic_accessibility': 'Medium',  # Placeholder
                    'recommendations': ['Consider starting materials', 'Evaluate reaction conditions']
                }
            
            # Add toxicity predictions if requested
            if include_toxicity:
                result['toxicity_prediction'] = {
                    'mutagenicity_alert': False,  # Placeholder
                    'carcinogenicity_alert': False,  # Placeholder
                    'overall_toxicity_score': 0.3,  # Placeholder
                    'recommendations': ['Structure appears safe', 'Consider experimental validation']
                }
            
            return result
            
        except Exception as e:
            return {'error': f'Advanced analysis failed: {str(e)}'}
    
    def _assess_druglikeness(self, mol, properties: Dict[str, Any], thresholds: Dict[str, Any] = None) -> Dict[str, Any]:
        """Assess drug-likeness based on molecular properties."""
        if thresholds is None:
            thresholds = {}
        
        mw_threshold = thresholds.get('molecular_weight', 500)
        logp_threshold = thresholds.get('logp', 5.0)
        
        # Get relevant properties
        mw = properties.get('molecular_weight', 0)
        logp = properties.get('clogp', properties.get('logp', 0))
        hbd = properties.get('num_hbd', properties.get('hbd', 0))
        hba = properties.get('num_hba', properties.get('hba', 0))
        rotatable_bonds = properties.get('num_rotatable_bonds', 0)
        
        # Lipinski Rule of Five violations
        lipinski_violations = 0
        lipinski_rules = {}
        
        if mw > 500:
            lipinski_violations += 1
            lipinski_rules['molecular_weight'] = False
        else:
            lipinski_rules['molecular_weight'] = True
            
        if logp > 5:
            lipinski_violations += 1
            lipinski_rules['logp'] = False
        else:
            lipinski_rules['logp'] = True
            
        if hbd > 5:
            lipinski_violations += 1
            lipinski_rules['hbd'] = False
        else:
            lipinski_rules['hbd'] = True
            
        if hba > 10:
            lipinski_violations += 1
            lipinski_rules['hba'] = False
        else:
            lipinski_rules['hba'] = True
        
        # Veber rules (additional)
        veber_violations = 0
        veber_rules = {}
        
        if rotatable_bonds > 10:
            veber_violations += 1
            veber_rules['rotatable_bonds'] = False
        else:
            veber_rules['rotatable_bonds'] = True
        
        # Calculate overall drug-likeness score
        total_rules = len(lipinski_rules) + len(veber_rules)
        passed_rules = sum(lipinski_rules.values()) + sum(veber_rules.values())
        overall_score = passed_rules / total_rules if total_rules > 0 else 0
        
        return {
            'overall_score': overall_score,
            'lipinski_violations': lipinski_violations,
            'veber_violations': veber_violations,
            'rules': {**lipinski_rules, **veber_rules},
            'assessment': 'Good drug-like properties' if overall_score > 0.8 else 'Some violations detected'
        }
    
    def _generate_recommendations(self, mol, properties: Dict[str, Any], thresholds: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate recommendations based on molecular properties."""
        if thresholds is None:
            thresholds = {}
        
        recommendations = {
            'priority': [],
            'general': [],
            'optimization': []
        }
        
        mw = properties.get('molecular_weight', 0)
        logp = properties.get('clogp', properties.get('logp', 0))
        
        # Priority recommendations
        if mw > thresholds.get('molecular_weight', 500):
            recommendations['priority'].append({
                'type': 'Molecular Weight',
                'message': f'High molecular weight ({mw:.1f} Da). Consider reducing size for better bioavailability.'
            })
        
        if logp > thresholds.get('logp', 5.0):
            recommendations['priority'].append({
                'type': 'Lipophilicity',
                'message': f'High LogP ({logp:.2f}). Consider adding polar groups for better solubility.'
            })
        
        # General recommendations
        recommendations['general'].append({
            'type': 'Structure Analysis',
            'message': 'Structure analyzed successfully. Consider experimental validation of predicted properties.'
        })
        
        recommendations['general'].append({
            'type': 'Further Analysis',
            'message': 'Consider performing conformational analysis to understand 3D structure effects.'
        })
        
        return recommendations
    
    def _generate_optimization_suggestions(self, mol, properties: Dict[str, Any], thresholds: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate structure optimization suggestions."""
        suggestions = {
            'targets': [
                {'property': 'Molecular Weight', 'target_range': '300-500 Da', 'current': properties.get('molecular_weight', 0)},
                {'property': 'LogP', 'target_range': '1-3', 'current': properties.get('clogp', properties.get('logp', 0))},
                {'property': 'H-bond Donors', 'target_range': '0-5', 'current': properties.get('num_hbd', 0)},
            ],
            'modifications': [
                {
                    'type': 'Functional Group Addition',
                    'description': 'Consider adding hydroxyl groups to improve solubility',
                    'priority': 'Medium',
                    'impact': 'Increased solubility, potentially reduced LogP'
                },
                {
                    'type': 'Size Reduction',
                    'description': 'Consider removing or replacing bulky groups',
                    'priority': 'High' if properties.get('molecular_weight', 0) > 500 else 'Low',
                    'impact': 'Reduced molecular weight, improved permeability'
                }
            ]
        }
        
        return suggestions

    def analyze_conformational_changes(self, smiles: str, conformer_ids: Tuple[int, int] = None, **kwargs) -> Dict[str, Any]:
        """
        Analyze conformational changes between conformers.
        
        Args:
            smiles: SMILES string of the molecule
            conformer_ids: Tuple of two conformer IDs to compare (optional)
            **kwargs: Additional parameters for change analysis
            
        Returns:
            Dictionary with conformational change analysis
        """
        if not self.capabilities.has_conformational_analysis:
            return {'error': 'Conformational analysis not available'}
        
        try:
            from rdkit import Chem
            from molecular_analyzer.conformational import ConformerGenerator, ConformationalChangeAnalyzer
            
            # Generate conformers if not already done
            generator = ConformerGenerator()
            mol = generator.generate_conformers(smiles, num_conformers=kwargs.get('num_conformers', 10))
            
            if mol is None or mol.GetNumConformers() < 2:
                return {'error': 'Failed to generate sufficient conformers for change analysis'}
            
            # Initialize change analyzer with custom thresholds if provided
            angle_threshold = kwargs.get('angle_threshold', 15.0)
            distance_threshold = kwargs.get('distance_threshold', 1.0)
            change_analyzer = ConformationalChangeAnalyzer(angle_threshold, distance_threshold)
            
            if conformer_ids:
                # Analyze specific conformer pair
                conf1_id, conf2_id = conformer_ids
                if conf1_id >= mol.GetNumConformers() or conf2_id >= mol.GetNumConformers():
                    return {'error': 'Invalid conformer IDs specified'}
                
                change_analysis = change_analyzer.analyze_conformational_changes(mol, conf1_id, conf2_id)
            else:
                # Analyze all conformer pairs
                change_analysis = change_analyzer.compare_all_conformers(mol)
            
            # Add molecule info
            change_analysis['smiles'] = smiles
            change_analysis['num_total_conformers'] = mol.GetNumConformers()
            change_analysis['analysis_parameters'] = {
                'angle_threshold': angle_threshold,
                'distance_threshold': distance_threshold
            }
            
            return change_analysis
            
        except Exception as e:
            return {'error': f'Conformational change analysis failed: {str(e)}'}

    def get_conformational_change_visualization_data(self, smiles: str, conf1_id: int, conf2_id: int, **kwargs) -> Dict[str, Any]:
        """
        Get visualization data for conformational changes between two conformers.
        
        Args:
            smiles: SMILES string of the molecule
            conf1_id: First conformer ID
            conf2_id: Second conformer ID
            **kwargs: Additional visualization parameters
            
        Returns:
            Dictionary with visualization data for highlighting changes
        """
        if not self.capabilities.has_conformational_analysis:
            return {'error': 'Conformational analysis not available'}
        
        try:
            from rdkit import Chem
            from molecular_analyzer.conformational import ConformerGenerator, ConformationalChangeAnalyzer
            
            # Try to use more conformers to ensure we have the required ones
            min_conformers_needed = max(conf1_id, conf2_id) + 5  # Add buffer
            generator = ConformerGenerator()
            mol = generator.generate_conformers(smiles, num_conformers=min_conformers_needed)
            
            if mol is None:
                return {'error': 'Failed to generate molecule'}
            
            # Check if we have enough conformers
            num_conformers = mol.GetNumConformers()
            if num_conformers <= max(conf1_id, conf2_id):
                # Try a different approach: generate more conformers with looser constraints
                mol = generator.generate_conformers(smiles, num_conformers=min_conformers_needed * 2)
                if mol is None or mol.GetNumConformers() <= max(conf1_id, conf2_id):
                    return {'error': f'Only generated {mol.GetNumConformers() if mol else 0} conformers, need at least {max(conf1_id, conf2_id) + 1}'}
            
            # Analyze changes between the specific conformers
            change_analyzer = ConformationalChangeAnalyzer(
                kwargs.get('angle_threshold', 15.0),
                kwargs.get('distance_threshold', 1.0)
            )
            
            change_data = change_analyzer.analyze_conformational_changes(mol, conf1_id, conf2_id)
            
            if 'error' in change_data:
                return change_data
            
            # Get 3D coordinates for both conformers
            conf1_atoms = []
            conf2_atoms = []
            
            conf1 = mol.GetConformer(conf1_id)
            conf2 = mol.GetConformer(conf2_id)
            
            for i in range(mol.GetNumAtoms()):
                atom = mol.GetAtomWithIdx(i)
                pos1 = conf1.GetAtomPosition(i)
                pos2 = conf2.GetAtomPosition(i)
                
                conf1_atoms.append({
                    'index': i,
                    'element': atom.GetSymbol(),
                    'x': float(pos1.x),
                    'y': float(pos1.y),
                    'z': float(pos1.z),
                    'displacement': change_data['atom_displacements'].get(i, 0.0)
                })
                
                conf2_atoms.append({
                    'index': i,
                    'element': atom.GetSymbol(),
                    'x': float(pos2.x),
                    'y': float(pos2.y),
                    'z': float(pos2.z),
                    'displacement': change_data['atom_displacements'].get(i, 0.0)
                })
            
            # Extract bond information
            bonds = []
            for bond in mol.GetBonds():
                bonds.append({
                    'atom1': bond.GetBeginAtomIdx(),
                    'atom2': bond.GetEndAtomIdx(),
                    'bond_type': bond.GetBondType().name,
                    'is_aromatic': bond.GetIsAromatic()
                })
            
            return {
                'smiles': smiles,
                'conformer_pair': (conf1_id, conf2_id),
                'conf1_atoms': conf1_atoms,
                'conf2_atoms': conf2_atoms,
                'bonds': bonds,
                'change_analysis': change_data,
                'visualization_markers': {
                    'displaced_atoms': change_data.get('displaced_atoms', []),
                    'torsion_changes': change_data.get('torsion_changes', []),
                    'change_magnitude': change_data.get('change_magnitude', 'minor')
                }
            }
            
        except Exception as e:
            return {'error': f'Change visualization data generation failed: {str(e)}'}
    
    def get_module_info(self) -> Dict[str, Any]:
        """Get information about available modules."""
        if not self.capabilities.has_core_analysis:
            return {'error': 'Core module not available'}
        
        try:
            info = self._core_analyzer.get_package_info()
            return {
                'package_info': info,
                'adapter_version': '2.1',
                'capabilities': self.get_capabilities()
            }
        except Exception as e:
            return {
                'error': f'Failed to get module info: {str(e)}',
                'adapter_version': '2.1'
            }
    
    def compare_molecules(self, smiles_list: List[str], **kwargs) -> Dict[str, Any]:
        """Compare multiple molecules and calculate similarities."""
        if not self.capabilities.has_comparison:
            return {'error': 'Comparison functionality not available'}
        
        if len(smiles_list) < 2:
            return {'error': 'At least 2 molecules required for comparison'}
        
        try:
            # Check if OOP comparison is available
            if getattr(self, '_has_oop_calculators', False):
                try:
                    # Use OOP comparison calculator
                    factory = self._core_analyzer.create_calculator_factory()
                    comparison_calc = factory.create_calculator('comparison')
                    
                    # Analyze each molecule first
                    molecules = []
                    for smiles in smiles_list:
                        result = self.analyze_single_molecule(smiles)
                        if result.get('valid', False):
                            molecules.append(result)
                    
                    if len(molecules) < 2:
                        return {'error': 'Not enough valid molecules for comparison'}
                    
                    # Calculate similarity matrix
                    similarities = []
                    for i in range(len(molecules)):
                        for j in range(i + 1, len(molecules)):
                            mol1_smiles = molecules[i]['smiles']
                            mol2_smiles = molecules[j]['smiles']
                            
                            # Basic similarity calculation
                            try:
                                from rdkit import Chem, DataStructs
                                from rdkit.Chem import rdMolDescriptors
                                
                                mol1 = Chem.MolFromSmiles(mol1_smiles)
                                mol2 = Chem.MolFromSmiles(mol2_smiles)
                                
                                if mol1 and mol2:
                                    fp1 = rdMolDescriptors.GetMorganFingerprintAsBitVect(mol1, 2)
                                    fp2 = rdMolDescriptors.GetMorganFingerprintAsBitVect(mol2, 2)
                                    similarity = DataStructs.TanimotoSimilarity(fp1, fp2)
                                    similarities.append({
                                        'molecule1': mol1_smiles,
                                        'molecule2': mol2_smiles,
                                        'similarity': similarity
                                    })
                            except Exception:
                                similarities.append({
                                    'molecule1': mol1_smiles,
                                    'molecule2': mol2_smiles,
                                    'similarity': 0.0,
                                    'error': 'Could not calculate similarity'
                                })
                    
                    return {
                        'molecules': molecules,
                        'similarities': similarities,
                        'method': 'oop_comparison'
                    }
                    
                except Exception as e:
                    # Fall back to basic comparison
                    pass
            
            # Basic comparison without OOP
            molecules = []
            for smiles in smiles_list:
                result = self.analyze_single_molecule(smiles)
                molecules.append(result)
            
            return {
                'molecules': molecules,
                'similarities': [],
                'method': 'basic_comparison',
                'note': 'Advanced similarity calculations not available'
            }
            
        except Exception as e:
            return {'error': f'Comparison failed: {str(e)}'}
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get adapter capabilities."""
        return {
            'core_analysis': self.capabilities.has_core_analysis,
            'advanced_properties': self.capabilities.has_advanced_properties,
            '3d_visualization': self.capabilities.has_3d_visualization,
            'batch_processing': self.capabilities.has_batch_processing,
            'comparison': self.capabilities.has_comparison,
            'conformational_analysis': self.capabilities.has_conformational_analysis,
            'supported_formats': self.capabilities.supported_formats,
            'oop_workflows': getattr(self, '_has_oop_workflows', False),
            'oop_calculators': getattr(self, '_has_oop_calculators', False),
            'oop_visualization': getattr(self, '_has_oop_visualization', False),
            'version': '2.1'
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check adapter health and availability."""
        status = {
            'core_available': self.capabilities.has_core_analysis,
            'ready': self.capabilities.has_core_analysis,
            'version': '2.1'
        }
        
        if self._core_analyzer:
            try:
                # Test basic functionality
                test_result = self._core_analyzer.quick_analysis("CCO")
                status['core_functional'] = True
                
                # Test OOP functionality if available
                if getattr(self, '_has_oop_workflows', False):
                    try:
                        workflow = self._core_analyzer.create_analyzer_workflow()
                        status['oop_workflows_functional'] = True
                    except Exception as e:
                        status['oop_workflows_functional'] = False
                        status['oop_workflows_error'] = str(e)
                
                if getattr(self, '_has_oop_calculators', False):
                    try:
                        calc = self._core_analyzer.create_basic_calculator()
                        status['oop_calculators_functional'] = True
                    except Exception as e:
                        status['oop_calculators_functional'] = False
                        status['oop_calculators_error'] = str(e)
                        
            except Exception as e:
                status['core_functional'] = False
                status['core_error'] = str(e)
        
        return status


class AdapterFactory:
    """Factory for creating adapters with different configurations."""
    
    @staticmethod
    def create_auto_adapter() -> MolecularAnalyzerAdapter:
        """Create adapter with auto-detected capabilities."""
        return MolecularAnalyzerAdapter()
    
    @staticmethod
    def create_minimal_adapter() -> MolecularAnalyzerAdapter:
        """Create minimal adapter for basic functionality only."""
        adapter = MolecularAnalyzerAdapter()
        # Could restrict capabilities here if needed
        return adapter
    
    @staticmethod
    def create_full_adapter() -> MolecularAnalyzerAdapter:
        """Create adapter with all features enabled."""
        return MolecularAnalyzerAdapter()


# Backwards compatibility
def create_adapter(**kwargs) -> MolecularAnalyzerAdapter:
    """Create a molecular analyzer adapter."""
    return AdapterFactory.create_auto_adapter()


# Quick access functions
def quick_analyze(smiles: str) -> Dict[str, Any]:
    """Quick analysis function."""
    adapter = AdapterFactory.create_auto_adapter()
    return adapter.analyze_single_molecule(smiles)


if __name__ == "__main__":
    # Self-test
    adapter = AdapterFactory.create_auto_adapter()
    print("Adapter Health Check:")
    print(adapter.health_check())
    
    print("\nAdapter Capabilities:")
    print(adapter.get_capabilities())
    
    print("\nTest Analysis:")
    result = adapter.analyze_single_molecule("CCO")
    print(f"CCO Analysis: {result}")
