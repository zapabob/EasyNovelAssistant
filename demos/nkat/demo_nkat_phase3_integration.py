# -*- coding: utf-8 -*-
"""
NKAT Phase 3 統合テストデモ
高度な非可換テンソル処理システムと統合マネージャーの検証

【テスト項目】
1. NKAT Advanced Tensor Processing System
2. NKAT Integration Manager 
3. 既存システムとの統合確認
4. パフォーマンスベンチマーク
5. 品質改善測定

Author: EasyNovelAssistant Development Team
Date: 2025-01-06
Version: Phase 3 Integration Test
"""

import os
import sys
import json
import time
import logging
from typing import Dict, List, Any
from collections import defaultdict

# プロジェクトパス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from nkat.nkat_advanced_tensor import create_advanced_nkat_processor
    from nkat.nkat_integration_manager import create_nkat_integration_manager
    NKAT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ NKAT モジュールインポートエラー: {e}")
    NKAT_AVAILABLE = False


class NKATPhase3TestSuite:
    """NKAT Phase 3 テストスイート"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_results = {
            'advanced_tensor_tests': [],
            'integration_manager_tests': [],
            'performance_benchmarks': [],
            'quality_measurements': [],
            'system_coordination_tests': []
        }
        
        # テストケース定義
        self.test_cases = self._define_test_cases()
        
        self.logger.info("🧪 NKAT Phase 3 テストスイート初期化完了")
    
    def _define_test_cases(self) -> List[Dict[str, Any]]:
        """テストケースの定義"""
        return [
            {
                'id': 'repetition_case_1',
                'text': 'お兄ちゃんお兄ちゃん、どこに行くのですかお兄ちゃん？',
                'character': '妹キャラ',
                'context': '家族会話',
                'expected_improvement': 'repetition_reduction',
                'priority': 'high'
            },
            {
                'id': 'emotional_expression_1',
                'text': '嬉しいです。とても嬉しいです。本当に嬉しいです。',
                'character': '樹里',
                'context': '感情表現',
                'expected_improvement': 'emotional_enhancement',
                'priority': 'high'
            },
            {
                'id': 'monotonous_response_1',
                'text': 'そうですね。そうですね。でも難しいですね。',
                'character': '美里',
                'context': '相槌会話',
                'expected_improvement': 'variety_increase',
                'priority': 'medium'
            },
            {
                'id': 'complex_narrative_1',
                'text': '彼女は美しい朝の光の中で、美しい花を見つめながら、美しい思い出を思い出していた。',
                'character': '主人公',
                'context': '心理描写',
                'expected_improvement': 'vocabulary_diversification',
                'priority': 'medium'
            },
            {
                'id': 'dialogue_enhancement_1',
                'text': '「こんにちは」と彼は言った。「こんにちは」と彼女も言った。「こんにちは」と子供も言った。',
                'character': '群衆',
                'context': '会話シーン',
                'expected_improvement': 'dialogue_variation',
                'priority': 'high'
            }
        ]
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """包括的テスト実行"""
        print("🚀 NKAT Phase 3 包括的テスト開始")
        print("=" * 70)
        
        # システム可用性チェック
        if not NKAT_AVAILABLE:
            print("❌ NKATシステムが利用できません")
            return {'success': False, 'error': 'NKAT systems not available'}
        
        # 1. Advanced Tensor Processing Tests
        print("\n🔬 1. Advanced Tensor Processing テスト")
        print("-" * 50)
        self._test_advanced_tensor_processing()
        
        # 2. Integration Manager Tests  
        print("\n🎯 2. Integration Manager テスト")
        print("-" * 50)
        self._test_integration_manager()
        
        # 3. Performance Benchmarks
        print("\n⚡ 3. パフォーマンスベンチマーク")
        print("-" * 50)
        self._run_performance_benchmarks()
        
        # 4. Quality Measurements
        print("\n📊 4. 品質測定")
        print("-" * 50)
        self._measure_quality_improvements()
        
        # 5. System Coordination Tests
        print("\n🔗 5. システム協調テスト")
        print("-" * 50)
        self._test_system_coordination()
        
        # 結果集計
        return self._compile_test_results()
    
    def _test_advanced_tensor_processing(self):
        """Advanced Tensor Processing システムテスト"""
        try:
            # プロセッサ初期化
            config = {
                'tensor_dimension': 128,  # テスト用
                'quality_threshold': 0.6,
                'max_iterations': 5,
                'literary_enhancement': True
            }
            processor = create_advanced_nkat_processor(config)
            
            for i, test_case in enumerate(self.test_cases):
                print(f"  テストケース {i+1}: {test_case['id']}")
                
                start_time = time.time()
                enhanced_text, metrics = processor.process_expression(
                    test_case['text'],
                    test_case['character'],
                    test_case['context']
                )
                processing_time = (time.time() - start_time) * 1000
                
                test_result = {
                    'test_case_id': test_case['id'],
                    'original_text': test_case['text'],
                    'enhanced_text': enhanced_text,
                    'processing_time_ms': processing_time,
                    'quality_metrics': metrics,
                    'expected_improvement': test_case['expected_improvement'],
                    'success': len(enhanced_text) > 0
                }
                
                self.test_results['advanced_tensor_tests'].append(test_result)
                
                # 結果表示
                print(f"    原文: {test_case['text'][:50]}...")
                print(f"    拡張: {enhanced_text[:50]}...")
                print(f"    品質改善: {metrics.get('quality_improvement', 0):.3f}")
                print(f"    処理時間: {processing_time:.1f}ms")
                print(f"    成功: {'✅' if test_result['success'] else '❌'}")
                print()
                
        except Exception as e:
            print(f"❌ Advanced Tensor Processing テストエラー: {e}")
            self.logger.error(f"Advanced Tensor Processing test error: {e}")
    
    def _test_integration_manager(self):
        """Integration Manager システムテスト"""
        try:
            # 統合マネージャー初期化
            manager = create_nkat_integration_manager()
            
            # システム状態確認
            status = manager.get_system_status()
            active_systems = sum(status['active_systems'].values())
            
            print(f"  📊 アクティブシステム数: {active_systems}/5")
            print(f"  🔧 協調効率: {status['system_coordination']['coordination_efficiency']:.1%}")
            
            for i, test_case in enumerate(self.test_cases):
                print(f"\n  統合処理テスト {i+1}: {test_case['id']}")
                
                # 包括的処理実行
                result = manager.process_text_comprehensive(
                    test_case['text'],
                    test_case['character'],
                    test_case['context'],
                    session_id=f"test_session_{i+1}"
                )
                
                test_result = {
                    'test_case_id': test_case['id'],
                    'processing_result': result,
                    'system_coordination': result.system_coordination,
                    'processing_stages': len(result.processing_stages),
                    'total_time_ms': result.total_processing_time_ms,
                    'success': result.success
                }
                
                self.test_results['integration_manager_tests'].append(test_result)
                
                # 結果表示
                print(f"    拡張結果: {result.enhanced_text[:50]}...")
                print(f"    処理ステージ数: {len(result.processing_stages)}")
                print(f"    総処理時間: {result.total_processing_time_ms:.1f}ms")
                print(f"    品質改善: {result.quality_metrics.get('quality_improvement', 0):.3f}")
                print(f"    成功: {'✅' if result.success else '❌'}")
                
                # ステージ詳細
                for stage_name, stage_data in result.processing_stages.items():
                    status_icon = "✅" if stage_data.get('success', False) else "❌"
                    print(f"      {status_icon} {stage_name}: {stage_data.get('processing_time_ms', 0):.1f}ms")
                
        except Exception as e:
            print(f"❌ Integration Manager テストエラー: {e}")
            self.logger.error(f"Integration Manager test error: {e}")
    
    def _run_performance_benchmarks(self):
        """パフォーマンスベンチマーク実行"""
        try:
            # ベンチマーク設定
            benchmark_iterations = 3
            
            # Advanced Tensor Processing ベンチマーク
            print("  🔬 Advanced Tensor Processing ベンチマーク")
            processor = create_advanced_nkat_processor({
                'tensor_dimension': 256,
                'max_iterations': 10
            })
            
            tensor_times = []
            for iteration in range(benchmark_iterations):
                start_time = time.time()
                for test_case in self.test_cases[:3]:  # 最初の3ケース
                    processor.process_expression(
                        test_case['text'],
                        test_case['character'],
                        test_case['context']
                    )
                iteration_time = (time.time() - start_time) * 1000
                tensor_times.append(iteration_time)
                print(f"    反復 {iteration+1}: {iteration_time:.1f}ms")
            
            # Integration Manager ベンチマーク
            print("\n  🎯 Integration Manager ベンチマーク")
            manager = create_nkat_integration_manager()
            
            integration_times = []
            for iteration in range(benchmark_iterations):
                start_time = time.time()
                for test_case in self.test_cases[:3]:
                    manager.process_text_comprehensive(
                        test_case['text'],
                        test_case['character'],
                        test_case['context']
                    )
                iteration_time = (time.time() - start_time) * 1000
                integration_times.append(iteration_time)
                print(f"    反復 {iteration+1}: {iteration_time:.1f}ms")
            
            # ベンチマーク結果保存
            benchmark_results = {
                'tensor_processing': {
                    'times_ms': tensor_times,
                    'average_ms': sum(tensor_times) / len(tensor_times),
                    'min_ms': min(tensor_times),
                    'max_ms': max(tensor_times)
                },
                'integration_manager': {
                    'times_ms': integration_times,
                    'average_ms': sum(integration_times) / len(integration_times),
                    'min_ms': min(integration_times),
                    'max_ms': max(integration_times)
                }
            }
            
            self.test_results['performance_benchmarks'].append(benchmark_results)
            
            # 結果表示
            print(f"\n  📈 ベンチマーク結果:")
            print(f"    Tensor Processing 平均: {benchmark_results['tensor_processing']['average_ms']:.1f}ms")
            print(f"    Integration Manager 平均: {benchmark_results['integration_manager']['average_ms']:.1f}ms")
            
        except Exception as e:
            print(f"❌ パフォーマンスベンチマークエラー: {e}")
    
    def _measure_quality_improvements(self):
        """品質改善の測定"""
        try:
            # 品質測定システム初期化
            processor = create_advanced_nkat_processor()
            manager = create_nkat_integration_manager()
            
            quality_comparisons = []
            
            for test_case in self.test_cases:
                print(f"  📏 品質測定: {test_case['id']}")
                
                # 1. 原文（ベースライン）
                baseline_quality = self._calculate_text_quality(test_case['text'])
                
                # 2. Advanced Tensor Processing
                tensor_enhanced, tensor_metrics = processor.process_expression(
                    test_case['text'],
                    test_case['character'],
                    test_case['context']
                )
                tensor_quality = self._calculate_text_quality(tensor_enhanced)
                
                # 3. Integration Manager（全システム統合）
                integration_result = manager.process_text_comprehensive(
                    test_case['text'],
                    test_case['character'],
                    test_case['context']
                )
                integration_quality = self._calculate_text_quality(integration_result.enhanced_text)
                
                comparison = {
                    'test_case_id': test_case['id'],
                    'baseline_quality': baseline_quality,
                    'tensor_quality': tensor_quality,
                    'integration_quality': integration_quality,
                    'tensor_improvement': tensor_quality - baseline_quality,
                    'integration_improvement': integration_quality - baseline_quality,
                    'tensor_vs_integration': integration_quality - tensor_quality
                }
                
                quality_comparisons.append(comparison)
                
                # 結果表示
                print(f"    ベースライン品質: {baseline_quality:.3f}")
                print(f"    Tensor処理品質: {tensor_quality:.3f} (改善: {comparison['tensor_improvement']:+.3f})")
                print(f"    統合処理品質: {integration_quality:.3f} (改善: {comparison['integration_improvement']:+.3f})")
                print(f"    統合優位性: {comparison['tensor_vs_integration']:+.3f}")
                print()
            
            self.test_results['quality_measurements'] = quality_comparisons
            
            # 全体統計
            avg_tensor_improvement = sum(c['tensor_improvement'] for c in quality_comparisons) / len(quality_comparisons)
            avg_integration_improvement = sum(c['integration_improvement'] for c in quality_comparisons) / len(quality_comparisons)
            
            print(f"  📊 品質改善統計:")
            print(f"    Tensor Processing 平均改善: {avg_tensor_improvement:+.3f}")
            print(f"    Integration Manager 平均改善: {avg_integration_improvement:+.3f}")
            
        except Exception as e:
            print(f"❌ 品質測定エラー: {e}")
    
    def _calculate_text_quality(self, text: str) -> float:
        """簡易的なテキスト品質計算"""
        if not text:
            return 0.0
        
        # 基本指標
        words = text.split()
        unique_words = set(words)
        
        # 語彙多様性
        vocabulary_diversity = len(unique_words) / max(len(words), 1)
        
        # 文の多様性（簡易）
        sentences = text.split('。')
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
        sentence_diversity = len(set(sentence_lengths)) / max(len(sentence_lengths), 1)
        
        # 反復度（低いほど良い）
        repetition_penalty = 0.0
        for word in unique_words:
            count = words.count(word)
            if count > 2:
                repetition_penalty += (count - 2) * 0.1
        
        # 総合品質スコア
        quality_score = (vocabulary_diversity * 0.4 + 
                        sentence_diversity * 0.3 + 
                        0.3) - min(repetition_penalty, 0.5)
        
        return max(0.0, min(1.0, quality_score))
    
    def _test_system_coordination(self):
        """システム協調テスト"""
        try:
            print("  🔗 システム協調機能テスト")
            
            # 異なる設定での統合マネージャー
            configs = [
                {'name': '全システム有効', 'config': {}},
                {'name': 'Tensor Processing のみ', 'config': {
                    'integration_systems': {
                        'repetition_suppression': False,
                        'lora_coordination': False,
                        'cross_suppression': False
                    }
                }},
                {'name': 'Legacy システム無効', 'config': {
                    'nkat_legacy': {'enabled': False}
                }}
            ]
            
            coordination_results = []
            
            for config_set in configs:
                print(f"\n    設定: {config_set['name']}")
                manager = create_nkat_integration_manager(config_set['config'])
                
                status = manager.get_system_status()
                active_count = sum(status['active_systems'].values())
                coordination_efficiency = status['system_coordination']['coordination_efficiency']
                
                # テストケースで処理時間測定
                test_case = self.test_cases[0]  # 最初のケース
                start_time = time.time()
                result = manager.process_text_comprehensive(
                    test_case['text'],
                    test_case['character'],
                    test_case['context']
                )
                processing_time = (time.time() - start_time) * 1000
                
                coordination_result = {
                    'config_name': config_set['name'],
                    'active_systems': active_count,
                    'coordination_efficiency': coordination_efficiency,
                    'processing_time_ms': processing_time,
                    'quality_improvement': result.quality_metrics.get('quality_improvement', 0),
                    'success': result.success
                }
                
                coordination_results.append(coordination_result)
                
                print(f"      アクティブシステム: {active_count}/5")
                print(f"      協調効率: {coordination_efficiency:.1%}")
                print(f"      処理時間: {processing_time:.1f}ms")
                print(f"      品質改善: {coordination_result['quality_improvement']:.3f}")
            
            self.test_results['system_coordination_tests'] = coordination_results
            
        except Exception as e:
            print(f"❌ システム協調テストエラー: {e}")
    
    def _compile_test_results(self) -> Dict[str, Any]:
        """テスト結果の集計"""
        print("\n📋 テスト結果集計")
        print("=" * 50)
        
        # 成功率計算
        tensor_success_rate = self._calculate_success_rate(self.test_results['advanced_tensor_tests'])
        integration_success_rate = self._calculate_success_rate(self.test_results['integration_manager_tests'])
        
        # 平均品質改善
        avg_quality_improvement = 0.0
        if self.test_results['quality_measurements']:
            avg_quality_improvement = sum(
                q['integration_improvement'] for q in self.test_results['quality_measurements']
            ) / len(self.test_results['quality_measurements'])
        
        # 平均処理時間
        avg_processing_time = 0.0
        if self.test_results['performance_benchmarks']:
            benchmark = self.test_results['performance_benchmarks'][0]
            avg_processing_time = benchmark['integration_manager']['average_ms']
        
        # システム協調効率
        coordination_efficiency = 0.0
        if self.test_results['system_coordination_tests']:
            coordination_efficiency = max(
                c['coordination_efficiency'] for c in self.test_results['system_coordination_tests']
            )
        
        final_results = {
            'success': True,
            'test_summary': {
                'total_test_cases': len(self.test_cases),
                'tensor_success_rate': tensor_success_rate,
                'integration_success_rate': integration_success_rate,
                'average_quality_improvement': avg_quality_improvement,
                'average_processing_time_ms': avg_processing_time,
                'coordination_efficiency': coordination_efficiency
            },
            'detailed_results': self.test_results,
            'phase3_readiness': self._assess_phase3_readiness()
        }
        
        # 結果表示
        print(f"  ✅ Advanced Tensor Processing 成功率: {tensor_success_rate:.1%}")
        print(f"  ✅ Integration Manager 成功率: {integration_success_rate:.1%}")
        print(f"  📈 平均品質改善: {avg_quality_improvement:+.3f}")
        print(f"  ⚡ 平均処理時間: {avg_processing_time:.1f}ms")
        print(f"  🔗 協調効率: {coordination_efficiency:.1%}")
        
        return final_results
    
    def _calculate_success_rate(self, test_results: List[Dict]) -> float:
        """成功率計算"""
        if not test_results:
            return 0.0
        
        successful = sum(1 for result in test_results if result.get('success', False))
        return successful / len(test_results)
    
    def _assess_phase3_readiness(self) -> Dict[str, Any]:
        """Phase 3 準備状況評価"""
        readiness_criteria = {
            'tensor_processing_functional': False,
            'integration_manager_functional': False,
            'quality_improvement_achieved': False,
            'performance_acceptable': False,
            'system_coordination_working': False
        }
        
        # 基準評価
        if self.test_results['advanced_tensor_tests']:
            tensor_success = self._calculate_success_rate(self.test_results['advanced_tensor_tests'])
            readiness_criteria['tensor_processing_functional'] = tensor_success >= 0.8
        
        if self.test_results['integration_manager_tests']:
            integration_success = self._calculate_success_rate(self.test_results['integration_manager_tests'])
            readiness_criteria['integration_manager_functional'] = integration_success >= 0.8
        
        if self.test_results['quality_measurements']:
            avg_improvement = sum(q['integration_improvement'] for q in self.test_results['quality_measurements']) / len(self.test_results['quality_measurements'])
            readiness_criteria['quality_improvement_achieved'] = avg_improvement > 0.1
        
        if self.test_results['performance_benchmarks']:
            benchmark = self.test_results['performance_benchmarks'][0]
            avg_time = benchmark['integration_manager']['average_ms']
            readiness_criteria['performance_acceptable'] = avg_time < 5000  # 5秒以内
        
        if self.test_results['system_coordination_tests']:
            max_efficiency = max(c['coordination_efficiency'] for c in self.test_results['system_coordination_tests'])
            readiness_criteria['system_coordination_working'] = max_efficiency >= 0.6
        
        overall_readiness = sum(readiness_criteria.values()) / len(readiness_criteria)
        
        return {
            'criteria': readiness_criteria,
            'overall_readiness_score': overall_readiness,
            'phase3_ready': overall_readiness >= 0.8,
            'recommendation': self._get_readiness_recommendation(readiness_criteria)
        }
    
    def _get_readiness_recommendation(self, criteria: Dict[str, bool]) -> str:
        """準備状況に基づく推奨事項"""
        failed_criteria = [k for k, v in criteria.items() if not v]
        
        if not failed_criteria:
            return "Phase 3 実装準備完了 ✅"
        elif len(failed_criteria) <= 2:
            return f"軽微な調整が必要: {', '.join(failed_criteria)}"
        else:
            return f"重要な改善が必要: {', '.join(failed_criteria)}"


def main():
    """メイン実行関数"""
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 NKAT Phase 3 統合テストデモ")
    print("=" * 70)
    print("高度な非可換テンソル処理システムと統合マネージャーの検証")
    print()
    
    # テストスイート実行
    test_suite = NKATPhase3TestSuite()
    results = test_suite.run_comprehensive_tests()
    
    # 最終評価
    print("\n🎯 Phase 3 準備状況評価")
    print("=" * 50)
    
    if results['success']:
        readiness = results['phase3_readiness']
        print(f"📊 総合準備度: {readiness['overall_readiness_score']:.1%}")
        print(f"🎯 Phase 3 準備状況: {'✅ 準備完了' if readiness['phase3_ready'] else '⚠️ 調整必要'}")
        print(f"💡 推奨事項: {readiness['recommendation']}")
        
        print("\n📋 準備基準詳細:")
        for criterion, status in readiness['criteria'].items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {criterion.replace('_', ' ').title()}")
        
        # 結果保存
        output_file = f"nkat_phase3_test_results_{int(time.time())}.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 詳細結果を保存: {output_file}")
        except Exception as e:
            print(f"⚠️ 結果保存エラー: {e}")
    else:
        print("❌ テスト実行に失敗しました")
        if 'error' in results:
            print(f"エラー詳細: {results['error']}")
    
    print("\n✅ NKAT Phase 3 統合テストデモ完了")


if __name__ == "__main__":
    main() 