"""
Batch Analysis Workflow

This module provides the BatchAnalysisWorkflow class for efficient 
batch processing of multiple molecules with support for file I/O,
parallel processing, and result export.
"""

from typing import Dict, List, Optional, Tuple, Union, Any
import os
import time
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import json
import csv
import pandas as pd

try:
    from rdkit import Chem
    from rdkit.Chem import PandasTools
except ImportError:
    Chem = None
    PandasTools = None

from .analysis import MolecularAnalysisWorkflow, WorkflowMetrics
from ..models.models import MoleculeData, AnalysisResult, PropertyData
from ..models.config import AnalysisConfig
from ..models.exceptions import ValidationError, AnalysisError, FileIOError


class BatchAnalysisWorkflow(MolecularAnalysisWorkflow):
    """
    Specialized workflow for batch processing of molecular data.
    
    This workflow extends MolecularAnalysisWorkflow with capabilities for:
    - Batch file processing (SDF, CSV, SMILES)
    - Parallel processing for improved performance
    - Result export in multiple formats
    - Progress tracking and reporting
    - Memory-efficient streaming for large datasets
    
    Key Features:
    - File format auto-detection
    - Configurable batch sizes
    - Parallel processing support
    - Multiple export formats (CSV, JSON, Excel)
    - Error handling and recovery
    - Progress monitoring
    
    Example:
        >>> from molecular_analyzer.models.config import AnalysisConfig
        >>> from molecular_analyzer.workflows.batch import BatchAnalysisWorkflow
        >>> 
        >>> config = AnalysisConfig(include_basic_properties=True)
        >>> batch_workflow = BatchAnalysisWorkflow(config, batch_size=50)
        >>> results, errors = batch_workflow.process_file("molecules.sdf")
        >>> batch_workflow.export_results(results, "output/")
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None, batch_size: int = 100, 
                 parallel_processing: bool = True, max_workers: Optional[int] = None):
        """
        Initialize the batch analysis workflow.
        
        Args:
            config: Analysis configuration. If None, uses default config.
            batch_size: Number of molecules to process in each batch
            parallel_processing: Whether to use parallel processing
            max_workers: Maximum number of worker processes. If None, uses CPU count.
        """
        super().__init__(config)
        self.batch_size = batch_size
        self.parallel_processing = parallel_processing
        self.max_workers = max_workers or min(multiprocessing.cpu_count(), 4)
        self._logger = logging.getLogger(__name__)
        
        self._logger.info(f"Initialized batch workflow with batch_size={batch_size}, "
                         f"parallel_processing={parallel_processing}, max_workers={self.max_workers}")
    
    def process_file(self, filepath: str, output_dir: Optional[str] = None) -> Tuple[List[AnalysisResult], List[str]]:
        """
        Process molecules from a file in batches.
        
        Args:
            filepath: Path to the input file (SDF, CSV, or SMILES)
            output_dir: Optional directory to save results
            
        Returns:
            Tuple of (analysis_results, error_messages)
            
        Raises:
            FileIOError: If file cannot be read or is in unsupported format
            AnalysisError: If analysis fails critically
        """
        if not os.path.exists(filepath):
            raise FileIOError(f"File not found: {filepath}")
        
        file_path = Path(filepath)
        file_extension = file_path.suffix.lower()
        
        self._logger.info(f"Processing file: {filepath} (format: {file_extension})")
        
        try:
            # Parse molecules based on file format
            if file_extension == '.sdf':
                molecules, parse_errors = self._parse_sdf_file(filepath)
            elif file_extension in ['.csv', '.tsv']:
                molecules, parse_errors = self._parse_csv_file(filepath)
            elif file_extension in ['.smi', '.smiles', '.txt']:
                molecules, parse_errors = self._parse_smiles_file(filepath)
            else:
                raise FileIOError(f"Unsupported file format: {file_extension}")
            
            if not molecules:
                raise AnalysisError("No valid molecules found in file")
            
            self._logger.info(f"Parsed {len(molecules)} molecules with {len(parse_errors)} parsing errors")
            
            # Process molecules in batches
            results = self._process_molecules_in_batches(molecules)
            
            # Export results if output directory specified
            if output_dir:
                self.export_results(results, output_dir)
            
            return results, parse_errors
            
        except Exception as e:
            if isinstance(e, (FileIOError, AnalysisError)):
                raise
            else:
                raise FileIOError(f"Failed to process file {filepath}: {str(e)}")
    
    def process_smiles_list(self, smiles_list: List[str], names: Optional[List[str]] = None) -> List[AnalysisResult]:
        """
        Process a list of SMILES strings.
        
        Args:
            smiles_list: List of SMILES strings
            names: Optional list of molecule names
            
        Returns:
            List of AnalysisResult objects
        """
        if names and len(names) != len(smiles_list):
            raise ValueError("Names list must have same length as SMILES list")
        
        # Create MoleculeData objects
        molecules = []
        for i, smiles in enumerate(smiles_list):
            name = names[i] if names else f"Molecule_{i+1}"
            try:
                molecule = MoleculeData(smiles=smiles, name=name)
                molecules.append(molecule)
            except Exception as e:
                self._logger.warning(f"Failed to create molecule from SMILES {smiles}: {str(e)}")
        
        self._logger.info(f"Processing {len(molecules)} molecules from SMILES list")
        return self._process_molecules_in_batches(molecules)
    
    def _process_molecules_in_batches(self, molecules: List[MoleculeData]) -> List[AnalysisResult]:
        """
        Process molecules in batches with optional parallel processing.
        
        Args:
            molecules: List of MoleculeData objects
            
        Returns:
            List of AnalysisResult objects
        """
        total_molecules = len(molecules)
        all_results = []
        
        # Split into batches
        batches = [molecules[i:i + self.batch_size] for i in range(0, total_molecules, self.batch_size)]
        
        self._logger.info(f"Processing {total_molecules} molecules in {len(batches)} batches")
        
        if self.parallel_processing and len(batches) > 1:
            # Parallel processing
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit batch jobs
                future_to_batch = {
                    executor.submit(self._process_batch, batch, i): i 
                    for i, batch in enumerate(batches)
                }
                
                # Collect results
                for future in as_completed(future_to_batch):
                    batch_idx = future_to_batch[future]
                    try:
                        batch_results = future.result()
                        all_results.extend(batch_results)
                        self._logger.info(f"Completed batch {batch_idx + 1}/{len(batches)}")
                    except Exception as e:
                        self._logger.error(f"Batch {batch_idx + 1} failed: {str(e)}")
        else:
            # Sequential processing
            for i, batch in enumerate(batches):
                batch_results = self._process_batch(batch, i)
                all_results.extend(batch_results)
                self._logger.info(f"Completed batch {i + 1}/{len(batches)}")
        
        self._logger.info(f"Batch processing completed: {len(all_results)} results generated")
        return all_results
    
    def _process_batch(self, molecules: List[MoleculeData], batch_idx: int) -> List[AnalysisResult]:
        """
        Process a single batch of molecules.
        
        Args:
            molecules: List of MoleculeData objects in the batch
            batch_idx: Index of the current batch
            
        Returns:
            List of AnalysisResult objects
        """
        start_time = time.time()
        results = []
        
        for molecule in molecules:
            try:
                result = self.analyze(molecule)
                results.append(result)
            except Exception as e:
                # Create failed result
                failed_result = AnalysisResult(
                    molecule=molecule,
                    properties=PropertyData(properties={}, calculation_method="Failed analysis"),
                    success=False,
                    errors=[str(e)],
                    execution_time=0.0,
                    analysis_config={"analysis_type": "batch"}
                )
                results.append(failed_result)
        
        batch_time = time.time() - start_time
        self._logger.debug(f"Batch {batch_idx + 1} processed in {batch_time:.2f}s")
        
        return results
    
    def export_results(self, results: List[AnalysisResult], output_dir: str) -> None:
        """
        Export batch results to various formats.
        
        Args:
            results: List of AnalysisResult objects
            output_dir: Directory to save results
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Prepare data for export
        export_data = []
        error_data = []
        
        for result in results:
            # Basic result data
            result_dict = {
                'name': result.molecule.name or 'Unknown',
                'smiles': result.molecule.smiles,
                'success': result.success,
                'calculation_time': result.calculation_time,
                'analysis_type': result.analysis_type,
            }
            
            # Add properties if successful
            if result.success and result.properties:
                props_dict = result.properties.to_dict()
                result_dict.update(props_dict)
            
            export_data.append(result_dict)
            
            # Track errors
            if result.errors:
                error_data.append({
                    'name': result.molecule.name or 'Unknown',
                    'smiles': result.molecule.smiles,
                    'errors': '; '.join(result.errors),
                    'warnings': '; '.join(result.warnings) if result.warnings else ''
                })
        
        # Export to CSV
        csv_path = os.path.join(output_dir, 'analysis_results.csv')
        df = pd.DataFrame(export_data)
        df.to_csv(csv_path, index=False)
        self._logger.info(f"Results exported to CSV: {csv_path}")
        
        # Export to JSON
        json_path = os.path.join(output_dir, 'analysis_results.json')
        with open(json_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        self._logger.info(f"Results exported to JSON: {json_path}")
        
        # Export errors if any
        if error_data:
            error_csv_path = os.path.join(output_dir, 'analysis_errors.csv')
            error_df = pd.DataFrame(error_data)
            error_df.to_csv(error_csv_path, index=False)
            self._logger.info(f"Errors exported to CSV: {error_csv_path}")
        
        # Export summary statistics
        self._export_summary_statistics(results, output_dir)
    
    def _export_summary_statistics(self, results: List[AnalysisResult], output_dir: str) -> None:
        """Export summary statistics of the batch analysis."""
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        summary = {
            'total_molecules': len(results),
            'successful_analyses': len(successful_results),
            'failed_analyses': len(failed_results),
            'success_rate': len(successful_results) / len(results) if results else 0,
            'average_calculation_time': sum(r.calculation_time for r in results) / len(results) if results else 0,
            'total_processing_time': sum(r.calculation_time for r in results),
            'workflow_metrics': self.get_metrics().__dict__,
        }
        
        summary_path = os.path.join(output_dir, 'analysis_summary.json')
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        self._logger.info(f"Summary statistics exported: {summary_path}")
    
    def _parse_sdf_file(self, filepath: str) -> Tuple[List[MoleculeData], List[str]]:
        """Parse SDF file and extract molecules."""
        molecules = []
        errors = []
        
        if Chem is None:
            raise FileIOError("RDKit not available for SDF file parsing")
        
        try:
            suppl = Chem.SDMolSupplier(filepath)
            for i, mol in enumerate(suppl):
                if mol is None:
                    errors.append(f"Failed to parse molecule at index {i}")
                    continue
                
                try:
                    smiles = Chem.MolToSmiles(mol)
                    name = mol.GetProp('_Name') if mol.HasProp('_Name') else f"Molecule_{i+1}"
                    
                    molecule_data = MoleculeData(
                        smiles=smiles,
                        name=name,
                        id=str(i+1),
                        mol=mol
                    )
                    molecules.append(molecule_data)
                    
                except Exception as e:
                    errors.append(f"Failed to process molecule {i}: {str(e)}")
                    
        except Exception as e:
            raise FileIOError(f"Failed to read SDF file: {str(e)}")
        
        return molecules, errors
    
    def _parse_csv_file(self, filepath: str) -> Tuple[List[MoleculeData], List[str]]:
        """Parse CSV file and extract molecules."""
        molecules = []
        errors = []
        
        try:
            # Detect delimiter
            delimiter = '\t' if filepath.endswith('.tsv') else ','
            df = pd.read_csv(filepath, delimiter=delimiter)
            
            # Look for SMILES column
            smiles_col = None
            name_col = None
            
            for col in df.columns:
                col_lower = col.lower()
                if 'smiles' in col_lower:
                    smiles_col = col
                elif 'name' in col_lower or 'compound' in col_lower or 'molecule' in col_lower:
                    name_col = col
            
            if smiles_col is None:
                raise FileIOError("No SMILES column found in CSV file")
            
            for i, row in df.iterrows():
                try:
                    smiles = str(row[smiles_col]).strip()
                    name = str(row[name_col]).strip() if name_col else f"Molecule_{i+1}"
                    
                    if smiles and smiles.lower() not in ['nan', 'none', '']:
                        molecule_data = MoleculeData(
                            smiles=smiles,
                            name=name,
                            id=str(i+1)
                        )
                        molecules.append(molecule_data)
                    else:
                        errors.append(f"Empty or invalid SMILES at row {i+1}")
                        
                except Exception as e:
                    errors.append(f"Failed to process row {i+1}: {str(e)}")
                    
        except Exception as e:
            raise FileIOError(f"Failed to read CSV file: {str(e)}")
        
        return molecules, errors
    
    def _parse_smiles_file(self, filepath: str) -> Tuple[List[MoleculeData], List[str]]:
        """Parse SMILES file (one SMILES per line)."""
        molecules = []
        errors = []
        
        try:
            with open(filepath, 'r') as f:
                for i, line in enumerate(f):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    try:
                        # Handle tab or space separated name
                        parts = line.split()
                        smiles = parts[0]
                        name = parts[1] if len(parts) > 1 else f"Molecule_{i+1}"
                        
                        molecule_data = MoleculeData(
                            smiles=smiles,
                            name=name,
                            id=str(i+1)
                        )
                        molecules.append(molecule_data)
                        
                    except Exception as e:
                        errors.append(f"Failed to process line {i+1}: {str(e)}")
                        
        except Exception as e:
            raise FileIOError(f"Failed to read SMILES file: {str(e)}")
        
        return molecules, errors
    
