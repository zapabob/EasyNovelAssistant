# -*- coding: utf-8 -*-
"""
統合システムテスト v3.0 (Integrated System Test v3.0)
メモリ効率化・リアルタイム協調制御・NKAT理論統合　総合連携テスト

テスト対象:
1. メモリ効率化システム v3.0
2. リアルタイム協調制御システム v3.0  
3. NKAT理論統合準備システム v3.0
4. システム間連携・性能統合
"""

import asyncio
import time
import threading
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Callable
from dataclasses import dataclass
import gc

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_dir = os.path.join(project_root, "src")
sys.path.insert(0, src_dir)

# テスト対象システム
try:
    from optimization.memory_efficiency_system_v3 import create_memory_efficiency_system
    from integration.realtime_coordination_controller_v3 import create_realtime_coordination_controller, TaskPriority
    from nkat.nkat_integration_preparation_v3 import create_nkat_integration_system, NKATCharacterArchetype
    from utils.repetition_suppressor_v3 import AdvancedRepetitionSuppressorV3
    SYSTEMS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ システムインポートエラー: {e}")
    SYSTEMS_AVAILABLE = False


@dataclass
class IntegrationTestResult:
    """統合テスト結果"""
    test_name: str
    success: bool
    execution_time: float
    details: Dict[str, Any]
    error_message: str = ""


class IntegratedSystemTestV3:
    """
    統合システムテスト v3.0
    3システム連携・性能統合検証
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # テスト設定
        self.test_duration = self.config.get('test_duration', 30.0)  # 30秒
        self.load_test_tasks = self.config.get('load_test_tasks', 50)
        self.memory_stress_mb = self.config.get('memory_stress_mb', 100.0)
        self.enable_detailed_logging = self.config.get('enable_detailed_logging', True)
        
        # システムインスタンス
        self.memory_system = None
        self.coordination_controller = None
        self.nkat_system = None
        self.repetition_suppressor = None
        
        # テスト結果
        self.test_results: List[IntegrationTestResult] = []
        self.integration_stats = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'total_execution_time': 0.0,
            'memory_efficiency_gain': 0.0,
            'coordination_performance': 0.0,
            'nkat_coherence_score': 0.0
        }
        
        # ログ設定
        self.logger = self._setup_logging()
        
        print(f"🧪 統合システムテスト v3.0 初期化")
        print(f"   ├─ テスト時間: {self.test_duration}秒")
        print(f"   ├─ 負荷テストタスク数: {self.load_test_tasks}")
        print(f"   ├─ メモリストレス: {self.memory_stress_mb}MB")
        print(f"   └─ システム利用可能: {'有効' if SYSTEMS_AVAILABLE else '無効'}")

    def _setup_logging(self) -> logging.Logger:
        """ログ設定"""
        logger = logging.getLogger('IntegratedTestV3')
        logger.setLevel(logging.INFO if self.enable_detailed_logging else logging.WARNING)
        
        if not logger.handlers:
            # ファイルハンドラー
            log_dir = Path("logs/integration_tests")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp_str = time.strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"integration_test_{timestamp_str}.log"
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            console_handler = logging.StreamHandler()
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger

    async def initialize_systems(self) -> bool:
        """システム初期化"""
        
        if not SYSTEMS_AVAILABLE:
            self.logger.error("❌ 必要なシステムが利用できません")
            return False
        
        try:
            self.logger.info("🚀 統合システム初期化開始")
            
            # 1. メモリ効率化システム
            self.memory_system = create_memory_efficiency_system({
                'monitoring_interval': 0.5,
                'warning_threshold_percent': 80.0,
                'rtx3080_optimization': True
            })
            
            # 2. リアルタイム協調制御システム
            self.coordination_controller = create_realtime_coordination_controller({
                'max_workers': 6,
                'monitoring_interval': 0.05,
                'dynamic_scaling': True
            })
            
            # 3. NKAT理論統合システム
            self.nkat_system = create_nkat_integration_system({
                'emotion_update_interval': 0.2,
                'pattern_recognition_threshold': 0.7
            })
            
            # 4. 反復抑制システム
            self.repetition_suppressor = AdvancedRepetitionSuppressorV3({
                'kansai_mode': True,
                'learning_enabled': True
            })
            
            # システム連携設定
            await self.nkat_system.integrate_with_systems(
                coordination_controller=self.coordination_controller,
                memory_system=self.memory_system,
                repetition_suppressor=self.repetition_suppressor
            )
            
            # システム開始
            self.memory_system.start_monitoring()
            await self.coordination_controller.start()
            
            self.logger.info("✅ 統合システム初期化完了")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ システム初期化エラー: {e}")
            return False

    async def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """包括的テストスイート実行"""
        
        self.logger.info("🎯 包括的テストスイート開始")
        start_time = time.time()
        
        # システム初期化
        if not await self.initialize_systems():
            return {'error': 'システム初期化失敗'}
        
        try:
            # テスト1: 基本機能テスト
            await self._test_basic_functionality()
            
            # テスト2: システム連携テスト
            await self._test_system_integration()
            
            # テスト3: 負荷テスト
            await self._test_load_performance()
            
            # テスト4: メモリ効率テスト
            await self._test_memory_efficiency()
            
            # テスト5: NKAT理論テスト
            await self._test_nkat_theory_integration()
            
            # テスト6: エラー回復テスト
            await self._test_error_recovery()
            
            # 統計計算
            self._calculate_final_statistics()
            
            total_time = time.time() - start_time
            
            # 最終レポート生成
            final_report = self._generate_final_report(total_time)
            
            self.logger.info(f"🏁 テストスイート完了 ({total_time:.2f}秒)")
            return final_report
            
        except Exception as e:
            self.logger.error(f"❌ テストスイートエラー: {e}")
            return {'error': str(e)}
            
        finally:
            await self._cleanup_systems()

    async def _test_basic_functionality(self):
        """基本機能テスト"""
        
        self.logger.info("📋 基本機能テスト開始")
        
        # メモリシステム基本テスト
        result = await self._run_test("memory_basic", self._test_memory_basic)
        self.test_results.append(result)
        
        # 協調制御基本テスト
        result = await self._run_test("coordination_basic", self._test_coordination_basic)
        self.test_results.append(result)
        
        # NKAT基本テスト
        result = await self._run_test("nkat_basic", self._test_nkat_basic)
        self.test_results.append(result)

    async def _test_memory_basic(self) -> Dict[str, Any]:
        """メモリシステム基本テスト"""
        
        # メモリ情報取得
        memory_info = self.memory_system.get_current_memory_info()
        
        # 強制クリーンアップテスト
        cleanup_result = self.memory_system.force_memory_cleanup()
        
        return {
            'memory_monitoring': memory_info.get('monitoring_active', False),
            'cleanup_successful': cleanup_result.get('success', False),
            'memory_recovered_mb': cleanup_result.get('recovered_mb', 0.0),
            'rtx3080_enabled': memory_info.get('gpu_allocated_mb') is not None
        }

    async def _test_coordination_basic(self) -> Dict[str, Any]:
        """協調制御基本テスト"""
        
        # テストタスク定義
        async def simple_task(task_id: str):
            await asyncio.sleep(0.1)
            return f"完了: {task_id}"
        
        # タスク投入
        task_id = await self.coordination_controller.submit_task(
            task_id="basic_test_task",
            func=simple_task,
            args=("basic_test",),
            priority=TaskPriority.HIGH
        )
        
        # 実行待機
        await asyncio.sleep(0.5)
        
        # 状態確認
        task_status = await self.coordination_controller.get_task_status(task_id)
        system_status = self.coordination_controller.get_system_status()
        
        return {
            'task_submitted': task_id is not None,
            'task_completed': task_status and task_status.get('status') == 'COMPLETED',
            'system_running': system_status.get('is_running', False),
            'workers_active': system_status.get('current_workers', 0) > 0
        }

    async def _test_nkat_basic(self) -> Dict[str, Any]:
        """NKAT基本テスト"""
        
        # テストキャラクター作成
        profile = self.nkat_system.create_character_profile(
            character_id="test_character",
            archetype=NKATCharacterArchetype.INNOCENT
        )
        
        # テキスト処理
        test_text = "おはようございます！今日もええ天気やなあ♪"
        processed_text, result_info = await self.nkat_system.process_text_with_nkat(
            test_text, "test_character"
        )
        
        return {
            'character_created': profile is not None,
            'text_processed': processed_text != test_text or len(processed_text) > 0,
            'coherence_score': result_info.get('coherence_score', 0.0),
            'processing_time': result_info.get('processing_time', 0.0),
            'emotion_detected': 'character_emotion' in result_info
        }

    async def _test_system_integration(self):
        """システム連携テスト"""
        
        self.logger.info("🔗 システム連携テスト開始")
        
        result = await self._run_test("integration_flow", self._test_integration_flow)
        self.test_results.append(result)

    async def _test_integration_flow(self) -> Dict[str, Any]:
        """統合フロー テスト"""
        
        # 統合処理タスク定義
        async def integrated_processing_task(text: str, character_id: str):
            # 1. NKAT処理
            processed_text, nkat_info = await self.nkat_system.process_text_with_nkat(
                text, character_id
            )
            
            # 2. 反復抑制処理  
            if self.repetition_suppressor:
                final_text, suppression_info = self.repetition_suppressor.suppress_repetitions_with_debug_v3(
                    processed_text, character_id
                )
            else:
                final_text = processed_text
                suppression_info = {}
            
            return {
                'original_text': text,
                'nkat_processed': processed_text,
                'final_text': final_text,
                'nkat_info': nkat_info,
                'suppression_info': suppression_info
            }
        
        # キャラクター準備
        self.nkat_system.create_character_profile(
            character_id="integration_test_char",
            archetype=NKATCharacterArchetype.HERO
        )
        
        # 統合タスク投入
        task_id = await self.coordination_controller.submit_task(
            task_id="integration_task",
            func=integrated_processing_task,
            args=("今日はええ天気やなあ！戦いに行くで！", "integration_test_char"),
            priority=TaskPriority.HIGH
        )
        
        # 実行待機
        await asyncio.sleep(1.0)
        
        # 結果確認
        task_status = await self.coordination_controller.get_task_status(task_id)
        
        return {
            'integration_task_completed': task_status and task_status.get('status') == 'COMPLETED',
            'processing_result': task_status.get('result') if task_status else None,
            'coordination_successful': task_id is not None,
            'memory_stable': self.memory_system.get_current_memory_info().get('system_usage_percent', 100) < 90
        }

    async def _test_load_performance(self):
        """負荷性能テスト"""
        
        self.logger.info("⚡ 負荷性能テスト開始")
        
        result = await self._run_test("load_performance", self._test_high_load)
        self.test_results.append(result)

    async def _test_high_load(self) -> Dict[str, Any]:
        """高負荷テスト"""
        
        start_time = time.time()
        
        # 複数のNKATキャラクター作成
        characters = []
        for i in range(5):
            char_id = f"load_test_char_{i}"
            archetype = list(NKATCharacterArchetype)[i % len(NKATCharacterArchetype)]
            self.nkat_system.create_character_profile(char_id, archetype)
            characters.append(char_id)
        
        # 大量タスク投入
        task_ids = []
        test_texts = [
            "おはようございます！",
            "今日もええ天気やなあ♪",
            "頑張って戦うで！",
            "ちょっと疲れたわ…",
            "でも負けへんで！"
        ]
        
        for i in range(self.load_test_tasks):
            text = test_texts[i % len(test_texts)]
            character_id = characters[i % len(characters)]
            
            task_id = await self.coordination_controller.submit_task(
                task_id=f"load_task_{i}",
                func=self._simple_nkat_processing,
                args=(text, character_id),
                priority=TaskPriority.NORMAL
            )
            task_ids.append(task_id)
        
        # 完了待機
        completed_tasks = 0
        timeout = start_time + 20.0  # 20秒タイムアウト
        
        while completed_tasks < len(task_ids) and time.time() < timeout:
            completed_count = 0
            for task_id in task_ids:
                status = await self.coordination_controller.get_task_status(task_id)
                if status and status.get('status') in ['COMPLETED', 'FAILED']:
                    completed_count += 1
            
            completed_tasks = completed_count
            await asyncio.sleep(0.1)
        
        execution_time = time.time() - start_time
        success_rate = completed_tasks / len(task_ids)
        throughput = completed_tasks / execution_time
        
        return {
            'total_tasks': len(task_ids),
            'completed_tasks': completed_tasks,
            'success_rate': success_rate,
            'execution_time': execution_time,
            'throughput_per_second': throughput,
            'performance_acceptable': success_rate > 0.8 and throughput > 1.0
        }

    async def _simple_nkat_processing(self, text: str, character_id: str) -> str:
        """簡易NKAT処理"""
        processed_text, _ = await self.nkat_system.process_text_with_nkat(text, character_id)
        return processed_text

    async def _test_memory_efficiency(self):
        """メモリ効率テスト"""
        
        self.logger.info("💾 メモリ効率テスト開始")
        
        result = await self._run_test("memory_efficiency", self._test_memory_stress)
        self.test_results.append(result)

    async def _test_memory_stress(self) -> Dict[str, Any]:
        """メモリストレステスト"""
        
        # 初期メモリ状態
        initial_memory = self.memory_system.get_current_memory_info()
        initial_usage = initial_memory.get('process_memory_mb', 0)
        
        # メモリ負荷生成
        stress_data = []
        for i in range(int(self.memory_stress_mb)):
            stress_data.append([0] * 1000)  # 約1MBのデータ
        
        # 負荷後のメモリ状態
        peak_memory = self.memory_system.get_current_memory_info()
        peak_usage = peak_memory.get('process_memory_mb', 0)
        
        # メモリクリーンアップ
        cleanup_result = self.memory_system.force_memory_cleanup()
        
        # 解放後のメモリ状態
        del stress_data
        gc.collect()
        await asyncio.sleep(1.0)
        
        final_memory = self.memory_system.get_current_memory_info()
        final_usage = final_memory.get('process_memory_mb', 0)
        
        memory_recovered = peak_usage - final_usage
        efficiency_ratio = memory_recovered / max(peak_usage - initial_usage, 1.0)
        
        return {
            'initial_memory_mb': initial_usage,
            'peak_memory_mb': peak_usage,
            'final_memory_mb': final_usage,
            'memory_increase_mb': peak_usage - initial_usage,
            'memory_recovered_mb': memory_recovered,
            'efficiency_ratio': efficiency_ratio,
            'cleanup_successful': cleanup_result.get('success', False),
            'memory_management_effective': efficiency_ratio > 0.5
        }

    async def _test_nkat_theory_integration(self):
        """NKAT理論統合テスト"""
        
        self.logger.info("🧠 NKAT理論統合テスト開始")
        
        result = await self._run_test("nkat_theory", self._test_nkat_theory_depth)
        self.test_results.append(result)

    async def _test_nkat_theory_depth(self) -> Dict[str, Any]:
        """NKAT理論深度テスト"""
        
        # 複数の原型でキャラクター作成
        test_characters = [
            ("innocent_char", NKATCharacterArchetype.INNOCENT),
            ("sage_char", NKATCharacterArchetype.SAGE),
            ("hero_char", NKATCharacterArchetype.HERO)
        ]
        
        for char_id, archetype in test_characters:
            self.nkat_system.create_character_profile(char_id, archetype)
        
        # 感情表現テスト
        emotion_tests = [
            ("今日はめっちゃ嬉しいわ！♪", "innocent_char", "joy"),
            ("深く考察すべき事案である。", "sage_char", "contemplation"),
            ("敵を倒すために戦うんや！", "hero_char", "determination")
        ]
        
        coherence_scores = []
        processing_times = []
        
        for text, char_id, expected_emotion in emotion_tests:
            start_time = time.time()
            
            processed_text, result_info = await self.nkat_system.process_text_with_nkat(
                text, char_id
            )
            
            processing_time = time.time() - start_time
            processing_times.append(processing_time)
            
            coherence_score = result_info.get('coherence_score', 0.0)
            coherence_scores.append(coherence_score)
        
        avg_coherence = sum(coherence_scores) / len(coherence_scores)
        avg_processing_time = sum(processing_times) / len(processing_times)
        
        # 性能レポート取得
        nkat_performance = self.nkat_system.get_performance_report()
        
        return {
            'characters_tested': len(test_characters),
            'emotion_tests_completed': len(emotion_tests),
            'average_coherence_score': avg_coherence,
            'average_processing_time': avg_processing_time,
            'theory_integration_successful': avg_coherence > 0.7,
            'performance_acceptable': avg_processing_time < 0.1,
            'nkat_performance_summary': nkat_performance.get('summary', {})
        }

    async def _test_error_recovery(self):
        """エラー回復テスト"""
        
        self.logger.info("🛡️ エラー回復テスト開始")
        
        result = await self._run_test("error_recovery", self._test_system_resilience)
        self.test_results.append(result)

    async def _test_system_resilience(self) -> Dict[str, Any]:
        """システム復元力テスト"""
        
        # エラーを発生させるタスク
        async def error_task():
            raise Exception("テスト例外")
        
        # 正常なタスク
        async def normal_task(task_id: str):
            await asyncio.sleep(0.1)
            return f"正常完了: {task_id}"
        
        # エラータスクと正常タスクを混在投入
        task_ids = []
        
        # エラータスク投入
        for i in range(3):
            task_id = await self.coordination_controller.submit_task(
                task_id=f"error_task_{i}",
                func=error_task,
                priority=TaskPriority.NORMAL
            )
            task_ids.append(task_id)
        
        # 正常タスク投入
        for i in range(7):
            task_id = await self.coordination_controller.submit_task(
                task_id=f"normal_task_{i}",
                func=normal_task,
                args=(f"normal_{i}",),
                priority=TaskPriority.NORMAL
            )
            task_ids.append(task_id)
        
        # 実行待機
        await asyncio.sleep(2.0)
        
        # 結果確認
        completed_count = 0
        failed_count = 0
        
        for task_id in task_ids:
            status = await self.coordination_controller.get_task_status(task_id)
            if status:
                if status.get('status') == 'COMPLETED':
                    completed_count += 1
                elif status.get('status') == 'FAILED':
                    failed_count += 1
        
        # システム状態確認
        system_status = self.coordination_controller.get_system_status()
        
        return {
            'total_tasks': len(task_ids),
            'completed_tasks': completed_count,
            'failed_tasks': failed_count,
            'system_still_running': system_status.get('is_running', False),
            'error_recovery_successful': completed_count >= 7 and failed_count >= 3,
            'resilience_acceptable': system_status.get('is_running', False) and completed_count > 0
        }

    async def _run_test(self, test_name: str, test_func: Callable) -> IntegrationTestResult:
        """テスト実行ヘルパー"""
        
        start_time = time.time()
        
        try:
            details = await test_func()
            execution_time = time.time() - start_time
            
            # 成功判定（詳細結果に基づく）
            success = self._evaluate_test_success(test_name, details)
            
            result = IntegrationTestResult(
                test_name=test_name,
                success=success,
                execution_time=execution_time,
                details=details
            )
            
            status = "✅" if success else "❌"
            self.logger.info(f"{status} {test_name}: {execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            result = IntegrationTestResult(
                test_name=test_name,
                success=False,
                execution_time=execution_time,
                details={},
                error_message=str(e)
            )
            
            self.logger.error(f"❌ {test_name} エラー: {e}")
            return result

    def _evaluate_test_success(self, test_name: str, details: Dict[str, Any]) -> bool:
        """テスト成功判定"""
        
        success_criteria = {
            'memory_basic': details.get('memory_monitoring', False) and details.get('cleanup_successful', False),
            'coordination_basic': details.get('task_completed', False) and details.get('system_running', False),
            'nkat_basic': details.get('character_created', False) and details.get('coherence_score', 0) > 0.5,
            'integration_flow': details.get('integration_task_completed', False) and details.get('memory_stable', False),
            'load_performance': details.get('performance_acceptable', False),
            'memory_efficiency': details.get('memory_management_effective', False),
            'nkat_theory': details.get('theory_integration_successful', False),
            'error_recovery': details.get('error_recovery_successful', False) and details.get('resilience_acceptable', False)
        }
        
        return success_criteria.get(test_name, False)

    def _calculate_final_statistics(self):
        """最終統計計算"""
        
        self.integration_stats['total_tests'] = len(self.test_results)
        self.integration_stats['passed_tests'] = sum(1 for r in self.test_results if r.success)
        self.integration_stats['failed_tests'] = self.integration_stats['total_tests'] - self.integration_stats['passed_tests']
        self.integration_stats['total_execution_time'] = sum(r.execution_time for r in self.test_results)
        
        # 個別性能指標
        for result in self.test_results:
            if result.test_name == 'memory_efficiency' and result.success:
                self.integration_stats['memory_efficiency_gain'] = result.details.get('efficiency_ratio', 0.0)
            elif result.test_name == 'load_performance' and result.success:
                self.integration_stats['coordination_performance'] = result.details.get('throughput_per_second', 0.0)
            elif result.test_name == 'nkat_theory' and result.success:
                self.integration_stats['nkat_coherence_score'] = result.details.get('average_coherence_score', 0.0)

    def _generate_final_report(self, total_time: float) -> Dict[str, Any]:
        """最終レポート生成"""
        
        success_rate = self.integration_stats['passed_tests'] / max(self.integration_stats['total_tests'], 1)
        
        return {
            'summary': {
                'test_suite_version': '3.0',
                'total_execution_time': total_time,
                'success_rate': success_rate,
                'systems_tested': ['Memory Efficiency v3.0', 'Realtime Coordination v3.0', 'NKAT Integration v3.0'],
                'overall_status': '✅ 成功' if success_rate >= 0.8 else '⚠️ 部分成功' if success_rate >= 0.5 else '❌ 失敗'
            },
            'statistics': self.integration_stats,
            'detailed_results': [
                {
                    'test_name': result.test_name,
                    'success': result.success,
                    'execution_time': result.execution_time,
                    'key_metrics': self._extract_key_metrics(result)
                }
                for result in self.test_results
            ],
            'performance_metrics': {
                'memory_efficiency_gain': self.integration_stats['memory_efficiency_gain'],
                'coordination_throughput': self.integration_stats['coordination_performance'],
                'nkat_coherence_score': self.integration_stats['nkat_coherence_score']
            },
            'recommendations': self._generate_recommendations(success_rate)
        }

    def _extract_key_metrics(self, result: IntegrationTestResult) -> Dict[str, Any]:
        """主要メトリクス抽出"""
        
        key_metrics = {}
        
        if result.test_name == 'memory_basic':
            key_metrics = {
                'memory_recovered_mb': result.details.get('memory_recovered_mb', 0),
                'rtx3080_enabled': result.details.get('rtx3080_enabled', False)
            }
        elif result.test_name == 'load_performance':
            key_metrics = {
                'throughput_per_second': result.details.get('throughput_per_second', 0),
                'success_rate': result.details.get('success_rate', 0)
            }
        elif result.test_name == 'nkat_theory':
            key_metrics = {
                'average_coherence_score': result.details.get('average_coherence_score', 0),
                'processing_time': result.details.get('average_processing_time', 0)
            }
        
        return key_metrics

    def _generate_recommendations(self, success_rate: float) -> List[str]:
        """改善推奨事項生成"""
        
        recommendations = []
        
        if success_rate < 0.8:
            recommendations.append("システム統合の安定性向上が必要")
            
        if self.integration_stats['memory_efficiency_gain'] < 0.5:
            recommendations.append("メモリ効率化アルゴリズムの最適化を推奨")
            
        if self.integration_stats['coordination_performance'] < 2.0:
            recommendations.append("協調制御システムのスループット向上が必要")
            
        if self.integration_stats['nkat_coherence_score'] < 0.7:
            recommendations.append("NKAT理論の一貫性アルゴリズム改善を推奨")
        
        if not recommendations:
            recommendations.append("全システムが期待される性能を達成しています")
        
        return recommendations

    async def _cleanup_systems(self):
        """システムクリーンアップ"""
        
        try:
            if self.coordination_controller:
                await self.coordination_controller.stop()
            
            if self.memory_system:
                self.memory_system.shutdown()
            
            if self.nkat_system:
                await self.nkat_system.shutdown()
                
            self.logger.info("🧹 システムクリーンアップ完了")
            
        except Exception as e:
            self.logger.error(f"クリーンアップエラー: {e}")


# メイン実行関数

async def run_integrated_system_test():
    """統合システムテスト実行"""
    
    print("🚀 統合システムテスト v3.0 開始")
    print("=" * 60)
    
    # テストシステム作成
    test_system = IntegratedSystemTestV3({
        'test_duration': 30.0,
        'load_test_tasks': 30,
        'memory_stress_mb': 50.0
    })
    
    try:
        # 包括的テスト実行
        final_report = await test_system.run_comprehensive_test_suite()
        
        # 結果表示
        print("\n" + "=" * 60)
        print("📊 統合テスト結果")
        print("=" * 60)
        
        summary = final_report.get('summary', {})
        print(f"総合状態: {summary.get('overall_status', '不明')}")
        print(f"成功率: {summary.get('success_rate', 0):.1%}")
        print(f"実行時間: {summary.get('total_execution_time', 0):.2f}秒")
        
        print("\n📈 性能メトリクス:")
        metrics = final_report.get('performance_metrics', {})
        print(f"  メモリ効率向上: {metrics.get('memory_efficiency_gain', 0):.1%}")
        print(f"  協調制御スループット: {metrics.get('coordination_throughput', 0):.1f}タスク/秒")
        print(f"  NKAT一貫性スコア: {metrics.get('nkat_coherence_score', 0):.3f}")
        
        print("\n💡 推奨事項:")
        recommendations = final_report.get('recommendations', [])
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
        
        # 詳細結果保存
        await _save_test_report(final_report)
        
        print("\n✅ 統合システムテスト v3.0 完了")
        
    except Exception as e:
        print(f"\n❌ テストエラー: {e}")
        return False
    
    return True


async def _save_test_report(report: Dict[str, Any]):
    """テストレポート保存"""
    
    try:
        report_dir = Path("logs/integration_tests")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"integration_test_report_{timestamp_str}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📋 詳細レポート保存: {report_file}")
        
    except Exception as e:
        print(f"⚠️ レポート保存エラー: {e}")


if __name__ == "__main__":
    import sys
    
    if SYSTEMS_AVAILABLE:
        # 統合テスト実行
        success = asyncio.run(run_integrated_system_test())
        sys.exit(0 if success else 1)
    else:
        print("❌ 必要なシステムが利用できません")
        sys.exit(1) 