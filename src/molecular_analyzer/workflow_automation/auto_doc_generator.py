"""
AutoDocGenerator: Main orchestrator for automated documentation generation.

This module integrates the CodeChangeAnalyzer and DocumentationTemplateEngine
to provide comprehensive automated documentation generation with cross-reference
management and real-time updates.
"""

import os
import json
import time
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path
from datetime import datetime
import logging

from .code_analyzer import CodeChangeAnalyzer, CodeElement, CodeChange
from .doc_template_engine import DocumentationTemplateEngine

logger = logging.getLogger(__name__)

class CrossReferenceManager:
    """
    Manages cross-references and automatic updates in documentation.
    
    Features:
    - Track dependencies between code elements
    - Detect broken references
    - Automatically update cross-references when code changes
    - Generate reference graphs and impact analysis
    """
    
    def __init__(self, project_root: str):
        """Initialize the CrossReferenceManager."""
        self.project_root = Path(project_root)
        self.reference_graph: Dict[str, Set[str]] = {}
        self.reverse_references: Dict[str, Set[str]] = {}
        self.documentation_files: Dict[str, str] = {}
        
    def build_reference_graph(self, all_elements: Dict[str, List[CodeElement]]):
        """
        Build a complete reference graph from all code elements.
        
        Args:
            all_elements: Dictionary mapping file paths to code elements
        """
        self.reference_graph.clear()
        self.reverse_references.clear()
        
        # Build forward references
        for file_path, elements in all_elements.items():
            file_refs = set()
            
            for element in elements:
                element_id = f"{file_path}::{element.name}"
                
                # Add dependencies as references
                for dep in element.dependencies:
                    if self._is_valid_reference(dep):
                        file_refs.add(dep)
                        
                        # Build reverse references
                        if dep not in self.reverse_references:
                            self.reverse_references[dep] = set()
                        self.reverse_references[dep].add(element_id)
            
            self.reference_graph[file_path] = file_refs
    
    def _is_valid_reference(self, reference: str) -> bool:
        """Check if a reference is valid and should be tracked."""
        invalid_refs = {'self', 'cls', 'None', 'True', 'False'}
        return (reference not in invalid_refs and 
                not reference.startswith('__') and
                not reference.startswith('_'))
    
    def find_broken_references(self, all_elements: Dict[str, List[CodeElement]]) -> List[Dict[str, str]]:
        """
        Find broken references in the codebase.
        
        Args:
            all_elements: Dictionary mapping file paths to code elements
            
        Returns:
            List of broken reference information
        """
        broken_refs = []
        all_defined_names = set()
        
        # Collect all defined names
        for file_path, elements in all_elements.items():
            for element in elements:
                all_defined_names.add(element.name)
                all_defined_names.add(f"{Path(file_path).stem}.{element.name}")
        
        # Check for broken references
        for file_path, file_refs in self.reference_graph.items():
            for ref in file_refs:
                if ref not in all_defined_names and '.' not in ref:
                    broken_refs.append({
                        'reference': ref,
                        'file': file_path,
                        'type': 'undefined_reference',
                        'severity': 'warning'
                    })
        
        return broken_refs
    
    def get_impact_analysis(self, changed_element: CodeElement) -> Dict[str, List[str]]:
        """
        Analyze the impact of changes to a code element.
        
        Args:
            changed_element: The code element that was changed
            
        Returns:
            Dictionary with impact analysis information
        """
        element_id = f"{changed_element.file_path}::{changed_element.name}"
        
        impact = {
            'direct_dependents': [],
            'documentation_updates_needed': [],
            'test_files_affected': [],
            'api_changes': []
        }
        
        # Find direct dependents
        if changed_element.name in self.reverse_references:
            impact['direct_dependents'] = list(self.reverse_references[changed_element.name])
        
        # Identify documentation that needs updates
        for file_path in self.documentation_files:
            if changed_element.name in self.documentation_files[file_path]:
                impact['documentation_updates_needed'].append(file_path)
        
        # Identify potential test files
        test_patterns = ['test_', '_test', 'tests/']
        for dependent in impact['direct_dependents']:
            dep_file = dependent.split('::')[0]
            if any(pattern in dep_file.lower() for pattern in test_patterns):
                impact['test_files_affected'].append(dep_file)
        
        # Check for API changes
        if changed_element.type in ['class', 'function'] and not changed_element.name.startswith('_'):
            impact['api_changes'].append(f"Public {changed_element.type} '{changed_element.name}' modified")
        
        return impact
    
    def update_documentation_references(self, file_path: str, old_name: str, new_name: str):
        """
        Update references in documentation files when a code element is renamed.
        
        Args:
            file_path: Path to the file containing the renamed element
            old_name: Previous name of the element
            new_name: New name of the element
        """
        for doc_file, content in self.documentation_files.items():
            updated_content = content.replace(f"`{old_name}`", f"`{new_name}`")
            updated_content = updated_content.replace(f"{old_name}(", f"{new_name}(")
            updated_content = updated_content.replace(f"## {old_name}", f"## {new_name}")
            
            if updated_content != content:
                self.documentation_files[doc_file] = updated_content
                logger.info(f"Updated references in {doc_file}: {old_name} -> {new_name}")

class AutoDocGenerator:
    """
    Main orchestrator for automated documentation generation.
    
    Integrates code analysis, template generation, and cross-reference management
    to provide comprehensive automated documentation with real-time updates.
    """
    
    def __init__(self, project_root: str):
        """Initialize the AutoDocGenerator."""
        self.project_root = Path(project_root)
        self.code_analyzer = CodeChangeAnalyzer(str(project_root))
        self.template_engine = DocumentationTemplateEngine(str(project_root))
        self.cross_ref_manager = CrossReferenceManager(str(project_root))
        
        # State tracking
        self.last_analysis_time = 0
        self.documentation_coverage: Dict[str, float] = {}
        self.quality_scores: Dict[str, float] = {}
        
        # Configuration
        self.auto_update_enabled = True
        self.documentation_formats = ['markdown', 'docstring']
        self.output_directory = self.project_root / 'docs' / 'generated'
        
        # Ensure output directory exists
        self.output_directory.mkdir(parents=True, exist_ok=True)
    
    def analyze_and_generate_docs(self, force_full_analysis: bool = False) -> Dict[str, any]:
        """
        Perform complete analysis and documentation generation.
        
        Args:
            force_full_analysis: Whether to force full analysis regardless of timestamps
            
        Returns:
            Dictionary with analysis results and generated documentation info
        """
        start_time = time.time()
        
        # Analyze all project files
        logger.info("Starting comprehensive project analysis...")
        all_elements = self.code_analyzer.analyze_project()
        
        # Build cross-reference graph
        self.cross_ref_manager.build_reference_graph(all_elements)
        
        # Generate documentation for each file
        generated_docs = {}
        total_elements = 0
        documented_elements = 0
        
        for file_path, elements in all_elements.items():
            if not elements:
                continue
                
            total_elements += len(elements)
            
            # Generate module documentation
            module_doc = self.template_engine.generate_module_documentation(file_path, elements)
            
            # Generate API documentation for each element
            api_docs = []
            for element in elements:
                element_doc = self.template_engine.generate_documentation(element, "api")
                api_docs.append(element_doc)
                
                # Calculate quality score
                quality_score = self.template_engine.get_documentation_quality_score(element)
                self.quality_scores[f"{file_path}::{element.name}"] = quality_score
                
                if element.docstring or quality_score > 0.5:
                    documented_elements += 1
            
            # Save generated documentation
            relative_path = Path(file_path).relative_to(self.project_root)
            output_file = self.output_directory / f"{relative_path.stem}_docs.md"
            
            full_doc = f"{module_doc}\n\n{''.join(api_docs)}"
            generated_docs[str(output_file)] = full_doc
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_doc)
        
        # Calculate overall coverage
        overall_coverage = (documented_elements / total_elements) if total_elements > 0 else 0.0
        self.documentation_coverage['overall'] = overall_coverage
        
        # Find broken references
        broken_refs = self.cross_ref_manager.find_broken_references(all_elements)
        
        # Generate summary report
        analysis_time = time.time() - start_time
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'analysis_time_seconds': round(analysis_time, 2),
            'total_files_analyzed': len(all_elements),
            'total_elements_found': total_elements,
            'documented_elements': documented_elements,
            'documentation_coverage': round(overall_coverage * 100, 1),
            'generated_documentation_files': len(generated_docs),
            'broken_references_found': len(broken_refs),
            'average_quality_score': round(sum(self.quality_scores.values()) / len(self.quality_scores), 2) if self.quality_scores else 0.0,
            'broken_references': broken_refs,
            'quality_scores_by_element': self.quality_scores
        }
        
        # Save analysis report
        report_file = self.output_directory / 'analysis_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Documentation generation completed in {analysis_time:.2f}s")
        logger.info(f"Coverage: {overall_coverage*100:.1f}% ({documented_elements}/{total_elements})")
        logger.info(f"Generated {len(generated_docs)} documentation files")
        
        self.last_analysis_time = time.time()
        
        return report
    
    def detect_and_document_changes(self, file_path: str, backup_path: Optional[str] = None) -> Dict[str, any]:
        """
        Detect changes in a specific file and update documentation accordingly.
        
        Args:
            file_path: Path to the file to analyze
            backup_path: Path to backup/previous version of the file
            
        Returns:
            Dictionary with change detection and documentation update results
        """
        if not backup_path:
            backup_path = f"{file_path}.backup"
        
        # Detect changes
        changes = self.code_analyzer.detect_changes(backup_path, file_path)
        
        if not changes:
            return {'changes_detected': 0, 'documentation_updated': False}
        
        # Generate change documentation
        change_doc = self.template_engine.generate_change_documentation(changes)
        
        # Analyze impact
        impact_analysis = {}
        for change in changes:
            if change.element:
                impact = self.cross_ref_manager.get_impact_analysis(change.element)
                impact_analysis[change.element.name] = impact
        
        # Update existing documentation
        self._update_existing_documentation(changes)
        
        # Save change log
        change_log_file = self.output_directory / f"changes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(change_log_file, 'w', encoding='utf-8') as f:
            f.write(change_doc)
        
        result = {
            'changes_detected': len(changes),
            'change_types': [c.change_type for c in changes],
            'impact_analysis': impact_analysis,
            'change_log_file': str(change_log_file),
            'documentation_updated': True
        }
        
        logger.info(f"Detected {len(changes)} changes in {file_path}")
        
        return result
    
    def _update_existing_documentation(self, changes: List[CodeChange]):
        """Update existing documentation based on detected changes."""
        for change in changes:
            if change.change_type == 'modified' and change.old_element and change.element:
                # Handle renamed elements
                if change.old_element.name != change.element.name:
                    self.cross_ref_manager.update_documentation_references(
                        change.element.file_path,
                        change.old_element.name,
                        change.element.name
                    )
    
    def get_documentation_suggestions(self) -> List[Dict[str, str]]:
        """
        Get suggestions for improving documentation coverage and quality.
        
        Returns:
            List of suggestion dictionaries
        """
        suggestions = []
        
        # Analyze all elements for suggestions
        all_elements = self.code_analyzer.analyze_project()
        
        for file_path, elements in all_elements.items():
            for element in elements:
                element_suggestions = self.code_analyzer.get_documentation_suggestions(element)
                
                for suggestion in element_suggestions:
                    suggestions.append({
                        'file': file_path,
                        'element': element.name,
                        'element_type': element.type,
                        'suggestion': suggestion,
                        'priority': self._get_suggestion_priority(element),
                        'line_number': element.line_number
                    })
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        suggestions.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return suggestions
    
    def _get_suggestion_priority(self, element: CodeElement) -> str:
        """Determine priority for documentation suggestions."""
        if element.type == 'class' and not element.docstring:
            return 'high'
        elif element.complexity_score > 5 and not element.docstring:
            return 'high'
        elif element.type == 'function' and element.parameters and not element.docstring:
            return 'medium'
        else:
            return 'low'
    
    def generate_coverage_report(self) -> str:
        """
        Generate a comprehensive documentation coverage report.
        
        Returns:
            Markdown-formatted coverage report
        """
        all_elements = self.code_analyzer.analyze_project()
        
        total_elements = sum(len(elements) for elements in all_elements.values())
        documented_elements = 0
        
        report = "# Documentation Coverage Report\n\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Overall statistics
        for file_path, elements in all_elements.items():
            file_documented = 0
            for element in elements:
                if element.docstring:
                    documented_elements += 1
                    file_documented += 1
            
            if elements:
                file_coverage = (file_documented / len(elements)) * 100
                relative_path = Path(file_path).relative_to(self.project_root)
                report += f"- **{relative_path}**: {file_coverage:.1f}% ({file_documented}/{len(elements)})\n"
        
        overall_coverage = (documented_elements / total_elements) * 100 if total_elements > 0 else 0
        
        report += f"\n## Overall Coverage: {overall_coverage:.1f}%\n"
        report += f"- Total elements: {total_elements}\n"
        report += f"- Documented elements: {documented_elements}\n"
        report += f"- Missing documentation: {total_elements - documented_elements}\n\n"
        
        # Quality metrics
        if self.quality_scores:
            avg_quality = sum(self.quality_scores.values()) / len(self.quality_scores)
            report += f"## Average Quality Score: {avg_quality:.2f}/1.0\n\n"
        
        # Suggestions summary
        suggestions = self.get_documentation_suggestions()
        high_priority = len([s for s in suggestions if s['priority'] == 'high'])
        medium_priority = len([s for s in suggestions if s['priority'] == 'medium'])
        
        report += f"## Improvement Suggestions\n"
        report += f"- High priority: {high_priority}\n"
        report += f"- Medium priority: {medium_priority}\n"
        report += f"- Total suggestions: {len(suggestions)}\n"
        
        return report
    
    def enable_real_time_monitoring(self, watch_patterns: List[str] = None):
        """
        Enable real-time documentation monitoring (placeholder for future implementation).
        
        Args:
            watch_patterns: File patterns to monitor for changes
        """
        if watch_patterns is None:
            watch_patterns = ['*.py']
        
        logger.info("Real-time monitoring would be implemented here")
        logger.info(f"Watching patterns: {watch_patterns}")
        
        # This would integrate with file system watchers in a real implementation
        # For now, this is a placeholder for the architecture