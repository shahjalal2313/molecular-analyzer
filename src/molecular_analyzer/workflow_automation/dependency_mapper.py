"""
Task Dependency Mapper

Intelligent task dependency detection and mapping with orchestration integration.
Analyzes task relationships and provides dependency-aware scheduling.
"""

import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

# Add path to workflow automation session management
lab_path = Path(__file__).parent.parent.parent.parent / "Lab" / "Project Management" / "workflow-automation" / "src"
if str(lab_path) not in sys.path:
    sys.path.insert(0, str(lab_path))

try:
    from session_management.intelligent_task_orchestrator import IntelligentTaskOrchestrator
    from session_management.token_efficient_task_manager import TokenEfficientTaskManager
except ImportError:
    # Graceful fallback if session management not available
    IntelligentTaskOrchestrator = None
    TokenEfficientTaskManager = None


@dataclass
class TaskDependency:
    """Represents a dependency relationship between tasks."""
    prerequisite_id: str
    dependent_id: str
    dependency_type: str  # 'hard', 'soft', 'suggested'
    strength: float  # 0.0 to 1.0
    reason: str
    detected_method: str


@dataclass
class DependencyGraph:
    """Represents the complete dependency graph for a set of tasks."""
    tasks: Dict[str, Dict[str, Any]]
    dependencies: List[TaskDependency]
    cycles: List[List[str]]
    execution_order: List[str]
    parallel_groups: List[List[str]]


class TaskDependencyMapper:
    """
    Intelligent task dependency detection and mapping system.
    
    Analyzes task content, keywords, and relationships to build dependency graphs
    and suggest optimal execution orders with orchestration integration.
    """
    
    def __init__(self, project_path: Optional[str] = None):
        """Initialize the dependency mapper."""
        self.project_path = project_path or os.getcwd()
        
        # Initialize orchestration integration if available
        self.orchestrator = None
        self.token_manager = None
        
        if IntelligentTaskOrchestrator:
            try:
                self.orchestrator = IntelligentTaskOrchestrator(self.project_path)
            except Exception:
                pass
        
        if TokenEfficientTaskManager:
            try:
                self.token_manager = TokenEfficientTaskManager(self.project_path)
            except Exception:
                pass
        
        # Dependency detection patterns
        self.dependency_patterns = {
            'hard': [
                r'after\s+(.+?)(?:\s|$)',
                r'depends\s+on\s+(.+?)(?:\s|$)',
                r'requires\s+(.+?)(?:\s|$)',
                r'needs\s+(.+?)(?:\s|$)',
                r'once\s+(.+?)(?:\sis|$)',
                r'following\s+(.+?)(?:\s|$)'
            ],
            'soft': [
                r'should\s+follow\s+(.+?)(?:\s|$)',
                r'ideally\s+after\s+(.+?)(?:\s|$)',
                r'preferably\s+(.+?)(?:\s|$)',
                r'better\s+if\s+(.+?)(?:\s|$)'
            ],
            'suggested': [
                r'might\s+need\s+(.+?)(?:\s|$)',
                r'could\s+use\s+(.+?)(?:\s|$)',
                r'may\s+require\s+(.+?)(?:\s|$)'
            ]
        }
        
        # Keywords indicating task relationships
        self.relationship_keywords = {
            'setup': ['foundation', 'base', 'infrastructure', 'core', 'initial'],
            'implementation': ['implement', 'create', 'build', 'develop', 'add'],
            'integration': ['integrate', 'connect', 'merge', 'combine', 'link'],
            'testing': ['test', 'validate', 'verify', 'check', 'ensure'],
            'documentation': ['document', 'write', 'update', 'explain', 'record'],
            'optimization': ['optimize', 'improve', 'enhance', 'refactor', 'polish']
        }
        
        # Task type hierarchy (lower number = higher priority, earlier execution)
        self.task_type_priority = {
            'setup': 1,
            'foundation': 1,
            'core': 2,
            'implementation': 3,
            'integration': 4,
            'testing': 5,
            'documentation': 6,
            'optimization': 7,
            'cleanup': 8
        }
    
    def map_dependencies(self, todos: List[Dict[str, Any]]) -> DependencyGraph:
        """
        Map dependencies for a list of todos and create dependency graph.
        
        Args:
            todos: List of todo items
            
        Returns:
            Complete dependency graph with execution order
        """
        # Create task mapping
        tasks = {todo['id']: todo for todo in todos}
        
        # Detect dependencies
        dependencies = self._detect_dependencies(todos)
        
        # Detect cycles
        cycles = self._detect_cycles(tasks, dependencies)
        
        # Calculate execution order
        execution_order = self._calculate_execution_order(tasks, dependencies)
        
        # Identify parallel groups
        parallel_groups = self._identify_parallel_groups(tasks, dependencies, execution_order)
        
        return DependencyGraph(
            tasks=tasks,
            dependencies=dependencies,
            cycles=cycles,
            execution_order=execution_order,
            parallel_groups=parallel_groups
        )
    
    def _detect_dependencies(self, todos: List[Dict[str, Any]]) -> List[TaskDependency]:
        """Detect dependencies between tasks using multiple methods."""
        dependencies = []
        
        for todo in todos:
            # Method 1: Explicit dependency patterns in content
            explicit_deps = self._detect_explicit_dependencies(todo, todos)
            dependencies.extend(explicit_deps)
            
            # Method 2: Keyword-based relationship detection
            keyword_deps = self._detect_keyword_dependencies(todo, todos)
            dependencies.extend(keyword_deps)
            
            # Method 3: Task type hierarchy dependencies
            hierarchy_deps = self._detect_hierarchy_dependencies(todo, todos)
            dependencies.extend(hierarchy_deps)
            
            # Method 4: File/module dependencies
            file_deps = self._detect_file_dependencies(todo, todos)
            dependencies.extend(file_deps)
        
        # Remove duplicates and merge similar dependencies
        dependencies = self._merge_dependencies(dependencies)
        
        return dependencies
    
    def _detect_explicit_dependencies(self, todo: Dict[str, Any], 
                                    all_todos: List[Dict[str, Any]]) -> List[TaskDependency]:
        """Detect explicit dependencies mentioned in task content."""
        dependencies = []
        content = todo.get('content', '').lower()
        
        for dep_type, patterns in self.dependency_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    referenced_text = match.group(1).strip()
                    
                    # Try to match with other tasks
                    matching_task = self._find_matching_task(referenced_text, all_todos, todo['id'])
                    if matching_task:
                        dependency = TaskDependency(
                            prerequisite_id=matching_task['id'],
                            dependent_id=todo['id'],
                            dependency_type=dep_type,
                            strength=self._calculate_dependency_strength(dep_type, match.group(0)),
                            reason=f"Explicit reference: '{match.group(0)}'",
                            detected_method='explicit_pattern'
                        )
                        dependencies.append(dependency)
        
        return dependencies
    
    def _detect_keyword_dependencies(self, todo: Dict[str, Any], 
                                   all_todos: List[Dict[str, Any]]) -> List[TaskDependency]:
        """Detect dependencies based on keyword relationships."""
        dependencies = []
        content = todo.get('content', '').lower()
        
        # Determine task type
        task_type = self._determine_task_type(content)
        
        # Look for related tasks that should come before this one
        for other_todo in all_todos:
            if other_todo['id'] == todo['id']:
                continue
            
            other_content = other_todo.get('content', '').lower()
            other_type = self._determine_task_type(other_content)
            
            # Check for logical dependencies
            dependency = self._analyze_keyword_relationship(todo, other_todo, task_type, other_type)
            if dependency:
                dependencies.append(dependency)
        
        return dependencies
    
    def _detect_hierarchy_dependencies(self, todo: Dict[str, Any], 
                                     all_todos: List[Dict[str, Any]]) -> List[TaskDependency]:
        """Detect dependencies based on task type hierarchy."""
        dependencies = []
        content = todo.get('content', '').lower()
        task_type = self._determine_task_type(content)
        
        # Find tasks that should naturally come before this type
        for other_todo in all_todos:
            if other_todo['id'] == todo['id']:
                continue
            
            other_content = other_todo.get('content', '').lower()
            other_type = self._determine_task_type(other_content)
            
            # Check hierarchy
            if (self.task_type_priority.get(other_type, 5) < 
                self.task_type_priority.get(task_type, 5)):
                
                # Additional check for content relevance
                if self._check_content_relevance(content, other_content):
                    dependency = TaskDependency(
                        prerequisite_id=other_todo['id'],
                        dependent_id=todo['id'],
                        dependency_type='soft',
                        strength=0.6,
                        reason=f"Task type hierarchy: {other_type} typically before {task_type}",
                        detected_method='hierarchy'
                    )
                    dependencies.append(dependency)
        
        return dependencies
    
    def _detect_file_dependencies(self, todo: Dict[str, Any], 
                                all_todos: List[Dict[str, Any]]) -> List[TaskDependency]:
        """Detect dependencies based on file/module references."""
        dependencies = []
        content = todo.get('content', '').lower()
        
        # Extract file/module references
        file_patterns = [
            r'(\w+\.py)',
            r'(\w+\.md)',
            r'(\w+\.json)',
            r'(\w+/\w+)',
            r'(src/\w+)',
            r'(tests/\w+)'
        ]
        
        referenced_files = set()
        for pattern in file_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                referenced_files.add(match.group(1))
        
        # Look for tasks that create/modify these files
        for other_todo in all_todos:
            if other_todo['id'] == todo['id']:
                continue
            
            other_content = other_todo.get('content', '').lower()
            
            # Check if other task creates files this task needs
            for file_ref in referenced_files:
                if (file_ref in other_content and 
                    any(action in other_content for action in ['create', 'implement', 'build', 'write'])):
                    
                    dependency = TaskDependency(
                        prerequisite_id=other_todo['id'],
                        dependent_id=todo['id'],
                        dependency_type='hard',
                        strength=0.8,
                        reason=f"File dependency: requires {file_ref}",
                        detected_method='file_reference'
                    )
                    dependencies.append(dependency)
        
        return dependencies
    
    def _find_matching_task(self, referenced_text: str, all_todos: List[Dict[str, Any]], 
                           current_id: str) -> Optional[Dict[str, Any]]:
        """Find task that matches referenced text."""
        referenced_text = referenced_text.lower().strip()
        
        for todo in all_todos:
            if todo['id'] == current_id:
                continue
            
            content = todo.get('content', '').lower()
            
            # Check for direct keyword matches
            if any(word in content for word in referenced_text.split() if len(word) > 3):
                return todo
        
        return None
    
    def _determine_task_type(self, content: str) -> str:
        """Determine task type based on content analysis."""
        content = content.lower()
        
        # Score each type based on keyword presence
        type_scores = {}
        for task_type, keywords in self.relationship_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content)
            if score > 0:
                type_scores[task_type] = score
        
        # Return type with highest score, or 'implementation' as default
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        
        return 'implementation'
    
    def _analyze_keyword_relationship(self, todo: Dict[str, Any], other_todo: Dict[str, Any],
                                    task_type: str, other_type: str) -> Optional[TaskDependency]:
        """Analyze relationship between two tasks based on keywords."""
        content = todo.get('content', '').lower()
        other_content = other_todo.get('content', '').lower()
        
        # Check for shared keywords indicating relationship
        content_words = set(content.split())
        other_content_words = set(other_content.split())
        shared_words = content_words.intersection(other_content_words)
        
        # Filter out common words
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
        meaningful_shared = shared_words - common_words
        
        if len(meaningful_shared) >= 2:  # At least 2 meaningful shared words
            # Determine relationship based on task types
            if (self.task_type_priority.get(other_type, 5) < 
                self.task_type_priority.get(task_type, 5)):
                
                return TaskDependency(
                    prerequisite_id=other_todo['id'],
                    dependent_id=todo['id'],
                    dependency_type='soft',
                    strength=min(0.8, 0.3 + len(meaningful_shared) * 0.1),
                    reason=f"Shared context: {', '.join(list(meaningful_shared)[:3])}",
                    detected_method='keyword_relationship'
                )
        
        return None
    
    def _check_content_relevance(self, content1: str, content2: str, threshold: float = 0.3) -> bool:
        """Check if two task contents are related enough to have dependencies."""
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        # Remove common words
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
        words1 -= common_words
        words2 -= common_words
        
        if not words1 or not words2:
            return False
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = intersection / union if union > 0 else 0
        return similarity >= threshold
    
    def _calculate_dependency_strength(self, dep_type: str, matched_text: str) -> float:
        """Calculate strength of dependency based on type and context."""
        base_strengths = {
            'hard': 0.9,
            'soft': 0.6,
            'suggested': 0.3
        }
        
        base_strength = base_strengths.get(dep_type, 0.5)
        
        # Boost for strong keywords
        strong_keywords = ['must', 'required', 'necessary', 'critical', 'essential']
        if any(keyword in matched_text.lower() for keyword in strong_keywords):
            base_strength = min(1.0, base_strength + 0.2)
        
        return base_strength
    
    def _merge_dependencies(self, dependencies: List[TaskDependency]) -> List[TaskDependency]:
        """Merge similar dependencies and remove duplicates."""
        merged = {}
        
        for dep in dependencies:
            key = (dep.prerequisite_id, dep.dependent_id)
            
            if key in merged:
                # Merge with existing dependency - take stronger one
                existing = merged[key]
                if dep.strength > existing.strength:
                    merged[key] = dep
                elif dep.strength == existing.strength and dep.dependency_type == 'hard':
                    merged[key] = dep
            else:
                merged[key] = dep
        
        return list(merged.values())
    
    def _detect_cycles(self, tasks: Dict[str, Any], dependencies: List[TaskDependency]) -> List[List[str]]:
        """Detect circular dependencies in the dependency graph."""
        # Build adjacency list
        graph = {task_id: [] for task_id in tasks.keys()}
        for dep in dependencies:
            graph[dep.prerequisite_id].append(dep.dependent_id)
        
        # DFS to detect cycles
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    return True
            
            rec_stack.remove(node)
            path.pop()
            return False
        
        for task_id in tasks.keys():
            if task_id not in visited:
                dfs(task_id)
        
        return cycles
    
    def _calculate_execution_order(self, tasks: Dict[str, Any], 
                                 dependencies: List[TaskDependency]) -> List[str]:
        """Calculate optimal execution order using topological sort."""
        # Build graph and in-degree count
        graph = {task_id: [] for task_id in tasks.keys()}
        in_degree = {task_id: 0 for task_id in tasks.keys()}
        
        # Only consider hard and soft dependencies for ordering
        for dep in dependencies:
            if dep.dependency_type in ['hard', 'soft']:
                graph[dep.prerequisite_id].append(dep.dependent_id)
                in_degree[dep.dependent_id] += 1
        
        # Topological sort with priority consideration
        execution_order = []
        queue = []
        
        # Start with tasks that have no dependencies
        for task_id in tasks.keys():
            if in_degree[task_id] == 0:
                queue.append(task_id)
        
        # Sort queue by task priority and type
        queue.sort(key=lambda tid: self._get_task_sort_priority(tasks[tid]))
        
        while queue:
            # Get highest priority task
            current = queue.pop(0)
            execution_order.append(current)
            
            # Update neighbors
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
            
            # Re-sort queue
            queue.sort(key=lambda tid: self._get_task_sort_priority(tasks[tid]))
        
        # Add any remaining tasks (due to cycles)
        remaining = set(tasks.keys()) - set(execution_order)
        if remaining:
            remaining_sorted = sorted(remaining, key=lambda tid: self._get_task_sort_priority(tasks[tid]))
            execution_order.extend(remaining_sorted)
        
        return execution_order
    
    def _get_task_sort_priority(self, task: Dict[str, Any]) -> Tuple[int, int, str]:
        """Get sorting priority for task (lower values = higher priority)."""
        content = task.get('content', '').lower()
        task_type = self._determine_task_type(content)
        
        # Priority mapping
        priority_map = {'high': 1, 'medium': 2, 'low': 3}
        priority_value = priority_map.get(task.get('priority', 'medium'), 2)
        
        # Type priority
        type_priority = self.task_type_priority.get(task_type, 5)
        
        # Task name for stable sort
        task_name = task.get('content', '')
        
        return (priority_value, type_priority, task_name)
    
    def _identify_parallel_groups(self, tasks: Dict[str, Any], dependencies: List[TaskDependency],
                                execution_order: List[str]) -> List[List[str]]:
        """Identify groups of tasks that can be executed in parallel."""
        parallel_groups = []
        
        # Build dependency graph for quick lookup
        predecessors = {task_id: set() for task_id in tasks.keys()}
        for dep in dependencies:
            if dep.dependency_type in ['hard', 'soft']:
                predecessors[dep.dependent_id].add(dep.prerequisite_id)
        
        # Group tasks by their dependency level
        levels = {}
        for task_id in execution_order:
            # Calculate maximum dependency level
            if not predecessors[task_id]:
                levels[task_id] = 0
            else:
                max_level = max(levels.get(pred, 0) for pred in predecessors[task_id])
                levels[task_id] = max_level + 1
        
        # Group by level
        level_groups = {}
        for task_id, level in levels.items():
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(task_id)
        
        # Convert to list format
        for level in sorted(level_groups.keys()):
            if len(level_groups[level]) > 1:
                parallel_groups.append(level_groups[level])
        
        return parallel_groups
    
    def get_dependency_summary(self, dependency_graph: DependencyGraph) -> Dict[str, Any]:
        """Get a summary of the dependency analysis."""
        total_tasks = len(dependency_graph.tasks)
        total_dependencies = len(dependency_graph.dependencies)
        
        # Count by type
        dep_by_type = {}
        for dep in dependency_graph.dependencies:
            dep_type = dep.dependency_type
            dep_by_type[dep_type] = dep_by_type.get(dep_type, 0) + 1
        
        # Calculate parallelization potential
        parallel_tasks = sum(len(group) for group in dependency_graph.parallel_groups)
        parallelization_ratio = parallel_tasks / total_tasks if total_tasks > 0 else 0
        
        return {
            'total_tasks': total_tasks,
            'total_dependencies': total_dependencies,
            'dependencies_by_type': dep_by_type,
            'cycles_detected': len(dependency_graph.cycles),
            'parallel_groups': len(dependency_graph.parallel_groups),
            'parallelizable_tasks': parallel_tasks,
            'parallelization_ratio': round(parallelization_ratio, 2),
            'execution_order_available': bool(dependency_graph.execution_order)
        }
    
    def suggest_dependency_resolution(self, dependency_graph: DependencyGraph) -> List[str]:
        """Suggest actions to resolve dependency issues."""
        suggestions = []
        
        # Cycle resolution
        if dependency_graph.cycles:
            suggestions.append(f"Detected {len(dependency_graph.cycles)} circular dependencies")
            for i, cycle in enumerate(dependency_graph.cycles):
                cycle_tasks = [dependency_graph.tasks[tid]['content'][:50] + '...' for tid in cycle]
                suggestions.append(f"Cycle {i+1}: {' -> '.join(cycle_tasks)}")
            suggestions.append("Consider breaking circular dependencies by making some dependencies optional")
        
        # Parallelization opportunities
        if dependency_graph.parallel_groups:
            total_parallel = sum(len(group) for group in dependency_graph.parallel_groups)
            suggestions.append(f"Found {total_parallel} tasks that can be executed in parallel")
            suggestions.append("Consider parallel execution to improve efficiency")
        
        # High dependency tasks
        dependent_counts = {}
        for dep in dependency_graph.dependencies:
            task_id = dep.dependent_id
            dependent_counts[task_id] = dependent_counts.get(task_id, 0) + 1
        
        high_dependency_tasks = [tid for tid, count in dependent_counts.items() if count >= 3]
        if high_dependency_tasks:
            suggestions.append(f"Tasks with many dependencies: {len(high_dependency_tasks)}")
            suggestions.append("Consider simplifying or breaking down complex dependent tasks")
        
        return suggestions