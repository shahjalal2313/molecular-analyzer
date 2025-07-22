"""
Documentation Quality Assurance: Comprehensive documentation completeness and style validation.

This module provides automated documentation quality checking, including completeness
analysis, style validation, and quality scoring to maintain 99% documentation coverage.
"""

import ast
import re
import os
import json
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import logging

from .code_analyzer import CodeChangeAnalyzer, CodeElement
from .doc_template_engine import DocumentationTemplateEngine
# Import quality components as needed to avoid circular imports

logger = logging.getLogger(__name__)

@dataclass
class DocumentationIssue:
    """Represents a documentation quality issue."""
    issue_type: str  # 'missing', 'incomplete', 'style', 'quality'
    severity: str    # 'critical', 'high', 'medium', 'low'
    element_name: str
    file_path: str
    line_number: int
    description: str
    suggestion: str
    auto_fixable: bool

@dataclass
class CoverageMetrics:
    """Documentation coverage metrics."""
    total_elements: int
    documented_elements: int
    coverage_percentage: float
    missing_docstrings: int
    incomplete_docstrings: int
    quality_score: float
    issues_by_severity: Dict[str, int]

@dataclass
class StyleIssue:
    """Style consistency issue."""
    rule_name: str
    description: str
    location: str
    suggestion: str
    auto_fixable: bool

class DocumentationCompletenessChecker:
    """
    Comprehensive documentation completeness analysis system.
    
    Features:
    - Complete code element documentation coverage analysis
    - Missing docstring detection with severity assessment
    - Incomplete documentation identification
    - Parameter and return value documentation validation
    - Cross-reference completeness checking
    - Quality scoring with detailed metrics
    """
    
    def __init__(self, project_root: str):
        """Initialize the documentation completeness checker."""
        self.project_root = Path(project_root)
        self.code_analyzer = CodeChangeAnalyzer(str(project_root))
        self.template_engine = DocumentationTemplateEngine(str(project_root))
        
        # Completeness requirements
        self.completeness_rules = {
            'class_docstring_required': True,
            'function_docstring_required': True,
            'method_docstring_required': True,
            'module_docstring_required': True,
            'parameter_docs_required': True,
            'return_docs_required': True,
            'exception_docs_required': False,  # Optional but recommended
            'example_docs_required': False,    # Optional but recommended
            'minimum_docstring_length': 20,    # Characters
            'complexity_threshold_for_detailed_docs': 5
        }
        
        # Quality thresholds
        self.quality_thresholds = {
            'excellent': 0.9,
            'good': 0.7,
            'fair': 0.5,
            'poor': 0.3
        }
    
    def check_project_completeness(self) -> Tuple[CoverageMetrics, List[DocumentationIssue]]:
        """
        Check documentation completeness for the entire project.
        
        Returns:
            Tuple of coverage metrics and list of documentation issues
        """
        logger.info("Starting comprehensive project documentation completeness check...")
        
        all_elements = self.code_analyzer.analyze_project()
        all_issues = []
        
        total_elements = 0
        documented_elements = 0
        quality_scores = []
        issues_by_severity = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for file_path, elements in all_elements.items():
            # Check module-level documentation
            module_issues = self._check_module_documentation(file_path)
            all_issues.extend(module_issues)
            
            for issue in module_issues:
                issues_by_severity[issue.severity] += 1
            
            # Check each code element
            for element in elements:
                total_elements += 1
                
                element_issues = self._check_element_completeness(element)
                all_issues.extend(element_issues)
                
                for issue in element_issues:
                    issues_by_severity[issue.severity] += 1
                
                # Calculate quality score
                quality_score = self.template_engine.get_documentation_quality_score(element)
                quality_scores.append(quality_score)
                
                # Count as documented if has docstring or quality score > 0.3
                if element.docstring or quality_score > 0.3:
                    documented_elements += 1
        
        # Calculate overall metrics
        coverage_percentage = (documented_elements / total_elements * 100) if total_elements > 0 else 100
        average_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        missing_docstrings = len([issue for issue in all_issues if issue.issue_type == 'missing'])
        incomplete_docstrings = len([issue for issue in all_issues if issue.issue_type == 'incomplete'])
        
        coverage_metrics = CoverageMetrics(
            total_elements=total_elements,
            documented_elements=documented_elements,
            coverage_percentage=coverage_percentage,
            missing_docstrings=missing_docstrings,
            incomplete_docstrings=incomplete_docstrings,
            quality_score=average_quality,
            issues_by_severity=issues_by_severity
        )
        
        logger.info(f"Documentation completeness check completed: {coverage_percentage:.1f}% coverage")
        
        return coverage_metrics, all_issues
    
    def _check_module_documentation(self, file_path: str) -> List[DocumentationIssue]:
        """Check module-level documentation completeness."""
        issues = []
        
        if not self.completeness_rules['module_docstring_required']:
            return issues
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Check for module docstring
            has_module_docstring = False
            if (tree.body and isinstance(tree.body[0], ast.Expr) and 
                isinstance(tree.body[0].value, ast.Constant) and 
                isinstance(tree.body[0].value.value, str)):
                
                docstring = tree.body[0].value.value
                has_module_docstring = True
                
                # Check docstring quality
                if len(docstring.strip()) < self.completeness_rules['minimum_docstring_length']:
                    issues.append(DocumentationIssue(
                        issue_type='incomplete',
                        severity='medium',
                        element_name=f"Module {Path(file_path).name}",
                        file_path=file_path,
                        line_number=1,
                        description=f"Module docstring too short ({len(docstring)} chars)",
                        suggestion=f"Expand module docstring to at least {self.completeness_rules['minimum_docstring_length']} characters",
                        auto_fixable=False
                    ))
            
            if not has_module_docstring:
                issues.append(DocumentationIssue(
                    issue_type='missing',
                    severity='high',
                    element_name=f"Module {Path(file_path).name}",
                    file_path=file_path,
                    line_number=1,
                    description="Missing module docstring",
                    suggestion="Add module-level docstring describing the module's purpose",
                    auto_fixable=True
                ))
                
        except Exception as e:
            logger.error(f"Error checking module documentation for {file_path}: {e}")
        
        return issues
    
    def _check_element_completeness(self, element: CodeElement) -> List[DocumentationIssue]:
        """Check documentation completeness for a code element."""
        issues = []
        
        # Check if docstring is required for this element type
        docstring_required = self.completeness_rules.get(f"{element.type}_docstring_required", False)
        
        if not element.docstring:
            if docstring_required:
                severity = self._get_missing_docstring_severity(element)
                issues.append(DocumentationIssue(
                    issue_type='missing',
                    severity=severity,
                    element_name=element.name,
                    file_path=element.file_path,
                    line_number=element.line_number,
                    description=f"Missing {element.type} docstring",
                    suggestion=f"Add docstring to {element.type} '{element.name}'",
                    auto_fixable=True
                ))
        else:
            # Check docstring completeness
            docstring_issues = self._check_docstring_completeness(element)
            issues.extend(docstring_issues)
        
        return issues
    
    def _get_missing_docstring_severity(self, element: CodeElement) -> str:
        """Determine severity of missing docstring based on element characteristics."""
        if element.type == 'class':
            return 'critical'
        elif element.type == 'function':
            if element.name.startswith('_'):
                return 'medium'  # Private functions
            elif element.complexity_score > self.completeness_rules['complexity_threshold_for_detailed_docs']:
                return 'high'  # Complex functions
            else:
                return 'medium'
        elif element.type == 'method':
            if element.name.startswith('__'):
                return 'low'  # Magic methods
            elif element.name.startswith('_'):
                return 'low'  # Private methods
            else:
                return 'medium'
        else:
            return 'low'
    
    def _check_docstring_completeness(self, element: CodeElement) -> List[DocumentationIssue]:
        """Check completeness of existing docstring."""
        issues = []
        docstring = element.docstring.lower()
        
        # Check minimum length
        if len(element.docstring) < self.completeness_rules['minimum_docstring_length']:
            issues.append(DocumentationIssue(
                issue_type='incomplete',
                severity='medium',
                element_name=element.name,
                file_path=element.file_path,
                line_number=element.line_number,
                description=f"Docstring too short ({len(element.docstring)} chars)",
                suggestion=f"Expand docstring to at least {self.completeness_rules['minimum_docstring_length']} characters",
                auto_fixable=False
            ))
        
        # Check parameter documentation
        if element.parameters and self.completeness_rules['parameter_docs_required']:
            missing_params = []
            for param in element.parameters:
                if param not in ['self', 'cls'] and param.lower() not in docstring:
                    missing_params.append(param)
            
            if missing_params:
                issues.append(DocumentationIssue(
                    issue_type='incomplete',
                    severity='medium',
                    element_name=element.name,
                    file_path=element.file_path,
                    line_number=element.line_number,
                    description=f"Missing parameter documentation: {', '.join(missing_params)}",
                    suggestion=f"Document parameters: {', '.join(missing_params)}",
                    auto_fixable=True
                ))
        
        # Check return documentation
        if (element.return_type and self.completeness_rules['return_docs_required'] and
            'return' not in docstring):
            issues.append(DocumentationIssue(
                issue_type='incomplete',
                severity='medium',
                element_name=element.name,
                file_path=element.file_path,
                line_number=element.line_number,
                description="Missing return value documentation",
                suggestion="Add return value documentation to docstring",
                auto_fixable=True
            ))
        
        # Check for complex functions needing detailed documentation
        if (element.complexity_score > self.completeness_rules['complexity_threshold_for_detailed_docs'] and
            len(element.docstring) < 100):
            issues.append(DocumentationIssue(
                issue_type='incomplete',
                severity='high',
                element_name=element.name,
                file_path=element.file_path,
                line_number=element.line_number,
                description=f"Complex {element.type} needs detailed documentation (complexity: {element.complexity_score})",
                suggestion="Add detailed description, examples, and edge case documentation",
                auto_fixable=False
            ))
        
        return issues
    
    def get_coverage_by_file(self) -> Dict[str, float]:
        """Get documentation coverage percentage by file."""
        all_elements = self.code_analyzer.analyze_project()
        coverage_by_file = {}
        
        for file_path, elements in all_elements.items():
            if not elements:
                coverage_by_file[file_path] = 100.0
                continue
            
            documented = sum(1 for element in elements if element.docstring)
            coverage = (documented / len(elements)) * 100
            coverage_by_file[file_path] = coverage
        
        return coverage_by_file
    
    def get_coverage_by_type(self) -> Dict[str, float]:
        """Get documentation coverage by element type (class, function, etc.)."""
        all_elements = self.code_analyzer.analyze_project()
        type_counts = {}
        type_documented = {}
        
        for file_path, elements in all_elements.items():
            for element in elements:
                type_counts[element.type] = type_counts.get(element.type, 0) + 1
                if element.docstring:
                    type_documented[element.type] = type_documented.get(element.type, 0) + 1
        
        coverage_by_type = {}
        for element_type, total in type_counts.items():
            documented = type_documented.get(element_type, 0)
            coverage_by_type[element_type] = (documented / total) * 100
        
        return coverage_by_type
    
    def generate_completeness_report(self) -> str:
        """
        Generate a comprehensive documentation completeness report.
        
        Returns:
            Formatted markdown report
        """
        metrics, issues = self.check_project_completeness()
        coverage_by_file = self.get_coverage_by_file()
        coverage_by_type = self.get_coverage_by_type()
        
        report = f"# Documentation Completeness Report\n\n"
        report += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Overall metrics
        report += f"## Overall Coverage\n\n"
        report += f"- **Total Elements**: {metrics.total_elements}\n"
        report += f"- **Documented Elements**: {metrics.documented_elements}\n"
        report += f"- **Coverage Percentage**: {metrics.coverage_percentage:.1f}%\n"
        report += f"- **Quality Score**: {metrics.quality_score:.2f}/1.0\n\n"
        
        # Coverage status
        if metrics.coverage_percentage >= 99:
            status = "✅ EXCELLENT"
        elif metrics.coverage_percentage >= 90:
            status = "✅ GOOD"
        elif metrics.coverage_percentage >= 70:
            status = "⚠️ FAIR"
        else:
            status = "❌ POOR"
        
        report += f"**Status**: {status}\n\n"
        
        # Issues summary
        report += f"## Issues Summary\n\n"
        for severity, count in metrics.issues_by_severity.items():
            if count > 0:
                report += f"- **{severity.title()}**: {count}\n"
        report += f"\n"
        
        # Coverage by file
        if coverage_by_file:
            report += f"## Coverage by File\n\n"
            for file_path, coverage in sorted(coverage_by_file.items(), key=lambda x: x[1]):
                relative_path = Path(file_path).relative_to(self.project_root)
                status_icon = "✅" if coverage >= 90 else "⚠️" if coverage >= 70 else "❌"
                report += f"- {status_icon} **{relative_path}**: {coverage:.1f}%\n"
            report += f"\n"
        
        # Coverage by type
        if coverage_by_type:
            report += f"## Coverage by Element Type\n\n"
            for element_type, coverage in sorted(coverage_by_type.items(), key=lambda x: x[1]):
                status_icon = "✅" if coverage >= 90 else "⚠️" if coverage >= 70 else "❌"
                report += f"- {status_icon} **{element_type.title()}**: {coverage:.1f}%\n"
            report += f"\n"
        
        # Top priority issues
        critical_issues = [issue for issue in issues if issue.severity == 'critical']
        high_issues = [issue for issue in issues if issue.severity == 'high']
        
        if critical_issues or high_issues:
            report += f"## Priority Issues\n\n"
            
            if critical_issues:
                report += f"### Critical Issues\n\n"
                for issue in critical_issues[:10]:  # Top 10
                    report += f"- **{issue.element_name}** ({Path(issue.file_path).name}:{issue.line_number})\n"
                    report += f"  - {issue.description}\n"
                    report += f"  - Suggestion: {issue.suggestion}\n\n"
            
            if high_issues:
                report += f"### High Priority Issues\n\n"
                for issue in high_issues[:10]:  # Top 10
                    report += f"- **{issue.element_name}** ({Path(issue.file_path).name}:{issue.line_number})\n"
                    report += f"  - {issue.description}\n"
                    report += f"  - Suggestion: {issue.suggestion}\n\n"
        
        # Recommendations
        report += f"## Recommendations\n\n"
        
        if metrics.coverage_percentage < 99:
            target_additions = int((99 - metrics.coverage_percentage) / 100 * metrics.total_elements)
            report += f"1. **Increase Coverage**: Add documentation to {target_additions} more elements to reach 99% target\n"
        
        if metrics.issues_by_severity.get('critical', 0) > 0:
            report += f"2. **Fix Critical Issues**: Address {metrics.issues_by_severity['critical']} critical documentation issues immediately\n"
        
        if metrics.quality_score < 0.8:
            report += f"3. **Improve Quality**: Current quality score ({metrics.quality_score:.2f}) below target (0.8)\n"
        
        auto_fixable = len([issue for issue in issues if issue.auto_fixable])
        if auto_fixable > 0:
            report += f"4. **Auto-fixes Available**: {auto_fixable} issues can be automatically fixed\n"
        
        return report
    
    def get_auto_fixable_issues(self) -> List[DocumentationIssue]:
        """Get list of documentation issues that can be automatically fixed."""
        _, issues = self.check_project_completeness()
        return [issue for issue in issues if issue.auto_fixable]
    
    def suggest_documentation_improvements(self, file_path: str) -> List[str]:
        """
        Suggest specific documentation improvements for a file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            List of improvement suggestions
        """
        elements = self.code_analyzer.analyze_file(file_path)
        suggestions = []
        
        for element in elements:
            element_suggestions = self.code_analyzer.get_documentation_suggestions(element)
            suggestions.extend(element_suggestions)
        
        # Add file-specific suggestions
        _, issues = self.check_project_completeness()
        file_issues = [issue for issue in issues if issue.file_path == file_path]
        
        for issue in file_issues:
            suggestions.append(f"{issue.element_name}: {issue.suggestion}")
        
        return list(set(suggestions))  # Remove duplicates


class IntegratedDocumentationQualityAssurance:
    """
    Comprehensive documentation quality assurance system.
    
    Integrates completeness checking, style validation, and quality scoring
    to provide complete documentation quality management.
    """
    
    def __init__(self, project_root: str):
        """Initialize the integrated quality assurance system."""
        self.project_root = Path(project_root)
        self.completeness_checker = DocumentationCompletenessChecker(str(project_root))
        
        # Import here to avoid circular imports
        from .documentation_style_validator import DocumentationStyleValidator
        from .documentation_quality_scorer import DocumentationQualityScorer
        
        self.style_validator = DocumentationStyleValidator(str(project_root))
        self.quality_scorer = DocumentationQualityScorer(str(project_root))
        
        # Integration settings
        self.quality_thresholds = {
            'excellent': 0.9,
            'good': 0.8,
            'fair': 0.7,
            'poor': 0.6
        }
        
        # Auto-fix capabilities
        self.auto_fix_enabled = True
        self.auto_fix_types = ['missing_docstrings', 'style_violations', 'parameter_docs']
    
    def perform_comprehensive_qa(self) -> Dict[str, Any]:
        """
        Perform comprehensive documentation quality assurance.
        
        Returns:
            Complete QA results with all metrics and recommendations
        """
        logger.info("Starting comprehensive documentation quality assurance...")
        
        start_time = datetime.now()
        
        # Run all QA components
        coverage_metrics, completeness_issues = self.completeness_checker.check_project_completeness()
        style_violations, style_stats = self.style_validator.validate_project_style()
        quality_metrics = self.quality_scorer.assess_project_quality()
        
        # Generate integrated analysis
        integrated_results = {
            'timestamp': start_time.isoformat(),
            'overall_assessment': {
                'quality_grade': quality_metrics.quality_grade,
                'quality_score': quality_metrics.overall_score,
                'coverage_percentage': coverage_metrics.coverage_percentage,
                'total_violations': style_stats['violations_found'],
                'auto_fixable_issues': len(self.get_auto_fixable_issues())
            },
            'detailed_metrics': {
                'completeness': {
                    'coverage': coverage_metrics,
                    'issues': completeness_issues
                },
                'style': {
                    'violations': style_violations,
                    'statistics': style_stats
                },
                'quality': quality_metrics
            },
            'recommendations': self._generate_integrated_recommendations(
                coverage_metrics, completeness_issues, style_violations, quality_metrics
            ),
            'auto_fix_opportunities': self._identify_auto_fix_opportunities(
                completeness_issues, style_violations
            ),
            'qa_duration': (datetime.now() - start_time).total_seconds()
        }
        
        logger.info(f"QA completed in {integrated_results['qa_duration']:.2f}s - Grade: {quality_metrics.quality_grade}")
        
        return integrated_results
    
    def get_auto_fixable_issues(self) -> List[Dict[str, Any]]:
        """Get all issues that can be automatically fixed."""
        auto_fixable = []
        
        # Get auto-fixable completeness issues
        _, completeness_issues = self.completeness_checker.check_project_completeness()
        for issue in completeness_issues:
            if issue.auto_fixable:
                auto_fixable.append({
                    'type': 'completeness',
                    'category': issue.issue_type,
                    'element': issue.element_name,
                    'file': issue.file_path,
                    'line': issue.line_number,
                    'description': issue.description,
                    'fix_suggestion': issue.suggestion
                })
        
        # Get auto-fixable style violations
        style_violations, _ = self.style_validator.validate_project_style()
        for violation in style_violations:
            if violation.auto_fixable:
                auto_fixable.append({
                    'type': 'style',
                    'category': violation.rule_name,
                    'element': violation.element_name,
                    'file': violation.file_path,
                    'line': violation.line_number,
                    'description': violation.description,
                    'fix_suggestion': violation.suggestion
                })
        
        return auto_fixable
    
    def _generate_integrated_recommendations(self, coverage_metrics,
                                          completeness_issues: List,
                                          style_violations: List,
                                          quality_metrics) -> List[str]:
        """Generate integrated recommendations from all QA components."""
        recommendations = []
        
        # Priority 1: Critical issues
        critical_completeness = len([i for i in completeness_issues if i.severity == 'critical'])
        critical_style = len([v for v in style_violations if v.severity.value == 'critical'])
        
        if critical_completeness > 0 or critical_style > 0:
            recommendations.append(
                f"🚨 URGENT: Fix {critical_completeness + critical_style} critical documentation issues immediately"
            )
        
        # Priority 2: Coverage targets
        if coverage_metrics.coverage_percentage < 99:
            missing_elements = int((99 - coverage_metrics.coverage_percentage) / 100 * coverage_metrics.total_elements)
            recommendations.append(
                f"📝 Add documentation to {missing_elements} elements to reach 99% coverage target"
            )
        
        # Priority 3: Quality improvement
        if quality_metrics.overall_score < 0.9:
            target_improvement = 0.9 - quality_metrics.overall_score
            recommendations.append(
                f"🎯 Improve overall quality by {target_improvement:.2f} points to reach 'A' grade"
            )
        
        # Priority 4: Auto-fixes
        auto_fixable_count = len(self.get_auto_fixable_issues())
        if auto_fixable_count > 0:
            recommendations.append(
                f"🔧 Apply {auto_fixable_count} automatic fixes for immediate improvement"
            )
        
        # Priority 5: Style consistency
        if style_violations:
            style_issues = len(style_violations)
            recommendations.append(
                f"✨ Resolve {style_issues} style violations for consistency"
            )
        
        # Add dimension-specific recommendations
        weakest_dimensions = sorted(
            quality_metrics.dimension_scores.items(), 
            key=lambda x: x[1]
        )[:2]  # Top 2 weakest
        
        for dimension, score in weakest_dimensions:
            if score < 0.8:
                if dimension == 'completeness':
                    recommendations.append("📚 Focus on completing missing documentation sections")
                elif dimension == 'style':
                    recommendations.append("🎨 Improve documentation formatting and style consistency")
                elif dimension == 'clarity':
                    recommendations.append("💡 Enhance documentation clarity with better explanations")
                elif dimension == 'usability':
                    recommendations.append("🛠️ Add practical examples and usage guidance")
        
        return recommendations[:8]  # Top 8 recommendations
    
    def _identify_auto_fix_opportunities(self, completeness_issues: List,
                                       style_violations: List) -> Dict[str, List[str]]:
        """Identify specific auto-fix opportunities by category."""
        opportunities = {
            'missing_docstrings': [],
            'parameter_documentation': [],
            'style_formatting': [],
            'capitalization_punctuation': []
        }
        
        for issue in completeness_issues:
            if issue.auto_fixable:
                if issue.issue_type == 'missing':
                    opportunities['missing_docstrings'].append(
                        f"{issue.element_name} in {Path(issue.file_path).name}"
                    )
                elif 'parameter' in issue.description.lower():
                    opportunities['parameter_documentation'].append(
                        f"{issue.element_name} parameters in {Path(issue.file_path).name}"
                    )
        
        for violation in style_violations:
            if violation.auto_fixable:
                if violation.rule_name in ['docstring_capitalization', 'docstring_punctuation']:
                    opportunities['capitalization_punctuation'].append(
                        f"{violation.element_name} in {Path(violation.file_path).name}"
                    )
                else:
                    opportunities['style_formatting'].append(
                        f"{violation.element_name} in {Path(violation.file_path).name}"
                    )
        
        # Remove empty categories
        return {k: v for k, v in opportunities.items() if v}
    
    def generate_comprehensive_report(self) -> str:
        """
        Generate a comprehensive quality assurance report.
        
        Returns:
            Complete QA report in markdown format
        """
        qa_results = self.perform_comprehensive_qa()
        
        report = f"# 📊 Comprehensive Documentation Quality Assurance Report\n\n"
        report += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"**Analysis Duration**: {qa_results['qa_duration']:.2f} seconds\n\n"
        
        # Executive summary
        overall = qa_results['overall_assessment']
        report += f"## 🎯 Executive Summary\n\n"
        report += f"- **Overall Grade**: {overall['quality_grade']}\n"
        report += f"- **Quality Score**: {overall['quality_score']:.2f}/1.0\n"
        report += f"- **Documentation Coverage**: {overall['coverage_percentage']:.1f}%\n"
        report += f"- **Style Violations**: {overall['total_violations']}\n"
        report += f"- **Auto-fixable Issues**: {overall['auto_fixable_issues']}\n\n"
        
        # Quality status
        if overall['quality_score'] >= 0.95:
            status = "🌟 OUTSTANDING"
        elif overall['quality_score'] >= 0.9:
            status = "🎉 EXCELLENT"
        elif overall['quality_score'] >= 0.8:
            status = "✅ GOOD"
        elif overall['quality_score'] >= 0.7:
            status = "⚠️ FAIR"
        else:
            status = "🚨 NEEDS ATTENTION"
        
        report += f"**Quality Status**: {status}\n\n"
        
        # Quality dimensions
        quality_metrics = qa_results['detailed_metrics']['quality']
        report += f"## 📈 Quality Dimensions\n\n"
        for dimension, score in quality_metrics.dimension_scores.items():
            percentage = score * 100
            bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
            report += f"- **{dimension.replace('_', ' ').title()}**: {percentage:.1f}% {bar}\n"
        report += f"\n"
        
        # Key findings
        report += f"## 🔍 Key Findings\n\n"
        completeness = qa_results['detailed_metrics']['completeness']
        style = qa_results['detailed_metrics']['style']
        
        # Coverage analysis
        coverage = completeness['coverage']
        report += f"### Documentation Coverage\n"
        report += f"- **Total Elements**: {coverage.total_elements}\n"
        report += f"- **Documented Elements**: {coverage.documented_elements}\n"
        report += f"- **Missing Documentation**: {coverage.missing_docstrings}\n"
        report += f"- **Incomplete Documentation**: {coverage.incomplete_docstrings}\n\n"
        
        # Style analysis
        style_stats = style['statistics']
        report += f"### Style Consistency\n"
        report += f"- **Files Checked**: {style_stats['files_checked']}\n"
        report += f"- **Total Violations**: {style_stats['violations_found']}\n"
        report += f"- **Auto-fixable**: {style_stats['auto_fixable_violations']}\n"
        
        # Violations by severity
        for severity, count in style_stats['violations_by_severity'].items():
            if count > 0:
                icon = {"critical": "🔴", "high": "🟡", "medium": "🟠", "low": "🔵", "info": "⚪"}.get(severity, "⚪")
                report += f"- {icon} **{severity.title()}**: {count}\n"
        report += f"\n"
        
        # Priority recommendations
        recommendations = qa_results['recommendations']
        if recommendations:
            report += f"## 🎯 Priority Recommendations\n\n"
            for i, rec in enumerate(recommendations, 1):
                report += f"{i}. {rec}\n"
            report += f"\n"
        
        # Auto-fix opportunities
        auto_fix = qa_results['auto_fix_opportunities']
        if auto_fix:
            report += f"## 🔧 Auto-fix Opportunities\n\n"
            for category, items in auto_fix.items():
                if items:
                    report += f"### {category.replace('_', ' ').title()}\n"
                    for item in items[:5]:  # Top 5 per category
                        report += f"- {item}\n"
                    if len(items) > 5:
                        report += f"- ... and {len(items) - 5} more\n"
                    report += f"\n"
        
        # Next steps
        report += f"## 🚀 Next Steps\n\n"
        
        if overall['quality_score'] >= 0.95:
            report += f"✨ **Maintain Excellence**: Documentation quality is outstanding! Focus on keeping it current.\n"
        elif overall['quality_score'] >= 0.9:
            report += f"🎯 **Polish and Perfect**: Close to excellence - address remaining minor issues.\n"
        elif overall['quality_score'] >= 0.8:
            report += f"📈 **Systematic Improvement**: Good foundation - implement recommendations systematically.\n"
        else:
            report += f"🔥 **Immediate Action**: Focus on critical issues and auto-fixes for quick wins.\n"
        
        # Implementation timeline
        if overall['auto_fixable_issues'] > 0:
            report += f"\n### Suggested Timeline\n"
            report += f"1. **Week 1**: Apply {overall['auto_fixable_issues']} auto-fixes\n"
            
            missing_docs = coverage.missing_docstrings
            if missing_docs > 0:
                report += f"2. **Week 2**: Add {min(missing_docs, 20)} priority docstrings\n"
            
            if overall['total_violations'] > overall['auto_fixable_issues']:
                manual_fixes = overall['total_violations'] - overall['auto_fixable_issues']
                report += f"3. **Week 3**: Address {min(manual_fixes, 15)} manual style issues\n"
            
            if overall['quality_score'] < 0.9:
                report += f"4. **Week 4**: Quality review and enhancement\n"
        
        return report
    
    def get_qa_dashboard_data(self) -> Dict[str, Any]:
        """Get summary data for a QA dashboard."""
        qa_results = self.perform_comprehensive_qa()
        
        return {
            'overall_grade': qa_results['overall_assessment']['quality_grade'],
            'quality_score': qa_results['overall_assessment']['quality_score'],
            'coverage_percentage': qa_results['overall_assessment']['coverage_percentage'],
            'total_issues': qa_results['overall_assessment']['total_violations'],
            'auto_fixable': qa_results['overall_assessment']['auto_fixable_issues'],
            'dimension_scores': qa_results['detailed_metrics']['quality'].dimension_scores,
            'top_recommendations': qa_results['recommendations'][:3],
            'quick_wins': list(qa_results['auto_fix_opportunities'].keys())
        }