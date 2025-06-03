# -*- coding: utf-8 -*-
"""
NKAT Package
NKAT理論統合・感情エンジン・動的パラメータ調整システム
"""

try:
    from .nkat_integration_preparation_v3 import (
        NKATEmotionType,
        NKATIntegrationPreparationV3,
        EmotionState,
        NKATOptimizationSettings
    )
    NKAT_V3_AVAILABLE = True
except ImportError:
    NKAT_V3_AVAILABLE = False

__all__ = []

if NKAT_V3_AVAILABLE:
    __all__.extend([
        'NKATEmotionType',
        'NKATIntegrationPreparationV3', 
        'EmotionState',
        'NKATOptimizationSettings'
    ]) 