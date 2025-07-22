
"""
Molecular Analyzer Streamlit Web Application v2
Enhanced with Independent UI Components and Adapter Pattern

A comprehensive web interface for molecular analysis, visualization, and comparison
built using the new modular component system.
"""

# Page configuration - MUST be first Streamlit command
import streamlit as st
st.set_page_config(
    page_title="Molecular Analyzer v2",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
from datetime import datetime

# Add paths for components and integration
src_path = Path(__file__).parent.parent / "src"
integration_path = Path(__file__).parent.parent / "integration"
components_path = Path(__file__).parent

for path in [src_path, integration_path, components_path]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

try:
    # Import integration adapter
    from adapter_v2 import AdapterFactory, MolecularAnalyzerAdapter
    
    # Import UI components
    from components.charts.visualization_manager import VisualizationManagerComponent
    from components.charts.molecule_3d import Molecule3DComponent
    from components.charts.bar_chart import BarChartComponent
    from components.charts.scatter_plot import ScatterPlotComponent
    from components.charts.line_plot import LinePlotComponent
    from components.charts.histogram import HistogramComponent
    from components.charts.correlation_matrix import CorrelationMatrixComponent
    from components.charts.distribution_plot import DistributionPlotComponent
    from components.charts.radar_chart import RadarChartComponent
    from components.input.molecule_input import MoleculeInputComponent
    from components.display.message_display import MessageDisplayComponent
    from components.progress.progress_bar import ProgressBarComponent
    from components.progress.status_tracker import StatusTrackerComponent
    from components.progress.analytics_dashboard import AnalyticsDashboardComponent
    from components.progress.operation_history import OperationHistoryComponent
    from components.conformational_analysis_component import conformational_analysis_component
    from components.advanced_analysis_component import advanced_analysis_component
    
    # Import RDKit for basic molecular operations
    from rdkit import Chem
    from rdkit.Chem import Draw
    
    # Initialize adapter with explicit error checking
    @st.cache_resource
    def create_adapter():
        """Create and cache the molecular analyzer adapter."""
        adapter = AdapterFactory.create_auto_adapter()
        # Verify the adapter has required methods
        if not hasattr(adapter, 'get_3d_visualization'):
            st.error(f"Adapter missing get_3d_visualization method. Type: {type(adapter)}")
            st.error(f"Available methods: {[m for m in dir(adapter) if not m.startswith('_')]}")
            raise AttributeError("Adapter missing required methods")
        return adapter
    
    adapter = create_adapter()
    
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Please ensure all required modules are installed and available")
    st.stop()

# Helper function to fix dataframe types for Streamlit display
def fix_dataframe_types(df):
    """Convert dataframe columns to appropriate types to avoid Arrow serialization issues."""
    df_fixed = df.copy()
    for col in df_fixed.columns:
        try:
            # Try to keep numeric columns as numeric
            if df_fixed[col].dtype in ['object']:
                # Check if all non-null values can be converted to numeric
                non_null_values = df_fixed[col].dropna()
                if not non_null_values.empty:
                    try:
                        pd.to_numeric(non_null_values)
                        df_fixed[col] = pd.to_numeric(df_fixed[col], errors='coerce')
                    except (ValueError, TypeError):
                        # If can't convert to numeric, convert to string
                        df_fixed[col] = df_fixed[col].astype('string')
            elif df_fixed[col].dtype in ['int64', 'float64']:
                # Keep numeric types as is
                pass
            else:
                # Convert other types to string
                df_fixed[col] = df_fixed[col].astype('string')
        except Exception:
            # If anything fails, convert to string as fallback
            df_fixed[col] = df_fixed[col].astype('string')
    return df_fixed

# Initialize session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = {}
if 'comparison_results' not in st.session_state:
    st.session_state.comparison_results = {}
if 'batch_results' not in st.session_state:
    st.session_state.batch_results = None

# Initialize components
@st.cache_resource
def get_components():
    """Initialize and cache UI components"""
    return {
        'visualization_manager': VisualizationManagerComponent(),
        'molecule_3d': Molecule3DComponent(),
        'bar_chart': BarChartComponent(),
        'scatter_plot': ScatterPlotComponent(),
        'line_plot': LinePlotComponent(),
        'histogram': HistogramComponent(),
        'correlation_matrix': CorrelationMatrixComponent(),
        'distribution_plot': DistributionPlotComponent(),
        'molecule_input': MoleculeInputComponent(),
        'message_display': MessageDisplayComponent(),
        'progress_bar': ProgressBarComponent(),
        'status_tracker': StatusTrackerComponent(),
        'analytics_dashboard': AnalyticsDashboardComponent(),
        'operation_history': OperationHistoryComponent(),
        'radar_chart': RadarChartComponent()
    }

components = get_components()

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1.5rem;
        background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%);
        border-radius: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .info-box {
        background: linear-gradient(135deg, #DBEAFE 0%, #EBF8FF 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #3B82F6;
        margin: 1.5rem 0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .tab-container {
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .success-box {
        background: linear-gradient(135deg, #D1FAE5 0%, #ECFDF5 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #10B981;
        margin: 1.5rem 0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .error-box {
        background: linear-gradient(135deg, #FEE2E2 0%, #FEF2F2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #EF4444;
        margin: 1.5rem 0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .warning-box {
        background: linear-gradient(135deg, #FEF3C7 0%, #FFFBEB 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #F59E0B;
        margin: 1.5rem 0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<div class="main-header">🧬 Molecular Analyzer v2</div>', unsafe_allow_html=True)

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Choose Analysis Type",
    ["Single Molecule Analysis", "Batch Analysis", "Molecule Comparison", "Conformational Analysis", "Advanced Analysis", "System Info"]
)

st.sidebar.markdown("--- ")
components['operation_history'].render()

# Display adapter capabilities
capabilities = adapter.get_capabilities()
if not capabilities.get('core_analysis', False):
    components['message_display'].show_error("Core analysis module not available. Please check your installation.")
    st.stop()

# Single Molecule Analysis Page
if page == "Single Molecule Analysis":
    st.header("Single Molecule Analysis")
    
    # Molecule input section
    st.subheader("Molecule Input")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Use the molecule input component
        molecule_data = components['molecule_input'].render()
        
        if molecule_data and isinstance(molecule_data, str):
            smiles = molecule_data
            
            # Progress tracking
            progress_container = st.container()
            with progress_container:
                progress_bar = components['progress_bar']
                progress_bar.start_progress(max_value=100, initial_value=0)
                progress_bar.render(progress_type="advanced")
            
            # Perform analysis
            try:
                # Update progress
                components['progress_bar'].update_progress(25, "Validating SMILES...")
                
                # Analyze molecule using adapter
                analysis_results = adapter.analyze_single_molecule(smiles)
                
                components['progress_bar'].update_progress(50, "Calculating properties...")
                
                if analysis_results.get('error'):
                    components['message_display'].show_error(f"Analysis failed: {analysis_results['error']}")
                else:
                    components['progress_bar'].update_progress(75, "Generating visualizations...")
                    
                    # Store results
                    st.session_state.analysis_results = analysis_results
                    
                    components['progress_bar'].update_progress(100, "Analysis complete!")
                    
                    # Display results
                    st.success("Analysis completed successfully!")
                    
                    # Create tabs for different views
                    tabs = st.tabs(["Properties", "Visualizations", "3D Structure", "Raw Data", "Radar Chart"])
                    
                    with tabs[0]:
                        st.subheader("Molecular Properties")
                        
                        if 'properties' in analysis_results:
                            properties = analysis_results['properties']
                            
                            # Display properties using bar chart
                            if isinstance(properties, dict):
                                # Convert to format suitable for bar chart
                                prop_data = pd.DataFrame([
                                    {'Property': str(k), 'Value': float(v)} 
                                    for k, v in properties.items() 
                                    if isinstance(v, (int, float)) and not pd.isna(v)
                                ])
                                # Ensure proper data types
                                if not prop_data.empty:
                                    prop_data = fix_dataframe_types(prop_data)
                                
                                if not prop_data.empty:
                                    fig = components['bar_chart'].create_chart(
                                        data=prop_data,
                                        x_column='Property',
                                        y_column='Value',
                                        custom_config={'title': 'Molecular Properties'}
                                    )
                                    if fig is not None:
                                        st.plotly_chart(fig, use_container_width=True)
                                    else:
                                        st.error("Failed to generate properties chart")
                                
                                # Display all properties in a table
                                st.subheader("All Properties")
                                prop_df = pd.DataFrame([
                                    {'Property': str(k), 'Value': str(v)} 
                                    for k, v in properties.items()
                                ])
                                # Fix column types to avoid Arrow conversion issues
                                prop_df = fix_dataframe_types(prop_df)
                                st.dataframe(prop_df, use_container_width=True)
                        else:
                            components['message_display'].show_warning("No properties calculated")
                    
                    with tabs[1]:
                        st.subheader("Property Visualizations")
                        
                        # Handle both nested and flat property structures
                        if 'properties' in analysis_results:
                            properties = analysis_results['properties']
                        else:
                            # Properties might be at the top level
                            properties = {k: v for k, v in analysis_results.items() 
                                        if k not in ['error', 'smiles', 'mol'] and not k.startswith('_')}
                        
                        if properties:
                            # Use visualization manager to create charts
                            viz_manager = components['visualization_manager']
                            
                            # Create histogram of property values
                            numeric_props = {k: v for k, v in properties.items() if isinstance(v, (int, float))}
                            if numeric_props:
                                prop_values = list(numeric_props.values())
                                prop_names = list(numeric_props.keys())
                                
                                # Create histogram
                                hist_data = pd.DataFrame({
                                    'Values': [float(v) for v in prop_values], 
                                    'Properties': [str(p) for p in prop_names]
                                })
                                hist_data = fix_dataframe_types(hist_data)
                                
                                hist_fig = components['histogram'].create_chart(
                                    data=hist_data,
                                    column='Values',
                                    custom_config={'title': 'Property Value Distribution'}
                                )
                                if hist_fig is not None:
                                    st.plotly_chart(hist_fig, use_container_width=True)
                                else:
                                    st.error("Failed to generate histogram chart")
                    
                    with tabs[2]:
                        st.subheader("3D Molecular Structure")
                        
                        # Use 3D molecule component
                        if capabilities.get('3d_visualization', False):
                            try:
                                mol_3d_data = adapter.get_3d_visualization(smiles)
                                if mol_3d_data.get('error'):
                                    components['message_display'].show_warning(f"3D visualization not available: {mol_3d_data['error']}")
                                else:
                                    # Use the 3D molecule component with proper data
                                    fig_3d = components['molecule_3d'].create_3d_visualization(
                                        mol_data=mol_3d_data,  # Pass the actual 3D data, not SMILES
                                        custom_config={'title': '3D Molecular Structure'}
                                    )
                                    if fig_3d is not None:
                                        st.plotly_chart(fig_3d, use_container_width=True)
                                    else:
                                        st.error("Failed to generate 3D visualization")
                            except AttributeError as e:
                                st.error(f"Adapter missing method: {str(e)}")
                                st.info("Try refreshing the page to reload the adapter")
                            except Exception as e:
                                st.error(f"3D visualization error: {str(e)}")
                        else:
                            components['message_display'].show_info("3D visualization module not available")
                    
                    with tabs[3]:
                        st.subheader("Raw Analysis Data")
                        st.json(analysis_results)
                        
                        # Download button
                        json_str = json.dumps(analysis_results, indent=2)
                        st.download_button(
                            label="Download Analysis Results",
                            data=json_str,
                            file_name=f"analysis_{smiles}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )

                    with tabs[4]:
                        st.subheader("Molecular Property Radar Chart")
                        if 'properties' in analysis_results:
                            properties = analysis_results['properties']
                            numeric_props = {k: v for k, v in properties.items() if isinstance(v, (int, float)) and not pd.isna(v)}
                            if numeric_props:
                                # Normalize properties for radar chart (simple min-max scaling for demonstration)
                                # In a real application, you'd use domain-specific normalization
                                min_val = min(numeric_props.values())
                                max_val = max(numeric_props.values())
                                
                                if max_val == min_val:
                                    normalized_props = {k: 0.5 for k in numeric_props} # Avoid division by zero
                                else:
                                    normalized_props = {k: (v - min_val) / (max_val - min_val) for k, v in numeric_props.items()}

                                fig = components['radar_chart'].create_chart(
                                    data=normalized_props,
                                    custom_config={'title': 'Normalized Molecular Properties'}
                                )
                                if fig is not None:
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.error("Failed to generate radar chart")
                            else:
                                components['message_display'].show_warning("No numeric properties available for radar chart.")
                        else:
                            components['message_display'].show_warning("No properties available for radar chart.")
                
            except Exception as e:
                components['message_display'].show_error(f"Analysis failed: {str(e)}")
    
    with col2:
        # Display molecule structure if available
        if 'analysis_results' in st.session_state and st.session_state.analysis_results:
            st.subheader("Molecule Structure")
            smiles = st.session_state.analysis_results.get('smiles', '')
            if smiles:
                try:
                    mol = Chem.MolFromSmiles(smiles)
                    if mol:
                        img = Draw.MolToImage(mol, size=(300, 300))
                        st.image(img, caption=f"SMILES: {smiles}")
                except Exception as e:
                    components['message_display'].show_warning(f"Could not display structure: {str(e)}")

# Conformational Analysis Page
elif page == "Conformational Analysis":
    st.header("Conformational Analysis")
    conformational_analysis_component()

# Advanced Analysis Page
elif page == "Advanced Analysis":
    st.header("Advanced Molecular Analysis")
    advanced_analysis_component()

# Batch Analysis Page
elif page == "Batch Analysis":
    st.header("Batch Molecular Analysis")
    
    # File upload or manual input
    input_method = st.radio("Choose input method:", ["Upload CSV", "Manual Input"])
    
    if input_method == "Upload CSV":
        uploaded_file = st.file_uploader("Upload CSV file with SMILES", type=['csv'])
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.write("Preview of uploaded data:")
                # Fix dataframe types to avoid Arrow issues
                df_display = fix_dataframe_types(df.head())
                st.dataframe(df_display)
                
                # Check for SMILES column
                smiles_column = st.selectbox("Select SMILES column:", df.columns)
                
                if st.button("Analyze Batch"):
                    with st.spinner("Analyzing molecules..."):
                        # Use adapter for batch analysis
                        smiles_list = df[smiles_column].tolist()
                        
                        # Progress tracking
                        progress_container = st.container()
                        with progress_container:
                            progress_bar = components['progress_bar']
                            progress_bar.start_progress(max_value=100, initial_value=0)
                            progress_bar.render(progress_type="advanced")
                        
                        # Perform batch analysis
                        batch_results = adapter.batch_analyze(smiles_list)
                        
                        components['progress_bar'].update_progress(100, "Batch analysis complete!")
                        
                        if isinstance(batch_results, list) and batch_results:
                            # Convert list of results to DataFrame for display
                            flattened_results = []
                            for result in batch_results:
                                # Flatten the result structure
                                flat_result = {
                                    'SMILES': result.get('smiles', ''),
                                    'Valid': result.get('valid', False),
                                    'Error': result.get('error', ''),
                                }
                                # Add properties if available
                                properties = result.get('properties', {})
                                if properties:
                                    flat_result.update(properties)
                                
                                flattened_results.append(flat_result)
                            
                            # Create DataFrame
                            batch_df = pd.DataFrame(flattened_results)
                            st.session_state.batch_results = batch_df
                            
                            # Count successful analyses
                            valid_count = sum(1 for r in batch_results if r.get('valid', False))
                            st.success(f"Successfully analyzed {valid_count}/{len(batch_results)} molecules!")
                            
                            # Display results
                            st.subheader("Batch Analysis Results")
                            batch_display = fix_dataframe_types(batch_df)
                            st.dataframe(batch_display, use_container_width=True)
                            
                            # Show summary statistics
                            if valid_count > 0:
                                st.subheader("Batch Analysis Summary")
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Total Molecules", len(batch_results))
                                with col2:
                                    st.metric("Valid Molecules", valid_count)
                                with col3:
                                    success_rate = (valid_count / len(batch_results)) * 100
                                    st.metric("Success Rate", f"{success_rate:.1f}%")
                        else:
                            components['message_display'].show_error("Batch analysis failed or returned no results")
                            
            except Exception as e:
                components['message_display'].show_error(f"Error processing file: {str(e)}")
    
    else:  # Manual Input
        st.subheader("Manual SMILES Input")
        smiles_input = st.text_area("Enter SMILES (one per line):", height=150)
        
        if st.button("Analyze SMILES List"):
            if smiles_input.strip():
                smiles_list = [s.strip() for s in smiles_input.split('\n') if s.strip()]
                
                with st.spinner(f"Analyzing {len(smiles_list)} molecules..."):
                    batch_results = adapter.batch_analyze(smiles_list)
                    
                    if isinstance(batch_results, list) and batch_results:
                        # Convert list of results to DataFrame for display
                        flattened_results = []
                        for result in batch_results:
                            # Flatten the result structure
                            flat_result = {
                                'SMILES': result.get('smiles', ''),
                                'Valid': result.get('valid', False),
                                'Error': result.get('error', ''),
                            }
                            # Add properties if available
                            properties = result.get('properties', {})
                            if properties:
                                flat_result.update(properties)
                            
                            flattened_results.append(flat_result)
                        
                        # Create DataFrame
                        batch_df = pd.DataFrame(flattened_results)
                        st.session_state.batch_results = batch_df
                        
                        # Count successful analyses
                        valid_count = sum(1 for r in batch_results if r.get('valid', False))
                        st.success(f"Successfully analyzed {valid_count}/{len(batch_results)} molecules!")
                        
                        # Display results
                        batch_display = fix_dataframe_types(batch_df)
                        st.dataframe(batch_display, use_container_width=True)
                        
                        # Show summary statistics
                        if valid_count > 0:
                            st.subheader("Batch Analysis Summary")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Molecules", len(batch_results))
                            with col2:
                                st.metric("Valid Molecules", valid_count)
                            with col3:
                                success_rate = (valid_count / len(batch_results)) * 100
                                st.metric("Success Rate", f"{success_rate:.1f}%")
                    else:
                        components['message_display'].show_error("Batch analysis failed or returned no results")

# Molecule Comparison Page
elif page == "Molecule Comparison":
    st.header("Molecule Comparison")
    
    # Input molecules for comparison
    st.subheader("Enter Molecules to Compare")
    num_molecules = st.slider("Number of molecules to compare:", 2, 5, 2)
    
    smiles_list = []
    cols = st.columns(num_molecules)
    
    for i in range(num_molecules):
        with cols[i]:
            smiles = st.text_input(f"SMILES {i+1}:", key=f"comp_smiles_{i}")
            if smiles:
                smiles_list.append(smiles)
    
    if len(smiles_list) >= 2 and st.button("Compare Molecules"):
        with st.spinner("Comparing molecules..."):
            # Use adapter for comparison
            comparison_results = adapter.compare_molecules(smiles_list)
            
            if comparison_results.get('error'):
                components['message_display'].show_error(f"Comparison failed: {comparison_results['error']}")
            else:
                st.session_state.comparison_results = comparison_results
                st.success("Comparison completed!")
                
                # Display comparison results
                st.subheader("Comparison Results")
                
                if 'molecules' in comparison_results:
                    molecules = comparison_results['molecules']
                    
                    # Create comparison table
                    comparison_data = []
                    for i, mol_data in enumerate(molecules):
                        row = {'Molecule': f"Molecule {i+1}", 'SMILES': mol_data.get('smiles', 'N/A')}
                        if 'properties' in mol_data:
                            row.update(mol_data['properties'])
                        comparison_data.append(row)
                    
                    comparison_df = pd.DataFrame(comparison_data)
                    # Fix dataframe types to avoid Arrow conversion issues
                    comparison_df = fix_dataframe_types(comparison_df)
                    st.dataframe(comparison_df)
                    
                    # Visualizations
                    st.subheader("Comparison Visualizations")
                    
                    # Bar chart comparison
                    numeric_cols = comparison_df.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 0:
                        property_to_compare = st.selectbox("Select property to compare:", numeric_cols)
                        
                        if property_to_compare:
                            comparison_chart = components['bar_chart'].create_chart(
                                data=comparison_df,
                                x_column='Molecule',
                                y_column=property_to_compare,
                                custom_config={'title': f'Comparison of {property_to_compare}'}
                            )
                            if comparison_chart is not None:
                                st.plotly_chart(comparison_chart, use_container_width=True)
                            else:
                                st.error("Failed to generate comparison chart")
                    
                    # Radar chart would go here if available
                    
                st.json(comparison_results)

# System Info Page
elif page == "System Info":
    st.header("System Information")
    
    # Display adapter capabilities
    st.subheader("Adapter Capabilities")
    capabilities = adapter.get_capabilities()
    
    cap_data = []
    for capability, available in capabilities.items():
        cap_data.append({
            'Capability': capability.replace('_', ' ').title(),
            'Available': '✅' if available else '❌',
            'Status': 'Available' if available else 'Not Available'
        })
    
    cap_df = pd.DataFrame(cap_data)
    # Fix dataframe types
    cap_df = fix_dataframe_types(cap_df)
    st.dataframe(cap_df, use_container_width=True)
    
    # Display module information
    st.subheader("Module Information")
    module_info = adapter.get_module_info()
    
    for key, value in module_info.items():
        if key != 'capabilities':
            st.write(f"**{key.replace('_', ' ').title()}**: {value}")
    
    # Component status
    st.subheader("UI Components Status")
    component_status = []
    for comp_name, comp_obj in components.items():
        try:
            # Try to check if component is working
            status = "✅ Working"
            if hasattr(comp_obj, 'test_component'):
                comp_obj.test_component()
        except Exception as e:
            status = f"❌ Error: {str(e)}"
        
        component_status.append({
            'Component': comp_name.replace('_', ' ').title(),
            'Status': status
        })
    
    comp_df = pd.DataFrame(component_status)
    # Fix dataframe types
    comp_df = fix_dataframe_types(comp_df)
    st.dataframe(comp_df, use_container_width=True)
    
    # Analytics dashboard
    st.subheader("Analytics Dashboard")
    analytics_data = {
        'total_analyses': len(st.session_state.get('analysis_results', {})),
        'batch_analyses': 1 if st.session_state.get('batch_results') is not None else 0,
        'comparisons': len(st.session_state.get('comparison_results', {}))
    }
    
    try:
        components['analytics_dashboard'].render(analytics_data)
    except Exception as e:
        components['message_display'].show_warning(f"Analytics dashboard not available: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center;">
    <strong>Molecular Analyzer v2</strong><br>
    🧬 Powered by RDKit and Streamlit<br>
    <small style="opacity: 0.6;">Developed by: SHAH MD. JALAL UDDIN | Contact: shahjalal2313@gmail.com</small>
</div>
""", unsafe_allow_html=True)
