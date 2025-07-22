"""
Enhanced TodoWrite System

Intelligent TodoWrite integration that maintains backward compatibility while adding
smart prioritization, dependency mapping, and effort estimation capabilities.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import json
import copy

# Add path to workflow automation session management
lab_path = Path(__file__).parent.parent.parent.parent / "Lab" / "Project Management" / "workflow-automation" / "src"
if str(lab_path) not in sys.path:
    sys.path.insert(0, str(lab_path))

# Import our components
from .priority_optimizer import DynamicPriorityOptimizer
from .dependency_mapper import TaskDependencyMapper, DependencyGraph
from .effort_estimator import EffortEstimationEngine, EffortEstimate

try:
    from session_management.auto_session_manager import AutoSessionManager
    from session_management.intelligent_task_orchestrator import IntelligentTaskOrchestrator
except ImportError:
    # Graceful fallback if session management not available
    AutoSessionManager = None
    IntelligentTaskOrchestrator = None


class EnhancedTodoSystem:
    """
    Enhanced TodoWrite system with intelligent features.
    
    Provides backward-compatible TodoWrite functionality with added intelligence:
    - Smart task prioritization using token efficiency analysis
    - Dependency mapping and execution order optimization
    - Effort estimation with session planning
    - Integration with workflow automation system
    """
    
    def __init__(self, project_path: Optional[str] = None, enable_intelligence: bool = True):
        """
        Initialize the enhanced todo system.
        
        Args:
            project_path: Path to project root
            enable_intelligence: Whether to enable intelligent features (default: True)
        """
        self.project_path = project_path or os.getcwd()
        self.enable_intelligence = enable_intelligence
        
        # Initialize intelligence components if enabled
        self.priority_optimizer = None
        self.dependency_mapper = None
        self.effort_estimator = None
        self.session_manager = None
        self.orchestrator = None
        
        if enable_intelligence:
            try:
                self.priority_optimizer = DynamicPriorityOptimizer(self.project_path)
                self.dependency_mapper = TaskDependencyMapper(self.project_path)
                self.effort_estimator = EffortEstimationEngine(self.project_path)
                
                if AutoSessionManager:
                    self.session_manager = AutoSessionManager(self.project_path)
                if IntelligentTaskOrchestrator:
                    self.orchestrator = IntelligentTaskOrchestrator(self.project_path)
            except Exception as e:
                # If intelligence components fail, continue with basic functionality
                self.enable_intelligence = False
                print(f"Intelligence features disabled due to initialization error: {e}")
        
        # State management
        self._last_analysis = None
        self._dependency_graph = None
        self._effort_estimates = {}
    
    def process_todos(self, todos: List[Dict[str, Any]], 
                     analysis_level: str = 'full') -> Dict[str, Any]:
        """
        Process todos with intelligent analysis.
        
        Args:
            todos: List of todo items in standard TodoWrite format
            analysis_level: 'basic', 'priority', 'dependency', 'effort', or 'full'
            
        Returns:
            Enhanced todos with analysis results
        """
        if not todos:
            return {'todos': [], 'analysis': {}, 'recommendations': []}
        
        # Start with original todos (backward compatibility)
        enhanced_todos = copy.deepcopy(todos)
        analysis_results = {}
        recommendations = []
        
        if not self.enable_intelligence or analysis_level == 'basic':
            return {
                'todos': enhanced_todos,
                'analysis': analysis_results,
                'recommendations': ['Intelligence features disabled - using basic TodoWrite functionality']
            }
        
        try:
            # Priority optimization
            if analysis_level in ['priority', 'full'] and self.priority_optimizer:
                optimized_todos = self.priority_optimizer.optimize_todo_priorities(enhanced_todos)
                enhanced_todos = optimized_todos
                analysis_results['priority_optimization'] = True
                recommendations.append("Tasks optimized using intelligent priority analysis")
            
            # Dependency mapping
            if analysis_level in ['dependency', 'full'] and self.dependency_mapper:
                dependency_graph = self.dependency_mapper.map_dependencies(enhanced_todos)
                self._dependency_graph = dependency_graph
                
                # Apply dependency-based ordering
                if dependency_graph.execution_order:
                    ordered_todos = []
                    for task_id in dependency_graph.execution_order:
                        todo = next((t for t in enhanced_todos if t['id'] == task_id), None)
                        if todo:
                            todo['execution_order'] = len(ordered_todos) + 1
                            ordered_todos.append(todo)
                    enhanced_todos = ordered_todos
                
                analysis_results['dependency_analysis'] = {
                    'total_dependencies': len(dependency_graph.dependencies),
                    'cycles_detected': len(dependency_graph.cycles),
                    'parallel_groups': len(dependency_graph.parallel_groups),
                    'execution_order_available': bool(dependency_graph.execution_order)
                }
                
                if dependency_graph.cycles:
                    recommendations.append(f"⚠️ Detected {len(dependency_graph.cycles)} circular dependencies")
                if dependency_graph.parallel_groups:
                    recommendations.append(f"✅ Found {len(dependency_graph.parallel_groups)} groups of parallelizable tasks")
            
            # Effort estimation
            if analysis_level in ['effort', 'full'] and self.effort_estimator:
                batch_analysis = self.effort_estimator.estimate_batch_effort(enhanced_todos)
                self._effort_estimates = {est.task_id: est for est in batch_analysis['individual_estimates']}
                
                # Add effort information to todos
                for todo in enhanced_todos:
                    task_id = todo.get('id')
                    if task_id in self._effort_estimates:
                        estimate = self._effort_estimates[task_id]
                        todo['effort_estimate'] = {
                            'time_minutes': estimate.estimated_time_minutes,
                            'tokens': estimate.estimated_tokens,
                            'complexity': estimate.complexity_level,
                            'confidence': estimate.confidence_score,
                            'sessions_needed': estimate.session_count_estimate,
                            'breakdown_recommended': estimate.breakdown_recommended
                        }
                
                analysis_results['effort_analysis'] = batch_analysis['efficiency_metrics']
                analysis_results['session_plan'] = batch_analysis['recommended_session_plan']
                
                # Add effort-based recommendations
                recommendations.extend(batch_analysis['batch_recommendations'])
                
                total_time = batch_analysis['total_estimated_time_minutes']
                if total_time > 480:  # More than 8 hours
                    recommendations.append(f"⏰ Total estimated time: {total_time // 60}h {total_time % 60}m - consider multi-day planning")
            
            # Integration with orchestration system
            if analysis_level == 'full' and self.orchestrator:
                # Check for large tasks that need orchestration
                large_tasks = [todo for todo in enhanced_todos 
                             if todo.get('effort_estimate', {}).get('breakdown_recommended', False)]
                
                if large_tasks:
                    analysis_results['orchestration_candidates'] = len(large_tasks)
                    recommendations.append(f"🎯 {len(large_tasks)} tasks recommended for orchestrated breakdown")
            
            self._last_analysis = {
                'timestamp': datetime.now(),
                'analysis_level': analysis_level,
                'todos_count': len(enhanced_todos),
                'analysis_results': analysis_results
            }
            
        except Exception as e:
            recommendations.append(f"⚠️ Intelligence analysis partially failed: {str(e)}")
            # Continue with basic todos if intelligence fails
        
        return {
            'todos': enhanced_todos,
            'analysis': analysis_results,
            'recommendations': recommendations
        }
    
    def get_next_task_recommendation(self, todos: List[Dict[str, Any]], 
                                   context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Get intelligent recommendation for next task to work on.
        
        Args:
            todos: Current todo list
            context: Optional context (time available, session type, etc.)
            
        Returns:
            Recommended task with reasoning
        """
        if not todos or not self.enable_intelligence:
            # Fallback to first pending task
            pending_todos = [t for t in todos if t.get('status') == 'pending']
            return pending_todos[0] if pending_todos else None
        
        try:
            # Process todos if not already analyzed
            if not self._last_analysis or self._last_analysis['todos_count'] != len(todos):
                self.process_todos(todos, 'full')
            
            # Filter to pending tasks
            pending_todos = [t for t in todos if t.get('status') == 'pending']
            if not pending_todos:
                return None
            
            # Apply context-based filtering
            if context:
                time_available = context.get('time_minutes', 120)  # Default 2 hours
                token_budget = context.get('token_budget', 15000)  # Default normal session
                
                # Filter tasks that fit within time/token constraints
                suitable_todos = []
                for todo in pending_todos:
                    effort = todo.get('effort_estimate', {})
                    if (effort.get('time_minutes', 60) <= time_available and 
                        effort.get('tokens', 5000) <= token_budget):
                        suitable_todos.append(todo)
                
                if suitable_todos:
                    pending_todos = suitable_todos
            
            # Get highest priority task
            if self.priority_optimizer:
                # Use intelligent priority score
                best_todo = max(pending_todos, 
                              key=lambda t: t.get('intelligent_priority_score', 0))
            else:
                # Fallback to manual priority
                priority_order = {'high': 3, 'medium': 2, 'low': 1}
                best_todo = max(pending_todos,
                              key=lambda t: priority_order.get(t.get('priority', 'medium'), 2))
            
            # Add recommendation reasoning
            reasoning = []
            if 'intelligent_priority_score' in best_todo:
                score = best_todo['intelligent_priority_score']
                reasoning.append(f"Highest intelligent priority score: {score:.3f}")
            
            if 'effort_estimate' in best_todo:
                effort = best_todo['effort_estimate']
                reasoning.append(f"Estimated effort: {effort['time_minutes']}min, {effort['complexity']} complexity")
            
            if 'execution_order' in best_todo:
                reasoning.append(f"Optimal execution order: #{best_todo['execution_order']}")
            
            # Add context to recommendation
            recommendation = copy.deepcopy(best_todo)
            recommendation['recommendation_reasoning'] = reasoning
            recommendation['recommended_at'] = datetime.now().isoformat()
            
            return recommendation
            
        except Exception as e:
            # Fallback to simple selection
            pending_todos = [t for t in todos if t.get('status') == 'pending']
            if pending_todos:
                return pending_todos[0]
            return None
    
    def generate_session_plan(self, todos: List[Dict[str, Any]], 
                            session_constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate optimal session execution plan.
        
        Args:
            todos: Todo list to plan
            session_constraints: Time, token, and other constraints
            
        Returns:
            Detailed session plan
        """
        if not self.enable_intelligence or not self.effort_estimator:
            return {
                'error': 'Session planning requires effort estimation capabilities',
                'fallback': 'Use manual session planning'
            }
        
        try:
            # Get effort analysis
            batch_analysis = self.effort_estimator.estimate_batch_effort(todos)
            
            # Apply constraints if provided
            constraints = session_constraints or {}
            max_session_time = constraints.get('max_session_minutes', 150)
            max_tokens_per_session = constraints.get('max_tokens', 15000)
            preferred_session_count = constraints.get('preferred_sessions', None)
            
            # Generate optimized plan
            session_plan = batch_analysis['recommended_session_plan']
            
            # Adjust plan based on constraints
            if preferred_session_count and len(session_plan) != preferred_session_count:
                # Redistribute tasks to match preferred session count
                session_plan = self._redistribute_sessions(session_plan, preferred_session_count)
            
            # Add session recommendations
            for session in session_plan:
                session.prerequisites = self._get_session_prerequisites(session, todos)
                session.outcomes = self._get_session_outcomes(session, todos)
            
            return {
                'session_plan': session_plan,
                'total_estimated_time': batch_analysis['total_estimated_time_minutes'],
                'total_estimated_tokens': batch_analysis['total_estimated_tokens'],
                'efficiency_metrics': batch_analysis['efficiency_metrics'],
                'recommendations': batch_analysis['batch_recommendations']
            }
            
        except Exception as e:
            return {
                'error': f'Session planning failed: {str(e)}',
                'fallback': 'Use manual session planning'
            }
    
    def get_dependency_insights(self, todos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get insights about task dependencies."""
        if not self.enable_intelligence or not self.dependency_mapper:
            return {'error': 'Dependency analysis not available'}
        
        try:
            if not self._dependency_graph:
                self._dependency_graph = self.dependency_mapper.map_dependencies(todos)
            
            summary = self.dependency_mapper.get_dependency_summary(self._dependency_graph)
            suggestions = self.dependency_mapper.suggest_dependency_resolution(self._dependency_graph)
            
            return {
                'summary': summary,
                'suggestions': suggestions,
                'dependency_graph': self._dependency_graph
            }
            
        except Exception as e:
            return {'error': f'Dependency analysis failed: {str(e)}'}
    
    def explain_task_priority(self, task_id: str, todos: List[Dict[str, Any]]) -> str:
        """Get explanation of why a task has its priority."""
        if not self.enable_intelligence or not self.priority_optimizer:
            return "Priority explanation requires intelligent analysis features"
        
        try:
            todo = next((t for t in todos if t.get('id') == task_id), None)
            if not todo:
                return f"Task {task_id} not found"
            
            return self.priority_optimizer.get_priority_explanation(todo)
            
        except Exception as e:
            return f"Priority explanation failed: {str(e)}"
    
    def _redistribute_sessions(self, session_plan: List, target_count: int) -> List:
        """Redistribute tasks across target number of sessions."""
        # Simple redistribution - can be enhanced
        if target_count <= 0 or not session_plan:
            return session_plan
        
        # Flatten all tasks
        all_tasks = []
        for session in session_plan:
            all_tasks.extend(session.tasks)
        
        # Create new sessions
        tasks_per_session = len(all_tasks) // target_count
        remainder = len(all_tasks) % target_count
        
        new_sessions = []
        task_idx = 0
        
        for i in range(target_count):
            session_size = tasks_per_session + (1 if i < remainder else 0)
            session_tasks = all_tasks[task_idx:task_idx + session_size]
            
            # Create simplified session (would need more sophisticated logic in practice)
            from .effort_estimator import SessionPlan
            new_session = SessionPlan(
                session_number=i + 1,
                estimated_duration_minutes=90,  # Default
                estimated_tokens=10000,  # Default
                tasks=session_tasks,
                session_type='normal',
                prerequisites=[],
                outcomes=[]
            )
            new_sessions.append(new_session)
            task_idx += session_size
        
        return new_sessions
    
    def _get_session_prerequisites(self, session, todos: List[Dict[str, Any]]) -> List[str]:
        """Get prerequisites for a session."""
        # Simplified implementation
        return ["Ensure development environment is ready", "Review session goals"]
    
    def _get_session_outcomes(self, session, todos: List[Dict[str, Any]]) -> List[str]:
        """Get expected outcomes for a session."""
        # Simplified implementation
        task_count = len(session.tasks)
        return [f"Complete {task_count} tasks", "Update progress documentation"]
    
    def get_intelligence_status(self) -> Dict[str, Any]:
        """Get status of intelligence features."""
        return {
            'intelligence_enabled': self.enable_intelligence,
            'components_available': {
                'priority_optimizer': self.priority_optimizer is not None,
                'dependency_mapper': self.dependency_mapper is not None,
                'effort_estimator': self.effort_estimator is not None,
                'session_manager': self.session_manager is not None,
                'orchestrator': self.orchestrator is not None
            },
            'last_analysis': self._last_analysis
        }