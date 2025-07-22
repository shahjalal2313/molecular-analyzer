"""
Setup utilities for creating standalone molecular analyzer packages
"""

import os
import shutil
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import tempfile
import importlib.util


def create_standalone_package(target_dir: str, include_examples: bool = True) -> str:
    """
    Create a standalone molecular analyzer package.
    
    Args:
        target_dir: Target directory for the standalone package
        include_examples: Whether to include example scripts
    
    Returns:
        Path to the created package
    """
    # Get current package location
    current_dir = Path(__file__).parent.parent.parent
    src_dir = current_dir / "src" / "molecular_analyzer"
    
    # Create target structure
    target_path = Path(target_dir) / "molecular_analyzer_standalone"
    target_path.mkdir(parents=True, exist_ok=True)
    
    # Copy core molecular analyzer
    core_target = target_path / "molecular_analyzer"
    if core_target.exists():
        shutil.rmtree(core_target)
    
    shutil.copytree(src_dir, core_target)
    
    # Create requirements.txt
    requirements_content = """
rdkit-pypi>=2023.9.1
numpy>=1.21.0
pandas>=1.3.0
scipy>=1.7.0
matplotlib>=3.4.0
plotly>=5.0.0
streamlit>=1.25.0
"""
    
    with open(target_path / "requirements.txt", "w") as f:
        f.write(requirements_content.strip())
    
    # Create setup.py
    setup_content = '''
from setuptools import setup, find_packages

setup(
    name="molecular-analyzer-standalone",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "rdkit-pypi>=2023.9.1",
        "numpy>=1.21.0", 
        "pandas>=1.3.0",
        "scipy>=1.7.0",
        "matplotlib>=3.4.0",
        "plotly>=5.0.0"
    ],
    python_requires=">=3.8",
    author="Molecular Analyzer Team",
    description="Standalone molecular analysis toolkit",
    long_description="A comprehensive toolkit for molecular property analysis and visualization."
)
'''
    
    with open(target_path / "setup.py", "w") as f:
        f.write(setup_content.strip())
    
    # Create examples if requested
    if include_examples:
        examples_dir = target_path / "examples"
        examples_dir.mkdir(exist_ok=True)
        
        example_script = '''
"""
Example usage of standalone molecular analyzer
"""

from molecular_analyzer import quick_analysis, MolecularAnalyzer

# Quick analysis
result = quick_analysis("CCO")  # Ethanol
print("Quick Analysis Result:", result)

# Detailed analysis
analyzer = MolecularAnalyzer()
detailed_result = analyzer.analyze("CCO")
print("Detailed Analysis:", detailed_result)
'''
        
        with open(examples_dir / "basic_usage.py", "w") as f:
            f.write(example_script.strip())
    
    # Create README
    readme_content = """
# Molecular Analyzer Standalone Package

This is a standalone version of the molecular analyzer toolkit.

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from molecular_analyzer import quick_analysis

result = quick_analysis("CCO")  # Analyze ethanol
print(result)
```

## Features

- Molecular property calculation
- 3D structure generation
- Visualization capabilities
- Batch processing
- Drug-likeness assessment

## Examples

See the `examples/` directory for usage examples.
"""
    
    with open(target_path / "README.md", "w") as f:
        f.write(readme_content.strip())
    
    return str(target_path)


def validate_standalone_package(package_path: str) -> Dict[str, Any]:
    """
    Validate that a standalone package works correctly.
    
    Args:
        package_path: Path to the standalone package
    
    Returns:
        Validation results
    """
    results = {
        'valid': True,
        'tests_passed': [],
        'tests_failed': [],
        'errors': []
    }
    
    package_path = Path(package_path)
    
    # Test 1: Package structure
    try:
        required_files = [
            'molecular_analyzer/__init__.py',
            'setup.py',
            'requirements.txt',
            'README.md'
        ]
        
        for file_path in required_files:
            if not (package_path / file_path).exists():
                raise FileNotFoundError(f"Required file missing: {file_path}")
        
        results['tests_passed'].append('Package structure')
        
    except Exception as e:
        results['tests_failed'].append('Package structure')
        results['errors'].append(str(e))
        results['valid'] = False
    
    # Test 2: Import test
    try:
        # Add package to path temporarily
        old_path = sys.path[:]
        sys.path.insert(0, str(package_path))
        
        spec = importlib.util.spec_from_file_location(
            "molecular_analyzer", 
            package_path / "molecular_analyzer" / "__init__.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Test basic functionality
        if hasattr(module, 'quick_analysis'):
            test_result = module.quick_analysis("CCO")
            if test_result and test_result.get('valid'):
                results['tests_passed'].append('Import and basic functionality')
            else:
                raise RuntimeError("Basic functionality test failed")
        else:
            raise AttributeError("quick_analysis function not found")
        
        # Restore path
        sys.path[:] = old_path
        
    except Exception as e:
        results['tests_failed'].append('Import and basic functionality')
        results['errors'].append(str(e))
        results['valid'] = False
        sys.path[:] = old_path
    
    # Test 3: Dependencies check
    try:
        requirements_file = package_path / "requirements.txt"
        if requirements_file.exists():
            with open(requirements_file, 'r') as f:
                requirements = f.read()
                if 'rdkit' in requirements and 'numpy' in requirements:
                    results['tests_passed'].append('Dependencies specification')
                else:
                    raise ValueError("Required dependencies missing from requirements.txt")
        else:
            raise FileNotFoundError("requirements.txt not found")
            
    except Exception as e:
        results['tests_failed'].append('Dependencies specification')
        results['errors'].append(str(e))
        results['valid'] = False
    
    return results


def get_package_info() -> Dict[str, Any]:
    """Get information about the current molecular analyzer package."""
    try:
        from . import __version__
        version = __version__
    except ImportError:
        version = "unknown"
    
    current_dir = Path(__file__).parent
    
    return {
        'version': version,
        'location': str(current_dir),
        'components': {
            'core': (current_dir / "core.py").exists(),
            'properties': (current_dir / "properties.py").exists(),
            'advanced_properties': (current_dir / "advanced_properties.py").exists(),
            'calculator': (current_dir / "calculator.py").exists(),
            'visualization_3d': (current_dir / "visualization_3d.py").exists(),
            'comparison': (current_dir / "comparison.py").exists(),
            'conformational': (current_dir / "conformational.py").exists()
        }
    }


if __name__ == "__main__":
    # Self-test
    with tempfile.TemporaryDirectory() as temp_dir:
        print("Creating standalone package...")
        package_path = create_standalone_package(temp_dir, include_examples=True)
        print(f"Package created at: {package_path}")
        
        print("\nValidating package...")
        validation = validate_standalone_package(package_path)
        print(f"Validation result: {validation}")
        
        print("\nPackage info:")
        info = get_package_info()
        print(info)