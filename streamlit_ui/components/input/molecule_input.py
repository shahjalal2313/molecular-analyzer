"""
Molecule Input Components for Streamlit Application

This module provides reusable components for molecule input including SMILES entry,
molecule selection, and file upload functionality.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from rdkit import Chem
from rdkit.Chem import Draw

from ..base import BaseComponent


class MoleculeInputComponent(BaseComponent):
    """
    Component for various types of molecule input (SMILES, selection, file upload).
    
    Features:
    - Manual SMILES entry with validation
    - Predefined molecule selection
    - CSV file upload
    - Batch processing
    - Error handling and validation
    """
    
    def __init__(self, name: str = "Molecule Input", key_prefix: str = None):
        """
        Initialize the molecule input component.
        
        Args:
            name: Component display name
            key_prefix: Unique key prefix for Streamlit widgets
        """
        super().__init__(name, key_prefix)
        
        # Default example molecules
        self.default_examples = {
            "Simple Molecules": {
                "Water": "O",
                "Ethanol": "CCO", 
                "Methane": "C",
                "Acetone": "CC(=O)C",
                "Benzene": "C1=CC=CC=C1"
            },
            "Drug Molecules": {
                "Aspirin": "CC(=O)OC1=CC=CC=C1C(=O)O",
                "Caffeine": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
                "Ibuprofen": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",
                "Paracetamol": "CC(=O)NC1=CC=C(C=C1)O"
            },
            "Amino Acids": {
                "Glycine": "NCC(=O)O",
                "Alanine": "CC(N)C(=O)O",
                "Serine": "NC(CO)C(=O)O", 
                "Cysteine": "NC(CS)C(=O)O",
                "Phenylalanine": "NC(CC1=CC=CC=C1)C(=O)O"
            }
        }
    
    def validate_smiles(self, smiles: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a SMILES string.
        
        Args:
            smiles: SMILES string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not smiles or not isinstance(smiles, str):
                return False, "SMILES string is empty or invalid"
            
            smiles = smiles.strip()
            if len(smiles) == 0:
                return False, "SMILES string is empty"
            
            if len(smiles) > 1000:  # Reasonable length limit
                return False, "SMILES string too long (max 1000 characters)"
            
            # Basic validation - check for obviously invalid characters
            invalid_chars = set(smiles) - set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789()[]=#+-@./\\%")
            if invalid_chars:
                return False, f"Invalid characters found: {invalid_chars}"
            
            # Try to use RDKit if available for proper validation
            try:
                from rdkit import Chem
                mol = Chem.MolFromSmiles(smiles)
                if mol is None:
                    return False, "Invalid SMILES structure"
                return True, None
            except ImportError:
                # If RDKit not available, do basic validation
                if smiles.count('(') != smiles.count(')'):
                    return False, "Unmatched parentheses"
                if smiles.count('[') != smiles.count(']'):
                    return False, "Unmatched brackets"
                return True, None
                
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def render_smiles_input(self, 
                           label: str = "Enter SMILES string",
                           placeholder: str = "e.g., CCO (ethanol)",
                           show_validation: bool = True,
                           key_suffix: str = "") -> Optional[str]:
        """
        Render SMILES input field with validation and 2D preview.
        
        Args:
            label: Input field label
            placeholder: Placeholder text
            show_validation: Whether to show validation feedback
            key_suffix: Suffix for unique component keys
            
        Returns:
            Valid SMILES string or None
        """
        try:
            # Input field
            smiles_input = st.text_input(
                label=label,
                placeholder=placeholder,
                help="Enter a valid SMILES string for molecular structure",
                key=self.get_key(f'smiles_input_{key_suffix}'),
                max_chars=1000,
                on_change=self._update_smiles_preview, # Trigger update on change
                args=(self.get_key(f'smiles_input_{key_suffix}'),)
            )
            
            # Get current SMILES from session state for real-time preview
            current_smiles = st.session_state.get(self.get_key(f'smiles_input_{key_suffix}'), '')

            # Early return if no input
            if not current_smiles or not current_smiles.strip():
                return None
                
            current_smiles = current_smiles.strip()
            
            # Validation and Preview
            if show_validation:
                is_valid, error_msg = self.validate_smiles(current_smiles)
                
                if is_valid:
                    st.success("Valid SMILES structure")
                    try:
                        mol = Chem.MolFromSmiles(current_smiles)
                        if mol:
                            img = Draw.MolToImage(mol, size=(200, 200))
                            st.image(img, caption="2D Structure Preview")
                    except Exception:
                        st.warning("Could not generate 2D preview.")
                    return current_smiles
                else:
                    st.error(f"Invalid SMILES: {error_msg}")
                    return None
            else:
                return current_smiles
                
        except Exception as e:
            self.add_error(f"Error in SMILES input: {str(e)}", e)
            return None

    def _update_smiles_preview(self, key):
        """Callback to update the SMILES preview when input changes."""
        # This function is a placeholder. The actual update happens implicitly
        # because Streamlit re-runs the script on widget changes.
        pass

    def render_molecule_selection(self,
                                examples: Dict[str, Dict[str, str]] = None,
                                layout: str = "dropdown",
                                key_suffix: str = "") -> Optional[str]:
        """
        Render molecule selection component.
        
        Args:
            examples: Nested dict of {category: {name: smiles}}
            layout: Layout style ('dropdown', 'categorized', 'grid')
            key_suffix: Suffix for unique component keys
            
        Returns:
            Selected SMILES string or None
        """
        try:
            if examples is None:
                examples = self.default_examples
            
            if layout == "dropdown":
                return self._render_dropdown_selection(examples, key_suffix)
            elif layout == "categorized":
                return self._render_categorized_selection(examples, key_suffix)
            elif layout == "grid":
                return self._render_grid_selection(examples, key_suffix)
            else:
                self.add_error(f"Unknown layout: {layout}")
                return None
                
        except Exception as e:
            self.add_error(f"Error in molecule selection: {str(e)}", e)
            return None
    
    def render_file_upload(self,
                          label: str = "Upload CSV file with molecules",
                          show_preview: bool = True,
                          max_file_size: int = 10,
                          key_suffix: str = "") -> Optional[pd.DataFrame]:
        """
        Render file upload component for CSV molecule data.
        
        Args:
            label: Upload widget label
            show_preview: Whether to show file preview
            max_file_size: Maximum file size in MB
            key_suffix: Suffix for unique component keys
            
        Returns:
            DataFrame with validated molecule data or None
        """
        try:
            # File upload widget
            uploaded_file = st.file_uploader(
                label=label,
                type=["csv"],
                help="Upload a CSV file with 'Name' and 'SMILES' columns",
                key=self.get_key(f'file_upload_{key_suffix}')
            )
            
            if uploaded_file is None:
                return None
            
            # File size check
            if uploaded_file.size > max_file_size * 1024 * 1024:
                st.error(f"File too large. Maximum size: {max_file_size}MB")
                return None
            
            # Read CSV
            try:
                df = pd.read_csv(uploaded_file)
            except Exception as e:
                st.error(f"Could not read CSV file: {str(e)}")
                return None
            
            # Validate columns
            if not self._validate_csv_columns(df):
                return None
            
            # Validate SMILES
            validated_df = self._validate_smiles_in_dataframe(df)
            
            if validated_df is not None and len(validated_df) > 0:
                st.success(f"Successfully loaded {len(validated_df)} molecules from {uploaded_file.name}")
                
                # Preview
                if show_preview:
                    self._show_dataframe_preview(validated_df)
                
                return validated_df
            else:
                st.error("No valid molecules found in uploaded file")
                return None
                
        except Exception as e:
            self.add_error(f"Error in file upload: {str(e)}", e)
            return None
    
    def render_batch_input(self,
                          methods: List[str] = None,
                          key_suffix: str = "") -> Tuple[Optional[List[str]], Optional[pd.DataFrame]]:
        """
        Render batch molecule input with multiple methods.
        
        Args:
            methods: List of input methods ('text_area', 'file', 'examples')
            key_suffix: Suffix for unique component keys
            
        Returns:
            Tuple of (smiles_list, dataframe) - one will be None
        """
        try:
            if methods is None:
                methods = ["text_area", "file"]
            
            # Method selection
            method_names = {
                "text_area": "Enter Multiple SMILES",
                "file": "Upload CSV File", 
                "examples": "Use Example Sets"
            }
            
            method_options = [method_names[m] for m in methods if m in method_names]
            
            if len(method_options) > 1:
                selected_method_name = st.radio(
                    "Choose batch input method:",
                    options=method_options,
                    horizontal=True,
                    key=self.get_key(f'batch_method_{key_suffix}')
                )
                
                # Get method key from display name
                selected_method = None
                for key, name in method_names.items():
                    if name == selected_method_name:
                        selected_method = key
                        break
            else:
                selected_method = methods[0] if methods else "text_area"
            
            # Render appropriate input
            if selected_method == "text_area":
                smiles_list = self._render_text_area_input(key_suffix)
                return smiles_list, None
            elif selected_method == "file":
                df = self.render_file_upload(key_suffix=f"batch_{key_suffix}")
                return None, df
            elif selected_method == "examples":
                smiles_list = self._render_example_sets(key_suffix)
                return smiles_list, None
            else:
                return None, None
                
        except Exception as e:
            self.add_error(f"Error in batch input: {str(e)}", e)
            return None, None
    
    def render(self,
              input_type: str = "single",
              methods: List[str] = None,
              show_config: bool = False,
              key_suffix: str = "") -> Any:
        """
        Main render method for molecule input component.
        
        Args:
            input_type: Type of input ('single', 'batch', 'comparison')
            methods: Available input methods
            show_config: Whether to show configuration options
            key_suffix: Suffix for unique component keys
            
        Returns:
            Input result (varies by input_type)
        """
        try:
            self.clear_messages()
            
            if show_config:
                st.subheader("Molecule Input Configuration")
                # Configuration options could go here
            
            if input_type == "single":
                return self._render_single_input(methods, key_suffix)
            elif input_type == "batch":
                return self.render_batch_input(methods, key_suffix)
            elif input_type == "comparison":
                return self._render_comparison_input(methods, key_suffix)
            else:
                self.add_error(f"Unknown input type: {input_type}")
                return None
                
        except Exception as e:
            self.add_error(f"Error rendering molecule input: {str(e)}", e)
            self.display_messages()
            return None
    
    def _render_single_input(self, methods: List[str], key_suffix: str) -> Optional[str]:
        """Render single molecule input."""
        if methods is None:
            methods = ["manual", "examples"]
        
        method_names = {
            "manual": "Manual SMILES Entry",
            "examples": "Select from Examples",
            "file": "Upload File"
        }
        
        if len(methods) > 1:
            method_options = [method_names[m] for m in methods if m in method_names]
            selected_method_name = st.radio(
                "Choose input method:",
                options=method_options,
                horizontal=True,
                key=self.get_key(f'single_method_{key_suffix}')
            )
            
            selected_method = None
            for key, name in method_names.items():
                if name == selected_method_name:
                    selected_method = key
                    break
        else:
            selected_method = methods[0] if methods else "manual"
        
        if selected_method == "manual":
            return self.render_smiles_input(key_suffix=f"single_{key_suffix}")
        elif selected_method == "examples":
            return self.render_molecule_selection(layout="categorized", key_suffix=f"single_{key_suffix}")
        elif selected_method == "file":
            df = self.render_file_upload(key_suffix=f"single_{key_suffix}")
            if df is not None and len(df) > 0:
                # Let user select one molecule
                options = [f"{row['Name']} ({row['SMILES']})" for _, row in df.iterrows()]
                selected = st.selectbox(
                    "Select molecule:",
                    options=["-- Select --"] + options,
                    key=self.get_key(f'single_file_select_{key_suffix}')
                )
                if selected != "-- Select --":
                    return selected.split("(")[-1].rstrip(")")
        
        return None
    
    def _render_dropdown_selection(self, examples: Dict[str, Dict[str, str]], key_suffix: str) -> Optional[str]:
        """Render dropdown molecule selection."""
        # Flatten examples
        flat_examples = {}
        for category, molecules in examples.items():
            for name, smiles in molecules.items():
                flat_examples[f"{name} ({category})"] = smiles
        
        options = ["-- Select a molecule --"] + list(flat_examples.keys())
        selected = st.selectbox(
            "Select a molecule:",
            options=options,
            key=self.get_key(f'dropdown_{key_suffix}')
        )
        
        if selected != "-- Select a molecule --":
            smiles = flat_examples[selected]
            st.success(f"Selected: {selected}")
            st.code(f"SMILES: {smiles}")
            return smiles
        
        return None
    
    def _render_categorized_selection(self, examples: Dict[str, Dict[str, str]], key_suffix: str) -> Optional[str]:
        """Render categorized molecule selection."""
        # Category selection
        categories = ["-- Select category --"] + list(examples.keys())
        selected_category = st.selectbox(
            "Select molecule category:",
            options=categories,
            key=self.get_key(f'category_{key_suffix}')
        )
        
        if selected_category == "-- Select category --":
            return None
        
        # Molecule selection within category
        molecules = examples[selected_category]
        molecule_options = ["-- Select molecule --"] + list(molecules.keys())
        selected_molecule = st.selectbox(
            f"Select molecule from {selected_category}:",
            options=molecule_options,
            key=self.get_key(f'molecule_{key_suffix}')
        )
        
        if selected_molecule != "-- Select molecule --":
            smiles = molecules[selected_molecule]
            st.success(f"Selected: {selected_molecule} from {selected_category}")
            st.code(f"SMILES: {smiles}")
            return smiles
        
        return None
    
    def _render_grid_selection(self, examples: Dict[str, Dict[str, str]], key_suffix: str) -> Optional[str]:
        """Render grid molecule selection."""
        st.write("Click to select a molecule:")
        
        # Use simple molecules for grid
        molecules = examples.get("Simple Molecules", {})
        
        # Create grid
        cols = st.columns(3)
        molecule_items = list(molecules.items())
        
        for i, (name, smiles) in enumerate(molecule_items):
            with cols[i % 3]:
                if st.button(
                    name,
                    key=self.get_key(f'grid_{name}_{key_suffix}'),
                    help=f"SMILES: {smiles}",
                    use_container_width=True
                ):
                    st.success(f"Selected: {name}")
                    st.code(f"SMILES: {smiles}")
                    return smiles
        
        return None
    
    def _render_text_area_input(self, key_suffix: str) -> List[str]:
        """Render text area for multiple SMILES input."""
        smiles_text = st.text_area(
            "Enter SMILES strings (one per line):",
            placeholder="CCO\nCC(=O)OC1=CC=CC=C1C(=O)O\nCN1C=NC2=C1C(=O)N(C(=O)N2C)C",
            height=150,
            help="Enter one SMILES string per line. Invalid entries will be skipped.",
            key=self.get_key(f'text_area_{key_suffix}')
        )
        
        if not smiles_text or not smiles_text.strip():
            return []
        
        # Parse and validate lines
        lines = [line.strip() for line in smiles_text.split('\n') if line.strip()]
        valid_smiles = []
        invalid_count = 0
        
        for smiles in lines:
            is_valid, _ = self.validate_smiles(smiles)
            if is_valid:
                valid_smiles.append(smiles)
            else:
                invalid_count += 1
        
        # Display summary
        if valid_smiles:
            st.success(f"Found {len(valid_smiles)} valid SMILES structures")
            if invalid_count > 0:
                st.warning(f"Skipped {invalid_count} invalid entries")
        elif lines:
            st.error("No valid SMILES found in input")
        
        return valid_smiles
    
    def _render_example_sets(self, key_suffix: str) -> List[str]:
        """Render example molecule sets for batch input."""
        test_sets = {
            "Small Drug-like Molecules": [
                "CCO", "CC(=O)OC1=CC=CC=C1C(=O)O", "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
                "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O", "CC(=O)NC1=CC=C(C=C1)O"
            ],
            "Simple Molecules": [
                "O", "C", "CC", "CCC", "CCCC", "CO", "CCO", "CCCO"
            ],
            "Diverse Set": [
                "C1=CC=CC=C1", "C1=CC=C(C=C1)O", "CC(C)(C)C", "C1CCC(CC1)N",
                "CC(=O)C", "CCCCCCCC", "C1=CC=C2C(=C1)C=CC=C2"
            ]
        }
        
        selected_set = st.selectbox(
            "Select example molecule set:",
            options=list(test_sets.keys()),
            key=self.get_key(f'example_set_{key_suffix}')
        )
        
        if st.button(f"Load {selected_set}", key=self.get_key(f'load_set_{key_suffix}')):
            smiles_list = test_sets[selected_set]
            st.success(f"Loaded {len(smiles_list)} molecules from {selected_set}")
            return smiles_list
        
        return []
    
    def _render_comparison_input(self, methods: List[str], key_suffix: str) -> List[Tuple[str, str]]:
        """Render comparison molecule input."""
        st.write("Add molecules for comparison:")
        
        # Initialize session state
        comparison_key = self.get_key(f'comparison_{key_suffix}')
        if comparison_key not in st.session_state:
            st.session_state[comparison_key] = []
        
        molecules = st.session_state[comparison_key]
        
        # Add molecule interface
        col1, col2, col3 = st.columns([2, 3, 1])
        
        with col1:
            name = st.text_input(
                "Molecule name:",
                key=self.get_key(f'comp_name_{key_suffix}'),
                placeholder="e.g., Aspirin"
            )
        
        with col2:
            smiles = st.text_input(
                "SMILES:",
                key=self.get_key(f'comp_smiles_{key_suffix}'),
                placeholder="e.g., CC(=O)OC1=CC=CC=C1C(=O)O"
            )
        
        with col3:
            if st.button("Add", key=self.get_key(f'comp_add_{key_suffix}')):
                if name and smiles:
                    is_valid, error_msg = self.validate_smiles(smiles)
                    if is_valid:
                        molecules.append((name.strip(), smiles.strip()))
                        st.session_state[comparison_key] = molecules
                        st.rerun()
                    else:
                        st.error(f"Invalid SMILES: {error_msg}")
                else:
                    st.error("Please enter both name and SMILES")
        
        # Display current molecules
        if molecules:
            st.write(f"**Current molecules ({len(molecules)}):**")
            for i, (mol_name, mol_smiles) in enumerate(molecules):
                col1, col2, col3 = st.columns([2, 4, 1])
                with col1:
                    st.write(f"**{mol_name}**")
                with col2:
                    st.code(mol_smiles)
                with col3:
                    if st.button("Remove", key=self.get_key(f'comp_remove_{i}_{key_suffix}')):
                        molecules.pop(i)
                        st.session_state[comparison_key] = molecules
                        st.rerun()
        
        return molecules
    
    def _validate_csv_columns(self, df: pd.DataFrame) -> bool:
        """Validate that CSV has required columns."""
        required_columns = ["Name", "SMILES"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"Missing required columns: {', '.join(missing_columns)}. Found columns: {', '.join(df.columns)}")
            return False
        
        if len(df) == 0:
            st.error("CSV file is empty")
            return False
        
        return True
    
    def _validate_smiles_in_dataframe(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Validate SMILES in dataframe and return cleaned version."""
        valid_rows = []
        invalid_count = 0
        
        for idx, row in df.iterrows():
            name = str(row.get("Name", f"Molecule_{idx}")).strip()
            smiles = str(row.get("SMILES", "")).strip()
            
            if not smiles or smiles.lower() in ["nan", "none", ""]:
                invalid_count += 1
                continue
            
            is_valid, _ = self.validate_smiles(smiles)
            if is_valid:
                valid_rows.append(row)
            else:
                invalid_count += 1
        
        if invalid_count > 0:
            st.warning(f"Skipped {invalid_count} invalid entries")
        
        if valid_rows:
            return pd.DataFrame(valid_rows).reset_index(drop=True)
        else:
            return None
    
    def _show_dataframe_preview(self, df: pd.DataFrame):
        """Show preview of uploaded dataframe."""
        with st.expander("File Preview", expanded=True):
            preview_rows = min(10, len(df))
            st.write(f"**First {preview_rows} rows of {len(df)} total:**")
            st.dataframe(df.head(preview_rows), use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Molecules", len(df))
            with col2:
                st.metric("Columns", len(df.columns))
            with col3:
                unique_smiles = df["SMILES"].nunique()
                st.metric("Unique SMILES", unique_smiles)