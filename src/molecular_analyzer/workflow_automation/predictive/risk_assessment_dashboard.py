"""
Risk Assessment Dashboard Module - Task 2.2

This module provides a real-time risk assessment dashboard with visual indicators
and automated monitoring capabilities.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json

from .project_health_analyzer import ProjectHealthAnalyzer, HealthStatus, ProjectHealthReport
from .quality_predictor import QualityTrendAnalyzer, PredictiveRiskAssessment, RiskAssessment
from .early_warning_system import EarlyWarningSystem, AlertManager


class RiskLevel(Enum):
    """Risk severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertPriority(Enum):
    """Alert priority levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class RiskIndicator:
    """Individual risk indicator"""
    name: str
    level: RiskLevel
    score: float
    description: str
    impact: str
    likelihood: float
    mitigation: str
    last_updated: datetime


@dataclass
class DashboardAlert:
    """Dashboard alert information"""
    id: str
    title: str
    message: str
    priority: AlertPriority
    risk_level: RiskLevel
    timestamp: datetime
    source: str
    actionable: bool
    auto_resolvable: bool


@dataclass
class RiskDashboardData:
    """Complete risk dashboard data"""
    overall_risk_level: RiskLevel
    risk_score: float
    timestamp: datetime
    risk_indicators: List[RiskIndicator]
    active_alerts: List[DashboardAlert]
    trend_data: Dict[str, Any]
    health_summary: Dict[str, Any]
    recommendations: List[str]
    confidence_level: float


class RiskAssessmentDashboard:
    """
    Real-time risk assessment dashboard with visual indicators and monitoring.
    
    Provides comprehensive risk visualization and automated alert management
    for proactive project health monitoring.
    """
    
    def __init__(self, project_path: str):
        """Initialize risk assessment dashboard"""
        self.project_path = project_path
        self.project_health_analyzer = ProjectHealthAnalyzer(project_path)
        quality_analyzer = QualityTrendAnalyzer()
        self.predictive_risk_assessment = PredictiveRiskAssessment(quality_analyzer)
        self.early_warning_system = EarlyWarningSystem(quality_analyzer, self.predictive_risk_assessment)
        self.alert_manager = AlertManager(self.early_warning_system)
        
        # Risk thresholds and configuration
        self.risk_thresholds = {
            'critical': 0.8,
            'high': 0.6,
            'medium': 0.4,
            'low': 0.2
        }
        
        # Dashboard state
        self.dashboard_history: List[RiskDashboardData] = []
        self.active_monitoring = False
        self.update_interval_seconds = 300  # 5 minutes default
        
        self.logger = logging.getLogger(__name__)
    
    def generate_dashboard_data(self) -> RiskDashboardData:
        """
        Generate comprehensive dashboard data for real-time monitoring.
        
        Returns:
            RiskDashboardData: Complete dashboard state with all indicators
        """
        try:
            # Get current health analysis
            health_report = self.project_health_analyzer.analyze_project_health()
            
            # Collect risk indicators
            risk_indicators = self._collect_risk_indicators(health_report)
            
            # Calculate overall risk level and score
            overall_risk_level, risk_score = self._calculate_overall_risk(risk_indicators)
            
            # Generate alerts
            active_alerts = self._generate_alerts(risk_indicators, health_report)
            
            # Analyze trend data
            trend_data = self._analyze_risk_trends()
            
            # Create health summary
            health_summary = self._create_health_summary(health_report)
            
            # Generate recommendations
            recommendations = self._generate_risk_recommendations(risk_indicators, active_alerts)
            
            # Calculate confidence
            confidence_level = self._calculate_dashboard_confidence(health_report, risk_indicators)
            
            # Create dashboard data
            dashboard_data = RiskDashboardData(
                overall_risk_level=overall_risk_level,
                risk_score=risk_score,
                timestamp=datetime.now(),
                risk_indicators=risk_indicators,
                active_alerts=active_alerts,
                trend_data=trend_data,
                health_summary=health_summary,
                recommendations=recommendations,
                confidence_level=confidence_level
            )
            
            # Store for trend analysis
            self._update_dashboard_history(dashboard_data)
            
            self.logger.info(f"Dashboard data generated: {overall_risk_level.value} risk level ({risk_score:.2f})")
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Error generating dashboard data: {str(e)}")
            return self._create_error_dashboard_data(str(e))
    
    def _collect_risk_indicators(self, health_report: ProjectHealthReport) -> List[RiskIndicator]:
        """Collect all risk indicators from various sources"""
        indicators = []
        
        try:
            # Health-based risk indicators
            for metric in health_report.metrics:
                risk_level = self._metric_to_risk_level(metric.status)
                
                # Create risk indicator for problematic metrics
                if risk_level != RiskLevel.LOW:
                    indicators.append(RiskIndicator(
                        name=f"{metric.name}_risk",
                        level=risk_level,
                        score=self._calculate_risk_score(metric.value, metric.name),
                        description=f"{metric.name.replace('_', ' ').title()} shows {metric.status.value} status",
                        impact=self._assess_risk_impact(metric.name, risk_level),
                        likelihood=metric.confidence,
                        mitigation=self._suggest_risk_mitigation(metric.name, risk_level),
                        last_updated=datetime.now()
                    ))
            
            # Predictive risk indicators
            try:
                predictive_assessment = self.predictive_risk_assessment.assess_risk({})
                if predictive_assessment.risk_factors:
                    for i, risk_factor in enumerate(predictive_assessment.risk_factors[:5]):  # Top 5
                        risk_level = self._score_to_risk_level(predictive_assessment.overall_risk_level)
                        
                        indicators.append(RiskIndicator(
                            name=f"predictive_risk_{i+1}",
                            level=risk_level,
                            score=predictive_assessment.overall_risk_level,
                            description=risk_factor,
                            impact="Potential future issues based on trend analysis",
                            likelihood=predictive_assessment.confidence,
                            mitigation="Monitor trends and address underlying patterns",
                            last_updated=datetime.now()
                        ))
            except Exception:
                pass  # Graceful degradation
            
            # Trend-based risk indicators
            if health_report.trend_analysis.get('trend') == 'declining':
                velocity = abs(health_report.trend_analysis.get('velocity', 0))
                risk_level = RiskLevel.HIGH if velocity > 0.1 else RiskLevel.MEDIUM
                
                indicators.append(RiskIndicator(
                    name="declining_health_trend",
                    level=risk_level,
                    score=velocity * 2,  # Amplify for visibility
                    description="Project health showing declining trend",
                    impact="Continued degradation may affect project success",
                    likelihood=health_report.trend_analysis.get('confidence', 0.5),
                    mitigation="Investigate root causes and implement corrective actions",
                    last_updated=datetime.now()
                ))
            
            # System-level risks
            if health_report.overall_score < 0.6:
                indicators.append(RiskIndicator(
                    name="overall_health_risk",
                    level=RiskLevel.HIGH,
                    score=1.0 - health_report.overall_score,
                    description="Overall project health below acceptable threshold",
                    impact="Multiple areas need attention to maintain project quality",
                    likelihood=health_report.confidence_level,
                    mitigation="Implement comprehensive improvement plan",
                    last_updated=datetime.now()
                ))
            
        except Exception as e:
            self.logger.warning(f"Error collecting risk indicators: {str(e)}")
            # Add fallback indicator
            indicators.append(RiskIndicator(
                name="assessment_error",
                level=RiskLevel.MEDIUM,
                score=0.5,
                description="Risk assessment temporarily impaired",
                impact="Reduced visibility into project risks",
                likelihood=1.0,
                mitigation="Resolve system issues for complete risk monitoring",
                last_updated=datetime.now()
            ))
        
        return indicators
    
    def _metric_to_risk_level(self, health_status: HealthStatus) -> RiskLevel:
        """Convert health status to risk level"""
        mapping = {
            HealthStatus.EXCELLENT: RiskLevel.LOW,
            HealthStatus.GOOD: RiskLevel.LOW,
            HealthStatus.FAIR: RiskLevel.MEDIUM,
            HealthStatus.POOR: RiskLevel.HIGH,
            HealthStatus.CRITICAL: RiskLevel.CRITICAL
        }
        return mapping.get(health_status, RiskLevel.MEDIUM)
    
    def _score_to_risk_level(self, score: float) -> RiskLevel:
        """Convert numerical score to risk level"""
        if score >= self.risk_thresholds['critical']:
            return RiskLevel.CRITICAL
        elif score >= self.risk_thresholds['high']:
            return RiskLevel.HIGH
        elif score >= self.risk_thresholds['medium']:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _calculate_risk_score(self, metric_value: float, metric_name: str) -> float:
        """Calculate risk score from metric value"""
        # Convert metric to risk score (higher risk = higher score)
        if metric_name in ['complexity_score', 'risk_level']:
            return metric_value  # Already risk-oriented
        else:
            return 1.0 - metric_value  # Invert quality metrics
    
    def _assess_risk_impact(self, metric_name: str, risk_level: RiskLevel) -> str:
        """Assess the impact of a risk"""
        impacts = {
            'code_quality': {
                RiskLevel.CRITICAL: "Severe maintainability issues and potential bugs",
                RiskLevel.HIGH: "Significant technical debt and maintenance burden",
                RiskLevel.MEDIUM: "Moderate impact on code maintainability",
                RiskLevel.LOW: "Minor quality concerns"
            },
            'test_coverage': {
                RiskLevel.CRITICAL: "High risk of undetected bugs and regressions",
                RiskLevel.HIGH: "Limited confidence in code changes",
                RiskLevel.MEDIUM: "Some areas may lack adequate testing",
                RiskLevel.LOW: "Good test coverage with minor gaps"
            },
            'documentation_coverage': {
                RiskLevel.CRITICAL: "Severe knowledge gaps and onboarding difficulties",
                RiskLevel.HIGH: "Significant impact on team productivity",
                RiskLevel.MEDIUM: "Some documentation gaps may slow development",
                RiskLevel.LOW: "Minor documentation improvements needed"
            }
        }
        
        return impacts.get(metric_name, {}).get(risk_level, "Unknown impact level")
    
    def _suggest_risk_mitigation(self, metric_name: str, risk_level: RiskLevel) -> str:
        """Suggest mitigation strategies for risks"""
        mitigations = {
            'code_quality': "Implement code reviews, refactoring, and static analysis",
            'test_coverage': "Add unit tests and improve test automation",
            'documentation_coverage': "Update documentation and establish documentation standards",
            'complexity_score': "Refactor complex functions and improve code structure",
            'risk_level': "Address underlying risk factors and monitor trends"
        }
        
        return mitigations.get(metric_name, "Consult with team for appropriate mitigation strategy")
    
    def _calculate_overall_risk(self, risk_indicators: List[RiskIndicator]) -> Tuple[RiskLevel, float]:
        """Calculate overall risk level and score"""
        try:
            if not risk_indicators:
                return RiskLevel.LOW, 0.2
            
            # Weight risks by severity
            weights = {
                RiskLevel.CRITICAL: 1.0,
                RiskLevel.HIGH: 0.8,
                RiskLevel.MEDIUM: 0.5,
                RiskLevel.LOW: 0.2
            }
            
            total_weighted_score = 0.0
            total_weight = 0.0
            
            for indicator in risk_indicators:
                weight = weights.get(indicator.level, 0.5)
                weighted_score = indicator.score * weight * indicator.likelihood
                total_weighted_score += weighted_score
                total_weight += weight
            
            if total_weight > 0:
                overall_score = total_weighted_score / total_weight
            else:
                overall_score = 0.3
            
            # Determine overall risk level
            overall_risk_level = self._score_to_risk_level(overall_score)
            
            return overall_risk_level, overall_score
            
        except Exception as e:
            self.logger.error(f"Error calculating overall risk: {str(e)}")
            return RiskLevel.MEDIUM, 0.5
    
    def _generate_alerts(self, risk_indicators: List[RiskIndicator], health_report: ProjectHealthReport) -> List[DashboardAlert]:
        """Generate actionable alerts based on current state"""
        alerts = []
        
        try:
            # Generate alerts from risk indicators
            for indicator in risk_indicators:
                if indicator.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                    priority = AlertPriority.CRITICAL if indicator.level == RiskLevel.CRITICAL else AlertPriority.ERROR
                    
                    alerts.append(DashboardAlert(
                        id=f"risk_{indicator.name}_{datetime.now().timestamp()}",
                        title=f"{indicator.level.value.upper()}: {indicator.name.replace('_', ' ').title()}",
                        message=f"{indicator.description}. {indicator.mitigation}",
                        priority=priority,
                        risk_level=indicator.level,
                        timestamp=datetime.now(),
                        source="risk_assessment",
                        actionable=True,
                        auto_resolvable=False
                    ))
            
            # Generate alerts from health trends
            if health_report.trend_analysis.get('trend') == 'declining':
                alerts.append(DashboardAlert(
                    id=f"trend_alert_{datetime.now().timestamp()}",
                    title="Declining Health Trend Detected",
                    message="Project health has been declining. Review risk factors and implement corrective actions.",
                    priority=AlertPriority.WARNING,
                    risk_level=RiskLevel.MEDIUM,
                    timestamp=datetime.now(),
                    source="trend_analysis",
                    actionable=True,
                    auto_resolvable=False
                ))
            
            # Generate alerts for multiple risk factors
            if len(risk_indicators) > 5:
                alerts.append(DashboardAlert(
                    id=f"multiple_risks_{datetime.now().timestamp()}",
                    title="Multiple Risk Factors Detected",
                    message=f"{len(risk_indicators)} risk factors identified. Prioritize mitigation efforts.",
                    priority=AlertPriority.WARNING,
                    risk_level=RiskLevel.MEDIUM,
                    timestamp=datetime.now(),
                    source="risk_aggregation",
                    actionable=True,
                    auto_resolvable=False
                ))
            
        except Exception as e:
            self.logger.warning(f"Error generating alerts: {str(e)}")
            alerts.append(DashboardAlert(
                id=f"system_error_{datetime.now().timestamp()}",
                title="Alert System Error",
                message=f"Unable to generate complete alerts: {str(e)}",
                priority=AlertPriority.WARNING,
                risk_level=RiskLevel.MEDIUM,
                timestamp=datetime.now(),
                source="system",
                actionable=False,
                auto_resolvable=True
            ))
        
        # Limit alerts to prevent overwhelm
        return sorted(alerts, key=lambda x: (x.priority.value, x.risk_level.value), reverse=True)[:10]
    
    def _analyze_risk_trends(self) -> Dict[str, Any]:
        """Analyze risk trends over time"""
        try:
            if len(self.dashboard_history) < 3:
                return {
                    'trend': 'insufficient_data',
                    'risk_velocity': 0.0,
                    'prediction': 'unknown',
                    'confidence': 0.3
                }
            
            # Analyze risk score trends
            recent_scores = [data.risk_score for data in self.dashboard_history[-7:]]
            if len(recent_scores) >= 2:
                risk_velocity = recent_scores[-1] - recent_scores[0]
                risk_velocity /= len(recent_scores)
            else:
                risk_velocity = 0.0
            
            # Determine trend
            if risk_velocity > 0.05:
                trend = 'increasing'
                prediction = 'risk_escalation'
            elif risk_velocity < -0.05:
                trend = 'decreasing' 
                prediction = 'risk_mitigation'
            else:
                trend = 'stable'
                prediction = 'stable_risk'
            
            # Alert frequency analysis
            recent_alert_counts = [len(data.active_alerts) for data in self.dashboard_history[-5:]]
            avg_alert_count = sum(recent_alert_counts) / len(recent_alert_counts) if recent_alert_counts else 0
            
            return {
                'trend': trend,
                'risk_velocity': risk_velocity,
                'prediction': prediction,
                'confidence': min(0.9, 0.4 + 0.1 * len(recent_scores)),
                'avg_alert_count': avg_alert_count,
                'risk_pattern': self._identify_risk_patterns()
            }
            
        except Exception as e:
            self.logger.warning(f"Error analyzing risk trends: {str(e)}")
            return {
                'trend': 'unknown',
                'risk_velocity': 0.0,
                'prediction': 'unknown',
                'confidence': 0.3
            }
    
    def _identify_risk_patterns(self) -> str:
        """Identify recurring risk patterns"""
        try:
            if len(self.dashboard_history) < 5:
                return "insufficient_data"
            
            # Simple pattern analysis
            risk_levels = [data.overall_risk_level.value for data in self.dashboard_history[-10:]]
            
            # Check for recurring patterns
            if risk_levels.count('critical') > 2:
                return "recurring_critical_risks"
            elif risk_levels.count('high') > 3:
                return "frequent_high_risks"
            elif len(set(risk_levels)) == 1:
                return "stable_risk_pattern"
            else:
                return "variable_risk_pattern"
                
        except Exception:
            return "unknown_pattern"
    
    def _create_health_summary(self, health_report: ProjectHealthReport) -> Dict[str, Any]:
        """Create concise health summary for dashboard"""
        return {
            'overall_status': health_report.overall_status.value,
            'overall_score': health_report.overall_score,
            'confidence': health_report.confidence_level,
            'metric_count': len(health_report.metrics),
            'risk_factor_count': len(health_report.risk_factors),
            'trend': health_report.trend_analysis.get('trend', 'unknown'),
            'last_updated': health_report.timestamp.isoformat()
        }
    
    def _generate_risk_recommendations(self, risk_indicators: List[RiskIndicator], alerts: List[DashboardAlert]) -> List[str]:
        """Generate actionable recommendations for risk mitigation"""
        recommendations = []
        
        try:
            # Priority-based recommendations
            critical_risks = [r for r in risk_indicators if r.level == RiskLevel.CRITICAL]
            high_risks = [r for r in risk_indicators if r.level == RiskLevel.HIGH]
            
            if critical_risks:
                recommendations.append(f"URGENT: Address {len(critical_risks)} critical risk(s) immediately")
                for risk in critical_risks[:2]:  # Top 2
                    recommendations.append(f"• {risk.mitigation}")
            
            if high_risks:
                recommendations.append(f"High Priority: Mitigate {len(high_risks)} high-risk area(s)")
                
            if len(alerts) > 5:
                recommendations.append("Review and prioritize active alerts to reduce system noise")
            
            # General recommendations based on patterns
            if not critical_risks and not high_risks:
                recommendations.append("Maintain current risk monitoring practices")
                recommendations.append("Continue proactive health monitoring")
            
            if len(recommendations) == 0:
                recommendations.append("No immediate risk mitigation actions required")
            
        except Exception as e:
            self.logger.warning(f"Error generating risk recommendations: {str(e)}")
            recommendations.append("Risk recommendations temporarily unavailable")
        
        return recommendations[:6]  # Limit to top 6
    
    def _calculate_dashboard_confidence(self, health_report: ProjectHealthReport, risk_indicators: List[RiskIndicator]) -> float:
        """Calculate overall confidence in dashboard data"""
        try:
            confidence_factors = [health_report.confidence_level]
            confidence_factors.extend([indicator.likelihood for indicator in risk_indicators])
            
            # Factor in data quality
            data_quality = 1.0
            if len(risk_indicators) == 0:
                data_quality *= 0.7  # Reduce confidence if no risks detected
            
            # Factor in historical data availability
            history_factor = min(1.0, len(self.dashboard_history) / 10.0)  # Full confidence at 10+ data points
            
            base_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
            return base_confidence * data_quality * (0.5 + 0.5 * history_factor)
            
        except Exception:
            return 0.6  # Safe default
    
    def _update_dashboard_history(self, dashboard_data: RiskDashboardData):
        """Update dashboard history for trend analysis"""
        try:
            self.dashboard_history.append(dashboard_data)
            
            # Trim history to last 30 days
            cutoff_date = datetime.now() - timedelta(days=30)
            self.dashboard_history = [
                data for data in self.dashboard_history 
                if data.timestamp > cutoff_date
            ]
            
        except Exception as e:
            self.logger.warning(f"Error updating dashboard history: {str(e)}")
    
    def _create_error_dashboard_data(self, error_message: str) -> RiskDashboardData:
        """Create error dashboard data when generation fails"""
        return RiskDashboardData(
            overall_risk_level=RiskLevel.MEDIUM,
            risk_score=0.5,
            timestamp=datetime.now(),
            risk_indicators=[RiskIndicator(
                name="system_error",
                level=RiskLevel.MEDIUM,
                score=0.5,
                description=f"Dashboard error: {error_message}",
                impact="Reduced risk monitoring capabilities",
                likelihood=1.0,
                mitigation="Resolve system issues for complete risk assessment",
                last_updated=datetime.now()
            )],
            active_alerts=[DashboardAlert(
                id=f"error_{datetime.now().timestamp()}",
                title="Dashboard System Error",
                message=f"Risk assessment temporarily impaired: {error_message}",
                priority=AlertPriority.WARNING,
                risk_level=RiskLevel.MEDIUM,
                timestamp=datetime.now(),
                source="system",
                actionable=True,
                auto_resolvable=False
            )],
            trend_data={'trend': 'error', 'confidence': 0.0},
            health_summary={'status': 'error', 'error': error_message},
            recommendations=["Resolve dashboard system issues"],
            confidence_level=0.3
        )
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get a quick dashboard summary"""
        try:
            dashboard_data = self.generate_dashboard_data()
            return {
                'risk_level': dashboard_data.overall_risk_level.value,
                'risk_score': dashboard_data.risk_score,
                'active_alerts': len(dashboard_data.active_alerts),
                'critical_alerts': len([a for a in dashboard_data.active_alerts if a.priority == AlertPriority.CRITICAL]),
                'confidence': dashboard_data.confidence_level,
                'trend': dashboard_data.trend_data.get('trend', 'unknown'),
                'top_recommendations': dashboard_data.recommendations[:3]
            }
        except Exception as e:
            return {
                'risk_level': 'error',
                'error': str(e),
                'confidence': 0.0
            }
    
    def export_dashboard_data(self, format_type: str = "json") -> str:
        """Export dashboard data in specified format"""
        try:
            dashboard_data = self.generate_dashboard_data()
            
            if format_type.lower() == "json":
                # Convert to JSON-serializable format
                export_data = {
                    'overall_risk_level': dashboard_data.overall_risk_level.value,
                    'risk_score': dashboard_data.risk_score,
                    'timestamp': dashboard_data.timestamp.isoformat(),
                    'confidence_level': dashboard_data.confidence_level,
                    'risk_indicators': [
                        {
                            'name': indicator.name,
                            'level': indicator.level.value,
                            'score': indicator.score,
                            'description': indicator.description,
                            'impact': indicator.impact,
                            'likelihood': indicator.likelihood,
                            'mitigation': indicator.mitigation
                        }
                        for indicator in dashboard_data.risk_indicators
                    ],
                    'active_alerts': [
                        {
                            'title': alert.title,
                            'message': alert.message,
                            'priority': alert.priority.value,
                            'risk_level': alert.risk_level.value,
                            'timestamp': alert.timestamp.isoformat(),
                            'actionable': alert.actionable
                        }
                        for alert in dashboard_data.active_alerts
                    ],
                    'trend_data': dashboard_data.trend_data,
                    'health_summary': dashboard_data.health_summary,
                    'recommendations': dashboard_data.recommendations
                }
                
                return json.dumps(export_data, indent=2)
            else:
                return f"Unsupported format: {format_type}"
                
        except Exception as e:
            return f"Export error: {str(e)}"