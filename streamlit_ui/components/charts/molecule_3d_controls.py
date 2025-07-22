"""
3D Molecular Visualization Controls Component

Provides interactive controls for 3D molecular visualization including
camera positioning, zoom, rotation, and advanced display options.
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Callable
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base import BaseComponent


class Molecule3DControlsComponent(BaseComponent):
    """
    Interactive controls for 3D molecular visualization.
    
    Features:
    - Camera position controls (eye position, center, up vector)
    - Zoom and rotation controls
    - Preset viewing angles (front, side, top, isometric)
    - Animation controls for molecular rotation
    - Export and screenshot functionality
    - Display mode toggles
    """
    
    def __init__(self, name: str = "3D Molecule Controls", key_prefix: str = None):
        """
        Initialize the 3D controls component.
        
        Args:
            name: Component display name
            key_prefix: Unique key prefix for Streamlit widgets
        """
        super().__init__(name, key_prefix)
        
        # Default camera settings
        self.camera_settings = {
            'eye': {'x': 1.5, 'y': 1.5, 'z': 1.5},
            'center': {'x': 0, 'y': 0, 'z': 0},
            'up': {'x': 0, 'y': 0, 'z': 1},
            'projection': 'perspective'  # or 'orthographic'
        }
        
        # Preset viewing angles
        self.view_presets = {
            'Default': {'eye': {'x': 1.5, 'y': 1.5, 'z': 1.5}},
            'Front': {'eye': {'x': 0, 'y': -2, 'z': 0}},
            'Side': {'eye': {'x': -2, 'y': 0, 'z': 0}},
            'Top': {'eye': {'x': 0, 'y': 0, 'z': 2}},
            'Isometric': {'eye': {'x': 1.2, 'y': 1.2, 'z': 1.2}},
            'Close-up': {'eye': {'x': 0.8, 'y': 0.8, 'z': 0.8}},
            'Far': {'eye': {'x': 3, 'y': 3, 'z': 3}}
        }
        
        # Animation settings
        self.animation_settings = {
            'auto_rotate': False,
            'rotation_speed': 1.0,
            'rotation_axis': 'z',
            'rotation_angle': 0.0
        }
        
        # Display settings
        self.display_settings = {
            'show_axes': True,
            'show_grid': False,
            'show_bounding_box': False,
            'transparent_background': False,
            'lighting': 'auto'
        }
        
        # Export settings
        self.export_settings = {
            'format': 'png',
            'resolution': 'high',
            'width': 800,
            'height': 600,
            'scale': 2
        }
    
    def get_camera_settings(self) -> Dict[str, Any]:
        """
        Get current camera settings.
        
        Returns:
            Dictionary containing camera configuration
        """
        return self.camera_settings.copy()
    
    def set_camera_position(self, 
                           eye: Dict[str, float] = None,
                           center: Dict[str, float] = None,
                           up: Dict[str, float] = None,
                           projection: str = None) -> None:
        """
        Set camera position and orientation.
        
        Args:
            eye: Eye position (x, y, z)
            center: Center point (x, y, z)
            up: Up vector (x, y, z)
            projection: Projection type ('perspective' or 'orthographic')
        """
        if eye:
            self.camera_settings['eye'].update(eye)
        if center:
            self.camera_settings['center'].update(center)
        if up:
            self.camera_settings['up'].update(up)
        if projection:
            self.camera_settings['projection'] = projection
    
    def apply_view_preset(self, preset_name: str) -> bool:
        """
        Apply a predefined viewing angle.
        
        Args:
            preset_name: Name of the preset to apply
            
        Returns:
            True if preset was applied, False if not found
        """
        if preset_name not in self.view_presets:
            self.add_error(f"View preset '{preset_name}' not found")
            return False
        
        preset = self.view_presets[preset_name]
        self.camera_settings['eye'].update(preset['eye'])
        
        # Reset center and up to defaults for presets
        self.camera_settings['center'] = {'x': 0, 'y': 0, 'z': 0}
        self.camera_settings['up'] = {'x': 0, 'y': 0, 'z': 1}
        
        return True
    
    def calculate_rotation_matrix(self, axis: str, angle: float) -> np.ndarray:
        """
        Calculate rotation matrix for given axis and angle.
        
        Args:
            axis: Rotation axis ('x', 'y', or 'z')
            angle: Rotation angle in radians
            
        Returns:
            3x3 rotation matrix
        """
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)
        
        if axis == 'x':
            return np.array([
                [1, 0, 0],
                [0, cos_a, -sin_a],
                [0, sin_a, cos_a]
            ])
        elif axis == 'y':
            return np.array([
                [cos_a, 0, sin_a],
                [0, 1, 0],
                [-sin_a, 0, cos_a]
            ])
        elif axis == 'z':
            return np.array([
                [cos_a, -sin_a, 0],
                [sin_a, cos_a, 0],
                [0, 0, 1]
            ])
        else:
            return np.eye(3)
    
    def rotate_camera(self, axis: str, angle_degrees: float) -> None:
        """
        Rotate camera around specified axis.
        
        Args:
            axis: Rotation axis ('x', 'y', or 'z')
            angle_degrees: Rotation angle in degrees
        """
        angle_rad = np.radians(angle_degrees)
        rotation_matrix = self.calculate_rotation_matrix(axis, angle_rad)
        
        # Apply rotation to eye position
        eye_vector = np.array([
            self.camera_settings['eye']['x'],
            self.camera_settings['eye']['y'],
            self.camera_settings['eye']['z']
        ])
        
        rotated_eye = rotation_matrix @ eye_vector
        
        self.camera_settings['eye'] = {
            'x': float(rotated_eye[0]),
            'y': float(rotated_eye[1]),
            'z': float(rotated_eye[2])
        }
    
    def zoom_camera(self, factor: float) -> None:
        """
        Zoom camera in or out by scaling eye position.
        
        Args:
            factor: Zoom factor (>1 zooms out, <1 zooms in)
        """
        self.camera_settings['eye']['x'] *= factor
        self.camera_settings['eye']['y'] *= factor
        self.camera_settings['eye']['z'] *= factor
    
    def reset_camera(self) -> None:
        """Reset camera to default position."""
        self.camera_settings = {
            'eye': {'x': 1.5, 'y': 1.5, 'z': 1.5},
            'center': {'x': 0, 'y': 0, 'z': 0},
            'up': {'x': 0, 'y': 0, 'z': 1},
            'projection': 'perspective'
        }
    
    def get_export_config(self) -> Dict[str, Any]:
        """
        Get export configuration.
        
        Returns:
            Dictionary with export settings
        """
        return {
            'format': self.export_settings['format'],
            'width': self.export_settings['width'],
            'height': self.export_settings['height'],
            'scale': self.export_settings['scale']
        }
    
    def create_animation_frames(self, 
                               base_camera: Dict[str, Any],
                               axis: str = 'z',
                               num_frames: int = 36) -> List[Dict[str, Any]]:
        """
        Create animation frames for rotating visualization.
        
        Args:
            base_camera: Base camera position
            axis: Rotation axis
            num_frames: Number of animation frames
            
        Returns:
            List of camera configurations for each frame
        """
        frames = []
        angle_step = 360.0 / num_frames
        
        for i in range(num_frames):
            angle = i * angle_step
            camera = base_camera.copy()
            
            # Calculate rotated eye position
            eye_vector = np.array([
                base_camera['eye']['x'],
                base_camera['eye']['y'],
                base_camera['eye']['z']
            ])
            
            rotation_matrix = self.calculate_rotation_matrix(axis, np.radians(angle))
            rotated_eye = rotation_matrix @ eye_vector
            
            camera['eye'] = {
                'x': float(rotated_eye[0]),
                'y': float(rotated_eye[1]),
                'z': float(rotated_eye[2])
            }
            
            frames.append(camera)
        
        return frames
    
    def render_basic_controls(self) -> Dict[str, Any]:
        """
        Render basic camera controls.
        
        Returns:
            Dictionary with updated camera settings
        """
        st.subheader("Camera Controls")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.text("Eye Position")
            self.camera_settings['eye']['x'] = st.slider(
                "X Position",
                min_value=-5.0,
                max_value=5.0,
                value=self.camera_settings['eye']['x'],
                step=0.1,
                key=self.get_key('eye_x')
            )
            
            self.camera_settings['eye']['y'] = st.slider(
                "Y Position",
                min_value=-5.0,
                max_value=5.0,
                value=self.camera_settings['eye']['y'],
                step=0.1,
                key=self.get_key('eye_y')
            )
            
            self.camera_settings['eye']['z'] = st.slider(
                "Z Position",
                min_value=-5.0,
                max_value=5.0,
                value=self.camera_settings['eye']['z'],
                step=0.1,
                key=self.get_key('eye_z')
            )
        
        with col2:
            st.text("View Presets")
            selected_preset = st.selectbox(
                "Choose View",
                options=list(self.view_presets.keys()),
                key=self.get_key('preset_select')
            )
            
            if st.button("Apply Preset", key=self.get_key('apply_preset')):
                self.apply_view_preset(selected_preset)
                st.experimental_rerun()
            
            st.text("Quick Actions")
            col2a, col2b = st.columns(2)
            
            with col2a:
                if st.button("Reset Camera", key=self.get_key('reset_camera')):
                    self.reset_camera()
                    st.experimental_rerun()
            
            with col2b:
                zoom_factor = st.selectbox(
                    "Zoom",
                    options=[0.5, 0.75, 1.0, 1.25, 1.5, 2.0],
                    index=2,
                    key=self.get_key('zoom_factor')
                )
                
                if st.button("Apply Zoom", key=self.get_key('apply_zoom')):
                    current_distance = np.sqrt(
                        self.camera_settings['eye']['x']**2 +
                        self.camera_settings['eye']['y']**2 +
                        self.camera_settings['eye']['z']**2
                    )
                    target_distance = 1.5 / zoom_factor
                    scale = target_distance / current_distance
                    self.zoom_camera(scale)
                    st.experimental_rerun()
        
        return self.camera_settings
    
    def render_advanced_controls(self) -> Dict[str, Any]:
        """
        Render advanced camera and display controls.
        
        Returns:
            Dictionary with all settings
        """
        st.subheader("Advanced Controls")
        
        # Rotation controls
        st.text("Rotation Controls")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            rotation_axis = st.selectbox(
                "Rotation Axis",
                options=['x', 'y', 'z'],
                index=2,
                key=self.get_key('rotation_axis')
            )
        
        with col2:
            rotation_angle = st.slider(
                "Rotation Angle (°)",
                min_value=-180,
                max_value=180,
                value=0,
                step=15,
                key=self.get_key('rotation_angle')
            )
        
        with col3:
            if st.button("Apply Rotation", key=self.get_key('apply_rotation')):
                if rotation_angle != 0:
                    self.rotate_camera(rotation_axis, rotation_angle)
                    st.experimental_rerun()
        
        # Display settings
        st.text("Display Settings")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            self.display_settings['show_axes'] = st.checkbox(
                "Show Axes",
                value=self.display_settings['show_axes'],
                key=self.get_key('show_axes')
            )
        
        with col2:
            self.display_settings['show_grid'] = st.checkbox(
                "Show Grid",
                value=self.display_settings['show_grid'],
                key=self.get_key('show_grid')
            )
        
        with col3:
            self.camera_settings['projection'] = st.selectbox(
                "Projection",
                options=['perspective', 'orthographic'],
                index=0 if self.camera_settings['projection'] == 'perspective' else 1,
                key=self.get_key('projection')
            )
        
        # Export settings
        st.text("Export Settings")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            self.export_settings['format'] = st.selectbox(
                "Format",
                options=['png', 'jpeg', 'svg', 'pdf'],
                key=self.get_key('export_format')
            )
        
        with col2:
            self.export_settings['resolution'] = st.selectbox(
                "Resolution",
                options=['low', 'medium', 'high', 'ultra'],
                index=2,
                key=self.get_key('export_resolution')
            )
        
        with col3:
            self.export_settings['scale'] = st.slider(
                "Scale Factor",
                min_value=1,
                max_value=4,
                value=2,
                key=self.get_key('export_scale')
            )
        
        return {
            'camera': self.camera_settings,
            'display': self.display_settings,
            'export': self.export_settings
        }
    
    def render(self, 
               control_level: str = 'basic',
               show_camera_info: bool = True) -> Dict[str, Any]:
        """
        Render the 3D controls component.
        
        Args:
            control_level: Level of controls ('basic' or 'advanced')
            show_camera_info: Whether to show current camera information
            
        Returns:
            Dictionary with all current settings
        """
        try:
            self.clear_messages()
            
            # Show current camera information
            if show_camera_info:
                st.subheader("Current Camera Position")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Eye X", f"{self.camera_settings['eye']['x']:.2f}")
                    st.metric("Eye Y", f"{self.camera_settings['eye']['y']:.2f}")
                    st.metric("Eye Z", f"{self.camera_settings['eye']['z']:.2f}")
                
                with col2:
                    distance = np.sqrt(
                        self.camera_settings['eye']['x']**2 +
                        self.camera_settings['eye']['y']**2 +
                        self.camera_settings['eye']['z']**2
                    )
                    st.metric("Distance", f"{distance:.2f}")
                    st.metric("Projection", self.camera_settings['projection'])
                
                with col3:
                    # Show elevation and azimuth angles
                    x, y, z = (self.camera_settings['eye']['x'],
                              self.camera_settings['eye']['y'],
                              self.camera_settings['eye']['z'])
                    
                    elevation = np.degrees(np.arctan2(z, np.sqrt(x**2 + y**2)))
                    azimuth = np.degrees(np.arctan2(y, x))
                    
                    st.metric("Elevation", f"{elevation:.1f}°")
                    st.metric("Azimuth", f"{azimuth:.1f}°")
            
            # Render controls based on level
            if control_level == 'basic':
                settings = {'camera': self.render_basic_controls()}
            else:
                settings = self.render_advanced_controls()
            
            # Log interaction
            self.log_interaction('controls_rendered', {
                'control_level': control_level,
                'camera_position': self.camera_settings['eye'],
                'projection': self.camera_settings['projection']
            })
            
            return settings
            
        except Exception as e:
            self.add_error(f"Error rendering 3D controls: {str(e)}", e)
            self.display_messages()
            return {
                'camera': self.camera_settings,
                'display': self.display_settings,
                'export': self.export_settings
            }
    
    def get_plotly_camera_config(self) -> Dict[str, Any]:
        """
        Get camera configuration formatted for Plotly.
        
        Returns:
            Dictionary with Plotly-compatible camera configuration
        """
        return {
            'eye': self.camera_settings['eye'],
            'center': self.camera_settings['center'],
            'up': self.camera_settings['up'],
            'projection': {'type': self.camera_settings['projection']}
        }
    
    def get_plotly_scene_config(self) -> Dict[str, Any]:
        """
        Get scene configuration for Plotly based on display settings.
        
        Returns:
            Dictionary with Plotly-compatible scene configuration
        """
        scene_config = {
            'camera': self.get_plotly_camera_config()
        }
        
        if not self.display_settings['show_axes']:
            scene_config.update({
                'xaxis': {'visible': False},
                'yaxis': {'visible': False},
                'zaxis': {'visible': False}
            })
        
        if self.display_settings['show_grid']:
            scene_config.update({
                'xaxis': {'showgrid': True, 'gridcolor': 'lightgray'},
                'yaxis': {'showgrid': True, 'gridcolor': 'lightgray'},
                'zaxis': {'showgrid': True, 'gridcolor': 'lightgray'}
            })
        
        return scene_config