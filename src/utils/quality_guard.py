# -*- coding: utf-8 -*-
"""
Quality Guard System for NKAT Expression Enhancement
品質ガードシステム - "盛り過ぎ"防止と自動補正機能
"""

import re
import json
import time
import threading
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict
import numpy as np
from tqdm import tqdm

@dataclass
class QualityMetrics:
    """品質メトリクス"""
    grammar_score: float  # 文法スコア (0.0-1.0)
    sense_score: float    # 常識性スコア (0.0-1.0)
    coherence_score: float # 一貫性スコア (0.0-1.0)
    diversity_score: float # 多様性スコア (0.0-1.0)
    repetition_rate: float # 反復率 (0.0-1.0)
    error_count: int      # エラー数
    overall_score: float  # 総合スコア (0.0-1.0)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'grammar_score': self.grammar_score,
            'sense_score': self.sense_score,
            'coherence_score': self.coherence_score,
            'diversity_score': self.diversity_score,
            'repetition_rate': self.repetition_rate,
            'error_count': self.error_count,
            'overall_score': self.overall_score
        }

class GrammarChecker:
    """文法チェッカー"""
    
    def __init__(self):
        # 文法パターン定義
        self.error_patterns = {
            'particle_error': [
                (r'[ををお]([^ぁ-ゔァ-ヾ])', '助詞「を」の誤用'),
                (r'[はわ]([なに])', '助詞「は」の誤用'),
                (r'([あいうえお])[がか]([あいうえお])', '助詞の重複'),
            ],
            'conjugation_error': [
                (r'([る動詞])れた', '動詞活用エラー'),
                (r'([い形容詞])かった([^ぁ-ゔァ-ヾ])', '形容詞活用エラー'),
            ],
            'punctuation_error': [
                (r'[。！？]{3,}', '句読点の過多'),
                (r'[、，]{2,}', '読点の重複'),
                (r'[「『]{2,}', '括弧の重複'),
            ]
        }
        
        self.correction_rules = {
            'particle_correction': [
                (r'ををを', 'を'),
                (r'はははは', 'は'),
                (r'がががが', 'が'),
            ],
            'repetition_correction': [
                (r'([あ-ん])\1{4,}', r'\1\1\1'),  # 4文字以上の反復を3文字に
                (r'([！？]){4,}', r'\1\1\1'),     # 感嘆符の過多修正
                (r'(…){3,}', r'\1\1'),            # 省略記号の過多修正
            ]
        }
    
    def check_grammar(self, text: str) -> Tuple[float, List[Dict[str, Any]]]:
        """文法チェック実行"""
        errors = []
        error_count = 0
        
        for category, patterns in self.error_patterns.items():
            for pattern, description in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    errors.append({
                        'category': category,
                        'description': description,
                        'position': match.span(),
                        'matched_text': match.group(),
                        'severity': self._calculate_severity(category)
                    })
                    error_count += 1
        
        # 文法スコア計算（エラー数に基づく）
        text_length = len(text)
        if text_length == 0:
            return 1.0, errors
        
        error_density = error_count / max(text_length, 1) * 100
        grammar_score = max(0.0, 1.0 - error_density * 0.1)
        
        return grammar_score, errors
    
    def _calculate_severity(self, category: str) -> float:
        """エラーの重要度計算"""
        severity_map = {
            'particle_error': 0.8,
            'conjugation_error': 0.9,
            'punctuation_error': 0.3
        }
        return severity_map.get(category, 0.5)
    
    def auto_correct_grammar(self, text: str) -> str:
        """自動文法補正"""
        corrected_text = text
        
        for category, rules in self.correction_rules.items():
            for pattern, replacement in rules:
                corrected_text = re.sub(pattern, replacement, corrected_text)
        
        return corrected_text

class SenseChecker:
    """常識性チェッカー"""
    
    def __init__(self):
        # 常識的でない表現パターン
        self.nonsense_patterns = [
            (r'([あ-ん])\1{10,}', '異常な反復'),
            (r'[！？]{5,}', '感嘆符の過多'),
            (r'[。]{3,}', '句点の過多'),
            (r'同じ[^。]{0,20}同じ[^。]{0,20}同じ', '過度な反復表現'),
        ]
        
        # 一般的でない語彙パターン
        self.unusual_vocab_patterns = [
            (r'[ｱ-ﾝ]{5,}', '半角カタカナの過多'),
            (r'[A-Z]{10,}', '大文字英字の過多'),
            (r'[0-9]{8,}', '数字の過多'),
        ]
    
    def check_sense(self, text: str) -> Tuple[float, List[Dict[str, Any]]]:
        """常識性チェック実行"""
        issues = []
        issue_count = 0
        
        # 非常識パターンチェック
        for pattern, description in self.nonsense_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                issues.append({
                    'type': 'nonsense',
                    'description': description,
                    'position': match.span(),
                    'matched_text': match.group(),
                    'severity': 0.8
                })
                issue_count += 1
        
        # 異常語彙チェック
        for pattern, description in self.unusual_vocab_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                issues.append({
                    'type': 'unusual_vocab',
                    'description': description,
                    'position': match.span(),
                    'matched_text': match.group(),
                    'severity': 0.6
                })
                issue_count += 1
        
        # 常識性スコア計算
        text_length = len(text)
        if text_length == 0:
            return 1.0, issues
        
        issue_density = issue_count / max(text_length, 1) * 100
        sense_score = max(0.0, 1.0 - issue_density * 0.15)
        
        return sense_score, issues

class DiversityAnalyzer:
    """多様性分析器"""
    
    def __init__(self):
        self.vocab_cache = {}
        
    def calculate_diversity(self, text: str) -> float:
        """語彙多様性計算"""
        if len(text) < 10:
            return 0.0
        
        # 単語分割（簡易版）
        words = self._simple_tokenize(text)
        
        if len(words) < 2:
            return 0.0
        
        # ユニーク語彙率
        unique_words = set(words)
        diversity_score = len(unique_words) / len(words)
        
        return min(diversity_score, 1.0)
    
    def _simple_tokenize(self, text: str) -> List[str]:
        """簡易トークン化"""
        # ひらがな・カタカナ・漢字の境界で分割
        import re
        tokens = re.findall(r'[ぁ-ん]+|[ァ-ン]+|[一-龯]+|[a-zA-Z]+|\d+', text)
        return tokens

class QualityGuard:
    """品質ガードメインクラス"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('quality_guard_enabled', True)
        self.error_threshold = config.get('auto_correction_threshold', 0.03)
        self.diversity_target = config.get('diversity_target', 0.35)
        self.gamma_adjustment = config.get('gamma_adjustment_step', 0.01)
        
        # 各チェッカーの初期化
        self.grammar_checker = GrammarChecker()
        self.sense_checker = SenseChecker()
        self.diversity_analyzer = DiversityAnalyzer()
        
        # 統計情報
        self.stats = {
            'total_checks': 0,
            'corrections_applied': 0,
            'gamma_adjustments': 0,
            'average_quality_score': 0.0,
            'error_prevention_rate': 0.0
        }
        
        # 品質履歴
        self.quality_history = []
        self.max_history_size = config.get('quality_history_size', 100)
        
        print(f"🛡️ 品質ガードシステム初期化 (閾値: {self.error_threshold*100:.1f}%)")
    
    def evaluate_quality(self, text: str, context: str = "") -> QualityMetrics:
        """品質評価実行"""
        if not self.enabled:
            return QualityMetrics(1.0, 1.0, 1.0, 1.0, 0.0, 0, 1.0)
        
        start_time = time.time()
        
        # 各種チェック実行
        grammar_score, grammar_errors = self.grammar_checker.check_grammar(text)
        sense_score, sense_issues = self.sense_checker.check_sense(text)
        diversity_score = self.diversity_analyzer.calculate_diversity(text)
        
        # 一貫性スコア（簡易版）
        coherence_score = self._calculate_coherence(text, context)
        
        # 反復率計算
        repetition_rate = self._calculate_repetition_rate(text)
        
        # 総エラー数
        total_errors = len(grammar_errors) + len(sense_issues)
        
        # 総合スコア計算
        overall_score = (
            grammar_score * 0.3 +
            sense_score * 0.25 +
            coherence_score * 0.25 +
            diversity_score * 0.2
        )
        
        metrics = QualityMetrics(
            grammar_score=grammar_score,
            sense_score=sense_score,
            coherence_score=coherence_score,
            diversity_score=diversity_score,
            repetition_rate=repetition_rate,
            error_count=total_errors,
            overall_score=overall_score
        )
        
        # 統計更新
        self._update_stats(metrics, time.time() - start_time)
        
        return metrics
    
    def auto_correct_if_needed(self, text: str, current_gamma: float, 
                              context: str = "") -> Tuple[str, float, bool]:
        """必要に応じて自動補正実行"""
        if not self.enabled:
            return text, current_gamma, False
        
        # 品質評価
        metrics = self.evaluate_quality(text, context)
        
        # エラー率計算
        text_length = len(text)
        error_rate = metrics.error_count / max(text_length, 1) * 100
        
        correction_applied = False
        new_gamma = current_gamma
        corrected_text = text
        
        # エラー率が閾値を超えている場合
        if error_rate > self.error_threshold * 100:
            # 自動文法補正
            corrected_text = self.grammar_checker.auto_correct_grammar(text)
            
            # γ値調整（安定性を高める）
            new_gamma = min(1.0, current_gamma + self.gamma_adjustment)
            
            correction_applied = True
            self.stats['corrections_applied'] += 1
            self.stats['gamma_adjustments'] += 1
            
            print(f"🔧 品質ガード発動: エラー率 {error_rate:.1f}% → γ調整 {current_gamma:.3f} → {new_gamma:.3f}")
        
        # 多様性不足の場合
        elif metrics.diversity_score < self.diversity_target:
            # γ値を下げて多様性を向上
            new_gamma = max(0.8, current_gamma - self.gamma_adjustment * 0.5)
            
            if new_gamma != current_gamma:
                correction_applied = True
                self.stats['gamma_adjustments'] += 1
                print(f"📈 多様性向上: {metrics.diversity_score:.1f} → γ調整 {current_gamma:.3f} → {new_gamma:.3f}")
        
        return corrected_text, new_gamma, correction_applied
    
    def _calculate_coherence(self, text: str, context: str) -> float:
        """一貫性スコア計算（簡易版）"""
        if not context or len(text) < 10:
            return 1.0
        
        # 簡易的な一貫性チェック
        context_chars = set(context.lower())
        text_chars = set(text.lower())
        
        # 文字レベルでの類似度
        common_chars = context_chars & text_chars
        if len(context_chars) == 0:
            return 1.0
        
        char_similarity = len(common_chars) / len(context_chars)
        
        # 長さの一貫性
        length_ratio = min(len(text), len(context)) / max(len(text), len(context), 1)
        
        coherence_score = (char_similarity * 0.6 + length_ratio * 0.4)
        return min(coherence_score, 1.0)
    
    def _calculate_repetition_rate(self, text: str) -> float:
        """反復率計算"""
        if len(text) < 4:
            return 0.0
        
        repetition_count = 0
        
        # 2文字以上の反復検出
        for length in range(2, min(8, len(text) // 3)):
            for i in range(len(text) - length):
                phrase = text[i:i+length]
                if text.count(phrase) > 1:
                    repetition_count += 1
        
        return min(repetition_count / len(text), 1.0)
    
    def _update_stats(self, metrics: QualityMetrics, processing_time: float):
        """統計情報更新"""
        self.stats['total_checks'] += 1
        
        # 品質履歴追加
        self.quality_history.append({
            'timestamp': time.time(),
            'metrics': metrics.to_dict(),
            'processing_time': processing_time
        })
        
        # 履歴サイズ制限
        if len(self.quality_history) > self.max_history_size:
            self.quality_history.pop(0)
        
        # 平均品質スコア更新
        recent_scores = [h['metrics']['overall_score'] for h in self.quality_history[-20:]]
        self.stats['average_quality_score'] = sum(recent_scores) / len(recent_scores)
        
        # エラー防止率計算
        recent_error_counts = [h['metrics']['error_count'] for h in self.quality_history[-20:]]
        avg_errors = sum(recent_error_counts) / len(recent_error_counts)
        self.stats['error_prevention_rate'] = max(0.0, 1.0 - avg_errors / 10.0)
    
    def get_quality_report(self) -> Dict[str, Any]:
        """品質レポート生成"""
        if not self.quality_history:
            return {"message": "品質データがありません"}
        
        recent_metrics = [h['metrics'] for h in self.quality_history[-10:]]
        
        # 平均値計算
        avg_grammar = sum(m['grammar_score'] for m in recent_metrics) / len(recent_metrics)
        avg_sense = sum(m['sense_score'] for m in recent_metrics) / len(recent_metrics)
        avg_diversity = sum(m['diversity_score'] for m in recent_metrics) / len(recent_metrics)
        avg_overall = sum(m['overall_score'] for m in recent_metrics) / len(recent_metrics)
        
        # トレンド分析
        scores_trend = [m['overall_score'] for m in recent_metrics]
        trend_direction = "改善" if len(scores_trend) > 1 and scores_trend[-1] > scores_trend[0] else "安定"
        
        return {
            'enabled': self.enabled,
            'error_threshold': self.error_threshold * 100,
            'diversity_target': self.diversity_target * 100,
            'statistics': self.stats,
            'recent_averages': {
                'grammar_score': avg_grammar,
                'sense_score': avg_sense,
                'diversity_score': avg_diversity,
                'overall_score': avg_overall
            },
            'quality_trend': trend_direction,
            'total_evaluations': len(self.quality_history),
            'recommendations': self._generate_recommendations(avg_diversity, avg_overall)
        }
    
    def _generate_recommendations(self, avg_diversity: float, avg_overall: float) -> List[str]:
        """改善提案生成"""
        recommendations = []
        
        if avg_diversity < self.diversity_target:
            recommendations.append(f"語彙多様性向上: 現在{avg_diversity*100:.1f}% → 目標{self.diversity_target*100:.1f}%")
        
        if avg_overall < 0.8:
            recommendations.append(f"全体品質向上: 現在{avg_overall*100:.1f}% → 推奨80%以上")
        
        if self.stats['corrections_applied'] > self.stats['total_checks'] * 0.1:
            recommendations.append("γ値のデフォルト設定見直しを検討")
        
        if not recommendations:
            recommendations.append("品質は良好です。現在の設定を維持してください")
        
        return recommendations
    
    def reset_stats(self):
        """統計リセット"""
        self.stats = {
            'total_checks': 0,
            'corrections_applied': 0,
            'gamma_adjustments': 0,
            'average_quality_score': 0.0,
            'error_prevention_rate': 0.0
        }
        self.quality_history.clear()
        print("🔄 品質ガード統計をリセットしました")

# 使用例とテスト関数
def test_quality_guard():
    """品質ガードシステムのテスト"""
    config = {
        'quality_guard_enabled': True,
        'auto_correction_threshold': 0.03,
        'diversity_target': 0.35,
        'gamma_adjustment_step': 0.01
    }
    
    guard = QualityGuard(config)
    
    # テストケース
    test_cases = [
        "こんにちは！今日はいい天気ですね。",  # 正常
        "あああああああああああああああああ！！！！！！",  # 反復過多
        "私ははははは嬉しいいいいいです。。。。",  # 文法エラー
        "Hello World 12345678901234567890",  # 異常語彙
    ]
    
    print("🧪 品質ガードシステムテスト開始")
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n--- テストケース {i} ---")
        print(f"入力: {text}")
        
        metrics = guard.evaluate_quality(text)
        print(f"品質スコア: {metrics.overall_score:.2f}")
        print(f"文法: {metrics.grammar_score:.2f}, 常識性: {metrics.sense_score:.2f}")
        print(f"多様性: {metrics.diversity_score:.2f}, エラー数: {metrics.error_count}")
        
        corrected, new_gamma, applied = guard.auto_correct_if_needed(text, 0.98)
        if applied:
            print(f"補正適用: {corrected}")
            print(f"γ調整: 0.98 → {new_gamma:.3f}")
        else:
            print("補正不要")
    
    # レポート生成
    report = guard.get_quality_report()
    print(f"\n📊 最終レポート:")
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_quality_guard() 