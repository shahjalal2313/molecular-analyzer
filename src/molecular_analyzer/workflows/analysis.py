"""
Molecular Analysis Workflow

This module provides the MolecularAnalysisWorkflow class for orchestrating 
complete molecular analysis pipelines with configurable calculators and renderers.
"""

from typing import Dict, List, Optional, Any, Union
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime

try:
    from rdkit import Chem
except ImportError:
    Chem = None

from ..models.models import MoleculeData, PropertyData, AnalysisResult
from ..models.config import AnalysisConfig
from ..models.base import BaseCalculator
from ..models.exceptions import ValidationError, AnalysisError, ComputationError
from ..calculators.factory import CalculatorFactory


@dataclass
class WorkflowMetrics:
    """Performance metrics for workflow execution."""
    total_molecules: int = 0
    successful_analyses: int = 0
    failed_analyses: int = 0
    total_time: float = 0.0
    average_time_per_molecule: float = 0.0
    memory_usage_mb: Optional[float] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class MolecularAnalysisWorkflow:
    """
    Orchestrate complete molecular analysis pipeline.
    
    This workflow class provides a high-level interface for performing
    comprehensive molecular analysis using configurable calculators and
    renderers. It handles the coordination between different analysis
    components while maintaining type safety and error handling.
    
    Key Features:
    - Configurable analysis pipeline
    - Multiple calculator support
    - Comprehensive error handling
    - Performance monitoring
    - Result aggregation
    
    Example:
        >>> from molecular_analyzer.models.config import AnalysisConfig
        >>> from molecular_analyzer.workflows.analysis import MolecularAnalysisWorkflow
        >>> 
        >>> config = AnalysisConfig(include_basic_properties=True, include_advanced_properties=True)
        >>> workflow = MolecularAnalysisWorkflow(config)
        >>> result = workflow.analyze_smiles("CCO")
        >>> print(f"Molecular weight: {result.properties.molecular_weight}")
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """
        Initialize the molecular analysis workflow.
        
        Args:
            config: Analysis configuration. If None, uses default config.
        """
        self.config = config or AnalysisConfig()
        self.calculators: Dict[str, BaseCalculator] = {}
        self.metrics = WorkflowMetrics()
        self._logger = logging.getLogger(__name__)
        
        # Setup calculators based on configuration
        self._setup_calculators()
    
    def _setup_calculators(self) -> None:
        """Setup calculators based on configuration."""
        try:
            # Create factory instance
            factory = CalculatorFactory()
            
            # Always include basic properties if enabled
            if self.config.include_basic_properties:
                self.calculators['basic'] = factory.create_calculator('basic')
            
            # Include advanced properties if enabled
            if self.config.include_advanced_properties:
                self.calculators['advanced'] = factory.create_calculator('advanced')
            
            # Include 3D/conformational analysis if enabled
            if self.config.include_3d_analysis:
                self.calculators['conformational'] = factory.create_calculator('conformational')
            
            self._logger.info(f"Initialized workflow with {len(self.calculators)} calculators")
            
        except Exception as e:
            raise AnalysisError(f"Failed to setup calculators: {str(e)}")
    
    def analyze_smiles(self, smiles: str, name: Optional[str] = None) -> AnalysisResult:
        """
        Analyze a molecule from its SMILES string.
        
        Args:
            smiles: SMILES string of the molecule
            name: Optional name for the molecule
            
        Returns:
            AnalysisResult containing the complete analysis
            
        Raises:
            ValidationError: If SMILES string is invalid
            AnalysisError: If analysis fails
        """
        # Create molecule data object
        molecule_data = MoleculeData(smiles=smiles, name=name)
        
        # Validate the molecule
        if not molecule_data.validate():
            raise ValidationError(f"Invalid SMILES string: {smiles}")
        
        return self.analyze(molecule_data)
    
    def analyze(self, molecule: MoleculeData) -> AnalysisResult:
        """
        Perform complete analysis of a single molecule.
        
        Args:
            molecule: MoleculeData object to analyze
            
        Returns:
            AnalysisResult containing the complete analysis
            
        Raises:
            ValidationError: If molecule data is invalid
            AnalysisError: If analysis fails
        """
        start_time = time.time()
        errors = []
        warnings = []
        properties_data = {}
        
        try:
            # Validate input molecule
            if not molecule.validate():
                raise ValidationError("Invalid molecule data provided")
            
            # Run each calculator
            for calc_name, calculator in self.calculators.items():
                try:
                    self._logger.debug(f"Running {calc_name} calculator")
                    calc_result = calculator.calculate(molecule)
                    
                    if isinstance(calc_result, PropertyData):
                        # Merge PropertyData into our properties_data dict
                        properties_data.update(calc_result.to_dict())
                    elif isinstance(calc_result, dict):
                        # Direct dict result
                        properties_data.update(calc_result)
                    else:
                        warnings.append(f"{calc_name} calculator returned unexpected result type")
                        
                except ComputationError as e:
                    error_msg = f"{calc_name} calculation failed: {str(e)}"
                    errors.append(error_msg)
                    self._logger.warning(error_msg)
                except Exception as e:
                    error_msg = f"Unexpected error in {calc_name} calculator: {str(e)}"
                    errors.append(error_msg)
                    self._logger.error(error_msg)
            
            # Create PropertyData object from collected properties
            if properties_data:
                property_data = PropertyData(
                    properties=properties_data,
                    calculation_method=f"Workflow with {list(self.calculators.keys())}",
                )
            else:
                # If no properties calculated, create empty PropertyData
                property_data = PropertyData(
                    properties={},
                    calculation_method="Failed analysis",
                )
                errors.append("No properties could be calculated")
            
            calculation_time = time.time() - start_time
            
            # Update metrics
            self.metrics.total_molecules += 1
            if not errors:
                self.metrics.successful_analyses += 1
            else:
                self.metrics.failed_analyses += 1
            self.metrics.total_time += calculation_time
            self.metrics.average_time_per_molecule = self.metrics.total_time / self.metrics.total_molecules
            self.metrics.errors.extend(errors)
            self.metrics.warnings.extend(warnings)
            
            # Create analysis result
            result = AnalysisResult(
                molecule=molecule,
                properties=property_data,
                success=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                execution_time=calculation_time,
                analysis_config={"analysis_type": "comprehensive", "calculators": list(self.calculators.keys())}
            )
            
            self._logger.info(f"Analysis completed in {calculation_time:.3f}s with {len(errors)} errors")
            return result
            
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            calculation_time = time.time() - start_time
            error_msg = f"Analysis failed: {str(e)}"
            
            # Update metrics for failed analysis
            self.metrics.total_molecules += 1
            self.metrics.failed_analyses += 1
            self.metrics.total_time += calculation_time
            self.metrics.average_time_per_molecule = self.metrics.total_time / self.metrics.total_molecules
            self.metrics.errors.append(error_msg)
            
            raise AnalysisError(error_msg)
    
    def batch_analyze(self, molecules: List[MoleculeData]) -> List[AnalysisResult]:
        """
        Analyze multiple molecules efficiently.
        
        Args:
            molecules: List of MoleculeData objects to analyze
            
        Returns:
            List of AnalysisResult objects
        """
        results = []
        
        for i, molecule in enumerate(molecules):
            try:
                result = self.analyze(molecule)
                results.append(result)
                
                # Log progress
                if (i + 1) % 10 == 0:
                    self._logger.info(f"Processed {i + 1}/{len(molecules)} molecules")
                    
            except Exception as e:
                # Create failed result
                failed_result = AnalysisResult(
                    molecule=molecule,
                    properties=PropertyData(
                        properties={},
                        calculation_method="Failed batch analysis",
                    ),
                    success=False,
                    errors=[str(e)],
                    execution_time=0.0,
                    analysis_config={"analysis_type": "batch"}
                )
                results.append(failed_result)
                self._logger.warning(f"Failed to analyze molecule {i}: {str(e)}")
        
        self._logger.info(f"Batch analysis completed: {len(results)} molecules processed")
        return results
    
    def add_calculator(self, name: str, calculator: BaseCalculator) -> None:
        """
        Add a calculator to the workflow.
        
        Args:
            name: Name identifier for the calculator
            calculator: Calculator instance
        """
        if not isinstance(calculator, BaseCalculator):
            raise ValueError("Calculator must inherit from BaseCalculator")
        
        self.calculators[name] = calculator
        self._logger.info(f"Added calculator: {name}")
    
    def remove_calculator(self, name: str) -> None:
        """
        Remove a calculator from the workflow.
        
        Args:
            name: Name of the calculator to remove
        """
        if name in self.calculators:
            del self.calculators[name]
            self._logger.info(f"Removed calculator: {name}")
        else:
            self._logger.warning(f"Calculator not found: {name}")
    
    def get_available_calculators(self) -> List[str]:
        """
        Get list of available calculator names.
        
        Returns:
            List of calculator names
        """
        return list(self.calculators.keys())
    
    def get_metrics(self) -> WorkflowMetrics:
        """
        Get workflow performance metrics.
        
        Returns:
            WorkflowMetrics object with performance data
        """
        return self.metrics
    
    def reset_metrics(self) -> None:
        """Reset workflow metrics."""
        self.metrics = WorkflowMetrics()
        self._logger.info("Workflow metrics reset")
    
    def configure_logging(self, level: str = "INFO") -> None:
        """
        Configure logging level for the workflow.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        logging.basicConfig(level=getattr(logging, level.upper()))
        self._logger.setLevel(getattr(logging, level.upper()))
        self._logger.info(f"Logging level set to {level}")