# -*- coding: utf-8 -*-
"""
NKAT表現空間拡大実証デモ
NKATがどの程度表現空間を広げているかを定量的・視覚的に実証
"""

import sys
import os
import time
import json
import re
import random
from typing import Dict, List, Tuple
from collections import defaultdict
import numpy as np

# 拡張エンジンのインポート
try:
    from enhanced_nkat_expression_engine import ExpressionExpansionEngine, NKATExpressionIntegration
    ENHANCED_ENGINE_AVAILABLE = True
except ImportError:
    ENHANCED_ENGINE_AVAILABLE = False

class NKATSpaceExpansionDemo:
    """NKAT表現空間拡大実証デモ"""
    
    def __init__(self):
        self.expansion_engine = ExpressionExpansionEngine() if ENHANCED_ENGINE_AVAILABLE else None
        self.test_results = []
        
        print("🌟 NKAT表現空間拡大実証デモ初期化完了")
        print(f"Enhanced Engine: {'✅ 利用可能' if ENHANCED_ENGINE_AVAILABLE else '❌ 利用不可'}")
    
    def analyze_text_diversity(self, text: str) -> Dict[str, float]:
        """テキストの表現多様性を詳細分析"""
        
        if not text or len(text.strip()) == 0:
            return {"vocabulary_diversity": 0, "pattern_diversity": 0, "emotion_diversity": 0, 
                   "style_variance": 0, "uniqueness_score": 0}
        
        # 語彙抽出
        words = re.findall(r'[ぁ-ゖァ-ヺー一-龯]+', text)
        words = [word for word in words if len(word) >= 2]  # 助詞等除外
        
        # 1. 語彙多様性 (Type-Token Ratio)
        vocab_diversity = len(set(words)) / max(len(words), 1)
        
        # 2. 文型パターン多様性
        sentences = re.split(r'[。！？]', text)
        sentence_patterns = []
        for sentence in sentences:
            if len(sentence.strip()) > 0:
                if sentence.endswith(("です", "ます")):
                    sentence_patterns.append("polite")
                elif sentence.endswith(("だ", "である")):
                    sentence_patterns.append("assertive")
                elif "…" in sentence or "〜" in sentence:
                    sentence_patterns.append("emotional")
                else:
                    sentence_patterns.append("neutral")
        
        pattern_diversity = len(set(sentence_patterns)) / max(len(sentence_patterns), 1)
        
        # 3. 感情表現多様性
        emotional_expressions = []
        # 感嘆符パターン
        emotional_expressions.extend(re.findall(r'[！？…〜ー]+', text))
        # 感情語彙
        emotion_words = ["嬉しい", "悲しい", "怒り", "驚き", "わあ", "すごい", "きれい"]
        for word in emotion_words:
            if word in text:
                emotional_expressions.append(word)
        
        emotion_diversity = len(set(emotional_expressions)) / max(len(emotional_expressions), 1) if emotional_expressions else 0
        
        # 4. 文体変化度（文長の変動係数）
        sentence_lengths = [len(s.strip()) for s in sentences if len(s.strip()) > 0]
        if len(sentence_lengths) >= 2:
            mean_length = np.mean(sentence_lengths)
            std_length = np.std(sentence_lengths)
            style_variance = std_length / max(mean_length, 1)
        else:
            style_variance = 0
        
        # 5. 表現独自性（n-gramユニーク度）
        if len(text) >= 3:
            char_2grams = [text[i:i+2] for i in range(len(text)-1)]
            char_3grams = [text[i:i+3] for i in range(len(text)-2)]
            
            char_2gram_uniqueness = len(set(char_2grams)) / max(len(char_2grams), 1)
            char_3gram_uniqueness = len(set(char_3grams)) / max(len(char_3grams), 1)
            
            uniqueness_score = (char_2gram_uniqueness + char_3gram_uniqueness) / 2
        else:
            uniqueness_score = 1.0
        
        return {
            "vocabulary_diversity": vocab_diversity,
            "pattern_diversity": pattern_diversity,
            "emotion_diversity": emotion_diversity,
            "style_variance": style_variance,
            "uniqueness_score": uniqueness_score,
            "total_words": len(words),
            "unique_words": len(set(words)),
            "sentence_count": len([s for s in sentences if s.strip()]),
            "character_count": len(text)
        }
    
    def calculate_expansion_rate(self, before: Dict, after: Dict) -> Dict[str, float]:
        """表現空間拡大率の計算"""
        
        improvements = {}
        metrics = ["vocabulary_diversity", "pattern_diversity", "emotion_diversity", 
                  "style_variance", "uniqueness_score"]
        
        for metric in metrics:
            before_val = before.get(metric, 0)
            after_val = after.get(metric, 0)
            
            if before_val > 0:
                improvement = (after_val - before_val) / before_val
            else:
                improvement = after_val
            
            improvements[f"{metric}_improvement"] = improvement
            improvements[f"{metric}_before"] = before_val
            improvements[f"{metric}_after"] = after_val
        
        # 総合拡大率
        improvement_values = [improvements[f"{metric}_improvement"] for metric in metrics]
        improvements["overall_expansion"] = np.mean(improvement_values)
        
        return improvements
    
    def run_expansion_demo(self):
        """表現空間拡大デモの実行"""
        
        print("\n🚀 NKAT表現空間拡大実証デモ開始")
        print("=" * 80)
        
        # テストケース定義
        test_cases = [
            {
                "name": "感情表現の単調性",
                "original": "嬉しいです。とても嬉しいです。本当に嬉しいです。嬉しい気持ちです。",
                "character": "樹里",
                "description": "同一感情表現の連続使用による表現力の限定"
            },
            {
                "name": "反復表現の単純性",
                "original": "あああああ…！ あああああ…！ うわああああ…！ あああああ…！",
                "character": "樹里", 
                "description": "感嘆詞の単純反復による感情表現の貧困化"
            },
            {
                "name": "語彙選択の限定性",
                "original": "そうですね。そうですね。でも難しいですね。やっぱり難しいですね。",
                "character": "美里",
                "description": "接続詞・副詞の反復による語彙多様性の欠如"
            },
            {
                "name": "文体パターンの均一性",
                "original": "きれいです。すてきです。いいですね。よいですね。",
                "character": "美里",
                "description": "敬語パターンの均一化による文体変化の欠如"
            },
            {
                "name": "感嘆表現の貧困性",
                "original": "わあ！わあ！すごい！わあ！きれい！わあ！",
                "character": "美里",
                "description": "限定的な感嘆語による感情表現の単調化"
            }
        ]
        
        successful_expansions = 0
        total_expansion_rate = 0
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n📝 テストケース {i}: {case['name']}")
            print(f"キャラクター: {case['character']}")
            print(f"問題: {case['description']}")
            print(f"原文: 「{case['original']}」")
            
            # 拡張前分析
            before_analysis = self.analyze_text_diversity(case['original'])
            
            # NKAT表現拡張実行
            if ENHANCED_ENGINE_AVAILABLE:
                start_time = time.time()
                expanded_text = self.expansion_engine.expand_expression(
                    case['original'], case['character']
                )
                processing_time = time.time() - start_time
            else:
                expanded_text = case['original']
                processing_time = 0
            
            print(f"拡張後: 「{expanded_text}」")
            
            # 拡張後分析
            after_analysis = self.analyze_text_diversity(expanded_text)
            
            # 拡大効果計算
            expansion_results = self.calculate_expansion_rate(before_analysis, after_analysis)
            
            # 結果表示
            print(f"\n📊 表現空間拡大効果:")
            print(f"  🔤 語彙多様性: {before_analysis['vocabulary_diversity']:.3f} → {after_analysis['vocabulary_diversity']:.3f} ({expansion_results['vocabulary_diversity_improvement']:+.1%})")
            print(f"  📝 文型多様性: {before_analysis['pattern_diversity']:.3f} → {after_analysis['pattern_diversity']:.3f} ({expansion_results['pattern_diversity_improvement']:+.1%})")
            print(f"  💖 感情多様性: {before_analysis['emotion_diversity']:.3f} → {after_analysis['emotion_diversity']:.3f} ({expansion_results['emotion_diversity_improvement']:+.1%})")
            print(f"  🎭 文体変化度: {before_analysis['style_variance']:.3f} → {after_analysis['style_variance']:.3f} ({expansion_results['style_variance_improvement']:+.1%})")
            print(f"  ✨ 表現独自性: {before_analysis['uniqueness_score']:.3f} → {after_analysis['uniqueness_score']:.3f} ({expansion_results['uniqueness_score_improvement']:+.1%})")
            print(f"  🏆 総合拡大率: {expansion_results['overall_expansion']:+.1%}")
            print(f"  ⏱️ 処理時間: {processing_time:.3f}秒")
            
            # 拡大成功判定
            if expansion_results['overall_expansion'] > 0:
                successful_expansions += 1
                print("  ✅ 表現空間拡大成功")
            else:
                print("  ❌ 表現空間拡大なし")
            
            total_expansion_rate += expansion_results['overall_expansion']
            
            # 結果保存
            self.test_results.append({
                "case": case,
                "before": before_analysis,
                "after": after_analysis,
                "expansion": expansion_results,
                "expanded_text": expanded_text,
                "processing_time": processing_time
            })
            
            print("-" * 70)
        
        # 総合結果
        avg_expansion_rate = total_expansion_rate / len(test_cases)
        success_rate = successful_expansions / len(test_cases)
        
        print(f"\n🏆 NKAT表現空間拡大総合結果")
        print("=" * 80)
        print(f"📊 総テストケース数: {len(test_cases)}")
        print(f"✅ 拡大成功ケース: {successful_expansions}/{len(test_cases)} ({success_rate:.1%})")
        print(f"📈 平均拡大率: {avg_expansion_rate:+.1%}")
        
        # 詳細分析
        if ENHANCED_ENGINE_AVAILABLE:
            engine_stats = self.expansion_engine.get_expansion_stats()
            print(f"\n🔧 NKAT拡張エンジン統計:")
            print(f"  - 総拡張実行数: {engine_stats['total_expansions']}")
            print(f"  - 語彙追加数: {engine_stats['vocabulary_additions']}")
            print(f"  - 文体変化数: {engine_stats['style_variations']}")
            print(f"  - 感情強化数: {engine_stats['emotional_enhancements']}")
            print(f"  - パターン多様化数: {engine_stats['pattern_diversifications']}")
        
        # 結論
        print(f"\n🎯 結論:")
        if success_rate >= 0.6:
            print("✅ NKATシステムによる表現空間の拡大が確認されました！")
            print("📈 文章の表現多様性と語彙空間が有意に向上しています。")
        elif success_rate >= 0.3:
            print("🔶 NKATシステムによる部分的な表現空間拡大が確認されました。")
            print("🔧 更なる改善の余地があります。")
        else:
            print("❌ 現在のNKATシステムでは十分な表現空間拡大が確認できませんでした。")
            print("🔧 システムの見直しが必要です。")
        
        return self.test_results
    
    def save_detailed_report(self, filepath: str = "logs/nkat_expansion_report.json"):
        """詳細レポートの保存"""
        
        if not self.test_results:
            print("❌ 保存可能なテスト結果がありません")
            return
        
        # ディレクトリ作成
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # レポート作成
        report = {
            "timestamp": time.time(),
            "test_summary": {
                "total_cases": len(self.test_results),
                "successful_expansions": sum(1 for r in self.test_results if r['expansion']['overall_expansion'] > 0),
                "average_expansion": np.mean([r['expansion']['overall_expansion'] for r in self.test_results]),
                "enhanced_engine_used": ENHANCED_ENGINE_AVAILABLE
            },
            "detailed_results": self.test_results
        }
        
        # JSON保存
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📄 詳細レポートを保存: {filepath}")


def main():
    """メイン実行関数"""
    
    print("🌟 NKAT表現空間拡大実証システム")
    print("=" * 80)
    
    # デモ実行
    demo = NKATSpaceExpansionDemo()
    results = demo.run_expansion_demo()
    
    # レポート保存
    demo.save_detailed_report()
    
    print("\n🎉 NKAT表現空間拡大実証デモが完了しました")


if __name__ == "__main__":
    main() 