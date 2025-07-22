"""
Documentation Quality Scorer: Advanced quality assessment algorithms for documentation.

This module provides sophisticated quality scoring algorithms that combine completeness,
style, accuracy, and usability metrics to provide comprehensive documentation quality assessment.
"""

import re
import math
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

from .code_analyzer import CodeElement
from .documentation_style_validator import DocumentationStyleValidator, StyleViolation

logger = logging.getLogger(__name__)

class QualityDimension(Enum):
    """Different dimensions of documentation quality."""
    COMPLETENESS = "completeness"
    STYLE = "style"
    CLARITY = "clarity"
    ACCURACY = "accuracy"
    USABILITY = "usability"
    MAINTAINABILITY = "maintainability"

@dataclass
class QualityMetrics:
    """Comprehensive quality metrics for documentation."""
    overall_score: float  # 0.0 to 1.0
    dimension_scores: Dict[str, float]
    element_scores: Dict[str, float]
    file_scores: Dict[str, float]
    improvement_suggestions: List[str]
    quality_grade: str  # A+, A, B+, B, C+, C, D, F
    
@dataclass
class QualityFactor:
    """Individual quality factor with weight and score."""
    name: str
    score: float  # 0.0 to 1.0
    weight: float  # Importance weight
    description: str
    impact: str  # 'high', 'medium', 'low'

class DocumentationQualityScorer:
    """
    Advanced documentation quality assessment system.
    
    Combines multiple quality dimensions:
    - Completeness: Coverage and thoroughness
    - Style: Consistency and formatting
    - Clarity: Readability and comprehension
    - Accuracy: Correctness and currency
    - Usability: Helpfulness and practicality
    - Maintainability: Sustainability and evolution
    """
    
    def __init__(self, project_root: str):
        """Initialize the quality scorer."""
        self.project_root = project_root
        # Import here to avoid circular imports
        from .doc_quality_assurance import DocumentationCompletenessChecker
        self.completeness_checker = DocumentationCompletenessChecker(project_root)
        self.style_validator = DocumentationStyleValidator(project_root)
        
        # Quality dimension weights (should sum to 1.0)
        self.dimension_weights = {
            QualityDimension.COMPLETENESS.value: 0.25,
            QualityDimension.STYLE.value: 0.15,
            QualityDimension.CLARITY.value: 0.25,
            QualityDimension.ACCURACY.value: 0.15,
            QualityDimension.USABILITY.value: 0.15,
            QualityDimension.MAINTAINABILITY.value: 0.05
        }
        
        # Quality factor configurations
        self.quality_factors = self._initialize_quality_factors()
        
        # Grade thresholds
        self.grade_thresholds = {
            'A+': 0.95, 'A': 0.90, 'A-': 0.85,
            'B+': 0.80, 'B': 0.75, 'B-': 0.70,
            'C+': 0.65, 'C': 0.60, 'C-': 0.55,
            'D+': 0.50, 'D': 0.40, 'F': 0.0
        }
    
    def _initialize_quality_factors(self) -> Dict[str, QualityFactor]:
        """Initialize all quality assessment factors."""
        factors = {}
        
        # Completeness factors
        factors['docstring_coverage'] = QualityFactor(
            name='docstring_coverage',
            score=0.0, weight=0.4,
            description='Percentage of code elements with docstrings',
            impact='high'
        )
        
        factors['parameter_documentation'] = QualityFactor(
            name='parameter_documentation',
            score=0.0, weight=0.3,
            description='Completeness of parameter documentation',
            impact='high'
        )
        
        factors['return_documentation'] = QualityFactor(
            name='return_documentation',
            score=0.0, weight=0.2,
            description='Quality of return value documentation',
            impact='medium'
        )
        
        factors['example_coverage'] = QualityFactor(
            name='example_coverage',
            score=0.0, weight=0.1,
            description='Presence of usage examples',
            impact='medium'
        )
        
        # Style factors
        factors['formatting_consistency'] = QualityFactor(
            name='formatting_consistency',
            score=0.0, weight=0.4,
            description='Consistent formatting and structure',
            impact='medium'
        )
        
        factors['style_compliance'] = QualityFactor(
            name='style_compliance',
            score=0.0, weight=0.6,
            description='Adherence to style guidelines',
            impact='medium'
        )
        
        # Clarity factors
        factors['readability'] = QualityFactor(
            name='readability',
            score=0.0, weight=0.4,
            description='Text readability and comprehension',
            impact='high'
        )
        
        factors['structure_clarity'] = QualityFactor(
            name='structure_clarity',
            score=0.0, weight=0.3,
            description='Logical organization and flow',
            impact='high'
        )
        
        factors['terminology_consistency'] = QualityFactor(
            name='terminology_consistency',
            score=0.0, weight=0.3,
            description='Consistent technical terminology',
            impact='medium'
        )
        
        # Accuracy factors
        factors['cross_reference_accuracy'] = QualityFactor(
            name='cross_reference_accuracy',
            score=0.0, weight=0.5,
            description='Accuracy of cross-references and links',
            impact='high'
        )
        
        factors['code_documentation_sync'] = QualityFactor(
            name='code_documentation_sync',
            score=0.0, weight=0.5,
            description='Synchronization between code and documentation',
            impact='high'
        )
        
        # Usability factors
        factors['practical_examples'] = QualityFactor(
            name='practical_examples',
            score=0.0, weight=0.5,
            description='Practical, working examples',
            impact='high'
        )
        
        factors['user_guidance'] = QualityFactor(
            name='user_guidance',
            score=0.0, weight=0.5,
            description='Clear guidance for users',
            impact='high'
        )
        
        # Maintainability factors
        factors['update_frequency'] = QualityFactor(
            name='update_frequency',
            score=0.0, weight=0.6,
            description='How recently documentation was updated',
            impact='low'
        )
        
        factors['automation_coverage'] = QualityFactor(
            name='automation_coverage',
            score=0.0, weight=0.4,
            description='Level of automated documentation maintenance',
            impact='medium'
        )
        
        return factors
    
    def assess_project_quality(self) -> QualityMetrics:
        """
        Perform comprehensive quality assessment for the entire project.
        
        Returns:
            Complete quality metrics with scores and recommendations
        """
        logger.info("Starting comprehensive documentation quality assessment...")
        
        # Get base metrics
        coverage_metrics, completeness_issues = self.completeness_checker.check_project_completeness()
        style_violations, style_stats = self.style_validator.validate_project_style()
        
        # Calculate dimension scores
        dimension_scores = {}
        
        # Completeness dimension
        dimension_scores[QualityDimension.COMPLETENESS.value] = self._calculate_completeness_score(
            coverage_metrics, completeness_issues
        )
        
        # Style dimension
        dimension_scores[QualityDimension.STYLE.value] = self._calculate_style_score(
            style_violations, style_stats
        )
        
        # Clarity dimension
        dimension_scores[QualityDimension.CLARITY.value] = self._calculate_clarity_score(
            coverage_metrics, completeness_issues
        )
        
        # Accuracy dimension
        dimension_scores[QualityDimension.ACCURACY.value] = self._calculate_accuracy_score(
            completeness_issues
        )
        
        # Usability dimension
        dimension_scores[QualityDimension.USABILITY.value] = self._calculate_usability_score(
            completeness_issues
        )
        
        # Maintainability dimension
        dimension_scores[QualityDimension.MAINTAINABILITY.value] = self._calculate_maintainability_score()
        
        # Calculate overall score
        overall_score = sum(
            score * self.dimension_weights[dimension]
            for dimension, score in dimension_scores.items()
        )
        
        # Calculate element and file scores
        element_scores = self._calculate_element_scores()
        file_scores = self._calculate_file_scores()
        
        # Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(
            dimension_scores, completeness_issues, style_violations
        )
        
        # Determine quality grade
        quality_grade = self._calculate_quality_grade(overall_score)
        
        quality_metrics = QualityMetrics(
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            element_scores=element_scores,
            file_scores=file_scores,
            improvement_suggestions=improvement_suggestions,
            quality_grade=quality_grade
        )
        
        logger.info(f"Quality assessment completed: {quality_grade} ({overall_score:.2f})")
        
        return quality_metrics
    
    def _calculate_completeness_score(self, metrics, issues: List) -> float:
        """Calculate completeness dimension score."""
        # Base score from coverage percentage
        coverage_score = metrics.coverage_percentage / 100.0
        
        # Adjust for issue severity
        severity_penalty = 0.0
        total_elements = metrics.total_elements
        
        if total_elements > 0:
            critical_issues = len([i for i in issues if i.severity == 'critical'])
            high_issues = len([i for i in issues if i.severity == 'high'])
            medium_issues = len([i for i in issues if i.severity == 'medium'])
            
            severity_penalty = (
                (critical_issues * 0.1) +
                (high_issues * 0.05) +
                (medium_issues * 0.02)
            ) / total_elements
        
        # Parameter and return documentation bonus
        param_bonus = 0.0
        return_bonus = 0.0
        
        # This would require additional analysis to determine parameter/return coverage
        # For now, use quality score as proxy
        if metrics.quality_score > 0.7:
            param_bonus = 0.05
            return_bonus = 0.05
        
        completeness_score = max(0.0, min(1.0, 
            coverage_score - severity_penalty + param_bonus + return_bonus
        ))
        
        return completeness_score
    
    def _calculate_style_score(self, violations: List, 
                             stats: Dict[str, Any]) -> float:
        """Calculate style dimension score."""
        if stats['files_checked'] == 0:
            return 1.0
        
        # Base score starts at 1.0, reduce for violations
        base_score = 1.0
        total_violations = stats['violations_found']
        
        if total_violations == 0:
            return 1.0
        
        # Calculate penalty based on violation severity
        severity_penalties = {
            'critical': 0.05,
            'high': 0.03,
            'medium': 0.02,
            'low': 0.01,
            'info': 0.005
        }
        
        total_penalty = 0.0
        for violation in violations:
            penalty = severity_penalties.get(violation.severity.value, 0.01)
            total_penalty += penalty
        
        # Normalize penalty by number of files
        normalized_penalty = total_penalty / max(1, stats['files_checked'])
        
        style_score = max(0.0, base_score - normalized_penalty)
        
        return style_score
    
    def _calculate_clarity_score(self, metrics, issues: List) -> float:
        """Calculate clarity dimension score."""
        # Base score from quality metrics
        base_score = metrics.quality_score
        
        # Adjust for clarity-specific factors
        clarity_issues = [i for i in issues if 'unclear' in i.description.lower() or 
                         'confusing' in i.description.lower()]
        
        clarity_penalty = len(clarity_issues) * 0.02
        
        # Length and detail bonus
        detail_bonus = 0.0
        if metrics.quality_score > 0.6:
            detail_bonus = 0.1
        
        clarity_score = max(0.0, min(1.0, base_score - clarity_penalty + detail_bonus))
        
        return clarity_score
    
    def _calculate_accuracy_score(self, issues: List) -> float:
        """Calculate accuracy dimension score."""
        # Start with high accuracy assumption
        base_score = 0.9
        
        # Penalize for accuracy-related issues
        accuracy_issues = [i for i in issues if 'outdated' in i.description.lower() or
                          'incorrect' in i.description.lower() or
                          'mismatch' in i.description.lower()]
        
        accuracy_penalty = len(accuracy_issues) * 0.05
        
        accuracy_score = max(0.0, base_score - accuracy_penalty)
        
        return accuracy_score
    
    def _calculate_usability_score(self, issues: List) -> float:
        """Calculate usability dimension score."""
        # Base score for usability
        base_score = 0.7
        
        # Look for example-related issues
        example_issues = [i for i in issues if 'example' in i.description.lower()]
        
        # Bonus for having examples
        if not example_issues:
            example_bonus = 0.2
        else:
            example_bonus = max(0.0, 0.2 - (len(example_issues) * 0.05))
        
        usability_score = min(1.0, base_score + example_bonus)
        
        return usability_score
    
    def _calculate_maintainability_score(self) -> float:
        """Calculate maintainability dimension score."""
        # Since we're implementing automated documentation, give high score
        automation_score = 0.9
        
        # This could be enhanced with actual update frequency analysis
        update_score = 0.8
        
        maintainability_score = (automation_score + update_score) / 2
        
        return maintainability_score
    
    def _calculate_element_scores(self) -> Dict[str, float]:
        """Calculate quality scores for individual elements."""
        element_scores = {}
        
        # Get all elements from code analyzer
        all_elements = self.completeness_checker.code_analyzer.analyze_project()
        
        for file_path, elements in all_elements.items():
            for element in elements:
                element_key = f"{file_path}::{element.name}"
                element_score = self.completeness_checker.template_engine.get_documentation_quality_score(element)
                element_scores[element_key] = element_score
        
        return element_scores
    
    def _calculate_file_scores(self) -> Dict[str, float]:
        """Calculate quality scores for individual files."""
        file_scores = {}
        coverage_by_file = self.completeness_checker.get_coverage_by_file()
        
        for file_path, coverage in coverage_by_file.items():
            # Base score from coverage
            base_score = coverage / 100.0
            
            # Adjust with element quality scores
            all_elements = self.completeness_checker.code_analyzer.analyze_project()
            if file_path in all_elements:
                elements = all_elements[file_path]
                if elements:
                    element_quality_scores = [
                        self.completeness_checker.template_engine.get_documentation_quality_score(elem)
                        for elem in elements
                    ]
                    avg_element_quality = sum(element_quality_scores) / len(element_quality_scores)
                    
                    # Combine coverage and quality
                    file_score = (base_score + avg_element_quality) / 2
                else:
                    file_score = base_score
            else:
                file_score = base_score
            
            file_scores[file_path] = file_score
        
        return file_scores
    
    def _generate_improvement_suggestions(self, dimension_scores: Dict[str, float],
                                        completeness_issues: List,
                                        style_violations: List) -> List[str]:
        """Generate prioritized improvement suggestions."""
        suggestions = []
        
        # Identify weakest dimensions
        sorted_dimensions = sorted(dimension_scores.items(), key=lambda x: x[1])
        
        # Suggestions for each dimension
        for dimension, score in sorted_dimensions:
            if score < 0.8:
                if dimension == QualityDimension.COMPLETENESS.value:
                    missing_count = len([i for i in completeness_issues if i.issue_type == 'missing'])
                    if missing_count > 0:
                        suggestions.append(f"Add {missing_count} missing docstrings to improve completeness")
                
                elif dimension == QualityDimension.STYLE.value:
                    auto_fixable = len([v for v in style_violations if v.auto_fixable])
                    if auto_fixable > 0:
                        suggestions.append(f"Auto-fix {auto_fixable} style violations for consistency")
                
                elif dimension == QualityDimension.CLARITY.value:
                    suggestions.append("Expand brief docstrings with more detailed explanations")
                
                elif dimension == QualityDimension.ACCURACY.value:
                    suggestions.append("Review and update documentation to match current code")
                
                elif dimension == QualityDimension.USABILITY.value:
                    suggestions.append("Add practical examples and usage guidance")
                
                elif dimension == QualityDimension.MAINTAINABILITY.value:
                    suggestions.append("Implement automated documentation maintenance workflows")
        
        # Priority suggestions based on issues
        critical_issues = [i for i in completeness_issues if i.severity == 'critical']
        if critical_issues:
            suggestions.insert(0, f"URGENT: Fix {len(critical_issues)} critical documentation issues")
        
        return suggestions[:10]  # Top 10 suggestions
    
    def _calculate_quality_grade(self, score: float) -> str:
        """Convert quality score to letter grade."""
        for grade, threshold in self.grade_thresholds.items():
            if score >= threshold:
                return grade
        return 'F'
    
    def generate_quality_report(self) -> str:
        """
        Generate a comprehensive quality assessment report.
        
        Returns:
            Formatted markdown report
        """
        metrics = self.assess_project_quality()
        
        report = f"# Documentation Quality Assessment Report\n\n"
        report += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"**Overall Grade**: {metrics.quality_grade}\n"
        report += f"**Overall Score**: {metrics.overall_score:.2f}/1.0\n\n"
        
        # Quality status
        if metrics.overall_score >= 0.9:
            status = "🌟 EXCELLENT"
        elif metrics.overall_score >= 0.8:
            status = "✅ GOOD"
        elif metrics.overall_score >= 0.7:
            status = "⚠️ FAIR"
        else:
            status = "❌ NEEDS IMPROVEMENT"
        
        report += f"**Quality Status**: {status}\n\n"
        
        # Dimension scores
        report += f"## Quality Dimensions\n\n"
        for dimension, score in metrics.dimension_scores.items():
            percentage = score * 100
            bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
            report += f"- **{dimension.replace('_', ' ').title()}**: {percentage:.1f}% {bar}\n"
        report += f"\n"
        
        # Top performing files
        if metrics.file_scores:
            sorted_files = sorted(metrics.file_scores.items(), key=lambda x: x[1], reverse=True)
            report += f"## Top Performing Files\n\n"
            for i, (file_path, score) in enumerate(sorted_files[:5], 1):
                from pathlib import Path
                file_name = Path(file_path).name
                report += f"{i}. **{file_name}**: {score:.2f}\n"
            report += f"\n"
        
        # Improvement opportunities
        if metrics.improvement_suggestions:
            report += f"## Priority Improvements\n\n"
            for i, suggestion in enumerate(metrics.improvement_suggestions, 1):
                report += f"{i}. {suggestion}\n"
            report += f"\n"
        
        # Quality factor analysis
        report += f"## Quality Factor Analysis\n\n"
        
        # Group factors by impact
        high_impact = [f for f in self.quality_factors.values() if f.impact == 'high']
        medium_impact = [f for f in self.quality_factors.values() if f.impact == 'medium']
        
        if high_impact:
            report += f"### High Impact Factors\n\n"
            for factor in high_impact:
                report += f"- **{factor.name.replace('_', ' ').title()}**: {factor.description}\n"
            report += f"\n"
        
        # Recommendations
        report += f"## Recommendations\n\n"
        
        if metrics.overall_score >= 0.95:
            report += f"🎉 **Outstanding**: Documentation quality is exceptional!\n"
        elif metrics.overall_score >= 0.8:
            report += f"💪 **Strong**: Good documentation quality with room for polish\n"
        elif metrics.overall_score >= 0.6:
            report += f"📈 **Improving**: Focus on completeness and clarity improvements\n"
        else:
            report += f"🚨 **Action Required**: Significant documentation improvements needed\n"
        
        return report
    
    def get_quality_trends(self) -> Dict[str, Any]:
        """Get quality trends and projections (placeholder for future enhancement)."""
        return {
            'current_score': self.assess_project_quality().overall_score,
            'trend': 'improving',  # This would be calculated from historical data
            'projection': 'excellent',  # Based on current improvements
            'time_to_target': '1 week'  # Estimated time to reach target quality
        }