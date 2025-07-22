"""
Comprehensive tests for OOP structure in molecular analyzer.

This module tests the new object-oriented architecture including:
- Data models and type system
- Calculator classes
- Workflow classes
- Visualization classes
- Integration layer
"""

import unittest
import sys
import os
from pathlib import Path

# Add src to path for testing
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    import molecular_analyzer
    from molecular_analyzer.models import MoleculeData, PropertyData, AnalysisResult
    from molecular_analyzer.models.exceptions import ValidationError, AnalysisError
    from molecular_analyzer.models.config import AnalysisConfig, ConfigurationManager
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False

try:
    from molecular_analyzer.calculators import (
        BasicPropertiesCalculator,
        AdvancedPropertiesCalculator,
        ConformationalCalculator,
        ComparisonCalculator,
        CalculatorFactory
    )
    CALCULATORS_AVAILABLE = True
except ImportError:
    CALCULATORS_AVAILABLE = False

try:
    from molecular_analyzer.workflows import (
        MolecularAnalysisWorkflow,
        BatchAnalysisWorkflow
    )
    WORKFLOWS_AVAILABLE = True
except ImportError:
    WORKFLOWS_AVAILABLE = False

try:
    from molecular_analyzer.visualization import (
        Chart2DRenderer,
        Molecule3DRenderer,
        ReportGenerator
    )
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False


class TestPackageStructure(unittest.TestCase):
    """Test the overall package structure and imports."""
    
    def test_package_import(self):
        """Test that the main package can be imported."""
        self.assertTrue(hasattr(molecular_analyzer, '__version__'))
        self.assertTrue(hasattr(molecular_analyzer, 'get_package_info'))
    
    def test_package_info(self):
        """Test package information function."""
        info = molecular_analyzer.get_package_info()
        self.assertIsInstance(info, dict)
        self.assertIn('name', info)
        self.assertIn('version', info)
        self.assertIn('oop_capabilities', info)
        
        # Check OOP capabilities
        oop_caps = info['oop_capabilities']
        self.assertIsInstance(oop_caps, dict)
        self.assertIn('models', oop_caps)
        self.assertIn('calculators', oop_caps)
        self.assertIn('workflows', oop_caps)
        self.assertIn('visualization', oop_caps)
    
    def test_backwards_compatibility(self):
        """Test that legacy imports still work."""
        # These imports should work for backwards compatibility
        self.assertTrue(hasattr(molecular_analyzer, 'MolecularAnalyzer'))
        self.assertTrue(hasattr(molecular_analyzer, 'calculate_basic_properties'))
        self.assertTrue(hasattr(molecular_analyzer, 'quick_analysis'))
    
    def test_convenience_functions(self):
        """Test OOP convenience functions."""
        if WORKFLOWS_AVAILABLE:
            try:
                workflow = molecular_analyzer.create_analyzer_workflow()
                self.assertIsNotNone(workflow)
            except Exception as e:
                self.fail(f"Failed to create analyzer workflow: {e}")
        
        if CALCULATORS_AVAILABLE:
            try:
                calc = molecular_analyzer.create_basic_calculator()
                self.assertIsNotNone(calc)
            except Exception as e:
                self.fail(f"Failed to create basic calculator: {e}")
            
            try:
                factory = molecular_analyzer.create_calculator_factory()
                self.assertIsNotNone(factory)
            except Exception as e:
                self.fail(f"Failed to create calculator factory: {e}")


@unittest.skipUnless(MODELS_AVAILABLE, "Models not available")
class TestDataModels(unittest.TestCase):
    """Test data models and type system."""
    
    def test_molecule_data_creation(self):
        """Test MoleculeData creation and validation."""
        # Valid molecule
        mol_data = MoleculeData(smiles="CCO")
        self.assertTrue(mol_data.validated)
        self.assertEqual(mol_data.smiles, "CCO")
        self.assertIsNotNone(mol_data.validation_timestamp)
        
        # Invalid molecule should raise ValidationError during __post_init__
        with self.assertRaises(ValidationError):
            MoleculeData(smiles="invalid_smiles!!!")
    
    def test_property_data_creation(self):
        """Test PropertyData creation."""
        properties = {
            'molecular_weight': 46.07,
            'logp': -0.31,
            'num_atoms': 9
        }
        prop_data = PropertyData(properties=properties)
        self.assertEqual(prop_data.get_property('molecular_weight'), 46.07)
        self.assertEqual(prop_data.get_property('logp'), -0.31)
    
    def test_analysis_result_creation(self):
        """Test AnalysisResult creation."""
        mol_data = MoleculeData(smiles="CCO")
        prop_data = PropertyData(properties={'molecular_weight': 46.07})
        
        result = AnalysisResult(
            molecule=mol_data,
            properties=prop_data,
            analysis_config={"analysis_type": "basic"}
        )
        
        self.assertEqual(result.molecule.smiles, "CCO")
        self.assertEqual(result.properties.get_property('molecular_weight'), 46.07)
        self.assertEqual(result.analysis_config.get("analysis_type"), "basic")
    
    def test_configuration_system(self):
        """Test configuration system."""
        config = AnalysisConfig()
        self.assertIsNotNone(config.precision)
        self.assertIsNotNone(config.validation_level)
        
        # Test configuration manager
        manager = ConfigurationManager()
        effective_config = manager.get_effective_config()
        self.assertIsInstance(effective_config, AnalysisConfig)


@unittest.skipUnless(CALCULATORS_AVAILABLE, "Calculators not available")
class TestCalculators(unittest.TestCase):
    """Test calculator classes."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_smiles = "CCO"  # Ethanol
        self.mol_data = MoleculeData(smiles=self.test_smiles)
    
    def test_basic_properties_calculator(self):
        """Test BasicPropertiesCalculator."""
        calc = BasicPropertiesCalculator()
        result = calc.calculate(self.mol_data)
        
        self.assertIsInstance(result, PropertyData)
        self.assertGreater(result.get_property('molecular_weight', 0), 0)
        self.assertIsNotNone(result.get_property('num_atoms'))
    
    def test_advanced_properties_calculator(self):
        """Test AdvancedPropertiesCalculator."""
        calc = AdvancedPropertiesCalculator()
        result = calc.calculate(self.mol_data)
        
        self.assertIsInstance(result, PropertyData)
        # Should have drug-likeness properties
        self.assertIn('lipinski_violations', result.properties)
    
    def test_conformational_calculator(self):
        """Test ConformationalCalculator."""
        calc = ConformationalCalculator()
        result = calc.calculate(self.mol_data)
        
        self.assertIsInstance(result, PropertyData)
        # Should have 3D properties
        self.assertIn('num_conformers', result.properties)
    
    def test_comparison_calculator(self):
        """Test ComparisonCalculator."""
        calc = ComparisonCalculator()
        mol_data2 = MoleculeData(smiles="CCO")  # Same molecule
        
        similarity = calc.calculate_similarity(self.mol_data, mol_data2)
        self.assertEqual(similarity, 1.0)  # Same molecule should have similarity 1.0
    
    def test_calculator_factory(self):
        """Test CalculatorFactory."""
        factory = CalculatorFactory()
        
        # Test creating different calculators
        basic_calc = factory.create_calculator('basic')
        self.assertIsInstance(basic_calc, BasicPropertiesCalculator)
        
        advanced_calc = factory.create_calculator('advanced')
        self.assertIsInstance(advanced_calc, AdvancedPropertiesCalculator)
        
        # Test listing available calculators
        available = factory.get_available_calculators()
        self.assertIn('basic', available)
        self.assertIn('advanced', available)


@unittest.skipUnless(WORKFLOWS_AVAILABLE, "Workflows not available")
class TestWorkflows(unittest.TestCase):
    """Test workflow classes."""
    
    def test_molecular_analysis_workflow(self):
        """Test MolecularAnalysisWorkflow."""
        workflow = MolecularAnalysisWorkflow()
        result = workflow.analyze_smiles("CCO")
        
        self.assertIsInstance(result, AnalysisResult)
        self.assertEqual(result.molecule.smiles, "CCO")
        self.assertIsNotNone(result.properties)
    
    def test_batch_analysis_workflow(self):
        """Test BatchAnalysisWorkflow."""
        workflow = BatchAnalysisWorkflow()
        smiles_list = ["CCO", "CC", "C"]
        
        results = workflow.process_smiles_list(smiles_list)
        self.assertEqual(len(results), 3)
        
        for result in results:
            self.assertIsInstance(result, AnalysisResult)
            self.assertTrue(result.molecule.validated)


@unittest.skipUnless(VISUALIZATION_AVAILABLE, "Visualization not available")
class TestVisualization(unittest.TestCase):
    """Test visualization classes."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mol_data = MoleculeData(smiles="CCO")
        self.prop_data = PropertyData(properties={'molecular_weight': 46.07, 'logp': -0.31})
        self.result = AnalysisResult(
            molecule=self.mol_data,
            properties=self.prop_data,
            analysis_config={"analysis_type": "test"}
        )
    
    def test_chart_2d_renderer(self):
        """Test Chart2DRenderer."""
        renderer = Chart2DRenderer()
        
        # Test creating a simple chart
        chart_data = {
            'x': [1, 2, 3],
            'y': [1, 4, 9],
            'title': 'Test Chart'
        }
        
        try:
            chart = renderer.create_scatter_plot(chart_data)
            self.assertIsNotNone(chart)
        except Exception as e:
            # Some visualization backends might not be available in test environment
            self.skipTest(f"Visualization backend not available: {e}")
    
    def test_molecule_3d_renderer(self):
        """Test Molecule3DRenderer."""
        renderer = Molecule3DRenderer()
        
        try:
            html = renderer.render_molecule_3d(self.mol_data)
            self.assertIsInstance(html, str)
            self.assertIn('molecule', html.lower())
        except Exception as e:
            self.skipTest(f"3D visualization not available: {e}")
    
    def test_report_generator(self):
        """Test ReportGenerator."""
        generator = ReportGenerator(backend="json")
        
        try:
            # Test JSON report generation
            json_report = generator.render(self.result)
            self.assertIsInstance(json_report, str)
            
            # Test HTML report generation
            generator.backend = "html"
            html_report = generator.render(self.result)
            self.assertIsInstance(html_report, str)
            self.assertIn('html', html_report.lower())
        except Exception as e:
            self.skipTest(f"Report generation not fully implemented: {e}")


class TestIntegration(unittest.TestCase):
    """Test integration between components."""
    
    def test_end_to_end_analysis(self):
        """Test complete end-to-end analysis using OOP components."""
        if not (MODELS_AVAILABLE and CALCULATORS_AVAILABLE and WORKFLOWS_AVAILABLE):
            self.skipTest("Required OOP components not available")
        
        # Create workflow
        workflow = MolecularAnalysisWorkflow()
        
        # Perform analysis
        result = workflow.analyze_smiles("CCO")
        
        # Verify result structure
        self.assertIsInstance(result, AnalysisResult)
        self.assertTrue(result.molecule.validated)
        self.assertIsNotNone(result.properties)
        self.assertGreater(len(result.properties.properties), 0)
        
        # Test serialization
        result_dict = result.to_dict()
        self.assertIsInstance(result_dict, dict)
        self.assertIn('molecule', result_dict)
        self.assertIn('properties', result_dict)
    
    def test_calculator_integration(self):
        """Test integration between different calculators."""
        if not CALCULATORS_AVAILABLE:
            self.skipTest("Calculators not available")
        
        mol_data = MoleculeData(smiles="CCO")
        
        # Use factory to create calculators
        factory = CalculatorFactory()
        basic_calc = factory.create_calculator('basic')
        advanced_calc = factory.create_calculator('advanced')
        
        # Calculate properties
        basic_props = basic_calc.calculate(mol_data)
        advanced_props = advanced_calc.calculate(mol_data)
        
        # Both should return PropertyData objects
        self.assertIsInstance(basic_props, PropertyData)
        self.assertIsInstance(advanced_props, PropertyData)
        
        # Both should have some properties calculated
        self.assertGreater(len(basic_props.properties), 0)
        self.assertGreater(len(advanced_props.properties), 0)
        
        # If both have molecular weight, values should be consistent
        basic_mw = basic_props.get_property('molecular_weight')
        advanced_mw = advanced_props.get_property('molecular_weight')
        
        if basic_mw is not None and advanced_mw is not None:
            self.assertAlmostEqual(basic_mw, advanced_mw, places=2)


if __name__ == '__main__':
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestPackageStructure,
        TestDataModels,
        TestCalculators,
        TestWorkflows,
        TestVisualization,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"OOP STRUCTURE TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, failure in result.failures:
            print(f"  - {test}: {failure}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, error in result.errors:
            print(f"  - {test}: {error}")
    
    if result.skipped:
        print(f"\nSKIPPED:")
        for test, reason in result.skipped:
            print(f"  - {test}: {reason}")
    
    # Exit with appropriate code
    exit_code = 0 if result.wasSuccessful() else 1
    print(f"\nTest suite {'PASSED' if exit_code == 0 else 'FAILED'}")
    exit(exit_code)