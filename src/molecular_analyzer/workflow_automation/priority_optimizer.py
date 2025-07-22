"""
Dynamic Priority Optimizer

Integrates with TokenEfficientTaskManager to provide intelligent task prioritization
while maintaining backward compatibility with existing TodoWrite functionality.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

# Add path to workflow automation session management
lab_path = Path(__file__).parent.parent.parent.parent / "Lab" / "Project Management" / "workflow-automation" / "src"
if str(lab_path) not in sys.path:
    sys.path.insert(0, str(lab_path))

try:
    from session_management.token_efficient_task_manager import TokenEfficientTaskManager
    from session_management.intelligent_task_orchestrator import IntelligentTaskOrchestrator
except ImportError:
    # Graceful fallback if session management not available
    TokenEfficientTaskManager = None
    IntelligentTaskOrchestrator = None


class DynamicPriorityOptimizer:
    """
    Intelligent task priority optimization using token efficiency analysis.
    
    Provides smart prioritization while maintaining full backward compatibility
    with existing TodoWrite workflows.
    """
    
    def __init__(self, project_path: Optional[str] = None):
        """Initialize the priority optimizer with optional token management."""
        self.project_path = project_path or os.getcwd()
        
        # Initialize token management if available
        self.token_manager = None
        self.orchestrator = None
        
        if TokenEfficientTaskManager:
            try:
                self.token_manager = TokenEfficientTaskManager(self.project_path)
                if IntelligentTaskOrchestrator:
                    self.orchestrator = IntelligentTaskOrchestrator(self.project_path)
            except Exception:
                # Graceful fallback if initialization fails
                pass
        
        # Priority scoring weights
        self.priority_weights = {
            'urgency': 0.3,
            'impact': 0.25,
            'effort': 0.2,
            'dependencies': 0.15,
            'token_efficiency': 0.1
        }
        
        # Task complexity thresholds
        self.complexity_thresholds = {
            'simple': 1000,      # tokens
            'moderate': 5000,    # tokens
            'complex': 15000,    # tokens
            'very_complex': 25000 # tokens
        }
    
    def optimize_todo_priorities(self, todos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Optimize todo list priorities using intelligent analysis.
        
        Args:
            todos: List of todo items with standard TodoWrite format
            
        Returns:
            Optimized todo list with enhanced priority scores and recommendations
        """
        if not todos:
            return todos
        
        # Create enhanced todos with intelligent scoring
        enhanced_todos = []
        
        for todo in todos:
            enhanced_todo = todo.copy()
            
            # Calculate intelligent priority score
            priority_analysis = self._analyze_task_priority(todo)
            enhanced_todo['priority_analysis'] = priority_analysis
            
            # Add token efficiency analysis if available
            if self.token_manager:
                token_analysis = self._analyze_token_efficiency(todo)
                enhanced_todo['token_analysis'] = token_analysis
            
            # Calculate final priority score
            final_score = self._calculate_final_priority_score(priority_analysis, enhanced_todo.get('token_analysis'))
            enhanced_todo['intelligent_priority_score'] = final_score
            
            # Add recommendations
            recommendations = self._generate_task_recommendations(todo, priority_analysis)
            enhanced_todo['recommendations'] = recommendations
            
            enhanced_todos.append(enhanced_todo)
        
        # Sort by intelligent priority score (higher is more important)
        enhanced_todos.sort(key=lambda x: x.get('intelligent_priority_score', 0), reverse=True)
        
        return enhanced_todos
    
    def _analyze_task_priority(self, todo: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze task priority using multiple factors."""
        content = todo.get('content', '')
        priority = todo.get('priority', 'medium')
        status = todo.get('status', 'pending')
        
        analysis = {
            'urgency_score': self._calculate_urgency_score(todo),
            'impact_score': self._calculate_impact_score(todo),
            'effort_score': self._calculate_effort_score(todo),
            'dependency_score': self._calculate_dependency_score(todo),
            'context_relevance': self._calculate_context_relevance(todo)
        }
        
        return analysis
    
    def _analyze_token_efficiency(self, todo: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze token efficiency if token manager is available."""
        if not self.token_manager:
            return None
        
        content = todo.get('content', '')
        
        try:
            # Estimate task complexity
            complexity_analysis = self.token_manager.analyze_task_complexity(content)
            
            # Get breakdown strategy if task is complex
            breakdown_strategy = None
            if complexity_analysis.get('estimated_tokens', 0) > self.complexity_thresholds['moderate']:
                breakdown_strategy = self.token_manager.get_breakdown_strategy(content)
            
            return {
                'complexity_analysis': complexity_analysis,
                'breakdown_strategy': breakdown_strategy,
                'token_efficiency_score': self._calculate_token_efficiency_score(complexity_analysis)
            }
        except Exception:
            return None
    
    def _calculate_urgency_score(self, todo: Dict[str, Any]) -> float:
        """Calculate urgency score based on priority and keywords."""
        priority = todo.get('priority', 'medium')
        content = todo.get('content', '').lower()
        
        # Base score from priority
        priority_scores = {'high': 0.8, 'medium': 0.5, 'low': 0.2}
        base_score = priority_scores.get(priority, 0.5)
        
        # Boost for urgent keywords
        urgent_keywords = ['critical', 'urgent', 'asap', 'immediately', 'blocker', 'breaking']
        keyword_boost = sum(0.1 for keyword in urgent_keywords if keyword in content)
        
        # Boost for status
        status_boost = 0.2 if todo.get('status') == 'in_progress' else 0
        
        return min(1.0, base_score + keyword_boost + status_boost)
    
    def _calculate_impact_score(self, todo: Dict[str, Any]) -> float:
        """Calculate impact score based on content analysis."""
        content = todo.get('content', '').lower()
        
        # High impact keywords
        high_impact = ['architecture', 'core', 'framework', 'system', 'critical', 'security']
        medium_impact = ['feature', 'enhancement', 'optimization', 'integration']
        low_impact = ['documentation', 'cleanup', 'refactor', 'test']
        
        if any(keyword in content for keyword in high_impact):
            return 0.9
        elif any(keyword in content for keyword in medium_impact):
            return 0.6
        elif any(keyword in content for keyword in low_impact):
            return 0.3
        else:
            return 0.5
    
    def _calculate_effort_score(self, todo: Dict[str, Any]) -> float:
        """Calculate effort score (lower effort = higher score for prioritization)."""
        content = todo.get('content', '').lower()
        
        # High effort indicators (lower score)
        high_effort = ['implement', 'create', 'build', 'develop', 'design']
        medium_effort = ['update', 'modify', 'enhance', 'integrate']
        low_effort = ['fix', 'check', 'verify', 'test', 'review']
        
        if any(keyword in content for keyword in high_effort):
            return 0.3  # High effort = lower priority score
        elif any(keyword in content for keyword in medium_effort):
            return 0.6
        elif any(keyword in content for keyword in low_effort):
            return 0.9  # Low effort = higher priority score
        else:
            return 0.5
    
    def _calculate_dependency_score(self, todo: Dict[str, Any]) -> float:
        """Calculate dependency score based on blocking potential."""
        content = todo.get('content', '').lower()
        
        # Dependency indicators
        blocking_keywords = ['setup', 'foundation', 'core', 'base', 'infrastructure']
        dependent_keywords = ['after', 'once', 'following', 'depends on']
        
        if any(keyword in content for keyword in blocking_keywords):
            return 0.9  # High priority for blocking tasks
        elif any(keyword in content for keyword in dependent_keywords):
            return 0.2  # Lower priority for dependent tasks
        else:
            return 0.5
    
    def _calculate_context_relevance(self, todo: Dict[str, Any]) -> float:
        """Calculate relevance to current project context."""
        content = todo.get('content', '').lower()
        
        # Current project keywords (molecular analyzer specific)
        project_keywords = ['molecular', 'analyzer', 'chemistry', 'streamlit', 'visualization']
        workflow_keywords = ['workflow', 'automation', 'todo', 'session', 'management']
        
        project_relevance = sum(0.1 for keyword in project_keywords if keyword in content)
        workflow_relevance = sum(0.1 for keyword in workflow_keywords if keyword in content)
        
        return min(1.0, project_relevance + workflow_relevance + 0.3)  # Base relevance
    
    def _calculate_token_efficiency_score(self, complexity_analysis: Dict[str, Any]) -> float:
        """Calculate token efficiency score."""
        if not complexity_analysis:
            return 0.5
        
        estimated_tokens = complexity_analysis.get('estimated_tokens', 1000)
        
        # Higher score for more token-efficient tasks
        if estimated_tokens < self.complexity_thresholds['simple']:
            return 0.9  # Very efficient
        elif estimated_tokens < self.complexity_thresholds['moderate']:
            return 0.7  # Moderately efficient
        elif estimated_tokens < self.complexity_thresholds['complex']:
            return 0.4  # Less efficient
        else:
            return 0.2  # Requires breakdown
    
    def _calculate_final_priority_score(self, priority_analysis: Dict[str, Any], 
                                      token_analysis: Optional[Dict[str, Any]] = None) -> float:
        """Calculate final weighted priority score."""
        score = 0.0
        
        # Standard priority factors
        score += priority_analysis.get('urgency_score', 0) * self.priority_weights['urgency']
        score += priority_analysis.get('impact_score', 0) * self.priority_weights['impact']
        score += priority_analysis.get('effort_score', 0) * self.priority_weights['effort']
        score += priority_analysis.get('dependency_score', 0) * self.priority_weights['dependencies']
        
        # Token efficiency factor (if available)
        if token_analysis:
            token_score = token_analysis.get('token_efficiency_score', 0.5)
            score += token_score * self.priority_weights['token_efficiency']
        else:
            # Use context relevance as fallback
            score += priority_analysis.get('context_relevance', 0.5) * self.priority_weights['token_efficiency']
        
        return round(score, 3)
    
    def _generate_task_recommendations(self, todo: Dict[str, Any], 
                                     priority_analysis: Dict[str, Any]) -> List[str]:
        """Generate intelligent recommendations for task execution."""
        recommendations = []
        content = todo.get('content', '')
        
        # Urgency-based recommendations
        if priority_analysis.get('urgency_score', 0) > 0.8:
            recommendations.append("High urgency: Consider prioritizing this task")
        
        # Effort-based recommendations
        if priority_analysis.get('effort_score', 0) < 0.4:
            recommendations.append("High effort task: Consider breaking down into smaller subtasks")
        
        # Dependency-based recommendations
        if priority_analysis.get('dependency_score', 0) > 0.8:
            recommendations.append("Blocking task: Complete this before dependent tasks")
        elif priority_analysis.get('dependency_score', 0) < 0.3:
            recommendations.append("Dependent task: Ensure prerequisites are complete")
        
        # Token efficiency recommendations
        if hasattr(self, 'token_analysis') and self.token_analysis:
            token_analysis = getattr(todo, 'token_analysis', {})
            if token_analysis.get('breakdown_strategy'):
                recommendations.append("Complex task: Token-efficient breakdown strategy available")
        
        return recommendations
    
    def get_priority_explanation(self, todo: Dict[str, Any]) -> str:
        """Get human-readable explanation of priority calculation."""
        if 'priority_analysis' not in todo:
            return "Standard priority based on user assignment"
        
        analysis = todo['priority_analysis']
        score = todo.get('intelligent_priority_score', 0)
        
        explanation = f"Priority Score: {score:.3f}\n"
        explanation += f"• Urgency: {analysis.get('urgency_score', 0):.2f}\n"
        explanation += f"• Impact: {analysis.get('impact_score', 0):.2f}\n"
        explanation += f"• Effort: {analysis.get('effort_score', 0):.2f}\n"
        explanation += f"• Dependencies: {analysis.get('dependency_score', 0):.2f}\n"
        
        if 'token_analysis' in todo:
            token_score = todo['token_analysis'].get('token_efficiency_score', 0)
            explanation += f"• Token Efficiency: {token_score:.2f}\n"
        
        return explanation
    
    def suggest_optimal_execution_order(self, todos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Suggest optimal execution order considering dependencies and efficiency."""
        if not todos:
            return todos
        
        # First optimize priorities
        optimized_todos = self.optimize_todo_priorities(todos)
        
        # Then apply dependency-aware ordering
        ordered_todos = self._apply_dependency_ordering(optimized_todos)
        
        # Add execution recommendations
        for i, todo in enumerate(ordered_todos):
            todo['execution_order'] = i + 1
            todo['execution_recommendations'] = self._get_execution_recommendations(todo, i, len(ordered_todos))
        
        return ordered_todos
    
    def _apply_dependency_ordering(self, todos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply dependency-aware ordering to optimized todos."""
        # Separate by dependency scores
        blocking_tasks = [t for t in todos if t.get('priority_analysis', {}).get('dependency_score', 0) > 0.7]
        normal_tasks = [t for t in todos if 0.3 <= t.get('priority_analysis', {}).get('dependency_score', 0) <= 0.7]
        dependent_tasks = [t for t in todos if t.get('priority_analysis', {}).get('dependency_score', 0) < 0.3]
        
        # Order: blocking first, then normal by score, then dependent
        ordered = []
        ordered.extend(sorted(blocking_tasks, key=lambda x: x.get('intelligent_priority_score', 0), reverse=True))
        ordered.extend(sorted(normal_tasks, key=lambda x: x.get('intelligent_priority_score', 0), reverse=True))
        ordered.extend(sorted(dependent_tasks, key=lambda x: x.get('intelligent_priority_score', 0), reverse=True))
        
        return ordered
    
    def _get_execution_recommendations(self, todo: Dict[str, Any], position: int, total: int) -> List[str]:
        """Get execution-specific recommendations based on position in queue."""
        recommendations = []
        
        if position == 0:
            recommendations.append("Execute first - highest priority or blocking task")
        elif position < total * 0.3:
            recommendations.append("Execute early - high priority task")
        elif position > total * 0.7:
            recommendations.append("Execute later - lower priority or dependent task")
        
        # Add timing recommendations
        if 'token_analysis' in todo:
            complexity = todo['token_analysis'].get('complexity_analysis', {})
            estimated_tokens = complexity.get('estimated_tokens', 0)
            
            if estimated_tokens > self.complexity_thresholds['complex']:
                recommendations.append("Consider breaking down before execution")
            elif estimated_tokens < self.complexity_thresholds['simple']:
                recommendations.append("Quick task - good for short sessions")
        
        return recommendations