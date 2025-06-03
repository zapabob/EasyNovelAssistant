# -*- coding: utf-8 -*-
"""
Integration Package
統合システム・協調制御システム
"""

try:
    from .cross_suppression_engine import CrossSuppressionEngine, create_default_cross_engine
    CROSS_SUPPRESSION_AVAILABLE = True
except ImportError:
    CROSS_SUPPRESSION_AVAILABLE = False

try:
    from .lora_style_coordinator import LoRAStyleCoordinator, create_default_coordinator
    LORA_COORDINATOR_AVAILABLE = True
except ImportError:
    LORA_COORDINATOR_AVAILABLE = False

try:
    from .realtime_coordination_controller_v3 import RealtimeCoordinationControllerV3, TaskPriority
    REALTIME_CONTROLLER_AVAILABLE = True
except ImportError:
    REALTIME_CONTROLLER_AVAILABLE = False

__all__ = []

if CROSS_SUPPRESSION_AVAILABLE:
    __all__.extend(['CrossSuppressionEngine', 'create_default_cross_engine'])

if LORA_COORDINATOR_AVAILABLE:
    __all__.extend(['LoRAStyleCoordinator', 'create_default_coordinator'])

if REALTIME_CONTROLLER_AVAILABLE:
    __all__.extend(['RealtimeCoordinationControllerV3', 'TaskPriority']) 