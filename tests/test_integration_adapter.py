"""
Tests for the integration adapter system.

This module tests the improved integration adapter that connects
the molecular analyzer core with UI components and external systems.
"""

import unittest
import sys
import os
from pathlib import Path

# Add integration path for testing
integration_path = str(Path(__file__).parent.parent / "integration")
if integration_path not in sys.path:
    sys.path.insert(0, integration_path)

# Add src path for testing
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    from adapter_v2 import (
        MolecularAnalyzerAdapter,
        AdapterFactory,
        AdapterCapabilities,
        create_adapter,
        quick_analyze
    )
    ADAPTER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Adapter not available: {e}")
    ADAPTER_AVAILABLE = False


@unittest.skipUnless(ADAPTER_AVAILABLE, "Integration adapter not available")
class TestAdapterCapabilities(unittest.TestCase):
    """Test adapter capabilities system."""
    
    def test_capabilities_creation(self):
        """Test AdapterCapabilities creation."""
        caps = AdapterCapabilities()
        
        # Check default values
        self.assertTrue(caps.has_core_analysis)
        self.assertTrue(caps.has_advanced_properties)
        self.assertTrue(caps.has_3d_visualization)
        self.assertTrue(caps.has_batch_processing)
        self.assertTrue(caps.has_comparison)
        self.assertIn('SMILES', caps.supported_formats)
    
    def test_custom_capabilities(self):
        """Test custom capabilities creation."""
        caps = AdapterCapabilities(
            has_core_analysis=True,
            has_advanced_properties=False,
            supported_formats=['SMILES']
        )
        
        self.assertTrue(caps.has_core_analysis)
        self.assertFalse(caps.has_advanced_properties)
        self.assertEqual(caps.supported_formats, ['SMILES'])


@unittest.skipUnless(ADAPTER_AVAILABLE, "Integration adapter not available")
class TestMolecularAnalyzerAdapter(unittest.TestCase):
    """Test main adapter functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.adapter = MolecularAnalyzerAdapter()
        self.test_smiles = "CCO"  # Ethanol
        self.test_smiles_list = ["CCO", "CC", "C"]
    
    def test_adapter_initialization(self):
        """Test adapter initialization."""
        self.assertIsNotNone(self.adapter.capabilities)
        self.assertIsInstance(self.adapter.capabilities, AdapterCapabilities)
    
    def test_health_check(self):
        """Test adapter health check."""
        health = self.adapter.health_check()
        
        self.assertIsInstance(health, dict)
        self.assertIn('core_available', health)
        self.assertIn('ready', health)
        self.assertIn('version', health)
        
        # If core is available, it should be functional
        if health['core_available']:
            self.assertIn('core_functional', health)
    
    def test_get_capabilities(self):
        """Test capabilities reporting."""
        caps = self.adapter.get_capabilities()
        
        self.assertIsInstance(caps, dict)
        self.assertIn('core_analysis', caps)
        self.assertIn('version', caps)
        self.assertIn('supported_formats', caps)
        
        # Check for OOP capabilities
        self.assertIn('oop_workflows', caps)
        self.assertIn('oop_calculators', caps)
        self.assertIn('oop_visualization', caps)

    def test_get_capabilities_new_features(self):
        """Test capabilities reporting for new features."""
        caps = self.adapter.get_capabilities()

        self.assertIsInstance(caps, dict)
        self.assertIn('conformational_analysis', caps)
        self.assertIn('advanced_properties', caps)

        self.assertTrue(caps['conformational_analysis'])
        self.assertTrue(caps['advanced_properties'])

    def test_single_molecule_analysis(self):
        """Test single molecule analysis."""
        if not self.adapter.capabilities.has_core_analysis:
            self.skipTest("Core analysis not available")
        
        result = self.adapter.analyze_single_molecule(self.test_smiles)
        
        self.assertIsInstance(result, dict)
        self.assertIn('smiles', result)
        self.assertIn('valid', result)
        self.assertIn('properties', result)
        
        self.assertEqual(result['smiles'], self.test_smiles)
        if result['valid']:
            self.assertIsInstance(result['properties'], dict)
    
    def test_batch_analysis(self):
        """Test batch molecule analysis."""
        if not self.adapter.capabilities.has_core_analysis:
            self.skipTest("Core analysis not available")
        
        results = self.adapter.analyze_batch(self.test_smiles_list)
        
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), len(self.test_smiles_list))
        
        for i, result in enumerate(results):
            self.assertIsInstance(result, dict)
            self.assertEqual(result['smiles'], self.test_smiles_list[i])
    
    def test_workflow_analysis(self):
        """Test OOP workflow analysis."""
        caps = self.adapter.get_capabilities()
        
        if not caps.get('oop_workflows', False):
            self.skipTest("OOP workflows not available")
        
        result = self.adapter.analyze_with_workflow(self.test_smiles)
        
        self.assertIsInstance(result, dict)
        self.assertIn('smiles', result)
        self.assertIn('valid', result)
        
        # Should indicate it used the workflow method
        if 'method' in result:
            self.assertIn('workflow', result['method'])
    
    def test_calculator_creation(self):
        """Test OOP calculator creation."""
        caps = self.adapter.get_capabilities()
        
        if not caps.get('oop_calculators', False):
            self.skipTest("OOP calculators not available")
        
        try:
            basic_calc = self.adapter.create_calculator('basic')
            self.assertIsNotNone(basic_calc)
        except Exception as e:
            self.fail(f"Failed to create basic calculator: {e}")
        
        try:
            factory = self.adapter.create_calculator('factory')
            self.assertIsNotNone(factory)
        except Exception as e:
            self.fail(f"Failed to create calculator factory: {e}")
    
    def test_batch_workflow_analysis(self):
        """Test batch analysis with OOP workflows."""
        caps = self.adapter.get_capabilities()
        
        if not caps.get('oop_workflows', False):
            self.skipTest("OOP workflows not available")
        
        results = self.adapter.batch_analyze_with_workflow(self.test_smiles_list)
        
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), len(self.test_smiles_list))
        
        for result in results:
            self.assertIsInstance(result, dict)
            self.assertIn('smiles', result)
    
    def test_error_handling(self):
        """Test error handling for invalid input."""
        if not self.adapter.capabilities.has_core_analysis:
            self.skipTest("Core analysis not available")
        
        # Test with invalid SMILES
        result = self.adapter.analyze_single_molecule("invalid_smiles")
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['smiles'], "invalid_smiles")
        self.assertFalse(result['valid'])
        self.assertIn('properties', result)

    def test_perform_conformational_analysis(self):
        """Test conformational analysis."""
        if not self.adapter.capabilities.has_conformational_analysis:
            self.skipTest("Conformational analysis not available")

        test_smiles = "CCO"
        num_conformers = 3
        result = self.adapter.perform_conformational_analysis(test_smiles, num_conformers)

        self.assertIsInstance(result, dict)
        self.assertIn('smiles', result)
        self.assertIn('num_conformers_requested', result)
        self.assertIn('conformational_analysis_results', result)
        self.assertIn('method', result)

        self.assertEqual(result['smiles'], test_smiles)
        self.assertEqual(result['num_conformers_requested'], num_conformers)
        self.assertEqual(result['method'], 'conformational_analysis')

        if result['conformational_analysis_results'].get('error'):
            self.assertIn('Failed to generate at least 2 conformers', result['conformational_analysis_results']['error'])
        else:
            self.assertIsInstance(result['conformational_analysis_results'], dict)
            self.assertIn('num_conformers', result['conformational_analysis_results']['conformational_analysis'])
            self.assertGreater(result['conformational_analysis_results']['conformational_analysis']['num_conformers'], 0)

    def test_get_advanced_analysis(self):
        """Test advanced analysis."""
        if not self.adapter.capabilities.has_advanced_properties:
            self.skipTest("Advanced properties analysis not available")

        test_smiles = "CCO"
        result = self.adapter.get_advanced_analysis(test_smiles)

        self.assertIsInstance(result, dict)
        self.assertIn('smiles', result)
        self.assertIn('advanced_analysis_results', result)
        self.assertIn('method', result)

        self.assertEqual(result['smiles'], test_smiles)
        self.assertEqual(result['method'], 'advanced_properties_analysis')
        self.assertIsInstance(result['advanced_analysis_results'], dict)
        self.assertGreater(len(result['advanced_analysis_results']), 0)


@unittest.skipUnless(ADAPTER_AVAILABLE, "Integration adapter not available")
class TestAdapterFactory(unittest.TestCase):
    """Test adapter factory functionality."""
    
    def test_create_auto_adapter(self):
        """Test creating auto-configured adapter."""
        adapter = AdapterFactory.create_auto_adapter()
        
        self.assertIsInstance(adapter, MolecularAnalyzerAdapter)
        self.assertIsNotNone(adapter.capabilities)
    
    def test_create_minimal_adapter(self):
        """Test creating minimal adapter."""
        adapter = AdapterFactory.create_minimal_adapter()
        
        self.assertIsInstance(adapter, MolecularAnalyzerAdapter)
        self.assertIsNotNone(adapter.capabilities)
    
    def test_create_full_adapter(self):
        """Test creating full-featured adapter."""
        adapter = AdapterFactory.create_full_adapter()
        
        self.assertIsInstance(adapter, MolecularAnalyzerAdapter)
        self.assertIsNotNone(adapter.capabilities)
    
    def test_backwards_compatibility(self):
        """Test backwards compatible adapter creation."""
        adapter = create_adapter()
        
        self.assertIsInstance(adapter, MolecularAnalyzerAdapter)


@unittest.skipUnless(ADAPTER_AVAILABLE, "Integration adapter not available")
class TestQuickFunctions(unittest.TestCase):
    """Test quick access functions."""
    
    def test_quick_analyze(self):
        """Test quick analyze function."""
        result = quick_analyze("CCO")
        
        self.assertIsInstance(result, dict)
        self.assertIn('smiles', result)
        self.assertIn('valid', result)
        self.assertEqual(result['smiles'], "CCO")


class TestAdapterIntegration(unittest.TestCase):
    """Test adapter integration with the molecular analyzer system."""
    
    def setUp(self):
        """Set up test fixtures."""
        if ADAPTER_AVAILABLE:
            self.adapter = AdapterFactory.create_auto_adapter()
    
    @unittest.skipUnless(ADAPTER_AVAILABLE, "Integration adapter not available")
    def test_adapter_with_core_system(self):
        """Test adapter integration with core molecular analyzer."""
        health = self.adapter.health_check()
        
        if not health.get('core_available', False):
            self.skipTest("Core system not available")
        
        # Test that adapter can successfully analyze molecules
        result = self.adapter.analyze_single_molecule("CCO")
        self.assertTrue(result.get('valid', False))
        
        # Test capabilities match what's actually available
        caps = self.adapter.get_capabilities()
        if caps.get('oop_workflows', False):
            # Should be able to use workflow analysis
            workflow_result = self.adapter.analyze_with_workflow("CCO")
            self.assertIsInstance(workflow_result, dict)
    
    @unittest.skipUnless(ADAPTER_AVAILABLE, "Integration adapter not available")
    def test_adapter_performance(self):
        """Test adapter performance characteristics."""
        if not self.adapter.capabilities.has_core_analysis:
            self.skipTest("Core analysis not available")
        
        import time
        
        # Time single molecule analysis
        start_time = time.time()
        result = self.adapter.analyze_single_molecule("CCO")
        single_time = time.time() - start_time
        
        # Should complete in reasonable time (< 5 seconds)
        self.assertLess(single_time, 5.0)
        
        # Time batch analysis
        test_smiles = ["CCO", "CC", "C"]
        start_time = time.time()
        results = self.adapter.analyze_batch(test_smiles)
        batch_time = time.time() - start_time
        
        # Batch should complete in reasonable time
        self.assertLess(batch_time, 15.0)
        self.assertEqual(len(results), len(test_smiles))


if __name__ == '__main__':
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestAdapterCapabilities,
        TestMolecularAnalyzerAdapter,
        TestAdapterFactory,
        TestQuickFunctions,
        TestAdapterIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"INTEGRATION ADAPTER TEST SUMMARY")
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