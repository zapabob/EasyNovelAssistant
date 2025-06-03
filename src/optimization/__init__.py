# -*- coding: utf-8 -*-
"""
Optimization Package
最適化システム・性能監視・メモリ効率化
"""

try:
    from .memory_efficiency_system_v3 import MemoryEfficiencySystemV3
    MEMORY_EFFICIENCY_AVAILABLE = True
except ImportError:
    MEMORY_EFFICIENCY_AVAILABLE = False

try:
    from .performance_monitoring_v3 import PerformanceMonitoringV3
    PERFORMANCE_MONITORING_AVAILABLE = True
except ImportError:
    PERFORMANCE_MONITORING_AVAILABLE = False

__all__ = []

if MEMORY_EFFICIENCY_AVAILABLE:
    __all__.append('MemoryEfficiencySystemV3')

if PERFORMANCE_MONITORING_AVAILABLE:
    __all__.append('PerformanceMonitoringV3') 