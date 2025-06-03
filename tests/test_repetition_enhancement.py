# -*- coding: utf-8 -*-
"""
同語反復改善テスト
強化された反復抑制システムのテスト
"""

import sys
import os

# パス設定
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from utils.repetition_suppressor import AdvancedRepetitionSuppressor
import time


def test_same_word_repetition():
    """同語反復のテスト"""
    print("🧪 同語反復改善テスト開始")
    print("=" * 60)
    
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
    
    # テストケース
    test_cases = [
        # 同一語句の連続反復
        {
            "name": "同一語句連続反復",
            "input": "今日は今日は今日は良い天気ですね。",
            "expected_improvement": "語句反復の削減"
        },
        # 感嘆詞の過度な反復
        {
            "name": "感嘆詞反復",
            "input": "あああああ！うわああああ！きゃああああ！",
            "expected_improvement": "感嘆詞の簡略化"
        },
        # 語尾の反復
        {
            "name": "語尾反復",
            "input": "そうですそうですそうです。ですからですからですから。",
            "expected_improvement": "語尾反復の修正"
        },
        # 接続詞の反復
        {
            "name": "接続詞反復", 
            "input": "そしてそしてそして、でもでもでも、だからだからだから。",
            "expected_improvement": "接続詞の多様化"
        },
        # 文字レベルの過度な反復
        {
            "name": "文字レベル反復",
            "input": "うううううう〜〜〜〜〜〜っっっっっっ！！！！！！",
            "expected_improvement": "文字反復の短縮"
        },
        # 複合的な反復
        {
            "name": "複合反復",
            "input": "美咲：あああああ！そうですそうですそうです！でもでもでも〜〜〜〜！",
            "expected_improvement": "複数種類の反復改善"
        },
        # 実際の小説風サンプル
        {
            "name": "小説風文章",
            "input": "美咲：ああああ、本当に本当に本当に嬉しいです！そうですそうですそうです！ありがとうございますありがとうございます！うううう〜〜〜！",
            "expected_improvement": "自然な文章への修正"
        }
    ]
    
    print(f"設定:")
    print(f"  ├─ 反復検出閾値: {config['min_repeat_threshold']}")
    print(f"  ├─ 検出距離: {config['max_distance']}文字")
    print(f"  ├─ 類似度閾値: {config['similarity_threshold']}")
    print(f"  ├─ アグレッシブモード: {config['enable_aggressive_mode']}")
    print(f"  └─ 完全一致優先: {config['exact_match_priority']}")
    print()
    
    total_tests = len(test_cases)
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"テスト {i}/{total_tests}: {test_case['name']}")
        print(f"入力: {test_case['input']}")
        
        try:
            # 反復抑制処理実行
            start_time = time.time()
            result = suppressor.suppress_repetitions(test_case['input'], character_name="美咲")
            processing_time = time.time() - start_time
            
            # 改善度の評価
            original_length = len(test_case['input'])
            result_length = len(result)
            reduction_ratio = (original_length - result_length) / original_length * 100
            
            print(f"出力: {result}")
            print(f"期待: {test_case['expected_improvement']}")
            print(f"処理時間: {processing_time:.3f}秒")
            print(f"圧縮率: {reduction_ratio:.1f}% ({original_length} → {result_length}文字)")
            
            # 改善判定
            improved = len(result) <= len(test_case['input']) and result != test_case['input']
            if improved:
                print("✅ 改善: 反復が適切に抑制されました")
                success_count += 1
            else:
                print("❌ 未改善: 変化なしまたは悪化")
            
        except Exception as e:
            print(f"❌ エラー: {e}")
        
        print("-" * 50)
    
    # 統計情報
    stats = suppressor.get_statistics()
    print("\n📊 処理統計:")
    print(f"  ├─ 成功率: {success_count}/{total_tests} ({success_count/total_tests*100:.1f}%)")
    print(f"  ├─ 総分析回数: {stats.get('total_analyses', 0)}")
    print(f"  ├─ 平均重要度: {stats.get('average_severity', 0):.3f}")
    print(f"  └─ キャッシュサイズ: {stats.get('replacement_cache_size', 0)}")
    
    return success_count / total_tests


def test_real_world_samples():
    """実際の使用例をシミュレート"""
    print("\n🌍 実際の使用例テスト")
    print("=" * 60)
    
    # より厳しい設定
    config = {
        'min_repeat_threshold': 1,
        'max_distance': 25, 
        'similarity_threshold': 0.6,
        'phonetic_threshold': 0.7,
        'enable_aggressive_mode': True,
        'interjection_sensitivity': 0.4,
        'exact_match_priority': True,
        'character_repetition_limit': 2
    }
    
    suppressor = AdvancedRepetitionSuppressor(config)
    
    # 実際の問題文例
    problematic_texts = [
        "美咲：はいはいはい！分かりました分かりました！でもでも〜、そうですねそうですね〜。",
        "太郎：そうですかそうですか。なるほどなるほど。ううううう〜〜〜。",
        "花子：ああああ！本当ですか本当ですか！嬉しいです嬉しいです！！！！",
        "先生：そのとおりですそのとおりです。さあさあ、始めましょう始めましょう。"
    ]
    
    print("超厳格モード設定:")
    print(f"  ├─ 反復検出閾値: {config['min_repeat_threshold']}")
    print(f"  ├─ 検出距離: {config['max_distance']}文字")
    print(f"  ├─ 類似度閾値: {config['similarity_threshold']}")
    print(f"  └─ 感嘆詞感度: {config['interjection_sensitivity']}")
    print()
    
    improvement_count = 0
    
    for i, text in enumerate(problematic_texts, 1):
        print(f"例 {i}: {text}")
        
        try:
            result = suppressor.suppress_repetitions(text)
            
            if result != text:
                improvement_count += 1
                compression = (len(text) - len(result)) / len(text) * 100
                print(f"改善: {result}")
                print(f"圧縮: {compression:.1f}%")
                print("✅ 同語反復が改善されました")
            else:
                print("変更なし")
                print("⚠️ 改善の余地あり")
        except Exception as e:
            print(f"❌ 処理エラー: {e}")
        
        print()
    
    print(f"📈 実例改善率: {improvement_count}/{len(problematic_texts)} ({improvement_count/len(problematic_texts)*100:.1f}%)")
    
    return improvement_count / len(problematic_texts)


if __name__ == "__main__":
    print("🚀 同語反復改善システム 総合テスト")
    print(f"開始時刻: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    try:
        # 基本テスト
        basic_success_rate = test_same_word_repetition()
        
        # 実例テスト
        real_world_success_rate = test_real_world_samples()
        
        # 総合評価
        overall_rate = (basic_success_rate + real_world_success_rate) / 2
        
        print("\n" + "=" * 70)
        print("📋 総合結果")
        print(f"  ├─ 基本テスト成功率: {basic_success_rate*100:.1f}%")
        print(f"  ├─ 実例テスト成功率: {real_world_success_rate*100:.1f}%")
        print(f"  └─ 総合成功率: {overall_rate*100:.1f}%")
        
        if overall_rate >= 0.8:
            print("🎉 素晴らしい！同語反復問題は大幅に改善されました")
        elif overall_rate >= 0.6:
            print("👍 良好！同語反復問題は改善されています") 
        else:
            print("⚠️ 追加調整が必要です")
            
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc() 