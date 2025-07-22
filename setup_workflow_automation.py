#!/usr/bin/env python3
"""
Workflow Automation System - Quick Setup Script

This script helps you quickly set up and test the workflow automation system.
Run this after reading the implementation guide.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)

def print_step(step_num, description):
    """Print formatted step"""
    print(f"\n📋 Step {step_num}: {description}")

def test_import(module_name, component):
    """Test if a component can be imported"""
    try:
        exec(f"from {module_name} import {component}")
        print(f"✅ {component}: OK")
        return True
    except Exception as e:
        print(f"❌ {component}: {e}")
        return False

def setup_workflow_automation():
    """Main setup function"""
    
    print_header("Workflow Automation System Setup")
    print("This script will help you set up and test the workflow automation system.")
    print("Make sure you've read the implementation guide first!")
    
    # Step 1: Verify project structure
    print_step(1, "Verifying project structure")
    
    required_paths = [
        "src/molecular_analyzer/workflow_automation",
        "src/molecular_analyzer/workflow_automation/advanced",
        "src/molecular_analyzer/workflow_automation/predictive",
        "project-management"
    ]
    
    all_paths_exist = True
    for path in required_paths:
        if Path(path).exists():
            print(f"✅ {path}: Found")
        else:
            print(f"❌ {path}: Missing")
            all_paths_exist = False
    
    if not all_paths_exist:
        print("\n⚠️  Some required paths are missing. Please check your project structure.")
        return False
    
    # Step 2: Test imports
    print_step(2, "Testing component imports")
    
    components_to_test = [
        ("src.molecular_analyzer.workflow_automation.enhanced_todo_system", "EnhancedTodoSystem"),
        ("src.molecular_analyzer.workflow_automation.advanced.knowledge_capture", "KnowledgeCaptureSystem"),
        ("src.molecular_analyzer.workflow_automation.predictive.quality_metrics_collector", "QualityMetricsCollector"),
        ("src.molecular_analyzer.workflow_automation.predictive.quality_predictor", "QualityTrendAnalyzer"),
        ("src.molecular_analyzer.workflow_automation.predictive.quality_predictor", "PredictiveRiskAssessment"),
    ]
    
    import_success = True
    for module, component in components_to_test:
        if not test_import(module, component):
            import_success = False
    
    if not import_success:
        print("\n⚠️  Some components failed to import. Check the troubleshooting section.")
        return False
    
    # Step 3: Initialize knowledge base
    print_step(3, "Initializing knowledge base")
    
    try:
        from src.molecular_analyzer.workflow_automation.advanced.knowledge_capture import KnowledgeCaptureSystem
        kcs = KnowledgeCaptureSystem()
        print(f"✅ Knowledge base initialized at: {kcs.integrator.db_path}")
        
        # Test basic functionality
        stats = kcs.integrator.get_statistics()
        print(f"✅ Database connection: OK")
        print(f"   - Total decisions: {stats.get('total_decisions', 0)}")
        print(f"   - Total knowledge: {stats.get('total_knowledge', 0)}")
        
    except Exception as e:
        print(f"❌ Knowledge base setup failed: {e}")
        return False
    
    # Step 4: Test quality monitoring
    print_step(4, "Testing quality monitoring")
    
    try:
        from src.molecular_analyzer.workflow_automation.predictive.quality_metrics_collector import QualityMetricsCollector
        collector = QualityMetricsCollector()
        
        # Test project metrics collection
        metrics = collector.collect_project_metrics()
        print(f"✅ Quality monitoring: OK")
        print(f"   - Files analyzed: {metrics.get('total_files', 0)}")
        print(f"   - Code quality score: {metrics.get('code_quality_score', 0):.2f}")
        
    except Exception as e:
        print(f"❌ Quality monitoring failed: {e}")
        return False
    
    # Step 5: Test risk assessment
    print_step(5, "Testing risk assessment")
    
    try:
        from src.molecular_analyzer.workflow_automation.predictive.quality_predictor import QualityTrendAnalyzer, PredictiveRiskAssessment
        
        analyzer = QualityTrendAnalyzer()
        risk_assessment = PredictiveRiskAssessment(analyzer)
        
        # Test basic risk assessment
        risk_summary = risk_assessment.get_risk_summary()
        print(f"✅ Risk assessment: OK")
        print(f"   - Overall risk level: {risk_summary.get('overall_risk_level', 'unknown')}")
        print(f"   - Total risks identified: {risk_summary.get('total_risks', 0)}")
        
    except Exception as e:
        print(f"❌ Risk assessment failed: {e}")
        return False
    
    # Step 6: Create basic configuration
    print_step(6, "Creating basic configuration")
    
    config = {
        "knowledge_capture": {
            "enabled": True,
            "auto_capture": True,
            "confidence_threshold": 0.6,
            "database_path": "src/molecular_analyzer/workflow_automation/knowledge_base.db"
        },
        "quality_monitoring": {
            "enabled": True,
            "check_interval": "daily",
            "alert_threshold": 0.7,
            "metrics_to_track": ["code_quality", "test_coverage", "documentation"]
        },
        "risk_assessment": {
            "enabled": True,
            "prediction_horizon_days": 7,
            "alert_levels": ["high", "critical"]
        },
        "setup_date": datetime.now().isoformat(),
        "version": "1.0"
    }
    
    config_path = "workflow_automation_config.json"
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Configuration created: {config_path}")
    except Exception as e:
        print(f"❌ Configuration creation failed: {e}")
        return False
    
    # Step 7: Run integration test
    print_step(7, "Running integration test")
    
    try:
        # Test a complete workflow
        from datetime import datetime
        
        # 1. Capture a sample decision
        sample_session = {
            "completed_tasks": [
                {
                    "id": "setup_test",
                    "description": "Setup and test workflow automation system",
                    "completed_at": datetime.now().isoformat()
                }
            ]
        }
        
        results = kcs.capture_from_session_data(sample_session)
        print(f"✅ Integration test: OK")
        print(f"   - Decisions captured: {results.get('decisions_captured', 0)}")
        print(f"   - Knowledge extracted: {results.get('knowledge_extracted', 0)}")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False
    
    # Success!
    print_header("Setup Complete!")
    print("🎉 Workflow automation system is ready to use!")
    print("\n📋 Next Steps:")
    print("1. Review the configuration file: workflow_automation_config.json")
    print("2. Read the usage examples in the implementation guide")
    print("3. Start using the enhanced TodoWrite features")
    print("4. Monitor quality metrics during development")
    print("5. Check risk assessments regularly")
    
    print("\n🔗 Quick Usage Examples:")
    print("```python")
    print("# Enhanced TodoWrite")
    print("from src.molecular_analyzer.workflow_automation.enhanced_todo_system import EnhancedTodoSystem")
    print("todo_system = EnhancedTodoSystem()")
    print("")
    print("# Quality Monitoring")
    print("from src.molecular_analyzer.workflow_automation.predictive.quality_metrics_collector import QualityMetricsCollector")
    print("collector = QualityMetricsCollector()")
    print("summary = collector.get_metrics_summary()")
    print("")
    print("# Knowledge Search")
    print("from src.molecular_analyzer.workflow_automation.advanced.knowledge_capture import KnowledgeCaptureSystem")
    print("kcs = KnowledgeCaptureSystem()")
    print("results = kcs.search_knowledge('your search query')")
    print("```")
    
    return True

def main():
    """Main function"""
    try:
        success = setup_workflow_automation()
        if success:
            print("\n✅ Setup completed successfully!")
            print("📖 For detailed usage instructions, see: WORKFLOW_AUTOMATION_IMPLEMENTATION_GUIDE.md")
        else:
            print("\n❌ Setup encountered issues. Please check the error messages above.")
            print("📖 See the troubleshooting section in the implementation guide.")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error during setup: {e}")
        print("📖 Please check the troubleshooting section in the implementation guide.")

if __name__ == "__main__":
    main()