"""
Simple validation tests for OOP structure.

This module provides basic validation tests that work with the actual API
and verify that the core OOP components are functional.
"""

import unittest
import sys
import os
from pathlib import Path

# Add src to path for testing
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


class TestBasicFunctionality(unittest.TestCase):
    """Test basic functionality that should always work."""
    
    def test_package_import(self):
        """Test that the main package can be imported."""
        try:
            import molecular_analyzer
            self.assertTrue(hasattr(molecular_analyzer, '__version__'))
        except ImportError as e:
            self.fail(f"Failed to import molecular_analyzer: {e}")
    
    def test_legacy_functionality(self):
        """Test that legacy functions still work."""
        try:
            import molecular_analyzer
            
            # Test legacy analysis
            result = molecular_analyzer.quick_analysis("CCO")
            self.assertIsInstance(result, dict)
            self.assertIn('smiles', result)
            self.assertIn('valid', result)
            
        except Exception as e:
            self.fail(f"Legacy functionality failed: {e}")
    
    def test_package_info(self):
        """Test package information."""
        try:
            import molecular_analyzer
            info = molecular_analyzer.get_package_info()
            
            self.assertIsInstance(info, dict)
            self.assertIn('name', info)
            self.assertIn('version', info)
            self.assertIn('oop_capabilities', info)
            
        except Exception as e:
            self.fail(f"Package info failed: {e}")
    
    def test_oop_components_available(self):
        """Test that OOP components are available."""
        try:
            import molecular_analyzer
            info = molecular_analyzer.get_package_info()
            oop_caps = info.get('oop_capabilities', {})
            
            # At least models should be available
            self.assertTrue(oop_caps.get('models', False), "OOP models should be available")
            
            # Check what's actually available
            print(f"OOP Capabilities: {oop_caps}")
            
        except Exception as e:
            self.fail(f"OOP capabilities check failed: {e}")
    
    def test_models_basic_import(self):
        """Test basic model imports."""
        try:
            from molecular_analyzer.models import MoleculeData, PropertyData, AnalysisResult
            
            # Test basic creation
            mol_data = MoleculeData(smiles="CCO")
            self.assertEqual(mol_data.smiles, "CCO")
            self.assertTrue(mol_data.validated)
            
        except ImportError:
            self.skipTest("Models not available")
        except Exception as e:
            self.fail(f"Model creation failed: {e}")
    
    def test_calculators_basic_import(self):
        """Test basic calculator imports."""
        try:
            from molecular_analyzer.calculators import BasicPropertiesCalculator
            
            calc = BasicPropertiesCalculator()
            self.assertIsNotNone(calc)
            
        except ImportError:
            self.skipTest("Calculators not available")
        except Exception as e:
            self.fail(f"Calculator creation failed: {e}")
    
    def test_workflows_basic_import(self):
        """Test basic workflow imports."""
        try:
            from molecular_analyzer.workflows import MolecularAnalysisWorkflow
            
            workflow = MolecularAnalysisWorkflow()
            self.assertIsNotNone(workflow)
            
        except ImportError:
            self.skipTest("Workflows not available")
        except Exception as e:
            self.fail(f"Workflow creation failed: {e}")
    
    def test_visualization_basic_import(self):
        """Test basic visualization imports."""
        try:
            from molecular_analyzer.visualization import Chart2DRenderer, ReportGenerator
            
            renderer = Chart2DRenderer()
            generator = ReportGenerator()
            self.assertIsNotNone(renderer)
            self.assertIsNotNone(generator)
            
        except ImportError:
            self.skipTest("Visualization not available")
        except Exception as e:
            self.fail(f"Visualization creation failed: {e}")
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        try:
            import molecular_analyzer
            
            # Test workflow creation
            try:
                workflow = molecular_analyzer.create_analyzer_workflow()
                self.assertIsNotNone(workflow)
            except ImportError:
                self.skipTest("Workflow convenience function not available")
            
            # Test calculator creation
            try:
                calc = molecular_analyzer.create_basic_calculator()
                self.assertIsNotNone(calc)
            except ImportError:
                self.skipTest("Calculator convenience function not available")
            
            # Test factory creation
            try:
                factory = molecular_analyzer.create_calculator_factory()
                self.assertIsNotNone(factory)
            except ImportError:
                self.skipTest("Factory convenience function not available")
                
        except Exception as e:
            self.fail(f"Convenience functions failed: {e}")


class TestIntegrationAdapter(unittest.TestCase):
    """Test integration adapter functionality."""
    
    def test_adapter_import(self):
        """Test adapter import."""
        try:
            integration_path = str(Path(__file__).parent.parent / "integration")
            if integration_path not in sys.path:
                sys.path.insert(0, integration_path)
            
            from adapter_v2 import AdapterFactory
            
            adapter = AdapterFactory.create_auto_adapter()
            self.assertIsNotNone(adapter)
            
        except ImportError:
            self.skipTest("Integration adapter not available")
        except Exception as e:
            self.fail(f"Adapter creation failed: {e}")
    
    def test_adapter_health_check(self):
        """Test adapter health check."""
        try:
            integration_path = str(Path(__file__).parent.parent / "integration")
            if integration_path not in sys.path:
                sys.path.insert(0, integration_path)
            
            from adapter_v2 import AdapterFactory
            
            adapter = AdapterFactory.create_auto_adapter()
            health = adapter.health_check()
            
            self.assertIsInstance(health, dict)
            self.assertIn('core_available', health)
            self.assertIn('version', health)
            
        except ImportError:
            self.skipTest("Integration adapter not available")
        except Exception as e:
            self.fail(f"Adapter health check failed: {e}")
    
    def test_adapter_capabilities(self):
        """Test adapter capabilities."""
        try:
            integration_path = str(Path(__file__).parent.parent / "integration")
            if integration_path not in sys.path:
                sys.path.insert(0, integration_path)
            
            from adapter_v2 import AdapterFactory
            
            adapter = AdapterFactory.create_auto_adapter()
            caps = adapter.get_capabilities()
            
            self.assertIsInstance(caps, dict)
            self.assertIn('version', caps)
            self.assertIn('core_analysis', caps)
            
            # Print capabilities for debugging
            print(f"Adapter Capabilities: {caps}")
            
        except ImportError:
            self.skipTest("Integration adapter not available")
        except Exception as e:
            self.fail(f"Adapter capabilities check failed: {e}")


class TestEndToEndBasic(unittest.TestCase):
    """Test basic end-to-end functionality."""
    
    def test_simple_analysis(self):
        """Test simple molecular analysis."""
        try:
            import molecular_analyzer
            
            # Use legacy analysis (should always work)
            result = molecular_analyzer.quick_analysis("CCO")
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result['smiles'], "CCO")
            
            if result['valid']:
                self.assertIn('properties', result)
                self.assertIsInstance(result['properties'], dict)
            
        except Exception as e:
            self.fail(f"Simple analysis failed: {e}")
    
    def test_oop_workflow_if_available(self):
        """Test OOP workflow if available."""
        try:
            import molecular_analyzer
            info = molecular_analyzer.get_package_info()
            
            if info['oop_capabilities']['workflows']:
                workflow = molecular_analyzer.create_analyzer_workflow()
                result = workflow.analyze_smiles("CCO")
                
                self.assertIsNotNone(result)
                print(f"OOP Workflow result type: {type(result)}")
                
            else:
                self.skipTest("OOP workflows not available")
                
        except Exception as e:
            self.fail(f"OOP workflow test failed: {e}")


if __name__ == '__main__':
    # Run tests with maximum verbosity
    unittest.main(verbosity=2)