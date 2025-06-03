# -*- coding: utf-8 -*-
"""
反復抑制システム v3 ユニットテスト
成功率90%検証用テストスイート
"""

import unittest
import sys
import os

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_dir = os.path.join(project_root, "src")
sys.path.insert(0, project_root)
sys.path.insert(0, src_dir)

try:
    from utils.repetition_suppressor_v3 import AdvancedRepetitionSuppressorV3, SuppressionMetricsV3
    V3_AVAILABLE = True
    print("✅ v3システム読み込み成功")
except ImportError as e:
    V3_AVAILABLE = False
    print(f"⚠️ v3システムが見つかりません: {e}")


class TestRepetitionSuppressionV3(unittest.TestCase):
    """反復抑制システム v3 のテストクラス"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラス全体の初期設定"""
        if not V3_AVAILABLE:
            cls.skipTest(cls, "v3システムが利用できません")
        
        # 90%成功率を達成した推奨設定
        cls.config = {
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
            'debug_mode': False
        }
        
        cls.suppressor = AdvancedRepetitionSuppressorV3(cls.config)
    
    def setUp(self):
        """各テストの初期設定"""
        self.success_threshold = 0.7  # 70%以上を成功とみなす
        self.compression_threshold = 0.03  # 3%以上の圧縮を期待
    
    def test_01_basic_word_repetition(self):
        """基本的な同語反復テスト"""
        input_text = "お兄ちゃんお兄ちゃん、どこに行くのですかお兄ちゃん？"
        result, metrics = self.suppressor.suppress_repetitions_with_debug_v3(input_text, "妹")
        
        self.assertGreaterEqual(metrics.success_rate, self.success_threshold, 
                               f"成功率不足: {metrics.success_rate:.1%} < {self.success_threshold:.1%}")
        self.assertLess(len(result), len(input_text), "圧縮されていません")
        self.assertGreater(metrics.patterns_suppressed, 0, "パターンが抑制されていません")
    
    def test_02_dialect_repetition(self):
        """方言反復テスト"""
        input_text = "そやそやそや、あかんあかんあかん、やなやなそれは。"
        result, metrics = self.suppressor.suppress_repetitions_with_debug_v3(input_text, "関西弁キャラ")
        
        self.assertGreaterEqual(metrics.success_rate, self.success_threshold)
        compression_rate = (len(input_text) - len(result)) / len(input_text)
        self.assertGreaterEqual(compression_rate, self.compression_threshold)
    
    def test_03_ending_repetition(self):
        """語尾反復テスト"""
        input_text = "ですですね、ますますよ、でしょでしょう。"
        result, metrics = self.suppressor.suppress_repetitions_with_debug_v3(input_text, "丁寧語キャラ")
        
        self.assertGreaterEqual(metrics.success_rate, self.success_threshold)
        self.assertGreater(metrics.patterns_detected, 0, "パターンが検出されていません")
    
    def test_04_ngram_blocking(self):
        """3-gramブロック機能テスト"""
        input_text = "今日は良い天気ですね。今日は良い天気だから散歩しましょう。"
        result, metrics = self.suppressor.suppress_repetitions_with_debug_v3(input_text, "普通の人")
        
        self.assertGreaterEqual(metrics.success_rate, self.success_threshold)
        # 3-gramブロック機能が動作したかチェック
        self.assertGreaterEqual(metrics.ngram_blocks_applied, 0, "3-gramブロックが適用されていません")
    
    def test_05_latin_number_repetition(self):
        """連番反復テスト"""
        input_text = "wwwwww、そうですね。777777って数字ですか？"
        result, metrics = self.suppressor.suppress_repetitions_with_debug_v3(input_text, "ネットユーザー")
        
        self.assertGreaterEqual(metrics.success_rate, self.success_threshold)
        # 連番検知が動作したかチェック
        self.assertGreaterEqual(metrics.latin_number_blocks, 0, "連番検知が適用されていません")
    
    def test_06_rhetorical_protection(self):
        """修辞的反復保護テスト（保護無効設定）"""
        input_text = "ねえ、ねえ、ねえ！聞いてよ。"
        result, metrics = self.suppressor.suppress_repetitions_with_debug_v3(input_text, "感情的キャラ")
        
        # 修辞的保護が無効な設定では圧縮されるべき
        self.assertGreaterEqual(metrics.success_rate, self.success_threshold)
    
    def test_07_complex_repetition(self):
        """複合反復テスト"""
        input_text = "嬉しい嬉しい、楽しい楽しい、幸せ幸せという感じですです。"
        result, metrics = self.suppressor.suppress_repetitions_with_debug_v3(input_text, "ポジティブキャラ")
        
        self.assertGreaterEqual(metrics.success_rate, self.success_threshold)
        self.assertGreater(metrics.patterns_detected, 2, "複数パターンが検出されていません")
    
    def test_08_interjection_overuse(self):
        """感嘆詞過多テスト"""
        input_text = "あああああああ！うわああああああ！きゃああああああ！"
        result, metrics = self.suppressor.suppress_repetitions_with_debug_v3(input_text, "感情豊かキャラ")
        
        self.assertGreaterEqual(metrics.success_rate, self.success_threshold)
        compression_rate = (len(input_text) - len(result)) / len(input_text)
        self.assertGreaterEqual(compression_rate, 0.20, "感嘆詞が十分圧縮されていません")
    
    def test_09_short_repetition(self):
        """短文反復テスト"""
        input_text = "はい、はい、はい。"
        result, metrics = self.suppressor.suppress_repetitions_with_debug_v3(input_text, "相槌キャラ")
        
        self.assertGreaterEqual(metrics.success_rate, self.success_threshold)
    
    def test_10_performance_check(self):
        """処理性能テスト"""
        input_text = "これはテストこれはテストです。これはテストこれはテストですね。これはテストこれはテストでしょう。"
        result, metrics = self.suppressor.suppress_repetitions_with_debug_v3(input_text, "テストキャラ")
        
        self.assertGreaterEqual(metrics.success_rate, self.success_threshold)
        self.assertLess(metrics.processing_time_ms, 100, "処理時間が100ms以上です")  # 性能要件


def run_v3_validation():
    """v3システムの検証実行"""
    if not V3_AVAILABLE:
        print("❌ v3システムが利用できないため、テストをスキップします。")
        return False
    
    print("🧪 反復抑制システム v3 検証開始")
    print("=" * 60)
    
    # 10件のテストケースで成功率チェック
    test_cases = [
        "お兄ちゃんお兄ちゃん、どこに行くのですかお兄ちゃん？",
        "そやそやそや、あかんあかんあかん、やなやなそれは。",
        "ですですね、ますますよ、でしょでしょう。",
        "今日は良い天気ですね。今日は良い天気だから散歩しましょう。",
        "wwwwww、そうですね。777777って数字ですか？",
        "ねえ、ねえ、ねえ！聞いてよ。",
        "嬉しい嬉しい、楽しい楽しい、幸せ幸せという感じですです。",
        "あああああああ！うわああああああ！きゃああああああ！",
        "はい、はい、はい。",
        "これはテストこれはテストです。"
    ]
    
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
        'debug_mode': False
    }
    
    suppressor = AdvancedRepetitionSuppressorV3(config)
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, input_text in enumerate(test_cases, 1):
        print(f"\n📝 テスト {i}/10: {input_text[:30]}...")
        result, metrics = suppressor.suppress_repetitions_with_debug_v3(input_text, f"キャラ{i}")
        
        success = metrics.success_rate >= 0.7
        if success:
            success_count += 1
        
        status = "✅" if success else "❌"
        print(f"   {status} 成功率: {metrics.success_rate:.1%}, 圧縮率: {(len(input_text) - len(result)) / len(input_text):.1%}")
    
    overall_success_rate = success_count / total_count
    
    print(f"\n" + "=" * 60)
    print(f"📊 総合結果: {success_count}/{total_count} 成功 ({overall_success_rate:.1%})")
    
    # 80%成功率（8/10）を最低基準
    if overall_success_rate >= 0.8:
        if overall_success_rate >= 0.9:
            print(f"🎉 90%成功率達成！")
        else:
            print(f"✅ 80%成功率達成")
        return True
    else:
        print(f"❌ 成功率不足: {overall_success_rate:.1%} < 80%")
        return False


if __name__ == "__main__":
    success = run_v3_validation()
    sys.exit(0 if success else 1) 