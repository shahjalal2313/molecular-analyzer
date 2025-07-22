import streamlit as st
import sys
import os
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from typing import Dict, Any, List

# Add paths for integration
integration_path = Path(__file__).parent.parent.parent / "integration"
if str(integration_path) not in sys.path:
    sys.path.insert(0, str(integration_path))

try:
    from adapter_v2 import AdapterFactory
except ImportError:
    st.error("Could not import adapter. Please check your installation.")
    AdapterFactory = None

def conformational_analysis_component():
    st.subheader("Conformational Analysis")
    
    # Initialize session state for conformational analysis
    if 'conformational_results' not in st.session_state:
        st.session_state.conformational_results = None
    if 'conformational_smiles' not in st.session_state:
        st.session_state.conformational_smiles = ""
    if 'conformational_params' not in st.session_state:
        st.session_state.conformational_params = {}
    
    # Initialize adapter
    if AdapterFactory is None:
        st.error("Adapter not available. Cannot perform conformational analysis.")
        return
    
    try:
        adapter = AdapterFactory.create_auto_adapter()
    except Exception as e:
        st.error(f"Failed to create adapter: {str(e)}")
        return

    # Input section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        smiles = st.text_input("Enter SMILES string for conformational analysis:", "CCO", 
                              key="conformational_smiles_input")
        
    with col2:
        num_conformers = st.slider("Number of Conformers", 1, 50, 10, 
                                  key="conformational_num_conformers")
        optimization_level = st.selectbox("Optimization Level", ["Basic", "Standard", "Thorough"], 
                                        index=1, key="conformational_optimization_level")

    # Analysis parameters
    with st.expander("Advanced Parameters"):
        energy_threshold = st.slider("Energy Threshold (kcal/mol)", 0.1, 10.0, 5.0, 
                                    key="conformational_energy_threshold")
        include_energy_plot = st.checkbox("Include Energy Plot", value=True, 
                                        key="conformational_include_energy_plot")

    # Action buttons
    col1, col2 = st.columns([3, 1])
    with col1:
        run_analysis = st.button("Perform Conformational Analysis", type="primary", 
                                key="conformational_run_button")
    with col2:
        if st.button("Clear Results", key="conformational_clear_button"):
            # Clear all conformational analysis data
            keys_to_clear = [
                'conformational_results', 'conformational_smiles', 'conformational_params'
            ] + [key for key in st.session_state.keys() if key.startswith('conformational_3d_')]
            
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.success("Results cleared!")
            st.rerun()

    if run_analysis:
        if not smiles.strip():
            st.warning("Please enter a SMILES string.")
            return
            
        # Update session state parameters
        current_params = {
            'smiles': smiles,
            'num_conformers': num_conformers,
            'optimization_level': optimization_level,
            'energy_threshold': energy_threshold
        }
        st.session_state.conformational_params = current_params
        st.session_state.conformational_smiles = smiles
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("Initializing conformational analysis...")
            progress_bar.progress(10)
            
            # Check if adapter supports conformational analysis
            capabilities = adapter.get_capabilities()
            if not capabilities.get('conformational_analysis', False):
                st.error("Conformational analysis not supported by current adapter.")
                return
            
            status_text.text("Generating conformers...")
            progress_bar.progress(30)
            
            # Perform conformational analysis
            conformational_results = adapter.perform_conformational_analysis(
                smiles=smiles,
                num_conformers=num_conformers,
                optimization_level=optimization_level.lower(),
                energy_threshold=energy_threshold
            )
            
            progress_bar.progress(70)
            status_text.text("Processing results...")
            
            if conformational_results.get('error'):
                st.error(f"Conformational analysis failed: {conformational_results['error']}")
                return
            
            progress_bar.progress(100)
            status_text.text("Analysis complete!")
            
            # Store results in session state
            st.session_state.conformational_results = conformational_results
            
            # Display results
            st.success(f"Successfully generated {conformational_results.get('num_conformers_found', 0)} conformers!")
        
        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")
            st.write("Stack trace for debugging:")
            import traceback
            st.code(traceback.format_exc())
        
        finally:
            progress_bar.empty()
            status_text.empty()
    
    # Display results if available (from session state or fresh analysis)
    conformational_results = st.session_state.conformational_results
    
    if conformational_results and not conformational_results.get('error'):
        # Create tabs for different views
        tabs = st.tabs(["Conformer Summary", "Energy Analysis", "3D Visualization", "Change Analysis", "Raw Data"])
        
        with tabs[0]:
            st.subheader("Conformer Summary")
            
            if 'conformers' in conformational_results:
                conformers = conformational_results['conformers']
                
                # Create summary table
                summary_data = []
                for i, conf in enumerate(conformers):
                    summary_data.append({
                        'Conformer': f"Conf_{i+1}",
                        'Energy (kcal/mol)': round(conf.get('energy', 0), 3),
                        'Relative Energy': round(conf.get('relative_energy', 0), 3),
                        'Valid': conf.get('valid', False)
                    })
                
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, use_container_width=True)
                
                # Statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Conformers", len(conformers))
                with col2:
                    valid_conformers = sum(1 for c in conformers if c.get('valid', False))
                    st.metric("Valid Conformers", valid_conformers)
                with col3:
                    if conformers:
                        energy_range = max(c.get('energy', 0) for c in conformers) - min(c.get('energy', 0) for c in conformers)
                        st.metric("Energy Range (kcal/mol)", f"{energy_range:.2f}")
        
        with tabs[1]:
            st.subheader("Energy Analysis")
            
            if include_energy_plot and 'conformers' in conformational_results:
                conformers = conformational_results['conformers']
                
                # Energy plot
                energies = [c.get('relative_energy', 0) for c in conformers]
                conformer_ids = [f"Conf_{i+1}" for i in range(len(conformers))]
                
                fig_energy = px.bar(
                    x=conformer_ids,
                    y=energies,
                    title="Conformer Relative Energies",
                    labels={'x': 'Conformer', 'y': 'Relative Energy (kcal/mol)'}
                )
                fig_energy.update_layout(showlegend=False)
                st.plotly_chart(fig_energy, use_container_width=True)
                
                # Energy histogram
                fig_hist = px.histogram(
                    x=energies,
                    nbins=10,
                    title="Energy Distribution",
                    labels={'x': 'Relative Energy (kcal/mol)', 'y': 'Count'}
                )
                st.plotly_chart(fig_hist, use_container_width=True)
        
        with tabs[2]:
            st.subheader("3D Visualization")
            
            capabilities = adapter.get_capabilities()
            if capabilities.get('3d_visualization', False):
                conformers = conformational_results.get('conformers', [])
                if conformers:
                    conformer_options = [f"Conf_{i+1} (Energy: {conf.get('relative_energy', 0):.2f} kcal/mol)" 
                                       for i, conf in enumerate(conformers)]
                    conformer_to_view = st.selectbox(
                        "Select conformer to visualize:",
                        conformer_options,
                        key="conformational_conformer_selector"
                    )
                    
                    if conformer_to_view:
                        # Extract conformer index
                        conformer_idx = int(conformer_to_view.split('_')[1].split(' ')[0]) - 1
                        
                        # Visualization options
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            viz_style = st.selectbox(
                                "Visualization Style:",
                                ["Ball and Stick", "Space-filling", "Wireframe"],
                                index=0,
                                key="conformational_viz_style"
                            )
                        with col2:
                            show_labels = st.checkbox("Show Atom Labels", value=True,
                                                    key="conformational_show_labels")
                        with col3:
                            show_changes = st.checkbox("Show Conformational Changes", value=False,
                                                     key="conformational_show_changes")
                        
                        # Conformational change analysis options
                        if show_changes and len(conformers) > 1:
                            st.subheader("🔄 Conformational Change Analysis")
                            
                            # Conformer comparison selection
                            col1, col2 = st.columns(2)
                            with col1:
                                reference_conf = st.selectbox(
                                    "Reference Conformer:",
                                    conformer_options,
                                    index=0,
                                    key="reference_conformer_selector"
                                )
                            with col2:
                                compare_conf = st.selectbox(
                                    "Compare with Conformer:",
                                    conformer_options,
                                    index=min(1, len(conformer_options) - 1),
                                    key="compare_conformer_selector"
                                )
                            
                            # Change analysis parameters
                            col1, col2 = st.columns(2)
                            with col1:
                                angle_threshold = st.slider(
                                    "Torsion Angle Threshold (°):",
                                    min_value=5.0,
                                    max_value=45.0,
                                    value=15.0,
                                    step=5.0,
                                    key="angle_threshold_slider"
                                )
                            with col2:
                                distance_threshold = st.slider(
                                    "Displacement Threshold (Å):",
                                    min_value=0.5,
                                    max_value=3.0,
                                    value=1.0,
                                    step=0.1,
                                    key="distance_threshold_slider"
                                )
                            
                            # Extract conformer indices
                            ref_idx = int(reference_conf.split('_')[1].split(' ')[0]) - 1
                            comp_idx = int(compare_conf.split('_')[1].split(' ')[0]) - 1
                            
                            if ref_idx != comp_idx:
                                try:
                                    # Get conformational change analysis
                                    change_cache_key = f"change_analysis_{smiles}_{ref_idx}_{comp_idx}_{angle_threshold}_{distance_threshold}"
                                    
                                    if change_cache_key not in st.session_state:
                                        with st.spinner("Analyzing conformational changes..."):
                                            change_data = adapter.get_conformational_change_visualization_data(
                                                smiles=smiles,
                                                conf1_id=ref_idx,
                                                conf2_id=comp_idx,
                                                angle_threshold=angle_threshold,
                                                distance_threshold=distance_threshold
                                            )
                                        st.session_state[change_cache_key] = change_data
                                    else:
                                        change_data = st.session_state[change_cache_key]
                                    
                                    if change_data and not change_data.get('error'):
                                        # Display change analysis summary
                                        change_analysis = change_data.get('change_analysis', {})
                                        
                                        # Metrics display
                                        col1, col2, col3, col4 = st.columns(4)
                                        with col1:
                                            st.metric("Change Magnitude", change_analysis.get('change_magnitude', 'N/A').title())
                                        with col2:
                                            st.metric("Max Displacement", f"{change_analysis.get('max_displacement', 0):.2f} Å")
                                        with col3:
                                            st.metric("Max Angle Change", f"{change_analysis.get('max_angle_change', 0):.1f}°")
                                        with col4:
                                            st.metric("Changed Atoms", str(change_analysis.get('num_displaced_atoms', 0)))
                                        
                                        # Store change data for visualization
                                        conformational_change_data = change_data
                                    else:
                                        st.error(f"Change analysis failed: {change_data.get('error', 'Unknown error')}")
                                        conformational_change_data = None
                                        
                                except Exception as e:
                                    st.error(f"Error in change analysis: {str(e)}")
                                    conformational_change_data = None
                            else:
                                st.warning("Please select different conformers for comparison.")
                                conformational_change_data = None
                        else:
                            conformational_change_data = None
                        
                        try:
                            # Create cache key for 3D visualization
                            viz_cache_key = f"conformational_3d_{smiles}_{conformer_idx}"
                            
                            # Check if we have cached 3D data for this conformer
                            if viz_cache_key not in st.session_state:
                                # Generate 3D visualization data for the selected conformer
                                mol_3d_data = adapter.get_3d_visualization_for_conformer(
                                    smiles=smiles, 
                                    conformer_index=conformer_idx,
                                    conformers_data=conformers
                                )
                                # Cache the result
                                st.session_state[viz_cache_key] = mol_3d_data
                            else:
                                # Use cached data
                                mol_3d_data = st.session_state[viz_cache_key]
                            
                            if mol_3d_data and not mol_3d_data.get('error'):
                                # Create basic 3D plot directly
                                atoms = mol_3d_data.get('atoms', [])
                                bonds = mol_3d_data.get('bonds', [])
                                
                                # CPK colors for atoms
                                element_colors = {
                                    'H': '#FFFFFF', 'C': '#909090', 'N': '#3050F8', 'O': '#FF0D0D',
                                    'S': '#FFFF30', 'P': '#FF8000', 'F': '#90E050', 'Cl': '#1FF01F'
                                }
                                
                                # Special colors for aromatic carbons
                                aromatic_carbon_color = '#404040'
                                
                                # Atom sizes (hydrogen made smaller for better proportions)
                                element_sizes = {
                                    'H': 4, 'C': 18, 'N': 16, 'O': 16, 'S': 20, 'P': 20, 'F': 16, 'Cl': 18
                                }
                                
                                if atoms:
                                    # Extract atom positions and properties
                                    x_coords = [atom['x'] for atom in atoms]
                                    y_coords = [atom['y'] for atom in atoms]
                                    z_coords = [atom['z'] for atom in atoms]
                                    elements = [atom['element'] for atom in atoms]
                                    
                                    # Prepare colors and sizes with change highlighting
                                    colors = []
                                    sizes = []
                                    hover_texts = []
                                    
                                    # Check if we have conformational change data for highlighting
                                    displaced_atom_indices = set()
                                    if conformational_change_data and show_changes:
                                        displaced_atoms = conformational_change_data.get('visualization_markers', {}).get('displaced_atoms', [])
                                        displaced_atom_indices = set(atom['atom_idx'] for atom in displaced_atoms)
                                    
                                    # Get bond information for aromaticity detection
                                    aromatic_atoms = set()
                                    if bonds:
                                        for bond in bonds:
                                            if bond.get('is_aromatic', False):
                                                aromatic_atoms.add(bond['atom1'])
                                                aromatic_atoms.add(bond['atom2'])
                                    
                                    for i, (elem, atom) in enumerate(zip(elements, atoms)):
                                        # Base color and size from element
                                        if elem == 'C' and i in aromatic_atoms:
                                            base_color = aromatic_carbon_color  # Darker for aromatic carbons
                                        else:
                                            base_color = element_colors.get(elem, '#FF69B4')
                                        base_size = element_sizes.get(elem, 14)
                                        
                                        # Highlight if this atom has significant displacement
                                        if i in displaced_atom_indices and show_changes:
                                            # Find displacement info
                                            displacement = 0
                                            change_type = 'minor'
                                            for displaced_atom in conformational_change_data.get('visualization_markers', {}).get('displaced_atoms', []):
                                                if displaced_atom['atom_idx'] == i:
                                                    displacement = displaced_atom['displacement']
                                                    change_type = displaced_atom['change_type']
                                                    break
                                            
                                            # Use highlighting colors for changed atoms, but make them distinguishable
                                            if change_type == 'major':
                                                colors.append('#FF1A1A')  # Bright red for major changes
                                                sizes.append(base_size * 1.5)
                                            else:
                                                colors.append('#FF8C00')  # Orange for minor changes
                                                sizes.append(base_size * 1.2)
                                            
                                            hover_texts.append(f"{elem} (Atom {i}) - MOVED {displacement:.2f}Å ({change_type})")
                                        else:
                                            colors.append(base_color)
                                            sizes.append(base_size)
                                            hover_texts.append(f"{elem} (Atom {i})")
                                    
                                    # Create 3D scatter plot for atoms
                                    fig_3d = go.Figure()
                                    
                                    # Add atoms
                                    fig_3d.add_trace(go.Scatter3d(
                                        x=x_coords, y=y_coords, z=z_coords,
                                        mode='markers',
                                        marker=dict(size=sizes, color=colors, opacity=0.8),
                                        text=elements if show_labels else None,
                                        hovertext=hover_texts,
                                        name='Atoms'
                                    ))
                                    
                                    # Add bonds with change highlighting
                                    changed_bonds = set()
                                    if conformational_change_data and show_changes:
                                        # Mark bonds involved in torsion changes
                                        torsion_changes = conformational_change_data.get('visualization_markers', {}).get('torsion_changes', [])
                                        for torsion_change in torsion_changes:
                                            bond_atoms = torsion_change.get('bond_atoms', ())
                                            if len(bond_atoms) == 2:
                                                changed_bonds.add(tuple(sorted(bond_atoms)))
                                    
                                    for bond in bonds:
                                        atom1_idx = bond['atom1']
                                        atom2_idx = bond['atom2']
                                        bond_key = tuple(sorted([atom1_idx, atom2_idx]))
                                        bond_type_raw = bond.get('bond_type', 'SINGLE')
                                        is_aromatic = bond.get('is_aromatic', False)
                                        
                                        # Handle both string and numeric bond types
                                        if isinstance(bond_type_raw, (int, float)):
                                            if bond_type_raw == 1.0:
                                                bond_type = 'SINGLE'
                                            elif bond_type_raw == 2.0:
                                                bond_type = 'DOUBLE'
                                            elif bond_type_raw == 3.0:
                                                bond_type = 'TRIPLE'
                                            elif bond_type_raw == 1.5:
                                                bond_type = 'SINGLE'  # Aromatic bonds treated as single with special styling
                                                is_aromatic = True
                                            else:
                                                bond_type = 'SINGLE'
                                        else:
                                            bond_type = str(bond_type_raw)
                                        
                                        # Get atom positions
                                        pos1 = np.array([x_coords[atom1_idx], y_coords[atom1_idx], z_coords[atom1_idx]])
                                        pos2 = np.array([x_coords[atom2_idx], y_coords[atom2_idx], z_coords[atom2_idx]])
                                        
                                        # Check if either atom is hydrogen for bond length adjustment
                                        atom1_element = elements[atom1_idx] if atom1_idx < len(elements) else 'C'
                                        atom2_element = elements[atom2_idx] if atom2_idx < len(elements) else 'C'
                                        is_hydrogen_bond = atom1_element == 'H' or atom2_element == 'H'
                                        
                                        # Adjust bond length for hydrogen bonds (make them shorter)
                                        if is_hydrogen_bond:
                                            bond_vector = pos2 - pos1
                                            bond_center = (pos1 + pos2) / 2
                                            shortened_length = np.linalg.norm(bond_vector) * 0.7  # 70% of original length
                                            if np.linalg.norm(bond_vector) > 0:
                                                unit_vector = bond_vector / np.linalg.norm(bond_vector)
                                                half_shortened = unit_vector * (shortened_length / 2)
                                                pos1 = bond_center - half_shortened
                                                pos2 = bond_center + half_shortened
                                        
                                        # Determine bond color and width based on type, aromaticity, and changes
                                        base_width = 8  # Thicker base width for all bonds
                                        
                                        if bond_key in changed_bonds and show_changes:
                                            # Highlight bonds involved in conformational changes
                                            bond_color = '#FF1A1A'  # Bright red
                                            bond_width = base_width + 2
                                        elif (atom1_idx in displaced_atom_indices or atom2_idx in displaced_atom_indices) and show_changes:
                                            # Highlight bonds connected to moved atoms
                                            bond_color = '#FF8C00'  # Orange
                                            bond_width = base_width + 1
                                        elif bond_type == 'TRIPLE':
                                            # Triple bonds - blue color
                                            bond_color = '#0066CC'
                                            bond_width = base_width + 1
                                        elif bond_type == 'DOUBLE':
                                            # Double bonds - green color
                                            bond_color = '#228B22'
                                            bond_width = base_width
                                        elif is_aromatic:
                                            # Aromatic bonds - purple color
                                            bond_color = '#9932CC'
                                            bond_width = base_width
                                        else:
                                            # Single bonds - dark gray
                                            bond_color = '#404040'
                                            bond_width = base_width - 1
                                        
                                        # Draw bonds based on type
                                        if bond_type == 'DOUBLE' and not is_aromatic:
                                            # Double bond - draw two parallel lines
                                            bond_vector = pos2 - pos1
                                            bond_length = np.linalg.norm(bond_vector)
                                            
                                            if bond_length > 0:
                                                # Create perpendicular vector for offset
                                                if abs(bond_vector[2]) < 0.9:  # Not nearly vertical
                                                    perp_vector = np.array([bond_vector[1], -bond_vector[0], 0])
                                                else:  # Nearly vertical, use different perpendicular
                                                    perp_vector = np.array([1, 0, -bond_vector[0]/bond_vector[2]])
                                                
                                                perp_vector = perp_vector / np.linalg.norm(perp_vector)
                                                offset = perp_vector * 0.1  # Small offset for parallel lines
                                                
                                                # First line of double bond
                                                offset_pos1_1 = pos1 + offset
                                                offset_pos2_1 = pos2 + offset
                                                
                                                fig_3d.add_trace(go.Scatter3d(
                                                    x=[offset_pos1_1[0], offset_pos2_1[0], None],
                                                    y=[offset_pos1_1[1], offset_pos2_1[1], None],
                                                    z=[offset_pos1_1[2], offset_pos2_1[2], None],
                                                    mode='lines',
                                                    line=dict(color=bond_color, width=bond_width),
                                                    hoverinfo='none',
                                                    showlegend=False
                                                ))
                                                
                                                # Second line of double bond
                                                offset_pos1_2 = pos1 - offset
                                                offset_pos2_2 = pos2 - offset
                                                
                                                fig_3d.add_trace(go.Scatter3d(
                                                    x=[offset_pos1_2[0], offset_pos2_2[0], None],
                                                    y=[offset_pos1_2[1], offset_pos2_2[1], None],
                                                    z=[offset_pos1_2[2], offset_pos2_2[2], None],
                                                    mode='lines',
                                                    line=dict(color=bond_color, width=bond_width),
                                                    hoverinfo='none',
                                                    showlegend=False
                                                ))
                                            else:
                                                # Fallback to single line if bond length is zero
                                                fig_3d.add_trace(go.Scatter3d(
                                                    x=[pos1[0], pos2[0], None],
                                                    y=[pos1[1], pos2[1], None],
                                                    z=[pos1[2], pos2[2], None],
                                                    mode='lines',
                                                    line=dict(color=bond_color, width=bond_width),
                                                    hoverinfo='none',
                                                    showlegend=False
                                                ))
                                        
                                        elif bond_type == 'TRIPLE':
                                            # Triple bond - draw three lines (center line + two offset lines)
                                            bond_vector = pos2 - pos1
                                            bond_length = np.linalg.norm(bond_vector)
                                            
                                            if bond_length > 0:
                                                # Create two perpendicular vectors for offsets
                                                if abs(bond_vector[2]) < 0.9:
                                                    perp_vector1 = np.array([bond_vector[1], -bond_vector[0], 0])
                                                else:
                                                    perp_vector1 = np.array([1, 0, -bond_vector[0]/bond_vector[2]])
                                                
                                                perp_vector1 = perp_vector1 / np.linalg.norm(perp_vector1)
                                                perp_vector2 = np.cross(bond_vector, perp_vector1)
                                                perp_vector2 = perp_vector2 / np.linalg.norm(perp_vector2)
                                                
                                                offset1 = perp_vector1 * 0.1
                                                offset2 = perp_vector2 * 0.1
                                                
                                                # Center line
                                                fig_3d.add_trace(go.Scatter3d(
                                                    x=[pos1[0], pos2[0], None],
                                                    y=[pos1[1], pos2[1], None],
                                                    z=[pos1[2], pos2[2], None],
                                                    mode='lines',
                                                    line=dict(color=bond_color, width=bond_width),
                                                    hoverinfo='none',
                                                    showlegend=False
                                                ))
                                                
                                                # Two offset lines
                                                for offset in [offset1, offset2]:
                                                    offset_pos1 = pos1 + offset
                                                    offset_pos2 = pos2 + offset
                                                    
                                                    fig_3d.add_trace(go.Scatter3d(
                                                        x=[offset_pos1[0], offset_pos2[0], None],
                                                        y=[offset_pos1[1], offset_pos2[1], None],
                                                        z=[offset_pos1[2], offset_pos2[2], None],
                                                        mode='lines',
                                                        line=dict(color=bond_color, width=max(bond_width-1, 2)),
                                                        hoverinfo='none',
                                                        showlegend=False
                                                    ))
                                            else:
                                                # Fallback to single line
                                                fig_3d.add_trace(go.Scatter3d(
                                                    x=[pos1[0], pos2[0], None],
                                                    y=[pos1[1], pos2[1], None],
                                                    z=[pos1[2], pos2[2], None],
                                                    mode='lines',
                                                    line=dict(color=bond_color, width=bond_width),
                                                    hoverinfo='none',
                                                    showlegend=False
                                                ))
                                        else:
                                            # Single bond or aromatic (single line)
                                            fig_3d.add_trace(go.Scatter3d(
                                                x=[pos1[0], pos2[0], None],
                                                y=[pos1[1], pos2[1], None],
                                                z=[pos1[2], pos2[2], None],
                                                mode='lines',
                                                line=dict(color=bond_color, width=bond_width),
                                                hoverinfo='none',
                                                showlegend=False
                                            ))
                                    
                                    # Update layout
                                    fig_3d.update_layout(
                                        title=f'3D Structure - Conformer {conformer_idx + 1}',
                                        scene=dict(
                                            xaxis_title='X (Å)',
                                            yaxis_title='Y (Å)', 
                                            zaxis_title='Z (Å)',
                                            aspectmode='cube'
                                        ),
                                        height=500,
                                        margin=dict(l=0, r=0, t=50, b=0)
                                    )
                                    
                                    st.plotly_chart(fig_3d, use_container_width=True)
                                    
                                    # Show change legend if changes are displayed
                                    if show_changes and conformational_change_data:
                                        st.subheader("🎨 Change Visualization Legend")
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.markdown("""
                                            **Atom Colors:**
                                            - 🔴 **Red**: Major displacement (>2.0 Å)
                                            - 🟠 **Orange**: Minor displacement (1.0-2.0 Å)
                                            - **Dark Gray**: Aromatic carbons
                                            - **CPK Colors**: Normal atoms (unchanged)
                                            """)
                                        with col2:
                                            st.markdown("""
                                            **Bond Types & Colors:**
                                            - 🔵 **Blue**: Triple bonds (C≡C, C≡N, etc.)
                                            - 🟢 **Green**: Double bonds (C=C, C=O, etc.)
                                            - 🟣 **Purple**: Aromatic bonds (benzene rings)
                                            - **Dark Gray**: Single bonds (C-C, C-H, etc.)
                                            - 🔴 **Red**: Bonds involved in torsion changes
                                            - 🟠 **Orange**: Bonds connected to moved atoms
                                            
                                            **Note**: Hydrogen bonds are shortened for clarity
                                            """)
                                    
                                    # Display conformer information
                                    selected_conformer = conformers[conformer_idx]
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Energy", f"{selected_conformer.get('energy', 0):.3f} kcal/mol")
                                    with col2:
                                        st.metric("Relative Energy", f"{selected_conformer.get('relative_energy', 0):.3f} kcal/mol")
                                    with col3:
                                        st.metric("Atoms", len(atoms))
                                else:
                                    st.error("No atom data available for visualization")
                            else:
                                st.error(f"3D visualization error: {mol_3d_data.get('error', 'Unknown error')}")
                                
                        except Exception as e:
                            st.error(f"3D visualization error: {str(e)}")
                            st.code(f"Error details: {e}")
                else:
                    st.info("No conformers available for visualization.")
            else:
                st.info("3D visualization not available.")
        
        with tabs[3]:
            st.subheader("🔄 Conformational Change Analysis")
            
            if len(conformers) < 2:
                st.info("At least 2 conformers are required for change analysis.")
            else:
                # Global change analysis
                st.subheader("📊 Overall Flexibility Analysis")
                
                try:
                    # Perform global conformational change analysis
                    global_cache_key = f"global_change_analysis_{smiles}"
                    
                    if global_cache_key not in st.session_state:
                        with st.spinner("Performing global conformational analysis..."):
                            global_analysis = adapter.analyze_conformational_changes(smiles=smiles, num_conformers=len(conformers))
                        st.session_state[global_cache_key] = global_analysis
                    else:
                        global_analysis = st.session_state[global_cache_key]
                    
                    if global_analysis and not global_analysis.get('error'):
                        # Display global flexibility metrics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Major Changes", global_analysis.get('change_summary', {}).get('major', 0))
                        with col2:
                            st.metric("Moderate Changes", global_analysis.get('change_summary', {}).get('moderate', 0))
                        with col3:
                            st.metric("Minor Changes", global_analysis.get('change_summary', {}).get('minor', 0))
                        with col4:
                            st.metric("Total Comparisons", global_analysis.get('num_comparisons', 0))
                        
                        # Most flexible atoms
                        if 'most_flexible_atoms' in global_analysis and global_analysis['most_flexible_atoms']:
                            st.subheader("🎯 Most Flexible Regions")
                            flexible_data = []
                            for atom_idx, flexibility_info in global_analysis['most_flexible_atoms']:
                                flexible_data.append({
                                    'Atom Index': atom_idx,
                                    'Element': flexibility_info['element'],
                                    'Avg Displacement (Å)': round(flexibility_info['avg_displacement'], 3),
                                    'Max Displacement (Å)': round(flexibility_info['max_displacement'], 3),
                                    'Flexibility Score': round(flexibility_info['flexibility_score'], 3)
                                })
                            
                            if flexible_data:
                                df_flexible = pd.DataFrame(flexible_data)
                                st.dataframe(df_flexible, use_container_width=True)
                                
                                # Visualization of flexibility
                                fig_flexibility = px.bar(
                                    df_flexible.head(10), 
                                    x='Atom Index', 
                                    y='Flexibility Score',
                                    color='Element',
                                    title="Top 10 Most Flexible Atoms",
                                    labels={'Flexibility Score': 'Flexibility Score', 'Atom Index': 'Atom Index'}
                                )
                                st.plotly_chart(fig_flexibility, use_container_width=True)
                        
                        # Pairwise change analysis
                        st.subheader("🔍 Detailed Pairwise Analysis")
                        all_comparisons = global_analysis.get('all_comparisons', [])
                        
                        if all_comparisons:
                            # Create comparison summary table
                            comparison_data = []
                            for comp in all_comparisons:
                                conf_pair = comp.get('conformer_pair', (0, 1))
                                comparison_data.append({
                                    'Conformer Pair': f"Conf_{conf_pair[0]+1} vs Conf_{conf_pair[1]+1}",
                                    'Change Magnitude': comp.get('change_magnitude', 'N/A').title(),
                                    'Max Displacement (Å)': round(comp.get('max_displacement', 0), 3),
                                    'Max Angle Change (°)': round(comp.get('max_angle_change', 0), 1),
                                    'Torsion Changes': comp.get('num_torsion_changes', 0),
                                    'Displaced Atoms': comp.get('num_displaced_atoms', 0)
                                })
                            
                            df_comparisons = pd.DataFrame(comparison_data)
                            st.dataframe(df_comparisons, use_container_width=True)
                            
                            # Filter for detailed view
                            selected_comparison = st.selectbox(
                                "Select comparison for detailed analysis:",
                                options=range(len(comparison_data)),
                                format_func=lambda x: comparison_data[x]['Conformer Pair'],
                                key="detailed_comparison_selector"
                            )
                            
                            if selected_comparison is not None:
                                selected_comp = all_comparisons[selected_comparison]
                                
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.subheader("🔄 Torsion Changes")
                                    torsion_changes = selected_comp.get('torsion_changes', [])
                                    if torsion_changes:
                                        torsion_data = []
                                        for torsion in torsion_changes:
                                            torsion_data.append({
                                                'Bond': f"{torsion['bond_atoms'][0]}-{torsion['bond_atoms'][1]}",
                                                'Angle Change (°)': round(torsion['angle_change'], 1),
                                                'Type': torsion['change_type'].title()
                                            })
                                        df_torsions = pd.DataFrame(torsion_data)
                                        st.dataframe(df_torsions, use_container_width=True)
                                    else:
                                        st.info("No significant torsion changes detected.")
                                
                                with col2:
                                    st.subheader("📍 Displaced Atoms")
                                    displaced_atoms = selected_comp.get('displaced_atoms', [])
                                    if displaced_atoms:
                                        displacement_data = []
                                        for atom in displaced_atoms:
                                            displacement_data.append({
                                                'Atom Index': atom['atom_idx'],
                                                'Element': atom['element'],
                                                'Displacement (Å)': round(atom['displacement'], 3),
                                                'Type': atom['change_type'].title()
                                            })
                                        df_displacements = pd.DataFrame(displacement_data)
                                        st.dataframe(df_displacements, use_container_width=True)
                                    else:
                                        st.info("No significant atom displacements detected.")
                        
                    else:
                        st.error(f"Global analysis failed: {global_analysis.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"Error in conformational change analysis: {str(e)}")
        
        with tabs[4]:
            st.subheader("Raw Analysis Data")
            st.json(conformational_results)
            
            # Download button
            import json
            from datetime import datetime
            json_str = json.dumps(conformational_results, indent=2, default=str)
            st.download_button(
                label="Download Conformational Analysis Results",
                data=json_str,
                file_name=f"conformational_analysis_{smiles}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )