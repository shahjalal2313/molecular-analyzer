"""
Status Tracking Component for Molecular Analysis Workflows

Tracks and displays the status of molecular analysis tasks and workflows.
"""

import streamlit as st
import pandas as pd
from typing import Any, Dict, List, Optional, Union, Tuple
from enum import Enum
from datetime import datetime, timedelta
import json
import time

from ..base import BaseComponent


class TaskStatus(Enum):
    """Task status types."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WorkflowStatus(Enum):
    """Workflow status types."""
    INITIALIZED = "initialized"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StatusTrackerComponent(BaseComponent):
    """
    Status tracking component for molecular analysis workflows.
    
    Features:
    - Task status management (pending, running, completed, failed)
    - Workflow progress tracking
    - Real-time status updates
    - Task dependency management
    - Time tracking and analytics
    - Error logging and reporting
    - Export and reporting capabilities
    """
    
    def __init__(self, name: str = "Status Tracker", key_prefix: str = None):
        """
        Initialize the status tracker component.
        
        Args:
            name: Component display name
            key_prefix: Unique key prefix for Streamlit widgets
        """
        super().__init__(name, key_prefix)
        
        # Task and workflow storage
        self.tasks = {}
        self.workflows = {}
        self.task_history = []
        self.workflow_history = []
        
        # Configuration
        self.auto_refresh = True
        self.refresh_interval = 5  # seconds
        self.max_history_entries = 1000
        
        # Status display configuration
        self.status_icons = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.RUNNING: "🔄",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.CANCELLED: "🚫",
            TaskStatus.PAUSED: "⏸️"
        }
        
        self.status_colors = {
            TaskStatus.PENDING: "#6c757d",
            TaskStatus.RUNNING: "#17a2b8",
            TaskStatus.COMPLETED: "#28a745",
            TaskStatus.FAILED: "#dc3545",
            TaskStatus.CANCELLED: "#6c757d",
            TaskStatus.PAUSED: "#ffc107"
        }
        
        self.priority_colors = {
            TaskPriority.LOW: "#6c757d",
            TaskPriority.MEDIUM: "#ffc107",
            TaskPriority.HIGH: "#fd7e14",
            TaskPriority.CRITICAL: "#dc3545"
        }
    
    def add_task(self, 
                 task_id: str,
                 name: str,
                 description: str = None,
                 priority: TaskPriority = TaskPriority.MEDIUM,
                 estimated_duration: timedelta = None,
                 dependencies: List[str] = None,
                 metadata: Dict[str, Any] = None) -> bool:
        """
        Add a new task to track.
        
        Args:
            task_id: Unique task identifier
            name: Task display name
            description: Task description
            priority: Task priority level
            estimated_duration: Estimated task duration
            dependencies: List of task IDs this task depends on
            metadata: Additional task metadata
            
        Returns:
            True if task added successfully, False otherwise
        """
        try:
            if task_id in self.tasks:
                self.add_warning(f"Task {task_id} already exists")
                return False
            
            task = {
                'id': task_id,
                'name': name,
                'description': description or "",
                'status': TaskStatus.PENDING,
                'priority': priority,
                'created_at': datetime.now(),
                'started_at': None,
                'completed_at': None,
                'estimated_duration': estimated_duration,
                'actual_duration': None,
                'dependencies': dependencies or [],
                'metadata': metadata or {},
                'progress': 0.0,
                'error_message': None,
                'logs': []
            }
            
            self.tasks[task_id] = task
            self._record_task_history(task_id, TaskStatus.PENDING, "Task created")
            
            self.log_interaction("task_added", {
                'task_id': task_id,
                'name': name,
                'priority': priority.value
            })
            
            return True
            
        except Exception as e:
            self.add_error(f"Error adding task {task_id}: {str(e)}", e)
            return False
    
    def update_task_status(self, 
                          task_id: str, 
                          status: TaskStatus,
                          progress: float = None,
                          message: str = None,
                          error_message: str = None) -> bool:
        """
        Update task status and progress.
        
        Args:
            task_id: Task identifier
            status: New task status
            progress: Task progress (0-100)
            message: Status message
            error_message: Error message if status is FAILED
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            if task_id not in self.tasks:
                self.add_error(f"Task {task_id} not found")
                return False
            
            task = self.tasks[task_id]
            old_status = task['status']
            
            # Update task fields
            task['status'] = status
            
            if progress is not None:
                task['progress'] = max(0, min(progress, 100))
            
            if error_message:
                task['error_message'] = error_message
            
            # Update timestamps
            now = datetime.now()
            
            if status == TaskStatus.RUNNING and old_status == TaskStatus.PENDING:
                task['started_at'] = now
            elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                task['completed_at'] = now
                if task['started_at']:
                    task['actual_duration'] = now - task['started_at']
            
            # Add log entry
            log_entry = {
                'timestamp': now,
                'status': status.value,
                'message': message or f"Status changed to {status.value}",
                'progress': task['progress']
            }
            task['logs'].append(log_entry)
            
            # Record in history
            self._record_task_history(task_id, status, message or f"Status changed to {status.value}")
            
            self.log_interaction("task_status_updated", {
                'task_id': task_id,
                'old_status': old_status.value,
                'new_status': status.value,
                'progress': task['progress']
            })
            
            return True
            
        except Exception as e:
            self.add_error(f"Error updating task {task_id}: {str(e)}", e)
            return False
    
    def add_workflow(self,
                    workflow_id: str,
                    name: str,
                    description: str = None,
                    task_ids: List[str] = None,
                    metadata: Dict[str, Any] = None) -> bool:
        """
        Add a new workflow to track.
        
        Args:
            workflow_id: Unique workflow identifier
            name: Workflow display name
            description: Workflow description
            task_ids: List of task IDs in this workflow
            metadata: Additional workflow metadata
            
        Returns:
            True if workflow added successfully, False otherwise
        """
        try:
            if workflow_id in self.workflows:
                self.add_warning(f"Workflow {workflow_id} already exists")
                return False
            
            workflow = {
                'id': workflow_id,
                'name': name,
                'description': description or "",
                'status': WorkflowStatus.INITIALIZED,
                'created_at': datetime.now(),
                'started_at': None,
                'completed_at': None,
                'task_ids': task_ids or [],
                'metadata': metadata or {},
                'progress': 0.0,
                'error_message': None
            }
            
            self.workflows[workflow_id] = workflow
            self._record_workflow_history(workflow_id, WorkflowStatus.INITIALIZED, "Workflow created")
            
            self.log_interaction("workflow_added", {
                'workflow_id': workflow_id,
                'name': name,
                'task_count': len(task_ids or [])
            })
            
            return True
            
        except Exception as e:
            self.add_error(f"Error adding workflow {workflow_id}: {str(e)}", e)
            return False
    
    def update_workflow_status(self) -> None:
        """Update workflow status based on constituent tasks."""
        try:
            for workflow_id, workflow in self.workflows.items():
                if not workflow['task_ids']:
                    continue
                
                # Get task statuses
                task_statuses = []
                total_progress = 0
                
                for task_id in workflow['task_ids']:
                    if task_id in self.tasks:
                        task = self.tasks[task_id]
                        task_statuses.append(task['status'])
                        total_progress += task['progress']
                
                if not task_statuses:
                    continue
                
                # Calculate workflow progress
                workflow['progress'] = total_progress / len(task_statuses)
                
                # Determine workflow status
                old_status = workflow['status']
                new_status = self._calculate_workflow_status(task_statuses)
                
                if new_status != old_status:
                    workflow['status'] = new_status
                    
                    # Update timestamps
                    now = datetime.now()
                    if new_status == WorkflowStatus.RUNNING and old_status == WorkflowStatus.INITIALIZED:
                        workflow['started_at'] = now
                    elif new_status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
                        workflow['completed_at'] = now
                    
                    self._record_workflow_history(workflow_id, new_status, f"Status changed to {new_status.value}")
            
        except Exception as e:
            self.add_error(f"Error updating workflow status: {str(e)}", e)
    
    def _calculate_workflow_status(self, task_statuses: List[TaskStatus]) -> WorkflowStatus:
        """
        Calculate workflow status based on task statuses.
        
        Args:
            task_statuses: List of task statuses
            
        Returns:
            Calculated workflow status
        """
        if not task_statuses:
            return WorkflowStatus.INITIALIZED
        
        # Count status types
        status_counts = {}
        for status in task_statuses:
            status_counts[status] = status_counts.get(status, 0) + 1
        
        total_tasks = len(task_statuses)
        
        # Determine workflow status
        if status_counts.get(TaskStatus.FAILED, 0) > 0:
            return WorkflowStatus.FAILED
        elif status_counts.get(TaskStatus.CANCELLED, 0) == total_tasks:
            return WorkflowStatus.CANCELLED
        elif status_counts.get(TaskStatus.COMPLETED, 0) == total_tasks:
            return WorkflowStatus.COMPLETED
        elif status_counts.get(TaskStatus.PAUSED, 0) > 0:
            return WorkflowStatus.PAUSED
        elif status_counts.get(TaskStatus.RUNNING, 0) > 0:
            return WorkflowStatus.RUNNING
        else:
            return WorkflowStatus.INITIALIZED
    
    def _record_task_history(self, task_id: str, status: TaskStatus, message: str) -> None:
        """Record task status change in history."""
        history_entry = {
            'timestamp': datetime.now(),
            'type': 'task',
            'id': task_id,
            'status': status.value,
            'message': message
        }
        
        self.task_history.append(history_entry)
        
        # Keep history size manageable
        if len(self.task_history) > self.max_history_entries:
            self.task_history = self.task_history[-self.max_history_entries:]
    
    def _record_workflow_history(self, workflow_id: str, status: WorkflowStatus, message: str) -> None:
        """Record workflow status change in history."""
        history_entry = {
            'timestamp': datetime.now(),
            'type': 'workflow',
            'id': workflow_id,
            'status': status.value,
            'message': message
        }
        
        self.workflow_history.append(history_entry)
        
        # Keep history size manageable
        if len(self.workflow_history) > self.max_history_entries:
            self.workflow_history = self.workflow_history[-self.max_history_entries:]
    
    def get_task_summary(self) -> Dict[str, Any]:
        """
        Get summary of all tasks.
        
        Returns:
            Task summary dictionary
        """
        try:
            status_counts = {}
            priority_counts = {}
            total_tasks = len(self.tasks)
            
            for task in self.tasks.values():
                # Count by status
                status = task['status']
                status_counts[status.value] = status_counts.get(status.value, 0) + 1
                
                # Count by priority
                priority = task['priority']
                priority_counts[priority.value] = priority_counts.get(priority.value, 0) + 1
            
            return {
                'total_tasks': total_tasks,
                'status_counts': status_counts,
                'priority_counts': priority_counts,
                'completion_rate': (status_counts.get('completed', 0) / total_tasks * 100) if total_tasks > 0 else 0
            }
            
        except Exception as e:
            self.add_error(f"Error generating task summary: {str(e)}", e)
            return {}
    
    def render_task_table(self) -> None:
        """Render table of all tasks."""
        try:
            if not self.tasks:
                st.info("No tasks to display")
                return
            
            # Prepare data for table
            table_data = []
            for task in self.tasks.values():
                table_data.append({
                    'ID': task['id'],
                    'Name': task['name'],
                    'Status': f"{self.status_icons[task['status']]} {task['status'].value}",
                    'Priority': task['priority'].value,
                    'Progress': f"{task['progress']:.1f}%",
                    'Created': task['created_at'].strftime("%Y-%m-%d %H:%M"),
                    'Duration': str(task['actual_duration']).split('.')[0] if task['actual_duration'] else "N/A"
                })
            
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True)
            
        except Exception as e:
            self.add_error(f"Error rendering task table: {str(e)}", e)
    
    def render_workflow_table(self) -> None:
        """Render table of all workflows."""
        try:
            if not self.workflows:
                st.info("No workflows to display")
                return
            
            # Update workflow statuses first
            self.update_workflow_status()
            
            # Prepare data for table
            table_data = []
            for workflow in self.workflows.values():
                table_data.append({
                    'ID': workflow['id'],
                    'Name': workflow['name'],
                    'Status': workflow['status'].value,
                    'Progress': f"{workflow['progress']:.1f}%",
                    'Tasks': len(workflow['task_ids']),
                    'Created': workflow['created_at'].strftime("%Y-%m-%d %H:%M")
                })
            
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True)
            
        except Exception as e:
            self.add_error(f"Error rendering workflow table: {str(e)}", e)
    
    def render_status_summary(self) -> None:
        """Render status summary dashboard."""
        try:
            summary = self.get_task_summary()
            
            if summary['total_tasks'] == 0:
                st.info("No tasks to summarize")
                return
            
            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Tasks", summary['total_tasks'])
            
            with col2:
                completed = summary['status_counts'].get('completed', 0)
                st.metric("Completed", completed)
            
            with col3:
                running = summary['status_counts'].get('running', 0)
                st.metric("Running", running)
            
            with col4:
                failed = summary['status_counts'].get('failed', 0)
                st.metric("Failed", failed)
            
            # Status breakdown
            st.subheader("Status Breakdown")
            status_cols = st.columns(len(summary['status_counts']))
            
            for i, (status, count) in enumerate(summary['status_counts'].items()):
                with status_cols[i]:
                    percentage = (count / summary['total_tasks']) * 100
                    st.metric(
                        status.title(),
                        f"{count} ({percentage:.1f}%)"
                    )
            
        except Exception as e:
            self.add_error(f"Error rendering status summary: {str(e)}", e)
    
    def render_recent_activity(self, limit: int = 10) -> None:
        """
        Render recent activity log.
        
        Args:
            limit: Maximum number of entries to show
        """
        try:
            # Combine and sort all history
            all_history = self.task_history + self.workflow_history
            all_history.sort(key=lambda x: x['timestamp'], reverse=True)
            
            if not all_history:
                st.info("No recent activity")
                return
            
            st.subheader("Recent Activity")
            
            for entry in all_history[:limit]:
                timestamp = entry['timestamp'].strftime("%H:%M:%S")
                item_type = entry['type'].title()
                item_id = entry['id']
                status = entry['status']
                message = entry['message']
                
                st.write(f"**{timestamp}** - {item_type} `{item_id}`: {message}")
            
        except Exception as e:
            self.add_error(f"Error rendering recent activity: {str(e)}", e)
    
    def render(self, 
               view_type: str = "summary",
               auto_refresh: bool = None) -> Any:
        """
        Render the status tracker component.
        
        Args:
            view_type: Type of view ("summary", "tasks", "workflows", "activity")
            auto_refresh: Whether to enable auto-refresh
            
        Returns:
            Current status data
        """
        try:
            if auto_refresh is not None:
                self.auto_refresh = auto_refresh
            
            # Auto-refresh
            if self.auto_refresh:
                placeholder = st.empty()
                with placeholder:
                    st.info("🔄 Auto-refreshing...")
                time.sleep(1)
                placeholder.empty()
            
            # View selection
            view_options = {
                "summary": "Status Summary",
                "tasks": "Task List",
                "workflows": "Workflow List",
                "activity": "Recent Activity"
            }
            
            selected_view = st.selectbox(
                "Select View",
                list(view_options.keys()),
                format_func=lambda x: view_options[x],
                index=list(view_options.keys()).index(view_type),
                key=self.get_key("view_selector")
            )
            
            # Render selected view
            if selected_view == "summary":
                self.render_status_summary()
            elif selected_view == "tasks":
                self.render_task_table()
            elif selected_view == "workflows":
                self.render_workflow_table()
            elif selected_view == "activity":
                self.render_recent_activity()
            
            # Display any messages
            self.display_messages()
            
            return {
                'tasks': len(self.tasks),
                'workflows': len(self.workflows),
                'summary': self.get_task_summary()
            }
            
        except Exception as e:
            self.add_error(f"Error rendering status tracker: {str(e)}", e)
            self.display_messages()
            return {}
    
    def export_status_data(self) -> Dict[str, Any]:
        """
        Export all status tracking data.
        
        Returns:
            Complete status data
        """
        try:
            return {
                'tasks': {
                    task_id: {
                        **task,
                        'created_at': task['created_at'].isoformat(),
                        'started_at': task['started_at'].isoformat() if task['started_at'] else None,
                        'completed_at': task['completed_at'].isoformat() if task['completed_at'] else None,
                        'status': task['status'].value,
                        'priority': task['priority'].value,
                        'estimated_duration': str(task['estimated_duration']) if task['estimated_duration'] else None,
                        'actual_duration': str(task['actual_duration']) if task['actual_duration'] else None,
                        'logs': [
                            {
                                **log,
                                'timestamp': log['timestamp'].isoformat()
                            }
                            for log in task['logs']
                        ]
                    }
                    for task_id, task in self.tasks.items()
                },
                'workflows': {
                    workflow_id: {
                        **workflow,
                        'created_at': workflow['created_at'].isoformat(),
                        'started_at': workflow['started_at'].isoformat() if workflow['started_at'] else None,
                        'completed_at': workflow['completed_at'].isoformat() if workflow['completed_at'] else None,
                        'status': workflow['status'].value
                    }
                    for workflow_id, workflow in self.workflows.items()
                },
                'task_history': [
                    {
                        **entry,
                        'timestamp': entry['timestamp'].isoformat()
                    }
                    for entry in self.task_history
                ],
                'workflow_history': [
                    {
                        **entry,
                        'timestamp': entry['timestamp'].isoformat()
                    }
                    for entry in self.workflow_history
                ],
                'summary': self.get_task_summary()
            }
            
        except Exception as e:
            self.add_error(f"Error exporting status data: {str(e)}", e)
            return {}