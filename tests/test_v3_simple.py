# -*- coding: utf-8 -*-
"""
v3システム簡単テスト
基本的な反復検出機能を単体でテストする
"""

import sys
import os

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.insert(0, src_dir)

from utils.repetition_suppressor_v3 import AdvancedRepetitionSuppressorV3

def test_basic_detection():
    """基本的な検出機能のテスト"""
    print("🔧 v3基本検出テスト開始")
    
    # 基本設定
    config = {
        'similarity_threshold': 0.40,
        'max_distance': 50,
        'min_compress_rate': 0.05,
        'enable_rhetorical_protection': False,  # 保護を無効化
        'debug_mode': True
    }
    
    suppressor = AdvancedRepetitionSuppressorV3(config)
    
    # テストケース1: 最も基本的な同語反復
    test_text = "お兄ちゃんお兄ちゃん、どこに行くのですかお兄ちゃん？"
    print(f"\n📝 テストテキスト: {test_text}")
    
    # 分析フェーズ
    analysis = suppressor.analyze_text_v3(test_text)
    print(f"\n🔍 分析結果:")
    print(f"   検出パターン数: {sum(len(patterns) for patterns in analysis['patterns'].values())}")
    
    for pattern_type, patterns in analysis['patterns'].items():
        if patterns:
            print(f"   {pattern_type}:")
            for pattern in patterns:
                print(f"     - '{pattern.pattern}' (出現{pattern.count}回, 重要度{pattern.severity:.2f})")
    
    # 処理実行
    result, metrics = suppressor.suppress_repetitions_with_debug_v3(test_text)
    print(f"\n📊 処理結果:")
    print(f"   入力長: {metrics.input_length}")
    print(f"   出力長: {metrics.output_length}")
    print(f"   圧縮率: {(metrics.input_length - metrics.output_length) / metrics.input_length * 100:.1f}%")
    print(f"   検出パターン: {metrics.patterns_detected}")
    print(f"   抑制パターン: {metrics.patterns_suppressed}")
    print(f"   成功率: {metrics.success_rate:.1%}")
    
    print(f"\n💬 元の文章: {test_text}")
    print(f"💬 処理後: {result}")
    
    return metrics.success_rate >= 0.7

def test_simple_cases():
    """複数の簡単なケースをテスト"""
    config = {
        'similarity_threshold': 0.40,
        'max_distance': 50,
        'min_compress_rate': 0.05,
        'enable_rhetorical_protection': False,
        'debug_mode': False
    }
    
    suppressor = AdvancedRepetitionSuppressorV3(config)
    
    test_cases = [
        "あああああ",  # 単純な文字反復
        "そうですそうです",  # 語句反復
        "はいはいはい",  # 短い語反復
        "www777",  # 連番
    ]
    
    print(f"\n🧪 複数ケーステスト:")
    
    for i, text in enumerate(test_cases, 1):
        result, metrics = suppressor.suppress_repetitions_with_debug_v3(text)
        compression = (metrics.input_length - metrics.output_length) / metrics.input_length * 100
        print(f"   {i}. '{text}' → '{result}' (圧縮率: {compression:.1f}%, 成功率: {metrics.success_rate:.1%})")

if __name__ == "__main__":
    try:
        print("🚀 v3システム単体テスト")
        success = test_basic_detection()
        test_simple_cases()
        
        if success:
            print("\n✅ 基本テスト成功")
        else:
            print("\n❌ 基本テスト失敗")
    except Exception as e:
        print(f"\n💥 テストエラー: {e}")
        import traceback
        traceback.print_exc() 