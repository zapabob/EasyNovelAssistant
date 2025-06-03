# -*- coding: utf-8 -*-
"""
メモリ効率化システム v3.0 (Memory Efficiency System v3.0)
RTX3080最適化統合・自動ガベージコレクション・メモリリーク検出・動的バッファ管理

主要機能:
1. RTX3080 VRAM/RAM 最適化
2. 自動ガベージコレクション
3. メモリリーク検出・修復
4. 動的バッファサイズ調整
5. OOM予防システム
6. リアルタイム監視・アラート
"""

import gc
import os
import sys
import time
import threading
import psutil
import json
import logging
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from collections import deque, defaultdict
from pathlib import Path
import weakref

# GPU関連モジュール（オプション）
try:
    import torch
    import torch.cuda
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("WARNING: PyTorch not detected: CPU optimization only")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# プロジェクト内モジュール
try:
    from .rtx3080_optimizer import RTX3080Optimizer
    from ..integration.cross_suppression_engine import SessionMemoryBuffer
except ImportError:
    # フォールバック: 簡易版を使用
    RTX3080Optimizer = None
    SessionMemoryBuffer = None


@dataclass
class MemorySnapshot:
    """メモリスナップショット"""
    timestamp: float
    process_rss_mb: float
    process_vms_mb: float
    system_available_mb: float
    system_used_percent: float
    gpu_allocated_mb: Optional[float] = None
    gpu_reserved_mb: Optional[float] = None
    gpu_free_mb: Optional[float] = None
    cache_size_mb: float = 0.0
    buffer_count: int = 0
    gc_count: int = 0


@dataclass
class MemoryAlert:
    """メモリアラート"""
    level: str  # INFO, WARNING, CRITICAL
    message: str
    timestamp: float
    metrics: Dict[str, Any] = field(default_factory=dict)
    recovery_action: Optional[str] = None


class MemoryEfficiencySystemV3:
    """
    メモリ効率化システム v3.0
    RTX3080統合・自動最適化・予防的管理
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # 基本設定
        self.monitoring_enabled = self.config.get('monitoring_enabled', True)
        self.auto_gc_enabled = self.config.get('auto_gc_enabled', True)
        self.leak_detection_enabled = self.config.get('leak_detection_enabled', True)
        self.oom_prevention_enabled = self.config.get('oom_prevention_enabled', True)
        
        # RTX3080最適化
        self.rtx3080_optimization = self.config.get('rtx3080_optimization', True)
        self.gpu_memory_target_percent = self.config.get('gpu_memory_target_percent', 85.0)
        
        # 監視設定
        self.monitoring_interval = self.config.get('monitoring_interval', 1.0)  # 秒
        self.snapshot_history_size = self.config.get('snapshot_history_size', 1000)
        self.leak_detection_window = self.config.get('leak_detection_window', 300)  # 5分
        
        # アラート閾値
        self.warning_threshold_percent = self.config.get('warning_threshold_percent', 85.0)
        self.critical_threshold_percent = self.config.get('critical_threshold_percent', 95.0)
        self.gpu_warning_threshold_percent = self.config.get('gpu_warning_threshold_percent', 90.0)
        
        # GC設定
        self.gc_trigger_threshold_mb = self.config.get('gc_trigger_threshold_mb', 100.0)
        self.aggressive_gc_threshold_percent = self.config.get('aggressive_gc_threshold_percent', 90.0)
        
        # 状態管理
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.snapshot_history: deque = deque(maxlen=self.snapshot_history_size)
        self.alert_history: deque = deque(maxlen=100)
        
        # 統計
        self.stats = {
            'total_snapshots': 0,
            'total_alerts': 0,
            'gc_triggers': 0,
            'leak_detections': 0,
            'oom_preventions': 0,
            'memory_recovered_mb': 0.0
        }
        
        # キャッシュ・バッファ管理
        self.managed_caches: Dict[str, weakref.WeakValueDictionary] = {}
        self.managed_buffers: Dict[str, Any] = {}
        
        # RTX3080最適化器
        self.rtx_optimizer = None
        if self.rtx3080_optimization and RTX3080Optimizer:
            try:
                self.rtx_optimizer = RTX3080Optimizer(self.config)
                print("✅ RTX3080最適化器統合完了")
            except Exception as e:
                print(f"⚠️ RTX3080最適化器初期化失敗: {e}")
        
        # 緊急コールバック
        self.emergency_callbacks: List[Callable] = []
        
        # ログ設定
        self.logger = self._setup_logging()
        
        print(f"🚀 メモリ効率化システム v3.0 初期化完了")
        print(f"   ├─ RTX3080最適化: {'有効' if self.rtx_optimizer else '無効'}")
        print(f"   ├─ 自動GC: {'有効' if self.auto_gc_enabled else '無効'}")
        print(f"   ├─ リーク検出: {'有効' if self.leak_detection_enabled else '無効'}")
        print(f"   ├─ OOM予防: {'有効' if self.oom_prevention_enabled else '無効'}")
        print(f"   └─ 監視間隔: {self.monitoring_interval}秒")

    def _setup_logging(self) -> logging.Logger:
        """ログ設定"""
        logger = logging.getLogger('MemoryEfficiencyV3')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    def start_monitoring(self):
        """監視開始"""
        if self.is_monitoring:
            self.logger.warning("監視は既に実行中です")
            return
        
        self.is_monitoring = True
        self.snapshot_history.clear()
        self.alert_history.clear()
        
        # 初期スナップショット
        initial_snapshot = self._take_memory_snapshot()
        self.snapshot_history.append(initial_snapshot)
        
        # 監視スレッド開始
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop, 
            daemon=True,
            name="MemoryMonitorV3"
        )
        self.monitor_thread.start()
        
        self.logger.info(f"🔍 メモリ監視開始 (間隔: {self.monitoring_interval}秒)")
        
        # RTX3080最適化適用
        if self.rtx_optimizer:
            self._apply_rtx3080_optimizations()

    def stop_monitoring(self):
        """監視停止"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        
        # 最終統計
        final_stats = self.get_efficiency_report()
        self.logger.info(f"🛑 メモリ監視停止 - 統計: {final_stats['summary']}")

    def _monitoring_loop(self):
        """監視メインループ"""
        while self.is_monitoring:
            try:
                # スナップショット取得
                snapshot = self._take_memory_snapshot()
                self.snapshot_history.append(snapshot)
                self.stats['total_snapshots'] += 1
                
                # アラート評価
                alerts = self._evaluate_alerts(snapshot)
                for alert in alerts:
                    self._handle_alert(alert)
                
                # 自動GC評価
                if self.auto_gc_enabled:
                    self._evaluate_auto_gc(snapshot)
                
                # メモリリーク検出
                if self.leak_detection_enabled and len(self.snapshot_history) > 20:
                    self._detect_memory_leaks()
                
                # OOM予防
                if self.oom_prevention_enabled:
                    self._prevent_oom(snapshot)
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"監視ループエラー: {e}")
                time.sleep(max(self.monitoring_interval, 1.0))

    def _take_memory_snapshot(self) -> MemorySnapshot:
        """メモリスナップショット取得"""
        process = psutil.Process()
        memory_info = process.memory_info()
        system_memory = psutil.virtual_memory()
        
        # GPU統計
        gpu_allocated_mb = None
        gpu_reserved_mb = None
        gpu_free_mb = None
        
        if TORCH_AVAILABLE and torch.cuda.is_available():
            try:
                gpu_allocated_mb = torch.cuda.memory_allocated() / (1024 ** 2)
                gpu_reserved_mb = torch.cuda.memory_reserved() / (1024 ** 2)
                
                # 空きVRAM計算
                if self.rtx_optimizer:
                    total_vram = self.rtx_optimizer.gpu_info.get('memory_total', 10240)
                    gpu_free_mb = total_vram - gpu_reserved_mb
                
            except Exception as e:
                self.logger.debug(f"GPU統計取得エラー: {e}")
        
        # キャッシュ・バッファサイズ
        cache_size_mb = sum(
            sys.getsizeof(cache) / (1024 ** 2) 
            for cache in self.managed_caches.values()
        )
        
        buffer_count = len(self.managed_buffers)
        gc_count = sum(gc.get_count())
        
        return MemorySnapshot(
            timestamp=time.time(),
            process_rss_mb=memory_info.rss / (1024 ** 2),
            process_vms_mb=memory_info.vms / (1024 ** 2),
            system_available_mb=system_memory.available / (1024 ** 2),
            system_used_percent=system_memory.percent,
            gpu_allocated_mb=gpu_allocated_mb,
            gpu_reserved_mb=gpu_reserved_mb,
            gpu_free_mb=gpu_free_mb,
            cache_size_mb=cache_size_mb,
            buffer_count=buffer_count,
            gc_count=gc_count
        )

    def _evaluate_alerts(self, snapshot: MemorySnapshot) -> List[MemoryAlert]:
        """アラート評価"""
        alerts = []
        
        # システムメモリアラート
        if snapshot.system_used_percent >= self.critical_threshold_percent:
            alerts.append(MemoryAlert(
                level="CRITICAL",
                message=f"システムメモリ使用率が危険レベル: {snapshot.system_used_percent:.1f}%",
                timestamp=snapshot.timestamp,
                metrics={"memory_percent": snapshot.system_used_percent},
                recovery_action="emergency_gc"
            ))
        elif snapshot.system_used_percent >= self.warning_threshold_percent:
            alerts.append(MemoryAlert(
                level="WARNING",
                message=f"システムメモリ使用率が高い: {snapshot.system_used_percent:.1f}%",
                timestamp=snapshot.timestamp,
                metrics={"memory_percent": snapshot.system_used_percent},
                recovery_action="soft_gc"
            ))
        
        # GPUメモリアラート
        if snapshot.gpu_reserved_mb and snapshot.gpu_free_mb:
            gpu_usage_percent = (snapshot.gpu_reserved_mb / (snapshot.gpu_reserved_mb + snapshot.gpu_free_mb)) * 100
            
            if gpu_usage_percent >= self.gpu_warning_threshold_percent:
                alerts.append(MemoryAlert(
                    level="WARNING",
                    message=f"GPU メモリ使用率が高い: {gpu_usage_percent:.1f}%",
                    timestamp=snapshot.timestamp,
                    metrics={"gpu_usage_percent": gpu_usage_percent},
                    recovery_action="gpu_cache_clear"
                ))
        
        # プロセスメモリ急増アラート
        if len(self.snapshot_history) >= 2:
            prev_snapshot = self.snapshot_history[-2]
            memory_growth = snapshot.process_rss_mb - prev_snapshot.process_rss_mb
            
            if memory_growth > self.gc_trigger_threshold_mb:
                alerts.append(MemoryAlert(
                    level="INFO",
                    message=f"プロセスメモリ急増: +{memory_growth:.1f}MB",
                    timestamp=snapshot.timestamp,
                    metrics={"memory_growth_mb": memory_growth},
                    recovery_action="preventive_gc"
                ))
        
        return alerts

    def _handle_alert(self, alert: MemoryAlert):
        """アラート処理"""
        self.alert_history.append(alert)
        self.stats['total_alerts'] += 1
        
        # ログ出力
        log_level = getattr(self.logger, alert.level.lower(), self.logger.info)
        log_level(f"🚨 {alert.message}")
        
        # 回復アクション実行
        if alert.recovery_action:
            recovered_mb = self._execute_recovery_action(alert.recovery_action)
            if recovered_mb > 0:
                self.stats['memory_recovered_mb'] += recovered_mb
                self.logger.info(f"✅ メモリ回復: {recovered_mb:.1f}MB")

    def _execute_recovery_action(self, action: str) -> float:
        """回復アクション実行"""
        memory_before = psutil.Process().memory_info().rss / (1024 ** 2)
        
        try:
            if action == "emergency_gc":
                self._emergency_garbage_collection()
            elif action == "soft_gc":
                self._soft_garbage_collection()
            elif action == "preventive_gc":
                self._preventive_garbage_collection()
            elif action == "gpu_cache_clear":
                self._clear_gpu_cache()
            elif action == "cache_cleanup":
                self._cleanup_managed_caches()
            
            time.sleep(0.1)  # GC完了待機
            
        except Exception as e:
            self.logger.error(f"回復アクション '{action}' 実行エラー: {e}")
            return 0.0
        
        memory_after = psutil.Process().memory_info().rss / (1024 ** 2)
        return max(0.0, memory_before - memory_after)

    def _emergency_garbage_collection(self):
        """緊急ガベージコレクション"""
        self.logger.warning("🆘 緊急ガベージコレクション実行")
        
        # 全世代GC
        for i in range(3):
            collected = gc.collect()
            self.logger.debug(f"GC世代{i}: {collected}オブジェクト回収")
        
        # GPU キャッシュクリア
        if TORCH_AVAILABLE and torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        
        # 管理キャッシュクリア
        self._cleanup_managed_caches()
        
        # 緊急コールバック実行
        for callback in self.emergency_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"緊急コールバックエラー: {e}")
        
        self.stats['gc_triggers'] += 1

    def _soft_garbage_collection(self):
        """ソフトガベージコレクション"""
        collected = gc.collect()
        self.logger.debug(f"ソフトGC: {collected}オブジェクト回収")
        
        if TORCH_AVAILABLE and torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        self.stats['gc_triggers'] += 1

    def _preventive_garbage_collection(self):
        """予防的ガベージコレクション"""
        # 世代0のみ
        collected = gc.collect(0)
        self.logger.debug(f"予防GC: {collected}オブジェクト回収")

    def _clear_gpu_cache(self):
        """GPUキャッシュクリア"""
        if TORCH_AVAILABLE and torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            self.logger.debug("GPU キャッシュクリア完了")

    def _cleanup_managed_caches(self):
        """管理キャッシュクリーンアップ"""
        cleaned_count = 0
        
        for cache_name, cache in self.managed_caches.items():
            try:
                cache.clear()
                cleaned_count += 1
            except Exception as e:
                self.logger.error(f"キャッシュ '{cache_name}' クリーンアップエラー: {e}")
        
        self.logger.debug(f"管理キャッシュクリーンアップ: {cleaned_count}キャッシュ")

    def _evaluate_auto_gc(self, snapshot: MemorySnapshot):
        """自動GC評価"""
        # メモリ使用率に基づく判定
        if snapshot.system_used_percent >= self.aggressive_gc_threshold_percent:
            self._soft_garbage_collection()
        
        # プロセスメモリ増加に基づく判定
        if len(self.snapshot_history) >= 5:
            recent_snapshots = list(self.snapshot_history)[-5:]
            memory_trend = recent_snapshots[-1].process_rss_mb - recent_snapshots[0].process_rss_mb
            
            if memory_trend > self.gc_trigger_threshold_mb * 2:
                self._preventive_garbage_collection()

    def _detect_memory_leaks(self):
        """メモリリーク検出"""
        if len(self.snapshot_history) < 60:  # 1分以上のデータが必要
            return
        
        # 過去5分のスナップショット
        cutoff_time = time.time() - self.leak_detection_window
        recent_snapshots = [
            s for s in self.snapshot_history 
            if s.timestamp >= cutoff_time
        ]
        
        if len(recent_snapshots) < 20:
            return
        
        # 線形回帰でメモリ使用量の傾きを計算
        timestamps = [s.timestamp for s in recent_snapshots]
        memory_values = [s.process_rss_mb for s in recent_snapshots]
        
        slope = self._calculate_linear_regression_slope(timestamps, memory_values)
        
        # 傾きが正で一定値以上の場合、リークと判定
        leak_threshold_mb_per_minute = 5.0
        leak_threshold_per_second = leak_threshold_mb_per_minute / 60.0
        
        if slope > leak_threshold_per_second:
            self.stats['leak_detections'] += 1
            
            alert = MemoryAlert(
                level="WARNING",
                message=f"メモリリーク検出: {slope * 60:.2f}MB/分の増加",
                timestamp=time.time(),
                metrics={"leak_rate_mb_per_min": slope * 60},
                recovery_action="soft_gc"
            )
            
            self._handle_alert(alert)

    def _calculate_linear_regression_slope(self, x_values: List[float], y_values: List[float]) -> float:
        """線形回帰の傾きを計算"""
        n = len(x_values)
        if n < 2:
            return 0.0
        
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_xx = sum(x * x for x in x_values)
        
        denominator = n * sum_xx - sum_x * sum_x
        if denominator == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope

    def _prevent_oom(self, snapshot: MemorySnapshot):
        """OOM予防"""
        # 利用可能メモリが1GB未満の場合
        if snapshot.system_available_mb < 1024:
            self.stats['oom_preventions'] += 1
            
            alert = MemoryAlert(
                level="CRITICAL",
                message=f"OOM危険: 利用可能メモリ {snapshot.system_available_mb:.0f}MB",
                timestamp=snapshot.timestamp,
                metrics={"available_mb": snapshot.system_available_mb},
                recovery_action="emergency_gc"
            )
            
            self._handle_alert(alert)

    def _apply_rtx3080_optimizations(self):
        """RTX3080最適化適用"""
        if not self.rtx_optimizer:
            return
        
        try:
            # GPU メモリ最適化
            optimization_config = self.rtx_optimizer.get_current_config()
            
            if TORCH_AVAILABLE and torch.cuda.is_available():
                # PyTorchメモリ設定
                torch.cuda.set_per_process_memory_fraction(
                    self.gpu_memory_target_percent / 100.0
                )
                
                # メモリ断片化防止
                os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'
            
            self.logger.info("✅ RTX3080最適化適用完了")
            
        except Exception as e:
            self.logger.error(f"RTX3080最適化適用エラー: {e}")

    def register_cache(self, name: str, cache: Any):
        """キャッシュ登録"""
        if hasattr(cache, 'clear'):
            self.managed_caches[name] = weakref.WeakValueDictionary({'cache': cache})
            self.logger.debug(f"キャッシュ '{name}' 登録完了")
        else:
            self.logger.warning(f"キャッシュ '{name}' にclear()メソッドがありません")

    def register_buffer(self, name: str, buffer: Any):
        """バッファ登録"""
        self.managed_buffers[name] = buffer
        self.logger.debug(f"バッファ '{name}' 登録完了")

    def register_emergency_callback(self, callback: Callable):
        """緊急コールバック登録"""
        self.emergency_callbacks.append(callback)
        self.logger.debug("緊急コールバック登録完了")

    def get_current_memory_info(self) -> Dict[str, Any]:
        """現在のメモリ情報取得"""
        if not self.snapshot_history:
            return {}
        
        latest = self.snapshot_history[-1]
        
        return {
            'timestamp': latest.timestamp,
            'process_memory_mb': latest.process_rss_mb,
            'system_available_mb': latest.system_available_mb,
            'system_usage_percent': latest.system_used_percent,
            'gpu_allocated_mb': latest.gpu_allocated_mb,
            'gpu_free_mb': latest.gpu_free_mb,
            'cache_size_mb': latest.cache_size_mb,
            'buffer_count': latest.buffer_count,
            'monitoring_active': self.is_monitoring
        }

    def get_efficiency_report(self) -> Dict[str, Any]:
        """効率レポート取得"""
        if not self.snapshot_history:
            return {'error': 'スナップショット データなし'}
        
        # 統計計算
        snapshots = list(self.snapshot_history)
        duration_minutes = (snapshots[-1].timestamp - snapshots[0].timestamp) / 60
        
        memory_values = [s.process_rss_mb for s in snapshots]
        peak_memory = max(memory_values)
        avg_memory = sum(memory_values) / len(memory_values)
        min_memory = min(memory_values)
        
        # アラート統計
        alert_counts = defaultdict(int)
        for alert in self.alert_history:
            alert_counts[alert.level] += 1
        
        return {
            'summary': {
                'monitoring_duration_minutes': duration_minutes,
                'total_snapshots': len(snapshots),
                'peak_memory_mb': peak_memory,
                'average_memory_mb': avg_memory,
                'memory_variance_mb': peak_memory - min_memory
            },
            'performance': {
                'gc_triggers': self.stats['gc_triggers'],
                'leak_detections': self.stats['leak_detections'],
                'oom_preventions': self.stats['oom_preventions'],
                'total_memory_recovered_mb': self.stats['memory_recovered_mb']
            },
            'alerts': {
                'total_alerts': len(self.alert_history),
                'by_level': dict(alert_counts),
                'alert_rate_per_hour': len(self.alert_history) / max(duration_minutes / 60, 0.01)
            },
            'optimizations': {
                'rtx3080_enabled': self.rtx_optimizer is not None,
                'auto_gc_enabled': self.auto_gc_enabled,
                'leak_detection_enabled': self.leak_detection_enabled,
                'managed_caches': len(self.managed_caches),
                'managed_buffers': len(self.managed_buffers)
            }
        }

    def force_memory_cleanup(self) -> Dict[str, float]:
        """強制メモリクリーンアップ"""
        memory_before = psutil.Process().memory_info().rss / (1024 ** 2)
        
        # 管理キャッシュクリア
        self._cleanup_managed_caches()
        
        # 緊急GC
        self._emergency_garbage_collection()
        
        # 統計更新
        time.sleep(0.5)  # クリーンアップ完了待機
        memory_after = psutil.Process().memory_info().rss / (1024 ** 2)
        recovered = max(0.0, memory_before - memory_after)
        
        self.stats['memory_recovered_mb'] += recovered
        
        return {
            'memory_before_mb': memory_before,
            'memory_after_mb': memory_after,
            'recovered_mb': recovered,
            'success': recovered > 0
        }

    def shutdown(self):
        """システム終了"""
        self.logger.info("🔄 メモリ効率化システム v3.0 終了中...")
        
        # 監視停止
        self.stop_monitoring()
        
        # 最終クリーンアップ
        cleanup_result = self.force_memory_cleanup()
        
        # 統計保存
        self._save_session_stats()
        
        self.logger.info(f"✅ システム終了完了 - 最終回復: {cleanup_result['recovered_mb']:.1f}MB")

    def _save_session_stats(self):
        """セッション統計保存"""
        try:
            stats_dir = Path("logs/memory_efficiency")
            stats_dir.mkdir(parents=True, exist_ok=True)
            
            session_data = {
                'timestamp': time.time(),
                'stats': self.stats,
                'efficiency_report': self.get_efficiency_report(),
                'config': self.config
            }
            
            timestamp_str = time.strftime("%Y%m%d_%H%M%S")
            stats_file = stats_dir / f"memory_session_{timestamp_str}.json"
            
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"📊 セッション統計保存: {stats_file}")
            
        except Exception as e:
            self.logger.error(f"統計保存エラー: {e}")


def create_memory_efficiency_system(config: Dict[str, Any] = None) -> MemoryEfficiencySystemV3:
    """メモリ効率化システム v3.0 ファクトリ関数"""
    default_config = {
        'monitoring_enabled': True,
        'auto_gc_enabled': True,
        'leak_detection_enabled': True,
        'oom_prevention_enabled': True,
        'rtx3080_optimization': True,
        'monitoring_interval': 1.0,
        'warning_threshold_percent': 85.0,
        'critical_threshold_percent': 95.0,
        'gpu_warning_threshold_percent': 90.0,
        'gc_trigger_threshold_mb': 100.0,
        'aggressive_gc_threshold_percent': 90.0
    }
    
    if config:
        default_config.update(config)
    
    return MemoryEfficiencySystemV3(default_config)


# テスト関数
def test_memory_efficiency_system():
    """メモリ効率化システムのテスト"""
    print("🧪 メモリ効率化システム v3.0 テスト開始")
    
    # システム作成
    system = create_memory_efficiency_system({
        'monitoring_interval': 0.5,
        'warning_threshold_percent': 50.0  # テスト用低閾値
    })
    
    try:
        # 監視開始
        system.start_monitoring()
        
        # メモリ負荷テスト
        test_data = []
        for i in range(100):
            test_data.append([0] * 100000)  # メモリ使用量増加
            time.sleep(0.01)
        
        # 現在のメモリ情報
        memory_info = system.get_current_memory_info()
        print(f"📊 現在のメモリ使用量: {memory_info['process_memory_mb']:.1f}MB")
        
        # 強制クリーンアップテスト
        cleanup_result = system.force_memory_cleanup()
        print(f"🧹 クリーンアップ結果: {cleanup_result}")
        
        # 効率レポート
        efficiency_report = system.get_efficiency_report()
        print(f"📈 効率レポート: {efficiency_report['summary']}")
        
        # テスト成功
        print("✅ メモリ効率化システム v3.0 テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        
    finally:
        # システム終了
        system.shutdown()


if __name__ == "__main__":
    test_memory_efficiency_system() 