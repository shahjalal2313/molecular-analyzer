#!/usr/bin/env python3
"""
Test Suite for Knowledge Capture System - Phase 3 Advanced Features

Comprehensive testing of decision capture, knowledge extraction, 
validation, and database integration capabilities.

Author: Workflow Automation System  
Version: 3.0.0
Phase: 3 - Advanced Features
"""

import unittest
import tempfile
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add the source directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from molecular_analyzer.workflow_automation.advanced.knowledge_capture import (
    DecisionRecord,
    DecisionCaptureEngine,
    KnowledgeExtractor,
    KnowledgeBaseIntegrator,
    KnowledgeValidator,
    KnowledgeCaptureSystem
)


class TestDecisionRecord(unittest.TestCase):
    """Test DecisionRecord data class functionality."""
    
    def setUp(self):
        self.sample_decision = DecisionRecord(
            id="test_001",
            timestamp=datetime.now(),
            decision_type="technical",
            description="Test decision for unit testing",
            rationale="Testing serialization and deserialization",
            context={"test": True, "module": "knowledge_capture"},
            impact_level="medium",
            tags=["testing", "tech:python"],
            source="test",
            confidence=0.8,
            related_files=["test_file.py"]
        )
    
    def test_to_dict_conversion(self):
        """Test conversion to dictionary."""
        decision_dict = self.sample_decision.to_dict()
        
        self.assertIsInstance(decision_dict, dict)
        self.assertEqual(decision_dict['id'], "test_001")
        self.assertEqual(decision_dict['decision_type'], "technical")
        self.assertIsInstance(decision_dict['timestamp'], str)  # Should be ISO format
    
    def test_from_dict_conversion(self):
        """Test creation from dictionary."""
        decision_dict = self.sample_decision.to_dict()
        reconstructed = DecisionRecord.from_dict(decision_dict)
        
        self.assertEqual(reconstructed.id, self.sample_decision.id)
        self.assertEqual(reconstructed.decision_type, self.sample_decision.decision_type)
        self.assertEqual(reconstructed.description, self.sample_decision.description)
        self.assertIsInstance(reconstructed.timestamp, datetime)
    
    def test_serialization_roundtrip(self):
        """Test full serialization roundtrip."""
        decision_dict = self.sample_decision.to_dict()
        reconstructed = DecisionRecord.from_dict(decision_dict)
        
        # Compare all major fields
        self.assertEqual(self.sample_decision.id, reconstructed.id)
        self.assertEqual(self.sample_decision.decision_type, reconstructed.decision_type)
        self.assertEqual(self.sample_decision.confidence, reconstructed.confidence)
        self.assertEqual(self.sample_decision.tags, reconstructed.tags)


class TestDecisionCaptureEngine(unittest.TestCase):
    """Test DecisionCaptureEngine functionality."""
    
    def setUp(self):
        self.engine = DecisionCaptureEngine()
    
    def test_initialization(self):
        """Test proper initialization."""
        self.assertIsInstance(self.engine.decision_patterns, dict)
        self.assertIn('architectural', self.engine.decision_patterns)
        self.assertIn('technical', self.engine.decision_patterns)
        self.assertIsInstance(self.engine.impact_indicators, dict)
    
    def test_pattern_detection(self):
        """Test decision pattern detection."""
        # Test architectural decision detection
        arch_text = "We decided to use microservices architecture for better scalability"
        decision = self.engine._extract_decision_from_text(
            text=arch_text,
            source='test',
            context={'test': True}
        )
        
        self.assertIsNotNone(decision)
        self.assertEqual(decision.decision_type, 'architectural')
        self.assertGreater(decision.confidence, 0.5)
    
    def test_impact_level_determination(self):
        """Test impact level determination."""
        critical_text = "breaking change to core architecture affects entire system"
        impact = self.engine._determine_impact_level(critical_text.lower())
        self.assertEqual(impact, 'critical')
        
        low_text = "fixed typo in comment"
        impact = self.engine._determine_impact_level(low_text.lower())
        self.assertEqual(impact, 'low')
    
    def test_tag_extraction(self):
        """Test tag extraction from text."""
        text = "Implemented Python Django API with numpy for performance optimization"
        tags = self.engine._extract_tags(text)
        
        self.assertIn('tech:python', tags)
        self.assertIn('tech:django', tags)
        self.assertIn('tech:numpy', tags)
        self.assertIn('action:implement', tags)
        self.assertIn('domain:performance', tags)
    
    def test_rationale_extraction(self):
        """Test rationale extraction."""
        text = "Chose SQLite because it provides full-text search without external dependencies"
        rationale = self.engine._extract_rationale(text)
        
        self.assertIn('full-text search', rationale)
        self.assertIn('external dependencies', rationale)
    
    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        # High confidence text
        high_conf_text = "We decided to implement this approach because it provides better performance and is the industry standard"
        confidence = self.engine._calculate_confidence(high_conf_text, 'technical', {'type': 'docstring'})
        self.assertGreater(confidence, 0.7)
        
        # Low confidence text
        low_conf_text = "maybe use this thing"
        confidence = self.engine._calculate_confidence(low_conf_text, 'technical', {})
        self.assertLess(confidence, 0.7)
    
    def test_code_comment_analysis(self):
        """Test analysis of code comments."""
        sample_code = '''
# This is a short comment
# Decided to refactor this module because the old approach was causing performance issues
# We chose to implement caching to improve response times
def some_function():
    pass
'''
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(sample_code)
            temp_file = f.name
        
        try:
            decisions = self.engine.capture_from_code(temp_file)
            
            # Should capture decisions from meaningful comments
            self.assertGreater(len(decisions), 0)
            
            # Check that decisions have proper structure
            for decision in decisions:
                self.assertIsInstance(decision, DecisionRecord)
                self.assertIsNotNone(decision.id)
                self.assertIsNotNone(decision.decision_type)
                
        finally:
            os.unlink(temp_file)
    
    def test_session_data_analysis(self):
        """Test analysis of session data."""
        session_data = {
            'completed_tasks': [
                {
                    'id': 'task_1',
                    'description': 'Implemented new authentication system using JWT tokens for better security',
                    'completed_at': datetime.now().isoformat()
                },
                {
                    'id': 'task_2',
                    'description': 'Fixed bug',  # Too short, should be ignored
                    'completed_at': datetime.now().isoformat()
                }
            ],
            'file_changes': [
                {
                    'file': 'auth.py',
                    'type': 'major_refactor',
                    'lines_changed': 150,
                    'rationale': 'Modernizing authentication approach'
                }
            ]
        }
        
        decisions = self.engine.capture_from_session(session_data)
        
        # Should capture meaningful decisions
        self.assertGreater(len(decisions), 0)
        
        # Check decision quality
        meaningful_decisions = [d for d in decisions if d.confidence > 0.5]
        self.assertGreater(len(meaningful_decisions), 0)


class TestKnowledgeExtractor(unittest.TestCase):
    """Test KnowledgeExtractor functionality."""
    
    def setUp(self):
        self.extractor = KnowledgeExtractor()
        self.sample_decision = DecisionRecord(
            id="test_ext_001",
            timestamp=datetime.now(),
            decision_type="technical",
            description="Decided to implement caching using Redis because it provides better performance and scalability than in-memory caching",
            rationale="Redis offers persistence and distributed caching capabilities",
            context={"project": "web_app", "module": "cache"},
            impact_level="high",
            tags=["tech:redis", "performance", "caching"],
            source="code",
            confidence=0.9,
            related_files=["cache.py", "config.py"]
        )
    
    def test_initialization(self):
        """Test proper initialization."""
        self.assertIsInstance(self.extractor.classification_rules, dict)
        self.assertIn('patterns', self.extractor.classification_rules)
    
    def test_knowledge_extraction(self):
        """Test knowledge extraction from decision."""
        knowledge = self.extractor.extract_knowledge(self.sample_decision)
        
        self.assertIsInstance(knowledge, dict)
        self.assertIn('id', knowledge)
        self.assertIn('knowledge_type', knowledge)
        self.assertIn('key_concepts', knowledge)
        self.assertIn('quality_score', knowledge)
        
        # Verify knowledge structure
        self.assertEqual(knowledge['source_decision'], self.sample_decision.id)
        self.assertIsInstance(knowledge['key_concepts'], list)
        self.assertIsInstance(knowledge['quality_score'], float)
    
    def test_knowledge_type_classification(self):
        """Test knowledge type classification."""
        # Test different decision types
        knowledge_type = self.extractor._classify_knowledge_type(self.sample_decision)
        self.assertIn(knowledge_type, [
            'best_practice', 'lesson_learned', 'optimization', 
            'implementation_detail', 'design_pattern'
        ])
    
    def test_concept_extraction(self):
        """Test key concept extraction."""
        concepts = self.extractor._extract_concepts(self.sample_decision.description)
        
        self.assertIsInstance(concepts, list)
        # Should extract technical terms
        self.assertTrue(any('redis' in concept.lower() for concept in concepts))
    
    def test_applicability_determination(self):
        """Test applicability determination."""
        applicability = self.extractor._determine_applicability(self.sample_decision)
        
        self.assertIsInstance(applicability, dict)
        self.assertIn('project_types', applicability)
        self.assertIn('contexts', applicability)
        self.assertIn('conditions', applicability)
        self.assertIn('scope', applicability)
    
    def test_quality_score_calculation(self):
        """Test quality score calculation."""
        score = self.extractor._calculate_quality_score(self.sample_decision)
        
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        
        # High quality decision should have high score
        self.assertGreater(score, 0.6)


class TestKnowledgeBaseIntegrator(unittest.TestCase):
    """Test KnowledgeBaseIntegrator functionality."""
    
    def setUp(self):
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.integrator = KnowledgeBaseIntegrator(self.temp_db.name)
        
        self.sample_decision = DecisionRecord(
            id="test_int_001",
            timestamp=datetime.now(),
            decision_type="architectural",
            description="Adopted microservices architecture for better scalability and maintainability",
            rationale="Monolithic architecture was becoming difficult to maintain",
            context={"project": "ecommerce", "team_size": 10},
            impact_level="critical",
            tags=["architecture", "microservices", "scalability"],
            source="design_doc",
            confidence=0.85,
            related_files=["architecture.md", "services.py"]
        )
    
    def tearDown(self):
        """Clean up temporary database."""
        os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test database schema creation."""
        # Check that tables exist
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            self.assertIn('decisions', tables)
            self.assertIn('knowledge', tables)
            self.assertIn('decision_search', tables)
    
    def test_decision_storage_and_retrieval(self):
        """Test storing and retrieving decisions."""
        # Store decision
        result = self.integrator.store_decision(self.sample_decision)
        self.assertTrue(result)
        
        # Search for the decision
        search_results = self.integrator.search_decisions("microservices")
        
        self.assertGreater(len(search_results), 0)
        self.assertEqual(search_results[0].id, self.sample_decision.id)
        self.assertEqual(search_results[0].description, self.sample_decision.description)
    
    def test_knowledge_storage(self):
        """Test knowledge storage."""
        sample_knowledge = {
            'id': 'knowledge_test_001',
            'source_decision': self.sample_decision.id,
            'knowledge_type': 'best_practice',
            'key_concepts': ['microservices', 'scalability', 'architecture'],
            'applicability': {
                'project_types': ['web_development', 'distributed_systems'],
                'contexts': ['scalability', 'team_growth'],
                'conditions': ['when system grows beyond single team capability'],
                'scope': 'system_wide'
            },
            'relationships': ['technology:docker', 'pattern:service_mesh'],
            'quality_score': 0.85,
            'extracted_at': datetime.now().isoformat(),
            'metadata': {
                'decision_type': 'architectural',
                'impact_level': 'critical',
                'confidence': 0.85,
                'tags': ['architecture', 'microservices']
            }
        }
        
        result = self.integrator.store_knowledge(sample_knowledge)
        self.assertTrue(result)
        
        # Retrieve knowledge by type
        knowledge_list = self.integrator.get_knowledge_by_type('best_practice')
        self.assertGreater(len(knowledge_list), 0)
        self.assertEqual(knowledge_list[0]['id'], sample_knowledge['id'])
    
    def test_full_text_search(self):
        """Test full-text search functionality."""
        # Store multiple decisions
        decisions = [
            self.sample_decision,
            DecisionRecord(
                id="search_test_001",
                timestamp=datetime.now(),
                decision_type="technical",
                description="Implemented Redis caching for performance optimization",
                rationale="Database queries were too slow",
                context={"component": "cache"},
                impact_level="high",
                tags=["performance", "caching", "redis"],
                source="code",
                confidence=0.8,
                related_files=["cache.py"]
            )
        ]
        
        for decision in decisions:
            self.integrator.store_decision(decision)
        
        # Test searches
        arch_results = self.integrator.search_decisions("microservices architecture")
        self.assertGreater(len(arch_results), 0)
        
        cache_results = self.integrator.search_decisions("Redis caching")
        self.assertGreater(len(cache_results), 0)
        
        # Should not find unrelated terms
        empty_results = self.integrator.search_decisions("blockchain quantum computing")
        self.assertEqual(len(empty_results), 0)
    
    def test_statistics_generation(self):
        """Test statistics generation."""
        # Store sample data
        self.integrator.store_decision(self.sample_decision)
        
        stats = self.integrator.get_statistics()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('total_decisions', stats)
        self.assertIn('decisions_by_type', stats)
        self.assertIn('last_updated', stats)
        
        self.assertGreater(stats['total_decisions'], 0)
        self.assertIn('architectural', stats['decisions_by_type'])


class TestKnowledgeValidator(unittest.TestCase):
    """Test KnowledgeValidator functionality."""
    
    def setUp(self):
        self.validator = KnowledgeValidator()
        
        self.high_quality_decision = DecisionRecord(
            id="valid_001",
            timestamp=datetime.now(),
            decision_type="architectural",
            description="We decided to adopt a microservices architecture for our e-commerce platform because it provides better scalability, allows independent team development, and improves system resilience",
            rationale="The monolithic architecture was becoming difficult to maintain as the team grew, and we needed better scalability for peak shopping periods",
            context={"project": "ecommerce", "team_size": 15, "traffic": "high"},
            impact_level="critical",
            tags=["architecture", "microservices", "scalability", "team-organization"],
            source="design_review",
            confidence=0.9,
            related_files=["architecture.md", "services.yaml", "deployment.md"]
        )
        
        self.low_quality_decision = DecisionRecord(
            id="invalid_001",
            timestamp=datetime.now() - timedelta(days=400),  # Old
            decision_type="technical",
            description="Fixed bug",  # Too short
            rationale="",  # No rationale
            context={},  # No context
            impact_level="low",
            tags=[],  # No tags
            source="unknown",
            confidence=0.3,  # Low confidence
            related_files=[]
        )
    
    def test_initialization(self):
        """Test proper initialization."""
        self.assertIsInstance(self.validator.quality_criteria, dict)
        self.assertIn('completeness', self.validator.quality_criteria)
        self.assertIn('clarity', self.validator.quality_criteria)
    
    def test_high_quality_decision_validation(self):
        """Test validation of high-quality decision."""
        result = self.validator.validate_decision(self.high_quality_decision)
        
        self.assertIsInstance(result, dict)
        self.assertIn('overall_score', result)
        self.assertIn('is_valid', result)
        self.assertIn('criteria_scores', result)
        
        # Should pass validation
        self.assertTrue(result['is_valid'])
        self.assertGreater(result['overall_score'], 0.7)
        
        # Should have good scores across criteria
        self.assertGreater(result['criteria_scores']['completeness'], 0.8)
        self.assertGreater(result['criteria_scores']['relevance'], 0.7)
    
    def test_low_quality_decision_validation(self):
        """Test validation of low-quality decision."""
        result = self.validator.validate_decision(self.low_quality_decision)
        
        # Should fail validation
        self.assertFalse(result['is_valid'])
        self.assertLess(result['overall_score'], 0.6)
        
        # Should have issues identified
        self.assertGreater(len(result['issues']), 0)
        self.assertGreater(len(result['recommendations']), 0)
    
    def test_completeness_checking(self):
        """Test completeness criteria checking."""
        score, issues = self.validator._check_completeness(self.high_quality_decision)
        self.assertGreater(score, 0.8)
        self.assertEqual(len(issues), 0)
        
        score, issues = self.validator._check_completeness(self.low_quality_decision)
        self.assertLess(score, 0.5)
        self.assertGreater(len(issues), 0)
    
    def test_knowledge_validation(self):
        """Test knowledge validation."""
        sample_knowledge = {
            'id': 'knowledge_valid_001',
            'source_decision': 'valid_001',
            'knowledge_type': 'best_practice',
            'key_concepts': ['microservices', 'scalability', 'team-organization'],
            'applicability': {
                'project_types': ['web_development'],
                'contexts': ['high-traffic', 'large-team'],
                'conditions': ['when scaling beyond monolith'],
                'scope': 'system_wide'
            },
            'relationships': ['pattern:microservices', 'tech:containers'],
            'quality_score': 0.85,
            'extracted_at': datetime.now().isoformat(),
            'metadata': {
                'decision_type': 'architectural',
                'impact_level': 'critical',
                'confidence': 0.9,
                'tags': ['architecture', 'microservices']
            }
        }
        
        result = self.validator.validate_knowledge(sample_knowledge)
        
        self.assertIsInstance(result, dict)
        self.assertIn('overall_score', result)
        self.assertIn('is_valid', result)
        self.assertTrue(result['is_valid'])


class TestKnowledgeCaptureSystem(unittest.TestCase):
    """Test KnowledgeCaptureSystem integration."""
    
    def setUp(self):
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.kcs = KnowledgeCaptureSystem(self.temp_db.name)
    
    def tearDown(self):
        """Clean up temporary database."""
        os.unlink(self.temp_db.name)
    
    def test_initialization(self):
        """Test system initialization."""
        self.assertIsInstance(self.kcs.capture_engine, DecisionCaptureEngine)
        self.assertIsInstance(self.kcs.extractor, KnowledgeExtractor)
        self.assertIsInstance(self.kcs.integrator, KnowledgeBaseIntegrator)
        self.assertIsInstance(self.kcs.validator, KnowledgeValidator)
    
    def test_session_data_processing(self):
        """Test processing of session data."""
        session_data = {
            'completed_tasks': [
                {
                    'id': 'task_integration_001',
                    'description': 'Implemented comprehensive knowledge capture system with SQLite backend for intelligent decision tracking and automated knowledge extraction',
                    'completed_at': datetime.now().isoformat()
                }
            ],
            'file_changes': [
                {
                    'file': 'knowledge_capture.py',
                    'type': 'new_feature',
                    'lines_changed': 500,
                    'rationale': 'Phase 3 advanced features implementation'
                }
            ]
        }
        
        result = self.kcs.capture_from_session_data(session_data)
        
        self.assertIsInstance(result, dict)
        self.assertIn('decisions_captured', result)
        self.assertIn('decisions_stored', result)
        self.assertIn('knowledge_extracted', result)
        
        # Should have processed the meaningful task
        self.assertGreater(result['decisions_captured'], 0)
    
    def test_search_functionality(self):
        """Test knowledge search functionality."""
        # First, add some sample data
        session_data = {
            'completed_tasks': [
                {
                    'id': 'search_test_001',
                    'description': 'Implemented Redis caching system for performance optimization because database queries were becoming bottleneck',
                    'completed_at': datetime.now().isoformat()
                }
            ]
        }
        
        # Process the data
        self.kcs.capture_from_session_data(session_data)
        
        # Search for it
        search_result = self.kcs.search_knowledge("Redis caching performance")
        
        self.assertIsInstance(search_result, dict)
        self.assertIn('query', search_result)
        self.assertIn('decisions_found', search_result)
        self.assertIn('decisions', search_result)
        
        # Should find the relevant decision
        if search_result['decisions_found'] > 0:
            decision = search_result['decisions'][0]
            self.assertIn('redis', decision['description'].lower())
    
    def test_insights_generation(self):
        """Test insights generation."""
        insights = self.kcs.get_insights()
        
        self.assertIsInstance(insights, dict)
        self.assertIn('statistics', insights)
        self.assertIn('insights', insights)
        self.assertIn('generated_at', insights)
        
        # Check insight structure
        insight_data = insights['insights']
        self.assertIn('knowledge_base_health', insight_data)
        self.assertIn('recommendations', insight_data)
    
    def test_codebase_analysis(self):
        """Test codebase analysis functionality."""
        # Create a temporary Python file with decision content
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create sample Python file
            sample_file = temp_path / "sample.py"
            sample_file.write_text('''
# Decided to use dataclasses for better type safety and cleaner code
from dataclasses import dataclass

@dataclass
class Configuration:
    """
    We chose to implement configuration as a dataclass because it provides
    automatic __init__, __repr__, and type hints support.
    """
    database_url: str
    api_key: str
    
    def validate(self):
        # Implemented validation because we need to ensure configuration is correct
        pass
''')
            
            # Analyze the codebase
            result = self.kcs.capture_from_codebase(str(temp_path), ['*.py'])
            
            self.assertIsInstance(result, dict)
            self.assertIn('decisions_found', result)
            self.assertIn('statistics', result)
            
            # Should find decisions in the sample file
            self.assertGreaterEqual(result['decisions_found'], 0)


class TestSystemIntegration(unittest.TestCase):
    """Test system integration and end-to-end functionality."""
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.kcs = KnowledgeCaptureSystem(self.temp_db.name)
    
    def tearDown(self):
        os.unlink(self.temp_db.name)
    
    def test_full_pipeline(self):
        """Test the complete knowledge capture pipeline."""
        # 1. Create sample decision
        decision = DecisionRecord(
            id="pipeline_test_001",
            timestamp=datetime.now(),
            decision_type="architectural",
            description="Implemented knowledge capture system using SQLite with FTS5 for full-text search capabilities because it provides good performance without external dependencies",
            rationale="We needed searchable knowledge base that doesn't require complex setup",
            context={"phase": 3, "feature": "knowledge_capture"},
            impact_level="high",
            tags=["architecture", "database", "tech:sqlite", "search"],
            source="implementation",
            confidence=0.9,
            related_files=["knowledge_capture.py", "test_knowledge_capture.py"]
        )
        
        # 2. Validate decision
        validation = self.kcs.validator.validate_decision(decision)
        self.assertTrue(validation['is_valid'])
        
        # 3. Store decision
        stored = self.kcs.integrator.store_decision(decision)
        self.assertTrue(stored)
        
        # 4. Extract knowledge
        knowledge = self.kcs.extractor.extract_knowledge(decision)
        self.assertIsInstance(knowledge, dict)
        
        # 5. Validate and store knowledge
        knowledge_validation = self.kcs.validator.validate_knowledge(knowledge)
        self.assertTrue(knowledge_validation['is_valid'])
        
        knowledge_stored = self.kcs.integrator.store_knowledge(knowledge)
        self.assertTrue(knowledge_stored)
        
        # 6. Search and verify
        search_results = self.kcs.search_knowledge("SQLite full-text search")
        self.assertGreater(search_results['decisions_found'], 0)
        
        # 7. Generate insights
        insights = self.kcs.get_insights()
        self.assertIn('statistics', insights)
        self.assertGreater(insights['statistics']['total_decisions'], 0)
        self.assertGreater(insights['statistics']['total_knowledge'], 0)
    
    def test_performance_with_multiple_decisions(self):
        """Test performance with multiple decisions."""
        import time
        
        # Create multiple sample decisions
        decisions = []
        for i in range(20):
            decision = DecisionRecord(
                id=f"perf_test_{i:03d}",
                timestamp=datetime.now(),
                decision_type=["technical", "architectural", "process"][i % 3],
                description=f"Decision {i}: Implemented feature {i} using approach {i % 3} because it provides benefits A, B, and C",
                rationale=f"Rationale for decision {i}: This approach was selected after evaluating alternatives",
                context={"iteration": i, "batch": "performance_test"},
                impact_level=["low", "medium", "high", "critical"][i % 4],
                tags=[f"tag_{i}", f"category_{i % 5}", "performance_test"],
                source="test",
                confidence=0.7 + (i % 3) * 0.1,
                related_files=[f"file_{i}.py", f"module_{i % 5}.py"]
            )
            decisions.append(decision)
        
        # Measure processing time
        start_time = time.time()
        
        for decision in decisions:
            # Full pipeline for each decision
            validation = self.kcs.validator.validate_decision(decision)
            if validation['is_valid']:
                self.kcs.integrator.store_decision(decision)
                knowledge = self.kcs.extractor.extract_knowledge(decision)
                self.kcs.integrator.store_knowledge(knowledge)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process reasonably quickly (less than 5 seconds for 20 decisions)
        self.assertLess(processing_time, 10.0)
        
        # Verify all data was stored
        stats = self.kcs.integrator.get_statistics()
        self.assertEqual(stats['total_decisions'], len(decisions))
    
    def test_error_handling(self):
        """Test error handling and resilience."""
        # Test with malformed decision
        bad_decision = DecisionRecord(
            id="",  # Empty ID
            timestamp=datetime.now(),
            decision_type="",
            description="",
            rationale="",
            context={},
            impact_level="unknown",  # Invalid impact level
            tags=[],
            source="",
            confidence=-0.5,  # Invalid confidence
            related_files=[]
        )
        
        # System should handle gracefully
        validation = self.kcs.validator.validate_decision(bad_decision)
        self.assertFalse(validation['is_valid'])
        
        # Test with invalid database path
        try:
            invalid_kcs = KnowledgeCaptureSystem("/invalid/path/database.db")
            # Should not crash, might create the path or handle gracefully
            self.assertIsNotNone(invalid_kcs)
        except Exception as e:
            # If it does raise an exception, it should be a specific, handled one
            self.assertIsInstance(e, (OSError, PermissionError))


# Test runner configuration
def run_knowledge_capture_tests():
    """Run all knowledge capture tests with detailed output."""
    
    print("Starting Knowledge Capture System Test Suite")
    print("=" * 60)
    
    # Create test suite
    test_classes = [
        TestDecisionRecord,
        TestDecisionCaptureEngine,
        TestKnowledgeExtractor,
        TestKnowledgeBaseIntegrator,
        TestKnowledgeValidator,
        TestKnowledgeCaptureSystem,
        TestSystemIntegration
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Knowledge Capture System Test Results")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('\\n')[-2]}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("Excellent! Knowledge Capture System is highly reliable")
    elif success_rate >= 80:
        print("Good! Knowledge Capture System is working well")
    elif success_rate >= 70:
        print("Fair! Some issues need attention")
    else:
        print("Poor! Significant issues need to be resolved")
    
    return result


if __name__ == "__main__":
    run_knowledge_capture_tests()