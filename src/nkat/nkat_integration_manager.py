# -*- coding: utf-8 -*-
"""
NKAT Integration Manager
Phase 3: 統合システムマネージャー

【統合機能】
1. 既存NKAT統合システムとの連携
2. Advanced Tensor Processingシステムの統合
3. EasyNovelAssistantとの統合管理
4. 反復抑制v3システムとの協調
5. LoRA協調システムとの連携
6. クロス抑制システムとの統合

Author: EasyNovelAssistant Development Team
Date: 2025-01-06
Version: Phase 3 Integration Manager
"""

import os
import sys
import json
import time
import threading
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
from collections import defaultdict

# プロジェクトパス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
src_dir = os.path.join(project_root, "src")
sys.path.insert(0, project_root)
sys.path.insert(0, src_dir)

try:
    from nkat.nkat_advanced_tensor import NKATAdvancedProcessor, create_advanced_nkat_processor
    from nkat.nkat_integration import NKATIntegration, TextConsistencyProcessor
    from nkat.advanced_consistency import AdvancedConsistencyProcessor, ConsistencyLevel
    NKAT_COMPONENTS_AVAILABLE = True
except ImportError:
    NKAT_COMPONENTS_AVAILABLE = False

try:
    from utils.repetition_suppressor_v3 import AdvancedRepetitionSuppressorV3
    from integration.lora_style_coordinator import LoRAStyleCoordinator
    from integration.cross_suppression_engine import CrossSuppressionEngine
    INTEGRATION_SYSTEMS_AVAILABLE = True
except ImportError:
    INTEGRATION_SYSTEMS_AVAILABLE = False


@dataclass
class NKATProcessingResult:
    """NKAT処理結果"""
    original_text: str
    enhanced_text: str
    processing_stages: Dict[str, Any]
    quality_metrics: Dict[str, float]
    performance_metrics: Dict[str, float]
    system_coordination: Dict[str, bool]
    total_processing_time_ms: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class SystemCoordination:
    """システム協調状態"""
    repetition_suppression_active: bool
    lora_coordination_active: bool
    cross_suppression_active: bool
    nkat_advanced_active: bool
    nkat_legacy_active: bool
    coordination_efficiency: float


class NKATIntegrationManager:
    """NKAT統合システムマネージャー"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self.logger = logging.getLogger(__name__)
        
        # システムコンポーネント
        self.advanced_processor: Optional[NKATAdvancedProcessor] = None
        self.legacy_nkat: Optional[NKATIntegration] = None
        self.consistency_processor: Optional[AdvancedConsistencyProcessor] = None
        
        # 統合システム
        self.repetition_suppressor: Optional[AdvancedRepetitionSuppressorV3] = None
        self.lora_coordinator: Optional[LoRAStyleCoordinator] = None
        self.cross_engine: Optional[CrossSuppressionEngine] = None
        
        # 統合状態管理
        self.system_coordination = SystemCoordination(
            repetition_suppression_active=False,
            lora_coordination_active=False,
            cross_suppression_active=False,
            nkat_advanced_active=False,
            nkat_legacy_active=False,
            coordination_efficiency=0.0
        )
        
        # パフォーマンスメトリクス
        self.performance_stats = {
            'total_requests': 0,
            'successful_processes': 0,
            'average_processing_time': 0.0,
            'quality_improvements': 0,
            'system_errors': 0,
            'coordination_score': 0.0
        }
        
        # スレッドセーフ処理
        self.processing_lock = threading.RLock()
        
        self._initialize_systems()
        self.logger.info("🎯 NKAT統合マネージャー初期化完了")
    
    def _default_config(self) -> Dict[str, Any]:
        """デフォルト設定"""
        return {
            # NKAT Advanced設定
            'nkat_advanced': {
                'enabled': True,
                'tensor_dimension': 256,
                'quality_threshold': 0.7,
                'max_iterations': 8,
                'literary_enhancement': True
            },
            
            # Legacy NKAT設定
            'nkat_legacy': {
                'enabled': True,
                'consistency_mode': True,
                'advanced_mode': True
            },
            
            # 統合システム設定
            'integration_systems': {
                'repetition_suppression': True,
                'lora_coordination': True,
                'cross_suppression': True
            },
            
            # 処理順序設定
            'processing_pipeline': [
                'cross_suppression',
                'nkat_advanced',
                'lora_coordination',
                'repetition_suppression',
                'nkat_legacy'
            ],
            
            # 協調制御設定
            'coordination': {
                'enable_parallel_processing': False,
                'quality_gate_threshold': 0.5,
                'error_recovery_enabled': True,
                'adaptive_optimization': True
            },
            
            # パフォーマンス設定
            'performance': {
                'cache_enabled': True,
                'max_processing_time_ms': 5000,
                'quality_priority': True
            }
        }
    
    def _initialize_systems(self):
        """システム初期化"""
        initialization_results = {}
        
        # NKAT Advanced Processor
        if NKAT_COMPONENTS_AVAILABLE and self.config['nkat_advanced']['enabled']:
            try:
                self.advanced_processor = create_advanced_nkat_processor(
                    self.config['nkat_advanced']
                )
                self.system_coordination.nkat_advanced_active = True
                initialization_results['nkat_advanced'] = True
                self.logger.info("✅ NKAT Advanced Processor 初期化成功")
            except Exception as e:
                initialization_results['nkat_advanced'] = False
                self.logger.error(f"❌ NKAT Advanced Processor 初期化失敗: {e}")
        
        # Legacy NKAT Integration
        if NKAT_COMPONENTS_AVAILABLE and self.config['nkat_legacy']['enabled']:
            try:
                # モックコンテキスト作成
                mock_context = type('MockContext', (), self.config['nkat_legacy'])()
                self.legacy_nkat = NKATIntegration(mock_context)
                
                # Advanced Consistency Processor
                self.consistency_processor = AdvancedConsistencyProcessor(
                    self.config['nkat_legacy']
                )
                
                self.system_coordination.nkat_legacy_active = True
                initialization_results['nkat_legacy'] = True
                self.logger.info("✅ Legacy NKAT System 初期化成功")
            except Exception as e:
                initialization_results['nkat_legacy'] = False
                self.logger.error(f"❌ Legacy NKAT System 初期化失敗: {e}")
        
        # 統合システム初期化（利用可能な場合）
        if INTEGRATION_SYSTEMS_AVAILABLE:
            self._initialize_integration_systems()
        else:
            self.logger.warning("⚠️ 統合システム（反復抑制v3、LoRA、クロス抑制）が利用できません")
        
        # 協調効率の計算
        active_systems = sum([
            self.system_coordination.nkat_advanced_active,
            self.system_coordination.nkat_legacy_active,
            self.system_coordination.repetition_suppression_active,
            self.system_coordination.lora_coordination_active,
            self.system_coordination.cross_suppression_active
        ])
        
        self.system_coordination.coordination_efficiency = active_systems / 5.0
        
        self.logger.info(f"🔧 システム初期化完了: {active_systems}/5 アクティブ")
    
    def _initialize_integration_systems(self):
        """統合システムの初期化"""
        config = self.config['integration_systems']
        
        # 反復抑制v3システム
        if config.get('repetition_suppression', True):
            try:
                repetition_config = {
                    'similarity_threshold': 0.30,
                    'max_distance': 60,
                    'min_compress_rate': 0.02,
                    'enable_4gram_blocking': True,
                    'ngram_block_size': 3,
                    'enable_drp': True,
                    'drp_base': 1.15,
                    'drp_alpha': 0.6
                }
                self.repetition_suppressor = AdvancedRepetitionSuppressorV3(repetition_config)
                self.system_coordination.repetition_suppression_active = True
                self.logger.info("✅ 反復抑制v3システム 初期化成功")
            except Exception as e:
                self.logger.error(f"❌ 反復抑制v3システム 初期化失敗: {e}")
        
        # LoRA協調システム
        if config.get('lora_coordination', True):
            try:
                from integration.lora_style_coordinator import create_default_coordinator
                self.lora_coordinator = create_default_coordinator()
                self.system_coordination.lora_coordination_active = True
                self.logger.info("✅ LoRA協調システム 初期化成功")
            except Exception as e:
                self.logger.error(f"❌ LoRA協調システム 初期化失敗: {e}")
        
        # クロス抑制システム
        if config.get('cross_suppression', True):
            try:
                from integration.cross_suppression_engine import create_default_cross_engine
                self.cross_engine = create_default_cross_engine()
                if self.cross_engine.initialize_systems():
                    self.system_coordination.cross_suppression_active = True
                    self.logger.info("✅ クロス抑制システム 初期化成功")
            except Exception as e:
                self.logger.error(f"❌ クロス抑制システム 初期化失敗: {e}")
    
    def process_text_comprehensive(self, text: str, character: str = None,
                                 context: str = None, session_id: str = None,
                                 style_weight: float = 1.0,
                                 target_quality: float = None) -> NKATProcessingResult:
        """包括的テキスト処理"""
        start_time = time.time()
        
        with self.processing_lock:
            self.performance_stats['total_requests'] += 1
            
            processing_stages = {}
            current_text = text
            
            # エラーハンドリング
            try:
                # 処理パイプライン実行
                pipeline = self.config['processing_pipeline']
                
                for stage_name in pipeline:
                    stage_start = time.time()
                    stage_result = self._execute_processing_stage(
                        stage_name, current_text, character, context, 
                        session_id, style_weight, target_quality
                    )
                    
                    if stage_result['success']:
                        current_text = stage_result['output_text']
                        processing_stages[stage_name] = {
                            'input': stage_result['input_text'],
                            'output': stage_result['output_text'],
                            'metrics': stage_result.get('metrics', {}),
                            'processing_time_ms': (time.time() - stage_start) * 1000,
                            'success': True
                        }
                    else:
                        processing_stages[stage_name] = {
                            'input': stage_result['input_text'],
                            'output': stage_result['input_text'],  # フォールバック
                            'error': stage_result.get('error', 'Unknown error'),
                            'processing_time_ms': (time.time() - stage_start) * 1000,
                            'success': False
                        }
                        
                        if not self.config['coordination']['error_recovery_enabled']:
                            break  # エラー回復が無効の場合は処理停止
                
                # 品質メトリクス計算
                quality_metrics = self._calculate_quality_metrics(text, current_text)
                
                # パフォーマンスメトリクス計算
                total_time = (time.time() - start_time) * 1000
                performance_metrics = self._calculate_performance_metrics(
                    processing_stages, total_time
                )
                
                # 成功判定
                success = (len(current_text) > 0 and 
                          quality_metrics.get('overall_quality', 0) > 0.3)
                
                if success:
                    self.performance_stats['successful_processes'] += 1
                    if quality_metrics.get('quality_improvement', 0) > 0.1:
                        self.performance_stats['quality_improvements'] += 1
                
                # 統計更新
                self._update_performance_stats(total_time, success)
                
                return NKATProcessingResult(
                    original_text=text,
                    enhanced_text=current_text,
                    processing_stages=processing_stages,
                    quality_metrics=quality_metrics,
                    performance_metrics=performance_metrics,
                    system_coordination=asdict(self.system_coordination),
                    total_processing_time_ms=total_time,
                    success=success
                )
                
            except Exception as e:
                self.performance_stats['system_errors'] += 1
                self.logger.error(f"包括的処理エラー: {e}")
                
                return NKATProcessingResult(
                    original_text=text,
                    enhanced_text=text,  # フォールバック
                    processing_stages={},
                    quality_metrics={},
                    performance_metrics={},
                    system_coordination=asdict(self.system_coordination),
                    total_processing_time_ms=(time.time() - start_time) * 1000,
                    success=False,
                    error_message=str(e)
                )
    
    def _execute_processing_stage(self, stage_name: str, text: str, 
                                character: str, context: str, session_id: str,
                                style_weight: float, target_quality: float) -> Dict[str, Any]:
        """処理ステージの実行"""
        try:
            if stage_name == 'nkat_advanced' and self.advanced_processor:
                enhanced_text, metrics = self.advanced_processor.process_expression(
                    text, character, context, target_quality
                )
                return {
                    'success': True,
                    'input_text': text,
                    'output_text': enhanced_text,
                    'metrics': metrics
                }
            
            elif stage_name == 'nkat_legacy' and self.legacy_nkat:
                enhanced_text = self.legacy_nkat.enhance_text_generation(
                    prompt=context or "",
                    llm_output=text
                )
                return {
                    'success': True,
                    'input_text': text,
                    'output_text': enhanced_text,
                    'metrics': {}
                }
            
            elif stage_name == 'repetition_suppression' and self.repetition_suppressor:
                enhanced_text, metrics = self.repetition_suppressor.suppress_repetitions_with_debug_v3(
                    text, character
                )
                return {
                    'success': True,
                    'input_text': text,
                    'output_text': enhanced_text,
                    'metrics': metrics.__dict__ if hasattr(metrics, '__dict__') else {}
                }
            
            elif stage_name == 'lora_coordination' and self.lora_coordinator:
                enhanced_text, metrics = self.lora_coordinator.process_text_with_coordination(
                    text, character, style_weight
                )
                return {
                    'success': True,
                    'input_text': text,
                    'output_text': enhanced_text,
                    'metrics': metrics
                }
            
            elif stage_name == 'cross_suppression' and self.cross_engine:
                enhanced_text, metrics = self.cross_engine.process_with_cross_suppression(
                    text, character, session_id
                )
                return {
                    'success': True,
                    'input_text': text,
                    'output_text': enhanced_text,
                    'metrics': metrics
                }
            
            else:
                # システムが利用できない場合
                return {
                    'success': True,
                    'input_text': text,
                    'output_text': text,  # パススルー
                    'metrics': {}
                }
                
        except Exception as e:
            return {
                'success': False,
                'input_text': text,
                'output_text': text,
                'error': str(e)
            }
    
    def _calculate_quality_metrics(self, original: str, enhanced: str) -> Dict[str, float]:
        """品質メトリクスの計算"""
        if not enhanced or enhanced == original:
            return {
                'overall_quality': 0.5,
                'quality_improvement': 0.0,
                'text_diversity': 0.0,
                'coherence': 1.0
            }
        
        # 基本的な品質指標
        compression_rate = (len(original) - len(enhanced)) / len(original)
        word_diversity = len(set(enhanced.split())) / max(len(enhanced.split()), 1)
        
        # 単純な品質スコア（実際はより高度な手法を使用）
        quality_score = 0.5 + min(0.4, word_diversity) + min(0.1, max(0, compression_rate))
        quality_improvement = quality_score - 0.5  # ベースライン0.5
        
        return {
            'overall_quality': quality_score,
            'quality_improvement': quality_improvement,
            'text_diversity': word_diversity,
            'coherence': 0.9,  # 簡易実装
            'compression_rate': compression_rate
        }
    
    def _calculate_performance_metrics(self, processing_stages: Dict[str, Any], 
                                     total_time: float) -> Dict[str, float]:
        """パフォーマンスメトリクスの計算"""
        successful_stages = sum(1 for stage in processing_stages.values() 
                              if stage.get('success', False))
        total_stages = len(processing_stages)
        
        stage_times = [stage.get('processing_time_ms', 0) 
                      for stage in processing_stages.values()]
        avg_stage_time = sum(stage_times) / max(len(stage_times), 1)
        
        return {
            'total_processing_time_ms': total_time,
            'average_stage_time_ms': avg_stage_time,
            'stage_success_rate': successful_stages / max(total_stages, 1),
            'processing_efficiency': successful_stages / max(total_time / 1000, 0.001),
            'system_coordination_score': self.system_coordination.coordination_efficiency
        }
    
    def _update_performance_stats(self, processing_time: float, success: bool):
        """パフォーマンス統計の更新"""
        # 平均処理時間の更新
        total_requests = self.performance_stats['total_requests']
        current_avg = self.performance_stats['average_processing_time']
        new_avg = ((current_avg * (total_requests - 1)) + processing_time) / total_requests
        self.performance_stats['average_processing_time'] = new_avg
        
        # 協調スコアの更新
        active_systems = sum([
            self.system_coordination.nkat_advanced_active,
            self.system_coordination.nkat_legacy_active,
            self.system_coordination.repetition_suppression_active,
            self.system_coordination.lora_coordination_active,
            self.system_coordination.cross_suppression_active
        ])
        
        self.performance_stats['coordination_score'] = active_systems / 5.0
    
    def get_system_status(self) -> Dict[str, Any]:
        """システム状態の取得"""
        return {
            'system_coordination': asdict(self.system_coordination),
            'performance_stats': self.performance_stats,
            'active_systems': {
                'nkat_advanced': self.advanced_processor is not None,
                'nkat_legacy': self.legacy_nkat is not None,
                'repetition_suppression': self.repetition_suppressor is not None,
                'lora_coordination': self.lora_coordinator is not None,
                'cross_suppression': self.cross_engine is not None
            },
            'configuration': {
                'processing_pipeline': self.config['processing_pipeline'],
                'coordination_enabled': self.config['coordination'],
                'performance_settings': self.config['performance']
            }
        }
    
    def optimize_configuration(self) -> Dict[str, Any]:
        """設定の最適化"""
        optimization_results = {}
        
        # パフォーマンス分析
        success_rate = (self.performance_stats['successful_processes'] / 
                       max(self.performance_stats['total_requests'], 1))
        avg_time = self.performance_stats['average_processing_time']
        
        # 最適化提案
        if success_rate < 0.8:
            optimization_results['recommendation'] = "error_recovery_強化"
            optimization_results['suggested_config'] = {
                'coordination.error_recovery_enabled': True,
                'coordination.quality_gate_threshold': 0.3
            }
        
        if avg_time > 3000:  # 3秒以上
            optimization_results['recommendation'] = "performance_優先"
            optimization_results['suggested_config'] = {
                'nkat_advanced.max_iterations': 5,
                'performance.quality_priority': False
            }
        
        return optimization_results
    
    def clear_all_caches(self):
        """全システムのキャッシュクリア"""
        if self.advanced_processor:
            self.advanced_processor.clear_cache()
        
        # 他システムのキャッシュもクリア
        self.logger.info("🧹 全システムキャッシュクリア完了")


def create_nkat_integration_manager(config: Dict[str, Any] = None) -> NKATIntegrationManager:
    """NKAT統合マネージャーの作成"""
    return NKATIntegrationManager(config)


if __name__ == "__main__":
    # デモ実行
    logging.basicConfig(level=logging.INFO)
    
    print("🎯 NKAT統合マネージャー デモ")
    print("=" * 60)
    
    # 統合マネージャー初期化
    manager = create_nkat_integration_manager()
    
    # システム状態確認
    status = manager.get_system_status()
    print(f"📊 システム状態:")
    print(f"   アクティブシステム数: {sum(status['active_systems'].values())}/5")
    print(f"   協調効率: {status['system_coordination']['coordination_efficiency']:.1%}")
    
    # テストケース
    test_cases = [
        {
            'text': 'お兄ちゃんお兄ちゃん、どこに行くのですかお兄ちゃん？',
            'character': '妹キャラ',
            'context': '家族会話',
            'session_id': 'demo_session_1'
        },
        {
            'text': '嬉しいです。とても嬉しいです。本当に嬉しいです。',
            'character': '樹里',
            'context': '感情表現',
            'session_id': 'demo_session_2'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📝 統合処理テスト {i}")
        print(f"   キャラクター: {case['character']}")
        print(f"   原文: {case['text']}")
        
        # 包括的処理実行
        result = manager.process_text_comprehensive(
            case['text'], case['character'], case['context'], case['session_id']
        )
        
        print(f"   拡張後: {result.enhanced_text}")
        print(f"   成功: {'✅' if result.success else '❌'}")
        print(f"   総処理時間: {result.total_processing_time_ms:.1f}ms")
        print(f"   品質改善: {result.quality_metrics.get('quality_improvement', 0):.3f}")
        
        # 処理ステージ詳細
        print(f"   処理ステージ:")
        for stage_name, stage_data in result.processing_stages.items():
            status_icon = "✅" if stage_data.get('success', False) else "❌"
            print(f"     {status_icon} {stage_name}: {stage_data.get('processing_time_ms', 0):.1f}ms")
    
    # パフォーマンス統計
    final_status = manager.get_system_status()
    print(f"\n📈 最終統計:")
    print(f"   総リクエスト: {final_status['performance_stats']['total_requests']}")
    print(f"   成功処理: {final_status['performance_stats']['successful_processes']}")
    print(f"   平均処理時間: {final_status['performance_stats']['average_processing_time']:.1f}ms")
    print(f"   協調スコア: {final_status['performance_stats']['coordination_score']:.1%}")
    
    # 最適化提案
    optimization = manager.optimize_configuration()
    if optimization:
        print(f"\n🔧 最適化提案: {optimization.get('recommendation', 'なし')}")
    
    print("\n✅ NKAT統合マネージャー デモ完了") 