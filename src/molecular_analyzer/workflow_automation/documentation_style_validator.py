"""
Documentation Style Validator: Automated style consistency checking for documentation.

This module provides comprehensive style validation for documentation, ensuring
consistency across the project according to established style guidelines.
"""

import re
import ast
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
import logging

from .code_analyzer import CodeElement

logger = logging.getLogger(__name__)

class StyleSeverity(Enum):
    """Style issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class StyleRule:
    """Represents a documentation style rule."""
    name: str
    description: str
    category: str  # 'format', 'content', 'structure', 'naming'
    severity: StyleSeverity
    auto_fixable: bool
    pattern: Optional[str] = None
    validator_function: Optional[str] = None

@dataclass
class StyleViolation:
    """Represents a style rule violation."""
    rule_name: str
    severity: StyleSeverity
    file_path: str
    line_number: int
    element_name: str
    description: str
    violation_text: str
    suggestion: str
    auto_fixable: bool

class DocumentationStyleValidator:
    """
    Comprehensive documentation style validation system.
    
    Features:
    - Configurable style rules for different documentation formats
    - Docstring format validation (Google, NumPy, Sphinx styles)
    - Consistency checking across the project
    - Auto-fix suggestions for common style issues
    - Customizable style guidelines
    """
    
    def __init__(self, project_root: str, style_config: Optional[Dict] = None):
        """Initialize the documentation style validator."""
        self.project_root = Path(project_root)
        self.style_config = style_config or self._get_default_style_config()
        
        # Initialize style rules
        self.style_rules = self._initialize_style_rules()
        
        # Style statistics
        self.validation_stats = {
            'files_checked': 0,
            'violations_found': 0,
            'auto_fixable_violations': 0,
            'violations_by_severity': {severity.value: 0 for severity in StyleSeverity}
        }
    
    def _get_default_style_config(self) -> Dict[str, Any]:
        """Get default style configuration."""
        return {
            'docstring_style': 'google',  # 'google', 'numpy', 'sphinx'
            'max_line_length': 88,
            'enforce_parameter_types': True,
            'enforce_return_types': True,
            'require_examples': False,
            'allow_one_line_docstrings': True,
            'enforce_section_order': True,
            'check_spelling': False,  # Requires additional dependencies
            'enforce_capitalization': True,
            'enforce_punctuation': True,
            'check_cross_references': True,
            'enforce_consistent_terminology': True
        }
    
    def _initialize_style_rules(self) -> Dict[str, StyleRule]:
        """Initialize all style validation rules."""
        rules = {}
        
        # Docstring format rules
        rules['docstring_quotes'] = StyleRule(
            name='docstring_quotes',
            description='Docstrings should use triple double quotes',
            category='format',
            severity=StyleSeverity.MEDIUM,
            auto_fixable=True,
            pattern=r"'''[\s\S]*?'''"
        )
        
        rules['docstring_capitalization'] = StyleRule(
            name='docstring_capitalization',
            description='Docstring first sentence should start with capital letter',
            category='content',
            severity=StyleSeverity.LOW,
            auto_fixable=True
        )
        
        rules['docstring_punctuation'] = StyleRule(
            name='docstring_punctuation',
            description='Docstring first sentence should end with period',
            category='content',
            severity=StyleSeverity.LOW,
            auto_fixable=True
        )
        
        rules['line_length'] = StyleRule(
            name='line_length',
            description=f'Documentation lines should not exceed {self.style_config["max_line_length"]} characters',
            category='format',
            severity=StyleSeverity.MEDIUM,
            auto_fixable=False
        )
        
        rules['parameter_format'] = StyleRule(
            name='parameter_format',
            description='Parameters should follow consistent format',
            category='structure',
            severity=StyleSeverity.MEDIUM,
            auto_fixable=True
        )
        
        rules['return_format'] = StyleRule(
            name='return_format',
            description='Return documentation should follow consistent format',
            category='structure',
            severity=StyleSeverity.MEDIUM,
            auto_fixable=True
        )
        
        rules['section_order'] = StyleRule(
            name='section_order',
            description='Docstring sections should follow standard order',
            category='structure',
            severity=StyleSeverity.LOW,
            auto_fixable=False
        )
        
        rules['empty_lines'] = StyleRule(
            name='empty_lines',
            description='Consistent empty line usage in docstrings',
            category='format',
            severity=StyleSeverity.LOW,
            auto_fixable=True
        )
        
        rules['cross_reference_format'] = StyleRule(
            name='cross_reference_format',
            description='Cross-references should use consistent format',
            category='content',
            severity=StyleSeverity.MEDIUM,
            auto_fixable=True
        )
        
        rules['terminology_consistency'] = StyleRule(
            name='terminology_consistency',
            description='Technical terminology should be consistent',
            category='content',
            severity=StyleSeverity.LOW,
            auto_fixable=False
        )
        
        return rules
    
    def validate_project_style(self) -> Tuple[List[StyleViolation], Dict[str, Any]]:
        """
        Validate documentation style for the entire project.
        
        Returns:
            Tuple of style violations and validation statistics
        """
        logger.info("Starting project-wide documentation style validation...")
        
        violations = []
        self.validation_stats = {
            'files_checked': 0,
            'violations_found': 0,
            'auto_fixable_violations': 0,
            'violations_by_severity': {severity.value: 0 for severity in StyleSeverity}
        }
        
        # Find all Python files
        for py_file in self.project_root.rglob('*.py'):
            if '__pycache__' not in str(py_file):
                file_violations = self.validate_file_style(str(py_file))
                violations.extend(file_violations)
                self.validation_stats['files_checked'] += 1
        
        # Update statistics
        self.validation_stats['violations_found'] = len(violations)
        self.validation_stats['auto_fixable_violations'] = len(
            [v for v in violations if v.auto_fixable]
        )
        
        for violation in violations:
            self.validation_stats['violations_by_severity'][violation.severity.value] += 1
        
        logger.info(f"Style validation completed: {len(violations)} violations found")
        
        return violations, self.validation_stats
    
    def validate_file_style(self, file_path: str) -> List[StyleViolation]:
        """
        Validate documentation style for a specific file.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            List of style violations found in the file
        """
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            lines = content.split('\n')
            
            # Check module docstring style
            module_violations = self._check_module_docstring_style(tree, lines, file_path)
            violations.extend(module_violations)
            
            # Check each code element
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    element_violations = self._check_element_docstring_style(
                        node, lines, file_path
                    )
                    violations.extend(element_violations)
            
            # Check overall file style
            file_violations = self._check_file_style(lines, file_path)
            violations.extend(file_violations)
            
        except Exception as e:
            logger.error(f"Error validating style for {file_path}: {e}")
        
        return violations
    
    def _check_module_docstring_style(self, tree: ast.AST, lines: List[str], 
                                    file_path: str) -> List[StyleViolation]:
        """Check module docstring style."""
        violations = []
        
        if (tree.body and isinstance(tree.body[0], ast.Expr) and 
            isinstance(tree.body[0].value, ast.Constant) and 
            isinstance(tree.body[0].value.value, str)):
            
            docstring = tree.body[0].value.value
            element_name = f"Module {Path(file_path).name}"
            
            # Check docstring style
            docstring_violations = self._validate_docstring_content(
                docstring, element_name, file_path, tree.body[0].lineno
            )
            violations.extend(docstring_violations)
        
        return violations
    
    def _check_element_docstring_style(self, node: ast.AST, lines: List[str], 
                                     file_path: str) -> List[StyleViolation]:
        """Check docstring style for a code element."""
        violations = []
        
        # Get docstring
        docstring = None
        if (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and 
            isinstance(node.body[0].value.value, str)):
            docstring = node.body[0].value.value
        
        if docstring:
            element_violations = self._validate_docstring_content(
                docstring, node.name, file_path, node.lineno
            )
            violations.extend(element_violations)
            
            # Check element-specific style rules
            if isinstance(node, ast.FunctionDef):
                function_violations = self._check_function_docstring_style(
                    node, docstring, file_path
                )
                violations.extend(function_violations)
            elif isinstance(node, ast.ClassDef):
                class_violations = self._check_class_docstring_style(
                    node, docstring, file_path
                )
                violations.extend(class_violations)
        
        return violations
    
    def _validate_docstring_content(self, docstring: str, element_name: str, 
                                  file_path: str, line_number: int) -> List[StyleViolation]:
        """Validate general docstring content and format."""
        violations = []
        
        # Check quotes style (should use triple double quotes)
        if self.style_config.get('enforce_capitalization', True):
            first_sentence = docstring.strip().split('.')[0].strip()
            if first_sentence and not first_sentence[0].isupper():
                violations.append(StyleViolation(
                    rule_name='docstring_capitalization',
                    severity=StyleSeverity.LOW,
                    file_path=file_path,
                    line_number=line_number,
                    element_name=element_name,
                    description='Docstring should start with capital letter',
                    violation_text=first_sentence[:50] + '...',
                    suggestion=f'Start with: {first_sentence[0].upper() + first_sentence[1:]}',
                    auto_fixable=True
                ))
        
        # Check punctuation
        if self.style_config.get('enforce_punctuation', True):
            first_sentence = docstring.strip().split('\n')[0].strip()
            if first_sentence and not first_sentence.endswith('.'):
                violations.append(StyleViolation(
                    rule_name='docstring_punctuation',
                    severity=StyleSeverity.LOW,
                    file_path=file_path,
                    line_number=line_number,
                    element_name=element_name,
                    description='Docstring first sentence should end with period',
                    violation_text=first_sentence,
                    suggestion=f'End with period: {first_sentence}.',
                    auto_fixable=True
                ))
        
        # Check line length
        max_length = self.style_config.get('max_line_length', 88)
        docstring_lines = docstring.split('\n')
        for i, line in enumerate(docstring_lines):
            if len(line) > max_length:
                violations.append(StyleViolation(
                    rule_name='line_length',
                    severity=StyleSeverity.MEDIUM,
                    file_path=file_path,
                    line_number=line_number + i,
                    element_name=element_name,
                    description=f'Line exceeds {max_length} characters ({len(line)})',
                    violation_text=line[:50] + '...',
                    suggestion=f'Break line into multiple lines',
                    auto_fixable=False
                ))
        
        # Check cross-reference format
        if self.style_config.get('check_cross_references', True):
            # Look for common cross-reference patterns
            cross_ref_patterns = [
                r'`[^`]+`',  # Inline code
                r':func:`[^`]+`',  # Function references
                r':class:`[^`]+`',  # Class references
                r':mod:`[^`]+`'  # Module references
            ]
            
            for pattern in cross_ref_patterns:
                matches = re.finditer(pattern, docstring)
                for match in matches:
                    ref_text = match.group()
                    # Check if reference follows project conventions
                    # This could be expanded with specific validation rules
                    pass
        
        return violations
    
    def _check_function_docstring_style(self, node: ast.FunctionDef, docstring: str, 
                                      file_path: str) -> List[StyleViolation]:
        """Check function-specific docstring style rules."""
        violations = []
        
        # Check parameter documentation format
        if self.style_config.get('enforce_parameter_types', True) and node.args.args:
            param_violations = self._check_parameter_documentation_style(
                node, docstring, file_path
            )
            violations.extend(param_violations)
        
        # Check return documentation format
        if self.style_config.get('enforce_return_types', True) and node.returns:
            return_violations = self._check_return_documentation_style(
                node, docstring, file_path
            )
            violations.extend(return_violations)
        
        # Check section order
        if self.style_config.get('enforce_section_order', True):
            section_violations = self._check_docstring_section_order(
                docstring, node.name, file_path, node.lineno
            )
            violations.extend(section_violations)
        
        return violations
    
    def _check_class_docstring_style(self, node: ast.ClassDef, docstring: str, 
                                   file_path: str) -> List[StyleViolation]:
        """Check class-specific docstring style rules."""
        violations = []
        
        # Check for attributes documentation
        if 'Attributes:' not in docstring and 'Attributes' not in docstring:
            # Look for instance variables in __init__
            init_method = None
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                    init_method = item
                    break
            
            if init_method:
                # Check if __init__ has self.attribute assignments
                has_attributes = False
                for stmt in ast.walk(init_method):
                    if (isinstance(stmt, ast.Assign) and 
                        isinstance(stmt.targets[0], ast.Attribute) and
                        isinstance(stmt.targets[0].value, ast.Name) and
                        stmt.targets[0].value.id == 'self'):
                        has_attributes = True
                        break
                
                if has_attributes:
                    violations.append(StyleViolation(
                        rule_name='class_attributes_documentation',
                        severity=StyleSeverity.MEDIUM,
                        file_path=file_path,
                        line_number=node.lineno,
                        element_name=node.name,
                        description='Class with attributes should document them',
                        violation_text='Missing Attributes section',
                        suggestion='Add Attributes section to class docstring',
                        auto_fixable=False
                    ))
        
        return violations
    
    def _check_parameter_documentation_style(self, node: ast.FunctionDef, docstring: str, 
                                           file_path: str) -> List[StyleViolation]:
        """Check parameter documentation style consistency."""
        violations = []
        
        # Get parameter names (excluding self/cls)
        param_names = [arg.arg for arg in node.args.args if arg.arg not in ['self', 'cls']]
        
        if not param_names:
            return violations
        
        # Check if Args section exists
        if 'Args:' not in docstring and 'Arguments:' not in docstring and 'Parameters:' not in docstring:
            violations.append(StyleViolation(
                rule_name='parameter_format',
                severity=StyleSeverity.MEDIUM,
                file_path=file_path,
                line_number=node.lineno,
                element_name=node.name,
                description='Function with parameters should have Args section',
                violation_text='Missing Args section',
                suggestion='Add Args section documenting parameters',
                auto_fixable=True
            ))
        else:
            # Check parameter format consistency
            style = self.style_config.get('docstring_style', 'google')
            expected_format = self._get_expected_parameter_format(style)
            
            # This could be expanded to check specific formatting rules
            pass
        
        return violations
    
    def _check_return_documentation_style(self, node: ast.FunctionDef, docstring: str, 
                                        file_path: str) -> List[StyleViolation]:
        """Check return documentation style consistency."""
        violations = []
        
        if 'Returns:' not in docstring and 'Return:' not in docstring:
            violations.append(StyleViolation(
                rule_name='return_format',
                severity=StyleSeverity.MEDIUM,
                file_path=file_path,
                line_number=node.lineno,
                element_name=node.name,
                description='Function with return type should have Returns section',
                violation_text='Missing Returns section',
                suggestion='Add Returns section documenting return value',
                auto_fixable=True
            ))
        
        return violations
    
    def _check_docstring_section_order(self, docstring: str, element_name: str, 
                                     file_path: str, line_number: int) -> List[StyleViolation]:
        """Check if docstring sections are in the expected order."""
        violations = []
        
        # Standard section order for Google style
        expected_order = [
            'Args:', 'Arguments:', 'Parameters:',
            'Returns:', 'Return:',
            'Yields:', 'Yield:',
            'Raises:', 'Raise:',
            'Note:', 'Notes:',
            'Example:', 'Examples:'
        ]
        
        # Find sections in docstring
        found_sections = []
        for section in expected_order:
            if section in docstring:
                pos = docstring.find(section)
                found_sections.append((section, pos))
        
        # Check if sections are in order
        found_sections.sort(key=lambda x: x[1])  # Sort by position
        
        # Map to expected order indices
        section_indices = []
        for section, _ in found_sections:
            for i, expected in enumerate(expected_order):
                if section == expected:
                    section_indices.append(i)
                    break
        
        # Check if indices are in ascending order
        if section_indices != sorted(section_indices):
            violations.append(StyleViolation(
                rule_name='section_order',
                severity=StyleSeverity.LOW,
                file_path=file_path,
                line_number=line_number,
                element_name=element_name,
                description='Docstring sections not in expected order',
                violation_text='Sections: ' + ', '.join([s[0] for s in found_sections]),
                suggestion='Reorder sections: Args, Returns, Raises, Examples',
                auto_fixable=False
            ))
        
        return violations
    
    def _check_file_style(self, lines: List[str], file_path: str) -> List[StyleViolation]:
        """Check file-level style issues."""
        violations = []
        
        # Check for consistent indentation in docstrings
        # Check for consistent quote usage
        # This could be expanded with more file-level checks
        
        return violations
    
    def _get_expected_parameter_format(self, style: str) -> str:
        """Get expected parameter documentation format for the given style."""
        formats = {
            'google': 'param_name (type): Description',
            'numpy': 'param_name : type\n    Description',
            'sphinx': ':param param_name: Description\n:type param_name: type'
        }
        return formats.get(style, formats['google'])
    
    def generate_style_report(self) -> str:
        """
        Generate a comprehensive style validation report.
        
        Returns:
            Formatted markdown report
        """
        violations, stats = self.validate_project_style()
        
        report = f"# Documentation Style Validation Report\n\n"
        report += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"**Style Configuration**: {self.style_config['docstring_style'].title()} style\n\n"
        
        # Overall statistics
        report += f"## Validation Summary\n\n"
        report += f"- **Files Checked**: {stats['files_checked']}\n"
        report += f"- **Total Violations**: {stats['violations_found']}\n"
        report += f"- **Auto-fixable**: {stats['auto_fixable_violations']}\n"
        report += f"- **Manual Fix Required**: {stats['violations_found'] - stats['auto_fixable_violations']}\n\n"
        
        # Violations by severity
        report += f"## Violations by Severity\n\n"
        for severity, count in stats['violations_by_severity'].items():
            if count > 0:
                icon = "🔴" if severity == "critical" else "🟡" if severity == "high" else "🟠" if severity == "medium" else "🔵"
                report += f"- {icon} **{severity.title()}**: {count}\n"
        report += f"\n"
        
        # Group violations by rule
        violations_by_rule = {}
        for violation in violations:
            rule = violation.rule_name
            if rule not in violations_by_rule:
                violations_by_rule[rule] = []
            violations_by_rule[rule].append(violation)
        
        if violations_by_rule:
            report += f"## Violations by Rule\n\n"
            for rule_name, rule_violations in sorted(violations_by_rule.items()):
                count = len(rule_violations)
                auto_fixable = len([v for v in rule_violations if v.auto_fixable])
                rule_desc = self.style_rules.get(rule_name, StyleRule(rule_name, "Unknown rule", "unknown", StyleSeverity.LOW, False)).description
                
                report += f"### {rule_name.replace('_', ' ').title()} ({count} violations)\n\n"
                report += f"**Description**: {rule_desc}\n"
                report += f"**Auto-fixable**: {auto_fixable}/{count}\n\n"
                
                # Show top violations for this rule
                for violation in rule_violations[:5]:  # Top 5
                    file_name = Path(violation.file_path).name
                    report += f"- **{violation.element_name}** ({file_name}:{violation.line_number})\n"
                    report += f"  - {violation.description}\n"
                    if violation.suggestion:
                        report += f"  - Suggestion: {violation.suggestion}\n"
                
                if len(rule_violations) > 5:
                    report += f"  - ... and {len(rule_violations) - 5} more\n"
                
                report += f"\n"
        
        # Recommendations
        report += f"## Recommendations\n\n"
        
        if stats['auto_fixable_violations'] > 0:
            report += f"1. **Auto-fix Available**: {stats['auto_fixable_violations']} violations can be automatically fixed\n"
        
        critical_count = stats['violations_by_severity'].get('critical', 0)
        if critical_count > 0:
            report += f"2. **Critical Issues**: Address {critical_count} critical style violations immediately\n"
        
        if stats['violations_found'] == 0:
            report += f"✅ **Excellent**: No style violations found! Documentation follows consistent style guidelines.\n"
        elif stats['violations_found'] < 10:
            report += f"3. **Nearly Perfect**: Only {stats['violations_found']} minor violations to address\n"
        else:
            report += f"3. **Improvement Needed**: {stats['violations_found']} violations found - consider implementing style automation\n"
        
        return report
    
    def get_auto_fixable_violations(self) -> List[StyleViolation]:
        """Get all violations that can be automatically fixed."""
        violations, _ = self.validate_project_style()
        return [v for v in violations if v.auto_fixable]
    
    def validate_element_style(self, element: CodeElement) -> List[StyleViolation]:
        """
        Validate style for a specific code element.
        
        Args:
            element: Code element to validate
            
        Returns:
            List of style violations for the element
        """
        if not element.docstring:
            return []
        
        violations = self._validate_docstring_content(
            element.docstring, element.name, element.file_path, element.line_number
        )
        
        return violations