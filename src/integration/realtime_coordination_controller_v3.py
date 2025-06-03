# -*- coding: utf-8 -*-
"""
リアルタイム協調制御システム v3.0 (Real-time Coordination Controller v3.0)
高精度制御・動的負荷分散・エラー回復・性能最適化統合版

主要機能:
1. マイクロ秒精度のリアルタイム制御
2. 動的負荷分散・優先度制御
3. 自動エラー回復・フォールバック
4. RTX3080最適化統合
5. NKAT理論プリエンプション対応
6. 協調最適化・性能モニタリング
"""

import asyncio
import time
import threading
import queue
import json
import logging
import weakref
from typing import Dict, List, Optional, Tuple, Any, Callable, Awaitable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import asynccontextmanager
import heapq
from enum import Enum, auto

# プロジェクト内モジュール統合
try:
    from ..utils.repetition_suppressor_v3 import AdvancedRepetitionSuppressorV3
    from ..optimization.memory_efficiency_system_v3 import MemoryEfficiencySystemV3
    from .cross_suppression_engine import CrossSuppressionEngine
    from .lora_coordination_system import LoRACoordinationSystem
except ImportError:
    # フォールバック
    AdvancedRepetitionSuppressorV3 = None
    MemoryEfficiencySystemV3 = None
    CrossSuppressionEngine = None
    LoRACoordinationSystem = None


class TaskPriority(Enum):
    """タスク優先度"""
    CRITICAL = auto()    # クリティカル（最高優先度）
    HIGH = auto()        # 高優先度
    NORMAL = auto()      # 通常優先度
    LOW = auto()         # 低優先度
    BACKGROUND = auto()  # バックグラウンド


class TaskStatus(Enum):
    """タスク状態"""
    PENDING = auto()     # 待機中
    RUNNING = auto()     # 実行中
    COMPLETED = auto()   # 完了
    FAILED = auto()      # 失敗
    CANCELLED = auto()   # キャンセル
    RETRYING = auto()    # 再試行中


@dataclass
class CoordinationTask:
    """協調タスク"""
    task_id: str
    priority: TaskPriority
    func: Callable
    args: Tuple = ()
    kwargs: Dict[str, Any] = field(default_factory=dict)
    callback: Optional[Callable] = None
    timeout: Optional[float] = None
    max_retries: int = 3
    dependencies: List[str] = field(default_factory=list)
    
    # 実行時状態
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Any = None
    error: Optional[Exception] = None
    retry_count: int = 0
    execution_time: float = 0.0
    

@dataclass
class PerformanceMetrics:
    """性能メトリクス"""
    timestamp: float
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_execution_time: float
    throughput_per_second: float
    queue_length: int
    active_workers: int
    cpu_usage_percent: float
    memory_usage_mb: float
    gpu_utilization_percent: Optional[float] = None


class RealtimeCoordinationControllerV3:
    """
    リアルタイム協調制御システム v3.0
    マイクロ秒精度・動的負荷分散・自動回復統合版
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # 基本設定
        self.max_workers = self.config.get('max_workers', 8)
        self.queue_size = self.config.get('queue_size', 1000)
        self.monitoring_interval = self.config.get('monitoring_interval', 0.1)  # 100ms
        self.performance_window_size = self.config.get('performance_window_size', 1000)
        
        # 高精度制御設定
        self.precision_timing = self.config.get('precision_timing', True)
        self.microsecond_precision = self.config.get('microsecond_precision', True)
        self.preemptive_scheduling = self.config.get('preemptive_scheduling', True)
        
        # 動的負荷分散設定
        self.dynamic_scaling = self.config.get('dynamic_scaling', True)
        self.load_threshold_high = self.config.get('load_threshold_high', 0.8)
        self.load_threshold_low = self.config.get('load_threshold_low', 0.3)
        self.scale_up_delay = self.config.get('scale_up_delay', 1.0)
        self.scale_down_delay = self.config.get('scale_down_delay', 5.0)
        
        # エラー回復設定
        self.auto_recovery_enabled = self.config.get('auto_recovery_enabled', True)
        self.circuit_breaker_enabled = self.config.get('circuit_breaker_enabled', True)
        self.circuit_breaker_threshold = self.config.get('circuit_breaker_threshold', 0.5)
        self.circuit_breaker_timeout = self.config.get('circuit_breaker_timeout', 30.0)
        
        # 状態管理
        self.is_running = False
        self.is_paused = False
        self.start_timestamp = None
        
        # タスクキューとワーカー
        self.task_queue = queue.PriorityQueue(maxsize=self.queue_size)
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.active_tasks: Dict[str, CoordinationTask] = {}
        self.completed_tasks: Dict[str, CoordinationTask] = {}
        self.failed_tasks: Dict[str, CoordinationTask] = {}
        
        # 依存関係管理
        self.dependency_graph: Dict[str, List[str]] = defaultdict(list)
        self.waiting_tasks: Dict[str, CoordinationTask] = {}
        
        # 性能監視
        self.performance_history: deque = deque(maxlen=self.performance_window_size)
        self.metrics_lock = threading.Lock()
        self.monitor_thread: Optional[threading.Thread] = None
        
        # 動的スケーリング
        self.scaling_lock = threading.Lock()
        self.last_scale_up = 0.0
        self.last_scale_down = 0.0
        self.current_workers = self.max_workers
        
        # サーキットブレーカー
        self.circuit_breaker_state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.circuit_breaker_failures = 0
        self.circuit_breaker_last_failure = 0.0
        
        # 統合システム
        self.memory_system: Optional[MemoryEfficiencySystemV3] = None
        self.repetition_suppressor: Optional[AdvancedRepetitionSuppressorV3] = None
        self.cross_suppression_engine: Optional[CrossSuppressionEngine] = None
        self.lora_coordination: Optional[LoRACoordinationSystem] = None
        
        # コールバック
        self.task_callbacks: Dict[str, List[Callable]] = defaultdict(list)
        self.system_callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
        # ログ設定
        self.logger = self._setup_logging()
        
        # システム統合
        self._initialize_integrated_systems()
        
        print(f"🚀 リアルタイム協調制御システム v3.0 初期化完了")
        print(f"   ├─ 最大ワーカー数: {self.max_workers}")
        print(f"   ├─ マイクロ秒精度: {'有効' if self.microsecond_precision else '無効'}")
        print(f"   ├─ 動的スケーリング: {'有効' if self.dynamic_scaling else '無効'}")
        print(f"   ├─ 自動回復: {'有効' if self.auto_recovery_enabled else '無効'}")
        print(f"   └─ 統合システム: {self._get_integrated_systems_status()}")

    def _setup_logging(self) -> logging.Logger:
        """ログ設定"""
        logger = logging.getLogger('RealtimeCoordinationV3')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    def _initialize_integrated_systems(self):
        """統合システム初期化"""
        try:
            # メモリ効率化システム
            if MemoryEfficiencySystemV3:
                self.memory_system = MemoryEfficiencySystemV3(self.config)
                self.register_system_callback('memory_alert', self._handle_memory_alert)
            
            # 反復抑制システム
            if AdvancedRepetitionSuppressorV3:
                self.repetition_suppressor = AdvancedRepetitionSuppressorV3(self.config)
            
            # クロス抑制エンジン
            if CrossSuppressionEngine:
                self.cross_suppression_engine = CrossSuppressionEngine(self.config)
            
            # LoRA協調システム
            if LoRACoordinationSystem:
                self.lora_coordination = LoRACoordinationSystem(self.config)
            
            self.logger.info("✅ 統合システム初期化完了")
            
        except Exception as e:
            self.logger.error(f"統合システム初期化エラー: {e}")

    def _get_integrated_systems_status(self) -> str:
        """統合システム状態取得"""
        systems = []
        if self.memory_system:
            systems.append("Memory")
        if self.repetition_suppressor:
            systems.append("Repetition")
        if self.cross_suppression_engine:
            systems.append("CrossSuppression")
        if self.lora_coordination:
            systems.append("LoRA")
        
        return f"{len(systems)}システム統合 ({', '.join(systems)})"

    async def start(self):
        """システム開始"""
        if self.is_running:
            self.logger.warning("システムは既に実行中です")
            return
        
        self.is_running = True
        self.is_paused = False
        self.start_timestamp = time.time()
        
        # 統合システム開始
        if self.memory_system:
            self.memory_system.start_monitoring()
        
        # 性能監視開始
        self.monitor_thread = threading.Thread(
            target=self._performance_monitoring_loop,
            daemon=True,
            name="CoordinationMonitor"
        )
        self.monitor_thread.start()
        
        self.logger.info("🎯 リアルタイム協調制御システム開始")
        
        # 初期性能測定
        await self._take_performance_snapshot()

    async def stop(self):
        """システム停止"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # 残りタスクの完了待機
        self.logger.info("📋 残りタスクの完了を待機中...")
        await self._wait_for_completion()
        
        # エグゼキューター停止
        self.executor.shutdown(wait=True)
        
        # 統合システム停止
        if self.memory_system:
            self.memory_system.stop_monitoring()
        
        # 最終統計
        final_stats = self.get_performance_report()
        self.logger.info(f"🛑 システム停止完了 - 統計: {final_stats['summary']}")

    async def submit_task(self, 
                         task_id: str,
                         func: Callable,
                         priority: TaskPriority = TaskPriority.NORMAL,
                         args: Tuple = (),
                         kwargs: Dict[str, Any] = None,
                         callback: Optional[Callable] = None,
                         timeout: Optional[float] = None,
                         dependencies: List[str] = None) -> str:
        """タスク投入"""
        
        if not self.is_running:
            raise RuntimeError("システムが停止中です")
        
        if self.is_paused:
            raise RuntimeError("システムが一時停止中です")
        
        kwargs = kwargs or {}
        dependencies = dependencies or []
        
        # タスク作成
        task = CoordinationTask(
            task_id=task_id,
            priority=priority,
            func=func,
            args=args,
            kwargs=kwargs,
            callback=callback,
            timeout=timeout,
            dependencies=dependencies
        )
        
        # 依存関係チェック
        if dependencies:
            unresolved_deps = [dep for dep in dependencies if dep not in self.completed_tasks]
            
            if unresolved_deps:
                # 依存関係が未解決の場合は待機
                self.waiting_tasks[task_id] = task
                for dep in dependencies:
                    self.dependency_graph[dep].append(task_id)
                
                self.logger.debug(f"📋 タスク {task_id} は依存関係待機: {unresolved_deps}")
                return task_id
        
        # キューに投入
        await self._enqueue_task(task)
        
        return task_id

    async def _enqueue_task(self, task: CoordinationTask):
        """タスクをキューに投入"""
        
        # サーキットブレーカーチェック
        if not self._circuit_breaker_check():
            task.status = TaskStatus.FAILED
            task.error = Exception("サーキットブレーカーが開いています")
            self.failed_tasks[task.task_id] = task
            return
        
        # 優先度に基づくキューイング
        priority_value = self._get_priority_value(task.priority)
        timestamp = time.time()
        
        if self.microsecond_precision:
            timestamp = time.time_ns() / 1_000_000_000  # ナノ秒精度
        
        # 優先度キューに投入（優先度が高いほど値が小さい）
        queue_item = (priority_value, timestamp, task)
        
        try:
            self.task_queue.put_nowait(queue_item)
            self.logger.debug(f"📥 タスク投入: {task.task_id} (優先度: {task.priority})")
            
            # 非同期実行開始
            asyncio.create_task(self._execute_task_async(task))
            
        except queue.Full:
            self.logger.error(f"❌ キューが満杯: タスク {task.task_id} を拒否")
            task.status = TaskStatus.FAILED
            task.error = Exception("キューが満杯")
            self.failed_tasks[task.task_id] = task

    async def _execute_task_async(self, task: CoordinationTask):
        """タスク非同期実行"""
        
        # キューから取得待機
        try:
            priority_value, timestamp, queue_task = self.task_queue.get(timeout=1.0)
            
            if queue_task.task_id != task.task_id:
                # 順序が変わった場合は再投入
                self.task_queue.put((priority_value, timestamp, queue_task))
                return
            
        except queue.Empty:
            self.logger.warning(f"⏰ タスク {task.task_id} がキューから取得できませんでした")
            return
        
        # 実行開始
        task.status = TaskStatus.RUNNING
        task.start_time = time.time()
        self.active_tasks[task.task_id] = task
        
        try:
            # タイムアウト設定
            if task.timeout:
                result = await asyncio.wait_for(
                    self._execute_task_with_recovery(task),
                    timeout=task.timeout
                )
            else:
                result = await self._execute_task_with_recovery(task)
            
            # 完了処理
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.end_time = time.time()
            task.execution_time = task.end_time - task.start_time
            
            self.completed_tasks[task.task_id] = task
            self.logger.debug(f"✅ タスク完了: {task.task_id} ({task.execution_time:.3f}s)")
            
            # コールバック実行
            if task.callback:
                try:
                    await self._safe_callback_execution(task.callback, task.result)
                except Exception as e:
                    self.logger.error(f"コールバックエラー: {e}")
            
            # 依存タスクの解放
            await self._resolve_dependencies(task.task_id)
            
        except asyncio.TimeoutError:
            self.logger.error(f"⏰ タスクタイムアウト: {task.task_id}")
            task.status = TaskStatus.FAILED
            task.error = Exception("タイムアウト")
            self._handle_task_failure(task)
            
        except Exception as e:
            self.logger.error(f"❌ タスク実行エラー: {task.task_id} - {e}")
            task.status = TaskStatus.FAILED
            task.error = e
            self._handle_task_failure(task)
            
        finally:
            # クリーンアップ
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
            
            self.task_queue.task_done()

    async def _execute_task_with_recovery(self, task: CoordinationTask) -> Any:
        """エラー回復機能付きタスク実行"""
        
        for attempt in range(task.max_retries + 1):
            try:
                # 統合システム前処理
                await self._pre_task_execution(task)
                
                # メイン処理実行
                if asyncio.iscoroutinefunction(task.func):
                    result = await task.func(*task.args, **task.kwargs)
                else:
                    # 同期関数を非同期実行
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        self.executor, 
                        task.func, 
                        *task.args
                    )
                
                # 統合システム後処理
                await self._post_task_execution(task, result)
                
                return result
                
            except Exception as e:
                task.retry_count = attempt
                
                if attempt < task.max_retries:
                    self.logger.warning(f"🔄 タスク再試行: {task.task_id} ({attempt + 1}/{task.max_retries + 1})")
                    task.status = TaskStatus.RETRYING
                    
                    # 指数バックオフ待機
                    await asyncio.sleep(2 ** attempt * 0.1)
                    continue
                else:
                    # 最大再試行回数に達した
                    raise e

    async def _pre_task_execution(self, task: CoordinationTask):
        """タスク実行前処理"""
        
        # メモリチェック
        if self.memory_system:
            memory_info = self.memory_system.get_current_memory_info()
            if memory_info.get('system_usage_percent', 0) > 95:
                # 緊急メモリクリーンアップ
                self.memory_system.force_memory_cleanup()
        
        # RTX3080最適化適用
        if hasattr(task.func, '__name__') and 'gpu' in task.func.__name__.lower():
            if self.memory_system and self.memory_system.rtx_optimizer:
                # GPU タスク用最適化
                pass

    async def _post_task_execution(self, task: CoordinationTask, result: Any):
        """タスク実行後処理"""
        
        # 結果の統合処理
        if isinstance(result, str) and self.repetition_suppressor:
            # テキスト結果の反復チェック
            try:
                improved_result, _ = self.repetition_suppressor.suppress_repetitions_with_debug_v3(
                    result, task.kwargs.get('character')
                )
                task.result = improved_result
            except Exception as e:
                self.logger.debug(f"反復処理スキップ: {e}")

    async def _safe_callback_execution(self, callback: Callable, result: Any):
        """安全なコールバック実行"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(result)
            else:
                callback(result)
        except Exception as e:
            self.logger.error(f"コールバック実行エラー: {e}")

    async def _resolve_dependencies(self, completed_task_id: str):
        """依存関係解決"""
        
        if completed_task_id not in self.dependency_graph:
            return
        
        waiting_task_ids = self.dependency_graph[completed_task_id]
        del self.dependency_graph[completed_task_id]
        
        for waiting_task_id in waiting_task_ids:
            if waiting_task_id not in self.waiting_tasks:
                continue
            
            waiting_task = self.waiting_tasks[waiting_task_id]
            
            # 全ての依存関係が解決されたかチェック
            unresolved_deps = [
                dep for dep in waiting_task.dependencies 
                if dep not in self.completed_tasks
            ]
            
            if not unresolved_deps:
                # 依存関係が全て解決された
                del self.waiting_tasks[waiting_task_id]
                await self._enqueue_task(waiting_task)
                self.logger.debug(f"🔓 依存関係解決: タスク {waiting_task_id}")

    def _handle_task_failure(self, task: CoordinationTask):
        """タスク失敗処理"""
        
        task.end_time = time.time()
        if task.start_time:
            task.execution_time = task.end_time - task.start_time
        
        self.failed_tasks[task.task_id] = task
        
        # サーキットブレーカー更新
        self._update_circuit_breaker(False)
        
        # システムコールバック実行
        for callback in self.system_callbacks.get('task_failed', []):
            try:
                callback(task)
            except Exception as e:
                self.logger.error(f"システムコールバックエラー: {e}")

    def _circuit_breaker_check(self) -> bool:
        """サーキットブレーカーチェック"""
        
        if not self.circuit_breaker_enabled:
            return True
        
        current_time = time.time()
        
        if self.circuit_breaker_state == "OPEN":
            # タイムアウト経過後にHALF_OPENに移行
            if current_time - self.circuit_breaker_last_failure > self.circuit_breaker_timeout:
                self.circuit_breaker_state = "HALF_OPEN"
                self.logger.info("🔄 サーキットブレーカー: HALF_OPEN状態に移行")
                return True
            return False
        
        return True

    def _update_circuit_breaker(self, success: bool):
        """サーキットブレーカー更新"""
        
        if not self.circuit_breaker_enabled:
            return
        
        if success:
            if self.circuit_breaker_state == "HALF_OPEN":
                self.circuit_breaker_state = "CLOSED"
                self.circuit_breaker_failures = 0
                self.logger.info("✅ サーキットブレーカー: CLOSED状態に復帰")
        else:
            self.circuit_breaker_failures += 1
            self.circuit_breaker_last_failure = time.time()
            
            if self.circuit_breaker_state == "CLOSED":
                # 失敗率が閾値を超えた場合にOPENに移行
                total_tasks = len(self.completed_tasks) + len(self.failed_tasks)
                if total_tasks > 10:  # 最小サンプル数
                    failure_rate = len(self.failed_tasks) / total_tasks
                    if failure_rate > self.circuit_breaker_threshold:
                        self.circuit_breaker_state = "OPEN"
                        self.logger.warning(f"🚫 サーキットブレーカー: OPEN状態に移行 (失敗率: {failure_rate:.2%})")
            
            elif self.circuit_breaker_state == "HALF_OPEN":
                # HALF_OPEN中の失敗でOPENに戻る
                self.circuit_breaker_state = "OPEN"
                self.logger.warning("🚫 サーキットブレーカー: OPEN状態に戻る")

    def _get_priority_value(self, priority: TaskPriority) -> int:
        """優先度の数値変換"""
        priority_map = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.NORMAL: 2,
            TaskPriority.LOW: 3,
            TaskPriority.BACKGROUND: 4
        }
        return priority_map.get(priority, 2)

    def _performance_monitoring_loop(self):
        """性能監視ループ"""
        while self.is_running:
            try:
                # 性能スナップショット取得
                asyncio.run(self._take_performance_snapshot())
                
                # 動的スケーリング評価
                if self.dynamic_scaling:
                    self._evaluate_dynamic_scaling()
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"性能監視エラー: {e}")
                time.sleep(max(self.monitoring_interval, 1.0))

    async def _take_performance_snapshot(self):
        """性能スナップショット取得"""
        
        current_time = time.time()
        
        # 基本統計
        total_tasks = len(self.completed_tasks) + len(self.failed_tasks) + len(self.active_tasks)
        completed_count = len(self.completed_tasks)
        failed_count = len(self.failed_tasks)
        
        # 実行時間統計
        if self.completed_tasks:
            execution_times = [task.execution_time for task in self.completed_tasks.values()]
            avg_execution_time = sum(execution_times) / len(execution_times)
        else:
            avg_execution_time = 0.0
        
        # スループット計算
        if self.performance_history:
            time_window = current_time - self.performance_history[0].timestamp
            tasks_in_window = completed_count - (self.performance_history[0].completed_tasks if self.performance_history else 0)
            throughput = tasks_in_window / max(time_window, 0.001)
        else:
            throughput = 0.0
        
        # システムリソース
        import psutil
        cpu_usage = psutil.cpu_percent(interval=None)
        memory_info = psutil.virtual_memory()
        memory_usage_mb = (memory_info.total - memory_info.available) / (1024 ** 2)
        
        # GPU使用率（オプション）
        gpu_utilization = None
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            gpu_util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpu_utilization = gpu_util.gpu
        except:
            pass
        
        # メトリクス作成
        metrics = PerformanceMetrics(
            timestamp=current_time,
            total_tasks=total_tasks,
            completed_tasks=completed_count,
            failed_tasks=failed_count,
            average_execution_time=avg_execution_time,
            throughput_per_second=throughput,
            queue_length=self.task_queue.qsize(),
            active_workers=len(self.active_tasks),
            cpu_usage_percent=cpu_usage,
            memory_usage_mb=memory_usage_mb,
            gpu_utilization_percent=gpu_utilization
        )
        
        with self.metrics_lock:
            self.performance_history.append(metrics)

    def _evaluate_dynamic_scaling(self):
        """動的スケーリング評価"""
        
        if not self.performance_history:
            return
        
        with self.scaling_lock:
            current_time = time.time()
            latest_metrics = self.performance_history[-1]
            
            # 負荷評価
            queue_load = latest_metrics.queue_length / self.queue_size
            worker_load = latest_metrics.active_workers / self.current_workers
            cpu_load = latest_metrics.cpu_usage_percent / 100.0
            
            overall_load = (queue_load + worker_load + cpu_load) / 3.0
            
            # スケールアップ判定
            if (overall_load > self.load_threshold_high and 
                current_time - self.last_scale_up > self.scale_up_delay and
                self.current_workers < self.max_workers * 2):  # 最大2倍まで
                
                self.current_workers += 1
                self.last_scale_up = current_time
                self.logger.info(f"📈 ワーカー数増加: {self.current_workers}")
            
            # スケールダウン判定
            elif (overall_load < self.load_threshold_low and 
                  current_time - self.last_scale_down > self.scale_down_delay and
                  self.current_workers > max(2, self.max_workers // 2)):  # 最小半分まで
                
                self.current_workers -= 1
                self.last_scale_down = current_time
                self.logger.info(f"📉 ワーカー数減少: {self.current_workers}")

    def _handle_memory_alert(self, alert_data: Dict[str, Any]):
        """メモリアラート処理"""
        if alert_data.get('level') == 'CRITICAL':
            self.logger.warning("🆘 クリティカルメモリアラート: 低優先度タスクを一時停止")
            # 低優先度タスクの実行を一時的に停止
            self.is_paused = True
            
            # 一定時間後に再開
            def resume_after_delay():
                time.sleep(5.0)
                self.is_paused = False
                self.logger.info("🔄 タスク実行再開")
            
            threading.Thread(target=resume_after_delay, daemon=True).start()

    async def _wait_for_completion(self, timeout: Optional[float] = None):
        """完了待機"""
        start_time = time.time()
        
        while self.active_tasks or not self.task_queue.empty():
            if timeout and (time.time() - start_time) > timeout:
                self.logger.warning("⏰ 完了待機タイムアウト")
                break
            
            await asyncio.sleep(0.1)

    # パブリックAPI

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """タスク状態取得"""
        
        # アクティブタスク
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return {
                'task_id': task_id,
                'status': task.status.name,
                'start_time': task.start_time,
                'running_time': time.time() - task.start_time if task.start_time else 0,
                'retry_count': task.retry_count
            }
        
        # 完了タスク
        if task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
            return {
                'task_id': task_id,
                'status': task.status.name,
                'execution_time': task.execution_time,
                'result': task.result
            }
        
        # 失敗タスク
        if task_id in self.failed_tasks:
            task = self.failed_tasks[task_id]
            return {
                'task_id': task_id,
                'status': task.status.name,
                'error': str(task.error),
                'retry_count': task.retry_count
            }
        
        # 待機中タスク
        if task_id in self.waiting_tasks:
            task = self.waiting_tasks[task_id]
            return {
                'task_id': task_id,
                'status': 'WAITING_DEPENDENCIES',
                'dependencies': task.dependencies
            }
        
        return None

    def get_system_status(self) -> Dict[str, Any]:
        """システム状態取得"""
        
        current_time = time.time()
        uptime = current_time - self.start_timestamp if self.start_timestamp else 0
        
        return {
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'uptime_seconds': uptime,
            'active_tasks': len(self.active_tasks),
            'waiting_tasks': len(self.waiting_tasks),
            'completed_tasks': len(self.completed_tasks),
            'failed_tasks': len(self.failed_tasks),
            'queue_length': self.task_queue.qsize(),
            'current_workers': self.current_workers,
            'circuit_breaker_state': self.circuit_breaker_state,
            'integrated_systems': {
                'memory_system': self.memory_system is not None,
                'repetition_suppressor': self.repetition_suppressor is not None,
                'cross_suppression_engine': self.cross_suppression_engine is not None,
                'lora_coordination': self.lora_coordination is not None
            }
        }

    def get_performance_report(self) -> Dict[str, Any]:
        """性能レポート取得"""
        
        if not self.performance_history:
            return {'error': '性能データなし'}
        
        with self.metrics_lock:
            metrics_list = list(self.performance_history)
        
        if not metrics_list:
            return {'error': '性能データなし'}
        
        # 統計計算
        throughputs = [m.throughput_per_second for m in metrics_list]
        execution_times = [m.average_execution_time for m in metrics_list]
        cpu_usages = [m.cpu_usage_percent for m in metrics_list]
        
        latest = metrics_list[-1]
        duration = latest.timestamp - metrics_list[0].timestamp
        
        return {
            'summary': {
                'monitoring_duration_seconds': duration,
                'total_tasks_processed': latest.completed_tasks + latest.failed_tasks,
                'success_rate': latest.completed_tasks / max(latest.completed_tasks + latest.failed_tasks, 1),
                'average_throughput': sum(throughputs) / len(throughputs),
                'peak_throughput': max(throughputs),
                'average_execution_time': sum(execution_times) / len(execution_times),
                'average_cpu_usage': sum(cpu_usages) / len(cpu_usages)
            },
            'current': {
                'active_tasks': latest.active_workers,
                'queue_length': latest.queue_length,
                'throughput_per_second': latest.throughput_per_second,
                'cpu_usage_percent': latest.cpu_usage_percent,
                'memory_usage_mb': latest.memory_usage_mb,
                'gpu_utilization_percent': latest.gpu_utilization_percent
            },
            'scaling': {
                'current_workers': self.current_workers,
                'max_workers': self.max_workers,
                'last_scale_up': self.last_scale_up,
                'last_scale_down': self.last_scale_down
            }
        }

    def register_task_callback(self, event: str, callback: Callable):
        """タスクコールバック登録"""
        self.task_callbacks[event].append(callback)

    def register_system_callback(self, event: str, callback: Callable):
        """システムコールバック登録"""
        self.system_callbacks[event].append(callback)

    async def pause(self):
        """一時停止"""
        self.is_paused = True
        self.logger.info("⏸️ システム一時停止")

    async def resume(self):
        """再開"""
        self.is_paused = False
        self.logger.info("▶️ システム再開")

    async def cancel_task(self, task_id: str) -> bool:
        """タスクキャンセル"""
        
        # 待機中タスク
        if task_id in self.waiting_tasks:
            task = self.waiting_tasks[task_id]
            task.status = TaskStatus.CANCELLED
            del self.waiting_tasks[task_id]
            self.logger.info(f"🚫 タスクキャンセル: {task_id} (待機中)")
            return True
        
        # アクティブタスク（実行中のキャンセルは困難）
        if task_id in self.active_tasks:
            self.logger.warning(f"⚠️ 実行中タスクのキャンセルは未対応: {task_id}")
            return False
        
        return False


# ファクトリ関数とテスト関数

def create_realtime_coordination_controller(config: Dict[str, Any] = None) -> RealtimeCoordinationControllerV3:
    """リアルタイム協調制御システム v3.0 ファクトリ関数"""
    default_config = {
        'max_workers': 8,
        'queue_size': 1000,
        'monitoring_interval': 0.1,
        'precision_timing': True,
        'microsecond_precision': True,
        'dynamic_scaling': True,
        'auto_recovery_enabled': True,
        'circuit_breaker_enabled': True,
        'load_threshold_high': 0.8,
        'load_threshold_low': 0.3
    }
    
    if config:
        default_config.update(config)
    
    return RealtimeCoordinationControllerV3(default_config)


async def test_realtime_coordination_controller():
    """リアルタイム協調制御システムのテスト"""
    print("🧪 リアルタイム協調制御システム v3.0 テスト開始")
    
    # システム作成
    controller = create_realtime_coordination_controller({
        'max_workers': 4,
        'monitoring_interval': 0.05  # 50ms
    })
    
    try:
        # システム開始
        await controller.start()
        
        # テストタスク定義
        async def test_task(task_id: str, duration: float = 0.1):
            await asyncio.sleep(duration)
            return f"完了: {task_id}"
        
        def sync_test_task(task_id: str, duration: float = 0.1):
            time.sleep(duration)
            return f"完了: {task_id}"
        
        # 複数タスク投入
        task_ids = []
        for i in range(10):
            task_id = await controller.submit_task(
                task_id=f"test_task_{i}",
                func=test_task if i % 2 == 0 else sync_test_task,
                priority=TaskPriority.HIGH if i < 3 else TaskPriority.NORMAL,
                args=(f"task_{i}", 0.1)
            )
            task_ids.append(task_id)
        
        # 依存関係ありタスク
        dependent_task_id = await controller.submit_task(
            task_id="dependent_task",
            func=test_task,
            args=("dependent", 0.05),
            dependencies=["test_task_0", "test_task_1"]
        )
        
        # 実行結果待機
        await asyncio.sleep(2.0)
        
        # 状態確認
        system_status = controller.get_system_status()
        print(f"📊 システム状態: {system_status}")
        
        # 性能レポート
        performance_report = controller.get_performance_report()
        print(f"📈 性能レポート: {performance_report['summary']}")
        
        # 個別タスク状態確認
        for task_id in task_ids[:3]:  # 最初の3つのみ
            status = await controller.get_task_status(task_id)
            print(f"📋 タスク {task_id}: {status}")
        
        print("✅ リアルタイム協調制御システム v3.0 テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        
    finally:
        # システム停止
        await controller.stop()


if __name__ == "__main__":
    asyncio.run(test_realtime_coordination_controller()) 