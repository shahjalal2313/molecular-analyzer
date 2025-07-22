"""
Quality Integration Module - Task 2.1.4

Integrates predictive intelligence with existing quality assurance system,
creating a unified predictive quality management platform.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .quality_predictor import QualityTrendAnalyzer, PredictiveRiskAssessment, QualityMetrics
from .early_warning_system import EarlyWarningSystem, AlertManager, Alert, AlertSeverity

# Import existing QA system
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from doc_quality_assurance import IntegratedDocumentationQualityAssurance


@dataclass
class PredictiveQualityReport:
    """Comprehensive predictive quality assessment report"""
    timestamp: datetime
    current_metrics: QualityMetrics
    predicted_metrics_7d: QualityMetrics
    trend_analysis: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    active_alerts: List[Alert]
    recommendations: List[str]
    confidence_level: float
    overall_health_score: float


class PredictiveQualityIntegrator:
    """
    Integrates predictive intelligence with existing quality assurance system.
    
    Capabilities:
    - Seamless integration with existing QA workflows
    - Predictive enhancement of quality metrics
    - Automated quality trend monitoring
    - Early warning integration with QA reports
    - Unified quality dashboard with predictions
    """
    
    def __init__(self, project_root: str):
        """Initialize the predictive quality integrator"""
        self.project_root = project_root
        
        # Initialize existing QA system
        self.qa_system = IntegratedDocumentationQualityAssurance(project_root)
        
        # Initialize predictive components
        self.quality_analyzer = QualityTrendAnalyzer()
        self.risk_assessor = PredictiveRiskAssessment(self.quality_analyzer)
        self.early_warning = EarlyWarningSystem(self.quality_analyzer, self.risk_assessor)
        self.alert_manager = AlertManager(self.early_warning)
        
        # Integration settings
        self.integration_config = {
            'auto_update_baseline': True,
            'prediction_horizon_days': 7,
            'quality_sync_interval': 3600,  # 1 hour
            'alert_integration_enabled': True,
            'trend_history_days': 30
        }
        
        # Start monitoring
        self._initialize_integration()
    
    def _initialize_integration(self) -> None:
        """Initialize integration between systems"""
        # Load current quality state into predictive system
        self._sync_quality_metrics()
        
        # Start early warning monitoring
        if self.integration_config['alert_integration_enabled']:
            self.early_warning.start_monitoring(check_interval_seconds=300)  # 5 minutes
        
        # Register for quality updates
        self._setup_quality_monitoring()
    
    def _sync_quality_metrics(self) -> None:
        """Sync current quality metrics to predictive system"""
        try:
            # Get current QA results
            qa_results = self.qa_system.perform_comprehensive_qa()
            
            # Extract metrics
            overall_assessment = qa_results['overall_assessment']
            detailed_metrics = qa_results['detailed_metrics']
            
            # Create quality metrics object
            current_metrics = QualityMetrics(
                timestamp=datetime.now(),
                doc_coverage=overall_assessment['coverage_percentage'],
                code_quality_score=overall_assessment['quality_score'] * 100,
                test_coverage=self._estimate_test_coverage(),
                complexity_score=self._estimate_complexity_score(detailed_metrics),
                maintainability_index=detailed_metrics['quality'].dimension_scores.get('maintainability', 0.8) * 100,
                technical_debt_ratio=self._estimate_technical_debt(detailed_metrics)
            )
            
            # Add to trend analyzer
            self.quality_analyzer.add_quality_data(current_metrics)
            
        except Exception as e:
            print(f"Warning: Could not sync quality metrics: {e}")
    
    def _estimate_test_coverage(self) -> float:
        """Estimate test coverage (placeholder - would integrate with actual test tools)"""
        # In a real implementation, this would integrate with coverage.py or similar
        # For now, return a reasonable estimate based on project maturity
        return 75.0
    
    def _estimate_complexity_score(self, detailed_metrics: Dict[str, Any]) -> float:
        """Estimate complexity score from available metrics"""
        try:
            quality_metrics = detailed_metrics['quality']
            clarity_score = quality_metrics.dimension_scores.get('clarity', 0.8)
            # Convert clarity to complexity (inverse relationship)
            complexity = (1.0 - clarity_score) * 40  # Scale to 0-40 range
            return max(10, min(40, complexity))
        except:
            return 20.0  # Default moderate complexity
    
    def _estimate_technical_debt(self, detailed_metrics: Dict[str, Any]) -> float:
        """Estimate technical debt ratio from available metrics"""
        try:
            completeness = detailed_metrics['completeness']
            style_stats = detailed_metrics['style']['statistics']
            
            # Calculate debt based on incompleteness and violations
            coverage_debt = (100 - completeness['coverage'].coverage_percentage) * 0.3
            style_debt = min(20, style_stats['violations_found'] * 0.5)
            
            total_debt = coverage_debt + style_debt
            return min(30, max(5, total_debt))
        except:
            return 15.0  # Default moderate debt
    
    def _setup_quality_monitoring(self) -> None:
        """Setup automatic quality monitoring and updates"""
        # This would typically run in a background thread
        # For now, we'll trigger updates manually or on-demand
        pass
    
    def generate_predictive_quality_report(self) -> PredictiveQualityReport:
        """
        Generate comprehensive predictive quality report.
        
        Returns:
            Complete predictive quality assessment
        """
        # Get current quality trends
        quality_trends = self.quality_analyzer.get_overall_quality_trend()
        
        # Get risk assessment
        risks = self.risk_assessor.assess_risks()
        risk_summary = self.risk_assessor.get_risk_summary()
        
        # Get active alerts
        active_alerts = self.early_warning.get_active_alerts()
        
        # Get current and predicted metrics
        if self.quality_analyzer.historical_data:
            current_metrics = self.quality_analyzer.historical_data[-1]
            
            # Create predicted metrics based on trends
            predicted_metrics = self._generate_predicted_metrics(quality_trends)
        else:
            # Fallback if no historical data
            current_metrics = self._create_baseline_metrics()
            predicted_metrics = current_metrics
        
        # Calculate overall health score
        health_score = self._calculate_overall_health_score(
            quality_trends, risk_summary, active_alerts
        )
        
        # Generate recommendations
        recommendations = self._generate_integrated_recommendations(
            quality_trends, risk_summary, active_alerts
        )
        
        # Calculate confidence level
        confidence = self._calculate_prediction_confidence(quality_trends)
        
        return PredictiveQualityReport(
            timestamp=datetime.now(),
            current_metrics=current_metrics,
            predicted_metrics_7d=predicted_metrics,
            trend_analysis=quality_trends,
            risk_assessment=risk_summary,
            active_alerts=active_alerts,
            recommendations=recommendations,
            confidence_level=confidence,
            overall_health_score=health_score
        )
    
    def _generate_predicted_metrics(self, quality_trends: Dict[str, Any]) -> QualityMetrics:
        """Generate predicted metrics based on trends"""
        individual_trends = quality_trends['individual_trends']
        
        predicted_metrics = QualityMetrics(
            timestamp=datetime.now() + timedelta(days=7),
            doc_coverage=individual_trends.get('doc_coverage', type('obj', (), {'predicted_value_7d': 80.0})).predicted_value_7d,
            code_quality_score=individual_trends.get('code_quality_score', type('obj', (), {'predicted_value_7d': 80.0})).predicted_value_7d,
            test_coverage=individual_trends.get('test_coverage', type('obj', (), {'predicted_value_7d': 75.0})).predicted_value_7d,
            complexity_score=individual_trends.get('complexity_score', type('obj', (), {'predicted_value_7d': 20.0})).predicted_value_7d,
            maintainability_index=individual_trends.get('maintainability_index', type('obj', (), {'predicted_value_7d': 80.0})).predicted_value_7d,
            technical_debt_ratio=individual_trends.get('technical_debt_ratio', type('obj', (), {'predicted_value_7d': 15.0})).predicted_value_7d
        )
        
        return predicted_metrics
    
    def _create_baseline_metrics(self) -> QualityMetrics:
        """Create baseline metrics when no historical data available"""
        return QualityMetrics(
            timestamp=datetime.now(),
            doc_coverage=80.0,
            code_quality_score=80.0,
            test_coverage=75.0,
            complexity_score=20.0,
            maintainability_index=80.0,
            technical_debt_ratio=15.0
        )
    
    def _calculate_overall_health_score(self, quality_trends: Dict[str, Any], 
                                      risk_summary: Dict[str, Any],
                                      active_alerts: List[Alert]) -> float:
        """Calculate overall project health score (0-100)"""
        # Base score from current quality
        if quality_trends.get('overall_trend'):
            base_score = quality_trends['overall_trend'].current_value
        else:
            base_score = 80.0
        
        # Penalties for risks and alerts
        risk_penalty = 0
        if risk_summary['overall_risk_level'] == 'critical':
            risk_penalty = 20
        elif risk_summary['overall_risk_level'] == 'high':
            risk_penalty = 15
        elif risk_summary['overall_risk_level'] == 'medium':
            risk_penalty = 10
        
        alert_penalty = 0
        for alert in active_alerts:
            if alert.severity == AlertSeverity.CRITICAL:
                alert_penalty += 5
            elif alert.severity == AlertSeverity.ERROR:
                alert_penalty += 3
            elif alert.severity == AlertSeverity.WARNING:
                alert_penalty += 1
        
        # Trend bonus/penalty
        trend_adjustment = 0
        individual_trends = quality_trends.get('individual_trends', {})
        improving_trends = sum(1 for trend in individual_trends.values() 
                             if hasattr(trend, 'trend_direction') and trend.trend_direction == 'improving')
        declining_trends = sum(1 for trend in individual_trends.values() 
                             if hasattr(trend, 'trend_direction') and trend.trend_direction == 'declining')
        
        trend_adjustment = (improving_trends - declining_trends) * 2
        
        final_score = base_score - risk_penalty - alert_penalty + trend_adjustment
        return max(0, min(100, final_score))
    
    def _generate_integrated_recommendations(self, quality_trends: Dict[str, Any],
                                           risk_summary: Dict[str, Any],
                                           active_alerts: List[Alert]) -> List[str]:
        """Generate integrated recommendations from all data sources"""
        recommendations = []
        
        # Critical alerts first
        critical_alerts = [a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]
        if critical_alerts:
            recommendations.append(
                f"🚨 URGENT: Address {len(critical_alerts)} critical quality alerts immediately"
            )
        
        # High-risk items
        if risk_summary['immediate_actions_needed']:
            recommendations.append(
                "⚡ IMMEDIATE ACTION: Quality risks detected that need attention within 24 hours"
            )
        
        # Trend-based recommendations
        individual_trends = quality_trends.get('individual_trends', {})
        declining_metrics = [
            name for name, trend in individual_trends.items()
            if hasattr(trend, 'trend_direction') and trend.trend_direction == 'declining'
        ]
        
        if declining_metrics:
            recommendations.append(
                f"📉 MONITOR: {', '.join(declining_metrics[:3])} showing declining trends"
            )
        
        # Risk-specific recommendations
        top_risks = risk_summary.get('top_risks', [])
        for risk in top_risks[:2]:
            if hasattr(risk, 'mitigation_suggestions'):
                recommendations.extend(risk.mitigation_suggestions[:1])  # Top suggestion per risk
        
        # Auto-fix opportunities
        qa_results = self.qa_system.perform_comprehensive_qa()
        auto_fixable = qa_results['overall_assessment']['auto_fixable_issues']
        if auto_fixable > 0:
            recommendations.append(
                f"🔧 QUICK WIN: Apply {auto_fixable} automatic fixes for immediate improvement"
            )
        
        # Preventive maintenance
        if risk_summary['overall_risk_level'] == 'low':
            recommendations.append(
                "✨ MAINTAIN: Quality is stable - focus on preventive maintenance and documentation updates"
            )
        
        return recommendations[:8]  # Top 8 recommendations
    
    def _calculate_prediction_confidence(self, quality_trends: Dict[str, Any]) -> float:
        """Calculate overall prediction confidence"""
        individual_trends = quality_trends.get('individual_trends', {})
        
        if not individual_trends:
            return 0.5
        
        confidence_values = [
            trend.confidence_level for trend in individual_trends.values()
            if hasattr(trend, 'confidence_level')
        ]
        
        if not confidence_values:
            return 0.5
        
        return sum(confidence_values) / len(confidence_values)
    
    def get_enhanced_qa_dashboard(self) -> Dict[str, Any]:
        """Get enhanced QA dashboard with predictive insights"""
        # Get standard QA dashboard
        standard_dashboard = self.qa_system.get_qa_dashboard_data()
        
        # Get predictive report
        predictive_report = self.generate_predictive_quality_report()
        
        # Get alert statistics
        alert_stats = self.early_warning.get_alert_statistics()
        
        # Combine into enhanced dashboard
        enhanced_dashboard = {
            # Standard QA metrics
            **standard_dashboard,
            
            # Predictive enhancements
            'predictive_insights': {
                'overall_health_score': predictive_report.overall_health_score,
                'prediction_confidence': predictive_report.confidence_level,
                'predicted_coverage_7d': predictive_report.predicted_metrics_7d.doc_coverage,
                'predicted_quality_7d': predictive_report.predicted_metrics_7d.overall_quality(),
                'trending_metrics': self._get_trending_metrics(predictive_report.trend_analysis),
                'risk_level': predictive_report.risk_assessment['overall_risk_level'],
                'active_alerts': len(predictive_report.active_alerts),
                'immediate_actions_needed': predictive_report.risk_assessment['immediate_actions_needed']
            },
            
            # Alert system metrics
            'alert_system': {
                'monitoring_active': alert_stats['monitoring_active'],
                'alerts_last_24h': alert_stats['alerts_last_24h'],
                'critical_alerts': alert_stats['severity_distribution']['critical'],
                'most_frequent_issues': alert_stats['most_frequent_metrics'][:3]
            },
            
            # Enhanced recommendations
            'predictive_recommendations': predictive_report.recommendations,
            
            # Health trends
            'health_trends': {
                'current_health': predictive_report.overall_health_score,
                'predicted_health_7d': self._predict_health_score_7d(predictive_report),
                'health_trend': self._get_health_trend(predictive_report.overall_health_score)
            }
        }
        
        return enhanced_dashboard
    
    def _get_trending_metrics(self, trend_analysis: Dict[str, Any]) -> Dict[str, str]:
        """Get summary of trending metrics"""
        individual_trends = trend_analysis.get('individual_trends', {})
        trending = {}
        
        for metric_name, trend in individual_trends.items():
            if hasattr(trend, 'trend_direction'):
                if trend.trend_direction == 'improving':
                    trending[metric_name] = '📈 Improving'
                elif trend.trend_direction == 'declining':
                    trending[metric_name] = '📉 Declining'
                else:
                    trending[metric_name] = '➡️ Stable'
        
        return trending
    
    def _predict_health_score_7d(self, report: PredictiveQualityReport) -> float:
        """Predict health score in 7 days"""
        predicted_quality = report.predicted_metrics_7d.overall_quality()
        
        # Adjust for risk factors
        risk_adjustment = 0
        if report.risk_assessment['overall_risk_level'] == 'critical':
            risk_adjustment = -15
        elif report.risk_assessment['overall_risk_level'] == 'high':
            risk_adjustment = -10
        elif report.risk_assessment['overall_risk_level'] == 'medium':
            risk_adjustment = -5
        
        predicted_health = predicted_quality + risk_adjustment
        return max(0, min(100, predicted_health))
    
    def _get_health_trend(self, current_health: float) -> str:
        """Get health trend description"""
        if current_health >= 90:
            return "Excellent"
        elif current_health >= 80:
            return "Good"
        elif current_health >= 70:
            return "Fair"
        elif current_health >= 60:
            return "Poor"
        else:
            return "Critical"
    
    def generate_comprehensive_predictive_report(self) -> str:
        """Generate comprehensive markdown report with predictive insights"""
        predictive_report = self.generate_predictive_quality_report()
        enhanced_dashboard = self.get_enhanced_qa_dashboard()
        
        report = "# 🔮 Predictive Quality Intelligence Report\n\n"
        report += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"**Prediction Horizon**: 7 days\n"
        report += f"**Confidence Level**: {predictive_report.confidence_level:.1%}\n\n"
        
        # Executive Summary
        report += "## 🎯 Executive Summary\n\n"
        health = enhanced_dashboard['predictive_insights']
        report += f"- **Current Health Score**: {health['overall_health_score']:.1f}/100\n"
        report += f"- **Predicted Health (7d)**: {health['predicted_coverage_7d']:.1f}%\n"
        report += f"- **Risk Level**: {health['risk_level'].title()}\n"
        report += f"- **Active Alerts**: {health['active_alerts']}\n"
        report += f"- **Immediate Actions**: {'Yes' if health['immediate_actions_needed'] else 'No'}\n\n"
        
        # Health Trend
        health_trend = enhanced_dashboard['health_trends']
        if health_trend['predicted_health_7d'] > health_trend['current_health']:
            trend_icon = "📈"
            trend_desc = "Improving"
        elif health_trend['predicted_health_7d'] < health_trend['current_health']:
            trend_icon = "📉"
            trend_desc = "Declining"
        else:
            trend_icon = "➡️"
            trend_desc = "Stable"
        
        report += f"**Health Trend**: {trend_icon} {trend_desc}\n\n"
        
        # Current vs Predicted Metrics
        report += "## 📊 Quality Metrics Forecast\n\n"
        report += "| Metric | Current | Predicted (7d) | Trend |\n"
        report += "|--------|---------|---------------|-------|\n"
        
        current = predictive_report.current_metrics
        predicted = predictive_report.predicted_metrics_7d
        
        metrics = [
            ("Documentation Coverage", current.doc_coverage, predicted.doc_coverage),
            ("Code Quality Score", current.code_quality_score, predicted.code_quality_score),
            ("Test Coverage", current.test_coverage, predicted.test_coverage),
            ("Maintainability Index", current.maintainability_index, predicted.maintainability_index),
        ]
        
        for name, curr_val, pred_val in metrics:
            if pred_val > curr_val:
                trend = "📈"
            elif pred_val < curr_val:
                trend = "📉"
            else:
                trend = "➡️"
            report += f"| {name} | {curr_val:.1f}% | {pred_val:.1f}% | {trend} |\n"
        
        report += "\n"
        
        # Risk Assessment
        risk_summary = predictive_report.risk_assessment
        if risk_summary['total_risks'] > 0:
            report += "## ⚠️ Risk Assessment\n\n"
            report += f"- **Overall Risk Level**: {risk_summary['overall_risk_level'].title()}\n"
            report += f"- **Total Risks Identified**: {risk_summary['total_risks']}\n"
            report += f"- **High Priority Risks**: {risk_summary['high_priority_risks']}\n\n"
            
            if risk_summary.get('top_risks'):
                report += "### Top Risks\n\n"
                for i, risk in enumerate(risk_summary['top_risks'][:3], 1):
                    if hasattr(risk, 'risk_type'):
                        report += f"{i}. **{risk.risk_type}** (Probability: {risk.probability:.1%})\n"
                        report += f"   - Impact: {risk.impact_severity}\n"
                        report += f"   - Timeline: {risk.predicted_timeline}\n"
                        if risk.mitigation_suggestions:
                            report += f"   - Top Mitigation: {risk.mitigation_suggestions[0]}\n"
                        report += "\n"
        
        # Active Alerts
        if predictive_report.active_alerts:
            report += "## 🚨 Active Quality Alerts\n\n"
            for alert in predictive_report.active_alerts[:5]:  # Top 5 alerts
                severity_icon = {
                    AlertSeverity.CRITICAL: "🔴",
                    AlertSeverity.ERROR: "🟠", 
                    AlertSeverity.WARNING: "🟡",
                    AlertSeverity.INFO: "🔵"
                }.get(alert.severity, "⚪")
                
                report += f"### {severity_icon} {alert.title}\n"
                report += f"- **Severity**: {alert.severity.value.title()}\n"
                report += f"- **Description**: {alert.description}\n"
                report += f"- **Created**: {alert.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                if alert.recommended_actions:
                    report += f"- **Recommended Action**: {alert.recommended_actions[0]}\n"
                report += "\n"
        
        # Predictive Recommendations
        if predictive_report.recommendations:
            report += "## 🎯 Predictive Recommendations\n\n"
            for i, rec in enumerate(predictive_report.recommendations, 1):
                report += f"{i}. {rec}\n"
            report += "\n"
        
        # Next Steps
        report += "## 🚀 Next Steps\n\n"
        
        if health['immediate_actions_needed']:
            report += "### Immediate Actions (Next 24 Hours)\n"
            report += "1. Address critical alerts and high-risk items\n"
            report += "2. Implement top mitigation strategies\n"
            report += "3. Monitor trending metrics closely\n\n"
        
        report += "### Short-term Actions (This Week)\n"
        if enhanced_dashboard['auto_fixable_issues'] > 0:
            report += f"1. Apply {enhanced_dashboard['auto_fixable_issues']} auto-fixes for quick wins\n"
        
        declining_metrics = [
            name for name, trend in enhanced_dashboard['predictive_insights']['trending_metrics'].items()
            if '📉' in trend
        ]
        if declining_metrics:
            report += f"2. Focus on stabilizing declining metrics: {', '.join(declining_metrics)}\n"
        
        report += "3. Continue monitoring predictive trends\n\n"
        
        report += "### Long-term Strategy (Next Month)\n"
        report += "1. Implement preventive quality measures\n"
        report += "2. Enhance documentation for complex components\n"
        report += "3. Establish regular quality review cycles\n"
        
        return report
    
    def test_integration(self) -> Dict[str, bool]:
        """Test integration between all components"""
        test_results = {}
        
        try:
            # Test QA system
            qa_results = self.qa_system.perform_comprehensive_qa()
            test_results['qa_system'] = qa_results is not None
        except Exception as e:
            test_results['qa_system'] = False
            print(f"QA system test failed: {e}")
        
        try:
            # Test predictive components
            trends = self.quality_analyzer.get_overall_quality_trend()
            test_results['trend_analysis'] = trends is not None
        except Exception as e:
            test_results['trend_analysis'] = False
            print(f"Trend analysis test failed: {e}")
        
        try:
            # Test risk assessment
            risks = self.risk_assessor.assess_risks()
            test_results['risk_assessment'] = isinstance(risks, list)
        except Exception as e:
            test_results['risk_assessment'] = False
            print(f"Risk assessment test failed: {e}")
        
        try:
            # Test early warning system
            alert_stats = self.early_warning.get_alert_statistics()
            test_results['early_warning'] = alert_stats is not None
        except Exception as e:
            test_results['early_warning'] = False
            print(f"Early warning test failed: {e}")
        
        try:
            # Test integrated report generation
            report = self.generate_predictive_quality_report()
            test_results['integrated_reporting'] = report is not None
        except Exception as e:
            test_results['integrated_reporting'] = False
            print(f"Integrated reporting test failed: {e}")
        
        try:
            # Test dashboard integration
            dashboard = self.get_enhanced_qa_dashboard()
            test_results['dashboard_integration'] = dashboard is not None
        except Exception as e:
            test_results['dashboard_integration'] = False
            print(f"Dashboard integration test failed: {e}")
        
        # Overall integration health
        test_results['overall_integration'] = all(test_results.values())
        
        return test_results