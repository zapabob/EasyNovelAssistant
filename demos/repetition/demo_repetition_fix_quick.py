# -*- coding: utf-8 -*-
"""
同語反復修正クイックデモ
ユーザーが簡単に同語反復問題を修正できるインタラクティブツール
"""

import sys
import os

# パス設定
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from utils.repetition_suppressor import AdvancedRepetitionSuppressor


def main():
    print("🔧 同語反復修正ツール")
    print("=" * 50)
    print("同語反復が多い文章を自然な文章に修正します。")
    print("'quit' または 'exit' で終了")
    print()
    
    # アグレッシブモード設定
    config = {
        'min_repeat_threshold': 1,
        'max_distance': 30,
        'similarity_threshold': 0.7,
        'phonetic_threshold': 0.8,
        'enable_aggressive_mode': True,
        'interjection_sensitivity': 0.5,
        'exact_match_priority': True,
        'character_repetition_limit': 3
    }
    
    suppressor = AdvancedRepetitionSuppressor(config)
    
    print("設定:")
    print(f"  ├─ アグレッシブモード: 有効")
    print(f"  ├─ 反復検出閾値: {config['min_repeat_threshold']}")
    print(f"  ├─ 検出距離: {config['max_distance']}文字")
    print(f"  └─ 完全一致優先: 有効")
    print()
    
    while True:
        try:
            # ユーザー入力
            print("修正したい文章を入力してください:")
            user_input = input("> ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("終了します。")
                break
            
            print(f"\n📝 元の文章: {user_input}")
            print(f"文字数: {len(user_input)}")
            
            # 反復抑制処理
            try:
                result = suppressor.suppress_repetitions(user_input)
                
                reduction = len(user_input) - len(result)
                reduction_rate = (reduction / len(user_input)) * 100 if len(user_input) > 0 else 0
                
                print(f"\n✨ 修正後: {result}")
                print(f"文字数: {len(result)} (削減: {reduction}文字, {reduction_rate:.1f}%)")
                
                if result != user_input:
                    print("✅ 同語反復が改善されました")
                else:
                    print("ℹ️ 反復問題は検出されませんでした")
                
            except Exception as e:
                print(f"❌ 処理エラー: {e}")
            
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n\n終了します。")
            break
        except Exception as e:
            print(f"❌ エラー: {e}")


if __name__ == "__main__":
    main() 