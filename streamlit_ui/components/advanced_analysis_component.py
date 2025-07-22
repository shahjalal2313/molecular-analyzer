import streamlit as st
import sys
import os
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List
import numpy as np

# Add paths for integration
integration_path = Path(__file__).parent.parent.parent / "integration"
if str(integration_path) not in sys.path:
    sys.path.insert(0, str(integration_path))

try:
    from adapter_v2 import AdapterFactory
except ImportError:
    st.error("Could not import adapter. Please check your installation.")
    AdapterFactory = None

def advanced_analysis_component():
    st.subheader("Advanced Molecular Analysis & Recommendations")
    
    # Initialize adapter
    if AdapterFactory is None:
        st.error("Adapter not available. Cannot perform advanced analysis.")
        return
    
    try:
        adapter = AdapterFactory.create_auto_adapter()
    except Exception as e:
        st.error(f"Failed to create adapter: {str(e)}")
        return

    # Input section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        smiles = st.text_input("Enter SMILES string for advanced analysis:", "CCO")
        
    with col2:
        analysis_depth = st.selectbox("Analysis Depth", ["Standard", "Comprehensive", "Expert"], index=1)

    # Analysis parameters
    with st.expander("Analysis Configuration"):
        include_druglikeness = st.checkbox("Include Drug-likeness Assessment", value=True)
        include_toxicity = st.checkbox("Include Toxicity Prediction", value=True)
        include_synthesis = st.checkbox("Include Synthesis Recommendations", value=True)
        include_optimization = st.checkbox("Include Structure Optimization", value=True)
        
        # Property thresholds
        st.subheader("Property Thresholds")
        mw_threshold = st.slider("Molecular Weight Threshold", 100, 1000, 500)
        logp_threshold = st.slider("LogP Threshold", -2.0, 8.0, 5.0)

    if st.button("Perform Advanced Analysis", type="primary"):
        if not smiles.strip():
            st.warning("Please enter a SMILES string.")
            return
            
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("Initializing advanced analysis...")
            progress_bar.progress(10)
            
            # Check adapter capabilities
            capabilities = adapter.get_capabilities()
            if not capabilities.get('advanced_properties', False):
                st.error("Advanced properties analysis not supported by current adapter.")
                return
            
            status_text.text("Calculating molecular properties...")
            progress_bar.progress(25)
            
            # Get basic analysis first
            basic_results = adapter.analyze_single_molecule(smiles)
            if basic_results.get('error'):
                st.error(f"Basic analysis failed: {basic_results['error']}")
                return
            
            status_text.text("Performing advanced property calculations...")
            progress_bar.progress(50)
            
            # Perform advanced analysis
            advanced_results = adapter.perform_advanced_analysis(
                smiles=smiles,
                analysis_depth=analysis_depth.lower(),
                include_druglikeness=include_druglikeness,
                include_toxicity=include_toxicity,
                include_synthesis=include_synthesis,
                include_optimization=include_optimization,
                property_thresholds={
                    'molecular_weight': mw_threshold,
                    'logp': logp_threshold
                }
            )
            
            progress_bar.progress(75)
            status_text.text("Generating recommendations...")
            
            if advanced_results.get('error'):
                st.error(f"Advanced analysis failed: {advanced_results['error']}")
                return
            
            progress_bar.progress(100)
            status_text.text("Analysis complete!")
            
            # Display results
            st.success("Advanced analysis completed successfully!")
            
            # Create tabs for different views
            tabs = st.tabs(["Property Analysis", "Drug-likeness", "Recommendations", "Optimization", "Raw Data"])
            
            with tabs[0]:
                st.subheader("Advanced Property Analysis")
                
                # Combine basic and advanced properties
                all_properties = {}
                if 'properties' in basic_results:
                    all_properties.update(basic_results['properties'])
                if 'advanced_properties' in advanced_results:
                    all_properties.update(advanced_results['advanced_properties'])
                
                if all_properties:
                    # Create property comparison with thresholds
                    prop_analysis = []
                    for prop, value in all_properties.items():
                        if isinstance(value, (int, float)) and not pd.isna(value):
                            # Define property ranges (simplified)
                            status = "✅ Good"
                            if prop.lower() == 'molecular_weight':
                                status = "✅ Good" if value <= mw_threshold else "⚠️ High"
                            elif 'logp' in prop.lower():
                                status = "✅ Good" if value <= logp_threshold else "⚠️ High"
                            elif 'violations' in prop.lower():
                                status = "✅ Good" if value == 0 else f"⚠️ {int(value)} violations"
                            
                            prop_analysis.append({
                                'Property': prop.replace('_', ' ').title(),
                                'Value': round(value, 3) if isinstance(value, float) else value,
                                'Status': status
                            })
                    
                    prop_df = pd.DataFrame(prop_analysis)
                    st.dataframe(prop_df, use_container_width=True)
                    
                    # Property radar chart
                    numeric_props = {k: v for k, v in all_properties.items() 
                                   if isinstance(v, (int, float)) and not pd.isna(v)}
                    if len(numeric_props) >= 3:
                        # Normalize properties for radar chart
                        normalized_props = {}
                        for prop, value in numeric_props.items():
                            if prop.lower() == 'molecular_weight':
                                normalized_props[prop] = min(value / 500, 1.0)  # Normalize to 500 Da
                            elif 'logp' in prop.lower():
                                normalized_props[prop] = min(abs(value) / 5, 1.0)  # Normalize to ±5
                            else:
                                # Simple min-max normalization
                                all_values = list(numeric_props.values())
                                min_val, max_val = min(all_values), max(all_values)
                                if max_val != min_val:
                                    normalized_props[prop] = (value - min_val) / (max_val - min_val)
                                else:
                                    normalized_props[prop] = 0.5
                        
                        # Create radar chart
                        categories = list(normalized_props.keys())
                        values = list(normalized_props.values())
                        
                        fig_radar = go.Figure()
                        fig_radar.add_trace(go.Scatterpolar(
                            r=values,
                            theta=categories,
                            fill='toself',
                            name='Properties'
                        ))
                        fig_radar.update_layout(
                            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                            showlegend=True,
                            title="Normalized Property Profile"
                        )
                        st.plotly_chart(fig_radar, use_container_width=True)
            
            with tabs[1]:
                st.subheader("Drug-likeness Assessment")
                
                if include_druglikeness and 'druglikeness' in advanced_results:
                    druglikeness = advanced_results['druglikeness']
                    
                    # Overall score
                    overall_score = druglikeness.get('overall_score', 0)
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Drug-likeness Score", f"{overall_score:.2f}/1.0")
                    with col2:
                        lipinski_violations = druglikeness.get('lipinski_violations', 0)
                        st.metric("Lipinski Violations", lipinski_violations)
                    with col3:
                        veber_violations = druglikeness.get('veber_violations', 0)
                        st.metric("Veber Violations", veber_violations)
                    
                    # Rule compliance
                    st.subheader("Rule Compliance")
                    rules_data = []
                    for rule, passed in druglikeness.get('rules', {}).items():
                        rules_data.append({
                            'Rule': rule.replace('_', ' ').title(),
                            'Status': '✅ Pass' if passed else '❌ Fail',
                            'Compliant': passed
                        })
                    
                    if rules_data:
                        rules_df = pd.DataFrame(rules_data)
                        st.dataframe(rules_df, use_container_width=True)
                else:
                    st.info("Drug-likeness assessment not performed or not available.")
            
            with tabs[2]:
                st.subheader("Recommendations")
                
                if 'recommendations' in advanced_results:
                    recommendations = advanced_results['recommendations']
                    
                    # Priority recommendations
                    if 'priority' in recommendations:
                        st.markdown("#### 🔥 Priority Recommendations")
                        for rec in recommendations['priority']:
                            st.warning(f"**{rec.get('type', 'Recommendation')}**: {rec.get('message', 'N/A')}")
                    
                    # General recommendations
                    if 'general' in recommendations:
                        st.markdown("#### 💡 General Recommendations")
                        for rec in recommendations['general']:
                            st.info(f"**{rec.get('type', 'Suggestion')}**: {rec.get('message', 'N/A')}")
                    
                    # Optimization suggestions
                    if 'optimization' in recommendations:
                        st.markdown("#### ⚡ Optimization Suggestions")
                        for opt in recommendations['optimization']:
                            st.success(f"**{opt.get('property', 'Property')}**: {opt.get('suggestion', 'N/A')}")
                else:
                    st.info("No specific recommendations generated.")
            
            with tabs[3]:
                st.subheader("Structure Optimization")
                
                if include_optimization and 'optimization' in advanced_results:
                    optimization = advanced_results['optimization']
                    
                    # Optimization targets
                    if 'targets' in optimization:
                        st.markdown("#### 🎯 Optimization Targets")
                        targets_df = pd.DataFrame(optimization['targets'])
                        st.dataframe(targets_df, use_container_width=True)
                    
                    # Suggested modifications
                    if 'modifications' in optimization:
                        st.markdown("#### 🔧 Suggested Modifications")
                        for mod in optimization['modifications']:
                            with st.expander(f"{mod.get('type', 'Modification')} - {mod.get('priority', 'Normal')} Priority"):
                                st.write(f"**Description**: {mod.get('description', 'N/A')}")
                                st.write(f"**Expected Impact**: {mod.get('impact', 'N/A')}")
                                if 'smiles' in mod:
                                    st.write(f"**Modified SMILES**: `{mod['smiles']}`")
                else:
                    st.info("Structure optimization not performed or not available.")
            
            with tabs[4]:
                st.subheader("Raw Analysis Data")
                
                # Combine all results
                combined_results = {
                    'basic_analysis': basic_results,
                    'advanced_analysis': advanced_results
                }
                st.json(combined_results)
                
                # Download button
                import json
                from datetime import datetime
                json_str = json.dumps(combined_results, indent=2, default=str)
                st.download_button(
                    label="Download Advanced Analysis Results",
                    data=json_str,
                    file_name=f"advanced_analysis_{smiles}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
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