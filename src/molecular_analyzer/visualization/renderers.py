"""
Chart and molecular visualization renderers.

Provides Chart2DRenderer for 2D charts with multiple backends and
Molecule3DRenderer for interactive 3D molecular visualization.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union, Tuple
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from rdkit import Chem
from rdkit.Chem import AllChem

from ..models.base import BaseRenderer
from ..models.models import PropertyData, AnalysisResult, MoleculeData
from ..models.exceptions import ValidationError, ComputationError


class Chart2DRenderer(BaseRenderer[Union[PropertyData, List[PropertyData], Dict[str, Any]]]):
    """
    Flexible 2D chart renderer with strategy pattern for multiple backends.
    
    Supports various chart types including bar charts, scatter plots, line charts,
    histograms, and correlation matrices with matplotlib and plotly backends.
    """
    
    def __init__(self, backend: str = "plotly"):
        super().__init__(backend)
        self._chart_strategies = {
            'bar': self._render_bar_chart,
            'scatter': self._render_scatter_plot,
            'line': self._render_line_chart,
            'histogram': self._render_histogram,
            'correlation': self._render_correlation_matrix,
            'distribution': self._render_distribution_plot
        }
    
    @property
    def renderer_name(self) -> str:
        return "Chart2DRenderer"
    
    @property
    def supported_backends(self) -> List[str]:
        return ["plotly", "matplotlib"]
    
    @property
    def supported_chart_types(self) -> List[str]:
        return list(self._chart_strategies.keys())
    
    def _render_content(self, data: Union[PropertyData, List[PropertyData], Dict[str, Any]], **kwargs) -> Any:
        """
        Render 2D chart based on data type and requested chart type.
        
        Args:
            data: Property data, list of property data, or raw data dict
            **kwargs: Chart configuration including:
                - chart_type: str (required)
                - title: str
                - x_label: str
                - y_label: str
                - width: int
                - height: int
                - show_legend: bool
                - colors: List[str]
        
        Returns:
            Plotly figure or matplotlib figure depending on backend
        """
        chart_type = kwargs.get('chart_type')
        if not chart_type:
            raise ValidationError("chart_type is required for Chart2DRenderer")
        
        if chart_type not in self.supported_chart_types:
            raise ValidationError(
                f"Unsupported chart type: {chart_type}",
                validation_rule=f"Must be one of: {self.supported_chart_types}"
            )
        
        # Convert data to standardized format
        chart_data = self._prepare_chart_data(data, chart_type)
        
        # Render using appropriate strategy
        return self._chart_strategies[chart_type](chart_data, **kwargs)
    
    def _prepare_chart_data(self, data: Union[PropertyData, List[PropertyData], Dict[str, Any]], 
                           chart_type: str) -> Dict[str, Any]:
        """Convert input data to standardized chart data format."""
        if isinstance(data, dict):
            return data
        elif isinstance(data, PropertyData):
            return self._property_data_to_chart_data(data, chart_type)
        elif isinstance(data, list) and all(isinstance(item, PropertyData) for item in data):
            return self._property_list_to_chart_data(data, chart_type)
        else:
            raise ValidationError(f"Unsupported data type for charting: {type(data)}")
    
    def _property_data_to_chart_data(self, prop_data: PropertyData, chart_type: str) -> Dict[str, Any]:
        """Convert single PropertyData to chart data."""
        properties = prop_data.properties
        
        if chart_type in ['bar', 'histogram']:
            return {
                'labels': list(properties.keys()),
                'values': list(properties.values()),
                'title': f"Properties - {prop_data.calculation_method or 'Unknown Method'}"
            }
        elif chart_type == 'scatter':
            # For scatter plots, we need to extract numerical properties
            numerical_props = {k: v for k, v in properties.items() 
                             if isinstance(v, (int, float))}
            if len(numerical_props) < 2:
                raise ValidationError("Scatter plot requires at least 2 numerical properties")
            
            keys = list(numerical_props.keys())[:2]  # Take first two numerical properties
            return {
                'x': [numerical_props[keys[0]]],
                'y': [numerical_props[keys[1]]],
                'x_label': keys[0],
                'y_label': keys[1],
                'title': 'Property Scatter Plot'
            }
        else:
            return {'raw_data': properties}
    
    def _property_list_to_chart_data(self, prop_list: List[PropertyData], chart_type: str) -> Dict[str, Any]:
        """Convert list of PropertyData to chart data."""
        if not prop_list:
            raise ValidationError("Empty property list cannot be charted")
        
        # Extract common properties across all PropertyData objects
        all_props = {}
        for i, prop_data in enumerate(prop_list):
            for key, value in prop_data.properties.items():
                if key not in all_props:
                    all_props[key] = []
                all_props[key].append(value)
        
        # Filter numerical properties for most chart types
        numerical_props = {k: v for k, v in all_props.items() 
                          if all(isinstance(x, (int, float)) for x in v)}
        
        if chart_type == 'correlation':
            return {
                'data_matrix': np.array([numerical_props[k] for k in numerical_props.keys()]).T,
                'labels': list(numerical_props.keys()),
                'title': 'Property Correlation Matrix'
            }
        elif chart_type in ['bar', 'line']:
            # Use first numerical property for bar/line charts
            if numerical_props:
                first_prop = list(numerical_props.keys())[0]
                return {
                    'labels': [f"Molecule {i+1}" for i in range(len(numerical_props[first_prop]))],
                    'values': numerical_props[first_prop],
                    'title': f"{first_prop} Across Molecules"
                }
        elif chart_type == 'scatter':
            if len(numerical_props) >= 2:
                keys = list(numerical_props.keys())[:2]
                return {
                    'x': numerical_props[keys[0]],
                    'y': numerical_props[keys[1]],
                    'x_label': keys[0],
                    'y_label': keys[1],
                    'title': f"{keys[0]} vs {keys[1]}"
                }
        
        return {'raw_data': all_props}
    
    def _render_bar_chart(self, data: Dict[str, Any], **kwargs) -> go.Figure:
        """Render bar chart using plotly."""
        if self.backend == "plotly":
            fig = go.Figure(data=[
                go.Bar(
                    x=data.get('labels', []),
                    y=data.get('values', []),
                    marker_color=kwargs.get('colors', ['steelblue'] * len(data.get('values', [])))
                )
            ])
            
            fig.update_layout(
                title=kwargs.get('title', data.get('title', 'Bar Chart')),
                xaxis_title=kwargs.get('x_label', 'Categories'),
                yaxis_title=kwargs.get('y_label', 'Values'),
                width=kwargs.get('width', 800),
                height=kwargs.get('height', 600),
                showlegend=kwargs.get('show_legend', False)
            )
            
            return fig
        else:
            # Placeholder for matplotlib implementation
            raise NotImplementedError("Matplotlib backend not yet implemented for bar charts")
    
    def _render_scatter_plot(self, data: Dict[str, Any], **kwargs) -> go.Figure:
        """Render scatter plot using plotly."""
        if self.backend == "plotly":
            fig = go.Figure(data=[
                go.Scatter(
                    x=data.get('x', []),
                    y=data.get('y', []),
                    mode='markers',
                    marker=dict(
                        size=kwargs.get('marker_size', 8),
                        color=kwargs.get('colors', 'steelblue')
                    )
                )
            ])
            
            fig.update_layout(
                title=kwargs.get('title', data.get('title', 'Scatter Plot')),
                xaxis_title=kwargs.get('x_label', data.get('x_label', 'X')),
                yaxis_title=kwargs.get('y_label', data.get('y_label', 'Y')),
                width=kwargs.get('width', 800),
                height=kwargs.get('height', 600),
                showlegend=kwargs.get('show_legend', False)
            )
            
            return fig
        else:
            raise NotImplementedError("Matplotlib backend not yet implemented for scatter plots")
    
    def _render_line_chart(self, data: Dict[str, Any], **kwargs) -> go.Figure:
        """Render line chart using plotly."""
        if self.backend == "plotly":
            fig = go.Figure(data=[
                go.Scatter(
                    x=data.get('labels', []),
                    y=data.get('values', []),
                    mode='lines+markers',
                    line=dict(color=kwargs.get('line_color', 'steelblue'))
                )
            ])
            
            fig.update_layout(
                title=kwargs.get('title', data.get('title', 'Line Chart')),
                xaxis_title=kwargs.get('x_label', 'X'),
                yaxis_title=kwargs.get('y_label', 'Y'),
                width=kwargs.get('width', 800),
                height=kwargs.get('height', 600),
                showlegend=kwargs.get('show_legend', False)
            )
            
            return fig
        else:
            raise NotImplementedError("Matplotlib backend not yet implemented for line charts")
    
    def _render_histogram(self, data: Dict[str, Any], **kwargs) -> go.Figure:
        """Render histogram using plotly."""
        if self.backend == "plotly":
            fig = go.Figure(data=[
                go.Histogram(
                    x=data.get('values', []),
                    nbinsx=kwargs.get('bins', 20),
                    marker_color=kwargs.get('color', 'steelblue')
                )
            ])
            
            fig.update_layout(
                title=kwargs.get('title', data.get('title', 'Histogram')),
                xaxis_title=kwargs.get('x_label', 'Value'),
                yaxis_title=kwargs.get('y_label', 'Frequency'),
                width=kwargs.get('width', 800),
                height=kwargs.get('height', 600),
                showlegend=kwargs.get('show_legend', False)
            )
            
            return fig
        else:
            raise NotImplementedError("Matplotlib backend not yet implemented for histograms")
    
    def _render_correlation_matrix(self, data: Dict[str, Any], **kwargs) -> go.Figure:
        """Render correlation matrix heatmap using plotly."""
        if self.backend == "plotly":
            data_matrix = data.get('data_matrix')
            if data_matrix is None:
                raise ValidationError("data_matrix required for correlation matrix")
            
            # Calculate correlation matrix
            corr_matrix = np.corrcoef(data_matrix.T)
            labels = data.get('labels', [f"Property {i}" for i in range(corr_matrix.shape[0])])
            
            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix,
                x=labels,
                y=labels,
                colorscale='RdBu',
                zmid=0,
                text=np.round(corr_matrix, 2),
                texttemplate="%{text}",
                textfont={"size": 10},
                hoverongaps=False
            ))
            
            fig.update_layout(
                title=kwargs.get('title', data.get('title', 'Property Correlation Matrix')),
                width=kwargs.get('width', 800),
                height=kwargs.get('height', 600)
            )
            
            return fig
        else:
            raise NotImplementedError("Matplotlib backend not yet implemented for correlation matrix")
    
    def _render_distribution_plot(self, data: Dict[str, Any], **kwargs) -> go.Figure:
        """Render distribution plot (histogram + density) using plotly."""
        if self.backend == "plotly":
            values = data.get('values', [])
            if not values:
                raise ValidationError("values required for distribution plot")
            
            # Create subplots with secondary y-axis
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Add histogram
            fig.add_trace(
                go.Histogram(
                    x=values,
                    nbinsx=kwargs.get('bins', 20),
                    name='Histogram',
                    marker_color=kwargs.get('hist_color', 'lightblue'),
                    opacity=0.7
                ),
                secondary_y=False
            )
            
            # Add density curve (simplified)
            hist, bins = np.histogram(values, bins=kwargs.get('bins', 20))
            density = hist / (len(values) * (bins[1] - bins[0]))
            bin_centers = (bins[:-1] + bins[1:]) / 2
            
            fig.add_trace(
                go.Scatter(
                    x=bin_centers,
                    y=density,
                    mode='lines',
                    name='Density',
                    line=dict(color=kwargs.get('density_color', 'red'), width=2)
                ),
                secondary_y=True
            )
            
            fig.update_layout(
                title=kwargs.get('title', data.get('title', 'Distribution Plot')),
                width=kwargs.get('width', 800),
                height=kwargs.get('height', 600)
            )
            
            fig.update_xaxes(title_text=kwargs.get('x_label', 'Value'))
            fig.update_yaxes(title_text=kwargs.get('y_label', 'Frequency'), secondary_y=False)
            fig.update_yaxes(title_text="Density", secondary_y=True)
            
            return fig
        else:
            raise NotImplementedError("Matplotlib backend not yet implemented for distribution plots")


class Molecule3DRenderer(BaseRenderer[Union[MoleculeData, str, Chem.Mol]]):
    """
    Interactive 3D molecular visualization renderer.
    
    Provides comprehensive 3D visualization capabilities for molecules including
    structure optimization, animation, and interactive controls.
    """
    
    def __init__(self, backend: str = "plotly"):
        super().__init__(backend)
        self._element_colors = {
            'H': '#FFFFFF', 'C': '#909090', 'N': '#3050F8', 'O': '#FF0D0D',
            'S': '#FFFF30', 'P': '#FF8000', 'F': '#90E050', 'Cl': '#1FF01F',
            'Br': '#A62929', 'I': '#940094', 'He': '#D9FFFF', 'Ne': '#B3E3F5',
            'Ar': '#80D1E3', 'Kr': '#8FB8D1', 'Xe': '#429EB0', 'Rn': '#520066'
        }
        self._element_sizes = {
            'H': 8, 'C': 12, 'N': 12, 'O': 10, 'S': 14, 'P': 14, 'F': 9, 
            'Cl': 15, 'Br': 16, 'I': 18, 'He': 6, 'Ne': 7, 'Ar': 13, 
            'Kr': 14, 'Xe': 15, 'Rn': 16
        }
    
    @property
    def renderer_name(self) -> str:
        return "Molecule3DRenderer"
    
    @property
    def supported_backends(self) -> List[str]:
        return ["plotly"]
    
    def _render_content(self, data: Union[MoleculeData, str, Chem.Mol], **kwargs) -> go.Figure:
        """
        Render 3D molecular visualization.
        
        Args:
            data: Molecule data as MoleculeData, SMILES string, or RDKit Mol
            **kwargs: Visualization options including:
                - optimize: bool (optimize 3D structure)
                - show_bonds: bool
                - show_hydrogens: bool
                - style: str ('ball_and_stick', 'space_filling', 'wireframe')
                - title: str
                - width: int
                - height: int
        
        Returns:
            Plotly 3D figure
        """
        # Convert input to RDKit molecule
        mol = self._prepare_molecule(data)
        if mol is None:
            raise ComputationError("Failed to create molecule from input data")
        
        # Generate 3D coordinates
        mol_3d = self._generate_3d_coordinates(mol, kwargs.get('optimize', True))
        if mol_3d is None:
            raise ComputationError("Failed to generate 3D coordinates")
        
        # Extract visualization data
        atom_data, bond_data = self._extract_visualization_data(mol_3d, **kwargs)
        
        # Create 3D plot
        return self._create_3d_plot(atom_data, bond_data, **kwargs)
    
    def _prepare_molecule(self, data: Union[MoleculeData, str, Chem.Mol]) -> Optional[Chem.Mol]:
        """Convert input data to RDKit molecule."""
        try:
            if isinstance(data, str):
                return Chem.MolFromSmiles(data)
            elif isinstance(data, MoleculeData):
                if not data.validated:
                    data.validate()
                return Chem.MolFromSmiles(data.smiles)
            elif isinstance(data, Chem.Mol):
                return data
            else:
                raise ValidationError(f"Unsupported molecule data type: {type(data)}")
        except Exception as e:
            raise ComputationError(f"Failed to process molecule: {str(e)}") from e
    
    def _generate_3d_coordinates(self, mol: Chem.Mol, optimize: bool = True) -> Optional[Chem.Mol]:
        """Generate 3D coordinates for molecule."""
        try:
            mol_3d = Chem.Mol(mol)
            mol_3d = Chem.AddHs(mol_3d)
            
            # Embed molecule in 3D space
            embed_result = AllChem.EmbedMolecule(mol_3d, randomSeed=42)
            if embed_result != 0:
                # Try multiple conformations if first attempt fails
                embed_result = AllChem.EmbedMolecule(mol_3d, randomSeed=42, useRandomCoords=True)
                if embed_result != 0:
                    raise ComputationError("Failed to embed molecule in 3D space")
            
            # Optimize geometry if requested
            if optimize:
                optimization_result = AllChem.MMFFOptimizeMolecule(mol_3d)
                if optimization_result != 0:
                    # Try UFF if MMFF fails
                    AllChem.UFFOptimizeMolecule(mol_3d)
            
            return mol_3d
        except Exception as e:
            raise ComputationError(f"3D coordinate generation failed: {str(e)}") from e
    
    def _extract_visualization_data(self, mol_3d: Chem.Mol, **kwargs) -> Tuple[Dict[str, List], List[Dict]]:
        """Extract atomic coordinates and bonds for visualization."""
        conf = mol_3d.GetConformer()
        show_hydrogens = kwargs.get('show_hydrogens', True)
        
        # Extract atom data
        atom_data = {
            'x': [], 'y': [], 'z': [],
            'symbols': [], 'colors': [], 'sizes': [],
            'texts': []
        }
        
        atom_indices = {}  # Map atom index to position in arrays
        array_index = 0
        
        for atom in mol_3d.GetAtoms():
            atom_idx = atom.GetIdx()
            symbol = atom.GetSymbol()
            
            # Skip hydrogens if not requested
            if not show_hydrogens and symbol == 'H':
                continue
            
            pos = conf.GetAtomPosition(atom_idx)
            atom_data['x'].append(pos.x)
            atom_data['y'].append(pos.y)
            atom_data['z'].append(pos.z)
            atom_data['symbols'].append(symbol)
            atom_data['colors'].append(self._element_colors.get(symbol, '#808080'))
            atom_data['sizes'].append(self._element_sizes.get(symbol, 10))
            atom_data['texts'].append(f"{symbol}{atom_idx}")
            
            atom_indices[atom_idx] = array_index
            array_index += 1
        
        # Extract bond data
        bond_data = []
        if kwargs.get('show_bonds', True):
            for bond in mol_3d.GetBonds():
                begin_idx = bond.GetBeginAtomIdx()
                end_idx = bond.GetEndAtomIdx()
                
                # Skip bonds involving hidden hydrogens
                if not show_hydrogens:
                    begin_atom = mol_3d.GetAtomWithIdx(begin_idx)
                    end_atom = mol_3d.GetAtomWithIdx(end_idx)
                    if begin_atom.GetSymbol() == 'H' or end_atom.GetSymbol() == 'H':
                        continue
                
                if begin_idx in atom_indices and end_idx in atom_indices:
                    begin_pos = conf.GetAtomPosition(begin_idx)
                    end_pos = conf.GetAtomPosition(end_idx)
                    
                    bond_data.append({
                        'x': [begin_pos.x, end_pos.x, None],
                        'y': [begin_pos.y, end_pos.y, None],
                        'z': [begin_pos.z, end_pos.z, None],
                        'bond_order': bond.GetBondType()
                    })
        
        return atom_data, bond_data
    
    def _create_3d_plot(self, atom_data: Dict[str, List], bond_data: List[Dict], **kwargs) -> go.Figure:
        """Create the 3D plotly visualization."""
        fig = go.Figure()
        
        style = kwargs.get('style', 'ball_and_stick')
        
        # Add atoms
        if style in ['ball_and_stick', 'space_filling']:
            size_multiplier = 2.0 if style == 'space_filling' else 1.0
            
            fig.add_trace(go.Scatter3d(
                x=atom_data['x'],
                y=atom_data['y'],
                z=atom_data['z'],
                mode='markers',
                marker=dict(
                    size=[s * size_multiplier for s in atom_data['sizes']],
                    color=atom_data['colors'],
                    opacity=kwargs.get('atom_opacity', 0.8),
                    line=dict(width=1, color='black')
                ),
                text=atom_data['texts'],
                hovertemplate='<b>%{text}</b><br>x: %{x:.2f}<br>y: %{y:.2f}<br>z: %{z:.2f}<extra></extra>',
                name='Atoms'
            ))
        
        # Add bonds
        if kwargs.get('show_bonds', True) and style != 'space_filling':
            for bond in bond_data:
                fig.add_trace(go.Scatter3d(
                    x=bond['x'],
                    y=bond['y'],
                    z=bond['z'],
                    mode='lines',
                    line=dict(
                        color=kwargs.get('bond_color', '#808080'),
                        width=kwargs.get('bond_width', 3)
                    ),
                    showlegend=False,
                    hoverinfo='skip'
                ))
        
        # Update layout
        fig.update_layout(
            title=kwargs.get('title', '3D Molecular Structure'),
            scene=dict(
                xaxis_title='X (Å)',
                yaxis_title='Y (Å)',
                zaxis_title='Z (Å)',
                aspectmode='cube',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5),
                    up=dict(x=0, y=0, z=1)
                )
            ),
            width=kwargs.get('width', 800),
            height=kwargs.get('height', 600),
            showlegend=kwargs.get('show_legend', True)
        )
        
        return fig
    
    def create_animation(self, molecules: List[Union[MoleculeData, str, Chem.Mol]], **kwargs) -> go.Figure:
        """
        Create animated 3D visualization for multiple molecular conformations.
        
        Args:
            molecules: List of molecules or conformations
            **kwargs: Animation options
        
        Returns:
            Animated plotly figure
        """
        if not molecules:
            raise ValidationError("At least one molecule required for animation")
        
        frames = []
        for i, mol_data in enumerate(molecules):
            mol = self._prepare_molecule(mol_data)
            if mol is None:
                continue
            
            mol_3d = self._generate_3d_coordinates(mol, kwargs.get('optimize', True))
            if mol_3d is None:
                continue
            
            atom_data, bond_data = self._extract_visualization_data(mol_3d, **kwargs)
            
            # Create frame data
            frame_data = [go.Scatter3d(
                x=atom_data['x'],
                y=atom_data['y'],
                z=atom_data['z'],
                mode='markers',
                marker=dict(
                    size=atom_data['sizes'],
                    color=atom_data['colors'],
                    opacity=kwargs.get('atom_opacity', 0.8)
                ),
                text=atom_data['texts'],
                name='Atoms'
            )]
            
            # Add bonds to frame
            for bond in bond_data:
                frame_data.append(go.Scatter3d(
                    x=bond['x'],
                    y=bond['y'],
                    z=bond['z'],
                    mode='lines',
                    line=dict(color='gray', width=3),
                    showlegend=False
                ))
            
            frames.append(go.Frame(data=frame_data, name=f"Frame {i}"))
        
        # Create initial figure with first frame
        if frames:
            fig = go.Figure(data=frames[0].data, frames=frames)
            
            # Add animation controls
            fig.update_layout(
                updatemenus=[{
                    'buttons': [
                        {'args': [None, {'frame': {'duration': 500, 'redraw': True}, 
                                        'fromcurrent': True, 'transition': {'duration': 300}}],
                         'label': 'Play', 'method': 'animate'},
                        {'args': [[None], {'frame': {'duration': 0, 'redraw': True}, 
                                          'mode': 'immediate', 'transition': {'duration': 0}}],
                         'label': 'Pause', 'method': 'animate'}
                    ],
                    'direction': 'left',
                    'pad': {'r': 10, 't': 87},
                    'showactive': False,
                    'type': 'buttons',
                    'x': 0.1,
                    'xanchor': 'right',
                    'y': 0,
                    'yanchor': 'top'
                }],
                title=kwargs.get('title', '3D Molecular Animation'),
                scene=dict(
                    xaxis_title='X (Å)',
                    yaxis_title='Y (Å)',
                    zaxis_title='Z (Å)',
                    aspectmode='cube'
                ),
                width=kwargs.get('width', 800),
                height=kwargs.get('height', 600)
            )
            
            return fig
        else:
            raise ComputationError("Failed to create any valid frames for animation")