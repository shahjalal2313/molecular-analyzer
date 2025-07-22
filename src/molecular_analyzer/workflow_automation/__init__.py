"""
Workflow Automation Module

Enhanced TodoWrite integration with intelligent task prioritization,
dependency mapping, effort estimation, and automated documentation generation
while maintaining backward compatibility.
"""

from .enhanced_todo_system import EnhancedTodoSystem
from .priority_optimizer import DynamicPriorityOptimizer
from .dependency_mapper import TaskDependencyMapper
from .effort_estimator import EffortEstimationEngine
from .code_analyzer import CodeChangeAnalyzer, CodeElement, CodeChange
from .doc_template_engine import DocumentationTemplateEngine
from .auto_doc_generator import AutoDocGenerator, CrossReferenceManager
from .documentation_integration import DocumentationWorkflowIntegrator
from .doc_quality_assurance import DocumentationCompletenessChecker, IntegratedDocumentationQualityAssurance

__all__ = [
    'EnhancedTodoSystem',
    'DynamicPriorityOptimizer', 
    'TaskDependencyMapper',
    'EffortEstimationEngine',
    'CodeChangeAnalyzer',
    'CodeElement',
    'CodeChange',
    'DocumentationTemplateEngine',
    'AutoDocGenerator',
    'CrossReferenceManager',
    'DocumentationWorkflowIntegrator',
    'DocumentationCompletenessChecker',
    'IntegratedDocumentationQualityAssurance'
]