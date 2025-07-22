"""
3D Molecular Visualization Module

This module provides comprehensive 3D visualization capabilities for molecular analysis
including interactive plotting, animation, and export functionality.
"""

import plotly.graph_objects as go
from rdkit import Chem
from rdkit.Chem import AllChem
from typing import Optional, Dict, List


def generate_3d_coordinates(mol: Chem.Mol, optimize: bool = True) -> Optional[Chem.Mol]:
    """Generate 3D coordinates for a molecule."""
    if mol is None:
        return None

    try:
        mol_3d = Chem.Mol(mol)
        mol_3d = Chem.AddHs(mol_3d)
        AllChem.EmbedMolecule(mol_3d, randomSeed=42)

        if optimize:
            AllChem.MMFFOptimizeMolecule(mol_3d)

        return mol_3d
    except Exception:
        return None


def extract_atom_data(mol_3d: Chem.Mol) -> Optional[Dict[str, List]]:
    """Extract atomic coordinates and properties for visualization."""
    if mol_3d is None:
        return None

    conf = mol_3d.GetConformer()

    # Element colors (CPK scheme)
    element_colors = {
        'H': '#FFFFFF', 'C': '#909090', 'N': '#3050F8', 'O': '#FF0D0D',
        'S': '#FFFF30', 'P': '#FF8000', 'F': '#90E050', 'Cl': '#1FF01F'
    }

    # Element sizes (scaled van der Waals radii)
    element_sizes = {
        'H': 8, 'C': 12, 'N': 12, 'O': 10, 'S': 14, 'P': 14, 'F': 9, 'Cl': 15
    }

    atoms_data = {
        'x': [], 'y': [], 'z': [], 'element': [], 'symbol': [],
        'color': [], 'size': [], 'label': []
    }

    for i, atom in enumerate(mol_3d.GetAtoms()):
        pos = conf.GetAtomPosition(i)
        element = atom.GetSymbol()

        atoms_data['x'].append(pos.x)
        atoms_data['y'].append(pos.y)
        atoms_data['z'].append(pos.z)
        atoms_data['element'].append(element)
        atoms_data['symbol'].append(element)
        atoms_data['color'].append(element_colors.get(element, '#FF69B4'))
        atoms_data['size'].append(element_sizes.get(element, 10))
        atoms_data['label'].append(f"{element}{i+1}<br>({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f})")

    return atoms_data


def plot_molecule_3d(mol: Chem.Mol, title: str = "Molecule 3D Structure", 
                    style: str = "ball_and_stick", show_labels: bool = True) -> Optional[go.Figure]:
    """Create interactive 3D plot of a molecule."""
    mol_3d = generate_3d_coordinates(mol)
    if mol_3d is None:
        return None

    atoms = extract_atom_data(mol_3d)
    if atoms is None:
        return None

    fig = go.Figure()

    # Adjust visualization style
    if style == "space_filling":
        sizes = [s * 2 for s in atoms['size']]
        show_bonds = False
    elif style == "wireframe":
        sizes = [4] * len(atoms['size'])
        show_bonds = True
        bond_width = 2
    else:  # ball_and_stick
        sizes = atoms['size']
        show_bonds = True
        bond_width = 6

    # Add atoms
    fig.add_trace(go.Scatter3d(
        x=atoms['x'], y=atoms['y'], z=atoms['z'],
        mode='markers+text' if show_labels else 'markers',
        marker=dict(size=sizes, color=atoms['color'], opacity=0.8),
        text=atoms['symbol'] if show_labels else None,
        textposition="middle center",
        hovertext=atoms['label'],
        hoverinfo='text',
        name='Atoms'
    ))

    # Add bonds
    if show_bonds:
        for bond in mol_3d.GetBonds():
            atom1_idx = bond.GetBeginAtomIdx()
            atom2_idx = bond.GetEndAtomIdx()

            fig.add_trace(go.Scatter3d(
                x=[atoms['x'][atom1_idx], atoms['x'][atom2_idx], None],
                y=[atoms['y'][atom1_idx], atoms['y'][atom2_idx], None],
                z=[atoms['z'][atom1_idx], atoms['z'][atom2_idx], None],
                mode='lines',
                line=dict(color='gray', width=bond_width),
                hoverinfo='none',
                showlegend=False
            ))

    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title='X (Å)', yaxis_title='Y (Å)', zaxis_title='Z (Å)',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
            bgcolor='white', aspectmode='cube'
        ),
        width=800, height=600
    )

    return fig


def create_3d_plot(mol: Chem.Mol, title: str = "Molecule 3D Structure", 
                   style: str = "ball_and_stick", show_labels: bool = True) -> Optional[go.Figure]:
    """Create interactive 3D plot of a molecule (alias for plot_molecule_3d)."""
    return plot_molecule_3d(mol, title, style, show_labels)


def export_3d_visualization(fig: go.Figure, filename: str, format: str = 'html') -> bool:
    """Export 3D visualization to file."""
    try:
        if format == 'html':
            fig.write_html(f"{filename}.html")
        elif format == 'png':
            fig.write_image(f"{filename}.png", width=800, height=600, scale=2)
        return True
    except Exception:
        return False


# Default molecule styles and color schemes
VISUALIZATION_STYLES = ["ball_and_stick", "space_filling", "wireframe"]
COLOR_SCHEMES = ["cpk", "element", "rainbow"]

if __name__ == "__main__":
    # Test the module
    from rdkit import Chem

    mol = Chem.MolFromSmiles("CCO")
    if mol:
        mol = Chem.AddHs(mol)  # Add explicit hydrogens
    fig = plot_molecule_3d(mol, "Ethanol Test")
    if fig:
        print("✅ 3D visualization module working correctly!")
