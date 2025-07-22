"""
Predictive Intelligence Layer for Workflow Automation

This module provides predictive capabilities for quality assurance,
risk assessment, and project health monitoring.

Task 2.1: Quality Prediction System (Complete)
Task 2.2: Risk Assessment Framework (Complete)
"""

# Task 2.1 Components (Quality Prediction System)
from .quality_predictor import QualityTrendAnalyzer, PredictiveRiskAssessment, QualityMetrics, QualityTrend, RiskAssessment
from .quality_metrics_collector import QualityMetricsCollector, HistoricalMetricsManager, ProjectMetrics, CodeMetrics
from .early_warning_system import EarlyWarningSystem, AlertManager

# Task 2.2 Components (Risk Assessment Framework) 
from .project_health_analyzer import ProjectHealthAnalyzer, ProjectHealthReport, HealthStatus, HealthMetric
from .risk_assessment_dashboard import RiskAssessmentDashboard, RiskDashboardData, RiskLevel, RiskIndicator, DashboardAlert
from .trend_analysis_engine import TrendAnalysisEngine, ComprehensiveTrendReport, TrendDirection, TrendAnalysis
from .risk_framework_integration import RiskFrameworkIntegrator, IntegratedRiskAssessment

__all__ = [
    # Task 2.1 Components
    'QualityTrendAnalyzer',
    'PredictiveRiskAssessment',
    'QualityMetrics',
    'QualityTrend', 
    'RiskAssessment',
    'QualityMetricsCollector',
    'HistoricalMetricsManager',
    'ProjectMetrics',
    'CodeMetrics',
    'EarlyWarningSystem',
    'AlertManager',
    
    # Task 2.2 Components
    'ProjectHealthAnalyzer',
    'ProjectHealthReport',
    'HealthStatus',
    'HealthMetric',
    'RiskAssessmentDashboard',
    'RiskDashboardData',
    'RiskLevel',
    'RiskIndicator',
    'DashboardAlert',
    'TrendAnalysisEngine',
    'ComprehensiveTrendReport',
    'TrendDirection',
    'TrendAnalysis',
    'RiskFrameworkIntegrator',
    'IntegratedRiskAssessment'
]