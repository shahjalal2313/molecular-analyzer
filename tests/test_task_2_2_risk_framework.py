"""
Comprehensive Test Suite for Task 2.2 - Risk Assessment Framework

This test suite validates all Task 2.2 components and their integration
with existing Task 2.1 predictive intelligence.
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime, timedelta

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from molecular_analyzer.workflow_automation.predictive.project_health_analyzer import (
        ProjectHealthAnalyzer, ProjectHealthReport, HealthStatus, HealthMetric
    )
    from molecular_analyzer.workflow_automation.predictive.risk_assessment_dashboard import (
        RiskAssessmentDashboard, RiskDashboardData, RiskLevel, RiskIndicator
    )
    from molecular_analyzer.workflow_automation.predictive.trend_analysis_engine import (
        TrendAnalysisEngine, ComprehensiveTrendReport, TrendDirection, TrendAnalysis
    )
    from molecular_analyzer.workflow_automation.predictive.risk_framework_integration import (
        RiskFrameworkIntegrator, IntegratedRiskAssessment
    )
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


class TestProjectHealthAnalyzer(unittest.TestCase):
    """Test ProjectHealthAnalyzer functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_project_path = "/test/project/path"
        self.analyzer = ProjectHealthAnalyzer(self.test_project_path)
    
    def test_initialization(self):
        """Test proper initialization"""
        self.assertEqual(self.analyzer.project_path, self.test_project_path)
        self.assertIsNotNone(self.analyzer.health_thresholds)
        self.assertEqual(self.analyzer.max_history_days, 30)
    
    @patch('molecular_analyzer.workflow_automation.predictive.project_health_analyzer.QualityMetricsCollector')
    def test_analyze_project_health(self, mock_collector):
        """Test project health analysis"""
        # Mock the metrics collector
        mock_collector.return_value.collect_project_metrics.return_value = MagicMock()
        
        # Perform analysis
        report = self.analyzer.analyze_project_health()
        
        # Validate report structure
        self.assertIsInstance(report, ProjectHealthReport)
        self.assertIsInstance(report.overall_status, HealthStatus)
        self.assertIsInstance(report.overall_score, float)
        self.assertIsInstance(report.metrics, list)
        self.assertIsInstance(report.risk_factors, list)
        self.assertIsInstance(report.recommendations, list)
    
    def test_health_metric_creation(self):
        """Test health metric creation"""
        metric = HealthMetric(
            name="test_metric",
            value=0.8,
            status=HealthStatus.GOOD,
            trend="improving",
            confidence=0.9,
            last_updated=datetime.now()
        )
        
        self.assertEqual(metric.name, "test_metric")
        self.assertEqual(metric.value, 0.8)
        self.assertEqual(metric.status, HealthStatus.GOOD)
    
    def test_status_determination(self):
        """Test status determination logic"""
        # Test with good value
        status = self.analyzer._determine_status('code_quality', 0.85)
        self.assertEqual(status, HealthStatus.GOOD)
        
        # Test with poor value
        status = self.analyzer._determine_status('code_quality', 0.55)
        self.assertEqual(status, HealthStatus.POOR)
        
        # Test with lower-is-better metric
        status = self.analyzer._determine_status('complexity_score', 0.3, lower_is_better=True)
        self.assertEqual(status, HealthStatus.GOOD)
    
    def test_get_health_summary(self):
        """Test health summary generation"""
        with patch.object(self.analyzer, 'analyze_project_health') as mock_analyze:
            # Mock the analysis result
            mock_report = MagicMock()
            mock_report.overall_status.value = 'good'
            mock_report.overall_score = 0.8
            mock_report.confidence_level = 0.75
            mock_report.risk_factors = ['test_risk']
            mock_report.recommendations = ['test_recommendation']
            mock_report.trend_analysis = {'trend': 'stable'}
            mock_analyze.return_value = mock_report
            
            summary = self.analyzer.get_health_summary()
            
            self.assertEqual(summary['status'], 'good')
            self.assertEqual(summary['score'], 0.8)
            self.assertEqual(summary['confidence'], 0.75)


class TestRiskAssessmentDashboard(unittest.TestCase):
    """Test RiskAssessmentDashboard functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_project_path = "/test/project/path"
        self.dashboard = RiskAssessmentDashboard(self.test_project_path)
    
    def test_initialization(self):
        """Test proper initialization"""
        self.assertEqual(self.dashboard.project_path, self.test_project_path)
        self.assertIsNotNone(self.dashboard.risk_thresholds)
        self.assertEqual(self.dashboard.update_interval_seconds, 300)
    
    @patch('molecular_analyzer.workflow_automation.predictive.risk_assessment_dashboard.ProjectHealthAnalyzer')
    def test_generate_dashboard_data(self, mock_analyzer):
        """Test dashboard data generation"""
        # Mock health analyzer
        mock_health_report = MagicMock()
        mock_health_report.metrics = []
        mock_health_report.risk_factors = []
        mock_health_report.overall_score = 0.8
        mock_health_report.confidence_level = 0.75
        mock_health_report.trend_analysis = {'trend': 'stable'}
        
        mock_analyzer.return_value.analyze_project_health.return_value = mock_health_report
        
        # Generate dashboard data
        dashboard_data = self.dashboard.generate_dashboard_data()
        
        # Validate structure
        self.assertIsInstance(dashboard_data, RiskDashboardData)
        self.assertIsInstance(dashboard_data.overall_risk_level, RiskLevel)
        self.assertIsInstance(dashboard_data.risk_score, float)
        self.assertIsInstance(dashboard_data.risk_indicators, list)
        self.assertIsInstance(dashboard_data.active_alerts, list)
    
    def test_risk_indicator_creation(self):
        """Test risk indicator creation"""
        indicator = RiskIndicator(
            name="test_risk",
            level=RiskLevel.MEDIUM,
            score=0.6,
            description="Test risk description",
            impact="Test impact",
            likelihood=0.7,
            mitigation="Test mitigation",
            last_updated=datetime.now()
        )
        
        self.assertEqual(indicator.name, "test_risk")
        self.assertEqual(indicator.level, RiskLevel.MEDIUM)
        self.assertEqual(indicator.score, 0.6)
    
    def test_score_to_risk_level(self):
        """Test score to risk level conversion"""
        self.assertEqual(self.dashboard._score_to_risk_level(0.9), RiskLevel.CRITICAL)
        self.assertEqual(self.dashboard._score_to_risk_level(0.7), RiskLevel.HIGH)
        self.assertEqual(self.dashboard._score_to_risk_level(0.5), RiskLevel.MEDIUM)
        self.assertEqual(self.dashboard._score_to_risk_level(0.1), RiskLevel.LOW)
    
    def test_get_dashboard_summary(self):
        """Test dashboard summary generation"""
        with patch.object(self.dashboard, 'generate_dashboard_data') as mock_generate:
            # Mock dashboard data
            mock_data = MagicMock()
            mock_data.overall_risk_level.value = 'medium'
            mock_data.risk_score = 0.5
            mock_data.active_alerts = [MagicMock(), MagicMock()]
            mock_data.confidence_level = 0.8
            mock_data.trend_data = {'trend': 'stable'}
            mock_data.recommendations = ['test_rec_1', 'test_rec_2']
            mock_generate.return_value = mock_data
            
            summary = self.dashboard.get_dashboard_summary()
            
            self.assertEqual(summary['risk_level'], 'medium')
            self.assertEqual(summary['risk_score'], 0.5)
            self.assertEqual(summary['active_alerts'], 2)


class TestTrendAnalysisEngine(unittest.TestCase):
    """Test TrendAnalysisEngine functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = TrendAnalysisEngine()
    
    def test_initialization(self):
        """Test proper initialization"""
        self.assertEqual(self.engine.min_data_points, 5)
        self.assertEqual(self.engine.max_history_days, 90)
        self.assertEqual(self.engine.trend_sensitivity, 0.05)
    
    def test_trend_direction_calculation(self):
        """Test trend direction calculation"""
        # Test improving trend
        improving_values = [0.5, 0.6, 0.7, 0.8, 0.9]
        direction, strength = self.engine._calculate_trend_direction(improving_values)
        self.assertIn(direction, [TrendDirection.IMPROVING, TrendDirection.STRONGLY_IMPROVING])
        self.assertGreater(strength, 0.0)
        
        # Test declining trend
        declining_values = [0.9, 0.8, 0.7, 0.6, 0.5]
        direction, strength = self.engine._calculate_trend_direction(declining_values)
        self.assertIn(direction, [TrendDirection.DECLINING, TrendDirection.STRONGLY_DECLINING])
        
        # Test stable trend
        stable_values = [0.7, 0.71, 0.69, 0.7, 0.7]
        direction, strength = self.engine._calculate_trend_direction(stable_values)
        self.assertEqual(direction, TrendDirection.STABLE)
    
    def test_velocity_calculation(self):
        """Test velocity calculation"""
        timestamps = [
            datetime.now() - timedelta(days=4),
            datetime.now() - timedelta(days=3),
            datetime.now() - timedelta(days=2),
            datetime.now() - timedelta(days=1),
            datetime.now()
        ]
        values = [0.5, 0.6, 0.7, 0.8, 0.9]
        
        velocity = self.engine._calculate_velocity(values, timestamps)
        self.assertGreater(velocity, 0)  # Should be positive for improving trend
    
    def test_volatility_calculation(self):
        """Test volatility calculation"""
        # Low volatility data
        stable_values = [0.7, 0.71, 0.69, 0.7, 0.7]
        volatility = self.engine._calculate_volatility(stable_values)
        self.assertLess(volatility, 0.1)
        
        # High volatility data
        volatile_values = [0.1, 0.9, 0.2, 0.8, 0.3]
        volatility = self.engine._calculate_volatility(volatile_values)
        self.assertGreater(volatility, 0.5)
    
    def test_update_health_data(self):
        """Test health data updating"""
        mock_report = MagicMock()
        mock_report.timestamp = datetime.now()
        
        initial_count = len(self.engine.health_data_history)
        self.engine.update_health_data(mock_report)
        
        self.assertEqual(len(self.engine.health_data_history), initial_count + 1)
    
    def test_get_quick_trend_summary(self):
        """Test quick trend summary"""
        # Test with insufficient data
        summary = self.engine.get_quick_trend_summary()
        self.assertEqual(summary['status'], 'insufficient_data')
        
        # Add some mock data
        for i in range(5):
            mock_report = MagicMock()
            mock_report.timestamp = datetime.now() - timedelta(days=4-i)
            mock_report.overall_score = 0.7 + i * 0.05  # Improving trend
            self.engine.update_health_data(mock_report)
        
        summary = self.engine.get_quick_trend_summary()
        self.assertIn('overall_trend', summary)
        self.assertIn('confidence', summary)


class TestRiskFrameworkIntegrator(unittest.TestCase):
    """Test RiskFrameworkIntegrator functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_project_path = "/test/project/path"
        self.integrator = RiskFrameworkIntegrator(self.test_project_path)
    
    def test_initialization(self):
        """Test proper initialization"""
        self.assertEqual(self.integrator.project_path, self.test_project_path)
        self.assertTrue(self.integrator.integration_enabled)
        self.assertIsNone(self.integrator.last_assessment)
    
    @patch('molecular_analyzer.workflow_automation.predictive.risk_framework_integration.ProjectHealthAnalyzer')
    @patch('molecular_analyzer.workflow_automation.predictive.risk_framework_integration.RiskAssessmentDashboard')
    @patch('molecular_analyzer.workflow_automation.predictive.risk_framework_integration.TrendAnalysisEngine')
    def test_perform_integrated_assessment(self, mock_trend, mock_dashboard, mock_health):
        """Test integrated assessment performance"""
        # Mock components
        mock_health_report = MagicMock()
        mock_health_report.overall_score = 0.8
        mock_health_report.confidence_level = 0.75
        mock_health_report.metrics = []
        mock_health_report.risk_factors = []
        mock_health_report.recommendations = []
        mock_health_report.trend_analysis = {'trend': 'stable'}
        
        mock_dashboard_data = MagicMock()
        mock_dashboard_data.risk_score = 0.3
        mock_dashboard_data.confidence_level = 0.8
        mock_dashboard_data.active_alerts = []
        mock_dashboard_data.risk_indicators = []
        
        mock_trend_report = MagicMock()
        mock_trend_report.overall_trend = TrendDirection.STABLE
        mock_trend_report.overall_confidence.value = 'medium'
        mock_trend_report.detected_patterns = []
        mock_trend_report.recommendations = []
        
        # Configure mocks
        mock_health.return_value.analyze_project_health.return_value = mock_health_report
        mock_dashboard.return_value.generate_dashboard_data.return_value = mock_dashboard_data
        mock_trend.return_value.analyze_comprehensive_trends.return_value = mock_trend_report
        
        # Perform assessment
        assessment = self.integrator.perform_integrated_assessment()
        
        # Validate results
        self.assertIsInstance(assessment, IntegratedRiskAssessment)
        self.assertIsInstance(assessment.overall_risk_score, float)
        self.assertIsInstance(assessment.overall_confidence, float)
        self.assertIsInstance(assessment.prioritized_actions, list)
        self.assertIsInstance(assessment.long_term_strategy, list)
    
    def test_get_integration_summary(self):
        """Test integration summary generation"""
        with patch.object(self.integrator, 'perform_integrated_assessment') as mock_assess:
            # Mock assessment
            mock_assessment = MagicMock()
            mock_assessment.overall_risk_score = 0.4
            mock_assessment.overall_confidence = 0.8
            mock_assessment.integration_status = "excellent"
            mock_assessment.data_quality_score = 0.9
            mock_assessment.health_report.overall_status.value = "good"
            mock_assessment.dashboard_data.overall_risk_level.value = "medium"
            mock_assessment.dashboard_data.active_alerts = [MagicMock()]
            mock_assessment.trend_report.overall_trend.value = "stable"
            mock_assessment.timestamp = datetime.now()
            mock_assessment.analysis_duration_seconds = 1.5
            
            mock_assess.return_value = mock_assessment
            
            summary = self.integrator.get_integration_summary()
            
            self.assertEqual(summary['overall_risk_score'], 0.4)
            self.assertEqual(summary['integration_status'], "excellent")
            self.assertEqual(summary['active_alerts'], 1)
    
    def test_validate_integration(self):
        """Test integration validation"""
        with patch.object(self.integrator, '_validate_task_2_1_integration') as mock_2_1, \
             patch.object(self.integrator, '_validate_task_2_2_integration') as mock_2_2, \
             patch.object(self.integrator, '_validate_end_to_end_integration') as mock_e2e, \
             patch.object(self.integrator, '_validate_performance') as mock_perf:
            
            # Mock validation results
            mock_2_1.return_value = {'status': 'pass', 'score': 0.9}
            mock_2_2.return_value = {'status': 'pass', 'score': 0.9}
            mock_e2e.return_value = {'status': 'pass', 'score': 0.95}
            mock_perf.return_value = {'status': 'good', 'score': 0.8}
            
            validation = self.integrator.validate_integration()
            
            self.assertIn('overall_score', validation)
            self.assertIn('overall_status', validation)
            self.assertGreaterEqual(validation['overall_score'], 0.8)


class TestIntegrationWorkflow(unittest.TestCase):
    """Test complete integration workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_project_path = "/test/project/path"
    
    @patch('molecular_analyzer.workflow_automation.predictive.project_health_analyzer.QualityMetricsCollector')
    @patch('molecular_analyzer.workflow_automation.predictive.quality_predictor.PredictiveRiskAssessment')
    def test_complete_workflow(self, mock_risk_assessment, mock_collector):
        """Test complete workflow from health analysis to integrated assessment"""
        # Mock dependencies
        mock_collector.return_value.collect_project_metrics.return_value = MagicMock()
        mock_risk_assessment.return_value.assess_risk.return_value = MagicMock(
            overall_risk_level=0.3, confidence=0.8, risk_factors=[]
        )
        
        try:
            # Initialize components
            health_analyzer = ProjectHealthAnalyzer(self.test_project_path)
            dashboard = RiskAssessmentDashboard(self.test_project_path)
            trend_engine = TrendAnalysisEngine()
            integrator = RiskFrameworkIntegrator(self.test_project_path)
            
            # Perform health analysis
            health_report = health_analyzer.analyze_project_health()
            self.assertIsNotNone(health_report)
            
            # Generate dashboard data
            dashboard_data = dashboard.generate_dashboard_data()
            self.assertIsNotNone(dashboard_data)
            
            # Update trend engine and analyze
            trend_engine.update_health_data(health_report)
            trend_engine.update_risk_data(dashboard_data)
            
            # Add some mock data for trend analysis
            for i in range(5):
                mock_report = MagicMock()
                mock_report.timestamp = datetime.now() - timedelta(days=4-i)
                mock_report.overall_score = 0.7 + i * 0.02
                mock_report.metrics = []
                trend_engine.update_health_data(mock_report)
            
            trend_report = trend_engine.analyze_comprehensive_trends()
            self.assertIsNotNone(trend_report)
            
            # Perform integrated assessment
            integrated_assessment = integrator.perform_integrated_assessment()
            self.assertIsNotNone(integrated_assessment)
            
            # Validate integration
            validation = integrator.validate_integration()
            self.assertIn('overall_status', validation)
            
            # Test succeeded
            workflow_success = True
            
        except Exception as e:
            print(f"Workflow test error: {e}")
            workflow_success = False
        
        self.assertTrue(workflow_success, "Complete workflow should execute without errors")


def run_task_2_2_tests():
    """Run all Task 2.2 tests and return results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestProjectHealthAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestRiskAssessmentDashboard))
    suite.addTests(loader.loadTestsFromTestCase(TestTrendAnalysisEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestRiskFrameworkIntegrator))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationWorkflow))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return test summary
    return {
        'tests_run': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun if result.testsRun > 0 else 0,
        'success': result.wasSuccessful()
    }


if __name__ == '__main__':
    print("=" * 60)
    print("Task 2.2 Risk Assessment Framework - Test Suite")
    print("=" * 60)
    
    # Run tests
    test_results = run_task_2_2_tests()
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Tests Run: {test_results['tests_run']}")
    print(f"Failures: {test_results['failures']}")
    print(f"Errors: {test_results['errors']}")
    print(f"Success Rate: {test_results['success_rate']:.1%}")
    print(f"Overall Status: {'PASS' if test_results['success'] else 'FAIL'}")
    print("=" * 60)
    
    # Exit with appropriate code
    sys.exit(0 if test_results['success'] else 1)