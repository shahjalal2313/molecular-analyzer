"""
3D Molecule Renderer Component for Molecular Visualization

Provides interactive 3D molecular visualization with CPK coloring, atom sizing,
and bond highlighting using Plotly for enhanced molecular structure analysis.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union, Tuple
from ..base import BaseComponent


class Molecule3DComponent(BaseComponent):
    """
    3D molecular visualization component with CPK coloring and advanced styling.
    
    Features:
    - CPK color scheme for realistic atom representation
    - Proportional atom sizing based on van der Waals radii
    - Ring bond highlighting with different colors
    - Interactive 3D rotation and zoom
    - Customizable rendering styles
    - Export capabilities
    """
    
    def __init__(self, name: str = "3D Molecule Renderer", key_prefix: str = None):
        """
        Initialize the 3D molecule renderer component.
        
        Args:
            name: Component display name
            key_prefix: Unique key prefix for Streamlit widgets
        """
        super().__init__(name, key_prefix)
        
        # CPK color scheme for realistic atom representation
        self.element_colors = {
            'H': '#FFFFFF',   # White
            'C': '#222222',   # Black/Dark Gray
            'N': '#3050F8',   # Blue
            'O': '#FF0D0D',   # Red
            'S': '#FFFF30',   # Yellow
            'P': '#FF8000',   # Orange
            'F': '#90E050',   # Green
            'Cl': '#1FF01F',  # Green
            'Br': '#A62929',  # Brown
            'I': '#940094',   # Purple
            'B': '#FFB5B5',   # Pink
            'Si': '#F0C8A0',  # Beige
            'Fe': '#E06633',  # Orange-red
            'Ca': '#3DFF00',  # Bright green
            'Mg': '#8AFF00',  # Yellow-green
            'Na': '#AB5CF2',  # Purple
            'K': '#8F40D4',   # Purple
            'Al': '#BFA6A6',  # Gray
            'Zn': '#7D80B0',  # Blue-gray
            'Cu': '#C88033',  # Orange
            'Ni': '#50D050',  # Green
            'Co': '#F090A0',  # Pink
            'Mn': '#9C7AC7',  # Purple
            'Cr': '#8A99C7',  # Blue-gray
            'V': '#A6A6AB',   # Gray
            'Ti': '#BFC2C7',  # Light gray
            'Sc': '#E6E6E6',  # Very light gray
        }
        
        # Atom sizes based on van der Waals radii (scaled for visualization)
        self.element_sizes = {
            'H': 4,    # Even smaller for better proportions
            'C': 18,   # Larger
            'N': 16,   # Medium
            'O': 16,   # Medium
            'S': 20,   # Larger
            'P': 20,   # Larger
            'F': 16,   # Medium
            'Cl': 18,  # Larger
            'Br': 20,  # Larger
            'I': 22,   # Largest
            'B': 14,   # Smaller
            'Si': 22,  # Large
            'Fe': 16,  # Medium
            'Ca': 24,  # Very large
            'Mg': 18,  # Medium-large
            'Na': 26,  # Very large
            'K': 28,   # Largest
            'Al': 16,  # Medium
            'Zn': 16,  # Medium
            'Cu': 16,  # Medium
            'Ni': 16,  # Medium
            'Co': 16,  # Medium
            'Mn': 16,  # Medium
            'Cr': 16,  # Medium
            'V': 16,   # Medium
            'Ti': 16,  # Medium
            'Sc': 16,  # Medium
        }
        
        # Default visualization configuration
        self.viz_config = {
            'background_color': 'white',
            'atom_opacity': 0.85,
            'atom_border_width': 2,
            'atom_border_color': 'DarkSlateGrey',
            'regular_bond_color': '#404040',  # Darker single bonds
            'regular_bond_width': 8,  # Thicker bonds
            'ring_bond_color': '#9932CC',  # Purple aromatic bonds
            'ring_bond_width': 10,  # Thicker aromatic bonds
            'show_atom_labels': True,
            'show_ring_bonds': True,
            'camera_position': {'x': 1.5, 'y': 1.5, 'z': 1.5},
            'width': 800,
            'height': 600,
            'title': '3D Molecular Structure',
            'axis_labels': True,
            'show_legend': True,
            'visualization_style': 'Ball and Stick' # New default style
        }
    
    def configure_visualization(self,
                               background_color: str = 'white',
                               atom_opacity: float = 0.85,
                               atom_border_width: int = 2,
                               atom_border_color: str = 'DarkSlateGrey',
                               regular_bond_color: str = 'gray',
                               regular_bond_width: int = 4,
                               ring_bond_color: str = '#1976D2',
                               ring_bond_width: int = 7,
                               show_atom_labels: bool = True,
                               show_ring_bonds: bool = True,
                               camera_position: Dict[str, float] = None,
                               width: int = 800,
                               height: int = 600,
                               title: str = '3D Molecular Structure',
                               axis_labels: bool = True,
                               show_legend: bool = True) -> None:
        """
        Configure 3D visualization appearance and behavior.
        
        Args:
            background_color: Scene background color
            atom_opacity: Opacity of atom spheres (0-1)
            atom_border_width: Width of atom borders
            atom_border_color: Color of atom borders
            regular_bond_color: Color of regular bonds
            regular_bond_width: Width of regular bonds
            ring_bond_color: Color of ring bonds
            ring_bond_width: Width of ring bonds
            show_atom_labels: Whether to show atom element labels
            show_ring_bonds: Whether to highlight ring bonds
            camera_position: 3D camera position dict with x, y, z
            width: Chart width in pixels
            height: Chart height in pixels
            title: Chart title
            axis_labels: Whether to show axis labels
            show_legend: Whether to show legend
        """
        self.viz_config.update({
            'background_color': background_color,
            'atom_opacity': atom_opacity,
            'atom_border_width': atom_border_width,
            'atom_border_color': atom_border_color,
            'regular_bond_color': regular_bond_color,
            'regular_bond_width': regular_bond_width,
            'ring_bond_color': ring_bond_color,
            'ring_bond_width': ring_bond_width,
            'show_atom_labels': show_atom_labels,
            'show_ring_bonds': show_ring_bonds,
            'camera_position': camera_position or {'x': 1.5, 'y': 1.5, 'z': 1.5},
            'width': width,
            'height': height,
            'title': title,
            'axis_labels': axis_labels,
            'show_legend': show_legend
        })
    
    def validate_molecular_data(self, mol_data: Dict[str, Any]) -> bool:
        """
        Validate molecular data structure.
        
        Args:
            mol_data: Dictionary containing molecular data
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            if not isinstance(mol_data, dict):
                self.add_error("Molecular data must be a dictionary")
                return False
            
            required_keys = ['atoms', 'bonds']
            missing_keys = [key for key in required_keys if key not in mol_data]
            if missing_keys:
                self.add_error(f"Missing required keys: {missing_keys}")
                return False
            
            atoms = mol_data['atoms']
            bonds = mol_data['bonds']
            
            if not isinstance(atoms, list) or not atoms:
                self.add_error("Atoms must be a non-empty list")
                return False
            
            if not isinstance(bonds, list):
                self.add_error("Bonds must be a list")
                return False
            
            # Validate atom structure
            for i, atom in enumerate(atoms):
                if not isinstance(atom, dict):
                    self.add_error(f"Atom {i} must be a dictionary")
                    return False
                
                required_atom_keys = ['element', 'x', 'y', 'z']
                missing_atom_keys = [key for key in required_atom_keys if key not in atom]
                if missing_atom_keys:
                    self.add_error(f"Atom {i} missing required keys: {missing_atom_keys}")
                    return False
                
                # Validate coordinates are numeric
                for coord in ['x', 'y', 'z']:
                    if not isinstance(atom[coord], (int, float)):
                        self.add_error(f"Atom {i} coordinate {coord} must be numeric")
                        return False
            
            # Validate bond structure
            for i, bond in enumerate(bonds):
                if not isinstance(bond, dict):
                    self.add_error(f"Bond {i} must be a dictionary")
                    return False
                
                required_bond_keys = ['atom1', 'atom2']
                missing_bond_keys = [key for key in required_bond_keys if key not in bond]
                if missing_bond_keys:
                    self.add_error(f"Bond {i} missing required keys: {missing_bond_keys}")
                    return False
                
                # Validate atom indices
                atom1_idx = bond['atom1']
                atom2_idx = bond['atom2']
                
                if not isinstance(atom1_idx, int) or not isinstance(atom2_idx, int):
                    self.add_error(f"Bond {i} atom indices must be integers")
                    return False
                
                if atom1_idx < 0 or atom1_idx >= len(atoms):
                    self.add_error(f"Bond {i} atom1 index {atom1_idx} out of range")
                    return False
                
                if atom2_idx < 0 or atom2_idx >= len(atoms):
                    self.add_error(f"Bond {i} atom2 index {atom2_idx} out of range")
                    return False
            
            return True
            
        except Exception as e:
            self.add_error(f"Error validating molecular data: {str(e)}", e)
            return False
    
    def create_3d_visualization(self, mol_data: Dict[str, Any], custom_config: Dict = None) -> Optional[go.Figure]:
        """
        Create 3D molecular visualization.
        
        Args:
            mol_data: Dictionary containing molecular structure data
            custom_config: Additional visualization configuration
            
        Returns:
            Plotly figure object or None if error
        """
        try:
            # Validate molecular data
            if not self.validate_molecular_data(mol_data):
                return None
            
            # Apply custom configuration
            config = self.viz_config.copy()
            if custom_config:
                config.update(custom_config)
            
            atoms = mol_data['atoms']
            bonds = mol_data['bonds']
            ring_bonds = mol_data.get('ring_bonds', [])
            
            # Prepare atom data
            atom_x = [atom['x'] for atom in atoms]
            atom_y = [atom['y'] for atom in atoms]
            atom_z = [atom['z'] for atom in atoms]
            atom_elements = [atom['element'] for atom in atoms]
            atom_colors = [self.element_colors.get(elem, '#FF69B4') for elem in atom_elements]
            atom_sizes = [self.element_sizes.get(elem, 14) for elem in atom_elements]
            
            # Determine marker and line properties based on visualization style
            if config['visualization_style'] == 'Space-filling':
                marker_size = [s * 1.5 for s in atom_sizes] # Make atoms larger
                marker_opacity = 1.0
                bond_width_multiplier = 0.0 # No bonds in space-filling
            elif config['visualization_style'] == 'Wireframe':
                marker_size = [s * 0.5 for s in atom_sizes] # Make atoms smaller
                marker_opacity = 0.5
                bond_width_multiplier = 0.5 # Thinner bonds
            else: # Ball and Stick
                marker_size = atom_sizes
                marker_opacity = config['atom_opacity']
                bond_width_multiplier = 1.0

            # Create 3D plot
            fig = go.Figure()
            
            # Add atoms as scatter3d points
            atom_trace = go.Scatter3d(
                x=atom_x,
                y=atom_y,
                z=atom_z,
                mode='markers',
                marker=dict(
                    size=marker_size,
                    color=atom_colors,
                    opacity=marker_opacity,
                    line=dict(
                        width=config['atom_border_width'],
                        color=config['atom_border_color']
                    )
                ),
                text=atom_elements if config['show_atom_labels'] else None,
                hoverinfo='text' if config['show_atom_labels'] else 'none',
                hovertext=[f"{elem} (Atom {i})" for i, elem in enumerate(atom_elements)],
                name='Atoms',
                showlegend=config['show_legend']
            )
            fig.add_trace(atom_trace)
            
            # Add bonds as lines
            ring_bond_indices = set(ring_bonds) if config['show_ring_bonds'] else set()
            
            for i, bond in enumerate(bonds):
                atom1_idx = bond['atom1']
                atom2_idx = bond['atom2']
                
                # Determine bond styling
                is_ring_bond = i in ring_bond_indices
                bond_color = config['ring_bond_color'] if is_ring_bond else config['regular_bond_color']
                bond_width = (config['ring_bond_width'] if is_ring_bond else config['regular_bond_width']) * bond_width_multiplier
                
                # Only draw bonds if width > 0
                if bond_width > 0:
                    # Create bond line
                    bond_trace = go.Scatter3d(
                        x=[atom_x[atom1_idx], atom_x[atom2_idx], None],
                        y=[atom_y[atom1_idx], atom_y[atom2_idx], None],
                        z=[atom_z[atom1_idx], atom_z[atom2_idx], None],
                        mode='lines',
                        line=dict(
                            color=bond_color,
                            width=bond_width
                        ),
                        hoverinfo='none',
                        showlegend=False
                    )
                    fig.add_trace(bond_trace)
            
            # Update layout
            fig.update_layout(
                title=config['title'],
                scene=dict(
                    xaxis_title='X (Å)' if config['axis_labels'] else '',
                    yaxis_title='Y (Å)' if config['axis_labels'] else '',
                    zaxis_title='Z (Å)' if config['axis_labels'] else '',
                    bgcolor=config['background_color'],
                    camera=dict(
                        eye=dict(
                            x=config['camera_position']['x'],
                            y=config['camera_position']['y'],
                            z=config['camera_position']['z']
                        )
                    ),
                    aspectmode='cube'
                ),
                width=config['width'],
                height=config['height'],
                margin=dict(l=0, r=0, t=50, b=0),
                showlegend=config['show_legend']
            )
            
            return fig
            
        except Exception as e:
            self.add_error(f"Error creating 3D visualization: {str(e)}", e)
            return None
    
    def parse_rdkit_molecule(self, mol_obj: Any) -> Optional[Dict[str, Any]]:
        """
        Parse RDKit molecule object into compatible data structure.
        
        Args:
            mol_obj: RDKit molecule object
            
        Returns:
            Dictionary with atoms, bonds, and ring_bonds data
        """
        try:
            # This method would integrate with RDKit if available
            # For now, return None to indicate RDKit parsing is not implemented
            # This maintains module independence
            self.add_warning("RDKit integration not implemented in this component")
            return None
            
        except Exception as e:
            self.add_error(f"Error parsing RDKit molecule: {str(e)}", e)
            return None
    
    def render(self,
               mol_data: Dict[str, Any],
               show_config: bool = False,
               custom_config: Dict = None) -> Optional[go.Figure]:
        """
        Render the 3D molecular visualization component.
        
        Args:
            mol_data: Dictionary containing molecular structure data
            show_config: Whether to show configuration options
            custom_config: Additional visualization configuration
            
        Returns:
            Plotly figure object or None if error
        """
        try:
            self.clear_messages()
            
            # Show configuration options if requested
            if show_config:
                st.subheader("3D Visualization Configuration")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    self.viz_config['title'] = st.text_input(
                        "Chart Title",
                        value=self.viz_config['title'],
                        key=self.get_key('title')
                    )
                    
                    self.viz_config['atom_opacity'] = st.slider(
                        "Atom Opacity",
                        min_value=0.1,
                        max_value=1.0,
                        value=self.viz_config['atom_opacity'],
                        step=0.05,
                        key=self.get_key('atom_opacity')
                    )

                    self.viz_config['visualization_style'] = st.selectbox(
                        "Visualization Style",
                        options=['Ball and Stick', 'Space-filling', 'Wireframe'],
                        index=['Ball and Stick', 'Space-filling', 'Wireframe'].index(self.viz_config['visualization_style']),
                        key=self.get_key('visualization_style')
                    )
                    
                    self.viz_config['show_atom_labels'] = st.checkbox(
                        "Show Atom Labels",
                        value=self.viz_config['show_atom_labels'],
                        key=self.get_key('show_atom_labels')
                    )
                
                with col2:
                    self.viz_config['background_color'] = st.selectbox(
                        "Background Color",
                        options=['white', 'black', 'lightgray', 'darkgray'],
                        index=['white', 'black', 'lightgray', 'darkgray'].index(self.viz_config['background_color']),
                        key=self.get_key('background_color')
                    )
                    
                    self.viz_config['regular_bond_width'] = st.slider(
                        "Regular Bond Width",
                        min_value=1,
                        max_value=10,
                        value=self.viz_config['regular_bond_width'],
                        key=self.get_key('regular_bond_width')
                    )
                    
                    self.viz_config['show_ring_bonds'] = st.checkbox(
                        "Highlight Ring Bonds",
                        value=self.viz_config['show_ring_bonds'],
                        key=self.get_key('show_ring_bonds')
                    )
                
                with col3:
                    self.viz_config['width'] = st.slider(
                        "Chart Width",
                        min_value=400,
                        max_value=1200,
                        value=self.viz_config['width'],
                        step=50,
                        key=self.get_key('width')
                    )
                    
                    self.viz_config['height'] = st.slider(
                        "Chart Height",
                        min_value=300,
                        max_value=800,
                        value=self.viz_config['height'],
                        step=50,
                        key=self.get_key('height')
                    )
                    
                    self.viz_config['axis_labels'] = st.checkbox(
                        "Show Axis Labels",
                        value=self.viz_config['axis_labels'],
                        key=self.get_key('axis_labels')
                    )
            
            # Create and display visualization
            fig = self.create_3d_visualization(mol_data, custom_config)
            
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)
                
                # Display molecular information
                atoms = mol_data['atoms']
                bonds = mol_data['bonds']
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Atoms", len(atoms))
                with col2:
                    st.metric("Total Bonds", len(bonds))
                with col3:
                    unique_elements = len(set(atom['element'] for atom in atoms))
                    st.metric("Unique Elements", unique_elements)
                with col4:
                    ring_bonds = mol_data.get('ring_bonds', [])
                    st.metric("Ring Bonds", len(ring_bonds))
                
                # Show element distribution
                if len(atoms) > 0:
                    element_counts = {}
                    for atom in atoms:
                        element = atom['element']
                        element_counts[element] = element_counts.get(element, 0) + 1
                    
                    if len(element_counts) > 1:
                        st.subheader("Element Distribution")
                        element_df = pd.DataFrame(list(element_counts.items()), columns=['Element', 'Count'])
                        st.dataframe(element_df, use_container_width=True)
                
                # Log interaction
                self.log_interaction('3d_visualization_rendered', {
                    'total_atoms': len(atoms),
                    'total_bonds': len(bonds),
                    'unique_elements': len(set(atom['element'] for atom in atoms)),
                    'ring_bonds': len(mol_data.get('ring_bonds', [])),
                    'config': custom_config or {}
                })
                
                return fig
            else:
                self.display_messages()
                return None
                
        except Exception as e:
            self.add_error(f"Error rendering 3D visualization: {str(e)}", e)
            self.display_messages()
            return None