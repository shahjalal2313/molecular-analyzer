import streamlit as st
from typing import List, Dict, Any
from datetime import datetime

class OperationHistoryComponent:
    def __init__(self):
        if "operation_history" not in st.session_state:
            st.session_state.operation_history = []

    def add_entry(self, operation_type: str, details: Dict[str, Any]):
        # Ensure session state is initialized
        if "operation_history" not in st.session_state:
            st.session_state.operation_history = []
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "operation_type": operation_type,
            "details": details
        }
        st.session_state.operation_history.insert(0, entry) # Add to the beginning
        # Keep history to a reasonable length
        if len(st.session_state.operation_history) > 50:
            st.session_state.operation_history = st.session_state.operation_history[:50]

    def render(self):
        st.subheader("Operation History")
        # Ensure session state is initialized
        if "operation_history" not in st.session_state:
            st.session_state.operation_history = []
            
        if st.session_state.operation_history:
            for entry in st.session_state.operation_history:
                st.markdown(f"**{entry['timestamp']} - {entry['operation_type']}**")
                for key, value in entry['details'].items():
                    st.write(f"- {key}: {value}")
                st.markdown("---")
        else:
            st.info("No operations recorded yet.")

    def clear_history(self):
        st.session_state.operation_history = []
