"""
Molecular Comparison Module

This module provides comprehensive tools for comparing multiple molecules
including property analysis, similarity calculations, visualization, and
interactive dashboards for molecular comparison.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Union
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem, Draw
from rdkit.Chem.rdMolDescriptors import CalcExactMolWt, CalcTPSA, CalcNumHBD, CalcNumHBA
from rdkit.Chem import Descriptors
import io
import base64


def calculate_property_differences(molecules_dict: Dict[str, str], 
                                 reference_molecule: Optional[str] = None) -> pd.DataFrame:
    """
    Calculate property differences between molecules.
    
    Args:
        molecules_dict (Dict[str, str]): Dictionary mapping molecule names to SMILES
        reference_molecule (Optional[str]): Reference molecule name for comparison
        
    Returns:
        pd.DataFrame: DataFrame with property differences
        
    Examples:
        >>> molecules = {"aspirin": "CC(=O)OC1=CC=CC=C1C(=O)O", "ibuprofen": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O"}
        >>> df = calculate_property_differences(molecules)
        >>> "molecular_weight" in df.columns
        True
    """
    from .calculator import MolecularAnalyzer
    
    analyzer = MolecularAnalyzer()
    properties_data = []
    
    # Calculate properties for all molecules
    for name, smiles in molecules_dict.items():
        try:
            props = analyzer.calculate_properties(smiles)
            props['molecule_name'] = name
            properties_data.append(props)
        except Exception as e:
            properties_data.append({
                'molecule_name': name,
                'smiles': smiles,
                'error': str(e)
            })
    
    df = pd.DataFrame(properties_data)
    
    # If reference molecule is specified, calculate differences
    if reference_molecule and reference_molecule in molecules_dict:
        ref_row = df[df['molecule_name'] == reference_molecule]
        if not ref_row.empty:
            numeric_cols = ['molecular_weight', 'logP', 'tpsa', 'hbd', 'hba', 
                          'num_atoms', 'num_bonds', 'num_rings', 'num_rotatable_bonds']
            
            for col in numeric_cols:
                if col in df.columns:
                    ref_value = ref_row[col].iloc[0]
                    df[f'{col}_diff'] = df[col] - ref_value
                    df[f'{col}_pct_diff'] = ((df[col] - ref_value) / ref_value * 100).round(2)
    
    return df


def calculate_similarity_matrix(molecules_dict: Dict[str, str], 
                              method: str = "tanimoto") -> pd.DataFrame:
    """Calculate molecular similarity matrix using fingerprints."""
    mol_data = {}

    for name, smiles in molecules_dict.items():
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            mol = Chem.AddHs(mol)  # Add explicit hydrogens
            fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
            mol_data[name] = fp

    if len(mol_data) < 2:
        return None

    names = list(mol_data.keys())
    n_mols = len(names)
    similarity_matrix = np.zeros((n_mols, n_mols))

    for i, name1 in enumerate(names):
        for j, name2 in enumerate(names):
            if i == j:
                similarity_matrix[i, j] = 1.0
            else:
                fp1 = mol_data[name1]
                fp2 = mol_data[name2]

                if method == "tanimoto":
                    similarity = DataStructs.TanimotoSimilarity(fp1, fp2)
                elif method == "dice":
                    similarity = DataStructs.DiceSimilarity(fp1, fp2)
                else:
                    similarity = DataStructs.TanimotoSimilarity(fp1, fp2)

                similarity_matrix[i, j] = similarity

    return pd.DataFrame(similarity_matrix, index=names, columns=names)


def find_most_similar_pairs(similarity_matrix: pd.DataFrame, 
                           n_pairs: int = 3) -> List[Dict[str, Any]]:
    """Find the most similar molecule pairs from similarity matrix."""
    if similarity_matrix is None:
        return []

    similarities = []
    molecules = similarity_matrix.index.tolist()

    for i, mol1 in enumerate(molecules):
        for j, mol2 in enumerate(molecules):
            if i < j:
                sim = similarity_matrix.iloc[i, j]
                similarities.append({
                    'molecule1': mol1,
                    'molecule2': mol2,
                    'similarity': sim
                })

    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    return similarities[:n_pairs]


def compare_drug_likeness(molecules_dict: Dict[str, str]) -> Dict[str, Any]:
    """
    Compare drug-likeness across multiple molecules.
    
    Args:
        molecules_dict (Dict[str, str]): Dictionary mapping molecule names to SMILES
        
    Returns:
        Dict[str, Any]: Drug-likeness comparison results
        
    Examples:
        >>> molecules = {"aspirin": "CC(=O)OC1=CC=CC=C1C(=O)O"}
        >>> result = compare_drug_likeness(molecules)
        >>> "individual_results" in result
        True
    """
    from .calculator import MolecularAnalyzer
    
    analyzer = MolecularAnalyzer()
    results = {}
    drug_like_count = 0

    for name, smiles in molecules_dict.items():
        try:
            props = analyzer.calculate_properties(smiles)
            drug_like = props.get('drug_like', False)
            violations = props.get('lipinski_violations', 0)

            results[name] = {
                'drug_like': drug_like,
                'violations': violations,
                'assessment': props.get('assessment', {}).get('overall', 'Unknown'),
                'molecular_weight': props.get('molecular_weight', 0),
                'logP': props.get('logP', 0),
                'hbd': props.get('hbd', 0),
                'hba': props.get('hba', 0),
                'tpsa': props.get('tpsa', 0)
            }

            if drug_like:
                drug_like_count += 1
        except Exception as e:
            results[name] = {'error': str(e)}

    return {
        'individual_results': results,
        'drug_like_count': drug_like_count,
        'total_molecules': len(results),
        'drug_like_percentage': (drug_like_count / len(results) * 100) if results else 0
    }


def create_comparison_dashboard(molecules_dict: Dict[str, str]) -> Dict[str, Any]:
    """
    Create comprehensive comparison dashboard for multiple molecules.
    
    Args:
        molecules_dict (Dict[str, str]): Dictionary mapping molecule names to SMILES
        
    Returns:
        Dict[str, Any]: Dashboard components including plots and data
        
    Examples:
        >>> molecules = {"aspirin": "CC(=O)OC1=CC=CC=C1C(=O)O"}
        >>> dashboard = create_comparison_dashboard(molecules)
        >>> "property_comparison_plot" in dashboard
        True
    """
    # Get property differences
    prop_df = calculate_property_differences(molecules_dict)
    
    # Get similarity matrix
    similarity_matrix = calculate_similarity_matrix(molecules_dict)
    
    # Get drug-likeness comparison
    drug_likeness = compare_drug_likeness(molecules_dict)
    
    dashboard = {
        'property_data': prop_df,
        'similarity_matrix': similarity_matrix,
        'drug_likeness': drug_likeness,
        'property_comparison_plot': create_property_comparison_plot(prop_df),
        'similarity_heatmap': create_similarity_heatmap(similarity_matrix),
        'drug_likeness_plot': create_drug_likeness_plot(drug_likeness),
        'radar_chart': create_radar_comparison_chart(prop_df),
        'molecular_structures': create_structure_comparison(molecules_dict)
    }
    
    return dashboard


def create_property_comparison_plot(prop_df: pd.DataFrame) -> go.Figure:
    """
    Create property comparison bar plot.
    
    Args:
        prop_df (pd.DataFrame): DataFrame with molecular properties
        
    Returns:
        go.Figure: Plotly figure with property comparison
    """
    if prop_df.empty:
        return go.Figure()
    
    properties = ['molecular_weight', 'logP', 'tpsa', 'hbd', 'hba', 'num_atoms']
    available_props = [prop for prop in properties if prop in prop_df.columns]
    
    if not available_props:
        return go.Figure()
    
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=available_props,
        specs=[[{"secondary_y": False}]*3,
               [{"secondary_y": False}]*3]
    )
    
    colors = px.colors.qualitative.Set3
    
    for i, prop in enumerate(available_props[:6]):
        row = (i // 3) + 1
        col = (i % 3) + 1
        
        for j, (idx, row_data) in enumerate(prop_df.iterrows()):
            if 'error' not in row_data:
                fig.add_trace(
                    go.Bar(
                        x=[row_data['molecule_name']],
                        y=[row_data[prop]],
                        name=row_data['molecule_name'],
                        marker_color=colors[j % len(colors)],
                        showlegend=(i == 0),
                        legendgroup=row_data['molecule_name']
                    ),
                    row=row, col=col
                )
    
    fig.update_layout(
        title="Molecular Property Comparison",
        height=800,
        font=dict(size=12)
    )
    
    return fig


def create_similarity_heatmap(similarity_matrix: pd.DataFrame) -> go.Figure:
    """
    Create similarity heatmap.
    
    Args:
        similarity_matrix (pd.DataFrame): Similarity matrix
        
    Returns:
        go.Figure: Plotly heatmap figure
    """
    if similarity_matrix is None or similarity_matrix.empty:
        return go.Figure()
    
    fig = px.imshow(
        similarity_matrix,
        color_continuous_scale='Viridis',
        aspect='auto',
        title='Molecular Similarity Matrix',
        labels={'color': 'Similarity Score'}
    )
    
    # Add similarity values as text
    for i in range(len(similarity_matrix.index)):
        for j in range(len(similarity_matrix.columns)):
            fig.add_annotation(
                x=j, y=i,
                text=f"{similarity_matrix.iloc[i, j]:.3f}",
                showarrow=False,
                font=dict(color="white" if similarity_matrix.iloc[i, j] < 0.5 else "black")
            )
    
    fig.update_layout(
        height=500,
        width=500,
        font=dict(size=12)
    )
    
    return fig


def create_drug_likeness_plot(drug_likeness: Dict[str, Any]) -> go.Figure:
    """
    Create drug-likeness comparison plot.
    
    Args:
        drug_likeness (Dict[str, Any]): Drug-likeness comparison results
        
    Returns:
        go.Figure: Plotly figure with drug-likeness comparison
    """
    if 'individual_results' not in drug_likeness:
        return go.Figure()
    
    results = drug_likeness['individual_results']
    
    molecules = []
    violations = []
    drug_like_status = []
    colors = []
    
    for name, data in results.items():
        if 'error' not in data:
            molecules.append(name)
            violations.append(data.get('violations', 0))
            drug_like_status.append(data.get('drug_like', False))
            colors.append('green' if data.get('drug_like', False) else 'red')
    
    if not molecules:
        return go.Figure()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=molecules,
        y=violations,
        marker_color=colors,
        text=[f"{'Drug-like' if status else 'Not drug-like'}" for status in drug_like_status],
        textposition='auto',
        name='Lipinski Violations'
    ))
    
    fig.update_layout(
        title='Drug-likeness Assessment (Lipinski Rule of Five)',
        xaxis_title='Molecules',
        yaxis_title='Number of Violations',
        height=500,
        font=dict(size=12)
    )
    
    return fig


def create_radar_comparison_chart(prop_df: pd.DataFrame) -> go.Figure:
    """
    Create radar chart for property comparison.
    
    Args:
        prop_df (pd.DataFrame): DataFrame with molecular properties
        
    Returns:
        go.Figure: Plotly radar chart
    """
    if prop_df.empty:
        return go.Figure()
    
    properties = ['molecular_weight', 'logP', 'tpsa', 'hbd', 'hba', 'num_atoms']
    available_props = [prop for prop in properties if prop in prop_df.columns]
    
    if not available_props:
        return go.Figure()
    
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set3
    
    for i, (idx, row_data) in enumerate(prop_df.iterrows()):
        if 'error' not in row_data:
            # Normalize values for radar chart
            values = []
            for prop in available_props:
                val = row_data[prop]
                if isinstance(val, (int, float)):
                    values.append(val)
                else:
                    values.append(0)
            
            # Simple normalization (0-1 scale)
            if values:
                max_val = max(values) if max(values) > 0 else 1
                normalized_values = [v / max_val for v in values]
            else:
                normalized_values = [0] * len(available_props)
            
            fig.add_trace(go.Scatterpolar(
                r=normalized_values,
                theta=available_props,
                fill='toself',
                name=row_data['molecule_name'],
                line=dict(color=colors[i % len(colors)]),
                fillcolor=colors[i % len(colors)],
                opacity=0.6
            ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        showlegend=True,
        title="Molecular Properties Radar Chart",
        height=600,
        font=dict(size=12)
    )
    
    return fig


def create_structure_comparison(molecules_dict: Dict[str, str]) -> Dict[str, str]:
    """
    Create molecular structure images for comparison.
    
    Args:
        molecules_dict (Dict[str, str]): Dictionary mapping molecule names to SMILES
        
    Returns:
        Dict[str, str]: Dictionary mapping molecule names to base64-encoded images
    """
    structure_images = {}
    
    for name, smiles in molecules_dict.items():
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol:
                mol = Chem.AddHs(mol)  # Add explicit hydrogens
                # Generate 2D structure image
                img = Draw.MolToImage(mol, size=(300, 300))
                
                # Convert to base64
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                img_str = base64.b64encode(buffer.getvalue()).decode()
                structure_images[name] = img_str
        except Exception as e:
            structure_images[name] = f"Error generating structure: {str(e)}"
    
    return structure_images


def compare_molecules(molecules_dict: Dict[str, str]) -> Dict[str, Any]:
    """
    Compare multiple molecules and return their properties.
    
    Args:
        molecules_dict (Dict[str, str]): Dictionary mapping molecule names to SMILES
        
    Returns:
        Dict[str, Any]: Dictionary with molecular properties for each molecule
        
    Examples:
        >>> molecules = {"aspirin": "CC(=O)OC1=CC=CC=C1C(=O)O", "ibuprofen": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O"}
        >>> results = compare_molecules(molecules)
        >>> "aspirin" in results
        True
    """
    from .calculator import MolecularAnalyzer
    
    analyzer = MolecularAnalyzer()
    comparison_results = {}
    
    for name, smiles in molecules_dict.items():
        try:
            props = analyzer.calculate_properties(smiles)
            comparison_results[name] = props
        except Exception as e:
            comparison_results[name] = {
                'error': str(e),
                'smiles': smiles
            }
    
    return comparison_results


def create_comprehensive_comparison_report(molecules_dict: Dict[str, str]) -> Dict[str, Any]:
    """
    Create comprehensive comparison report with all analysis components.
    
    Args:
        molecules_dict (Dict[str, str]): Dictionary mapping molecule names to SMILES
        
    Returns:
        Dict[str, Any]: Comprehensive comparison report
        
    Examples:
        >>> molecules = {"aspirin": "CC(=O)OC1=CC=CC=C1C(=O)O"}
        >>> report = create_comprehensive_comparison_report(molecules)
        >>> "dashboard" in report
        True
    """
    dashboard = create_comparison_dashboard(molecules_dict)
    
    # Add summary statistics
    prop_df = dashboard['property_data']
    summary_stats = {}
    
    if not prop_df.empty:
        numeric_cols = ['molecular_weight', 'logP', 'tpsa', 'hbd', 'hba', 'num_atoms']
        for col in numeric_cols:
            if col in prop_df.columns:
                valid_data = prop_df[col].dropna()
                if len(valid_data) > 0:
                    summary_stats[col] = {
                        'mean': float(valid_data.mean()),
                        'std': float(valid_data.std()),
                        'min': float(valid_data.min()),
                        'max': float(valid_data.max()),
                        'range': float(valid_data.max() - valid_data.min())
                    }
    
    # Add insights
    insights = []
    
    # Drug-likeness insights
    drug_data = dashboard['drug_likeness']
    if drug_data['total_molecules'] > 0:
        insights.append({
            'category': 'Drug-likeness',
            'message': f"{drug_data['drug_like_count']}/{drug_data['total_molecules']} molecules are drug-like ({drug_data['drug_like_percentage']:.1f}%)"
        })
    
    # Similarity insights
    similarity_matrix = dashboard['similarity_matrix']
    if similarity_matrix is not None and not similarity_matrix.empty:
        # Find most similar pair
        max_sim = 0
        most_similar_pair = None
        
        for i in range(len(similarity_matrix.index)):
            for j in range(i + 1, len(similarity_matrix.columns)):
                sim = similarity_matrix.iloc[i, j]
                if sim > max_sim:
                    max_sim = sim
                    most_similar_pair = (similarity_matrix.index[i], similarity_matrix.columns[j])
        
        if most_similar_pair:
            insights.append({
                'category': 'Similarity',
                'message': f"Most similar molecules: {most_similar_pair[0]} and {most_similar_pair[1]} (similarity: {max_sim:.3f})"
            })
    
    report = {
        'dashboard': dashboard,
        'summary_statistics': summary_stats,
        'insights': insights,
        'molecule_count': len(molecules_dict),
        'analysis_timestamp': pd.Timestamp.now().isoformat()
    }
    
    return report


# Comparison utilities
COMPARISON_PROPERTIES = [
    'molecular_weight', 'logP', 'tpsa', 'num_atoms', 'num_bonds',
    'num_rings', 'hbd', 'hba', 'num_rotatable_bonds'
]

SIMILARITY_METHODS = ["tanimoto", "dice", "cosine"]

if __name__ == "__main__":
    # Test the module
    test_molecules = {
        "Aspirin": "CC(=O)OC1=CC=CC=C1C(=O)O",
        "Ibuprofen": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O"
    }

    similarity = calculate_similarity_matrix(test_molecules)
    if similarity is not None:
        print("✅ Comparison module working correctly!")
        print(similarity)
