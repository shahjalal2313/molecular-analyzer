"""
DocumentationTemplateEngine: Automated documentation generation and template management.

This module provides intelligent template-based documentation generation for code elements,
with support for multiple documentation formats and automatic cross-reference management.
"""

import re
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import logging

from .code_analyzer import CodeElement, CodeChange

logger = logging.getLogger(__name__)

@dataclass
class DocumentationTemplate:
    """Represents a documentation template with metadata."""
    name: str
    template_type: str  # 'function', 'class', 'module', 'api'
    template_content: str
    placeholders: List[str]
    required_fields: List[str]
    format_type: str  # 'markdown', 'rst', 'docstring'

@dataclass
class DocumentationSection:
    """Represents a section of generated documentation."""
    title: str
    content: str
    section_type: str
    references: List[str]
    auto_generated: bool
    last_updated: datetime

class DocumentationTemplateEngine:
    """
    Advanced template engine for automated documentation generation.
    
    Features:
    - Generate documentation from code analysis
    - Support multiple documentation formats (Markdown, RST, docstrings)
    - Automatic cross-reference management
    - Template customization and inheritance
    - Documentation quality assessment
    """
    
    def __init__(self, project_root: str):
        """
        Initialize the DocumentationTemplateEngine.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.templates: Dict[str, DocumentationTemplate] = {}
        self.cross_references: Dict[str, List[str]] = {}
        self.documentation_cache: Dict[str, str] = {}
        
        # Initialize default templates
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default documentation templates."""
        
        # Function documentation template
        function_template = DocumentationTemplate(
            name="function_docstring",
            template_type="function",
            template_content='''"""
{description}

Args:
{parameters}

Returns:
    {return_description}

Raises:
{exceptions}

Example:
    {example}
"""''',
            placeholders=["description", "parameters", "return_description", "exceptions", "example"],
            required_fields=["description"],
            format_type="docstring"
        )
        
        # Class documentation template
        class_template = DocumentationTemplate(
            name="class_docstring",
            template_type="class",
            template_content='''"""
{description}

Attributes:
{attributes}

Methods:
{methods_summary}

Example:
    {example}
"""''',
            placeholders=["description", "attributes", "methods_summary", "example"],
            required_fields=["description"],
            format_type="docstring"
        )
        
        # Module documentation template
        module_template = DocumentationTemplate(
            name="module_documentation",
            template_type="module",
            template_content='''# {module_name}

{description}

## Overview

{overview}

## Classes

{classes_list}

## Functions

{functions_list}

## Usage

{usage_examples}

## API Reference

{api_reference}
''',
            placeholders=["module_name", "description", "overview", "classes_list", "functions_list", "usage_examples", "api_reference"],
            required_fields=["module_name", "description"],
            format_type="markdown"
        )
        
        # API documentation template
        api_template = DocumentationTemplate(
            name="api_reference",
            template_type="api",
            template_content='''## {element_name}

**Type**: {element_type}  
**File**: `{file_path}:{line_number}`  
**Complexity**: {complexity_score}/10

### Description

{description}

### Signature

```python
{signature}
```

### Parameters

{parameters_table}

### Returns

{return_info}

### Dependencies

{dependencies_list}

### Usage Examples

{examples}

---
''',
            placeholders=["element_name", "element_type", "file_path", "line_number", "complexity_score", "description", "signature", "parameters_table", "return_info", "dependencies_list", "examples"],
            required_fields=["element_name", "element_type"],
            format_type="markdown"
        )
        
        # Store templates
        self.templates["function"] = function_template
        self.templates["class"] = class_template
        self.templates["module"] = module_template
        self.templates["api"] = api_template
    
    def generate_documentation(self, element: CodeElement, template_type: str = "api") -> str:
        """
        Generate documentation for a code element using the specified template.
        
        Args:
            element: The code element to document
            template_type: Type of template to use ('function', 'class', 'module', 'api')
            
        Returns:
            Generated documentation string
        """
        if template_type not in self.templates:
            logger.warning(f"Template type '{template_type}' not found, using 'api' template")
            template_type = "api"
        
        template = self.templates[template_type]
        content = template.template_content
        
        # Prepare template variables
        variables = self._prepare_template_variables(element)
        
        # Replace placeholders
        for placeholder in template.placeholders:
            placeholder_pattern = f"{{{placeholder}}}"
            replacement = variables.get(placeholder, f"[{placeholder.upper()}_TODO]")
            content = content.replace(placeholder_pattern, replacement)
        
        return content
    
    def _prepare_template_variables(self, element: CodeElement) -> Dict[str, str]:
        """Prepare variables for template substitution."""
        variables = {
            "element_name": element.name,
            "element_type": element.type.capitalize(),
            "file_path": str(Path(element.file_path).relative_to(self.project_root)),
            "line_number": str(element.line_number),
            "complexity_score": str(element.complexity_score),
            "description": element.docstring or f"[DESCRIPTION_TODO for {element.name}]",
            "signature": self._generate_signature(element),
            "parameters_table": self._generate_parameters_table(element),
            "return_info": self._generate_return_info(element),
            "dependencies_list": self._generate_dependencies_list(element),
            "examples": f"[EXAMPLES_TODO for {element.name}]",
            "parameters": self._generate_parameters_docstring(element),
            "return_description": element.return_type or "[RETURN_TODO]",
            "exceptions": "[EXCEPTIONS_TODO]",
            "example": f"[EXAMPLE_TODO for {element.name}]"
        }
        
        return variables
    
    def _generate_signature(self, element: CodeElement) -> str:
        """Generate function/method signature."""
        if element.type == "function":
            params = ", ".join(element.parameters) if element.parameters else ""
            return_annotation = f" -> {element.return_type}" if element.return_type else ""
            return f"def {element.name}({params}){return_annotation}:"
        elif element.type == "class":
            return f"class {element.name}:"
        else:
            return f"{element.name} = [VALUE]"
    
    def _generate_parameters_table(self, element: CodeElement) -> str:
        """Generate parameters table in markdown format."""
        if not element.parameters:
            return "No parameters."
        
        table = "| Parameter | Type | Description |\n"
        table += "|-----------|------|-------------|\n"
        
        for param in element.parameters:
            table += f"| `{param}` | [TYPE_TODO] | [DESCRIPTION_TODO] |\n"
        
        return table
    
    def _generate_parameters_docstring(self, element: CodeElement) -> str:
        """Generate parameters section for docstring."""
        if not element.parameters:
            return "    None"
        
        params_doc = []
        for param in element.parameters:
            params_doc.append(f"    {param} ([TYPE_TODO]): [DESCRIPTION_TODO]")
        
        return "\n".join(params_doc)
    
    def _generate_return_info(self, element: CodeElement) -> str:
        """Generate return information."""
        if element.return_type:
            return f"`{element.return_type}`: [RETURN_DESCRIPTION_TODO]"
        else:
            return "[RETURN_INFO_TODO]"
    
    def _generate_dependencies_list(self, element: CodeElement) -> str:
        """Generate dependencies list."""
        if not element.dependencies:
            return "No external dependencies."
        
        deps = []
        for dep in sorted(element.dependencies):
            if not dep.startswith('__') and dep not in ['self', 'cls']:
                deps.append(f"- `{dep}`")
        
        return "\n".join(deps) if deps else "No external dependencies."
    
    def generate_module_documentation(self, file_path: str, elements: List[CodeElement]) -> str:
        """
        Generate comprehensive module documentation.
        
        Args:
            file_path: Path to the module file
            elements: List of code elements in the module
            
        Returns:
            Generated module documentation
        """
        module_name = Path(file_path).stem
        
        # Separate elements by type
        classes = [e for e in elements if e.type == "class"]
        functions = [e for e in elements if e.type == "function"]
        variables = [e for e in elements if e.type == "variable"]
        
        # Generate sections
        classes_section = self._generate_classes_section(classes)
        functions_section = self._generate_functions_section(functions)
        variables_section = self._generate_variables_section(variables)
        
        # Module description
        module_docstring = self._extract_module_docstring(file_path)
        
        template = self.templates["module"]
        content = template.template_content
        
        variables_dict = {
            "module_name": module_name,
            "description": module_docstring or f"[MODULE_DESCRIPTION_TODO for {module_name}]",
            "overview": f"[MODULE_OVERVIEW_TODO for {module_name}]",
            "classes_list": classes_section,
            "functions_list": functions_section,
            "usage_examples": f"[USAGE_EXAMPLES_TODO for {module_name}]",
            "api_reference": f"[API_REFERENCE_TODO for {module_name}]"
        }
        
        for placeholder, value in variables_dict.items():
            content = content.replace(f"{{{placeholder}}}", value)
        
        return content
    
    def _generate_classes_section(self, classes: List[CodeElement]) -> str:
        """Generate classes section for module documentation."""
        if not classes:
            return "No classes defined in this module."
        
        section = []
        for cls in classes:
            description = cls.docstring or f"[DESCRIPTION_TODO for {cls.name}]"
            section.append(f"### {cls.name}\n\n{description}\n")
        
        return "\n".join(section)
    
    def _generate_functions_section(self, functions: List[CodeElement]) -> str:
        """Generate functions section for module documentation."""
        if not functions:
            return "No functions defined in this module."
        
        section = []
        for func in functions:
            description = func.docstring or f"[DESCRIPTION_TODO for {func.name}]"
            params = ", ".join(func.parameters) if func.parameters else ""
            section.append(f"### {func.name}({params})\n\n{description}\n")
        
        return "\n".join(section)
    
    def _generate_variables_section(self, variables: List[CodeElement]) -> str:
        """Generate variables section for module documentation."""
        if not variables:
            return "No module-level variables defined."
        
        section = []
        for var in variables:
            section.append(f"- **{var.name}**: [DESCRIPTION_TODO]")
        
        return "\n".join(section)
    
    def _extract_module_docstring(self, file_path: str) -> Optional[str]:
        """Extract module-level docstring from a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple regex to find module docstring
            docstring_pattern = r'^\s*"""(.*?)"""|^\s*\'\'\'(.*?)\'\'\''
            match = re.search(docstring_pattern, content, re.DOTALL | re.MULTILINE)
            
            if match:
                return match.group(1) or match.group(2)
            
        except Exception as e:
            logger.error(f"Error extracting module docstring from {file_path}: {e}")
        
        return None
    
    def generate_change_documentation(self, changes: List[CodeChange]) -> str:
        """
        Generate documentation for code changes.
        
        Args:
            changes: List of detected code changes
            
        Returns:
            Generated change documentation
        """
        if not changes:
            return "No changes detected."
        
        doc = f"# Code Changes - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        
        # Group changes by type
        added = [c for c in changes if c.change_type == "added"]
        modified = [c for c in changes if c.change_type == "modified"]
        deleted = [c for c in changes if c.change_type == "deleted"]
        
        if added:
            doc += "## Added Elements\n\n"
            for change in added:
                doc += f"- **{change.element.name}** ({change.element.type})\n"
                doc += f"  - File: `{change.element.file_path}:{change.element.line_number}`\n"
                doc += f"  - Impact: {change.impact_level}\n"
                doc += f"  - Description: {change.description}\n\n"
        
        if modified:
            doc += "## Modified Elements\n\n"
            for change in modified:
                doc += f"- **{change.element.name}** ({change.element.type})\n"
                doc += f"  - File: `{change.element.file_path}:{change.element.line_number}`\n"
                doc += f"  - Impact: {change.impact_level}\n"
                doc += f"  - Description: {change.description}\n\n"
        
        if deleted:
            doc += "## Deleted Elements\n\n"
            for change in deleted:
                doc += f"- **{change.element.name}** ({change.element.type})\n"
                doc += f"  - Impact: {change.impact_level}\n"
                doc += f"  - Description: {change.description}\n\n"
        
        return doc
    
    def update_cross_references(self, file_path: str, elements: List[CodeElement]):
        """
        Update cross-references for a file.
        
        Args:
            file_path: Path to the file
            elements: List of code elements in the file
        """
        self.cross_references[file_path] = []
        
        for element in elements:
            for dep in element.dependencies:
                if dep not in ['self', 'cls'] and not dep.startswith('__'):
                    self.cross_references[file_path].append(dep)
    
    def find_broken_references(self) -> List[str]:
        """
        Find broken cross-references in documentation.
        
        Returns:
            List of broken reference descriptions
        """
        broken_refs = []
        all_elements = set()
        
        # Collect all available elements
        for file_path, refs in self.cross_references.items():
            all_elements.update(refs)
        
        # Check for references that don't exist
        for file_path, refs in self.cross_references.items():
            for ref in refs:
                if ref not in all_elements and '.' not in ref:
                    broken_refs.append(f"Broken reference '{ref}' in {file_path}")
        
        return broken_refs
    
    def get_documentation_quality_score(self, element: CodeElement) -> float:
        """
        Calculate documentation quality score for a code element.
        
        Args:
            element: The code element to assess
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 0.0
        max_score = 0.0
        
        # Docstring presence and quality
        max_score += 0.4
        if element.docstring:
            score += 0.2
            if len(element.docstring) > 50:
                score += 0.1
            if any(keyword in element.docstring.lower() for keyword in ['args:', 'returns:', 'raises:']):
                score += 0.1
        
        # Parameter documentation
        if element.parameters:
            max_score += 0.3
            if element.docstring:
                documented_params = sum(1 for param in element.parameters 
                                      if param in element.docstring.lower())
                score += 0.3 * (documented_params / len(element.parameters))
        else:
            max_score += 0.3
            score += 0.3  # No parameters to document
        
        # Return type documentation
        max_score += 0.2
        if element.return_type:
            if element.docstring and 'return' in element.docstring.lower():
                score += 0.2
        else:
            score += 0.2  # No return type to document
        
        # Complexity vs documentation
        max_score += 0.1
        if element.complexity_score <= 3 or (element.docstring and len(element.docstring) > 100):
            score += 0.1
        
        return score / max_score if max_score > 0 else 0.0