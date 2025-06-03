# -*- coding: utf-8 -*-
"""
反復抑制システムテスト
実際のAI生成テキストで反復問題を再現・解決する
"""

import sys
import os
import time
from tqdm import tqdm

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


def test_repetition_cases():
    """実際の反復問題のテストケース"""
    
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
    
    # 実際のAI生成で発生しやすい反復パターン
    test_cases = [
        {
            "name": "感嘆詞過多",
            "text": "あああああ…！ オス様…！ あああああ…！ うわああああああああああああぁっ…！ あああああぁあぁっ…！",
            "character": "樹里"
        },
        {
            "name": "同一語句反復",
            "text": "嬉しいです嬉しいです。とても嬉しいです嬉しいです。本当に嬉しい気持ちです。",
            "character": "一般キャラ"
        },
        {
            "name": "接続詞反復",
            "text": "そうですねそうですね。でもでもでも、やっぱりやっぱりやっぱり難しいですね。",
            "character": "一般キャラ"
        },
        {
            "name": "感嘆表現連続",
            "text": "ひゃあああああ！ きゃああああ！ わああああ！ うわああああ！ ひゃあああ！",
            "character": "美里"
        },
        {
            "name": "文字連続反復",
            "text": "んんんんんんん…！ っっっっっ…！ あああああああ…！ うううううう…！",
            "character": "樹里"
        },
        {
            "name": "語尾反復",
            "text": "ですですです。ますますます。だっただっただった。でしょでしょでしょ。",
            "character": "一般キャラ"
        },
        {
            "name": "複合反復パターン",
            "text": "あああああ！ オス様オス様！ うわああああ！ 嬉しい嬉しい嬉しい！ そうですねそうですね！ あああああ！",
            "character": "樹里"
        },
        {
            "name": "音韻類似反復",
            "text": "きゃあきゃあ！ ぎゃあぎゃあ！ ひゃあひゃあ！ じゃあじゃあ！",
            "character": "美里"
        }
    ]
    
    print("🎯 反復抑制システム包括テスト")
    print("=" * 60)
    
    total_improvement = 0
    successful_suppressions = 0
    
    for i, case in enumerate(tqdm(test_cases, desc="テスト実行中"), 1):
        print(f"\n📝 テストケース {i}: {case['name']}")
        print(f"キャラクター: {case['character']}")
        print(f"原文 ({len(case['text'])}文字):")
        print(f"  {case['text']}")
        
        # 分析実行
        analysis = suppressor.analyze_text(case['text'], case['character'])
        
        # 反復抑制実行
        start_time = time.time()
        suppressed_text = suppressor.suppress_repetitions(case['text'], case['character'])
        processing_time = time.time() - start_time
        
        print(f"改善後 ({len(suppressed_text)}文字):")
        print(f"  {suppressed_text}")
        
        # 改善効果の計算
        improvement_rate = 1.0 - (analysis['total_severity'] if analysis['total_severity'] > 0 else 0)
        text_changed = case['text'] != suppressed_text
        
        if text_changed:
            successful_suppressions += 1
            total_improvement += improvement_rate
        
        # 分析結果の表示
        print(f"📊 分析結果:")
        print(f"  - 反復重要度: {analysis['total_severity']:.3f}")
        print(f"  - 処理時間: {processing_time:.3f}秒")
        print(f"  - テキスト変更: {'✅ あり' if text_changed else '❌ なし'}")
        print(f"  - 改善率: {improvement_rate:.1%}")
        
        # パターン詳細
        pattern_summary = {}
        for pattern_type, patterns in analysis['patterns'].items():
            if patterns:
                pattern_summary[pattern_type] = len(patterns)
        
        if pattern_summary:
            print(f"  - 検出パターン: {pattern_summary}")
        
        print("-" * 50)
        
        # 小休止（システム負荷軽減）
        time.sleep(0.1)
    
    # 総合結果
    print(f"\n🏆 総合テスト結果")
    print("=" * 60)
    print(f"総テストケース数: {len(test_cases)}")
    print(f"成功した抑制数: {successful_suppressions}")
    print(f"成功率: {successful_suppressions / len(test_cases):.1%}")
    if successful_suppressions > 0:
        print(f"平均改善率: {total_improvement / successful_suppressions:.1%}")
    
    # システム統計
    stats = suppressor.get_statistics()
    print(f"\n📊 システム統計:")
    print(f"- 総分析回数: {stats.get('total_analyses', 0)}")
    print(f"- 平均重要度: {stats.get('average_severity', 0):.3f}")
    print(f"- キャッシュサイズ: {stats.get('replacement_cache_size', 0)}")
    
    pattern_distribution = stats.get('pattern_type_distribution', {})
    if pattern_distribution:
        print(f"- パターン分布: {pattern_distribution}")
    
    # キャラクター別統計
    char_stats = stats.get('character_statistics', {})
    if char_stats:
        print(f"\n👤 キャラクター別統計:")
        for char, char_data in char_stats.items():
            print(f"  - {char}: {char_data['total_patterns']}パターン (平均重要度: {char_data['avg_severity']:.3f})")
    
    return stats


def benchmark_performance():
    """パフォーマンスベンチマーク"""
    
    if not SUPPRESSOR_AVAILABLE:
        print("反復抑制システムが利用できません")
        return
    
    print("\n⚡ パフォーマンスベンチマーク")
    print("=" * 60)
    
    suppressor = AdvancedRepetitionSuppressor()
    
    # さまざまなサイズのテキストでベンチマーク
    test_sizes = [
        (50, "あああああ！ オス様！ うわああああ！"),
        (100, "あああああ！ オス様！ うわああああ！ " * 3),
        (200, "あああああ！ オス様！ うわああああ！ 嬉しい嬉しい！ " * 5),
        (500, "あああああ！ オス様！ うわああああ！ 嬉しい嬉しい！ そうですねそうですね。" * 10),
        (1000, "あああああ！ オス様！ うわああああ！ 嬉しい嬉しい！ そうですねそうですね。でもでも。" * 20)
    ]
    
    for target_size, base_text in test_sizes:
        # テキストを目標サイズに調整
        multiplier = max(1, target_size // len(base_text))
        test_text = (base_text + " ") * multiplier
        actual_size = len(test_text)
        
        # ベンチマーク実行
        times = []
        for _ in range(3):  # 3回実行して平均を取る
            start_time = time.time()
            result = suppressor.suppress_repetitions(test_text, "ベンチマークキャラ")
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        chars_per_second = actual_size / avg_time
        
        print(f"テキストサイズ: {actual_size:4d}文字 | 処理時間: {avg_time:.3f}秒 | 速度: {chars_per_second:.0f}文字/秒")
    
    print("=" * 60)


def test_edge_cases():
    """エッジケースのテスト"""
    
    if not SUPPRESSOR_AVAILABLE:
        print("反復抑制システムが利用できません")
        return
    
    print("\n🔍 エッジケーステスト")
    print("=" * 60)
    
    suppressor = AdvancedRepetitionSuppressor()
    
    edge_cases = [
        ("空文字", ""),
        ("単一文字", "あ"),
        ("短いテキスト", "こんにちは"),
        ("英数字のみ", "Hello 123"),
        ("記号のみ", "！？…〜"),
        ("カタカナのみ", "アイウエオアイウエオ"),
        ("漢字のみ", "日本語日本語"),
        ("混合文字", "Hello あああ 123 ！！！"),
        ("超長反復", "あ" * 100),
        ("複雑な記号", "「」『』（）【】〈〉《》"),
    ]
    
    for name, text in edge_cases:
        try:
            result = suppressor.suppress_repetitions(text, "エッジテストキャラ")
            status = "✅ 成功"
            
            if text != result:
                status += f" (変更あり)"
            else:
                status += f" (変更なし)"
                
        except Exception as e:
            status = f"❌ エラー: {e}"
            result = "N/A"
        
        print(f"{name:12s}: {status}")
        if len(text) <= 50 and len(str(result)) <= 50:
            print(f"             原文: '{text}'")
            print(f"             結果: '{result}'")
        print()


if __name__ == "__main__":
    print("🚀 反復抑制システム総合テスト開始")
    print("=" * 70)
    
    try:
        # メインテスト
        stats = test_repetition_cases()
        
        # パフォーマンステスト
        benchmark_performance()
        
        # エッジケーステスト
        test_edge_cases()
        
        print("\n🎉 すべてのテストが完了しました")
        
    except KeyboardInterrupt:
        print("\n⏹️ テストが中断されました")
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc() 