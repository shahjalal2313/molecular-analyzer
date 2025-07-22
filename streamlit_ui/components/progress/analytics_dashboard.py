"""
Analytics Dashboard Component for Progress Metrics

Provides comprehensive analytics and metrics for molecular analysis workflows.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict
from enum import Enum

from ..base import BaseComponent

# Import related components for data integration
from .progress_bar import ProgressBarComponent
from .status_tracker import StatusTrackerComponent, TaskStatus, TaskPriority


class MetricType(Enum):
    """Types of metrics to display."""
    PERFORMANCE = "performance"
    PRODUCTIVITY = "productivity"
    QUALITY = "quality"
    EFFICIENCY = "efficiency"


class TimeRange(Enum):
    """Time range options for analytics."""
    LAST_HOUR = "last_hour"
    LAST_DAY = "last_day"
    LAST_WEEK = "last_week"
    LAST_MONTH = "last_month"
    ALL_TIME = "all_time"
    CUSTOM = "custom"


class AnalyticsDashboardComponent(BaseComponent):
    """
    Analytics dashboard component for progress metrics and insights.
    
    Features:
    - Task performance analytics
    - Workflow efficiency metrics
    - Time-based progress analysis
    - Resource utilization tracking
    - Predictive analytics
    - Custom metric definitions
    - Export and reporting capabilities
    """
    
    def __init__(self, name: str = "Analytics Dashboard", key_prefix: str = None):
        """
        Initialize the analytics dashboard component.
        
        Args:
            name: Component display name
            key_prefix: Unique key prefix for Streamlit widgets
        """
        super().__init__(name, key_prefix)
        
        # Data sources
        self.progress_trackers = {}
        self.status_trackers = {}
        self.custom_metrics = {}
        
        # Analytics configuration
        self.time_range = TimeRange.LAST_DAY
        self.custom_start_date = None
        self.custom_end_date = None
        self.refresh_interval = 30  # seconds
        
        # Chart configurations
        self.chart_colors = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#2ca02c',
            'warning': '#d62728',
            'info': '#9467bd'
        }
        
        # Cached analytics data
        self._analytics_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 60  # seconds
    
    def add_data_source(self, 
                       source_id: str,
                       source_type: str,
                       data_source: Union[ProgressBarComponent, StatusTrackerComponent]) -> bool:
        """
        Add a data source for analytics.
        
        Args:
            source_id: Unique source identifier
            source_type: Type of source ('progress' or 'status')
            data_source: Data source component
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            if source_type == 'progress':
                self.progress_trackers[source_id] = data_source
            elif source_type == 'status':
                self.status_trackers[source_id] = data_source
            else:
                self.add_error(f"Unknown source type: {source_type}")
                return False
            
            # Clear cache when new source is added
            self._clear_cache()
            
            self.log_interaction("data_source_added", {
                'source_id': source_id,
                'source_type': source_type
            })
            
            return True
            
        except Exception as e:
            self.add_error(f"Error adding data source {source_id}: {str(e)}", e)
            return False
    
    def remove_data_source(self, source_id: str) -> bool:
        """
        Remove a data source.
        
        Args:
            source_id: Source identifier to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        try:
            removed = False
            
            if source_id in self.progress_trackers:
                del self.progress_trackers[source_id]
                removed = True
            
            if source_id in self.status_trackers:
                del self.status_trackers[source_id]
                removed = True
            
            if removed:
                self._clear_cache()
                self.log_interaction("data_source_removed", {'source_id': source_id})
            
            return removed
            
        except Exception as e:
            self.add_error(f"Error removing data source {source_id}: {str(e)}", e)
            return False
    
    def add_custom_metric(self, 
                         metric_id: str,
                         name: str,
                         value: float,
                         unit: str = "",
                         description: str = "",
                         timestamp: datetime = None) -> bool:
        """
        Add a custom metric.
        
        Args:
            metric_id: Unique metric identifier
            name: Metric display name
            value: Metric value
            unit: Metric unit
            description: Metric description
            timestamp: Metric timestamp (defaults to now)
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            metric = {
                'id': metric_id,
                'name': name,
                'value': value,
                'unit': unit,
                'description': description,
                'timestamp': timestamp or datetime.now()
            }
            
            if metric_id not in self.custom_metrics:
                self.custom_metrics[metric_id] = []
            
            self.custom_metrics[metric_id].append(metric)
            
            # Keep only recent entries
            max_entries = 1000
            if len(self.custom_metrics[metric_id]) > max_entries:
                self.custom_metrics[metric_id] = self.custom_metrics[metric_id][-max_entries:]
            
            self._clear_cache()
            
            return True
            
        except Exception as e:
            self.add_error(f"Error adding custom metric {metric_id}: {str(e)}", e)
            return False
    
    def _clear_cache(self) -> None:
        """Clear analytics cache."""
        self._analytics_cache = {}
        self._cache_timestamp = None
    
    def _is_cache_valid(self) -> bool:
        """Check if analytics cache is still valid."""
        if self._cache_timestamp is None:
            return False
        
        elapsed = (datetime.now() - self._cache_timestamp).total_seconds()
        return elapsed < self._cache_ttl
    
    def _get_time_filter(self) -> Tuple[datetime, datetime]:
        """
        Get start and end datetime for the selected time range.
        
        Returns:
            Tuple of (start_time, end_time)
        """
        end_time = datetime.now()
        
        if self.time_range == TimeRange.LAST_HOUR:
            start_time = end_time - timedelta(hours=1)
        elif self.time_range == TimeRange.LAST_DAY:
            start_time = end_time - timedelta(days=1)
        elif self.time_range == TimeRange.LAST_WEEK:
            start_time = end_time - timedelta(weeks=1)
        elif self.time_range == TimeRange.LAST_MONTH:
            start_time = end_time - timedelta(days=30)
        elif self.time_range == TimeRange.CUSTOM:
            start_time = self.custom_start_date or (end_time - timedelta(days=1))
            end_time = self.custom_end_date or end_time
        else:  # ALL_TIME
            start_time = datetime.min
        
        return start_time, end_time
    
    def calculate_task_analytics(self) -> Dict[str, Any]:
        """
        Calculate task-based analytics from status trackers.
        
        Returns:
            Task analytics dictionary
        """
        try:
            if 'task_analytics' in self._analytics_cache and self._is_cache_valid():
                return self._analytics_cache['task_analytics']
            
            start_time, end_time = self._get_time_filter()
            
            analytics = {
                'total_tasks': 0,
                'completed_tasks': 0,
                'failed_tasks': 0,
                'running_tasks': 0,
                'pending_tasks': 0,
                'average_completion_time': 0,
                'success_rate': 0,
                'throughput': 0,
                'task_distribution': {},
                'priority_distribution': {},
                'completion_times': [],
                'failure_rate_over_time': [],
                'throughput_over_time': []
            }
            
            all_tasks = []
            
            # Collect data from all status trackers
            for tracker in self.status_trackers.values():
                for task in tracker.tasks.values():
                    if task['created_at'] >= start_time and task['created_at'] <= end_time:
                        all_tasks.append(task)
            
            if not all_tasks:
                self._analytics_cache['task_analytics'] = analytics
                self._cache_timestamp = datetime.now()
                return analytics
            
            # Calculate basic metrics
            analytics['total_tasks'] = len(all_tasks)
            
            for task in all_tasks:
                status = task['status']
                
                if status == TaskStatus.COMPLETED:
                    analytics['completed_tasks'] += 1
                    if task['actual_duration']:
                        analytics['completion_times'].append(task['actual_duration'].total_seconds())
                elif status == TaskStatus.FAILED:
                    analytics['failed_tasks'] += 1
                elif status == TaskStatus.RUNNING:
                    analytics['running_tasks'] += 1
                elif status == TaskStatus.PENDING:
                    analytics['pending_tasks'] += 1
                
                # Task distribution by status
                status_key = status.value
                analytics['task_distribution'][status_key] = analytics['task_distribution'].get(status_key, 0) + 1
                
                # Priority distribution
                priority_key = task['priority'].value
                analytics['priority_distribution'][priority_key] = analytics['priority_distribution'].get(priority_key, 0) + 1
            
            # Calculate derived metrics
            if analytics['completion_times']:
                analytics['average_completion_time'] = np.mean(analytics['completion_times'])
            
            if analytics['total_tasks'] > 0:
                analytics['success_rate'] = (analytics['completed_tasks'] / analytics['total_tasks']) * 100
                
                # Calculate throughput (tasks per hour)
                time_range_hours = (end_time - start_time).total_seconds() / 3600
                analytics['throughput'] = analytics['completed_tasks'] / time_range_hours if time_range_hours > 0 else 0
            
            self._analytics_cache['task_analytics'] = analytics
            self._cache_timestamp = datetime.now()
            
            return analytics
            
        except Exception as e:
            self.add_error(f"Error calculating task analytics: {str(e)}", e)
            return {}
    
    def calculate_progress_analytics(self) -> Dict[str, Any]:
        """
        Calculate progress-based analytics from progress trackers.
        
        Returns:
            Progress analytics dictionary
        """
        try:
            if 'progress_analytics' in self._analytics_cache and self._is_cache_valid():
                return self._analytics_cache['progress_analytics']
            
            start_time, end_time = self._get_time_filter()
            
            analytics = {
                'total_trackers': len(self.progress_trackers),
                'active_trackers': 0,
                'completed_trackers': 0,
                'average_progress': 0,
                'total_progress_points': 0,
                'progress_velocity': 0,
                'estimated_completion': None,
                'progress_over_time': []
            }
            
            all_progress_data = []
            
            # Collect data from all progress trackers
            for tracker in self.progress_trackers.values():
                if hasattr(tracker, 'progress_history'):
                    for entry in tracker.progress_history:
                        if entry['timestamp'] >= start_time and entry['timestamp'] <= end_time:
                            all_progress_data.append(entry)
                
                # Current tracker status
                if hasattr(tracker, 'is_complete') and tracker.is_complete:
                    analytics['completed_trackers'] += 1
                elif hasattr(tracker, 'current_value') and tracker.current_value > 0:
                    analytics['active_trackers'] += 1
            
            if all_progress_data:
                # Calculate progress metrics
                total_progress = sum(entry['percentage'] for entry in all_progress_data)
                analytics['average_progress'] = total_progress / len(all_progress_data)
                analytics['total_progress_points'] = len(all_progress_data)
                
                # Calculate progress velocity (percentage points per hour)
                if len(all_progress_data) >= 2:
                    sorted_data = sorted(all_progress_data, key=lambda x: x['timestamp'])
                    first_entry = sorted_data[0]
                    last_entry = sorted_data[-1]
                    
                    time_diff_hours = (last_entry['timestamp'] - first_entry['timestamp']).total_seconds() / 3600
                    progress_diff = last_entry['percentage'] - first_entry['percentage']
                    
                    if time_diff_hours > 0:
                        analytics['progress_velocity'] = progress_diff / time_diff_hours
            
            self._analytics_cache['progress_analytics'] = analytics
            self._cache_timestamp = datetime.now()
            
            return analytics
            
        except Exception as e:
            self.add_error(f"Error calculating progress analytics: {str(e)}", e)
            return {}
    
    def render_overview_metrics(self) -> None:
        """Render high-level overview metrics."""
        try:
            task_analytics = self.calculate_task_analytics()
            progress_analytics = self.calculate_progress_analytics()
            
            st.subheader("📊 Analytics Overview")
            
            # Main metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Tasks",
                    task_analytics.get('total_tasks', 0)
                )
            
            with col2:
                success_rate = task_analytics.get('success_rate', 0)
                st.metric(
                    "Success Rate",
                    f"{success_rate:.1f}%"
                )
            
            with col3:
                avg_progress = progress_analytics.get('average_progress', 0)
                st.metric(
                    "Avg Progress",
                    f"{avg_progress:.1f}%"
                )
            
            with col4:
                throughput = task_analytics.get('throughput', 0)
                st.metric(
                    "Throughput",
                    f"{throughput:.1f}/hr"
                )
            
            # Secondary metrics
            col5, col6, col7, col8 = st.columns(4)
            
            with col5:
                completed = task_analytics.get('completed_tasks', 0)
                st.metric("Completed", completed)
            
            with col6:
                running = task_analytics.get('running_tasks', 0)
                st.metric("Running", running)
            
            with col7:
                failed = task_analytics.get('failed_tasks', 0)
                st.metric("Failed", failed)
            
            with col8:
                active_trackers = progress_analytics.get('active_trackers', 0)
                st.metric("Active Trackers", active_trackers)
            
        except Exception as e:
            self.add_error(f"Error rendering overview metrics: {str(e)}", e)
    
    def render_task_distribution_chart(self) -> None:
        """Render task distribution pie chart."""
        try:
            task_analytics = self.calculate_task_analytics()
            distribution = task_analytics.get('task_distribution', {})
            
            if not distribution:
                st.info("No task distribution data available")
                return
            
            # Create pie chart
            fig = go.Figure(data=[go.Pie(
                labels=list(distribution.keys()),
                values=list(distribution.values()),
                hole=0.3,
                textinfo='label+percent',
                textposition='outside'
            )])
            
            fig.update_layout(
                title="Task Status Distribution",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            self.add_error(f"Error rendering task distribution chart: {str(e)}", e)
    
    def render_completion_time_chart(self) -> None:
        """Render task completion time analysis."""
        try:
            task_analytics = self.calculate_task_analytics()
            completion_times = task_analytics.get('completion_times', [])
            
            if not completion_times:
                st.info("No completion time data available")
                return
            
            # Convert to minutes for better readability
            completion_times_min = [t / 60 for t in completion_times]
            
            # Create histogram
            fig = go.Figure(data=[go.Histogram(
                x=completion_times_min,
                nbinsx=20,
                name="Completion Times"
            )])
            
            fig.update_layout(
                title="Task Completion Time Distribution",
                xaxis_title="Completion Time (minutes)",
                yaxis_title="Number of Tasks",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary statistics
            if completion_times_min:
                avg_time = np.mean(completion_times_min)
                median_time = np.median(completion_times_min)
                std_time = np.std(completion_times_min)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Avg Time", f"{avg_time:.1f} min")
                with col2:
                    st.metric("Median Time", f"{median_time:.1f} min")
                with col3:
                    st.metric("Std Dev", f"{std_time:.1f} min")
            
        except Exception as e:
            self.add_error(f"Error rendering completion time chart: {str(e)}", e)
    
    def render_progress_trends(self) -> None:
        """Render progress trends over time."""
        try:
            # Collect progress data from all trackers
            all_progress_data = []
            
            for source_id, tracker in self.progress_trackers.items():
                if hasattr(tracker, 'progress_history'):
                    for entry in tracker.progress_history:
                        all_progress_data.append({
                            'timestamp': entry['timestamp'],
                            'percentage': entry['percentage'],
                            'source': source_id
                        })
            
            if not all_progress_data:
                st.info("No progress trend data available")
                return
            
            # Create DataFrame
            df = pd.DataFrame(all_progress_data)
            df = df.sort_values('timestamp')
            
            # Create line chart
            fig = px.line(
                df,
                x='timestamp',
                y='percentage',
                color='source',
                title="Progress Trends Over Time"
            )
            
            fig.update_layout(
                xaxis_title="Time",
                yaxis_title="Progress (%)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            self.add_error(f"Error rendering progress trends: {str(e)}", e)
    
    def render_custom_metrics(self) -> None:
        """Render custom metrics dashboard."""
        try:
            if not self.custom_metrics:
                st.info("No custom metrics available")
                return
            
            st.subheader("Custom Metrics")
            
            for metric_id, metric_history in self.custom_metrics.items():
                if not metric_history:
                    continue
                
                latest_metric = metric_history[-1]
                
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.metric(
                        latest_metric['name'],
                        f"{latest_metric['value']:.2f} {latest_metric['unit']}"
                    )
                    if latest_metric['description']:
                        st.caption(latest_metric['description'])
                
                with col2:
                    if len(metric_history) > 1:
                        # Create trend chart
                        timestamps = [m['timestamp'] for m in metric_history]
                        values = [m['value'] for m in metric_history]
                        
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=timestamps,
                            y=values,
                            mode='lines+markers',
                            name=latest_metric['name']
                        ))
                        
                        fig.update_layout(
                            title=f"{latest_metric['name']} Trend",
                            height=200,
                            margin=dict(l=0, r=0, t=30, b=0)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            self.add_error(f"Error rendering custom metrics: {str(e)}", e)
    
    def render_time_range_selector(self) -> None:
        """Render time range selection interface."""
        try:
            st.subheader("⏰ Time Range")
            
            time_options = {
                TimeRange.LAST_HOUR.value: "Last Hour",
                TimeRange.LAST_DAY.value: "Last Day",
                TimeRange.LAST_WEEK.value: "Last Week",
                TimeRange.LAST_MONTH.value: "Last Month",
                TimeRange.ALL_TIME.value: "All Time",
                TimeRange.CUSTOM.value: "Custom Range"
            }
            
            selected_range = st.selectbox(
                "Select Time Range",
                list(time_options.keys()),
                format_func=lambda x: time_options[x],
                index=list(time_options.keys()).index(self.time_range.value),
                key=self.get_key("time_range")
            )
            
            self.time_range = TimeRange(selected_range)
            
            # Custom range inputs
            if self.time_range == TimeRange.CUSTOM:
                col1, col2 = st.columns(2)
                
                with col1:
                    self.custom_start_date = st.datetime_input(
                        "Start Date",
                        value=datetime.now() - timedelta(days=7),
                        key=self.get_key("start_date")
                    )
                
                with col2:
                    self.custom_end_date = st.datetime_input(
                        "End Date",
                        value=datetime.now(),
                        key=self.get_key("end_date")
                    )
            
            # Clear cache when time range changes
            self._clear_cache()
            
        except Exception as e:
            self.add_error(f"Error rendering time range selector: {str(e)}", e)
    
    def render(self, 
               dashboard_type: str = "overview",
               auto_refresh: bool = True) -> Any:
        """
        Render the analytics dashboard component.
        
        Args:
            dashboard_type: Type of dashboard ("overview", "tasks", "progress", "custom")
            auto_refresh: Whether to enable auto-refresh
            
        Returns:
            Analytics data
        """
        try:
            # Time range selector
            self.render_time_range_selector()
            
            # Auto-refresh button
            if auto_refresh and st.button("🔄 Refresh", key=self.get_key("refresh")):
                self._clear_cache()
                st.rerun()
            
            # Dashboard type selector
            dashboard_options = {
                "overview": "📊 Overview",
                "tasks": "📋 Task Analytics",
                "progress": "📈 Progress Analytics",
                "custom": "🎯 Custom Metrics"
            }
            
            selected_dashboard = st.selectbox(
                "Dashboard View",
                list(dashboard_options.keys()),
                format_func=lambda x: dashboard_options[x],
                index=list(dashboard_options.keys()).index(dashboard_type),
                key=self.get_key("dashboard_type")
            )
            
            # Render selected dashboard
            if selected_dashboard == "overview":
                self.render_overview_metrics()
                
                col1, col2 = st.columns(2)
                with col1:
                    self.render_task_distribution_chart()
                with col2:
                    self.render_completion_time_chart()
                    
            elif selected_dashboard == "tasks":
                task_analytics = self.calculate_task_analytics()
                self.render_task_distribution_chart()
                self.render_completion_time_chart()
                
                # Task analytics table
                if task_analytics:
                    st.subheader("Task Analytics Summary")
                    st.json(task_analytics)
                    
            elif selected_dashboard == "progress":
                progress_analytics = self.calculate_progress_analytics()
                self.render_progress_trends()
                
                # Progress analytics summary
                if progress_analytics:
                    st.subheader("Progress Analytics Summary")
                    st.json(progress_analytics)
                    
            elif selected_dashboard == "custom":
                self.render_custom_metrics()
            
            # Display any messages
            self.display_messages()
            
            return {
                'task_analytics': self.calculate_task_analytics(),
                'progress_analytics': self.calculate_progress_analytics(),
                'custom_metrics_count': len(self.custom_metrics),
                'data_sources': {
                    'progress_trackers': len(self.progress_trackers),
                    'status_trackers': len(self.status_trackers)
                }
            }
            
        except Exception as e:
            self.add_error(f"Error rendering analytics dashboard: {str(e)}", e)
            self.display_messages()
            return {}
    
    def export_analytics_data(self) -> Dict[str, Any]:
        """
        Export all analytics data.
        
        Returns:
            Complete analytics data
        """
        try:
            return {
                'task_analytics': self.calculate_task_analytics(),
                'progress_analytics': self.calculate_progress_analytics(),
                'custom_metrics': {
                    metric_id: [
                        {
                            **metric,
                            'timestamp': metric['timestamp'].isoformat()
                        }
                        for metric in metric_history
                    ]
                    for metric_id, metric_history in self.custom_metrics.items()
                },
                'data_sources': {
                    'progress_trackers': list(self.progress_trackers.keys()),
                    'status_trackers': list(self.status_trackers.keys())
                },
                'configuration': {
                    'time_range': self.time_range.value,
                    'custom_start_date': self.custom_start_date.isoformat() if self.custom_start_date else None,
                    'custom_end_date': self.custom_end_date.isoformat() if self.custom_end_date else None,
                    'refresh_interval': self.refresh_interval
                }
            }
            
        except Exception as e:
            self.add_error(f"Error exporting analytics data: {str(e)}", e)
            return {}