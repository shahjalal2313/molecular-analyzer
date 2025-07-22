"""
CodeChangeAnalyzer: AST-based code analysis for automated documentation generation.

This module provides comprehensive code analysis capabilities using Abstract Syntax Tree (AST)
parsing to detect code changes, extract documentation information, and identify dependencies.
"""

import ast
import os
import sys
import importlib.util
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CodeElement:
    """Represents a code element (class, function, method) with metadata."""
    name: str
    type: str  # 'class', 'function', 'method', 'variable'
    file_path: str
    line_number: int
    docstring: Optional[str]
    parameters: List[str]
    return_type: Optional[str]
    decorators: List[str]
    dependencies: Set[str]
    complexity_score: int

@dataclass
class CodeChange:
    """Represents a detected code change."""
    change_type: str  # 'added', 'modified', 'deleted'
    element: CodeElement
    old_element: Optional[CodeElement]
    impact_level: str  # 'low', 'medium', 'high'
    description: str

class CodeChangeAnalyzer:
    """
    AST-based code analysis system for automated documentation generation.
    
    Features:
    - Parse Python files using AST to extract code elements
    - Detect code changes by comparing current and previous states
    - Identify dependencies and cross-references
    - Calculate complexity metrics
    - Generate documentation templates based on code structure
    """
    
    def __init__(self, project_root: str):
        """
        Initialize the CodeChangeAnalyzer.
        
        Args:
            project_root: Root directory of the project to analyze
        """
        self.project_root = Path(project_root)
        self.code_elements_cache: Dict[str, List[CodeElement]] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
        
    def analyze_file(self, file_path: str) -> List[CodeElement]:
        """
        Analyze a Python file and extract all code elements.
        
        Args:
            file_path: Path to the Python file to analyze
            
        Returns:
            List of CodeElement objects representing the file's structure
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            elements = []
            
            # Visit all nodes in the AST
            for node in ast.walk(tree):
                element = self._extract_element_from_node(node, file_path)
                if element:
                    elements.append(element)
            
            # Cache the results
            self.code_elements_cache[file_path] = elements
            return elements
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return []
    
    def _extract_element_from_node(self, node: ast.AST, file_path: str) -> Optional[CodeElement]:
        """Extract CodeElement from an AST node."""
        if isinstance(node, ast.FunctionDef):
            return self._extract_function_element(node, file_path)
        elif isinstance(node, ast.ClassDef):
            return self._extract_class_element(node, file_path)
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            return self._extract_variable_element(node, file_path)
        return None
    
    def _extract_function_element(self, node: ast.FunctionDef, file_path: str) -> CodeElement:
        """Extract function/method information from AST node."""
        # Extract parameters
        parameters = []
        for arg in node.args.args:
            parameters.append(arg.arg)
        
        # Extract decorators
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                decorators.append(ast.unparse(decorator))
        
        # Extract docstring
        docstring = None
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            docstring = node.body[0].value.value
        
        # Extract return type annotation
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns)
        
        # Calculate complexity (simplified cyclomatic complexity)
        complexity = self._calculate_complexity(node)
        
        # Extract dependencies
        dependencies = self._extract_dependencies(node)
        
        return CodeElement(
            name=node.name,
            type='function',
            file_path=file_path,
            line_number=node.lineno,
            docstring=docstring,
            parameters=parameters,
            return_type=return_type,
            decorators=decorators,
            dependencies=dependencies,
            complexity_score=complexity
        )
    
    def _extract_class_element(self, node: ast.ClassDef, file_path: str) -> CodeElement:
        """Extract class information from AST node."""
        # Extract base classes
        dependencies = set()
        for base in node.bases:
            if isinstance(base, ast.Name):
                dependencies.add(base.id)
            elif isinstance(base, ast.Attribute):
                dependencies.add(ast.unparse(base))
        
        # Extract decorators
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                decorators.append(ast.unparse(decorator))
        
        # Extract docstring
        docstring = None
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            docstring = node.body[0].value.value
        
        # Calculate complexity (number of methods)
        complexity = len([n for n in node.body if isinstance(n, ast.FunctionDef)])
        
        return CodeElement(
            name=node.name,
            type='class',
            file_path=file_path,
            line_number=node.lineno,
            docstring=docstring,
            parameters=[],
            return_type=None,
            decorators=decorators,
            dependencies=dependencies,
            complexity_score=complexity
        )
    
    def _extract_variable_element(self, node: ast.Assign, file_path: str) -> Optional[CodeElement]:
        """Extract variable/constant information from AST node."""
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            return None
        
        var_name = node.targets[0].id
        
        # Only include constants (uppercase names) or module-level variables
        if not var_name.isupper():
            return None
        
        dependencies = self._extract_dependencies(node)
        
        return CodeElement(
            name=var_name,
            type='variable',
            file_path=file_path,
            line_number=node.lineno,
            docstring=None,
            parameters=[],
            return_type=None,
            decorators=[],
            dependencies=dependencies,
            complexity_score=1
        )
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate simplified cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _extract_dependencies(self, node: ast.AST) -> Set[str]:
        """Extract dependencies (imported modules, called functions, etc.)."""
        dependencies = set()
        
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                dependencies.add(child.id)
            elif isinstance(child, ast.Attribute):
                # Get the root of the attribute chain
                attr_parts = []
                current = child
                while isinstance(current, ast.Attribute):
                    attr_parts.append(current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    attr_parts.append(current.id)
                    dependencies.add('.'.join(reversed(attr_parts)))
        
        return dependencies
    
    def detect_changes(self, old_file_path: str, new_file_path: str) -> List[CodeChange]:
        """
        Detect changes between two versions of a file.
        
        Args:
            old_file_path: Path to the previous version of the file
            new_file_path: Path to the current version of the file
            
        Returns:
            List of CodeChange objects representing detected changes
        """
        old_elements = self.analyze_file(old_file_path) if os.path.exists(old_file_path) else []
        new_elements = self.analyze_file(new_file_path)
        
        changes = []
        
        # Create lookup dictionaries
        old_lookup = {elem.name: elem for elem in old_elements}
        new_lookup = {elem.name: elem for elem in new_elements}
        
        # Detect added elements
        for name, element in new_lookup.items():
            if name not in old_lookup:
                changes.append(CodeChange(
                    change_type='added',
                    element=element,
                    old_element=None,
                    impact_level=self._assess_impact_level(element, None),
                    description=f"Added {element.type} '{name}'"
                ))
        
        # Detect deleted elements
        for name, element in old_lookup.items():
            if name not in new_lookup:
                changes.append(CodeChange(
                    change_type='deleted',
                    element=element,
                    old_element=element,
                    impact_level=self._assess_impact_level(None, element),
                    description=f"Deleted {element.type} '{name}'"
                ))
        
        # Detect modified elements
        for name, new_element in new_lookup.items():
            if name in old_lookup:
                old_element = old_lookup[name]
                if self._elements_differ(old_element, new_element):
                    changes.append(CodeChange(
                        change_type='modified',
                        element=new_element,
                        old_element=old_element,
                        impact_level=self._assess_impact_level(new_element, old_element),
                        description=f"Modified {new_element.type} '{name}'"
                    ))
        
        return changes
    
    def _elements_differ(self, old: CodeElement, new: CodeElement) -> bool:
        """Check if two code elements are different."""
        return (old.parameters != new.parameters or
                old.return_type != new.return_type or
                old.decorators != new.decorators or
                old.docstring != new.docstring or
                old.dependencies != new.dependencies)
    
    def _assess_impact_level(self, new_element: Optional[CodeElement], 
                           old_element: Optional[CodeElement]) -> str:
        """Assess the impact level of a code change."""
        if new_element and new_element.type == 'class':
            return 'high'
        elif new_element and new_element.complexity_score > 5:
            return 'high'
        elif old_element and old_element.type == 'class':
            return 'high'
        elif (new_element and old_element and 
              new_element.parameters != old_element.parameters):
            return 'medium'
        else:
            return 'low'
    
    def analyze_project(self) -> Dict[str, List[CodeElement]]:
        """
        Analyze the entire project and return all code elements.
        
        Returns:
            Dictionary mapping file paths to lists of code elements
        """
        project_elements = {}
        
        # Find all Python files in the project
        for py_file in self.project_root.rglob('*.py'):
            if '__pycache__' not in str(py_file):
                elements = self.analyze_file(str(py_file))
                project_elements[str(py_file)] = elements
        
        return project_elements
    
    def get_documentation_suggestions(self, element: CodeElement) -> List[str]:
        """
        Generate documentation suggestions for a code element.
        
        Args:
            element: The code element to generate suggestions for
            
        Returns:
            List of documentation suggestions
        """
        suggestions = []
        
        # Check for missing docstring
        if not element.docstring:
            suggestions.append(f"Add docstring for {element.type} '{element.name}'")
        
        # Check for complex functions without proper documentation
        if element.complexity_score > 3 and not element.docstring:
            suggestions.append(f"Complex {element.type} '{element.name}' needs detailed documentation")
        
        # Check for functions with parameters but no parameter documentation
        if element.parameters and element.docstring:
            docstring_lower = element.docstring.lower()
            for param in element.parameters:
                if param not in docstring_lower:
                    suggestions.append(f"Document parameter '{param}' in {element.name}")
        
        # Check for functions with return type but no return documentation
        if element.return_type and element.docstring:
            if 'return' not in element.docstring.lower():
                suggestions.append(f"Document return value for {element.name}")
        
        return suggestions