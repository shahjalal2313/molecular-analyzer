"""
Quality Metrics Collector - Task 2.1.4

Collects and manages quality metrics from various sources for
historical analysis and predictive modeling.
"""

import ast
import os
import subprocess
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
import statistics


@dataclass
class CodeMetrics:
    """Code-level metrics for a file or module"""
    file_path: str
    lines_of_code: int
    cyclomatic_complexity: int
    maintainability_index: float
    class_count: int
    function_count: int
    comment_ratio: float
    import_count: int
    docstring_coverage: float


@dataclass
class ProjectMetrics:
    """Project-level aggregated metrics"""
    timestamp: datetime
    total_files: int
    total_lines: int
    average_complexity: float
    documentation_coverage: float
    test_coverage: float
    code_quality_score: float
    technical_debt_ratio: float
    maintainability_index: float
    dependency_count: int
    module_coupling: float


class QualityMetricsCollector:
    """
    Comprehensive quality metrics collection system that gathers
    data from multiple sources for predictive analysis.
    
    Capabilities:
    - AST-based code analysis
    - Documentation coverage assessment
    - Test coverage integration
    - Technical debt calculation
    - Historical data management
    """
    
    def __init__(self, project_root: str = None):
        """Initialize collector with project root directory"""
        self.project_root = project_root or os.getcwd()
        self.metrics_cache: Dict[str, Any] = {}
        self.last_collection_time: Optional[datetime] = None
        
    def collect_comprehensive_metrics(self) -> ProjectMetrics:
        """
        Collect comprehensive quality metrics for the entire project
        
        Returns:
            ProjectMetrics object with all collected data
        """
        print("Collecting comprehensive quality metrics...")
        
        # Collect file-level metrics
        file_metrics = self._collect_file_metrics()
        
        # Calculate project-level aggregations
        project_metrics = self._aggregate_project_metrics(file_metrics)
        
        # Enhance with additional metrics
        project_metrics = self._enhance_with_advanced_metrics(project_metrics, file_metrics)
        
        self.last_collection_time = datetime.now()
        
        print(f"Metrics collection complete: {len(file_metrics)} files analyzed")
        return project_metrics
    
    def _collect_file_metrics(self) -> List[CodeMetrics]:
        """Collect metrics for all Python files in the project"""
        file_metrics = []
        
        python_files = self._find_python_files()
        
        for file_path in python_files:
            try:
                metrics = self._analyze_file(file_path)
                if metrics:
                    file_metrics.append(metrics)
            except Exception as e:
                print(f"Warning: Could not analyze {file_path}: {e}")
                continue
        
        return file_metrics
    
    def _find_python_files(self) -> List[str]:
        """Find all Python files in the project"""
        python_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                '__pycache__', 'node_modules', 'venv', 'env', '.git'
            ]]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    python_files.append(file_path)
        
        return python_files
    
    def _analyze_file(self, file_path: str) -> Optional[CodeMetrics]:
        """Analyze a single Python file and extract metrics"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError:
                return None
            
            # Calculate basic metrics
            lines_of_code = len([line for line in content.split('\n') if line.strip() and not line.strip().startswith('#')])
            
            # Calculate complexity using AST
            complexity = self._calculate_cyclomatic_complexity(tree)
            
            # Count classes and functions
            class_count = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
            function_count = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
            
            # Calculate comment ratio
            total_lines = len(content.split('\n'))
            comment_lines = len([line for line in content.split('\n') if line.strip().startswith('#')])
            comment_ratio = (comment_lines / max(1, total_lines)) * 100
            
            # Count imports
            import_count = len([node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))])
            
            # Calculate docstring coverage
            docstring_coverage = self._calculate_docstring_coverage(tree)
            
            # Calculate maintainability index (simplified)
            maintainability_index = self._calculate_maintainability_index(
                lines_of_code, complexity, comment_ratio
            )
            
            return CodeMetrics(
                file_path=file_path,
                lines_of_code=lines_of_code,
                cyclomatic_complexity=complexity,
                maintainability_index=maintainability_index,
                class_count=class_count,
                function_count=function_count,
                comment_ratio=comment_ratio,
                import_count=import_count,
                docstring_coverage=docstring_coverage
            )
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity using AST"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            # Decision points that increase complexity
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, (ast.ExceptHandler,)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                # And/Or operators add complexity
                complexity += len(node.values) - 1
            elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                # Comprehensions add complexity
                complexity += 1
        
        return complexity
    
    def _calculate_docstring_coverage(self, tree: ast.AST) -> float:
        """Calculate docstring coverage percentage"""
        documentable_items = []
        documented_items = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                documentable_items.append(node)
                
                # Check if it has a docstring
                if (node.body and 
                    isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and 
                    isinstance(node.body[0].value.value, str)):
                    documented_items.append(node)
        
        if not documentable_items:
            return 100.0  # No documentable items means 100% coverage
        
        return (len(documented_items) / len(documentable_items)) * 100
    
    def _calculate_maintainability_index(self, loc: int, complexity: int, comment_ratio: float) -> float:
        """Calculate simplified maintainability index"""
        # Simplified version of Microsoft's Maintainability Index
        import math
        
        # Avoid log(0) by ensuring minimum values
        halstead_volume = max(1, loc * 2)  # Simplified Halstead volume approximation
        
        mi = (
            171 - 
            5.2 * math.log(halstead_volume) - 
            0.23 * complexity - 
            16.2 * math.log(max(1, loc)) +
            50 * math.sin(math.sqrt(2.4 * comment_ratio))
        )
        
        return max(0, min(100, mi))
    
    def _aggregate_project_metrics(self, file_metrics: List[CodeMetrics]) -> ProjectMetrics:
        """Aggregate file-level metrics to project level"""
        if not file_metrics:
            return self._create_empty_project_metrics()
        
        total_files = len(file_metrics)
        total_lines = sum(m.lines_of_code for m in file_metrics)
        
        # Calculate averages
        avg_complexity = statistics.mean([m.cyclomatic_complexity for m in file_metrics])
        avg_maintainability = statistics.mean([m.maintainability_index for m in file_metrics])
        avg_docstring_coverage = statistics.mean([m.docstring_coverage for m in file_metrics])
        
        # Calculate technical debt ratio (simplified)
        high_complexity_files = len([m for m in file_metrics if m.cyclomatic_complexity > 10])
        technical_debt_ratio = (high_complexity_files / total_files) * 100 if total_files > 0 else 0
        
        # Calculate dependency metrics
        total_imports = sum(m.import_count for m in file_metrics)
        avg_imports_per_file = total_imports / total_files if total_files > 0 else 0
        
        # Module coupling (simplified as average imports per file)
        module_coupling = min(100, avg_imports_per_file * 5)  # Scale to 0-100
        
        # Calculate overall code quality score
        code_quality_score = self._calculate_code_quality_score(
            avg_complexity, avg_maintainability, avg_docstring_coverage, technical_debt_ratio
        )
        
        return ProjectMetrics(
            timestamp=datetime.now(),
            total_files=total_files,
            total_lines=total_lines,
            average_complexity=avg_complexity,
            documentation_coverage=avg_docstring_coverage,
            test_coverage=0.0,  # Will be enhanced later
            code_quality_score=code_quality_score,
            technical_debt_ratio=technical_debt_ratio,
            maintainability_index=avg_maintainability,
            dependency_count=total_imports,
            module_coupling=module_coupling
        )
    
    def _create_empty_project_metrics(self) -> ProjectMetrics:
        """Create empty project metrics for projects with no analyzable files"""
        return ProjectMetrics(
            timestamp=datetime.now(),
            total_files=0,
            total_lines=0,
            average_complexity=0.0,
            documentation_coverage=0.0,
            test_coverage=0.0,
            code_quality_score=0.0,
            technical_debt_ratio=0.0,
            maintainability_index=0.0,
            dependency_count=0,
            module_coupling=0.0
        )
    
    def _calculate_code_quality_score(self, complexity: float, maintainability: float, 
                                    doc_coverage: float, debt_ratio: float) -> float:
        """Calculate overall code quality score (0-100)"""
        # Weight different factors
        complexity_score = max(0, 100 - (complexity - 1) * 10)  # Penalty for high complexity
        maintainability_score = maintainability
        documentation_score = doc_coverage
        debt_score = max(0, 100 - debt_ratio)  # Penalty for high debt
        
        # Weighted average
        quality_score = (
            complexity_score * 0.3 +
            maintainability_score * 0.3 +
            documentation_score * 0.2 +
            debt_score * 0.2
        )
        
        return max(0, min(100, quality_score))
    
    def _enhance_with_advanced_metrics(self, base_metrics: ProjectMetrics, 
                                     file_metrics: List[CodeMetrics]) -> ProjectMetrics:
        """Enhance basic metrics with advanced analysis"""
        # Try to get test coverage from common tools
        test_coverage = self._get_test_coverage()
        
        # Update test coverage in metrics
        enhanced_metrics = ProjectMetrics(
            timestamp=base_metrics.timestamp,
            total_files=base_metrics.total_files,
            total_lines=base_metrics.total_lines,
            average_complexity=base_metrics.average_complexity,
            documentation_coverage=base_metrics.documentation_coverage,
            test_coverage=test_coverage,
            code_quality_score=base_metrics.code_quality_score,
            technical_debt_ratio=base_metrics.technical_debt_ratio,
            maintainability_index=base_metrics.maintainability_index,
            dependency_count=base_metrics.dependency_count,
            module_coupling=base_metrics.module_coupling
        )
        
        return enhanced_metrics
    
    def collect_project_metrics(self, project_path: str = None) -> Dict[str, Any]:
        """
        Collect project metrics - interface method for compatibility
        
        Args:
            project_path: Path to project (optional, uses current project_root if not provided)
            
        Returns:
            Dictionary with project metrics
        """
        if project_path and project_path != self.project_root:
            # Create temporary collector for different project
            temp_collector = QualityMetricsCollector(project_path)
            metrics = temp_collector.collect_comprehensive_metrics()
        else:
            metrics = self.collect_comprehensive_metrics()
            
        return {
            'timestamp': metrics.timestamp.isoformat(),
            'total_files': metrics.total_files,
            'total_lines': metrics.total_lines,
            'average_complexity': metrics.average_complexity,
            'documentation_coverage': metrics.documentation_coverage,
            'test_coverage': metrics.test_coverage,
            'code_quality_score': metrics.code_quality_score,
            'technical_debt_ratio': metrics.technical_debt_ratio,
            'maintainability_index': metrics.maintainability_index,
            'dependency_count': metrics.dependency_count,
            'module_coupling': metrics.module_coupling
        }
    
    def _get_test_coverage(self) -> float:
        """Attempt to get test coverage from various sources"""
        coverage_methods = [
            self._get_coverage_from_pytest_cov,
            self._get_coverage_from_coverage_py,
            self._estimate_coverage_from_files
        ]
        
        for method in coverage_methods:
            try:
                coverage = method()
                if coverage is not None:
                    return coverage
            except Exception:
                continue
        
        return 0.0  # Default if no coverage information available
    
    def _get_coverage_from_pytest_cov(self) -> Optional[float]:
        """Get coverage from pytest-cov if available"""
        try:
            result = subprocess.run(
                ['python', '-m', 'pytest', '--cov=.', '--cov-report=term-missing', '--quiet'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse coverage percentage from output
                output = result.stdout
                coverage_match = re.search(r'TOTAL.*?(\d+)%', output)
                if coverage_match:
                    return float(coverage_match.group(1))
        except Exception:
            pass
        
        return None
    
    def _get_coverage_from_coverage_py(self) -> Optional[float]:
        """Get coverage from coverage.py if available"""
        try:
            result = subprocess.run(
                ['python', '-m', 'coverage', 'report'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse coverage percentage from output
                output = result.stdout
                coverage_match = re.search(r'TOTAL.*?(\d+)%', output)
                if coverage_match:
                    return float(coverage_match.group(1))
        except Exception:
            pass
        
        return None
    
    def _estimate_coverage_from_files(self) -> float:
        """Estimate test coverage based on test files present"""
        source_files = self._find_python_files()
        source_files = [f for f in source_files if not f.endswith('test.py') and '/test' not in f]
        
        test_files = []
        for root, dirs, files in os.walk(self.project_root):
            for file in files:
                if (file.startswith('test_') and file.endswith('.py')) or file.endswith('_test.py'):
                    test_files.append(os.path.join(root, file))
        
        if not source_files:
            return 0.0
        
        # Simple heuristic: assume each test file covers 5 source files on average
        estimated_covered_files = min(len(source_files), len(test_files) * 5)
        estimated_coverage = (estimated_covered_files / len(source_files)) * 100
        
        return min(85.0, estimated_coverage)  # Cap at 85% for estimates
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of collected metrics"""
        metrics = self.collect_comprehensive_metrics()
        
        return {
            'collection_timestamp': metrics.timestamp.isoformat(),
            'project_overview': {
                'total_files': metrics.total_files,
                'total_lines': metrics.total_lines,
                'dependency_count': metrics.dependency_count
            },
            'quality_scores': {
                'overall_quality': metrics.code_quality_score,
                'maintainability': metrics.maintainability_index,
                'complexity': metrics.average_complexity,
                'documentation_coverage': metrics.documentation_coverage,
                'test_coverage': metrics.test_coverage
            },
            'risk_indicators': {
                'technical_debt_ratio': metrics.technical_debt_ratio,
                'module_coupling': metrics.module_coupling,
                'complexity_risk': 'high' if metrics.average_complexity > 10 else 'low'
            },
            'recommendations': self._generate_improvement_recommendations(metrics)
        }
    
    def _generate_improvement_recommendations(self, metrics: ProjectMetrics) -> List[str]:
        """Generate actionable recommendations based on collected metrics"""
        recommendations = []
        
        if metrics.documentation_coverage < 70:
            recommendations.append("Improve documentation coverage - aim for >80%")
        
        if metrics.test_coverage < 60:
            recommendations.append("Increase test coverage - current coverage is low")
        
        if metrics.average_complexity > 10:
            recommendations.append("Reduce code complexity - refactor complex functions")
        
        if metrics.technical_debt_ratio > 20:
            recommendations.append("Address technical debt - high complexity file ratio")
        
        if metrics.maintainability_index < 60:
            recommendations.append("Improve maintainability - refactor and document code")
        
        if metrics.module_coupling > 50:
            recommendations.append("Reduce module coupling - minimize inter-module dependencies")
        
        if not recommendations:
            recommendations.append("Code quality metrics look good - maintain current standards")
        
        return recommendations
    
    def export_metrics_for_prediction(self, output_path: str) -> bool:
        """
        Export metrics in format suitable for predictive analysis
        
        Args:
            output_path: Path to export metrics data
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            metrics = self.collect_comprehensive_metrics()
            
            export_data = {
                'timestamp': metrics.timestamp.isoformat(),
                'metrics': {
                    'doc_coverage': metrics.documentation_coverage,
                    'code_quality_score': metrics.code_quality_score,
                    'test_coverage': metrics.test_coverage,
                    'complexity_score': metrics.average_complexity,
                    'maintainability_index': metrics.maintainability_index,
                    'technical_debt_ratio': metrics.technical_debt_ratio
                },
                'metadata': {
                    'total_files': metrics.total_files,
                    'total_lines': metrics.total_lines,
                    'dependency_count': metrics.dependency_count,
                    'module_coupling': metrics.module_coupling
                }
            }
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error exporting metrics: {e}")
            return False


class HistoricalMetricsManager:
    """
    Manages historical metrics data for trend analysis
    and predictive modeling.
    """
    
    def __init__(self, storage_path: str = None):
        """Initialize with storage path for historical data"""
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(__file__), '..', '..', '..', '..', 
            'Lab', 'Project Management', 'workflow-automation', 'historical_metrics.json'
        )
        self.historical_data: List[Dict[str, Any]] = []
        self._load_historical_data()
    
    def _load_historical_data(self) -> None:
        """Load historical metrics data from storage"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.historical_data = data.get('historical_metrics', [])
        except Exception as e:
            print(f"Warning: Could not load historical metrics: {e}")
            self.historical_data = []
    
    def add_metrics_snapshot(self, collector: QualityMetricsCollector) -> bool:
        """
        Add a new metrics snapshot to historical data
        
        Args:
            collector: QualityMetricsCollector instance
            
        Returns:
            True if snapshot added successfully
        """
        try:
            metrics = collector.collect_comprehensive_metrics()
            
            snapshot = {
                'timestamp': metrics.timestamp.isoformat(),
                'metrics': {
                    'doc_coverage': metrics.documentation_coverage,
                    'code_quality_score': metrics.code_quality_score,
                    'test_coverage': metrics.test_coverage,
                    'complexity_score': metrics.average_complexity,
                    'maintainability_index': metrics.maintainability_index,
                    'technical_debt_ratio': metrics.technical_debt_ratio
                },
                'metadata': {
                    'total_files': metrics.total_files,
                    'total_lines': metrics.total_lines,
                    'dependency_count': metrics.dependency_count
                }
            }
            
            self.historical_data.append(snapshot)
            
            # Keep only last 90 days of data
            cutoff_date = datetime.now().replace(day=datetime.now().day - 90)
            self.historical_data = [
                d for d in self.historical_data 
                if datetime.fromisoformat(d['timestamp']) > cutoff_date
            ]
            
            self._save_historical_data()
            return True
            
        except Exception as e:
            print(f"Error adding metrics snapshot: {e}")
            return False
    
    def _save_historical_data(self) -> None:
        """Save historical data to storage"""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            data = {'historical_metrics': self.historical_data}
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save historical metrics: {e}")
    
    def get_trend_data(self, metric_name: str, days_back: int = 30) -> List[Tuple[datetime, float]]:
        """
        Get trend data for a specific metric
        
        Args:
            metric_name: Name of the metric
            days_back: Number of days to look back
            
        Returns:
            List of (timestamp, value) tuples
        """
        cutoff_date = datetime.now().replace(day=datetime.now().day - days_back)
        trend_data = []
        
        for snapshot in self.historical_data:
            timestamp = datetime.fromisoformat(snapshot['timestamp'])
            if timestamp > cutoff_date:
                value = snapshot['metrics'].get(metric_name)
                if value is not None:
                    trend_data.append((timestamp, value))
        
        return sorted(trend_data, key=lambda x: x[0])
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics for historical data"""
        if not self.historical_data:
            return {'error': 'No historical data available'}
        
        metrics_names = [
            'doc_coverage', 'code_quality_score', 'test_coverage',
            'complexity_score', 'maintainability_index', 'technical_debt_ratio'
        ]
        
        stats = {}
        for metric in metrics_names:
            values = [s['metrics'].get(metric, 0) for s in self.historical_data]
            values = [v for v in values if v is not None]
            
            if values:
                stats[metric] = {
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
                    'min': min(values),
                    'max': max(values),
                    'trend': self._calculate_simple_trend(values)
                }
        
        return {
            'data_points': len(self.historical_data),
            'date_range': {
                'oldest': self.historical_data[0]['timestamp'] if self.historical_data else None,
                'newest': self.historical_data[-1]['timestamp'] if self.historical_data else None
            },
            'metric_statistics': stats
        }
    
    def _calculate_simple_trend(self, values: List[float]) -> str:
        """Calculate simple trend direction for a list of values"""
        if len(values) < 2:
            return 'stable'
        
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        change_percent = ((second_avg - first_avg) / first_avg) * 100 if first_avg != 0 else 0
        
        if change_percent > 5:
            return 'improving'
        elif change_percent < -5:
            return 'declining'
        else:
            return 'stable'