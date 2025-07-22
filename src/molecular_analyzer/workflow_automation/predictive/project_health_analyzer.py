"""
Project Health Analytics Module - Task 2.2

This module provides real-time project health monitoring with predictive capabilities,
building upon the Task 2.1 predictive intelligence foundation.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import statistics
import json

from .quality_predictor import QualityTrendAnalyzer, PredictiveRiskAssessment
from .quality_metrics_collector import QualityMetricsCollector, ProjectMetrics


class HealthStatus(Enum):
    """Project health status levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class HealthMetric:
    """Individual health metric"""
    name: str
    value: float
    status: HealthStatus
    trend: str  # "improving", "stable", "declining"
    confidence: float
    last_updated: datetime
    threshold_breached: bool = False


@dataclass
class ProjectHealthReport:
    """Comprehensive project health report"""
    overall_status: HealthStatus
    overall_score: float
    timestamp: datetime
    metrics: List[HealthMetric]
    risk_factors: List[str]
    recommendations: List[str]
    trend_analysis: Dict[str, Any]
    confidence_level: float


class ProjectHealthAnalyzer:
    """
    Real-time project health monitoring with predictive capabilities.
    
    Builds upon Task 2.1 predictive intelligence to provide comprehensive
    health analytics with 85%+ trend accuracy target.
    """
    
    def __init__(self, project_path: str):
        """Initialize project health analyzer"""
        self.project_path = project_path
        self.quality_trend_analyzer = QualityTrendAnalyzer()
        self.predictive_risk_assessment = PredictiveRiskAssessment(self.quality_trend_analyzer)
        self.metrics_collector = QualityMetricsCollector()
        
        # Health thresholds
        self.health_thresholds = {
            'code_quality': {'excellent': 0.9, 'good': 0.8, 'fair': 0.7, 'poor': 0.6},
            'test_coverage': {'excellent': 0.95, 'good': 0.85, 'fair': 0.75, 'poor': 0.65},
            'documentation_coverage': {'excellent': 0.95, 'good': 0.85, 'fair': 0.75, 'poor': 0.65},
            'complexity_score': {'excellent': 0.2, 'good': 0.4, 'fair': 0.6, 'poor': 0.8},  # Lower is better
            'risk_level': {'excellent': 0.1, 'good': 0.3, 'fair': 0.5, 'poor': 0.7}  # Lower is better
        }
        
        # Historical data for trend analysis
        self.health_history: List[ProjectHealthReport] = []
        self.max_history_days = 30
        
        self.logger = logging.getLogger(__name__)
        
    def analyze_project_health(self) -> ProjectHealthReport:
        """
        Perform comprehensive project health analysis.
        
        Returns:
            ProjectHealthReport: Complete health assessment with metrics and trends
        """
        try:
            # Collect current metrics
            current_metrics = self._collect_health_metrics()
            
            # Analyze trends
            trend_analysis = self._analyze_health_trends()
            
            # Assess risks
            risk_factors = self._assess_risk_factors(current_metrics)
            
            # Generate recommendations
            recommendations = self._generate_health_recommendations(current_metrics, risk_factors)
            
            # Calculate overall health
            overall_status, overall_score, confidence = self._calculate_overall_health(current_metrics)
            
            # Create comprehensive report
            health_report = ProjectHealthReport(
                overall_status=overall_status,
                overall_score=overall_score,
                timestamp=datetime.now(),
                metrics=current_metrics,
                risk_factors=risk_factors,
                recommendations=recommendations,
                trend_analysis=trend_analysis,
                confidence_level=confidence
            )
            
            # Store in history for trend analysis
            self._update_health_history(health_report)
            
            self.logger.info(f"Project health analysis completed: {overall_status.value} ({overall_score:.2f})")
            return health_report
            
        except Exception as e:
            self.logger.error(f"Error in project health analysis: {str(e)}")
            # Return default health report in case of error
            return self._create_error_health_report(str(e))
    
    def _collect_health_metrics(self) -> List[HealthMetric]:
        """Collect current health metrics from various sources"""
        metrics = []
        
        try:
            # Get project metrics from quality collector
            project_metrics = self.metrics_collector.collect_project_metrics(self.project_path)
            
            if project_metrics:
                # Code quality metric
                code_quality = self._calculate_code_quality_score(project_metrics)
                metrics.append(HealthMetric(
                    name="code_quality",
                    value=code_quality,
                    status=self._determine_status('code_quality', code_quality),
                    trend=self._calculate_metric_trend('code_quality'),
                    confidence=0.85,
                    last_updated=datetime.now()
                ))
                
                # Test coverage metric (simulated based on project structure)
                test_coverage = self._estimate_test_coverage(project_metrics)
                metrics.append(HealthMetric(
                    name="test_coverage",
                    value=test_coverage,
                    status=self._determine_status('test_coverage', test_coverage),
                    trend=self._calculate_metric_trend('test_coverage'),
                    confidence=0.75,
                    last_updated=datetime.now()
                ))
                
                # Documentation coverage metric
                doc_coverage = self._estimate_documentation_coverage(project_metrics)
                metrics.append(HealthMetric(
                    name="documentation_coverage",
                    value=doc_coverage,
                    status=self._determine_status('documentation_coverage', doc_coverage),
                    trend=self._calculate_metric_trend('documentation_coverage'),
                    confidence=0.80,
                    last_updated=datetime.now()
                ))
                
                # Complexity metric
                complexity_score = self._calculate_complexity_score(project_metrics)
                metrics.append(HealthMetric(
                    name="complexity_score",
                    value=complexity_score,
                    status=self._determine_status('complexity_score', complexity_score, lower_is_better=True),
                    trend=self._calculate_metric_trend('complexity_score'),
                    confidence=0.90,
                    last_updated=datetime.now()
                ))
            
            # Risk level from predictive assessment
            risk_assessment = self.predictive_risk_assessment.assess_risk({})  # Simplified for now
            risk_level = risk_assessment.overall_risk_level
            metrics.append(HealthMetric(
                name="risk_level",
                value=risk_level,
                status=self._determine_status('risk_level', risk_level, lower_is_better=True),
                trend=self._calculate_metric_trend('risk_level'),
                confidence=risk_assessment.confidence,
                last_updated=datetime.now()
            ))
            
        except Exception as e:
            self.logger.warning(f"Error collecting health metrics: {str(e)}")
            # Add default metrics if collection fails
            metrics.append(HealthMetric(
                name="system_status",
                value=0.7,
                status=HealthStatus.FAIR,
                trend="stable",
                confidence=0.5,
                last_updated=datetime.now()
            ))
        
        return metrics
    
    def _calculate_code_quality_score(self, project_metrics: ProjectMetrics) -> float:
        """Calculate overall code quality score"""
        try:
            # Combine various quality indicators
            quality_factors = []
            
            if hasattr(project_metrics, 'code_metrics') and project_metrics.code_metrics:
                # Use actual code metrics if available
                code_metrics = project_metrics.code_metrics
                
                # Cyclomatic complexity (normalized)
                if hasattr(code_metrics, 'cyclomatic_complexity'):
                    complexity_score = min(1.0, max(0.0, 1.0 - (code_metrics.cyclomatic_complexity / 20.0)))
                    quality_factors.append(complexity_score)
                
                # Lines of code quality (prefer moderate sizes)
                if hasattr(code_metrics, 'lines_of_code'):
                    loc_score = min(1.0, max(0.0, 1.0 - abs(code_metrics.lines_of_code - 100) / 200.0))
                    quality_factors.append(loc_score)
            
            # If no specific metrics, use baseline
            if not quality_factors:
                quality_factors = [0.75]  # Default baseline
            
            return statistics.mean(quality_factors)
        except Exception:
            return 0.70  # Safe default
    
    def _estimate_test_coverage(self, project_metrics: ProjectMetrics) -> float:
        """Estimate test coverage based on project structure"""
        try:
            # Simple heuristic based on presence of test files
            if hasattr(project_metrics, 'has_tests') and project_metrics.has_tests:
                return 0.80  # Assume good coverage if tests exist
            elif 'test' in str(self.project_path).lower():
                return 0.85  # Higher if we're in a test-focused project
            else:
                return 0.60  # Lower baseline
        except Exception:
            return 0.65  # Safe default
    
    def _estimate_documentation_coverage(self, project_metrics: ProjectMetrics) -> float:
        """Estimate documentation coverage"""
        try:
            # Based on presence of documentation files and docstrings
            doc_score = 0.70  # Baseline
            
            if hasattr(project_metrics, 'has_documentation'):
                if project_metrics.has_documentation:
                    doc_score += 0.15
            
            # Check for README and other doc files (simple heuristic)
            if 'readme' in str(self.project_path).lower() or 'doc' in str(self.project_path).lower():
                doc_score += 0.10
            
            return min(1.0, doc_score)
        except Exception:
            return 0.75  # Safe default
    
    def _calculate_complexity_score(self, project_metrics: ProjectMetrics) -> float:
        """Calculate complexity score (0-1, where lower is better)"""
        try:
            if hasattr(project_metrics, 'code_metrics') and project_metrics.code_metrics:
                complexity = getattr(project_metrics.code_metrics, 'cyclomatic_complexity', 5)
                # Normalize to 0-1 range (10 is considered moderate complexity)
                return min(1.0, complexity / 10.0)
            return 0.4  # Default moderate complexity
        except Exception:
            return 0.5  # Safe default
    
    def _determine_status(self, metric_name: str, value: float, lower_is_better: bool = False) -> HealthStatus:
        """Determine health status based on value and thresholds"""
        try:
            thresholds = self.health_thresholds.get(metric_name, {})
            
            if lower_is_better:
                # For metrics where lower values are better (complexity, risk)
                if value <= thresholds.get('excellent', 0.2):
                    return HealthStatus.EXCELLENT
                elif value <= thresholds.get('good', 0.4):
                    return HealthStatus.GOOD
                elif value <= thresholds.get('fair', 0.6):
                    return HealthStatus.FAIR
                elif value <= thresholds.get('poor', 0.8):
                    return HealthStatus.POOR
                else:
                    return HealthStatus.CRITICAL
            else:
                # For metrics where higher values are better (quality, coverage)
                if value >= thresholds.get('excellent', 0.9):
                    return HealthStatus.EXCELLENT
                elif value >= thresholds.get('good', 0.8):
                    return HealthStatus.GOOD
                elif value >= thresholds.get('fair', 0.7):
                    return HealthStatus.FAIR
                elif value >= thresholds.get('poor', 0.6):
                    return HealthStatus.POOR
                else:
                    return HealthStatus.CRITICAL
        except Exception:
            return HealthStatus.FAIR  # Safe default
    
    def _calculate_metric_trend(self, metric_name: str) -> str:
        """Calculate trend for a specific metric"""
        try:
            if len(self.health_history) < 2:
                return "stable"  # Need at least 2 data points
            
            # Get last 5 values for this metric
            recent_values = []
            for report in self.health_history[-5:]:
                for metric in report.metrics:
                    if metric.name == metric_name:
                        recent_values.append(metric.value)
                        break
            
            if len(recent_values) < 2:
                return "stable"
            
            # Simple trend analysis
            first_half_avg = statistics.mean(recent_values[:len(recent_values)//2])
            second_half_avg = statistics.mean(recent_values[len(recent_values)//2:])
            
            change = second_half_avg - first_half_avg
            if abs(change) < 0.05:  # 5% threshold
                return "stable"
            elif change > 0:
                return "improving"
            else:
                return "declining"
                
        except Exception:
            return "stable"  # Safe default
    
    def _analyze_health_trends(self) -> Dict[str, Any]:
        """Analyze overall health trends"""
        try:
            if len(self.health_history) < 3:
                return {
                    'trend': 'insufficient_data',
                    'velocity': 0.0,
                    'prediction': 'stable',
                    'confidence': 0.3
                }
            
            # Calculate trend velocity
            recent_scores = [report.overall_score for report in self.health_history[-7:]]
            if len(recent_scores) >= 2:
                velocity = recent_scores[-1] - recent_scores[0]
                velocity /= len(recent_scores)  # Per-period velocity
            else:
                velocity = 0.0
            
            # Predict trend direction
            if velocity > 0.05:
                trend = 'improving'
                prediction = 'continued_improvement'
            elif velocity < -0.05:
                trend = 'declining'
                prediction = 'attention_needed'
            else:
                trend = 'stable'
                prediction = 'stable'
            
            return {
                'trend': trend,
                'velocity': velocity,
                'prediction': prediction,
                'confidence': min(0.9, 0.3 + 0.1 * len(recent_scores))
            }
            
        except Exception:
            return {
                'trend': 'unknown',
                'velocity': 0.0,
                'prediction': 'stable',
                'confidence': 0.3
            }
    
    def _assess_risk_factors(self, metrics: List[HealthMetric]) -> List[str]:
        """Assess current risk factors"""
        risk_factors = []
        
        try:
            for metric in metrics:
                if metric.status in [HealthStatus.POOR, HealthStatus.CRITICAL]:
                    risk_factors.append(f"Poor {metric.name.replace('_', ' ')}: {metric.value:.2f}")
                
                if metric.trend == "declining" and metric.confidence > 0.7:
                    risk_factors.append(f"Declining trend in {metric.name.replace('_', ' ')}")
                
                if metric.threshold_breached:
                    risk_factors.append(f"Threshold breached for {metric.name.replace('_', ' ')}")
            
            # Additional risk assessment from predictive system
            try:
                risk_assessment = self.predictive_risk_assessment.assess_risk({})
                if risk_assessment.risk_factors:
                    risk_factors.extend(risk_assessment.risk_factors[:3])  # Add top 3
            except Exception:
                pass
                
        except Exception as e:
            self.logger.warning(f"Error assessing risk factors: {str(e)}")
            risk_factors.append("Risk assessment temporarily unavailable")
        
        return risk_factors[:10]  # Limit to top 10 risks
    
    def _generate_health_recommendations(self, metrics: List[HealthMetric], risk_factors: List[str]) -> List[str]:
        """Generate actionable health recommendations"""
        recommendations = []
        
        try:
            # Metric-specific recommendations
            for metric in metrics:
                if metric.status in [HealthStatus.POOR, HealthStatus.CRITICAL]:
                    if metric.name == 'code_quality':
                        recommendations.append("Consider code refactoring to improve quality metrics")
                    elif metric.name == 'test_coverage':
                        recommendations.append("Increase test coverage by adding unit tests")
                    elif metric.name == 'documentation_coverage':
                        recommendations.append("Improve documentation coverage for better maintainability")
                    elif metric.name == 'complexity_score':
                        recommendations.append("Simplify complex code structures and functions")
                    elif metric.name == 'risk_level':
                        recommendations.append("Address high-risk areas identified by predictive analysis")
                
                if metric.trend == "declining":
                    recommendations.append(f"Monitor {metric.name.replace('_', ' ')} - showing declining trend")
            
            # Risk-based recommendations
            if len(risk_factors) > 5:
                recommendations.append("High number of risk factors detected - prioritize risk mitigation")
            
            # General recommendations
            if not recommendations:
                recommendations.append("Project health is stable - continue current practices")
            
        except Exception as e:
            self.logger.warning(f"Error generating recommendations: {str(e)}")
            recommendations.append("Health analysis recommendations temporarily unavailable")
        
        return recommendations[:8]  # Limit to top 8 recommendations
    
    def _calculate_overall_health(self, metrics: List[HealthMetric]) -> Tuple[HealthStatus, float, float]:
        """Calculate overall health status and score"""
        try:
            if not metrics:
                return HealthStatus.FAIR, 0.7, 0.5
            
            # Weighted scoring
            weights = {
                'code_quality': 0.25,
                'test_coverage': 0.20,
                'documentation_coverage': 0.15,
                'complexity_score': 0.20,  # Inverted for calculation
                'risk_level': 0.20  # Inverted for calculation
            }
            
            total_score = 0.0
            total_weight = 0.0
            confidence_scores = []
            
            for metric in metrics:
                weight = weights.get(metric.name, 0.1)
                
                # For inverted metrics (lower is better)
                if metric.name in ['complexity_score', 'risk_level']:
                    score = 1.0 - metric.value  # Invert
                else:
                    score = metric.value
                
                total_score += score * weight
                total_weight += weight
                confidence_scores.append(metric.confidence)
            
            # Calculate final score
            if total_weight > 0:
                final_score = total_score / total_weight
            else:
                final_score = 0.7
            
            # Calculate overall confidence
            overall_confidence = statistics.mean(confidence_scores) if confidence_scores else 0.5
            
            # Determine status
            if final_score >= 0.9:
                status = HealthStatus.EXCELLENT
            elif final_score >= 0.8:
                status = HealthStatus.GOOD
            elif final_score >= 0.65:
                status = HealthStatus.FAIR
            elif final_score >= 0.5:
                status = HealthStatus.POOR
            else:
                status = HealthStatus.CRITICAL
            
            return status, final_score, overall_confidence
            
        except Exception as e:
            self.logger.error(f"Error calculating overall health: {str(e)}")
            return HealthStatus.FAIR, 0.7, 0.5
    
    def _update_health_history(self, health_report: ProjectHealthReport):
        """Update health history for trend analysis"""
        try:
            self.health_history.append(health_report)
            
            # Trim history to max days
            cutoff_date = datetime.now() - timedelta(days=self.max_history_days)
            self.health_history = [
                report for report in self.health_history 
                if report.timestamp > cutoff_date
            ]
            
        except Exception as e:
            self.logger.warning(f"Error updating health history: {str(e)}")
    
    def _create_error_health_report(self, error_message: str) -> ProjectHealthReport:
        """Create a default health report when analysis fails"""
        return ProjectHealthReport(
            overall_status=HealthStatus.FAIR,
            overall_score=0.5,
            timestamp=datetime.now(),
            metrics=[HealthMetric(
                name="system_status",
                value=0.5,
                status=HealthStatus.FAIR,
                trend="unknown",
                confidence=0.3,
                last_updated=datetime.now()
            )],
            risk_factors=[f"Health analysis error: {error_message}"],
            recommendations=["Resolve system issues to enable proper health monitoring"],
            trend_analysis={'trend': 'unknown', 'confidence': 0.0},
            confidence_level=0.3
        )
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get a quick health summary"""
        try:
            latest_report = self.analyze_project_health()
            return {
                'status': latest_report.overall_status.value,
                'score': latest_report.overall_score,
                'confidence': latest_report.confidence_level,
                'top_risks': latest_report.risk_factors[:3],
                'top_recommendations': latest_report.recommendations[:3],
                'trend': latest_report.trend_analysis.get('trend', 'unknown')
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'confidence': 0.0
            }