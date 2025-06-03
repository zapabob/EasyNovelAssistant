# -*- coding: utf-8 -*-
"""
UI Package
ユーザーインターフェース・制御パネル
"""

try:
    from .repetition_control_panel import RepetitionControlPanel
    CONTROL_PANEL_AVAILABLE = True
except ImportError:
    CONTROL_PANEL_AVAILABLE = False

__all__ = []

if CONTROL_PANEL_AVAILABLE:
    __all__.append('RepetitionControlPanel') 