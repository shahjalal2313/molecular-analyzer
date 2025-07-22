"""
Progress Bar Component for Molecular Analysis Workflows

Provides customizable progress bars for tracking analysis progress.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from datetime import datetime, timedelta
import time

from ..base import BaseComponent


class ProgressStyle(Enum):
    """Available progress bar styles."""
    DEFAULT = "default"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    CUSTOM = "custom"


class ProgressAnimation(Enum):
    """Progress bar animation types."""
    NONE = "none"
    SMOOTH = "smooth"
    PULSE = "pulse"
    STRIPED = "striped"


class ProgressBarComponent(BaseComponent):
    """
    Customizable progress bar component for molecular analysis workflows.
    
    Features:
    - Multiple visual styles (success, warning, error, info, custom)
    - Animation support (smooth, pulse, striped)
    - Time estimation and ETA display
    - Customizable colors and themes
    - Sub-progress tracking for complex workflows
    - Progress history and analytics
    - Export and sharing capabilities
    """
    
    def __init__(self, name: str = "Progress Bar", key_prefix: str = None):
        """
        Initialize the progress bar component.
        
        Args:
            name: Component display name
            key_prefix: Unique key prefix for Streamlit widgets
        """
        super().__init__(name, key_prefix)
        
        # Progress state
        self.current_value = 0.0
        self.max_value = 100.0
        self.start_time = None
        self.end_time = None
        self.is_complete = False
        self.is_indeterminate = False
        
        # Visual configuration
        self.style = ProgressStyle.DEFAULT
        self.animation = ProgressAnimation.NONE
        self.show_percentage = True
        self.show_eta = True
        self.show_elapsed = True
        self.custom_colors = {
            'progress': '#1f77b4',
            'background': '#f0f0f0',
            'text': '#333333'
        }
        
        # Sub-progress tracking
        self.sub_progress = {}
        self.progress_history = []
        
        # Style configurations
        self.style_configs = {
            ProgressStyle.DEFAULT: {
                'progress_color': '#1f77b4',
                'background_color': '#f0f0f0',
                'text_color': '#333333'
            },
            ProgressStyle.SUCCESS: {
                'progress_color': '#28a745',
                'background_color': '#d4edda',
                'text_color': '#155724'
            },
            ProgressStyle.WARNING: {
                'progress_color': '#ffc107',
                'background_color': '#fff3cd',
                'text_color': '#856404'
            },
            ProgressStyle.ERROR: {
                'progress_color': '#dc3545',
                'background_color': '#f8d7da',
                'text_color': '#721c24'
            },
            ProgressStyle.INFO: {
                'progress_color': '#17a2b8',
                'background_color': '#d1ecf1',
                'text_color': '#0c5460'
            }
        }
    
    def start_progress(self, max_value: float = 100.0, initial_value: float = 0.0) -> None:
        """
        Start a new progress tracking session.
        
        Args:
            max_value: Maximum progress value
            initial_value: Initial progress value
        """
        self.max_value = max_value
        self.current_value = initial_value
        self.start_time = datetime.now()
        self.end_time = None
        self.is_complete = False
        self.is_indeterminate = False
        self.progress_history = [{
            'timestamp': self.start_time,
            'value': initial_value,
            'percentage': (initial_value / max_value) * 100 if max_value > 0 else 0
        }]
        
        self.log_interaction("progress_started", {
            'max_value': max_value,
            'initial_value': initial_value
        })
    
    def update_progress(self, value: float, message: str = None) -> None:
        """
        Update the progress value.
        
        Args:
            value: New progress value
            message: Optional progress message
        """
        try:
            if self.start_time is None:
                self.start_progress()
            
            # Clamp value to valid range
            self.current_value = max(0, min(value, self.max_value))
            
            # Record progress history
            progress_entry = {
                'timestamp': datetime.now(),
                'value': self.current_value,
                'percentage': (self.current_value / self.max_value) * 100 if self.max_value > 0 else 0,
                'message': message
            }
            self.progress_history.append(progress_entry)
            
            # Check if complete
            if self.current_value >= self.max_value:
                self.complete_progress()
            
            self.log_interaction("progress_updated", {
                'value': value,
                'percentage': progress_entry['percentage'],
                'message': message
            })
            
        except Exception as e:
            self.add_error(f"Error updating progress: {str(e)}", e)
    
    def complete_progress(self) -> None:
        """Mark progress as complete."""
        self.is_complete = True
        self.end_time = datetime.now()
        self.current_value = self.max_value
        
        self.log_interaction("progress_completed", {
            'total_time': str(self.end_time - self.start_time) if self.start_time else None
        })
    
    def set_indeterminate(self, indeterminate: bool = True) -> None:
        """
        Set progress bar to indeterminate mode.
        
        Args:
            indeterminate: Whether to enable indeterminate mode
        """
        self.is_indeterminate = indeterminate
    
    def set_style(self, style: ProgressStyle, custom_colors: Dict[str, str] = None) -> None:
        """
        Set the visual style of the progress bar.
        
        Args:
            style: Progress bar style
            custom_colors: Custom color configuration for CUSTOM style
        """
        self.style = style
        
        if style == ProgressStyle.CUSTOM and custom_colors:
            self.custom_colors.update(custom_colors)
    
    def set_animation(self, animation: ProgressAnimation) -> None:
        """
        Set progress bar animation.
        
        Args:
            animation: Animation type
        """
        self.animation = animation
    
    def add_sub_progress(self, name: str, value: float, max_value: float = 100.0) -> None:
        """
        Add or update a sub-progress item.
        
        Args:
            name: Sub-progress name
            value: Current value
            max_value: Maximum value
        """
        self.sub_progress[name] = {
            'value': value,
            'max_value': max_value,
            'percentage': (value / max_value) * 100 if max_value > 0 else 0
        }
    
    def remove_sub_progress(self, name: str) -> None:
        """
        Remove a sub-progress item.
        
        Args:
            name: Sub-progress name to remove
        """
        if name in self.sub_progress:
            del self.sub_progress[name]
    
    def get_eta(self) -> Optional[datetime]:
        """
        Calculate estimated time of arrival based on current progress.
        
        Returns:
            Estimated completion time or None if cannot be calculated
        """
        try:
            if (self.start_time is None or 
                self.current_value <= 0 or 
                self.current_value >= self.max_value or
                len(self.progress_history) < 2):
                return None
            
            # Use recent progress for better estimation
            recent_entries = self.progress_history[-5:]  # Last 5 entries
            if len(recent_entries) < 2:
                return None
            
            # Calculate average progress rate
            time_diff = (recent_entries[-1]['timestamp'] - recent_entries[0]['timestamp']).total_seconds()
            value_diff = recent_entries[-1]['value'] - recent_entries[0]['value']
            
            if time_diff <= 0 or value_diff <= 0:
                return None
            
            progress_rate = value_diff / time_diff  # units per second
            remaining_value = self.max_value - self.current_value
            estimated_seconds = remaining_value / progress_rate
            
            return datetime.now() + timedelta(seconds=estimated_seconds)
            
        except Exception as e:
            self.add_error(f"Error calculating ETA: {str(e)}", e)
            return None
    
    def get_elapsed_time(self) -> Optional[timedelta]:
        """
        Get elapsed time since progress started.
        
        Returns:
            Elapsed time or None if not started
        """
        if self.start_time is None:
            return None
        
        end_time = self.end_time if self.is_complete else datetime.now()
        return end_time - self.start_time
    
    def get_progress_percentage(self) -> float:
        """
        Get current progress as percentage.
        
        Returns:
            Progress percentage (0-100)
        """
        if self.max_value <= 0:
            return 0.0
        return (self.current_value / self.max_value) * 100
    
    def create_plotly_progress_bar(self) -> go.Figure:
        """
        Create a Plotly progress bar chart.
        
        Returns:
            Plotly figure
        """
        try:
            # Get style colors
            if self.style == ProgressStyle.CUSTOM:
                colors = self.custom_colors
            else:
                colors = self.style_configs.get(self.style, self.style_configs[ProgressStyle.DEFAULT])
            
            percentage = self.get_progress_percentage()
            
            # Create progress bar data
            fig = go.Figure()
            
            # Background bar
            fig.add_trace(go.Bar(
                x=[100],
                y=['Progress'],
                orientation='h',
                marker_color=colors['background_color'],
                name='Background',
                showlegend=False,
                hoverinfo='skip'
            ))
            
            # Progress bar
            fig.add_trace(go.Bar(
                x=[percentage],
                y=['Progress'],
                orientation='h',
                marker_color=colors['progress_color'],
                name='Progress',
                showlegend=False,
                text=f"{percentage:.1f}%" if self.show_percentage else "",
                textposition='inside',
                textfont_color=colors['text_color']
            ))
            
            # Update layout
            fig.update_layout(
                barmode='overlay',
                xaxis=dict(
                    range=[0, 100],
                    showgrid=False,
                    showticklabels=False,
                    zeroline=False
                ),
                yaxis=dict(
                    showgrid=False,
                    showticklabels=False,
                    zeroline=False
                ),
                margin=dict(l=0, r=0, t=20, b=0),
                height=60,
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            return fig
            
        except Exception as e:
            self.add_error(f"Error creating Plotly progress bar: {str(e)}", e)
            return go.Figure()
    
    def render_basic_progress(self) -> None:
        """Render basic Streamlit progress bar."""
        try:
            percentage = self.get_progress_percentage()
            
            if self.is_indeterminate:
                st.progress(0)
                st.caption("Processing...")
            else:
                st.progress(percentage / 100)
                
                if self.show_percentage:
                    st.caption(f"Progress: {percentage:.1f}%")
            
        except Exception as e:
            self.add_error(f"Error rendering basic progress: {str(e)}", e)
    
    def render_advanced_progress(self) -> None:
        """Render advanced progress bar with Plotly."""
        try:
            # Main progress bar
            fig = self.create_plotly_progress_bar()
            st.plotly_chart(fig, use_container_width=True)
            
            # Progress info
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if self.show_percentage:
                    percentage = self.get_progress_percentage()
                    st.metric("Progress", f"{percentage:.1f}%")
            
            with col2:
                if self.show_elapsed:
                    elapsed = self.get_elapsed_time()
                    if elapsed:
                        st.metric("Elapsed", str(elapsed).split('.')[0])
            
            with col3:
                if self.show_eta and not self.is_complete:
                    eta = self.get_eta()
                    if eta:
                        st.metric("ETA", eta.strftime("%H:%M:%S"))
            
            # Sub-progress bars
            if self.sub_progress:
                st.subheader("Sub-Tasks")
                for name, progress in self.sub_progress.items():
                    st.write(f"**{name}**")
                    sub_percentage = progress['percentage']
                    st.progress(sub_percentage / 100)
                    st.caption(f"{sub_percentage:.1f}% ({progress['value']}/{progress['max_value']})")
            
        except Exception as e:
            self.add_error(f"Error rendering advanced progress: {str(e)}", e)
    
    def render_progress_history(self) -> None:
        """Render progress history chart."""
        try:
            if len(self.progress_history) < 2:
                st.info("Not enough progress data to show history")
                return
            
            # Create progress over time chart
            timestamps = [entry['timestamp'] for entry in self.progress_history]
            percentages = [entry['percentage'] for entry in self.progress_history]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=percentages,
                mode='lines+markers',
                name='Progress',
                line=dict(color='#1f77b4', width=2),
                marker=dict(size=6)
            ))
            
            fig.update_layout(
                title="Progress Over Time",
                xaxis_title="Time",
                yaxis_title="Progress (%)",
                yaxis=dict(range=[0, 100]),
                height=300
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            self.add_error(f"Error rendering progress history: {str(e)}", e)
    
    def render(self, 
               progress_type: str = "advanced",
               show_history: bool = False) -> Any:
        """
        Render the progress bar component.
        
        Args:
            progress_type: Type of progress bar ("basic" or "advanced")
            show_history: Whether to show progress history
            
        Returns:
            Current progress percentage
        """
        try:
            # Progress bar
            if progress_type == "basic":
                self.render_basic_progress()
            else:
                self.render_advanced_progress()
            
            # Progress history
            if show_history:
                with st.expander("Progress History"):
                    self.render_progress_history()
            
            # Status indicators
            if self.is_complete:
                st.success("✅ Complete!")
            elif self.is_indeterminate:
                st.info("🔄 Processing...")
            
            # Display any messages
            self.display_messages()
            
            return self.get_progress_percentage()
            
        except Exception as e:
            self.add_error(f"Error rendering progress bar: {str(e)}", e)
            self.display_messages()
            return 0.0
    
    def export_progress_data(self) -> Dict[str, Any]:
        """
        Export progress data for analysis or saving.
        
        Returns:
            Progress data dictionary
        """
        return {
            "current_value": self.current_value,
            "max_value": self.max_value,
            "percentage": self.get_progress_percentage(),
            "is_complete": self.is_complete,
            "is_indeterminate": self.is_indeterminate,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "elapsed_time": str(self.get_elapsed_time()) if self.get_elapsed_time() else None,
            "eta": self.get_eta().isoformat() if self.get_eta() else None,
            "style": self.style.value,
            "animation": self.animation.value,
            "sub_progress": self.sub_progress,
            "progress_history": [
                {
                    "timestamp": entry["timestamp"].isoformat(),
                    "value": entry["value"],
                    "percentage": entry["percentage"],
                    "message": entry.get("message")
                }
                for entry in self.progress_history
            ]
        }