import streamlit as st
import sys
import os
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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
        include_rmsd_matrix = st.checkbox("Include RMSD Matrix", value=True, 
                                        key="conformational_include_rmsd_matrix")

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

    # Check if we need to run new analysis
    current_params = {
        'smiles': smiles,
        'num_conformers': num_conformers,
        'optimization_level': optimization_level,
        'energy_threshold': energy_threshold
    }
    
    params_changed = (
        st.session_state.conformational_params != current_params or 
        st.session_state.conformational_results is None
    )
    
    if run_analysis:
        if not smiles.strip():
            st.warning("Please enter a SMILES string.")
            return
            
        # Clear cached 3D visualization data if parameters changed
        if params_changed:
            # Clear all conformational 3D cache
            keys_to_remove = [key for key in st.session_state.keys() if key.startswith('conformational_3d_')]
            for key in keys_to_remove:
                del st.session_state[key]
        
        # Update session state parameters
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
        tabs = st.tabs(["Conformer Summary", "Energy Analysis", "3D Visualization", "Raw Data"])
        
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
                            col1, col2 = st.columns(2)
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
                                
                                if mol_3d_data.get('error'):
                                    st.warning(f"3D visualization error: {mol_3d_data['error']}")
                                    # Fallback: generate basic 3D structure
                                    st.info("Generating fallback 3D structure...")
                                    basic_3d_data = adapter.get_3d_visualization(smiles)
                                    if not basic_3d_data.get('error'):
                                        mol_3d_data = basic_3d_data
                                    else:
                                        st.error("Unable to generate 3D visualization.")
                                        mol_3d_data = None
                                
                                if mol_3d_data and not mol_3d_data.get('error'):
                                    # Import the 3D component with absolute import
                                    try:
                                        # Try to import directly from streamlit_ui components
                                        import sys
                                        from pathlib import Path
                                        
                                        # Add the streamlit_ui path
                                        streamlit_ui_path = Path(__file__).parent.parent.parent / "streamlit_ui"
                                        if str(streamlit_ui_path) not in sys.path:
                                            sys.path.insert(0, str(streamlit_ui_path))
                                        
                                        # Direct import
                                        from components.charts.molecule_3d import Molecule3DComponent
                                    except ImportError:
                                        # Alternative: create the visualization directly using plotly
                                        st.warning("Using fallback 3D visualization...")
                                        
                                        # Create basic 3D plot directly
                                        import plotly.graph_objects as go
                                        
                                        atoms = mol_3d_data.get('atoms', [])
                                        bonds = mol_3d_data.get('bonds', [])
                                        
                                        # CPK colors for atoms
                                        element_colors = {
                                            'H': '#FFFFFF', 'C': '#222222', 'N': '#3050F8', 'O': '#FF0D0D',
                                            'S': '#FFFF30', 'P': '#FF8000', 'F': '#90E050', 'Cl': '#1FF01F'
                                        }
                                        
                                        # Atom sizes
                                        element_sizes = {
                                            'H': 6, 'C': 18, 'N': 16, 'O': 16, 'S': 20, 'P': 20, 'F': 16, 'Cl': 18
                                        }
                                        
                                        if atoms:
                                            # Extract atom positions and properties
                                            x_coords = [atom['x'] for atom in atoms]
                                            y_coords = [atom['y'] for atom in atoms]
                                            z_coords = [atom['z'] for atom in atoms]
                                            elements = [atom['element'] for atom in atoms]
                                            colors = [element_colors.get(elem, '#FF69B4') for elem in elements]
                                            sizes = [element_sizes.get(elem, 14) for elem in elements]
                                            
                                            # Create 3D scatter plot for atoms
                                            fig_3d = go.Figure()
                                            
                                            # Add atoms
                                            fig_3d.add_trace(go.Scatter3d(
                                                x=x_coords, y=y_coords, z=z_coords,
                                                mode='markers',
                                                marker=dict(size=sizes, color=colors, opacity=0.8),
                                                text=elements if show_labels else None,
                                                hovertext=[f"{elem} (Atom {i})" for i, elem in enumerate(elements)],
                                                name='Atoms'
                                            ))
                                            
                                            # Add bonds
                                            for bond in bonds:
                                                atom1_idx = bond['atom1']
                                                atom2_idx = bond['atom2']
                                                
                                                fig_3d.add_trace(go.Scatter3d(
                                                    x=[x_coords[atom1_idx], x_coords[atom2_idx], None],
                                                    y=[y_coords[atom1_idx], y_coords[atom2_idx], None],
                                                    z=[z_coords[atom1_idx], z_coords[atom2_idx], None],
                                                    mode='lines',
                                                    line=dict(color='gray', width=4),
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
                                            
                                            # Display conformer information
                                            selected_conformer = conformers[conformer_idx]
                                            col1, col2, col3 = st.columns(3)
                                            with col1:
                                                st.metric("Energy", f"{selected_conformer.get('energy', 0):.3f} kcal/mol")
                                            with col2:
                                                st.metric("Relative Energy", f"{selected_conformer.get('relative_energy', 0):.3f} kcal/mol")
                                            with col3:
                                                st.metric("Atoms", len(atoms))
                                            
                                            # Skip the rest of the original code block
                                            mol_3d_component = None
                                        else:
                                            st.error("No atom data available for visualization")
                                            mol_3d_component = None
                                    
                                    # Only run this part if we successfully imported Molecule3DComponent
                                    if 'Molecule3DComponent' in locals():
                                        # Create 3D visualization using the component
                                        mol_3d_component = Molecule3DComponent()
                                        
                                        # Configure visualization
                                        viz_config = {
                                            'title': f'3D Structure - Conformer {conformer_idx + 1}',
                                            'visualization_style': viz_style,
                                            'show_atom_labels': show_labels,
                                            'height': 500
                                        }
                                        
                                        # Render 3D visualization
                                        if 'atoms' in mol_3d_data and 'bonds' in mol_3d_data:
                                            fig_3d = mol_3d_component.create_3d_visualization(
                                                mol_data=mol_3d_data,
                                                custom_config=viz_config
                                            )
                                            
                                            if fig_3d is not None:
                                                st.plotly_chart(fig_3d, use_container_width=True)
                                                
                                                # Display conformer information
                                                selected_conformer = conformers[conformer_idx]
                                                col1, col2, col3 = st.columns(3)
                                                with col1:
                                                    st.metric("Energy", f"{selected_conformer.get('energy', 0):.3f} kcal/mol")
                                                with col2:
                                                    st.metric("Relative Energy", f"{selected_conformer.get('relative_energy', 0):.3f} kcal/mol")
                                                with col3:
                                                    st.metric("Atoms", len(mol_3d_data.get('atoms', [])))
                                            else:
                                                st.error("Failed to generate 3D visualization")
                                        else:
                                            st.error("Invalid molecular data for 3D visualization")
                                else:
                                    st.error("Unable to generate 3D molecular data")
                                    
                            except Exception as e:
                                st.error(f"3D visualization error: {str(e)}")
                                st.code(f"Error details: {e}")
                    else:
                        st.info("No conformers available for visualization.")
                else:
                    st.info("3D visualization not available.")
            
        with tabs[3]:
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
        
        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")
            st.write("Stack trace for debugging:")
            import traceback
            st.code(traceback.format_exc())
        
        finally:
            progress_bar.empty()
            status_text.empty()