# Advanced Features - Phase 3 Implementation
"""
Advanced workflow automation features including:
- Knowledge capture and management
- Collaboration enhancement
- Onboarding automation
- System integration and optimization

This module builds upon Phase 1 (Core Automation) and Phase 2 (Predictive Intelligence)
to provide advanced collaboration and knowledge capture capabilities.
"""

from .knowledge_capture import (
    DecisionCaptureEngine,
    KnowledgeExtractor,
    KnowledgeBaseIntegrator,
    KnowledgeValidator,
    KnowledgeCaptureSystem
)

__all__ = [
    'DecisionCaptureEngine',
    'KnowledgeExtractor', 
    'KnowledgeBaseIntegrator',
    'KnowledgeValidator',
    'KnowledgeCaptureSystem'
]

__version__ = "3.0.0"
__phase__ = "Phase 3: Advanced Features"