import streamlit as st
import plotly.graph_objects as go

class RadarChartComponent:
    def __init__(self):
        pass

    def create_chart(self, data: dict, custom_config: dict = None):
        """Creates an interactive radar chart.

        Args:
            data (dict): A dictionary where keys are categories and values are numerical scores.
                         Example: {'Property A': 0.8, 'Property B': 0.6, 'Property C': 0.9}
            custom_config (dict, optional): Custom Plotly configuration options.

        Returns:
            plotly.graph_objects.Figure: A Plotly Figure object.
        """
        if not data:
            st.warning("No data provided for radar chart.")
            return None

        categories = list(data.keys())
        values = list(data.values())

        fig = go.Figure(
            data=go.Scatterpolar(r=values, theta=categories, fill='toself'),
            layout=go.Layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1]  # Assuming values are normalized between 0 and 1
                    )
                ),
                showlegend=False,
                title=custom_config.get('title', 'Molecular Property Radar Chart') if custom_config else 'Molecular Property Radar Chart'
            )
        )
        return fig
