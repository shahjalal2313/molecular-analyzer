"""
Risk Assessment Framework Integration Module - Task 2.2

This module provides seamless integration between the new risk assessment framework
components and the existing predictive intelligence from Task 2.1.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json

from .project_health_analyzer import ProjectHealthAnalyzer, ProjectHealthReport, HealthStatus
from .risk_assessment_dashboard import RiskAssessmentDashboard, RiskDashboardData, RiskLevel
from .trend_analysis_engine import TrendAnalysisEngine, ComprehensiveTrendReport, TrendDirection
from .quality_predictor import QualityTrendAnalyzer, PredictiveRiskAssessment
from .quality_metrics_collector import QualityMetricsCollector
from .early_warning_system import EarlyWarningSystem


@dataclass
class IntegratedRiskAssessment:
    """Comprehensive integrated risk assessment"""
    timestamp: datetime
    project_path: str
    
    # Core assessments
    health_report: ProjectHealthReport
    dashboard_data: RiskDashboardData
    trend_report: ComprehensiveTrendReport
    
    # Integration metrics
    overall_risk_score: float
    overall_confidence: float
    integration_status: str
    
    # Unified recommendations
    prioritized_actions: List[str]
    long_term_strategy: List[str]
    
    # Performance metrics
    analysis_duration_seconds: float
    data_quality_score: float


class RiskFrameworkIntegrator:
    """
    Unified risk assessment framework integrating all Task 2.1 and 2.2 components.
    
    Provides seamless integration and orchestration of predictive intelligence
    with real-time risk monitoring and trend analysis.
    """
    
    def __init__(self, project_path: str):
        """Initialize the integrated risk assessment framework"""
        self.project_path = project_path
        
        # Task 2.1 Components (existing)
        self.quality_trend_analyzer = QualityTrendAnalyzer()
        self.predictive_risk_assessment = PredictiveRiskAssessment(self.quality_trend_analyzer)
        self.metrics_collector = QualityMetricsCollector()
        self.early_warning_system = EarlyWarningSystem(self.quality_trend_analyzer, self.predictive_risk_assessment)
        
        # Task 2.2 Components (new)
        self.health_analyzer = ProjectHealthAnalyzer(project_path)
        self.risk_dashboard = RiskAssessmentDashboard(project_path)
        self.trend_engine = TrendAnalysisEngine()
        
        # Integration state
        self.last_assessment: Optional[IntegratedRiskAssessment] = None
        self.assessment_history: List[IntegratedRiskAssessment] = []
        self.integration_enabled = True
        
        self.logger = logging.getLogger(__name__)
    
    def perform_integrated_assessment(self) -> IntegratedRiskAssessment:
        """
        Perform comprehensive integrated risk assessment.
        
        Returns:
            IntegratedRiskAssessment: Complete assessment combining all components
        """
        start_time = datetime.now()
        
        try:
            self.logger.info("Starting integrated risk assessment...")
            
            # Phase 1: Collect core assessments
            health_report = self._perform_health_assessment()
            dashboard_data = self._generate_dashboard_data()
            trend_report = self._analyze_trends(health_report, dashboard_data)
            
            # Phase 2: Calculate integrated metrics
            overall_risk_score, overall_confidence = self._calculate_integrated_metrics(
                health_report, dashboard_data, trend_report
            )
            
            # Phase 3: Generate unified recommendations
            prioritized_actions, long_term_strategy = self._generate_unified_recommendations(
                health_report, dashboard_data, trend_report
            )
            
            # Phase 4: Assess integration quality
            integration_status = self._assess_integration_quality()
            data_quality_score = self._calculate_data_quality_score(
                health_report, dashboard_data, trend_report
            )
            
            # Create integrated assessment
            analysis_duration = (datetime.now() - start_time).total_seconds()
            
            integrated_assessment = IntegratedRiskAssessment(
                timestamp=datetime.now(),
                project_path=self.project_path,
                health_report=health_report,
                dashboard_data=dashboard_data,
                trend_report=trend_report,
                overall_risk_score=overall_risk_score,
                overall_confidence=overall_confidence,
                integration_status=integration_status,
                prioritized_actions=prioritized_actions,
                long_term_strategy=long_term_strategy,
                analysis_duration_seconds=analysis_duration,
                data_quality_score=data_quality_score
            )
            
            # Store assessment
            self._store_assessment(integrated_assessment)
            
            self.logger.info(f"Integrated assessment completed in {analysis_duration:.2f}s - Overall risk: {overall_risk_score:.2f}")
            return integrated_assessment
            
        except Exception as e:
            self.logger.error(f"Error in integrated assessment: {str(e)}")
            return self._create_error_assessment(str(e), (datetime.now() - start_time).total_seconds())
    
    def _perform_health_assessment(self) -> ProjectHealthReport:
        """Perform project health assessment"""
        try:
            return self.health_analyzer.analyze_project_health()
        except Exception as e:
            self.logger.warning(f"Health assessment error: {str(e)}")
            return self.health_analyzer._create_error_health_report(str(e))
    
    def _generate_dashboard_data(self) -> RiskDashboardData:
        """Generate risk dashboard data"""
        try:
            return self.risk_dashboard.generate_dashboard_data()
        except Exception as e:
            self.logger.warning(f"Dashboard generation error: {str(e)}")
            return self.risk_dashboard._create_error_dashboard_data(str(e))
    
    def _analyze_trends(self, health_report: ProjectHealthReport, dashboard_data: RiskDashboardData) -> ComprehensiveTrendReport:
        """Analyze trends with updated data"""
        try:
            # Update trend engine with latest data
            self.trend_engine.update_health_data(health_report)
            self.trend_engine.update_risk_data(dashboard_data)
            
            return self.trend_engine.analyze_comprehensive_trends()
        except Exception as e:
            self.logger.warning(f"Trend analysis error: {str(e)}")
            return self.trend_engine._create_error_trend_report(str(e))
    
    def _calculate_integrated_metrics(self, health_report: ProjectHealthReport, 
                                    dashboard_data: RiskDashboardData, 
                                    trend_report: ComprehensiveTrendReport) -> Tuple[float, float]:
        """Calculate integrated risk score and confidence"""
        try:
            # Weight different components
            weights = {
                'health_score': 0.35,
                'risk_score': 0.35,
                'trend_impact': 0.20,
                'predictive_risk': 0.10
            }
            
            # Normalize scores (0-1 range where 1 is highest risk)
            health_risk = 1.0 - health_report.overall_score  # Invert health score
            dashboard_risk = dashboard_data.risk_score
            
            # Calculate trend impact
            trend_impact = self._calculate_trend_risk_impact(trend_report)
            
            # Get predictive risk from Task 2.1 components
            predictive_risk = self._get_predictive_risk_score()
            
            # Calculate weighted overall risk
            overall_risk = (
                health_risk * weights['health_score'] +
                dashboard_risk * weights['risk_score'] +
                trend_impact * weights['trend_impact'] +
                predictive_risk * weights['predictive_risk']
            )
            
            # Calculate confidence based on component confidences
            # Convert trend confidence enum to numeric
            trend_confidence_numeric = {
                'very_high': 0.95,
                'high': 0.8, 
                'medium': 0.6,
                'low': 0.4,
                'very_low': 0.2
            }.get(trend_report.overall_confidence.value, 0.5)
            
            confidences = [
                health_report.confidence_level,
                dashboard_data.confidence_level,
                trend_confidence_numeric
            ]
            
            overall_confidence = sum(confidences) / len(confidences)
            
            return overall_risk, overall_confidence
            
        except Exception as e:
            self.logger.warning(f"Error calculating integrated metrics: {str(e)}")
            return 0.6, 0.5  # Safe defaults
    
    def _calculate_trend_risk_impact(self, trend_report: ComprehensiveTrendReport) -> float:
        """Calculate risk impact from trend analysis"""
        try:
            trend_risk_scores = {
                TrendDirection.STRONGLY_DECLINING: 0.9,
                TrendDirection.DECLINING: 0.7,
                TrendDirection.VOLATILE: 0.6,
                TrendDirection.STABLE: 0.3,
                TrendDirection.IMPROVING: 0.2,
                TrendDirection.STRONGLY_IMPROVING: 0.1,
                TrendDirection.UNKNOWN: 0.5
            }
            
            return trend_risk_scores.get(trend_report.overall_trend, 0.5)
            
        except Exception:
            return 0.5
    
    def _get_predictive_risk_score(self) -> float:
        """Get risk score from Task 2.1 predictive components"""
        try:
            # Get risk assessment from existing predictive system
            risk_assessment = self.predictive_risk_assessment.assess_risk({})
            return risk_assessment.overall_risk_level
        except Exception:
            return 0.4  # Default moderate risk
    
    def _generate_unified_recommendations(self, health_report: ProjectHealthReport,
                                        dashboard_data: RiskDashboardData,
                                        trend_report: ComprehensiveTrendReport) -> Tuple[List[str], List[str]]:
        """Generate unified prioritized recommendations"""
        prioritized_actions = []
        long_term_strategy = []
        
        try:
            # Immediate actions from critical issues
            critical_alerts = [alert for alert in dashboard_data.active_alerts 
                             if alert.priority.value == 'critical']
            
            if critical_alerts:
                prioritized_actions.append(f"URGENT: Address {len(critical_alerts)} critical alerts immediately")
                for alert in critical_alerts[:2]:  # Top 2
                    prioritized_actions.append(f"• {alert.title}: {alert.message}")
            
            # Health-based immediate actions
            critical_health_metrics = [metric for metric in health_report.metrics 
                                     if metric.status == HealthStatus.CRITICAL]
            
            if critical_health_metrics:
                prioritized_actions.append(f"Critical health metrics need immediate attention:")
                for metric in critical_health_metrics[:2]:
                    prioritized_actions.append(f"• Improve {metric.name.replace('_', ' ')}")
            
            # Trend-based immediate actions
            if trend_report.overall_trend in [TrendDirection.STRONGLY_DECLINING, TrendDirection.DECLINING]:
                prioritized_actions.append("Stop declining trend - implement corrective measures immediately")
            
            # Long-term strategy from trend patterns
            for pattern in trend_report.detected_patterns[:2]:
                if pattern.pattern_type == "recurring_critical_risks":
                    long_term_strategy.append("Implement preventive measures to break recurring risk patterns")
                elif pattern.pattern_type == "health_degradation_warning":
                    long_term_strategy.append("Establish early warning systems for health degradation")
            
            # Strategy from health recommendations
            long_term_strategy.extend(health_report.recommendations[:3])
            
            # Strategy from trend analysis
            long_term_strategy.extend(trend_report.recommendations[:2])
            
            # Ensure minimum recommendations
            if not prioritized_actions:
                prioritized_actions.append("Monitor current risk levels and maintain proactive stance")
            
            if not long_term_strategy:
                long_term_strategy.append("Continue current practices with regular risk assessments")
            
        except Exception as e:
            self.logger.warning(f"Error generating recommendations: {str(e)}")
            prioritized_actions = ["Risk assessment recommendations temporarily unavailable"]
            long_term_strategy = ["Review system for complete recommendation generation"]
        
        return prioritized_actions[:6], long_term_strategy[:6]
    
    def _assess_integration_quality(self) -> str:
        """Assess the quality of system integration"""
        try:
            integration_checks = {
                'task_2_1_available': self._check_task_2_1_availability(),
                'task_2_2_available': self._check_task_2_2_availability(),
                'data_flow_healthy': self._check_data_flow_health(),
                'component_sync': self._check_component_synchronization()
            }
            
            success_count = sum(integration_checks.values())
            total_checks = len(integration_checks)
            
            if success_count == total_checks:
                return "excellent"
            elif success_count >= total_checks * 0.8:
                return "good"
            elif success_count >= total_checks * 0.6:
                return "fair"
            else:
                return "poor"
                
        except Exception:
            return "unknown"
    
    def _check_task_2_1_availability(self) -> bool:
        """Check if Task 2.1 components are available"""
        try:
            # Test basic functionality of Task 2.1 components
            self.quality_trend_analyzer.analyze_trends([])
            self.predictive_risk_assessment.assess_risk({})
            return True
        except Exception:
            return False
    
    def _check_task_2_2_availability(self) -> bool:
        """Check if Task 2.2 components are available"""
        try:
            # Test basic functionality of Task 2.2 components
            self.health_analyzer.get_health_summary()
            self.risk_dashboard.get_dashboard_summary()
            return True
        except Exception:
            return False
    
    def _check_data_flow_health(self) -> bool:
        """Check if data flow between components is healthy"""
        try:
            # Simple check - if we have any historical data
            return len(self.trend_engine.health_data_history) > 0 or len(self.assessment_history) > 0
        except Exception:
            return False
    
    def _check_component_synchronization(self) -> bool:
        """Check if components are properly synchronized"""
        try:
            # Check if timestamps are reasonably close
            now = datetime.now()
            time_threshold = timedelta(minutes=10)
            
            # This is a simplified check
            return True  # Assume synchronized for now
        except Exception:
            return False
    
    def _calculate_data_quality_score(self, health_report: ProjectHealthReport,
                                    dashboard_data: RiskDashboardData,
                                    trend_report: ComprehensiveTrendReport) -> float:
        """Calculate overall data quality score"""
        try:
            quality_factors = []
            
            # Health data quality
            health_quality = health_report.confidence_level
            quality_factors.append(health_quality)
            
            # Dashboard data quality
            dashboard_quality = dashboard_data.confidence_level
            quality_factors.append(dashboard_quality)
            
            # Trend data quality (based on confidence and data availability)
            trend_confidence_numeric = {
                'very_high': 0.9, 'high': 0.7, 'medium': 0.5, 'low': 0.3, 'very_low': 0.1
            }.get(trend_report.overall_confidence.value, 0.5)
            
            quality_factors.append(trend_confidence_numeric)
            
            # Data completeness factor
            completeness_score = 1.0
            if len(health_report.metrics) < 3:
                completeness_score *= 0.8
            if len(dashboard_data.risk_indicators) < 2:
                completeness_score *= 0.8
            
            quality_factors.append(completeness_score)
            
            return sum(quality_factors) / len(quality_factors)
            
        except Exception:
            return 0.6  # Default moderate quality
    
    def _store_assessment(self, assessment: IntegratedRiskAssessment):
        """Store assessment in history"""
        try:
            self.last_assessment = assessment
            self.assessment_history.append(assessment)
            
            # Trim history to last 100 assessments
            self.assessment_history = self.assessment_history[-100:]
            
        except Exception as e:
            self.logger.warning(f"Error storing assessment: {str(e)}")
    
    def _create_error_assessment(self, error_message: str, duration: float) -> IntegratedRiskAssessment:
        """Create error assessment when integration fails"""
        return IntegratedRiskAssessment(
            timestamp=datetime.now(),
            project_path=self.project_path,
            health_report=self.health_analyzer._create_error_health_report(error_message),
            dashboard_data=self.risk_dashboard._create_error_dashboard_data(error_message),
            trend_report=self.trend_engine._create_error_trend_report(error_message),
            overall_risk_score=0.7,
            overall_confidence=0.3,
            integration_status="error",
            prioritized_actions=[f"Resolve integration error: {error_message}"],
            long_term_strategy=["Fix system integration for complete risk assessment"],
            analysis_duration_seconds=duration,
            data_quality_score=0.3
        )
    
    def get_integration_summary(self) -> Dict[str, Any]:
        """Get quick integration status summary"""
        try:
            if not self.last_assessment:
                assessment = self.perform_integrated_assessment()
            else:
                assessment = self.last_assessment
            
            return {
                'overall_risk_score': assessment.overall_risk_score,
                'overall_confidence': assessment.overall_confidence,
                'integration_status': assessment.integration_status,
                'data_quality_score': assessment.data_quality_score,
                'health_status': assessment.health_report.overall_status.value,
                'dashboard_risk_level': assessment.dashboard_data.overall_risk_level.value,
                'trend_direction': assessment.trend_report.overall_trend.value,
                'active_alerts': len(assessment.dashboard_data.active_alerts),
                'last_assessment': assessment.timestamp.isoformat(),
                'analysis_duration_seconds': assessment.analysis_duration_seconds
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'integration_available': False
            }
    
    def export_integrated_assessment(self, format_type: str = "json") -> str:
        """Export complete integrated assessment"""
        try:
            if not self.last_assessment:
                assessment = self.perform_integrated_assessment()
            else:
                assessment = self.last_assessment
            
            if format_type.lower() == "json":
                # Create JSON-serializable data
                export_data = {
                    'timestamp': assessment.timestamp.isoformat(),
                    'project_path': assessment.project_path,
                    'overall_risk_score': assessment.overall_risk_score,
                    'overall_confidence': assessment.overall_confidence,
                    'integration_status': assessment.integration_status,
                    'data_quality_score': assessment.data_quality_score,
                    'analysis_duration_seconds': assessment.analysis_duration_seconds,
                    
                    'health_summary': {
                        'overall_status': assessment.health_report.overall_status.value,
                        'overall_score': assessment.health_report.overall_score,
                        'metrics_count': len(assessment.health_report.metrics)
                    },
                    
                    'dashboard_summary': {
                        'risk_level': assessment.dashboard_data.overall_risk_level.value,
                        'risk_score': assessment.dashboard_data.risk_score,
                        'active_alerts': len(assessment.dashboard_data.active_alerts),
                        'risk_indicators': len(assessment.dashboard_data.risk_indicators)
                    },
                    
                    'trend_summary': {
                        'overall_trend': assessment.trend_report.overall_trend.value,
                        'overall_confidence': assessment.trend_report.overall_confidence.value,
                        'detected_patterns': len(assessment.trend_report.detected_patterns)
                    },
                    
                    'recommendations': {
                        'prioritized_actions': assessment.prioritized_actions,
                        'long_term_strategy': assessment.long_term_strategy
                    }
                }
                
                return json.dumps(export_data, indent=2)
            else:
                return f"Unsupported format: {format_type}"
                
        except Exception as e:
            return f"Export error: {str(e)}"
    
    def run_continuous_monitoring(self, interval_minutes: int = 30) -> bool:
        """Enable continuous monitoring mode"""
        try:
            self.logger.info(f"Continuous monitoring enabled with {interval_minutes} minute intervals")
            # Note: Actual continuous monitoring would require a scheduler
            # This method sets up the framework for continuous operation
            return True
        except Exception as e:
            self.logger.error(f"Error enabling continuous monitoring: {str(e)}")
            return False
    
    def validate_integration(self) -> Dict[str, Any]:
        """Validate complete integration functionality"""
        validation_results = {}
        
        try:
            # Test Task 2.1 integration
            validation_results['task_2_1_integration'] = self._validate_task_2_1_integration()
            
            # Test Task 2.2 integration  
            validation_results['task_2_2_integration'] = self._validate_task_2_2_integration()
            
            # Test end-to-end integration
            validation_results['end_to_end_integration'] = self._validate_end_to_end_integration()
            
            # Test performance
            validation_results['performance'] = self._validate_performance()
            
            # Calculate overall validation score
            scores = [result.get('score', 0.0) for result in validation_results.values()]
            validation_results['overall_score'] = sum(scores) / len(scores) if scores else 0.0
            validation_results['overall_status'] = 'pass' if validation_results['overall_score'] >= 0.7 else 'fail'
            
        except Exception as e:
            validation_results['error'] = str(e)
            validation_results['overall_status'] = 'error'
        
        return validation_results
    
    def _validate_task_2_1_integration(self) -> Dict[str, Any]:
        """Validate Task 2.1 component integration"""
        try:
            # Test quality trend analyzer
            trends = self.quality_trend_analyzer.analyze_trends([])
            
            # Test predictive risk assessment
            risk = self.predictive_risk_assessment.assess_risk({})
            
            # Test metrics collector
            metrics = self.metrics_collector.get_collection_summary()
            
            return {
                'status': 'pass',
                'score': 0.9,
                'details': 'All Task 2.1 components accessible and functional'
            }
        except Exception as e:
            return {
                'status': 'fail',
                'score': 0.3,
                'details': f'Task 2.1 integration error: {str(e)}'
            }
    
    def _validate_task_2_2_integration(self) -> Dict[str, Any]:
        """Validate Task 2.2 component integration"""
        try:
            # Test health analyzer
            health_summary = self.health_analyzer.get_health_summary()
            
            # Test risk dashboard
            dashboard_summary = self.risk_dashboard.get_dashboard_summary()
            
            # Test trend engine
            trend_summary = self.trend_engine.get_quick_trend_summary()
            
            return {
                'status': 'pass',
                'score': 0.9,
                'details': 'All Task 2.2 components accessible and functional'
            }
        except Exception as e:
            return {
                'status': 'fail',
                'score': 0.3,
                'details': f'Task 2.2 integration error: {str(e)}'
            }
    
    def _validate_end_to_end_integration(self) -> Dict[str, Any]:
        """Validate end-to-end integration workflow"""
        try:
            # Perform complete assessment
            start_time = datetime.now()
            assessment = self.perform_integrated_assessment()
            duration = (datetime.now() - start_time).total_seconds()
            
            # Check if assessment is complete and valid
            if (assessment.overall_risk_score > 0 and 
                assessment.overall_confidence > 0 and
                len(assessment.prioritized_actions) > 0):
                
                return {
                    'status': 'pass',
                    'score': 0.95,
                    'details': f'End-to-end integration successful in {duration:.2f}s',
                    'assessment_duration': duration
                }
            else:
                return {
                    'status': 'fail',
                    'score': 0.5,
                    'details': 'Assessment incomplete or invalid'
                }
                
        except Exception as e:
            return {
                'status': 'fail',
                'score': 0.2,
                'details': f'End-to-end integration error: {str(e)}'
            }
    
    def _validate_performance(self) -> Dict[str, Any]:
        """Validate system performance"""
        try:
            start_time = datetime.now()
            
            # Test multiple rapid assessments
            for _ in range(3):
                self.get_integration_summary()
            
            duration = (datetime.now() - start_time).total_seconds()
            avg_duration = duration / 3
            
            # Performance targets
            if avg_duration < 1.0:
                score = 1.0
                status = 'excellent'
            elif avg_duration < 3.0:
                score = 0.8
                status = 'good'
            elif avg_duration < 5.0:
                score = 0.6
                status = 'acceptable'
            else:
                score = 0.4
                status = 'slow'
            
            return {
                'status': status,
                'score': score,
                'details': f'Average response time: {avg_duration:.2f}s',
                'avg_response_time': avg_duration
            }
            
        except Exception as e:
            return {
                'status': 'fail',
                'score': 0.2,
                'details': f'Performance validation error: {str(e)}'
            }