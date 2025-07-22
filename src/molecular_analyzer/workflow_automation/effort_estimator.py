"""
Effort Estimation Engine

Token budget-aware effort estimation system that provides intelligent estimates
for task completion time and complexity while integrating with session management.
"""

import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import math

# Add path to workflow automation session management
lab_path = Path(__file__).parent.parent.parent.parent / "Lab" / "Project Management" / "workflow-automation" / "src"
if str(lab_path) not in sys.path:
    sys.path.insert(0, str(lab_path))

try:
    from session_management.token_efficient_task_manager import TokenEfficientTaskManager
    from session_management.session_continuity_manager import SessionContinuityManager
except ImportError:
    # Graceful fallback if session management not available
    TokenEfficientTaskManager = None
    SessionContinuityManager = None


@dataclass
class EffortEstimate:
    """Represents effort estimation for a task."""
    task_id: str
    estimated_time_minutes: int
    estimated_tokens: int
    complexity_level: str  # 'trivial', 'simple', 'moderate', 'complex', 'very_complex'
    confidence_score: float  # 0.0 to 1.0
    breakdown_recommended: bool
    session_count_estimate: int
    factors: Dict[str, float]
    recommendations: List[str]


@dataclass
class SessionPlan:
    """Represents a session execution plan."""
    session_number: int
    estimated_duration_minutes: int
    estimated_tokens: int
    tasks: List[str]
    session_type: str  # 'quick', 'normal', 'extended', 'complex'
    prerequisites: List[str]
    outcomes: List[str]


class EffortEstimationEngine:
    """
    Token budget-aware effort estimation system.
    
    Provides intelligent estimates for task completion considering token usage,
    complexity analysis, and historical patterns while integrating with session management.
    """
    
    def __init__(self, project_path: Optional[str] = None):
        """Initialize the effort estimation engine."""
        self.project_path = project_path or os.getcwd()
        
        # Initialize session management integration
        self.token_manager = None
        self.session_manager = None
        
        if TokenEfficientTaskManager:
            try:
                self.token_manager = TokenEfficientTaskManager(self.project_path)
            except Exception:
                pass
        
        if SessionContinuityManager:
            try:
                self.session_manager = SessionContinuityManager(self.project_path)
            except Exception:
                pass
        
        # Token budget thresholds
        self.token_budgets = {
            'quick_session': 5000,      # 15-30 minutes
            'normal_session': 15000,    # 1-2 hours
            'extended_session': 25000,  # 2-3 hours
            'complex_session': 35000    # 3+ hours with breaks
        }
        
        # Complexity thresholds
        self.complexity_thresholds = {
            'trivial': 500,      # Very quick tasks
            'simple': 2000,      # Simple tasks
            'moderate': 8000,    # Moderate complexity
            'complex': 20000,    # Complex tasks
            'very_complex': 35000 # Very complex tasks
        }
        
        # Effort factors and their weights
        self.effort_factors = {
            'task_type': {
                'create': 1.5,
                'implement': 1.8,
                'build': 1.6,
                'develop': 1.7,
                'design': 1.4,
                'update': 0.8,
                'modify': 0.9,
                'fix': 0.7,
                'test': 0.6,
                'document': 0.5,
                'review': 0.4,
                'check': 0.3
            },
            'complexity_keywords': {
                'algorithm': 1.8,
                'optimization': 1.6,
                'integration': 1.4,
                'architecture': 1.7,
                'framework': 1.5,
                'system': 1.3,
                'api': 1.2,
                'database': 1.4,
                'security': 1.6,
                'performance': 1.5,
                'ui': 1.1,
                'frontend': 1.1,
                'backend': 1.3,
                'full-stack': 1.8
            },
            'scope_indicators': {
                'multiple': 1.4,
                'all': 1.5,
                'entire': 1.6,
                'complete': 1.3,
                'comprehensive': 1.7,
                'full': 1.4,
                'major': 1.5,
                'minor': 0.8,
                'small': 0.7,
                'quick': 0.6,
                'simple': 0.7
            }
        }
        
        # Time estimation base rates (minutes per token)
        self.time_rates = {
            'implementation': 0.12,  # 12 seconds per token
            'documentation': 0.06,   # 6 seconds per token
            'testing': 0.08,         # 8 seconds per token
            'review': 0.04,          # 4 seconds per token
            'debugging': 0.15,       # 15 seconds per token
            'research': 0.10         # 10 seconds per token
        }
    
    def estimate_effort(self, todo: Dict[str, Any]) -> EffortEstimate:
        """
        Estimate effort for a single task.
        
        Args:
            todo: Task dictionary with content and metadata
            
        Returns:
            Comprehensive effort estimate
        """
        content = todo.get('content', '')
        
        # Get token estimation from token manager if available
        token_estimate = self._estimate_tokens(content)
        
        # Calculate effort factors
        effort_factors = self._calculate_effort_factors(content)
        
        # Estimate time
        time_estimate = self._estimate_time(content, token_estimate, effort_factors)
        
        # Determine complexity level
        complexity_level = self._determine_complexity_level(token_estimate, effort_factors)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(content, token_estimate, effort_factors)
        
        # Determine if breakdown is recommended
        breakdown_recommended = token_estimate > self.complexity_thresholds['moderate']
        
        # Estimate session count
        session_count = self._estimate_session_count(token_estimate, time_estimate)
        
        # Generate recommendations
        recommendations = self._generate_effort_recommendations(
            content, token_estimate, time_estimate, complexity_level
        )
        
        return EffortEstimate(
            task_id=todo.get('id', 'unknown'),
            estimated_time_minutes=time_estimate,
            estimated_tokens=token_estimate,
            complexity_level=complexity_level,
            confidence_score=confidence_score,
            breakdown_recommended=breakdown_recommended,
            session_count_estimate=session_count,
            factors=effort_factors,
            recommendations=recommendations
        )
    
    def estimate_batch_effort(self, todos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Estimate effort for a batch of tasks.
        
        Args:
            todos: List of task dictionaries
            
        Returns:
            Batch effort analysis with session planning
        """
        individual_estimates = [self.estimate_effort(todo) for todo in todos]
        
        # Calculate totals
        total_time = sum(est.estimated_time_minutes for est in individual_estimates)
        total_tokens = sum(est.estimated_tokens for est in individual_estimates)
        
        # Analyze complexity distribution
        complexity_distribution = {}
        for est in individual_estimates:
            level = est.complexity_level
            complexity_distribution[level] = complexity_distribution.get(level, 0) + 1
        
        # Generate session plan
        session_plan = self._generate_session_plan(individual_estimates)
        
        # Calculate efficiency metrics
        efficiency_metrics = self._calculate_batch_efficiency_metrics(individual_estimates)
        
        return {
            'individual_estimates': individual_estimates,
            'total_estimated_time_minutes': total_time,
            'total_estimated_tokens': total_tokens,
            'complexity_distribution': complexity_distribution,
            'recommended_session_plan': session_plan,
            'efficiency_metrics': efficiency_metrics,
            'batch_recommendations': self._generate_batch_recommendations(individual_estimates)
        }
    
    def _estimate_tokens(self, content: str) -> int:
        """Estimate token usage for task content."""
        if self.token_manager:
            try:
                complexity_analysis = self.token_manager.analyze_task_complexity(content)
                return complexity_analysis.get('estimated_tokens', self._fallback_token_estimate(content))
            except Exception:
                pass
        
        return self._fallback_token_estimate(content)
    
    def _fallback_token_estimate(self, content: str) -> int:
        """Fallback token estimation when token manager is not available."""
        # Simple heuristic based on content length and complexity indicators
        base_tokens = len(content.split()) * 50  # Base estimate
        
        # Adjust based on complexity keywords
        complexity_multiplier = 1.0
        for keyword, multiplier in self.effort_factors['complexity_keywords'].items():
            if keyword in content.lower():
                complexity_multiplier = max(complexity_multiplier, multiplier)
        
        # Adjust based on task type
        task_multiplier = 1.0
        for task_type, multiplier in self.effort_factors['task_type'].items():
            if task_type in content.lower():
                task_multiplier = max(task_multiplier, multiplier)
        
        estimated_tokens = int(base_tokens * complexity_multiplier * task_multiplier)
        return max(500, min(50000, estimated_tokens))  # Clamp to reasonable range
    
    def _calculate_effort_factors(self, content: str) -> Dict[str, float]:
        """Calculate various effort factors for the task."""
        content_lower = content.lower()
        factors = {}
        
        # Task type factor
        task_type_score = 1.0
        for task_type, multiplier in self.effort_factors['task_type'].items():
            if task_type in content_lower:
                task_type_score = max(task_type_score, multiplier)
        factors['task_type'] = task_type_score
        
        # Complexity factor
        complexity_score = 1.0
        for keyword, multiplier in self.effort_factors['complexity_keywords'].items():
            if keyword in content_lower:
                complexity_score = max(complexity_score, multiplier)
        factors['complexity'] = complexity_score
        
        # Scope factor
        scope_score = 1.0
        for indicator, multiplier in self.effort_factors['scope_indicators'].items():
            if indicator in content_lower:
                scope_score = max(scope_score, multiplier)
        factors['scope'] = scope_score
        
        # Uncertainty factor (based on vague language)
        uncertainty_keywords = ['maybe', 'might', 'could', 'possibly', 'perhaps', 'investigate']
        uncertainty_count = sum(1 for keyword in uncertainty_keywords if keyword in content_lower)
        factors['uncertainty'] = 1.0 + (uncertainty_count * 0.2)
        
        # Integration factor (based on integration keywords)
        integration_keywords = ['integrate', 'connect', 'merge', 'combine', 'link', 'sync']
        integration_count = sum(1 for keyword in integration_keywords if keyword in content_lower)
        factors['integration'] = 1.0 + (integration_count * 0.3)
        
        return factors
    
    def _estimate_time(self, content: str, token_estimate: int, effort_factors: Dict[str, float]) -> int:
        """Estimate time in minutes for task completion."""
        content_lower = content.lower()
        
        # Determine primary task type for time rate
        primary_rate = self.time_rates['implementation']  # Default
        for task_type, rate in self.time_rates.items():
            if task_type in content_lower:
                primary_rate = rate
                break
        
        # Base time from tokens
        base_time_minutes = (token_estimate * primary_rate) / 60
        
        # Apply effort factors
        total_multiplier = 1.0
        for factor_name, factor_value in effort_factors.items():
            if factor_name in ['task_type', 'complexity', 'scope']:
                total_multiplier *= factor_value
            elif factor_name in ['uncertainty', 'integration']:
                total_multiplier *= factor_value
        
        # Apply overhead for context switching and setup
        overhead_multiplier = 1.2  # 20% overhead
        
        final_time = int(base_time_minutes * total_multiplier * overhead_multiplier)
        
        # Clamp to reasonable range
        return max(5, min(480, final_time))  # 5 minutes to 8 hours
    
    def _determine_complexity_level(self, token_estimate: int, effort_factors: Dict[str, float]) -> str:
        """Determine complexity level based on tokens and factors."""
        # Adjust token estimate based on effort factors
        adjusted_tokens = token_estimate * effort_factors.get('complexity', 1.0)
        
        if adjusted_tokens <= self.complexity_thresholds['trivial']:
            return 'trivial'
        elif adjusted_tokens <= self.complexity_thresholds['simple']:
            return 'simple'
        elif adjusted_tokens <= self.complexity_thresholds['moderate']:
            return 'moderate'
        elif adjusted_tokens <= self.complexity_thresholds['complex']:
            return 'complex'
        else:
            return 'very_complex'
    
    def _calculate_confidence_score(self, content: str, token_estimate: int, 
                                  effort_factors: Dict[str, float]) -> float:
        """Calculate confidence score for the estimate."""
        base_confidence = 0.7
        
        # Reduce confidence for high uncertainty
        uncertainty_factor = effort_factors.get('uncertainty', 1.0)
        confidence_adjustment = -0.1 * (uncertainty_factor - 1.0)
        
        # Reduce confidence for very large tasks
        if token_estimate > self.complexity_thresholds['complex']:
            confidence_adjustment -= 0.2
        
        # Reduce confidence for vague descriptions
        if len(content.split()) < 5:
            confidence_adjustment -= 0.15
        
        # Increase confidence for specific tasks
        specific_keywords = ['fix', 'update', 'add', 'remove', 'modify']
        if any(keyword in content.lower() for keyword in specific_keywords):
            confidence_adjustment += 0.1
        
        final_confidence = base_confidence + confidence_adjustment
        return max(0.1, min(1.0, final_confidence))
    
    def _estimate_session_count(self, token_estimate: int, time_estimate: int) -> int:
        """Estimate number of sessions needed for task completion."""
        # Consider both token budget and time constraints
        sessions_by_tokens = math.ceil(token_estimate / self.token_budgets['normal_session'])
        sessions_by_time = math.ceil(time_estimate / 120)  # 2-hour sessions
        
        # Take the maximum, but consider practical limits
        estimated_sessions = max(sessions_by_tokens, sessions_by_time)
        
        return max(1, min(10, estimated_sessions))  # 1 to 10 sessions
    
    def _generate_effort_recommendations(self, content: str, token_estimate: int,
                                       time_estimate: int, complexity_level: str) -> List[str]:
        """Generate recommendations based on effort analysis."""
        recommendations = []
        
        # Time-based recommendations
        if time_estimate > 240:  # More than 4 hours
            recommendations.append("Large task: Consider breaking into smaller subtasks")
        elif time_estimate < 15:  # Less than 15 minutes
            recommendations.append("Quick task: Good for filling short sessions")
        
        # Token-based recommendations
        if token_estimate > self.token_budgets['normal_session']:
            recommendations.append("High token usage: Plan for multiple sessions or use token-efficient approach")
        
        # Complexity-based recommendations
        if complexity_level in ['complex', 'very_complex']:
            recommendations.append("Complex task: Consider pair programming or additional research time")
        elif complexity_level == 'trivial':
            recommendations.append("Simple task: Good for warm-up or quick wins")
        
        # Content-specific recommendations
        content_lower = content.lower()
        if 'integration' in content_lower:
            recommendations.append("Integration task: Allow extra time for debugging and testing")
        if 'new' in content_lower or 'create' in content_lower:
            recommendations.append("New development: Consider prototype first approach")
        if 'refactor' in content_lower:
            recommendations.append("Refactoring: Ensure comprehensive tests before starting")
        
        return recommendations
    
    def _generate_session_plan(self, estimates: List[EffortEstimate]) -> List[SessionPlan]:
        """Generate optimal session plan for batch of tasks."""
        session_plans = []
        current_session_tokens = 0
        current_session_time = 0
        current_session_tasks = []
        session_number = 1
        
        # Sort tasks by complexity and dependencies
        sorted_estimates = sorted(estimates, key=lambda x: (
            x.complexity_level == 'trivial',  # Simple tasks first
            -x.estimated_tokens  # Then by token count (larger first)
        ))
        
        for estimate in sorted_estimates:
            # Check if task fits in current session
            would_exceed_tokens = (current_session_tokens + estimate.estimated_tokens > 
                                 self.token_budgets['normal_session'])
            would_exceed_time = (current_session_time + estimate.estimated_time_minutes > 150)
            
            if (would_exceed_tokens or would_exceed_time) and current_session_tasks:
                # Finalize current session
                session_type = self._determine_session_type(current_session_tokens, current_session_time)
                session_plans.append(SessionPlan(
                    session_number=session_number,
                    estimated_duration_minutes=current_session_time,
                    estimated_tokens=current_session_tokens,
                    tasks=current_session_tasks.copy(),
                    session_type=session_type,
                    prerequisites=[],
                    outcomes=[]
                ))
                
                # Start new session
                session_number += 1
                current_session_tokens = 0
                current_session_time = 0
                current_session_tasks = []
            
            # Add task to current session
            current_session_tokens += estimate.estimated_tokens
            current_session_time += estimate.estimated_time_minutes
            current_session_tasks.append(estimate.task_id)
        
        # Finalize last session if there are tasks
        if current_session_tasks:
            session_type = self._determine_session_type(current_session_tokens, current_session_time)
            session_plans.append(SessionPlan(
                session_number=session_number,
                estimated_duration_minutes=current_session_time,
                estimated_tokens=current_session_tokens,
                tasks=current_session_tasks,
                session_type=session_type,
                prerequisites=[],
                outcomes=[]
            ))
        
        return session_plans
    
    def _determine_session_type(self, tokens: int, time_minutes: int) -> str:
        """Determine session type based on resource usage."""
        if tokens <= self.token_budgets['quick_session'] and time_minutes <= 30:
            return 'quick'
        elif tokens <= self.token_budgets['normal_session'] and time_minutes <= 120:
            return 'normal'
        elif tokens <= self.token_budgets['extended_session'] and time_minutes <= 180:
            return 'extended'
        else:
            return 'complex'
    
    def _calculate_batch_efficiency_metrics(self, estimates: List[EffortEstimate]) -> Dict[str, Any]:
        """Calculate efficiency metrics for batch of tasks."""
        if not estimates:
            return {}
        
        total_time = sum(est.estimated_time_minutes for est in estimates)
        total_tokens = sum(est.estimated_tokens for est in estimates)
        
        # Calculate averages
        avg_time_per_task = total_time / len(estimates)
        avg_tokens_per_task = total_tokens / len(estimates)
        avg_confidence = sum(est.confidence_score for est in estimates) / len(estimates)
        
        # Calculate efficiency ratios
        time_per_token = total_time / total_tokens if total_tokens > 0 else 0
        
        # Analyze complexity distribution
        complexity_counts = {}
        for est in estimates:
            level = est.complexity_level
            complexity_counts[level] = complexity_counts.get(level, 0) + 1
        
        # Calculate breakdown ratio
        breakdown_needed = sum(1 for est in estimates if est.breakdown_recommended)
        breakdown_ratio = breakdown_needed / len(estimates)
        
        return {
            'average_time_per_task_minutes': round(avg_time_per_task, 1),
            'average_tokens_per_task': round(avg_tokens_per_task, 0),
            'average_confidence_score': round(avg_confidence, 2),
            'time_per_token_ratio': round(time_per_token, 4),
            'complexity_distribution': complexity_counts,
            'breakdown_ratio': round(breakdown_ratio, 2),
            'estimated_sessions_needed': len(estimates) // 3 + 1  # Rough estimate
        }
    
    def _generate_batch_recommendations(self, estimates: List[EffortEstimate]) -> List[str]:
        """Generate recommendations for batch of tasks."""
        recommendations = []
        
        total_time = sum(est.estimated_time_minutes for est in estimates)
        complex_tasks = [est for est in estimates if est.complexity_level in ['complex', 'very_complex']]
        
        # Time-based recommendations
        if total_time > 480:  # More than 8 hours
            recommendations.append("Large batch: Consider spreading across multiple days")
        
        # Complexity-based recommendations
        if len(complex_tasks) > len(estimates) * 0.5:
            recommendations.append("Many complex tasks: Consider interspersing with simpler tasks")
        
        # Token efficiency recommendations
        high_token_tasks = [est for est in estimates if est.estimated_tokens > 15000]
        if high_token_tasks:
            recommendations.append(f"{len(high_token_tasks)} tasks need token-efficient approach")
        
        # Session planning recommendations
        if len(estimates) > 5:
            recommendations.append("Large task list: Use session planning for optimal execution")
        
        return recommendations
    
    def get_effort_summary(self, estimate: EffortEstimate) -> str:
        """Get human-readable summary of effort estimate."""
        summary = f"Task: {estimate.task_id}\n"
        summary += f"Estimated Time: {estimate.estimated_time_minutes} minutes\n"
        summary += f"Estimated Tokens: {estimate.estimated_tokens}\n"
        summary += f"Complexity: {estimate.complexity_level}\n"
        summary += f"Confidence: {estimate.confidence_score:.1%}\n"
        summary += f"Sessions Needed: {estimate.session_count_estimate}\n"
        
        if estimate.breakdown_recommended:
            summary += "⚠️ Breakdown recommended for this complex task\n"
        
        if estimate.recommendations:
            summary += f"Recommendations: {', '.join(estimate.recommendations)}\n"
        
        return summary