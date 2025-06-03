# -*- coding: utf-8 -*-
"""
高度一貫性機能包括テストスクリプト
キャラクター、感情、文体の一貫性を総合的にテスト
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nkat.advanced_consistency import AdvancedConsistencyProcessor, ConsistencyLevel
from nkat.nkat_integration import TextConsistencyProcessor
import json
import time

def load_test_config():
    """テスト用設定の読み込み"""
    return {
        "nkat_enabled": True,
        "nkat_consistency_mode": True,
        "nkat_stability_factor": 0.8,
        "nkat_context_memory": 3,
        "nkat_smoothing_enabled": True,
        "nkat_cache_size": 100,
        "nkat_async_processing": False,
        "nkat_advanced_mode": True,
        "consistency_level": "moderate",
        "character_memory_depth": 5,
        "emotion_smoothing_factor": 0.7,
        "style_adaptation_rate": 0.3
    }

def test_character_consistency():
    """キャラクター一貫性テスト"""
    print("=== キャラクター一貫性テスト ===\n")
    
    config = load_test_config()
    processor = AdvancedConsistencyProcessor(config)
    
    # キャラクター別テストケース
    character_dialogues = [
        {
            "character": "樹里",
            "dialogues": [
                "樹里：ああ…オス様…とても気持ちがいいです…",
                "樹里：優しく触れてください…お願いします…",
                "樹里：はい…そこです…もっと…",
                "樹里：うわああああああ！！！！激しすぎます！！！",  # 急激な変化
                "樹里：すみません…静かにします…"
            ]
        },
        {
            "character": "美里",
            "dialogues": [
                "美里：えっ…そんなこと…",
                "美里：恥ずかしいです…",
                "美里：でも…嬉しいかも…",
                "美里：ぎゃああああああああ！！！！",  # キャラクターに合わない表現
                "美里：ちょっと…驚きました…"
            ]
        }
    ]
    
    for char_data in character_dialogues:
        print(f"--- {char_data['character']}の一貫性テスト ---")
        
        for i, dialogue in enumerate(char_data['dialogues'], 1):
            print(f"\n{i}. 入力: {dialogue}")
            
            # キャラクター一貫性分析
            analysis = processor.analyze_character_consistency(dialogue)
            print(f"   一貫性スコア: {analysis['consistency_score']:.2f}")
            
            if analysis['issues']:
                print(f"   問題点: {', '.join(analysis['issues'])}")
            
            # 一貫性向上処理
            enhanced = processor.enhance_consistency(dialogue, f"シーン{i}")
            if enhanced != dialogue:
                print(f"   修正後: {enhanced}")
            else:
                print(f"   修正: なし")
        
        print("\n" + "="*50)

def test_emotional_flow():
    """感情推移テスト"""
    print("\n=== 感情推移テスト ===\n")
    
    config = load_test_config()
    processor = AdvancedConsistencyProcessor(config)
    
    # 感情推移テストケース
    emotional_sequence = [
        "静かな夜でした。月明かりが美しく照らしています。",
        "少し不安になってきました…",
        "急に恐怖を感じました。",
        "うわああああああああああああああ！！！！怖すぎます！！！",  # 急激な感情変化
        "でも、安心しました。",
        "ほっとして、微笑みました。"
    ]
    
    print("連続した感情推移の処理:")
    for i, text in enumerate(emotional_sequence, 1):
        print(f"\n{i}. 入力: {text}")
        
        # 感情推移分析
        emotion_analysis = processor.analyze_emotional_flow(text)
        print(f"   感情流れスコア: {emotion_analysis['flow_score']:.2f}")
        print(f"   検出感情: {emotion_analysis['emotions']}")
        
        if emotion_analysis['issues']:
            print(f"   問題: {', '.join(emotion_analysis['issues'])}")
        
        # 感情推移改善
        enhanced = processor.enhance_consistency(text, f"感情シーン{i}")
        if enhanced != text:
            print(f"   改善後: {enhanced}")
        else:
            print(f"   改善: なし")

def test_narrative_flow():
    """物語流れテスト"""
    print("\n=== 物語流れテスト ===\n")
    
    config = load_test_config()
    processor = AdvancedConsistencyProcessor(config)
    
    # 物語反復テストケース
    repetitive_narrative = [
        "そして彼女は部屋に入りました。",
        "そして彼女は窓を開けました。",
        "そして彼女は椅子に座りました。",
        "そして彼女は本を読み始めました。",  # "そして"の連続
        "そして彼女は眠りに落ちました。"
    ]
    
    print("反復的な物語展開の改善:")
    for i, text in enumerate(repetitive_narrative, 1):
        print(f"\n{i}. 入力: {text}")
        
        enhanced = processor.enhance_consistency(text, f"物語{i}")
        if enhanced != text:
            print(f"   改善後: {enhanced}")
        else:
            print(f"   改善: なし")

def test_integrated_consistency():
    """統合一貫性テスト（NKAT統合版）"""
    print("\n=== 統合一貫性テスト ===\n")
    
    config = load_test_config()
    nkat_processor = TextConsistencyProcessor(config)
    
    # 複合的な一貫性問題を含むテキスト
    complex_cases = [
        "樹里：ああ…オス様…気持ちいいです…",
        "樹里：うわああああああああああああああああああ！！！！！！激しすぎますぅっ！！！",
        "樹里：そして樹里は部屋を出ました。そして樹里は廊下を歩きました。",
        "樹里：静かになりました…ありがとうございます…"
    ]
    
    print("NKAT統合一貫性処理:")
    for i, text in enumerate(complex_cases, 1):
        print(f"\n{i}. 入力: {text}")
        
        enhanced = nkat_processor.maintain_consistency(text, f"統合テスト{i}")
        print(f"   処理後: {enhanced}")
        
        # 処理改善の確認
        if enhanced != text:
            print(f"   改善された: はい")
        else:
            print(f"   改善された: いいえ")

def test_performance_comparison():
    """パフォーマンス比較テスト"""
    print("\n=== パフォーマンス比較テスト ===\n")
    
    config = load_test_config()
    
    # 標準モード
    config_standard = config.copy()
    config_standard["nkat_advanced_mode"] = False
    processor_standard = TextConsistencyProcessor(config_standard)
    
    # 高度モード
    processor_advanced = TextConsistencyProcessor(config)
    
    test_text = "樹里：うわああああああああああああああああ！！！！激しすぎます！！！"
    
    # 標準モードテスト
    start_time = time.time()
    for i in range(10):
        result_standard = processor_standard.maintain_consistency(test_text, f"テスト{i}")
    standard_time = time.time() - start_time
    
    # 高度モードテスト
    start_time = time.time()
    for i in range(10):
        result_advanced = processor_advanced.maintain_consistency(test_text, f"テスト{i}")
    advanced_time = time.time() - start_time
    
    print(f"標準モード（10回処理）: {standard_time:.4f}秒")
    print(f"高度モード（10回処理）: {advanced_time:.4f}秒")
    print(f"結果比較:")
    print(f"  標準: {result_standard}")
    print(f"  高度: {result_advanced}")
    
    # 統計取得
    stats_standard = processor_standard.get_performance_stats()
    stats_advanced = processor_advanced.get_performance_stats()
    
    print(f"\n標準モード統計: {stats_standard}")
    print(f"高度モード統計: {stats_advanced}")

def main():
    """メイン関数"""
    try:
        print("高度一貫性機能包括テスト開始\n")
        
        # 各テストの実行
        test_character_consistency()
        test_emotional_flow()
        test_narrative_flow()
        test_integrated_consistency()
        test_performance_comparison()
        
        print("\n✅ 全テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 