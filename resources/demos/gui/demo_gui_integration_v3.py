# -*- coding: utf-8 -*-
"""
反復抑制システムv3 GUI統合デモ
リアルタイム制御パネルの動作確認

実行例:
python demo_gui_integration_v3.py
"""

import os
import sys
import time
import threading
from typing import Dict

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.insert(0, src_dir)

# GUI関連のインポート
try:
    import tkinter as tk
    import tkinter.ttk as ttk
    from tkinterdnd2 import TkinterDnD
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("❌ GUI関連モジュールが見つかりません。")

# v3システムのインポート
try:
    from utils.repetition_suppressor_v3 import AdvancedRepetitionSuppressorV3
    V3_AVAILABLE = True
except ImportError:
    V3_AVAILABLE = False
    print("❌ v3システムが見つかりません。")

# GUI制御パネルのインポート
try:
    from ui.repetition_control_panel import RepetitionControlPanel
    PANEL_AVAILABLE = True
except ImportError:
    PANEL_AVAILABLE = False
    print("❌ 制御パネルが見つかりません。")


class MockContext:
    """モックコンテキスト（デモ用）"""
    def __init__(self):
        self.data = {}
        self.repetition_suppressor = None
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def __setitem__(self, key, value):
        self.data[key] = value
    
    def __getitem__(self, key):
        return self.data[key]


class RepetitionDemoWindow:
    """反復抑制システムGUIデモウィンドウ"""
    
    def __init__(self):
        if not GUI_AVAILABLE or not V3_AVAILABLE or not PANEL_AVAILABLE:
            print("❌ 必要なモジュールが不足しています。")
            return
        
        # ウィンドウ設定
        self.root = TkinterDnD.Tk()
        self.root.title("反復抑制システム v3 - リアルタイム制御デモ")
        self.root.geometry("1200x800")
        
        # モックコンテキスト
        self.ctx = MockContext()
        
        # テストデータ
        self.test_texts = [
            "お兄ちゃんお兄ちゃん、どこに行くのですかお兄ちゃん？",
            "そやそやそや、あかんあかんあかん、やなやなそれは。",
            "嬉しい嬉しい、楽しい楽しい、幸せ幸せという感じですです。",
            "今日は良い天気ですね。今日は良い天気だから散歩しましょう。",
            "wwwwww、そうですね。777777って数字ですか？",
            "ねえ、ねえ、ねえ！聞いてよ。",
            "ドキドキしちゃう。ワクワクするね！",
            "あああああああ！うわああああああ！きゃああああああ！",
            "はい、はい、はい。"
        ]
        self.current_test_index = 0
        
        # v3システム初期化
        self.init_suppressor()
        
        # GUI構築
        self.build_gui()
        
        print("🚀 反復抑制GUI統合デモ起動完了")
    
    def init_suppressor(self):
        """v3反復抑制システムの初期化"""
        config = {
            'similarity_threshold': 0.35,
            'max_distance': 50,
            'min_compress_rate': 0.03,
            'ngram_block_size': 3,
            'enable_4gram_blocking': True,
            'drp_base': 1.10,
            'drp_alpha': 0.5,
            'enable_drp': True,
            'enable_mecab_normalization': False,
            'enable_rhetorical_protection': False,
            'enable_latin_number_detection': True,
            'enable_aggressive_mode': True,
            'debug_mode': True
        }
        
        self.ctx.repetition_suppressor = AdvancedRepetitionSuppressorV3(config)
        print("✅ v3システム初期化完了")
    
    def build_gui(self):
        """GUI構築"""
        # メインフレーム
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左側パネル（制御）
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 反復制御パネル
        self.control_panel = RepetitionControlPanel(
            left_frame,
            self.ctx,
            on_settings_changed=self.on_settings_changed
        )
        self.control_panel.pack(fill=tk.BOTH, expand=True)
        
        # 右側パネル（テスト実行）
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # テスト実行エリア
        test_frame = ttk.LabelFrame(right_frame, text="テスト実行", padding="5")
        test_frame.pack(fill=tk.BOTH, expand=True)
        
        # 入力テキストエリア
        input_frame = ttk.Frame(test_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="入力テキスト:").pack(anchor=tk.W)
        self.input_text = tk.Text(input_frame, height=4, wrap=tk.WORD)
        self.input_text.pack(fill=tk.X, pady=2)
        
        # コントロールボタン
        button_frame = ttk.Frame(test_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="次のテストケース", command=self.load_next_test).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="反復抑制実行", command=self.run_suppression).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="クリア", command=self.clear_results).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="連続テスト", command=self.run_batch_test).pack(side=tk.LEFT, padx=2)
        
        # 結果表示エリア
        result_frame = ttk.Frame(test_frame)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        ttk.Label(result_frame, text="出力結果:").pack(anchor=tk.W)
        self.output_text = tk.Text(result_frame, height=6, wrap=tk.WORD, bg="#f0f0f0")
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=2)
        
        # ログ表示エリア
        log_frame = ttk.LabelFrame(right_frame, text="実行ログ", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD, bg="#f8f8f8")
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 初期テストケース読み込み
        self.load_next_test()
    
    def on_settings_changed(self, settings: Dict):
        """制御パネルからの設定変更"""
        try:
            # 反復抑制システムの設定更新
            self.ctx.repetition_suppressor.update_config(settings)
            
            # ログ出力
            self.log(f"🔄 設定更新: 類似度={settings.get('similarity_threshold', '?'):.2f}, DRP={settings.get('enable_drp', '?')}")
            
        except Exception as e:
            self.log(f"❌ 設定更新エラー: {e}")
    
    def load_next_test(self):
        """次のテストケースを読み込み"""
        if self.test_texts:
            test_text = self.test_texts[self.current_test_index]
            self.input_text.delete(1.0, tk.END)
            self.input_text.insert(1.0, test_text)
            
            self.current_test_index = (self.current_test_index + 1) % len(self.test_texts)
            self.log(f"📝 テストケース{self.current_test_index} 読み込み")
    
    def run_suppression(self):
        """反復抑制実行"""
        try:
            input_text = self.input_text.get(1.0, tk.END).strip()
            if not input_text:
                self.log("⚠️ 入力テキストが空です")
                return
            
            self.log(f"🚀 反復抑制開始: {len(input_text)}文字")
            
            # 処理実行（v3版）
            start_time = time.time()
            result_text, metrics = self.ctx.repetition_suppressor.suppress_repetitions_with_debug_v3(
                input_text, "テストキャラ"
            )
            processing_time = (time.time() - start_time) * 1000
            
            # 結果表示
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(1.0, result_text)
            
            # 統計更新
            compression_rate = (len(input_text) - len(result_text)) / len(input_text)
            attempts = getattr(self.ctx.repetition_suppressor, 'total_attempts', 1)
            success_count = getattr(self.ctx.repetition_suppressor, 'total_success_count', 1)
            session_success_rate = success_count / max(1, attempts)
            
            # 制御パネルの統計更新
            self.control_panel.update_statistics(
                success_rate=session_success_rate,
                attempts=attempts,
                compression_rate=compression_rate
            )
            
            # ログ出力
            self.log(f"✅ 処理完了: 成功率={metrics.success_rate:.1%}, 圧縮率={compression_rate:.1%}, 処理時間={processing_time:.1f}ms")
            self.log(f"   検出={metrics.patterns_detected}, 抑制={metrics.patterns_suppressed}, 出力長={len(result_text)}")
            
            # v3機能の使用状況
            if hasattr(metrics, 'ngram_blocks_applied'):
                self.log(f"   v3機能: 4-gram={metrics.ngram_blocks_applied}, 連番={getattr(metrics, 'latin_number_blocks', 0)}")
            
        except Exception as e:
            self.log(f"❌ 処理エラー: {e}")
    
    def run_batch_test(self):
        """連続テスト実行"""
        self.log("🔥 連続テスト開始...")
        
        def batch_runner():
            results = []
            for i, test_text in enumerate(self.test_texts):
                try:
                    # GUI更新
                    self.root.after(0, lambda t=test_text: self.update_input_text(t))
                    
                    # 処理実行
                    result_text, metrics = self.ctx.repetition_suppressor.suppress_repetitions_with_debug_v3(
                        test_text, f"テストキャラ{i+1}"
                    )
                    
                    compression_rate = (len(test_text) - len(result_text)) / len(test_text)
                    results.append({
                        'success_rate': metrics.success_rate,
                        'compression_rate': compression_rate,
                        'patterns_detected': metrics.patterns_detected,
                        'patterns_suppressed': metrics.patterns_suppressed
                    })
                    
                    # ログ更新
                    self.root.after(0, lambda i=i, sr=metrics.success_rate, cr=compression_rate: 
                                   self.log(f"   テスト{i+1}: 成功率={sr:.1%}, 圧縮率={cr:.1%}"))
                    
                    time.sleep(0.5)  # 視覚的な遅延
                    
                except Exception as e:
                    self.root.after(0, lambda i=i, e=e: self.log(f"   テスト{i+1}: エラー - {e}"))
            
            # 総合結果
            if results:
                avg_success = sum(r['success_rate'] for r in results) / len(results)
                avg_compression = sum(r['compression_rate'] for r in results) / len(results)
                total_detected = sum(r['patterns_detected'] for r in results)
                total_suppressed = sum(r['patterns_suppressed'] for r in results)
                
                self.root.after(0, lambda: self.log(f"🎯 連続テスト完了: 平均成功率={avg_success:.1%}, 平均圧縮率={avg_compression:.1%}"))
                self.root.after(0, lambda: self.log(f"   総検出={total_detected}, 総抑制={total_suppressed}"))
                
                # 統計パネル更新
                attempts = getattr(self.ctx.repetition_suppressor, 'total_attempts', len(results))
                self.root.after(0, lambda: self.control_panel.update_statistics(
                    success_rate=avg_success,
                    attempts=attempts,
                    compression_rate=avg_compression
                ))
        
        # バックグラウンドで実行
        thread = threading.Thread(target=batch_runner)
        thread.daemon = True
        thread.start()
    
    def update_input_text(self, text):
        """入力テキストの更新（スレッドセーフ）"""
        self.input_text.delete(1.0, tk.END)
        self.input_text.insert(1.0, text)
    
    def clear_results(self):
        """結果クリア"""
        self.output_text.delete(1.0, tk.END)
        self.log("🧹 結果をクリアしました")
    
    def log(self, message: str):
        """ログ出力"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # コンソールにも出力
        print(log_entry.strip())
    
    def run(self):
        """デモ実行"""
        if not GUI_AVAILABLE or not V3_AVAILABLE or not PANEL_AVAILABLE:
            return
        
        self.log("🎮 反復抑制システムv3 GUI統合デモ開始")
        self.log("   左パネルで設定を調整し、右側でテストを実行してください")
        
        self.root.mainloop()


def main():
    """メイン実行関数"""
    print("🎯 反復抑制システム v3 GUI統合デモ")
    print("=" * 50)
    
    if not GUI_AVAILABLE:
        print("❌ GUI環境が利用できません。tkinter, tkinterdnd2をインストールしてください。")
        return 1
    
    if not V3_AVAILABLE:
        print("❌ v3システムが見つかりません。src/utils/repetition_suppressor_v3.pyを確認してください。")
        return 1
    
    if not PANEL_AVAILABLE:
        print("❌ 制御パネルが見つかりません。src/ui/repetition_control_panel.pyを確認してください。")
        return 1
    
    # デモ実行
    demo = RepetitionDemoWindow()
    demo.run()
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 