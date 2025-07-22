"""
Test Suite for Collaboration Enhancement System - Task 3.2

Comprehensive testing for the collaboration enhancement system that integrates
token-efficient task breakdown with collaborative workflows.
"""

import pytest
import tempfile
import shutil
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

# Import system under test
import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))
from molecular_analyzer.workflow_automation.advanced.collaboration_enhancement import (
    CollaborationEnhancementSystem,
    TeamMember,
    CollaborationRole,
    HandoffType,
    CollaborativeHandoff,
    TaskComplexity,
    TaskState
)


class TestCollaborationEnhancementSystem:
    """Test suite for collaboration enhancement system"""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def collaboration_system(self, temp_project_dir):
        """Create collaboration system instance for testing"""
        return CollaborationEnhancementSystem(
            project_root=temp_project_dir,
            team_id="test_team"
        )
    
    @pytest.fixture
    def sample_team_members(self):
        """Create sample team members for testing"""
        lead = TeamMember(
            id="lead_001",
            name="Dr. Test Lead",
            role=CollaborationRole.LEAD,
            expertise_areas=["architecture", "molecular analysis"],
            token_budget_per_session=25000,
            preferred_task_complexity=TaskComplexity.COMPLEX
        )
        
        developer = TeamMember(
            id="dev_001",
            name="Test Developer",
            role=CollaborationRole.DEVELOPER,
            expertise_areas=["python", "visualization"],
            token_budget_per_session=20000,
            preferred_task_complexity=TaskComplexity.MEDIUM
        )
        
        return [lead, developer]
    
    def test_initialization(self, temp_project_dir):
        """Test system initialization"""
        system = CollaborationEnhancementSystem(
            project_root=temp_project_dir,
            team_id="init_test"
        )
        
        assert system.team_id == "init_test"
        assert system.project_root == Path(temp_project_dir)
        assert system.db_path.exists()
        assert system.task_manager is not None
        assert isinstance(system.team_members, dict)
    
    def test_database_initialization(self, collaboration_system):
        """Test database tables creation"""
        with sqlite3.connect(collaboration_system.db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'team_members',
                'collaborative_handoffs', 
                'collaboration_events',
                'workflow_optimizations'
            ]
            
            for table in expected_tables:
                assert table in tables, f"Table {table} not found"
    
    def test_add_team_member(self, collaboration_system, sample_team_members):
        """Test adding team members"""
        lead = sample_team_members[0]
        
        # Add team member
        result = collaboration_system.add_team_member(lead)
        assert result is True
        
        # Verify in memory
        assert lead.id in collaboration_system.team_members
        assert collaboration_system.team_members[lead.id].name == lead.name
        
        # Verify in database
        with sqlite3.connect(collaboration_system.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM team_members WHERE id = ?",
                (lead.id,)
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[1] == lead.name  # name field
            assert row[2] == lead.role.value  # role field
    
    def test_create_collaborative_task(self, collaboration_system, sample_team_members):
        """Test creating collaborative tasks with token breakdown"""
        # Add team members first
        for member in sample_team_members:
            collaboration_system.add_team_member(member)
        
        # Create collaborative task
        task = collaboration_system.create_collaborative_task(
            title="Test Implementation Task",
            description="Implement a comprehensive test feature with multiple components including data processing, UI components, and validation logic",
            estimated_time="3-4 hours",
            success_criteria=["Feature works correctly", "Tests pass", "Documentation updated"]
        )
        
        assert task is not None
        assert task.title == "Test Implementation Task"
        assert len(task.subtasks) > 0  # Should break into subtasks
        
        # Verify task assignment
        assigned_member_found = False
        for member in collaboration_system.team_members.values():
            if task.id in member.current_tasks:
                assigned_member_found = True
                break
        
        assert assigned_member_found, "Task should be assigned to a team member"
    
    def test_task_assignment_logic(self, collaboration_system, sample_team_members):
        """Test intelligent task assignment based on expertise and workload"""
        # Add team members
        for member in sample_team_members:
            collaboration_system.add_team_member(member)
        
        # Create task that matches lead's expertise (architecture)
        task1 = collaboration_system.create_collaborative_task(
            title="System Architecture Design",
            description="Design the system architecture for molecular analysis",
            preferred_member_id="lead_001"
        )
        
        # Verify assignment to preferred member
        lead = collaboration_system.team_members["lead_001"]
        assert task1.id in lead.current_tasks
        
        # Create task without preference - should use best fit logic
        task2 = collaboration_system.create_collaborative_task(
            title="Python Data Visualization",
            description="Create python visualization components for molecular data"
        )
        
        # Should assign to developer (has python expertise)
        developer = collaboration_system.team_members["dev_001"]
        assert task2.id in developer.current_tasks
    
    def test_create_handoff(self, collaboration_system, sample_team_members):
        """Test creating task handoffs between team members"""
        # Setup
        for member in sample_team_members:
            collaboration_system.add_team_member(member)
        
        task = collaboration_system.create_collaborative_task(
            title="Test Handoff Task",
            description="Task for testing handoff functionality"
        )
        
        # Create handoff
        handoff = collaboration_system.create_handoff(
            task_id=task.id,
            from_member_id="lead_001",
            to_member_id="dev_001",
            handoff_type=HandoffType.SESSION_END,
            context_summary="Completed initial design, ready for implementation",
            next_actions=["Implement core functionality", "Add unit tests"]
        )
        
        assert handoff is not None
        assert handoff.task_id == task.id
        assert handoff.from_member == "lead_001"
        assert handoff.to_member == "dev_001"
        assert handoff.handoff_type == HandoffType.SESSION_END
        assert len(handoff.next_actions) == 2
        
        # Verify database persistence
        with sqlite3.connect(collaboration_system.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM collaborative_handoffs WHERE id = ?",
                (handoff.id,)
            )
            row = cursor.fetchone()
            assert row is not None
    
    def test_receive_handoff(self, collaboration_system, sample_team_members):
        """Test receiving and providing feedback on handoffs"""
        # Setup
        for member in sample_team_members:
            collaboration_system.add_team_member(member)
        
        task = collaboration_system.create_collaborative_task(
            title="Handoff Receive Test",
            description="Test handoff receiving"
        )
        
        handoff = collaboration_system.create_handoff(
            task_id=task.id,
            from_member_id="lead_001",
            to_member_id="dev_001",
            handoff_type=HandoffType.TASK_COMPLETION,
            context_summary="Task completed, ready for review",
            next_actions=["Review implementation", "Test functionality"]
        )
        
        # Receive handoff with feedback
        result = collaboration_system.receive_handoff(
            handoff.id,
            "dev_001",
            feedback="Context is clear, will proceed with review"
        )
        
        assert result is True
        
        # Verify handoff updated
        updated_handoff = collaboration_system.active_handoffs[handoff.id]
        assert updated_handoff.received_at is not None
        assert updated_handoff.feedback == "Context is clear, will proceed with review"
    
    def test_get_member_handoffs(self, collaboration_system, sample_team_members):
        """Test retrieving handoffs for specific team member"""
        # Setup
        for member in sample_team_members:
            collaboration_system.add_team_member(member)
        
        task = collaboration_system.create_collaborative_task(
            title="Member Handoffs Test",
            description="Test member handoff retrieval"
        )
        
        # Create multiple handoffs to developer
        handoff1 = collaboration_system.create_handoff(
            task_id=task.id,
            from_member_id="lead_001",
            to_member_id="dev_001",
            handoff_type=HandoffType.SESSION_END,
            context_summary="First handoff",
            next_actions=["Action 1"]
        )
        
        handoff2 = collaboration_system.create_handoff(
            task_id=task.id,
            from_member_id="lead_001",
            to_member_id="dev_001",
            handoff_type=HandoffType.REVIEW_NEEDED,
            context_summary="Second handoff",
            next_actions=["Action 2"]
        )
        
        # Get handoffs for developer
        member_handoffs = collaboration_system.get_member_handoffs("dev_001")
        
        assert len(member_handoffs) == 2
        handoff_ids = [h.id for h in member_handoffs]
        assert handoff1.id in handoff_ids
        assert handoff2.id in handoff_ids
    
    def test_intelligent_task_recommendations(self, collaboration_system, sample_team_members):
        """Test intelligent task recommendations based on token budget and expertise"""
        # Setup
        for member in sample_team_members:
            collaboration_system.add_team_member(member)
        
        # Create task with token-efficient breakdown
        task = collaboration_system.create_collaborative_task(
            title="Large Recommendation Test Task",
            description="Large comprehensive task requiring multiple subtasks for testing intelligent recommendations system",
            estimated_time="5-6 hours"  # Should trigger task breakdown
        )
        
        # Get recommendations for team member
        recommendations = collaboration_system.get_intelligent_task_recommendations("lead_001")
        
        assert len(recommendations) > 0
        
        # Check recommendation structure
        for rec in recommendations:
            assert "type" in rec
            assert "priority" in rec
            assert "reasoning" in rec
            
            if rec["type"] == "next_subtask":
                assert "subtask" in rec
                assert "estimated_time" in rec
                assert rec["subtask"]["estimated_tokens"] <= 25000  # Within budget
    
    def test_collaboration_metrics_generation(self, collaboration_system, sample_team_members):
        """Test generation of collaboration metrics"""
        # Setup with some activity
        for member in sample_team_members:
            collaboration_system.add_team_member(member)
        
        task = collaboration_system.create_collaborative_task(
            title="Metrics Test Task",
            description="Task for testing metrics generation"
        )
        
        handoff = collaboration_system.create_handoff(
            task_id=task.id,
            from_member_id="lead_001",
            to_member_id="dev_001",
            handoff_type=HandoffType.SESSION_END,
            context_summary="Metrics test handoff",
            next_actions=["Continue with metrics testing"]
        )
        
        collaboration_system.receive_handoff(handoff.id, "dev_001")
        
        # Generate metrics
        metrics = collaboration_system.generate_collaboration_metrics(days_back=1)
        
        assert metrics.team_id == "test_team"
        assert metrics.total_tasks_coordinated >= 1
        assert metrics.handoff_success_rate >= 0.0
        assert metrics.coordination_efficiency_improvement >= 0.0
    
    def test_workflow_optimizations(self, collaboration_system, sample_team_members):
        """Test workflow optimization recommendations"""
        # Setup
        for member in sample_team_members:
            collaboration_system.add_team_member(member)
        
        # Create large task that should generate optimizations
        task = collaboration_system.create_collaborative_task(
            title="Large Optimization Test Task",
            description="Implement comprehensive system with multiple components including data processing, machine learning models, user interface, API endpoints, and extensive testing suite",
            estimated_time="8-10 hours"  # Large task
        )
        
        # Get workflow optimizations
        optimizations = collaboration_system.get_workflow_optimizations(implemented=False)
        
        assert len(optimizations) > 0
        
        # Check optimization structure
        for opt in optimizations:
            assert opt.team_id == "test_team"
            assert opt.optimization_type in ["parallel_execution", "token_optimization"]
            assert opt.impact_estimate is not None
            assert opt.implementation_effort is not None
            assert not opt.implemented
    
    def test_collaboration_dashboard_data(self, collaboration_system, sample_team_members):
        """Test collaboration dashboard data generation"""
        # Setup with activity
        for member in sample_team_members:
            collaboration_system.add_team_member(member)
        
        task = collaboration_system.create_collaborative_task(
            title="Dashboard Test Task",
            description="Task for testing dashboard data"
        )
        
        # Generate dashboard data
        dashboard_data = collaboration_system.create_collaboration_dashboard_data()
        
        # Verify structure
        assert "team_overview" in dashboard_data
        assert "coordination_metrics" in dashboard_data
        assert "token_efficiency" in dashboard_data
        assert "team_performance" in dashboard_data
        assert "success_indicators" in dashboard_data
        
        # Verify team overview
        team_overview = dashboard_data["team_overview"]
        assert team_overview["team_id"] == "test_team"
        assert team_overview["total_members"] == 2
        assert team_overview["active_members"] == 2
        
        # Verify token efficiency data
        token_efficiency = dashboard_data["token_efficiency"]
        assert token_efficiency["total_team_token_budget"] == 45000  # 25000 + 20000
        assert "token_utilization_efficiency" in token_efficiency
    
    def test_token_efficient_integration(self, collaboration_system, sample_team_members):
        """Test integration with existing token-efficient task manager"""
        # Setup
        for member in sample_team_members:
            collaboration_system.add_team_member(member)
        
        # Create large task that should be broken down
        task = collaboration_system.create_collaborative_task(
            title="Token Integration Test",
            description="Implement comprehensive molecular analysis system with multiple complex components including quantum calculations, machine learning models, visualization dashboard, batch processing, and extensive API endpoints",
            estimated_time="12-15 hours"  # Very large task
        )
        
        # Verify task breakdown occurred
        assert len(task.subtasks) > 0
        
        # Check that subtasks are within reasonable token limits
        for subtask in task.subtasks:
            assert subtask.estimated_tokens <= 8000  # Complex subtasks should be manageable
        
        # Test getting next executable subtask
        next_subtask = collaboration_system.task_manager.get_next_executable_subtask(task.id)
        assert next_subtask is not None
        assert next_subtask.state == TaskState.PENDING
        
        # Test handoff context includes token information
        handoff_context = collaboration_system.task_manager.get_session_handoff_context(task.id)
        assert "task_summary" in handoff_context
        assert "consistency_rules" in handoff_context
        assert "success_criteria" in handoff_context
    
    def test_error_handling(self, collaboration_system):
        """Test error handling in various scenarios"""
        # Test creating handoff with non-existent task
        handoff = collaboration_system.create_handoff(
            task_id="non_existent_task",
            from_member_id="lead_001",
            to_member_id="dev_001",
            handoff_type=HandoffType.SESSION_END,
            context_summary="Test error handling",
            next_actions=["Should fail gracefully"]
        )
        
        assert handoff is None  # Should return None on error
        
        # Test receiving handoff with wrong member
        result = collaboration_system.receive_handoff(
            "non_existent_handoff",
            "non_existent_member"
        )
        
        assert result is False  # Should return False on error
        
        # Test getting recommendations for non-existent member
        recommendations = collaboration_system.get_intelligent_task_recommendations(
            "non_existent_member"
        )
        
        assert recommendations == []  # Should return empty list


class TestCollaborationMetrics:
    """Test suite for collaboration metrics calculation"""
    
    def test_efficiency_improvement_calculation(self, temp_project_dir):
        """Test calculation of coordination efficiency improvements"""
        system = CollaborationEnhancementSystem(temp_project_dir, "metrics_test")
        
        # Add test data to database
        with sqlite3.connect(system.db_path) as conn:
            # Insert test handoffs with known timing
            test_time = datetime.now()
            conn.execute('''
                INSERT INTO collaborative_handoffs 
                (id, task_id, from_member, to_member, handoff_type, 
                 context_summary, detailed_context, next_actions,
                 created_at, received_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                'test_handoff_1', 'test_task_1', 'member_1', 'member_2', 'session_end',
                'Test handoff', '{}', '["test action"]',
                test_time.isoformat(),
                (test_time + timedelta(minutes=30)).isoformat()
            ))
        
        metrics = system.generate_collaboration_metrics(days_back=1)
        
        assert metrics.total_tasks_coordinated >= 1
        assert metrics.average_handoff_time == 0.5  # 30 minutes = 0.5 hours
        assert metrics.handoff_success_rate == 100.0  # All test handoffs received
    
    def test_token_utilization_metrics(self, temp_project_dir):
        """Test token utilization efficiency calculations"""
        system = CollaborationEnhancementSystem(temp_project_dir, "token_metrics_test")
        
        # Add team members with different token budgets
        member1 = TeamMember(
            id="high_budget",
            name="High Budget Member",
            role=CollaborationRole.LEAD,
            token_budget_per_session=30000
        )
        
        member2 = TeamMember(
            id="low_budget", 
            name="Low Budget Member",
            role=CollaborationRole.DEVELOPER,
            token_budget_per_session=15000
        )
        
        system.add_team_member(member1)
        system.add_team_member(member2)
        
        # Create tasks to simulate token usage
        system.create_collaborative_task(
            title="Token Test Task 1",
            description="First test task for token metrics"
        )
        
        system.create_collaborative_task(
            title="Token Test Task 2", 
            description="Second test task for token metrics"
        )
        
        metrics = system.generate_collaboration_metrics()
        dashboard = system.create_collaboration_dashboard_data()
        
        # Verify token efficiency calculations
        assert dashboard["token_efficiency"]["total_team_token_budget"] == 45000
        assert metrics.token_utilization_efficiency >= 60.0  # Should have reasonable efficiency


# Integration test
def test_end_to_end_collaboration_scenario():
    """End-to-end test of complete collaboration workflow"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize system
        system = CollaborationEnhancementSystem(temp_dir, "e2e_test")
        
        # Add team members
        lead = TeamMember("lead", "Lead", CollaborationRole.LEAD, ["architecture"])
        dev = TeamMember("dev", "Developer", CollaborationRole.DEVELOPER, ["python"])
        
        system.add_team_member(lead)
        system.add_team_member(dev)
        
        # Create collaborative task
        task = system.create_collaborative_task(
            title="E2E Test Implementation",
            description="End-to-end test implementation with multiple components",
            estimated_time="4 hours"
        )
        
        # Create handoff
        handoff = system.create_handoff(
            task_id=task.id,
            from_member_id="lead",
            to_member_id="dev", 
            handoff_type=HandoffType.SESSION_END,
            context_summary="Architecture complete, ready for implementation",
            next_actions=["Implement core logic", "Add tests"]
        )
        
        # Receive handoff
        system.receive_handoff(handoff.id, "dev", feedback="Ready to implement")
        
        # Get recommendations
        recommendations = system.get_intelligent_task_recommendations("dev")
        assert len(recommendations) > 0
        
        # Generate metrics and dashboard
        metrics = system.generate_collaboration_metrics()
        dashboard = system.create_collaboration_dashboard_data()
        
        # Verify end-to-end flow worked
        assert task is not None
        assert handoff is not None
        assert metrics.total_tasks_coordinated >= 1
        assert dashboard["team_overview"]["total_members"] == 2
        
        print("✅ End-to-end collaboration scenario completed successfully")


if __name__ == "__main__":
    # Run key tests manually for validation
    test_end_to_end_collaboration_scenario()
    print("🚀 All collaboration enhancement tests completed successfully!")