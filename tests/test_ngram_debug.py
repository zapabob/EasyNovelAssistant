# -*- coding: utf-8 -*-
"""
3-gramブロック機能デバッグテスト（詳細版）
"""

import sys
import os
import re
from collections import Counter

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.insert(0, src_dir)

from utils.repetition_suppressor_v3 import AdvancedRepetitionSuppressorV3

def debug_ngram_extraction(text, ngram_size=3):
    """n-gram抽出処理を詳細デバッグ"""
    print(f"🔍 {ngram_size}-gram抽出デバッグ:")
    print(f"   テキスト: '{text}' (長さ: {len(text)})")
    
    if len(text) < ngram_size:
        print(f"   → 短すぎるためスキップ")
        return []
    
    # n-gramを抽出
    ngrams = []
    for i in range(len(text) - ngram_size + 1):
        ngram = text[i:i+ngram_size]
        has_japanese = re.search(r'[あ-んア-ン一-龯]', ngram)
        print(f"   位置{i}: '{ngram}' - 日本語?: {bool(has_japanese)}")
        
        if has_japanese:
            ngrams.append((ngram, i))
    
    # 重複を検出
    ngram_counts = Counter([ngram for ngram, _ in ngrams])
    repeated_ngrams = {ngram for ngram, count in ngram_counts.items() if count > 1}
    
    print(f"   抽出された{ngram_size}-gram: {len(ngrams)}個")
    print(f"   出現回数: {dict(ngram_counts)}")
    print(f"   重複パターン: {list(repeated_ngrams)}")
    
    return ngrams, repeated_ngrams

def test_ngram_blocking_detailed():
    """3-gramブロック機能の詳細テスト"""
    
    # テスト設定
    config = {
        'similarity_threshold': 0.30,
        'max_distance': 50,
        'min_compress_rate': 0.03,
        'enable_4gram_blocking': True,
        'ngram_block_size': 3,
        'enable_mecab_normalization': False,
        'enable_rhetorical_protection': False,
        'debug_mode': True
    }
    
    suppressor = AdvancedRepetitionSuppressorV3(config)
    
    # テストケース
    test_texts = [
        "今日は良い天気ですね。今日は良い天気だから散歩しましょう。",
        "あいうあいうあいう",
        "そやそやそや",
        "今日今日今日",
        "お兄ちゃんお兄ちゃん"
    ]
    
    print("🔧 3-gramブロック機能詳細デバッグテスト")
    print("=" * 60)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n📝 テスト {i}: {text}")
        
        # 手動でn-gram抽出をテスト
        ngrams, repeated = debug_ngram_extraction(text, 3)
        
        # 実際の3-gramブロック機能をテスト
        print(f"\n🔧 実際の3-gramブロック処理:")
        result = suppressor._apply_4gram_blocking(text)
        blocks_applied = getattr(suppressor, '_ngram_blocks_applied', 0)
        
        print(f"   入力: '{text}'")
        print(f"   出力: '{result}'")
        print(f"   ブロック適用回数: {blocks_applied}")
        print(f"   変化: {'あり' if text != result else 'なし'}")
        
        # カウンターリセット
        suppressor._ngram_blocks_applied = 0
        suppressor.debug_log = []
        
        print("-" * 60)

if __name__ == "__main__":
    test_ngram_blocking_detailed() 