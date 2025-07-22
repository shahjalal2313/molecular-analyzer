"""
Documentation Integration: Connects auto-documentation with session management.

This module integrates the AutoDocGenerator with the existing session management
system to provide real-time documentation updates and seamless workflow integration.
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import logging

from .auto_doc_generator import AutoDocGenerator
from .enhanced_todo_system import EnhancedTodoSystem

logger = logging.getLogger(__name__)

class DocumentationWorkflowIntegrator:
    """
    Integrates automated documentation generation with the existing workflow automation system.
    
    Features:
    - Real-time documentation updates during development sessions
    - Integration with TodoWrite system for documentation tasks
    - Session startup documentation health checks
    - Automated documentation maintenance workflows
    """
    
    def __init__(self, project_root: str):
        """Initialize the documentation workflow integrator."""
        self.project_root = Path(project_root)
        self.auto_doc_generator = AutoDocGenerator(str(project_root))
        self.enhanced_todo_system = None
        
        # Try to initialize enhanced todo system if available
        try:
            self.enhanced_todo_system = EnhancedTodoSystem(str(project_root))
        except Exception as e:
            logger.warning(f"Enhanced todo system not available: {e}")
        
        # Integration state
        self.documentation_session_data: Dict[str, Any] = {}
        self.last_documentation_check = 0
        self.documentation_tasks_created = []
    
    def initialize_documentation_session(self) -> Dict[str, Any]:
        """
        Initialize documentation checking for the current session.
        
        Returns:
            Dictionary with documentation session initialization results
        """
        logger.info("Initializing documentation session...")
        
        start_time = time.time()
        
        # Perform initial documentation analysis
        analysis_result = self.auto_doc_generator.analyze_and_generate_docs()
        
        # Get documentation suggestions
        suggestions = self.auto_doc_generator.get_documentation_suggestions()
        
        # Generate coverage report
        coverage_report = self.auto_doc_generator.generate_coverage_report()
        
        # Calculate session metrics
        session_data = {
            'session_start_time': datetime.now().isoformat(),
            'initialization_time': time.time() - start_time,
            'documentation_coverage': analysis_result.get('documentation_coverage', 0),
            'total_elements': analysis_result.get('total_elements_found', 0),
            'documented_elements': analysis_result.get('documented_elements', 0),
            'quality_score': analysis_result.get('average_quality_score', 0),
            'suggestions_count': len(suggestions),
            'high_priority_suggestions': len([s for s in suggestions if s['priority'] == 'high']),
            'broken_references': len(analysis_result.get('broken_references', [])),
            'generated_docs_count': analysis_result.get('generated_documentation_files', 0),
            'suggestions': suggestions[:10],  # Top 10 suggestions
            'coverage_report': coverage_report
        }
        
        self.documentation_session_data = session_data
        self.last_documentation_check = time.time()
        
        # Create documentation tasks if using enhanced todo system
        if self.enhanced_todo_system:
            self._create_documentation_todos(suggestions[:5])  # Top 5 suggestions as todos
        
        # Save session data
        self._save_documentation_session_data()
        
        logger.info(f"Documentation session initialized in {session_data['initialization_time']:.2f}s")
        logger.info(f"Coverage: {session_data['documentation_coverage']:.1f}%, Quality: {session_data['quality_score']:.2f}")
        
        return session_data
    
    def check_documentation_health(self) -> Dict[str, Any]:
        """
        Perform a quick documentation health check.
        
        Returns:
            Dictionary with health check results
        """
        health_data = {
            'check_time': datetime.now().isoformat(),
            'coverage_status': 'unknown',
            'quality_status': 'unknown',
            'broken_references_status': 'unknown',
            'overall_health': 'unknown',
            'recommendations': []
        }
        
        if not self.documentation_session_data:
            health_data['recommendations'].append("Run full documentation analysis first")
            return health_data
        
        # Check coverage status
        coverage = self.documentation_session_data.get('documentation_coverage', 0)
        if coverage >= 99:
            health_data['coverage_status'] = 'excellent'
        elif coverage >= 90:
            health_data['coverage_status'] = 'good'
        elif coverage >= 70:
            health_data['coverage_status'] = 'fair'
        else:
            health_data['coverage_status'] = 'poor'
            health_data['recommendations'].append(f"Documentation coverage is {coverage:.1f}% - aim for >90%")
        
        # Check quality status
        quality = self.documentation_session_data.get('quality_score', 0)
        if quality >= 0.8:
            health_data['quality_status'] = 'excellent'
        elif quality >= 0.6:
            health_data['quality_status'] = 'good'
        elif quality >= 0.4:
            health_data['quality_status'] = 'fair'
        else:
            health_data['quality_status'] = 'poor'
            health_data['recommendations'].append(f"Documentation quality is {quality:.2f} - aim for >0.8")
        
        # Check broken references
        broken_refs = self.documentation_session_data.get('broken_references', 0)
        if broken_refs == 0:
            health_data['broken_references_status'] = 'excellent'
        elif broken_refs <= 2:
            health_data['broken_references_status'] = 'good'
        elif broken_refs <= 5:
            health_data['broken_references_status'] = 'fair'
        else:
            health_data['broken_references_status'] = 'poor'
            health_data['recommendations'].append(f"{broken_refs} broken references found - fix immediately")
        
        # Overall health assessment
        status_scores = {
            'excellent': 4,
            'good': 3,
            'fair': 2,
            'poor': 1,
            'unknown': 0
        }
        
        avg_score = (
            status_scores[health_data['coverage_status']] +
            status_scores[health_data['quality_status']] +
            status_scores[health_data['broken_references_status']]
        ) / 3
        
        if avg_score >= 3.5:
            health_data['overall_health'] = 'excellent'
        elif avg_score >= 2.5:
            health_data['overall_health'] = 'good'
        elif avg_score >= 1.5:
            health_data['overall_health'] = 'fair'
        else:
            health_data['overall_health'] = 'poor'
            health_data['recommendations'].append("Documentation needs immediate attention")
        
        return health_data
    
    def monitor_file_changes(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Monitor a specific file for changes and update documentation if needed.
        
        Args:
            file_path: Path to the file to monitor
            
        Returns:
            Dictionary with change detection results, or None if no changes
        """
        if not os.path.exists(file_path) or not file_path.endswith('.py'):
            return None
        
        # Create backup for comparison
        backup_path = f"{file_path}.doc_backup"
        
        # If backup doesn't exist, create it and return (first time monitoring)
        if not os.path.exists(backup_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Created documentation backup for {file_path}")
                return None
            except Exception as e:
                logger.error(f"Error creating backup for {file_path}: {e}")
                return None
        
        # Detect changes
        try:
            change_result = self.auto_doc_generator.detect_and_document_changes(
                file_path, backup_path
            )
            
            if change_result['changes_detected'] > 0:
                # Update backup
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Create documentation update todos if using enhanced todo system
                if self.enhanced_todo_system and change_result.get('impact_analysis'):
                    self._create_change_documentation_todos(change_result)
                
                logger.info(f"Detected {change_result['changes_detected']} changes in {file_path}")
                return change_result
            
        except Exception as e:
            logger.error(f"Error monitoring changes in {file_path}: {e}")
        
        return None
    
    def _create_documentation_todos(self, suggestions: List[Dict[str, str]]):
        """Create TodoWrite tasks for documentation suggestions."""
        if not self.enhanced_todo_system:
            return
        
        for suggestion in suggestions:
            todo_content = f"Documentation: {suggestion['suggestion']} ({suggestion['element']} in {Path(suggestion['file']).name})"
            
            priority_mapping = {
                'high': 'high',
                'medium': 'medium',
                'low': 'low'
            }
            
            try:
                # This would integrate with the actual TodoWrite system
                todo_data = {
                    'content': todo_content,
                    'priority': priority_mapping.get(suggestion['priority'], 'medium'),
                    'category': 'documentation',
                    'auto_generated': True,
                    'source_file': suggestion['file'],
                    'source_line': suggestion.get('line_number', 1)
                }
                
                self.documentation_tasks_created.append(todo_data)
                logger.info(f"Created documentation todo: {todo_content}")
                
            except Exception as e:
                logger.error(f"Error creating documentation todo: {e}")
    
    def _create_change_documentation_todos(self, change_result: Dict[str, Any]):
        """Create TodoWrite tasks for documentation updates after code changes."""
        if not self.enhanced_todo_system:
            return
        
        impact_analysis = change_result.get('impact_analysis', {})
        
        for element_name, impact in impact_analysis.items():
            if impact.get('documentation_updates_needed'):
                todo_content = f"Update documentation for changed {element_name} (affects {len(impact['documentation_updates_needed'])} docs)"
                
                todo_data = {
                    'content': todo_content,
                    'priority': 'medium',
                    'category': 'documentation_update',
                    'auto_generated': True,
                    'change_type': 'code_change_impact'
                }
                
                self.documentation_tasks_created.append(todo_data)
                logger.info(f"Created change documentation todo: {todo_content}")
    
    def get_session_documentation_summary(self) -> str:
        """
        Get a formatted summary of documentation status for the current session.
        
        Returns:
            Formatted string with documentation session summary
        """
        if not self.documentation_session_data:
            return "Documentation session not initialized. Run initialization first."
        
        data = self.documentation_session_data
        health = self.check_documentation_health()
        
        summary = f"""
📚 DOCUMENTATION SESSION SUMMARY
{'='*50}

📊 Coverage & Quality:
   • Documentation Coverage: {data.get('documentation_coverage', 0):.1f}%
   • Quality Score: {data.get('quality_score', 0):.2f}/1.0
   • Total Elements: {data.get('total_elements', 0)}
   • Documented Elements: {data.get('documented_elements', 0)}

🔍 Health Status:
   • Overall Health: {health['overall_health'].upper()}
   • Coverage Status: {health['coverage_status'].upper()}
   • Quality Status: {health['quality_status'].upper()}
   • Broken References: {data.get('broken_references', 0)}

📋 Improvement Opportunities:
   • High Priority Suggestions: {data.get('high_priority_suggestions', 0)}
   • Total Suggestions: {data.get('suggestions_count', 0)}
   • Generated Docs: {data.get('generated_docs_count', 0)}

⚡ Performance:
   • Initialization Time: {data.get('initialization_time', 0):.2f}s
   • Last Check: {datetime.fromisoformat(data['session_start_time']).strftime('%H:%M:%S')}
"""
        
        if health.get('recommendations'):
            summary += f"\n🎯 Recommendations:\n"
            for i, rec in enumerate(health['recommendations'], 1):
                summary += f"   {i}. {rec}\n"
        
        return summary.strip()
    
    def _save_documentation_session_data(self):
        """Save documentation session data to cache."""
        try:
            cache_dir = self.project_root / '.claude'
            cache_dir.mkdir(exist_ok=True)
            
            cache_file = cache_dir / 'documentation_session.json'
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.documentation_session_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving documentation session data: {e}")
    
    def load_previous_documentation_session(self) -> Optional[Dict[str, Any]]:
        """Load previous documentation session data."""
        try:
            cache_file = self.project_root / '.claude' / 'documentation_session.json'
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.documentation_session_data = json.load(f)
                return self.documentation_session_data
        except Exception as e:
            logger.error(f"Error loading previous documentation session: {e}")
        
        return None
    
    def generate_session_documentation_report(self) -> str:
        """
        Generate a comprehensive documentation report for the session.
        
        Returns:
            Markdown-formatted documentation report
        """
        report = f"# Documentation Session Report\n\n"
        report += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if not self.documentation_session_data:
            report += "No documentation session data available.\n"
            return report
        
        data = self.documentation_session_data
        
        # Coverage analysis
        report += f"## Coverage Analysis\n\n"
        report += f"- **Overall Coverage**: {data.get('documentation_coverage', 0):.1f}%\n"
        report += f"- **Quality Score**: {data.get('quality_score', 0):.2f}/1.0\n"
        report += f"- **Total Elements**: {data.get('total_elements', 0)}\n"
        report += f"- **Documented Elements**: {data.get('documented_elements', 0)}\n"
        report += f"- **Missing Documentation**: {data.get('total_elements', 0) - data.get('documented_elements', 0)}\n\n"
        
        # Health status
        health = self.check_documentation_health()
        report += f"## Health Status\n\n"
        report += f"- **Overall Health**: {health['overall_health'].title()}\n"
        report += f"- **Coverage Status**: {health['coverage_status'].title()}\n"
        report += f"- **Quality Status**: {health['quality_status'].title()}\n"
        report += f"- **Broken References**: {data.get('broken_references', 0)}\n\n"
        
        # Top suggestions
        suggestions = data.get('suggestions', [])
        if suggestions:
            report += f"## Top Documentation Suggestions\n\n"
            for i, suggestion in enumerate(suggestions, 1):
                file_name = Path(suggestion['file']).name
                report += f"{i}. **{suggestion['element']}** ({suggestion['element_type']}) in `{file_name}`\n"
                report += f"   - {suggestion['suggestion']}\n"
                report += f"   - Priority: {suggestion['priority'].title()}\n\n"
        
        # Performance metrics
        report += f"## Performance Metrics\n\n"
        report += f"- **Initialization Time**: {data.get('initialization_time', 0):.2f}s\n"
        report += f"- **Generated Documentation Files**: {data.get('generated_docs_count', 0)}\n"
        report += f"- **Session Start**: {data.get('session_start_time', 'Unknown')}\n\n"
        
        # Recommendations
        if health.get('recommendations'):
            report += f"## Recommendations\n\n"
            for i, rec in enumerate(health['recommendations'], 1):
                report += f"{i}. {rec}\n"
        
        return report