"""
Integration Manager - Task 2.1.5

Integrates the quality prediction system with existing workflow automation,
providing seamless predictive intelligence capabilities.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

from .quality_predictor import QualityTrendAnalyzer, PredictiveRiskAssessment, QualityMetrics
from .quality_metrics_collector import QualityMetricsCollector, HistoricalMetricsManager
from .early_warning_system import EarlyWarningSystem


class QualityPredictionIntegrator:
    """
    Integrates quality prediction capabilities with existing workflow automation.
    
    Provides a unified interface for predictive intelligence that seamlessly
    works with the existing TodoWrite and session management systems.
    """
    
    def __init__(self, project_root: str = None):
        """Initialize the integration manager"""
        self.project_root = project_root or os.getcwd()
        
        # Initialize core components
        self.metrics_collector = QualityMetricsCollector(self.project_root)
        self.historical_manager = HistoricalMetricsManager()
        self.trend_analyzer = QualityTrendAnalyzer()
        self.risk_assessor = PredictiveRiskAssessment(self.trend_analyzer)
        self.early_warning = EarlyWarningSystem(self.trend_analyzer, self.risk_assessor)
        
        # Integration state
        self.last_analysis_time: Optional[datetime] = None
        self.auto_collect_enabled = True
        self.prediction_cache: Dict[str, Any] = {}
        
    def initialize_predictive_intelligence(self) -> Dict[str, Any]:
        """
        Initialize the predictive intelligence system
        
        Returns:
            Initialization status and capabilities
        """
        try:
            # Collect initial metrics
            initial_metrics = self.metrics_collector.collect_comprehensive_metrics()
            
            # Add to historical data
            self.historical_manager.add_metrics_snapshot(self.metrics_collector)
            
            # Convert to QualityMetrics format for trend analyzer
            quality_metrics = QualityMetrics(
                timestamp=initial_metrics.timestamp,
                doc_coverage=initial_metrics.documentation_coverage,
                code_quality_score=initial_metrics.code_quality_score,
                test_coverage=initial_metrics.test_coverage,
                complexity_score=initial_metrics.average_complexity,
                maintainability_index=initial_metrics.maintainability_index,
                technical_debt_ratio=initial_metrics.technical_debt_ratio
            )
            
            # Add to trend analyzer
            self.trend_analyzer.add_quality_data(quality_metrics)
            
            self.last_analysis_time = datetime.now()
            
            return {
                'status': 'initialized',
                'capabilities': [
                    'Quality trend analysis',
                    'Risk prediction',
                    'Early warning system',
                    'Historical tracking',
                    'Automated recommendations'
                ],
                'baseline_metrics': {
                    'documentation_coverage': initial_metrics.documentation_coverage,
                    'code_quality_score': initial_metrics.code_quality_score,
                    'test_coverage': initial_metrics.test_coverage,
                    'complexity_score': initial_metrics.average_complexity,
                    'maintainability_index': initial_metrics.maintainability_index,
                    'technical_debt_ratio': initial_metrics.technical_debt_ratio
                },
                'prediction_readiness': self._assess_prediction_readiness()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'fallback_available': True
            }
    
    def get_intelligent_task_recommendations(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get intelligent task recommendations based on predictive analysis
        
        Args:
            context: Optional context information about current session
            
        Returns:
            Intelligent recommendations for task prioritization
        """
        try:
            # Update metrics if needed
            self._update_metrics_if_needed()
            
            # Get quality trends
            quality_trends = self.trend_analyzer.get_overall_quality_trend()
            
            # Get risk assessment
            risks = self.risk_assessor.assess_risks()
            
            # Get early warnings
            warnings = []  # Simplified for now
            
            # Generate intelligent recommendations
            recommendations = self._generate_intelligent_recommendations(
                quality_trends, risks, warnings, context
            )
            
            return {
                'status': 'success',
                'recommendations': recommendations,
                'quality_overview': {
                    'overall_trend': quality_trends.get('overall_trend'),
                    'risk_summary': quality_trends.get('risk_summary'),
                    'immediate_actions': len([r for r in risks if r.predicted_timeline == 'immediate'])
                },
                'prediction_confidence': self._calculate_overall_confidence(quality_trends, risks),
                'next_analysis_due': self._get_next_analysis_time()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'fallback_recommendations': self._get_fallback_recommendations()
            }
    
    def enhance_todo_prioritization(self, todos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhance existing TodoWrite items with predictive intelligence
        
        Args:
            todos: List of todo items from TodoWrite
            
        Returns:
            Enhanced todos with intelligent prioritization
        """
        try:
            # Get current predictions
            predictions = self.get_intelligent_task_recommendations()
            
            if predictions['status'] != 'success':
                return todos  # Return unchanged if prediction failed
            
            # Enhance each todo with predictive insights
            enhanced_todos = []
            for todo in todos:
                enhanced_todo = todo.copy()
                
                # Add predictive insights
                insights = self._analyze_todo_for_quality_impact(todo, predictions)
                if insights:
                    enhanced_todo['predictive_insights'] = insights
                    
                    # Adjust priority if needed
                    if insights.get('quality_impact') == 'high':
                        if todo['priority'] == 'low':
                            enhanced_todo['priority'] = 'medium'
                        elif todo['priority'] == 'medium':
                            enhanced_todo['priority'] = 'high'
                
                enhanced_todos.append(enhanced_todo)
            
            # Sort by enhanced priority
            priority_order = {'high': 3, 'medium': 2, 'low': 1}
            enhanced_todos.sort(
                key=lambda x: (
                    priority_order.get(x['priority'], 1),
                    x.get('predictive_insights', {}).get('urgency_score', 0)
                ),
                reverse=True
            )
            
            return enhanced_todos
            
        except Exception as e:
            print(f"Warning: Todo enhancement failed: {e}")
            return todos  # Return original todos if enhancement fails
    
    def get_session_startup_insights(self) -> Dict[str, Any]:
        """
        Provide intelligent insights for session startup optimization
        
        Returns:
            Insights and recommendations for the current session
        """
        try:
            # Update metrics
            self._update_metrics_if_needed()
            
            # Get current status
            quality_trends = self.trend_analyzer.get_overall_quality_trend()
            risks = self.risk_assessor.assess_risks(days_ahead=1)  # Focus on immediate risks
            
            # Generate session-specific insights
            insights = {
                'session_priority_focus': self._determine_session_focus(quality_trends, risks),
                'immediate_warnings': [r for r in risks if r.predicted_timeline == 'immediate'],
                'quality_hotspots': self._identify_quality_hotspots(quality_trends),
                'recommended_first_actions': self._get_session_first_actions(risks),
                'productivity_factors': {
                    'predicted_efficiency': self._predict_session_efficiency(quality_trends),
                    'complexity_warning': quality_trends['overall_trend'].risk_level if hasattr(quality_trends.get('overall_trend'), 'risk_level') else 'unknown',
                    'technical_debt_pressure': quality_trends['risk_summary']['overall_risk_level']
                }
            }
            
            return {
                'status': 'success',
                'insights': insights,
                'confidence_level': self._calculate_overall_confidence(quality_trends, risks),
                'last_updated': self.last_analysis_time.isoformat() if self.last_analysis_time else None
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'fallback_insights': {
                    'session_priority_focus': 'general_development',
                    'recommended_first_actions': ['Review recent changes', 'Check system status']
                }
            }
    
    def _update_metrics_if_needed(self) -> bool:
        """Update metrics if sufficient time has passed"""
        if not self.last_analysis_time:
            return self._update_metrics()
        
        # Update every hour or if significant time has passed
        time_since_update = datetime.now() - self.last_analysis_time
        if time_since_update > timedelta(hours=1):
            return self._update_metrics()
        
        return False
    
    def _update_metrics(self) -> bool:
        """Force update of all metrics"""
        try:
            # Collect new metrics
            current_metrics = self.metrics_collector.collect_comprehensive_metrics()
            
            # Add to historical manager
            self.historical_manager.add_metrics_snapshot(self.metrics_collector)
            
            # Convert and add to trend analyzer
            quality_metrics = QualityMetrics(
                timestamp=current_metrics.timestamp,
                doc_coverage=current_metrics.documentation_coverage,
                code_quality_score=current_metrics.code_quality_score,
                test_coverage=current_metrics.test_coverage,
                complexity_score=current_metrics.average_complexity,
                maintainability_index=current_metrics.maintainability_index,
                technical_debt_ratio=current_metrics.technical_debt_ratio
            )
            
            self.trend_analyzer.add_quality_data(quality_metrics)
            
            # Clear prediction cache
            self.prediction_cache.clear()
            
            self.last_analysis_time = datetime.now()
            return True
            
        except Exception as e:
            print(f"Warning: Metrics update failed: {e}")
            return False
    
    def _assess_prediction_readiness(self) -> Dict[str, Any]:
        """Assess readiness of the prediction system"""
        historical_stats = self.historical_manager.get_summary_statistics()
        
        if 'error' in historical_stats:
            data_points = 0
        else:
            data_points = historical_stats.get('data_points', 0)
        
        readiness = {
            'data_sufficiency': 'good' if data_points >= 7 else 'limited' if data_points >= 3 else 'insufficient',
            'prediction_accuracy_expected': '90%+' if data_points >= 14 else '70-90%' if data_points >= 7 else '50-70%',
            'features_available': [
                'Trend analysis',
                'Risk assessment',
                'Quality scoring'
            ]
        }
        
        if data_points < 3:
            readiness['features_available'].append('Baseline establishment mode')
        elif data_points >= 14:
            readiness['features_available'].extend([
                'High-confidence predictions',
                'Advanced pattern recognition',
                'Seasonal trend analysis'
            ])
        
        return readiness
    
    def _generate_intelligent_recommendations(self, quality_trends: Dict[str, Any], 
                                           risks: List, warnings: List,
                                           context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Generate intelligent task recommendations"""
        recommendations = []
        
        # Process immediate risks
        for risk in risks[:3]:  # Top 3 risks
            if risk.predicted_timeline == 'immediate':
                priority = 'high'
            elif risk.predicted_timeline in ['1-3 days', '4-7 days']:
                priority = 'medium'
            else:
                priority = 'low'
            
            for suggestion in risk.mitigation_suggestions[:2]:  # Top 2 suggestions per risk
                recommendations.append({
                    'task': suggestion,
                    'priority': priority,
                    'category': 'risk_mitigation',
                    'risk_type': risk.risk_type,
                    'confidence': risk.confidence_level,
                    'timeline': risk.predicted_timeline,
                    'impact': risk.impact_severity
                })
        
        # Add trend-based recommendations
        individual_trends = quality_trends.get('individual_trends', {})
        for metric_name, trend in individual_trends.items():
            if trend.risk_level in ['high', 'critical']:
                recommendation = self._get_trend_recommendation(metric_name, trend)
                if recommendation:
                    recommendations.append(recommendation)
        
        # Add early warning recommendations
        for warning in warnings[:2]:  # Top 2 warnings
            recommendations.append({
                'task': f"Address warning: {warning.get('message', 'Check system status')}",
                'priority': 'high' if warning.get('severity') == 'critical' else 'medium',
                'category': 'early_warning',
                'warning_type': warning.get('type'),
                'confidence': warning.get('confidence', 0.8)
            })
        
        # Remove duplicates and sort by priority
        seen_tasks = set()
        unique_recommendations = []
        for rec in recommendations:
            task_key = rec['task'].lower()
            if task_key not in seen_tasks:
                seen_tasks.add(task_key)
                unique_recommendations.append(rec)
        
        # Sort by priority and confidence
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        unique_recommendations.sort(
            key=lambda x: (priority_order.get(x['priority'], 1), x.get('confidence', 0)),
            reverse=True
        )
        
        return unique_recommendations[:8]  # Return top 8 recommendations
    
    def _get_trend_recommendation(self, metric_name: str, trend) -> Optional[Dict[str, Any]]:
        """Get recommendation based on metric trend"""
        trend_recommendations = {
            'doc_coverage': {
                'task': 'Improve documentation coverage using auto-doc generator',
                'category': 'documentation'
            },
            'code_quality_score': {
                'task': 'Run code quality analysis and address issues',
                'category': 'code_quality'
            },
            'test_coverage': {
                'task': 'Add unit tests for critical components',
                'category': 'testing'
            },
            'complexity_score': {
                'task': 'Refactor high-complexity modules',
                'category': 'refactoring'
            },
            'maintainability_index': {
                'task': 'Improve code maintainability through refactoring',
                'category': 'maintainability'
            },
            'technical_debt_ratio': {
                'task': 'Address technical debt accumulation',
                'category': 'technical_debt'
            }
        }
        
        base_rec = trend_recommendations.get(metric_name)
        if not base_rec:
            return None
        
        priority = 'high' if trend.risk_level == 'critical' else 'medium' if trend.risk_level == 'high' else 'low'
        
        return {
            'task': base_rec['task'],
            'priority': priority,
            'category': base_rec['category'],
            'metric': metric_name,
            'trend_direction': trend.trend_direction,
            'confidence': trend.confidence_level,
            'current_value': trend.current_value,
            'predicted_value': trend.predicted_value_7d
        }
    
    def _analyze_todo_for_quality_impact(self, todo: Dict[str, Any], 
                                       predictions: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze a todo item for its potential quality impact"""
        content = todo.get('content', '').lower()
        
        # Quality impact keywords
        high_impact_keywords = [
            'refactor', 'optimize', 'fix', 'improve', 'enhance',
            'documentation', 'test', 'review', 'quality'
        ]
        
        medium_impact_keywords = [
            'update', 'modify', 'change', 'add', 'implement'
        ]
        
        quality_impact = 'low'
        urgency_score = 0
        
        for keyword in high_impact_keywords:
            if keyword in content:
                quality_impact = 'high'
                urgency_score += 2
                break
        
        if quality_impact == 'low':
            for keyword in medium_impact_keywords:
                if keyword in content:
                    quality_impact = 'medium'
                    urgency_score += 1
                    break
        
        # Enhance based on current risks
        recommendations = predictions.get('recommendations', [])
        for rec in recommendations:
            if any(word in content for word in rec.get('task', '').lower().split()):
                quality_impact = 'high'
                urgency_score += 3
                break
        
        if quality_impact == 'low' and urgency_score == 0:
            return None
        
        return {
            'quality_impact': quality_impact,
            'urgency_score': urgency_score,
            'analysis_confidence': 0.7
        }
    
    def _determine_session_focus(self, quality_trends: Dict[str, Any], risks: List) -> str:
        """Determine the primary focus for the current session"""
        immediate_risks = [r for r in risks if r.predicted_timeline == 'immediate']
        high_severity_risks = [r for r in risks if r.impact_severity in ['high', 'critical']]
        
        if immediate_risks:
            return 'immediate_risk_mitigation'
        elif high_severity_risks:
            return 'quality_improvement'
        elif quality_trends['risk_summary']['overall_risk_level'] in ['medium', 'high']:
            return 'preventive_maintenance'
        else:
            return 'feature_development'
    
    def _identify_quality_hotspots(self, quality_trends: Dict[str, Any]) -> List[str]:
        """Identify areas that need immediate attention"""
        hotspots = []
        individual_trends = quality_trends.get('individual_trends', {})
        
        for metric_name, trend in individual_trends.items():
            if trend.risk_level in ['high', 'critical'] or trend.trend_direction == 'declining':
                hotspots.append(metric_name)
        
        return hotspots[:3]  # Top 3 hotspots
    
    def _get_session_first_actions(self, risks: List) -> List[str]:
        """Get recommended first actions for the session"""
        immediate_risks = [r for r in risks if r.predicted_timeline == 'immediate']
        
        if immediate_risks:
            return [suggestion for risk in immediate_risks[:2] 
                   for suggestion in risk.mitigation_suggestions[:1]]
        
        high_priority_risks = [r for r in risks if r.impact_severity in ['high', 'critical']]
        if high_priority_risks:
            return [suggestion for risk in high_priority_risks[:1] 
                   for suggestion in risk.mitigation_suggestions[:2]]
        
        return ['Review recent changes', 'Run quality assessment', 'Check system health']
    
    def _predict_session_efficiency(self, quality_trends: Dict[str, Any]) -> str:
        """Predict session efficiency based on quality trends"""
        risk_level = quality_trends['risk_summary']['overall_risk_level']
        
        if risk_level == 'low':
            return 'high'
        elif risk_level == 'medium':
            return 'medium'
        else:
            return 'low'
    
    def _calculate_overall_confidence(self, quality_trends: Dict[str, Any], risks: List) -> float:
        """Calculate overall confidence in predictions"""
        individual_trends = quality_trends.get('individual_trends', {})
        
        if not individual_trends:
            return 0.5
        
        trend_confidences = [trend.confidence_level for trend in individual_trends.values()]
        risk_confidences = [risk.confidence_level for risk in risks]
        
        all_confidences = trend_confidences + risk_confidences
        
        if not all_confidences:
            return 0.5
        
        return sum(all_confidences) / len(all_confidences)
    
    def _get_next_analysis_time(self) -> str:
        """Get the time for the next analysis"""
        if not self.last_analysis_time:
            return 'immediately'
        
        next_time = self.last_analysis_time + timedelta(hours=1)
        return next_time.isoformat()
    
    def _get_fallback_recommendations(self) -> List[Dict[str, Any]]:
        """Get fallback recommendations when prediction fails"""
        return [
            {
                'task': 'Review code quality standards',
                'priority': 'medium',
                'category': 'maintenance',
                'confidence': 0.6
            },
            {
                'task': 'Update project documentation',
                'priority': 'medium',
                'category': 'documentation',
                'confidence': 0.6
            },
            {
                'task': 'Run existing test suite',
                'priority': 'low',
                'category': 'testing',
                'confidence': 0.6
            }
        ]
    
    def export_prediction_report(self, output_path: str) -> bool:
        """
        Export a comprehensive prediction report
        
        Args:
            output_path: Path to save the report
            
        Returns:
            True if export successful
        """
        try:
            # Get all prediction data
            recommendations = self.get_intelligent_task_recommendations()
            session_insights = self.get_session_startup_insights()
            
            report = {
                'report_timestamp': datetime.now().isoformat(),
                'system_status': {
                    'prediction_system_health': 'operational',
                    'last_analysis': self.last_analysis_time.isoformat() if self.last_analysis_time else None,
                    'data_sufficiency': self._assess_prediction_readiness()
                },
                'intelligent_recommendations': recommendations,
                'session_insights': session_insights,
                'historical_summary': self.historical_manager.get_summary_statistics(),
                'quality_metrics': self.metrics_collector.get_metrics_summary()
            }
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error exporting prediction report: {e}")
            return False