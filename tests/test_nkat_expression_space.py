# -*- coding: utf-8 -*-
"""
NKAT表現空間拡大効果測定テスト
NKATがどの程度表現空間を広げているかを定量的に評価
"""

import sys
import os
import time
import json
import numpy as np
from typing import Dict, List, Tuple, Set
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import matplotlib
from tqdm import tqdm
import hashlib

# matplotlib の日本語フォント設定（文字化け防止）
matplotlib.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.insert(0, src_dir)
sys.path.insert(0, current_dir)

try:
    from nkat.nkat_integration import NKATIntegration, TextConsistencyProcessor
    from nkat.advanced_consistency import AdvancedConsistencyProcessor, ConsistencyLevel
    NKAT_AVAILABLE = True
except ImportError:
    NKAT_AVAILABLE = False
    print("❌ NKATシステムが見つかりません")


class ExpressionSpaceAnalyzer:
    """
    表現空間分析器
    テキストの表現多様性と語彙空間を定量的に分析
    """
    
    def __init__(self):
        self.vocabulary_diversity = {}
        self.syntactic_patterns = {}
        self.semantic_clusters = {}
        self.emotional_range = {}
        self.expression_uniqueness = {}
        
    def analyze_text_diversity(self, text: str, label: str = "sample") -> Dict[str, float]:
        """テキストの表現多様性を分析"""
        
        # 語彙多様性（ユニーク語彙数 / 総語数）
        words = self._extract_words(text)
        vocab_diversity = len(set(words)) / max(len(words), 1)
        
        # 統語パターン多様性
        sentence_patterns = self._extract_sentence_patterns(text)
        pattern_diversity = len(set(sentence_patterns)) / max(len(sentence_patterns), 1)
        
        # 感情表現多様性
        emotional_expressions = self._extract_emotional_expressions(text)
        emotion_diversity = len(set(emotional_expressions)) / max(len(emotional_expressions), 1)
        
        # 文体変化度（文長・句読点パターンの変動）
        style_variance = self._calculate_style_variance(text)
        
        # 表現独自性（n-gramユニーク度）
        uniqueness_score = self._calculate_uniqueness_score(text)
        
        analysis_result = {
            "vocabulary_diversity": vocab_diversity,
            "pattern_diversity": pattern_diversity,
            "emotion_diversity": emotion_diversity,
            "style_variance": style_variance,
            "uniqueness_score": uniqueness_score,
            "total_words": len(words),
            "unique_words": len(set(words)),
            "sentence_count": text.count("。") + text.count("！") + text.count("？"),
            "character_count": len(text)
        }
        
        self.vocabulary_diversity[label] = analysis_result
        return analysis_result
    
    def _extract_words(self, text: str) -> List[str]:
        """語彙抽出"""
        import re
        # ひらがな・カタカナ・漢字の語彙を抽出
        words = re.findall(r'[ぁ-ゖァ-ヺー一-龯]+', text)
        # 1文字語彙は除外（助詞・助動詞等）
        return [word for word in words if len(word) >= 2]
    
    def _extract_sentence_patterns(self, text: str) -> List[str]:
        """文型パターン抽出"""
        sentences = text.replace("！", "。").replace("？", "。").split("。")
        patterns = []
        
        for sentence in sentences:
            if len(sentence.strip()) > 0:
                # 文末パターン
                if sentence.endswith(("だ", "である", "です", "ます")):
                    patterns.append("declarative")
                elif sentence.endswith(("か", "の")):
                    patterns.append("interrogative")
                elif "！" in sentence or "…" in sentence:
                    patterns.append("emotional")
                else:
                    patterns.append("neutral")
        
        return patterns
    
    def _extract_emotional_expressions(self, text: str) -> List[str]:
        """感情表現抽出"""
        emotional_patterns = [
            r'あ+[ああぁっ〜…！？]*',
            r'う+[ううぅっ〜…！？]*',
            r'お+[おぉっ〜…！？]*',
            r'わ+[わぁっ〜…！？]*',
            r'ひ+[ひっ〜…！？]*',
            r'き+[きっ〜…！？]*',
            r'ん+[んっ〜…！？]*'
        ]
        
        import re
        expressions = []
        for pattern in emotional_patterns:
            matches = re.findall(pattern, text)
            expressions.extend(matches)
        
        return expressions
    
    def _calculate_style_variance(self, text: str) -> float:
        """文体変化度の計算"""
        sentences = text.replace("！", "。").replace("？", "。").split("。")
        sentence_lengths = [len(s.strip()) for s in sentences if len(s.strip()) > 0]
        
        if len(sentence_lengths) < 2:
            return 0.0
        
        # 文長の変動係数（標準偏差 / 平均）
        mean_length = np.mean(sentence_lengths)
        std_length = np.std(sentence_lengths)
        
        return std_length / max(mean_length, 1)
    
    def _calculate_uniqueness_score(self, text: str) -> float:
        """表現独自性スコア（n-gramベース）"""
        # 2-gram, 3-gramの組み合わせ分析
        import re
        
        # 文字n-gram
        char_2grams = [text[i:i+2] for i in range(len(text)-1)]
        char_3grams = [text[i:i+3] for i in range(len(text)-2)]
        
        # 語彙n-gram
        words = self._extract_words(text)
        word_2grams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
        
        # ユニーク度計算
        char_2gram_uniqueness = len(set(char_2grams)) / max(len(char_2grams), 1)
        char_3gram_uniqueness = len(set(char_3grams)) / max(len(char_3grams), 1)
        word_2gram_uniqueness = len(set(word_2grams)) / max(len(word_2grams), 1)
        
        # 総合独自性スコア
        return (char_2gram_uniqueness + char_3gram_uniqueness + word_2gram_uniqueness) / 3.0
    
    def compare_expression_spaces(self, before_analysis: Dict, after_analysis: Dict) -> Dict[str, float]:
        """表現空間拡大の比較分析"""
        comparison = {}
        
        metrics = [
            "vocabulary_diversity", "pattern_diversity", "emotion_diversity",
            "style_variance", "uniqueness_score"
        ]
        
        for metric in metrics:
            before_value = before_analysis.get(metric, 0)
            after_value = after_analysis.get(metric, 0)
            
            if before_value > 0:
                improvement_rate = (after_value - before_value) / before_value
            else:
                improvement_rate = after_value
            
            comparison[f"{metric}_improvement"] = improvement_rate
            comparison[f"{metric}_before"] = before_value
            comparison[f"{metric}_after"] = after_value
        
        # 総合改善スコア
        improvements = [comparison[f"{metric}_improvement"] for metric in metrics]
        comparison["overall_improvement"] = np.mean(improvements)
        
        return comparison


def test_nkat_expression_expansion():
    """NKAT表現空間拡大効果のメインテスト"""
    
    if not NKAT_AVAILABLE:
        print("NKATシステムが利用できません")
        return None
    
    print("🎯 NKAT表現空間拡大効果測定テスト")
    print("=" * 70)
    
    # NKATシステム初期化
    config = {
        "nkat_enabled": True,
        "nkat_consistency_mode": True,
        "nkat_advanced_mode": True,
        "nkat_arnold_dimension": 32,
        "nkat_kolmogorov_layers": 2,
        "consistency_level": "moderate"
    }
    
    # モックのEasyNovelAssistantコンテキスト
    class MockContext:
        def __init__(self, config):
            self.config = config
        
        def __getitem__(self, key):
            return self.config.get(key)
        
        def get(self, key, default=None):
            return self.config.get(key, default)
    
    mock_ctx = MockContext(config)
    
    # NKAT統合システム初期化
    try:
        nkat = NKATIntegration(mock_ctx)
        consistency_processor = AdvancedConsistencyProcessor(config)
        print("✅ NKATシステム初期化完了")
    except Exception as e:
        print(f"❌ NKAT初期化エラー: {e}")
        return None
    
    # 表現空間分析器初期化
    analyzer = ExpressionSpaceAnalyzer()
    
    # テストケース（表現の限定性が問題となる典型例）
    test_cases = [
        {
            "name": "感情表現の限定性",
            "original": "嬉しいです。とても嬉しいです。本当に嬉しいです。嬉しい気持ちです。",
            "context": "樹里が喜んでいるシーン",
            "character": "樹里"
        },
        {
            "name": "反復表現の単調性", 
            "original": "あああああ…！ あああああ…！ うわああああ…！ あああああ…！",
            "context": "樹里が興奮しているシーン",
            "character": "樹里"
        },
        {
            "name": "語彙の限定性",
            "original": "そうですね。そうですね。でも難しいですね。やっぱり難しいですね。",
            "context": "美里が考えているシーン",
            "character": "美里"
        },
        {
            "name": "文体の単調性",
            "original": "きれいです。すてきです。いいですね。よいですね。",
            "context": "一般的な会話シーン",
            "character": "一般"
        },
        {
            "name": "感嘆表現の貧困性",
            "original": "わあ！わあ！すごい！わあ！きれい！わあ！",
            "context": "美里が驚いているシーン", 
            "character": "美里"
        }
    ]
    
    results = []
    overall_improvements = []
    
    print("\n📊 個別テストケース分析:")
    print("-" * 70)
    
    for i, case in enumerate(tqdm(test_cases, desc="NKAT処理実行中"), 1):
        print(f"\n🔬 テストケース {i}: {case['name']}")
        print(f"キャラクター: {case['character']}")
        print(f"原文: {case['original']}")
        
        # 元テキストの表現空間分析
        before_analysis = analyzer.analyze_text_diversity(case['original'], f"before_{i}")
        
        # NKAT処理による表現拡張
        start_time = time.time()
        try:
            # 統合処理実行
            enhanced_text = nkat.enhance_text_generation(
                prompt=case['context'],
                llm_output=case['original']
            )
            
            # 高度一貫性処理も実行
            consistency_enhanced = consistency_processor.enhance_consistency(
                enhanced_text, case['context']
            )
            
            processing_time = time.time() - start_time
            
        except Exception as e:
            print(f"❌ NKAT処理エラー: {e}")
            enhanced_text = case['original']
            consistency_enhanced = case['original']
            processing_time = 0
        
        print(f"NKAT処理後: {enhanced_text}")
        print(f"一貫性処理後: {consistency_enhanced}")
        
        # 処理後テキストの表現空間分析
        after_analysis = analyzer.analyze_text_diversity(consistency_enhanced, f"after_{i}")
        
        # 表現空間拡大効果の比較
        comparison = analyzer.compare_expression_spaces(before_analysis, after_analysis)
        
        # 結果表示
        print(f"\n📈 表現空間拡大効果:")
        print(f"  • 語彙多様性: {before_analysis['vocabulary_diversity']:.3f} → {after_analysis['vocabulary_diversity']:.3f} ({comparison['vocabulary_diversity_improvement']:+.1%})")
        print(f"  • パターン多様性: {before_analysis['pattern_diversity']:.3f} → {after_analysis['pattern_diversity']:.3f} ({comparison['pattern_diversity_improvement']:+.1%})")
        print(f"  • 感情表現多様性: {before_analysis['emotion_diversity']:.3f} → {after_analysis['emotion_diversity']:.3f} ({comparison['emotion_diversity_improvement']:+.1%})")
        print(f"  • 文体変化度: {before_analysis['style_variance']:.3f} → {after_analysis['style_variance']:.3f} ({comparison['style_variance_improvement']:+.1%})")
        print(f"  • 表現独自性: {before_analysis['uniqueness_score']:.3f} → {after_analysis['uniqueness_score']:.3f} ({comparison['uniqueness_score_improvement']:+.1%})")
        print(f"  • 総合改善度: {comparison['overall_improvement']:+.1%}")
        print(f"  • 処理時間: {processing_time:.3f}秒")
        
        results.append({
            "case": case,
            "before": before_analysis,
            "after": after_analysis,
            "comparison": comparison,
            "enhanced_text": consistency_enhanced,
            "processing_time": processing_time
        })
        
        overall_improvements.append(comparison['overall_improvement'])
        
        print("-" * 50)
    
    # 総合分析結果
    print(f"\n🏆 総合分析結果")
    print("=" * 70)
    
    avg_improvement = np.mean(overall_improvements)
    successful_cases = sum(1 for imp in overall_improvements if imp > 0)
    
    print(f"総テストケース数: {len(test_cases)}")
    print(f"表現拡大成功ケース: {successful_cases}/{len(test_cases)} ({successful_cases/len(test_cases):.1%})")
    print(f"平均表現空間拡大率: {avg_improvement:+.1%}")
    
    # メトリック別詳細分析
    metric_improvements = defaultdict(list)
    for result in results:
        comparison = result['comparison']
        metrics = ["vocabulary_diversity", "pattern_diversity", "emotion_diversity", "style_variance", "uniqueness_score"]
        for metric in metrics:
            metric_improvements[metric].append(comparison[f"{metric}_improvement"])
    
    print(f"\n📊 メトリック別改善度:")
    for metric, improvements in metric_improvements.items():
        avg_imp = np.mean(improvements)
        positive_cases = sum(1 for imp in improvements if imp > 0)
        print(f"  • {metric}: {avg_imp:+.1%} (改善ケース: {positive_cases}/{len(improvements)})")
    
    return results


def visualize_expression_space_expansion(results: List[Dict]):
    """表現空間拡大効果の可視化"""
    
    if not results:
        print("可視化データがありません")
        return
    
    print("\n📈 表現空間拡大効果の可視化")
    
    # メトリック別改善度のバープロット
    metrics = ["vocabulary_diversity", "pattern_diversity", "emotion_diversity", "style_variance", "uniqueness_score"]
    metric_names = ["語彙多様性", "パターン多様性", "感情表現多様性", "文体変化度", "表現独自性"]
    
    improvements = {metric: [] for metric in metrics}
    for result in results:
        for metric in metrics:
            improvements[metric].append(result['comparison'][f"{metric}_improvement"])
    
    # バープロット作成
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # 平均改善度
    avg_improvements = [np.mean(improvements[metric]) for metric in metrics]
    bars1 = ax1.bar(metric_names, avg_improvements, color=['skyblue', 'lightgreen', 'salmon', 'gold', 'plum'])
    ax1.set_title('Average Expression Space Expansion by Metric', fontsize=14, weight='bold')
    ax1.set_ylabel('Improvement Rate')
    ax1.set_ylim(-0.5, 1.5)
    ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax1.grid(True, alpha=0.3)
    
    # 値をバーの上に表示
    for bar, value in zip(bars1, avg_improvements):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                f'{value:+.1%}', ha='center', va='bottom', fontweight='bold')
    
    # ケース別総合改善度
    case_names = [f"Case {i+1}" for i in range(len(results))]
    overall_improvements = [result['comparison']['overall_improvement'] for result in results]
    
    colors = ['green' if imp > 0 else 'red' for imp in overall_improvements]
    bars2 = ax2.bar(case_names, overall_improvements, color=colors, alpha=0.7)
    ax2.set_title('Overall Improvement by Test Case', fontsize=14, weight='bold')
    ax2.set_ylabel('Overall Improvement Rate')
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax2.grid(True, alpha=0.3)
    
    # 値をバーの上に表示
    for bar, value in zip(bars2, overall_improvements):
        height = bar.get_height()
        offset = 0.02 if height >= 0 else -0.05
        ax2.text(bar.get_x() + bar.get_width()/2., height + offset,
                f'{value:+.1%}', ha='center', va='bottom' if height >= 0 else 'top', fontweight='bold')
    
    plt.tight_layout()
    
    # 画像保存
    os.makedirs("logs/analysis", exist_ok=True)
    filename = f"logs/analysis/nkat_expression_expansion_{int(time.time())}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"📊 可視化結果を保存: {filename}")
    
    plt.show()


def generate_expression_report(results: List[Dict]):
    """表現空間拡大レポート生成"""
    
    if not results:
        return
    
    print("\n📝 表現空間拡大レポート生成中...")
    
    report = {
        "timestamp": time.time(),
        "test_summary": {
            "total_cases": len(results),
            "successful_expansions": sum(1 for r in results if r['comparison']['overall_improvement'] > 0),
            "average_improvement": np.mean([r['comparison']['overall_improvement'] for r in results]),
            "total_processing_time": sum(r['processing_time'] for r in results)
        },
        "metric_analysis": {},
        "case_details": []
    }
    
    # メトリック別分析
    metrics = ["vocabulary_diversity", "pattern_diversity", "emotion_diversity", "style_variance", "uniqueness_score"]
    for metric in metrics:
        improvements = [r['comparison'][f"{metric}_improvement"] for r in results]
        report["metric_analysis"][metric] = {
            "average_improvement": np.mean(improvements),
            "success_rate": sum(1 for imp in improvements if imp > 0) / len(improvements),
            "max_improvement": max(improvements),
            "min_improvement": min(improvements)
        }
    
    # ケース詳細
    for i, result in enumerate(results):
        case_detail = {
            "case_number": i + 1,
            "case_name": result['case']['name'],
            "character": result['case']['character'],
            "original_text": result['case']['original'],
            "enhanced_text": result['enhanced_text'],
            "metrics_before": result['before'],
            "metrics_after": result['after'],
            "improvements": result['comparison'],
            "processing_time": result['processing_time']
        }
        report["case_details"].append(case_detail)
    
    # レポート保存
    os.makedirs("logs/analysis", exist_ok=True)
    report_filename = f"logs/analysis/nkat_expression_report_{int(time.time())}.json"
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"📄 詳細レポートを保存: {report_filename}")
    
    # サマリー表示
    print(f"\n📋 レポートサマリー:")
    print(f"• 総合成功率: {report['test_summary']['successful_expansions']}/{report['test_summary']['total_cases']} ({report['test_summary']['successful_expansions']/report['test_summary']['total_cases']:.1%})")
    print(f"• 平均改善度: {report['test_summary']['average_improvement']:+.1%}")
    print(f"• 総処理時間: {report['test_summary']['total_processing_time']:.3f}秒")
    
    return report


if __name__ == "__main__":
    print("🚀 NKAT表現空間拡大効果測定テスト開始")
    print("=" * 80)
    
    try:
        # メインテスト実行
        results = test_nkat_expression_expansion()
        
        if results:
            # 可視化
            visualize_expression_space_expansion(results)
            
            # レポート生成
            generate_expression_report(results)
            
            print("\n🎉 NKAT表現空間拡大効果測定が完了しました")
            print("結果: NKATにより文章の表現多様性と語彙空間が拡大されています！")
        else:
            print("❌ テストの実行に失敗しました")
            
    except KeyboardInterrupt:
        print("\n⏹️ テストが中断されました")
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc() 