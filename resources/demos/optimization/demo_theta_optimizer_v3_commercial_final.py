# -*- coding: utf-8 -*-
"""
Θ フィードバック最適化システム v3.0 商用レベルテスト（最終版）
Phase 4: 商用品質90%+ 達成のための修正版

解決項目:
- 文字化けエラー修正
- JSON serialization error修正
- θ収束度改善 (目標80%+)
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple
from tqdm import tqdm

# 商用レベルθ最適化システム
from integration.theta_feedback_optimizer_v3 import (
    ThetaFeedbackOptimizerV3,
    ThetaOptimizationConfig,
    create_commercial_theta_optimizer
)

class CommercialThetaTestSuiteFinal:
    """商用レベルθ最適化テストスイート（最終版）"""
    
    def __init__(self):
        self.test_version = "v3.0 Commercial Final"
        self.commercial_target = 90.0
        self.theta_convergence_target = 80.0
        
        # 商用レベルテストケース
        self.commercial_test_cases = [
            {
                'name': '商用丁寧語キャラクター',
                'profile': {'formality': 0.95, 'emotion': 0.25, 'complexity': 0.8},
                'texts': ['いつもお世話になっております。本日の件についてご報告申し上げます。'],
                'commercial_weight': 1.2
            },
            {
                'name': '商用カジュアルキャラクター',  
                'profile': {'formality': 0.15, 'emotion': 0.85, 'complexity': 0.3},
                'texts': ['やっほー！今日もめっちゃいい天気だね～♪'],
                'commercial_weight': 1.0
            },
            {
                'name': '商用学術専門キャラクター',
                'profile': {'formality': 0.98, 'emotion': 0.15, 'complexity': 0.95},
                'texts': ['本研究における統計的手法の妥当性について詳細な検討を行いました。'],
                'commercial_weight': 1.3
            },
            {
                'name': '商用感情豊かキャラクター',
                'profile': {'formality': 0.4, 'emotion': 0.95, 'complexity': 0.5},
                'texts': ['うわあ～！本当に感動しちゃった！涙が止まらないよ～！'],
                'commercial_weight': 1.1
            },
            {
                'name': '商用バランス型キャラクター',
                'profile': {'formality': 0.6, 'emotion': 0.6, 'complexity': 0.6},
                'texts': ['こんにちは。今日はとても良い天気ですね。散歩でもしませんか？'],
                'commercial_weight': 0.9
            },
            {
                'name': '商用高複雑度キャラクター',
                'profile': {'formality': 0.7, 'emotion': 0.3, 'complexity': 0.92},
                'texts': ['多次元的な解析手法を用いて、包括的かつ詳細な検討を実施いたします。'],
                'commercial_weight': 1.4
            }
        ]
        
    def run_commercial_theta_optimization_test(self) -> Dict[str, Any]:
        """商用レベルθ最適化テスト実行"""
        print("■ Theta フィードバック最適化システム v3.0 - 商用レベルテスト（最終版）")
        print("=" * 70)
        print(f"目標: θ収束度 {self.theta_convergence_target}%+ / 商用レベル {self.commercial_target}%+")
        print()
        
        # 商用レベルオプティマイザー初期化
        optimizer = create_commercial_theta_optimizer()
        
        test_results = []
        total_start_time = time.time()
        
        for i, test_case in enumerate(self.commercial_test_cases, 1):
            print(f"テストケース {i}/{len(self.commercial_test_cases)}: {test_case['name']}")
            print(f"   プロファイル: {test_case['profile']}")
            print(f"   商用重要度: {test_case['commercial_weight']:.1f}x")
            
            case_start_time = time.time()
            
            # θパラメータ最適化実行
            result = optimizer.optimize_theta_parameters(
                target_style=test_case['profile'],
                text_samples=test_case['texts']
            )
            
            case_processing_time = time.time() - case_start_time
            
            # 商用評価計算
            commercial_score = self._calculate_commercial_score(result, test_case)
            
            # 結果まとめ
            test_result = {
                'test_case': test_case['name'],
                'profile': test_case['profile'],
                'commercial_weight': test_case['commercial_weight'],
                'theta_convergence_rate': result['theta_convergence_rate'],
                'feedback_efficiency': result['feedback_efficiency'],
                'stability_score': result['stability_score'],
                'commercial_score': commercial_score,
                'commercial_level_achieved': result['commercial_level_achieved'],
                'processing_time': case_processing_time,
                'final_params': result['final_params'],
                'optimization_details': {
                    'final_loss': result['final_loss'],
                    'target_alignment': result['target_alignment'],
                    'convergence_analysis': result['convergence_analysis']
                }
            }
            
            test_results.append(test_result)
            
            # 結果表示
            self._display_case_result(test_result)
            print()
        
        total_processing_time = time.time() - total_start_time
        
        # 総合評価計算
        overall_results = self._calculate_overall_commercial_results(test_results, total_processing_time)
        
        # 最終結果表示
        self._display_final_results(overall_results)
        
        # 結果保存
        self._save_commercial_test_results(overall_results)
        
        return overall_results
    
    def _calculate_commercial_score(self, result: Dict[str, Any], test_case: Dict[str, Any]) -> float:
        """商用スコア計算"""
        # 基本スコア（θ収束度重視）
        base_score = (
            result['theta_convergence_rate'] * 0.4 +
            result['feedback_efficiency'] * 0.25 + 
            result['stability_score'] * 0.2 +
            result['target_alignment'] * 0.15
        )
        
        # 商用重要度による重み付け
        weighted_score = base_score * test_case['commercial_weight']
        
        # ペナルティ適用
        if result['optimization_time'] > 10.0:
            weighted_score *= 0.9
        
        if result['final_loss'] > 0.1:
            weighted_score *= 0.95
        
        return min(100.0, weighted_score)
    
    def _display_case_result(self, result: Dict[str, Any]):
        """ケース結果表示"""
        print(f"   結果:")
        print(f"      θ収束度: {result['theta_convergence_rate']:.1f}% (目標: {self.theta_convergence_target}%+)")
        print(f"      フィードバック効率: {result['feedback_efficiency']:.1f}%")
        print(f"      安定性: {result['stability_score']:.1f}%")
        print(f"      商用スコア: {result['commercial_score']:.1f}%")
        print(f"      商用レベル達成: {'YES' if result['commercial_level_achieved'] else 'NO'}")
        print(f"      処理時間: {result['processing_time']:.3f}秒")
        
        # 最終パラメータ表示
        params = result['final_params']
        print(f"      最終θパラメータ: formality={params['formality']:.3f}, emotion={params['emotion']:.3f}, complexity={params['complexity']:.3f}")
    
    def _calculate_overall_commercial_results(self, test_results: List[Dict], total_time: float) -> Dict[str, Any]:
        """総合商用結果計算"""
        
        # 重み付き平均計算
        total_weight = sum(r['commercial_weight'] for r in test_results)
        weighted_avg = lambda metric: sum(r[metric] * r['commercial_weight'] for r in test_results) / total_weight
        
        # メトリクス計算
        avg_theta_convergence = weighted_avg('theta_convergence_rate')
        avg_feedback_efficiency = weighted_avg('feedback_efficiency')
        avg_stability = weighted_avg('stability_score')
        avg_commercial_score = weighted_avg('commercial_score')
        
        # 商用レベル達成率
        commercial_achieved_count = sum(1 for r in test_results if r['commercial_level_achieved'])
        commercial_achievement_rate = commercial_achieved_count / len(test_results) * 100
        
        # 速度性能
        avg_processing_time = sum(r['processing_time'] for r in test_results) / len(test_results)
        
        # θ収束度目標達成判定
        theta_target_achieved = avg_theta_convergence >= self.theta_convergence_target
        
        # 総合商用レベル判定
        overall_commercial_criteria = {
            'theta_convergence_80plus': avg_theta_convergence >= 80.0,
            'feedback_efficiency_75plus': avg_feedback_efficiency >= 75.0,
            'stability_70plus': avg_stability >= 70.0,
            'commercial_score_90plus': avg_commercial_score >= 90.0,
            'achievement_rate_80plus': commercial_achievement_rate >= 80.0
        }
        
        overall_commercial_achieved = all(overall_commercial_criteria.values())
        criteria_score = sum(overall_commercial_criteria.values()) / len(overall_commercial_criteria) * 100
        
        # 改善度計算
        improvement_analysis = self._analyze_improvement_trends(test_results)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'test_version': self.test_version,
            'commercial_target': self.commercial_target,
            'theta_convergence_target': self.theta_convergence_target,
            'overall_metrics': {
                'avg_theta_convergence_rate': avg_theta_convergence,
                'avg_feedback_efficiency': avg_feedback_efficiency,
                'avg_stability_score': avg_stability,
                'avg_commercial_score': avg_commercial_score,
                'commercial_achievement_rate': commercial_achievement_rate,
                'avg_processing_time_sec': avg_processing_time,
                'total_processing_time_sec': total_time
            },
            'target_achievements': {
                'theta_convergence_target_achieved': bool(theta_target_achieved),
                'commercial_level_achieved': bool(overall_commercial_achieved),
                'criteria_satisfaction_rate': criteria_score
            },
            'commercial_criteria': {
                'theta_convergence_80plus': bool(overall_commercial_criteria['theta_convergence_80plus']),
                'feedback_efficiency_75plus': bool(overall_commercial_criteria['feedback_efficiency_75plus']),
                'stability_70plus': bool(overall_commercial_criteria['stability_70plus']),
                'commercial_score_90plus': bool(overall_commercial_criteria['commercial_score_90plus']),
                'achievement_rate_80plus': bool(overall_commercial_criteria['achievement_rate_80plus'])
            },
            'improvement_analysis': improvement_analysis,
            'detailed_results': test_results,
            'commercial_assessment': self._generate_commercial_assessment(
                avg_theta_convergence, avg_commercial_score, overall_commercial_achieved
            )
        }
    
    def _analyze_improvement_trends(self, test_results: List[Dict]) -> Dict[str, Any]:
        """改善トレンド分析"""
        # 前回結果と比較（ファイルが存在する場合）
        previous_results_file = 'logs/theta_optimization_v3_commercial_latest.json'
        
        if os.path.exists(previous_results_file):
            try:
                with open(previous_results_file, 'r', encoding='utf-8') as f:
                    previous_data = json.load(f)
                
                prev_theta = previous_data['overall_metrics']['avg_theta_convergence_rate']
                curr_theta = sum(r['theta_convergence_rate'] for r in test_results) / len(test_results)
                
                theta_improvement = curr_theta - prev_theta
                
                return {
                    'previous_theta_convergence': prev_theta,
                    'current_theta_convergence': curr_theta,
                    'theta_improvement': theta_improvement,
                    'improvement_trend': 'improving' if theta_improvement > 0 else 'declining',
                    'comparison_available': True
                }
            except Exception as e:
                return {'comparison_available': False, 'error': str(e)}
        else:
            return {'comparison_available': False, 'reason': 'no_previous_data'}
    
    def _generate_commercial_assessment(self, theta_convergence: float, commercial_score: float, achieved: bool) -> Dict[str, str]:
        """商用評価生成"""
        if achieved and theta_convergence >= 85.0:
            level = "Premium Commercial"
            recommendation = "即座に商用配布可能。最高品質達成。"
        elif achieved and theta_convergence >= 80.0:
            level = "Standard Commercial" 
            recommendation = "商用配布準備完了。最終調整推奨。"
        elif theta_convergence >= 75.0:
            level = "Pre-Commercial"
            recommendation = "商用に近い品質。微調整で達成可能。"
        elif theta_convergence >= 65.0:
            level = "Advanced Development"
            recommendation = "開発終盤。追加最適化で商用レベル到達。"
        else:
            level = "Development Phase"
            recommendation = "継続開発が必要。アルゴリズム改善を検討。"
        
        return {
            'commercial_level': level,
            'recommendation': recommendation,
            'readiness': "Ready" if achieved else "Not Ready",
            'confidence': "High" if theta_convergence >= 80.0 else "Medium" if theta_convergence >= 70.0 else "Low"
        }
    
    def _display_final_results(self, results: Dict[str, Any]):
        """最終結果表示"""
        print("■ 商用レベルθ最適化テスト - 最終結果")
        print("=" * 70)
        
        metrics = results['overall_metrics']
        targets = results['target_achievements']
        assessment = results['commercial_assessment']
        
        print(f"総合メトリクス:")
        print(f"   θ収束度: {metrics['avg_theta_convergence_rate']:.1f}% (目標: {self.theta_convergence_target}%+)")
        print(f"   フィードバック効率: {metrics['avg_feedback_efficiency']:.1f}%")
        print(f"   安定性スコア: {metrics['avg_stability_score']:.1f}%")
        print(f"   商用スコア: {metrics['avg_commercial_score']:.1f}%")
        print(f"   商用達成率: {metrics['commercial_achievement_rate']:.1f}%")
        print(f"   平均処理時間: {metrics['avg_processing_time_sec']:.3f}秒")
        print()
        
        print(f"目標達成状況:")
        print(f"   θ収束度目標達成: {'YES' if targets['theta_convergence_target_achieved'] else 'NO'}")
        print(f"   商用レベル達成: {'YES' if targets['commercial_level_achieved'] else 'NO'}")
        print(f"   基準満足率: {targets['criteria_satisfaction_rate']:.1f}%")
        print()
        
        print(f"商用評価:")
        print(f"   商用レベル: {assessment['commercial_level']}")
        print(f"   配布準備状況: {assessment['readiness']}")
        print(f"   信頼度: {assessment['confidence']}")
        print(f"   推奨事項: {assessment['recommendation']}")
        print()
        
        # 改善トレンド
        if results['improvement_analysis']['comparison_available']:
            improvement = results['improvement_analysis']
            print(f"改善トレンド:")
            print(f"   前回θ収束度: {improvement['previous_theta_convergence']:.1f}%")
            print(f"   今回θ収束度: {improvement['current_theta_convergence']:.1f}%")
            print(f"   改善幅: {improvement['theta_improvement']:+.1f}pt")
            print(f"   トレンド: {improvement['improvement_trend']}")
            print()
    
    def _save_commercial_test_results(self, results: Dict[str, Any]):
        """商用テスト結果保存"""
        os.makedirs('logs', exist_ok=True)
        
        # タイムスタンプ付きファイル
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'logs/theta_optimization_v3_commercial_final_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        # 最新版ファイル（比較用）
        latest_filename = 'logs/theta_optimization_v3_commercial_latest.json'
        with open(latest_filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"結果保存: {filename}")

def main():
    """メイン実行"""
    print("EasyNovelAssistant Phase 4 - θ最適化商用レベルテスト（最終版）")
    print("   商用品質90%+ 達成への最終チャレンジ")
    print()
    
    # 商用テストスイート実行
    test_suite = CommercialThetaTestSuiteFinal()
    results = test_suite.run_commercial_theta_optimization_test()
    
    # 成功判定
    if results['target_achievements']['commercial_level_achieved']:
        print("商用レベル達成成功！Phase 4 目標クリア！")
    else:
        print("商用レベル未達成。継続開発が必要です。")
        
        # 改善提案
        print("\n改善提案:")
        theta_rate = results['overall_metrics']['avg_theta_convergence_rate']
        if theta_rate < 80.0:
            needed_improvement = 80.0 - theta_rate
            print(f"  - θ収束度を{needed_improvement:.1f}pt向上させる必要があります")
            print(f"  - 収束アルゴリズムの学習率調整を検討")
            print(f"  - より高精度な目的関数の実装を検討")
    
    return results

if __name__ == "__main__":
    results = main() 