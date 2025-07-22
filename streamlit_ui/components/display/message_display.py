"""
Message Display Components for Molecular Analyzer

This module contains reusable components for displaying user feedback messages.
"""

import streamlit as st
from typing import Optional, Dict, Any, List

from ..base import BaseComponent


class MessageDisplayComponent(BaseComponent):
    """
    Component for displaying various types of user feedback messages.
    
    Features:
    - Success, error, warning, and info message types
    - Consistent styling and behavior
    - Auto-dismiss functionality
    - Message queuing and management
    - Detailed error information
    """
    
    def __init__(self, name: str = "Message Display", key_prefix: str = None):
        """
        Initialize the message display component.
        
        Args:
            name: Component display name
            key_prefix: Unique key prefix for Streamlit widgets
        """
        super().__init__(name, key_prefix)
        self.message_queue: List[Dict[str, Any]] = []
    
    def show_success(self, message: str, icon: str = "✅", auto_dismiss: bool = False) -> None:
        """
        Display a success message with custom styling.
        
        Args:
            message: Success message text
            icon: Icon to display with message
            auto_dismiss: Whether to auto-dismiss the message
        """
        try:
            st.markdown(f"<div class=\"success-box\">{icon} {message}</div>", unsafe_allow_html=True)
            
            self.log_interaction('success_message_displayed', {
                'message': message,
                'icon': icon,
                'auto_dismiss': auto_dismiss
            })
            
        except Exception as e:
            self.add_error(f"Error displaying success message: {str(e)}", e)
    
    def show_error(self, message: str, icon: str = "❌", 
                   show_details: bool = False, error_details: str = None) -> None:
        """
        Display an error message with custom styling.
        
        Args:
            message: Error message text
            icon: Icon to display with message
            show_details: Whether to show detailed error information
            error_details: Detailed error information
        """
        try:
            st.markdown(f"<div class=\"error-box\">{icon} {message}</div>", unsafe_allow_html=True)
            
            # Show detailed error information if requested
            if show_details and error_details:
                with st.expander("Error Details", expanded=False):
                    st.code(error_details, language="text")
            
            self.log_interaction('error_message_displayed', {
                'message': message,
                'icon': icon,
                'has_details': bool(error_details)
            })
            
        except Exception as e:
            print(f"Error displaying error message: {str(e)}")
    
    def show_warning(self, message: str, icon: str = "⚠️",
                    suggested_action: str = None) -> None:
        """
        Display a warning message with custom styling.
        
        Args:
            message: Warning message text
            icon: Icon to display with message
            suggested_action: Suggested action to resolve the warning
        """
        try:
            st.markdown(f"<div class=\"warning-box\">{icon} {message}</div>", unsafe_allow_html=True)
            
            # Show suggested action if provided
            if suggested_action:
                st.info(f"💡 **Suggestion:** {suggested_action}")
            
            self.log_interaction('warning_message_displayed', {
                'message': message,
                'icon': icon,
                'has_suggestion': bool(suggested_action)
            })
            
        except Exception as e:
            self.add_error(f"Error displaying warning message: {str(e)}", e)
    
    def show_info(self, message: str, icon: str = "ℹ️",
                  collapsible: bool = False, title: str = None) -> None:
        """
        Display an informational message.
        
        Args:
            message: Info message text
            icon: Icon to display with message
            collapsible: Whether to display in an expandable section
            title: Title for collapsible section
        """
        try:
            if collapsible:
                section_title = f"{icon} {title or 'Information'}"
                with st.expander(section_title, expanded=False):
                    st.markdown(message)
            else:
                st.info(f"{icon} {message}" if icon else message)
            
            self.log_interaction('info_message_displayed', {
                'message': message,
                'icon': icon,
                'collapsible': collapsible
            })
            
        except Exception as e:
            self.add_error(f"Error displaying info message: {str(e)}", e)
    
    def show_analysis_success(self, analysis_type: str = "", molecule_count: int = None) -> None:
        """
        Display a success message for completed analysis.
        
        Args:
            analysis_type: Type of analysis completed
            molecule_count: Number of molecules analyzed
        """
        try:
            if analysis_type and molecule_count:
                message = f"{analysis_type} completed successfully for {molecule_count} molecule(s)!"
            elif analysis_type:
                message = f"{analysis_type} completed successfully!"
            else:
                message = "Analysis completed successfully!"
            
            self.show_success(message, "🎯")
            
        except Exception as e:
            self.add_error(f"Error displaying analysis success: {str(e)}", e)
    
    def show_calculation_error(self, error: Exception, context: str = "calculation") -> None:
        """
        Display an error message for calculation failures.
        
        Args:
            error: Exception that occurred
            context: Context where the error occurred
        """
        try:
            message = f"Error during {context}. Please check your input and try again."
            error_details = f"Exception: {type(error).__name__}: {str(error)}"
            
            self.show_error(
                message, 
                "🚨", 
                show_details=True, 
                error_details=error_details
            )
            
        except Exception as e:
            self.add_error(f"Error displaying calculation error: {str(e)}", e)
    
    def show_validation_error(self, validation_message: str) -> None:
        """
        Display an error message for validation failures.
        
        Args:
            validation_message: Validation error details
        """
        try:
            self.show_error(validation_message, "❌")
            
        except Exception as e:
            self.add_error(f"Error displaying validation error: {str(e)}", e)
    
    def show_insufficient_data_warning(self, required_count: int, 
                                     current_count: int,
                                     data_type: str = "properties") -> None:
        """
        Display a warning for insufficient data.
        
        Args:
            required_count: Required number of data points
            current_count: Current number of data points
            data_type: Type of data (properties, molecules, etc.)
        """
        try:
            message = f"Need at least {required_count} {data_type}. Currently have {current_count}."
            suggestion = f"Run more analysis options to get additional {data_type}."
            
            self.show_warning(message, "⚠️", suggestion)
            
        except Exception as e:
            self.add_error(f"Error displaying insufficient data warning: {str(e)}", e)
    
    def show_welcome_message(self) -> None:
        """Display a welcome message for new users."""
        try:
            message = """
            🎉 **Welcome to Molecular Analyzer!** 
            
            This tool helps you analyze molecular properties, visualize structures, and compare molecules.
            Start by entering a SMILES string or selecting an example molecule.
            """
            self.show_info(message, "🎉", collapsible=True, title="Welcome!")
            
        except Exception as e:
            self.add_error(f"Error displaying welcome message: {str(e)}", e)
    
    def show_interpretation_guide(self, chart_type: str, 
                                interpretation_points: List[str]) -> None:
        """
        Display an interpretation guide for charts and visualizations.
        
        Args:
            chart_type: Type of chart or visualization
            interpretation_points: List of interpretation points
        """
        try:
            points_text = "\n".join([f"- {point}" for point in interpretation_points])
            message = f"**{chart_type} Interpretation:**\n{points_text}"
            
            self.show_info(
                message,
                "📊",
                collapsible=True,
                title=f"{chart_type} Interpretation"
            )
            
        except Exception as e:
            self.add_error(f"Error displaying interpretation guide: {str(e)}", e)
    
    def queue_message(self, message_type: str, message: str, 
                     priority: int = 0, **kwargs) -> None:
        """
        Add a message to the display queue.
        
        Args:
            message_type: Type of message ('success', 'error', 'warning', 'info')
            message: Message text
            priority: Message priority (higher = more important)
            **kwargs: Additional message parameters
        """
        try:
            message_data = {
                'type': message_type,
                'message': message,
                'priority': priority,
                'kwargs': kwargs
            }
            
            # Insert based on priority (higher priority first)
            insert_index = 0
            for i, msg in enumerate(self.message_queue):
                if msg['priority'] < priority:
                    insert_index = i
                    break
                insert_index = i + 1
            
            self.message_queue.insert(insert_index, message_data)
            
            # Limit queue size
            if len(self.message_queue) > 10:
                self.message_queue = self.message_queue[:10]
                
        except Exception as e:
            self.add_error(f"Error queueing message: {str(e)}", e)
    
    def display_queued_messages(self) -> int:
        """
        Display all queued messages.
        
        Returns:
            Number of messages displayed
        """
        try:
            displayed_count = 0
            
            for message_data in self.message_queue:
                message_type = message_data['type']
                message = message_data['message']
                kwargs = message_data.get('kwargs', {})
                
                if message_type == 'success':
                    self.show_success(message, **kwargs)
                elif message_type == 'error':
                    self.show_error(message, **kwargs)
                elif message_type == 'warning':
                    self.show_warning(message, **kwargs)
                elif message_type == 'info':
                    self.show_info(message, **kwargs)
                
                displayed_count += 1
            
            # Clear queue after displaying
            self.message_queue.clear()
            
            return displayed_count
            
        except Exception as e:
            self.add_error(f"Error displaying queued messages: {str(e)}", e)
            return 0
    
    def clear_messages(self) -> None:
        """Clear all queued messages."""
        self.message_queue.clear()
        super().clear_messages()
    
    def get_message_count(self) -> Dict[str, int]:
        """
        Get count of messages by type.
        
        Returns:
            Dictionary with message counts
        """
        try:
            counts = {"total": len(self.message_queue)}
            
            # Count by message type
            for message_data in self.message_queue:
                msg_type = message_data['type']
                counts[msg_type] = counts.get(msg_type, 0) + 1
            
            return counts
            
        except Exception as e:
            self.add_error(f"Error getting message count: {str(e)}", e)
            return {"total": 0}
    
    def render(self, auto_display_queue: bool = True) -> bool:
        """
        Render the message display component.
        
        Args:
            auto_display_queue: Whether to automatically display queued messages
            
        Returns:
            True if any messages were displayed
        """
        try:
            self.clear_messages()
            
            displayed_count = 0
            
            # Display queued messages if requested
            if auto_display_queue:
                displayed_count = self.display_queued_messages()
            
            # Display any component errors
            if self.has_errors():
                self.display_messages()
            
            return displayed_count > 0
            
        except Exception as e:
            print(f"Error rendering message display: {str(e)}")
            return False