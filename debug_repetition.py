#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import traceback

# srcディレクトリをパスに追加
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_path)

print(f"Debug: srcパスを追加: {src_path}")

try:
    from utils.repetition_suppressor_v3 import AdvancedRepetitionSuppressorV3
    print("✅ 反復抑制システムv3の読み込み成功")
except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    traceback.print_exc()
    sys.exit(1)

def test_dialect_repetition():
    """方言反復テストのデバッグ"""
    
    config = {
        'similarity_threshold': 0.35,
        'max_distance': 50,
        'min_compress_rate': 0.03,
        'enable_4gram_blocking': True,
        'ngram_block_size': 3,
        'enable_drp': True,
        'drp_base': 1.10,
        'drp_alpha': 0.5,
        'enable_mecab_normalization': False,
        'enable_rhetorical_protection': False,
        'enable_latin_number_detection': True,
        'debug_mode': True
    }
    
    suppressor = AdvancedRepetitionSuppressorV3(config)
    
    # テストケース1: 方言反復
    input_text = "そやそやそや、あかんあかんあかん、やなやなそれは。"
    print(f"入力: {input_text}")
    print(f"入力長: {len(input_text)}")
    
    result, metrics = suppressor.suppress_repetitions_with_debug_v3(input_text, "関西弁キャラ")
    
    print(f"出力: {result}")
    print(f"出力長: {len(result)}")
    
    compression_rate = (len(input_text) - len(result)) / len(input_text)
    print(f"圧縮率: {compression_rate:.2%}")
    
    print(f"パターン検出: {metrics.patterns_detected}")
    print(f"パターン抑制: {metrics.patterns_suppressed}")
    print(f"成功率: {metrics.success_rate:.1%}")
    
    # テストケース2: 複合反復
    print("\n" + "="*50)
    input_text2 = "嬉しい嬉しい、楽しい楽しい、幸せ幸せという感じですです。"
    print(f"入力: {input_text2}")
    print(f"入力長: {len(input_text2)}")
    
    result2, metrics2 = suppressor.suppress_repetitions_with_debug_v3(input_text2, "ポジティブキャラ")
    
    print(f"出力: {result2}")
    print(f"出力長: {len(result2)}")
    
    compression_rate2 = (len(input_text2) - len(result2)) / len(input_text2)
    print(f"圧縮率: {compression_rate2:.2%}")
    
    print(f"パターン検出: {metrics2.patterns_detected}")
    print(f"パターン抑制: {metrics2.patterns_suppressed}")
    print(f"成功率: {metrics2.success_rate:.1%}")

if __name__ == "__main__":
    test_dialect_repetition() 