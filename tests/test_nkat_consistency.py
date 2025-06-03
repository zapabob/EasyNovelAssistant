# -*- coding: utf-8 -*-
"""
NKAT文章一貫性向上機能テストスクリプト
出力される文章の一貫性問題を検証・改善
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nkat.nkat_integration import TextConsistencyProcessor
import json

def load_test_config():
    """テスト用設定の読み込み"""
    return {
        "nkat_enabled": True,
        "nkat_consistency_mode": True,
        "nkat_stability_factor": 0.8,
        "nkat_context_memory": 3,
        "nkat_smoothing_enabled": True,
        "nkat_cache_size": 100,
        "nkat_async_processing": False
    }

def test_consistency_improvement():
    """一貫性向上テスト"""
    print("=== NKAT文章一貫性向上テスト ===\n")
    
    # プロセッサ初期化
    config = load_test_config()
    processor = TextConsistencyProcessor(config)
    
    # テストケース
    test_cases = [
        {
            "context": "物語の始まり",
            "texts": [
                "静かな夜でした。月明かりが美しく照らしています。",
                "あああああああああああああ！！！！！ うわぁああああああああぁっ！！！",
                "そして彼女は微笑みました。",
                "ぎゃああああああああああああああああああああああ！！！！！！！！",
                "翌朝、鳥たちが歌い始めました。"
            ]
        },
        {
            "context": "感情的なシーン",
            "texts": [
                "悲しい気持ちになりました…",
                "うわあああああああああああああああああ！！！！！！！",
                "涙が頬を伝いました。",
                "あああああああああああああああああああ！！！！",
                "心が痛みます。"
            ]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"--- テストケース {i}: {test_case['context']} ---")
        
        for j, text in enumerate(test_case['texts'], 1):
            print(f"\n{j}. 入力テキスト:")
            print(f"   '{text}'")
            
            # 一貫性処理を適用
            processed = processor.maintain_consistency(text, test_case['context'])
            
            print(f"   処理後:")
            print(f"   '{processed}'")
            
            # 文体分析
            style = processor.analyze_text_style(processed)
            print(f"   文体分析: 感情強度={style['emotional_intensity']:.2f}, 反復={style['repetition_pattern']:.2f}")
        
        print("\n" + "="*60)
    
    # 統計情報出力
    stats = processor.get_performance_stats()
    print(f"\n=== 処理統計 ===")
    for key, value in stats.items():
        print(f"{key}: {value}")

def test_extreme_cases():
    """極端なケースのテスト"""
    print("\n=== 極端なケースのテスト ===\n")
    
    config = load_test_config()
    processor = TextConsistencyProcessor(config)
    
    extreme_cases = [
        "あああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああああ！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！",
        "。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。",
        "同じ同じ同じ同じ同じ同じ同じ同じ同じ同じ同じ同じ同じ同じ同じ同じ同じ同じ同じ同じ",
        "「」「」「」「」「」「」「」「」「」「」「」「」「」「」「」「」「」",
    ]
    
    for i, case in enumerate(extreme_cases, 1):
        print(f"{i}. 極端なケース:")
        print(f"   入力: '{case[:50]}{'...' if len(case) > 50 else ''}'")
        
        processed = processor.maintain_consistency(case, "極端テスト")
        print(f"   出力: '{processed[:50]}{'...' if len(processed) > 50 else ''}'")
        
        # 長さ比較
        print(f"   長さ変化: {len(case)} → {len(processed)}")
        print()

def main():
    """メイン関数"""
    try:
        print("NKAT文章一貫性向上機能テスト開始\n")
        
        # 基本テスト
        test_consistency_improvement()
        
        # 極端ケーステスト
        test_extreme_cases()
        
        print("\n✅ テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 