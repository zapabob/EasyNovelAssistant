# -*- coding: utf-8 -*-
"""
反復抑制システム統合デモ
EasyNovelAssistantで実際に語句反復問題を解決するデモ
"""

import sys
import os
import time

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.insert(0, src_dir)
sys.path.insert(0, current_dir)

try:
    from utils.repetition_suppressor import AdvancedRepetitionSuppressor
    SUPPRESSOR_AVAILABLE = True
except ImportError:
    SUPPRESSOR_AVAILABLE = False
    print("❌ 反復抑制システムが見つかりません")


def simulate_ai_generation_with_repetition():
    """
    AI生成で実際に発生する反復問題をシミュレート
    """
    
    # よくある反復パターンのシミュレーション
    repetitive_outputs = [
        {
            "prompt": "樹里が興奮している場面",
            "ai_output": "あああああ…！ オス様…！ あああああ…！ うわああああああああああああぁっ…！ あああああぁあぁっ…！ オス様の「キメオナ」を見ながら…！ あああああ…！"
        },
        {
            "prompt": "美里が喜んでいる場面", 
            "ai_output": "きゃあきゃあ！ 嬉しいです嬉しいです！ とても嬉しいです嬉しいです！ きゃあきゃあ！ 本当に嬉しい嬉しい！"
        },
        {
            "prompt": "一般的な会話シーン",
            "ai_output": "そうですねそうですね。でもでもでも、やっぱりやっぱりやっぱり難しいですね。そうですねそうですね。"
        },
        {
            "prompt": "感情的なシーン",
            "ai_output": "んんんんんんん…！ っっっっっ…！ ひゃあああああ！ んんんんんんん…！ うううううう…！"
        }
    ]
    
    if not SUPPRESSOR_AVAILABLE:
        print("反復抑制システムが利用できません")
        return
    
    # 反復抑制システムの初期化
    config = {
        'min_repeat_threshold': 2,
        'max_distance': 50,
        'similarity_threshold': 0.8,
        'phonetic_threshold': 0.9
    }
    
    suppressor = AdvancedRepetitionSuppressor(config)
    
    print("🎭 EasyNovelAssistant 反復抑制システム統合デモ")
    print("=" * 70)
    print("実際のAI生成で発生する語句反復問題を解決します\n")
    
    total_original_chars = 0
    total_improved_chars = 0
    total_processing_time = 0
    
    for i, case in enumerate(repetitive_outputs, 1):
        print(f"🎬 シナリオ {i}: {case['prompt']}")
        print("-" * 50)
        
        original_text = case['ai_output']
        total_original_chars += len(original_text)
        
        print(f"📝 AI生成結果 (オリジナル) - {len(original_text)}文字:")
        print(f"   {original_text}")
        print()
        
        # 反復分析
        start_time = time.time()
        analysis = suppressor.analyze_text(original_text, f"シナリオ{i}キャラ")
        
        # 反復抑制処理
        improved_text = suppressor.suppress_repetitions(original_text, f"シナリオ{i}キャラ")
        processing_time = time.time() - start_time
        total_processing_time += processing_time
        total_improved_chars += len(improved_text)
        
        print(f"✨ 反復抑制後 - {len(improved_text)}文字:")
        print(f"   {improved_text}")
        print()
        
        # 改善効果の分析
        char_reduction = len(original_text) - len(improved_text) 
        reduction_percent = (char_reduction / len(original_text)) * 100 if len(original_text) > 0 else 0
        
        print(f"📊 改善効果:")
        print(f"   • 反復重要度: {analysis['total_severity']:.2f}")
        print(f"   • 文字数削減: {char_reduction}文字 ({reduction_percent:.1f}%)")
        print(f"   • 処理時間: {processing_time:.3f}秒")
        print(f"   • 変更適用: {'✅ あり' if original_text != improved_text else '❌ なし'}")
        
        # 検出されたパターンの詳細
        pattern_details = []
        for pattern_type, patterns in analysis['patterns'].items():
            if patterns:
                pattern_details.append(f"{pattern_type}: {len(patterns)}個")
        
        if pattern_details:
            print(f"   • 検出パターン: {', '.join(pattern_details)}")
        
        print("\n" + "=" * 70 + "\n")
        
        # デモ用の小休止
        time.sleep(0.5)
    
    # 総合統計
    print("🏆 総合結果")
    print("=" * 70)
    print(f"処理シナリオ数: {len(repetitive_outputs)}")
    print(f"総文字数削減: {total_original_chars - total_improved_chars}文字")
    print(f"削減率: {((total_original_chars - total_improved_chars) / total_original_chars) * 100:.1f}%")
    print(f"総処理時間: {total_processing_time:.3f}秒")
    print(f"平均処理速度: {total_original_chars / total_processing_time:.0f}文字/秒")
    
    # システム統計
    stats = suppressor.get_statistics()
    print(f"\n📈 システム統計:")
    print(f"• 分析実行回数: {stats.get('total_analyses', 0)}")
    print(f"• 平均反復重要度: {stats.get('average_severity', 0):.2f}")
    print(f"• 代替表現キャッシュ: {stats.get('replacement_cache_size', 0)}個")
    
    pattern_distribution = stats.get('pattern_type_distribution', {})
    if pattern_distribution:
        print(f"• パターン検出分布:")
        for pattern_type, count in pattern_distribution.items():
            print(f"  - {pattern_type}: {count}個")
    
    return stats


def demonstrate_character_specific_patterns():
    """
    キャラクター固有の反復パターンの学習・適用デモ
    """
    
    if not SUPPRESSOR_AVAILABLE:
        return
    
    print("\n👤 キャラクター別反復パターン学習デモ")
    print("=" * 70)
    
    suppressor = AdvancedRepetitionSuppressor()
    
    # キャラクター別の特徴的な反復パターン
    character_patterns = {
        "樹里": [
            "あああああ…！ オス様…！ あああああ…！",
            "うわああああああああああああぁっ…！ あああああぁあぁっ…！",
            "オス様オス様…！ あああああ…！"
        ],
        "美里": [
            "きゃあきゃあ！ ひゃあひゃあ！ きゃあきゃあ！",
            "嬉しい嬉しい！ とても嬉しい嬉しい！",
            "わああああ！ きゃああああ！ わああああ！"
        ],
        "一般キャラ": [
            "そうですねそうですね。でもでもでも。",
            "ですですです。ますますます。",
            "だからだから。それでそれで。"
        ]
    }
    
    for character, patterns in character_patterns.items():
        print(f"\n🎭 {character}の反復パターン学習:")
        print("-" * 30)
        
        for i, pattern in enumerate(patterns, 1):
            print(f"  パターン{i}: {pattern}")
            
            # 分析・学習
            analysis = suppressor.analyze_text(pattern, character)
            improved = suppressor.suppress_repetitions(pattern, character)
            
            if pattern != improved:
                print(f"  → 改善: {improved}")
                print(f"    (重要度: {analysis['total_severity']:.2f})")
            else:
                print(f"    (変更なし)")
        
        print()
    
    # キャラクター別統計の表示
    stats = suppressor.get_statistics()
    char_stats = stats.get('character_statistics', {})
    
    if char_stats:
        print("📊 キャラクター別学習結果:")
        for character, char_data in char_stats.items():
            print(f"• {character}:")
            print(f"  - 学習パターン数: {char_data['total_patterns']}")
            print(f"  - 平均反復重要度: {char_data['avg_severity']:.3f}")


def demonstrate_real_time_processing():
    """
    リアルタイム処理のデモンストレーション
    """
    
    if not SUPPRESSOR_AVAILABLE:
        return
    
    print("\n⚡ リアルタイム反復抑制デモ")
    print("=" * 70)
    print("AI生成テキストをリアルタイムで反復抑制処理します\n")
    
    suppressor = AdvancedRepetitionSuppressor()
    
    # リアルタイム生成をシミュレート
    streaming_text_chunks = [
        "あああああ",
        "…！ オス様",
        "…！ あああああ",
        "…！ うわああああ",
        "ああああああ",
        "ああぁっ…！",
        "あああああぁあぁっ…！"
    ]
    
    accumulated_text = ""
    
    print("📡 ストリーミング生成シミュレーション:")
    
    for i, chunk in enumerate(streaming_text_chunks):
        accumulated_text += chunk
        
        print(f"\nチャンク {i+1}: '{chunk}'")
        print(f"累積テキスト: {accumulated_text}")
        
        # リアルタイム反復チェック
        if len(accumulated_text) > 10:  # 一定長度で反復チェック
            start_time = time.time()
            analysis = suppressor.analyze_text(accumulated_text)
            processing_time = time.time() - start_time
            
            if analysis['total_severity'] > 1.0:
                improved = suppressor.suppress_repetitions(accumulated_text)
                print(f"⚠️ 反復検出 (重要度: {analysis['total_severity']:.2f}) - 処理時間: {processing_time:.3f}秒")
                print(f"改善版: {improved}")
                accumulated_text = improved  # 改善版で継続
            else:
                print(f"✅ 反復問題なし (重要度: {analysis['total_severity']:.2f})")
        
        # ストリーミング効果のための遅延
        time.sleep(0.3)
    
    print(f"\n最終結果: {accumulated_text}")


if __name__ == "__main__":
    print("🚀 EasyNovelAssistant 反復抑制システム統合デモ開始")
    print("=" * 80)
    
    try:
        # メインデモ
        simulate_ai_generation_with_repetition()
        
        # キャラクター別学習デモ
        demonstrate_character_specific_patterns()
        
        # リアルタイム処理デモ
        demonstrate_real_time_processing()
        
        print("\n🎉 反復抑制システム統合デモが完了しました")
        print("これで「同じ語句が反復しやすい」問題が大幅に改善されます！")
        
    except KeyboardInterrupt:
        print("\n⏹️ デモが中断されました")
    except Exception as e:
        print(f"\n❌ デモ実行エラー: {e}")
        import traceback
        traceback.print_exc() 