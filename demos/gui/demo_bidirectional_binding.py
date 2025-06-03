# -*- coding: utf-8 -*-
"""
双方向バインディングシステム デモアプリケーション
GUI ↔ Core 双方向同期の実演

実行例:
python demo_bidirectional_binding.py
"""

import os
import sys
import time
import threading
from typing import Dict

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "..", "..", "src")
sys.path.insert(0, src_dir)

# GUI関連のインポート
try:
    import tkinter as tk
    import tkinter.ttk as ttk
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("❌ GUI関連モジュールが見つかりません。")

# 双方向バインディングシステムのインポート
try:
    from ui.bidirectional_binding import create_ena_bidirectional_system, ENASettingsModel, BidirectionalBinder
    BINDING_AVAILABLE = True
except ImportError:
    BINDING_AVAILABLE = False
    print("❌ 双方向バインディングシステムが見つかりません。")


class BidirectionalBindingDemo:
    """双方向バインディング デモアプリケーション"""
    
    def __init__(self):
        if not GUI_AVAILABLE:
            raise ImportError("GUI環境が利用できません")
        
        if not BINDING_AVAILABLE:
            raise ImportError("双方向バインディングシステムが利用できません")
        
        self.root = tk.Tk()
        self.root.title("🔄 双方向バインディング デモ - EasyNovelAssistant")
        self.root.geometry("900x700")
        
        # 双方向バインディングシステムの初期化
        self.model, self.binder = create_ena_bidirectional_system()
        
        # 変更履歴の記録
        self.change_history = []
        self.setup_change_monitoring()
        
        # GUI構築
        self.build_gui()
        
        # バインディング設定
        self.setup_bindings()
        
        print("🚀 双方向バインディング デモ起動完了！")
    
    def setup_change_monitoring(self):
        """変更監視の設定"""
        def on_change(property_name, value):
            timestamp = time.strftime("%H:%M:%S")
            self.change_history.append(f"[{timestamp}] {property_name} = {value}")
            
            # 履歴表示の更新
            if hasattr(self, 'history_text'):
                self.update_history_display()
        
        # 全プロパティの変更を監視
        for prop_name in self.model._properties:
            prop = self.model.get_property(prop_name)
            prop.subscribe(lambda val, name=prop_name: on_change(name, val))
    
    def build_gui(self):
        """GUI構築"""
        # メインフレーム
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # タイトル
        title_label = ttk.Label(
            main_frame, 
            text="🔄 双方向データバインディング デモ",
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 10))
        
        # 説明
        desc_label = ttk.Label(
            main_frame,
            text="GUI操作とコード操作が双方向で同期されることを確認できます",
            font=('Arial', 10)
        )
        desc_label.pack(pady=(0, 15))
        
        # 上部フレーム（GUI制御）
        self.build_gui_controls(main_frame)
        
        # 中部フレーム（コード制御）
        self.build_code_controls(main_frame)
        
        # 下部フレーム（変更履歴）
        self.build_history_display(main_frame)
    
    def build_gui_controls(self, parent):
        """GUI制御部分の構築"""
        gui_frame = ttk.LabelFrame(parent, text="🎛️ GUI制御（マウス操作）", padding="10")
        gui_frame.pack(fill=tk.X, pady=5)
        
        # 2列レイアウト
        left_frame = ttk.Frame(gui_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right_frame = ttk.Frame(gui_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # 左側：スライダー群
        ttk.Label(left_frame, text="類似度閾値:", font=('Arial', 10, 'bold')).pack(anchor='w')
        self.similarity_scale = ttk.Scale(left_frame, from_=0.1, to=0.8, orient=tk.HORIZONTAL)
        self.similarity_scale.pack(fill=tk.X, pady=2)
        self.similarity_label = ttk.Label(left_frame, text="0.35")
        self.similarity_label.pack(anchor='w')
        
        ttk.Label(left_frame, text="検出距離:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 0))
        self.distance_scale = ttk.Scale(left_frame, from_=10, to=100, orient=tk.HORIZONTAL)
        self.distance_scale.pack(fill=tk.X, pady=2)
        self.distance_label = ttk.Label(left_frame, text="50")
        self.distance_label.pack(anchor='w')
        
        ttk.Label(left_frame, text="圧縮率:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 0))
        self.compress_scale = ttk.Scale(left_frame, from_=0.01, to=0.10, orient=tk.HORIZONTAL)
        self.compress_scale.pack(fill=tk.X, pady=2)
        self.compress_label = ttk.Label(left_frame, text="0.03")
        self.compress_label.pack(anchor='w')
        
        # 右側：チェックボックス群
        ttk.Label(right_frame, text="機能切替:", font=('Arial', 10, 'bold')).pack(anchor='w')
        
        self.enable_4gram_var = tk.BooleanVar()
        self.enable_4gram_check = ttk.Checkbutton(
            right_frame, text="4-gramブロック", variable=self.enable_4gram_var
        )
        self.enable_4gram_check.pack(anchor='w', pady=2)
        
        self.enable_drp_var = tk.BooleanVar()
        self.enable_drp_check = ttk.Checkbutton(
            right_frame, text="DRP有効化", variable=self.enable_drp_var
        )
        self.enable_drp_check.pack(anchor='w', pady=2)
        
        self.enable_mecab_var = tk.BooleanVar()
        self.enable_mecab_check = ttk.Checkbutton(
            right_frame, text="MeCab正規化", variable=self.enable_mecab_var
        )
        self.enable_mecab_check.pack(anchor='w', pady=2)
        
        self.aggressive_mode_var = tk.BooleanVar()
        self.aggressive_mode_check = ttk.Checkbutton(
            right_frame, text="アグレッシブモード", variable=self.aggressive_mode_var
        )
        self.aggressive_mode_check.pack(anchor='w', pady=2)
    
    def build_code_controls(self, parent):
        """コード制御部分の構築"""
        code_frame = ttk.LabelFrame(parent, text="⚙️ コード制御（プログラム操作）", padding="10")
        code_frame.pack(fill=tk.X, pady=5)
        
        # ボタン群
        button_frame = ttk.Frame(code_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            button_frame, 
            text="デフォルト設定", 
            command=self.apply_default_settings
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame, 
            text="90%最適設定", 
            command=self.apply_optimal_settings
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame, 
            text="ランダム設定", 
            command=self.apply_random_settings
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame, 
            text="現在設定表示", 
            command=self.show_current_settings
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame, 
            text="連続変更テスト", 
            command=self.run_continuous_test
        ).pack(side=tk.LEFT, padx=2)
        
        # 現在値表示
        self.current_values_text = tk.Text(code_frame, height=6, width=80, bg="#f8f8f8")
        self.current_values_text.pack(fill=tk.X, pady=5)
        self.update_current_values_display()
    
    def build_history_display(self, parent):
        """変更履歴表示部分の構築"""
        history_frame = ttk.LabelFrame(parent, text="📝 変更履歴（リアルタイム監視）", padding="10")
        history_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # スクロール付きテキストエリア
        text_frame = ttk.Frame(history_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.history_text = tk.Text(text_frame, height=8, bg="#f0f0f0")
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.history_text.yview)
        self.history_text.configure(yscrollcommand=scrollbar.set)
        
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # クリアボタン
        ttk.Button(
            history_frame, 
            text="履歴クリア", 
            command=self.clear_history
        ).pack(pady=5)
    
    def setup_bindings(self):
        """双方向バインディングの設定"""
        try:
            # スライダーとバインド
            self.binder.bind_widget(self.similarity_scale, self.model, 'similarity_threshold')
            self.binder.bind_widget(self.distance_scale, self.model, 'max_distance')
            self.binder.bind_widget(self.compress_scale, self.model, 'min_compress_rate')
            
            # チェックボックスとバインド
            self.binder.bind_widget(self.enable_4gram_check, self.model, 'enable_4gram')
            self.binder.bind_widget(self.enable_drp_check, self.model, 'enable_drp')
            self.binder.bind_widget(self.enable_mecab_check, self.model, 'enable_mecab')
            self.binder.bind_widget(self.aggressive_mode_check, self.model, 'aggressive_mode')
            
            # ラベル更新の設定
            self.setup_label_updates()
            
            print("✅ 双方向バインディング設定完了")
        except Exception as e:
            print(f"❌ バインディング設定エラー: {e}")
    
    def setup_label_updates(self):
        """ラベル更新の設定"""
        def update_similarity_label(value):
            self.similarity_label.config(text=f"{value:.2f}")
        
        def update_distance_label(value):
            self.distance_label.config(text=f"{value}")
        
        def update_compress_label(value):
            self.compress_label.config(text=f"{value:.3f}")
        
        # プロパティ変更でラベル更新
        self.model.get_property('similarity_threshold').subscribe(update_similarity_label)
        self.model.get_property('max_distance').subscribe(update_distance_label)
        self.model.get_property('min_compress_rate').subscribe(update_compress_label)
        
        # 現在値表示の更新
        def update_current_display(value):
            self.update_current_values_display()
        
        for prop_name in self.model._properties:
            self.model.get_property(prop_name).subscribe(update_current_display)
    
    def apply_default_settings(self):
        """デフォルト設定を適用"""
        settings = {
            'similarity_threshold': 0.5,
            'max_distance': 30,
            'min_compress_rate': 0.05,
            'enable_4gram': False,
            'enable_drp': False,
            'enable_mecab': False,
            'aggressive_mode': False
        }
        self.model.load_from_dict(settings)
        print("🔧 デフォルト設定を適用しました")
    
    def apply_optimal_settings(self):
        """90%最適設定を適用"""
        settings = {
            'similarity_threshold': 0.35,
            'max_distance': 50,
            'min_compress_rate': 0.03,
            'enable_4gram': True,
            'enable_drp': True,
            'enable_mecab': False,
            'aggressive_mode': True
        }
        self.model.load_from_dict(settings)
        print("🎯 90%最適設定を適用しました")
    
    def apply_random_settings(self):
        """ランダム設定を適用"""
        import random
        
        settings = {
            'similarity_threshold': round(random.uniform(0.1, 0.8), 2),
            'max_distance': random.randint(10, 100),
            'min_compress_rate': round(random.uniform(0.01, 0.10), 3),
            'enable_4gram': random.choice([True, False]),
            'enable_drp': random.choice([True, False]),
            'enable_mecab': random.choice([True, False]),
            'aggressive_mode': random.choice([True, False])
        }
        self.model.load_from_dict(settings)
        print("🎲 ランダム設定を適用しました")
    
    def show_current_settings(self):
        """現在の設定を表示"""
        settings = self.model.to_dict()
        print("📊 現在の設定:")
        for key, value in settings.items():
            print(f"   {key}: {value}")
    
    def run_continuous_test(self):
        """連続変更テスト"""
        def test_worker():
            print("🔄 連続変更テスト開始...")
            for i in range(10):
                # 値を段階的に変更
                threshold = 0.1 + (i * 0.07)
                distance = 10 + (i * 9)
                
                self.model.set_value('similarity_threshold', threshold)
                time.sleep(0.5)
                self.model.set_value('max_distance', distance)
                time.sleep(0.5)
                
                # トグル切り替え
                if i % 3 == 0:
                    current = self.model.get_value('enable_4gram')
                    self.model.set_value('enable_4gram', not current)
            
            print("✅ 連続変更テスト完了")
        
        # 別スレッドで実行
        thread = threading.Thread(target=test_worker)
        thread.daemon = True
        thread.start()
    
    def update_current_values_display(self):
        """現在値表示の更新"""
        try:
            settings = self.model.to_dict()
            display_text = "📊 現在の設定値:\n"
            display_text += "=" * 50 + "\n"
            
            for key, value in settings.items():
                if isinstance(value, float):
                    display_text += f"{key:<25}: {value:.3f}\n"
                else:
                    display_text += f"{key:<25}: {value}\n"
            
            self.current_values_text.delete(1.0, tk.END)
            self.current_values_text.insert(1.0, display_text)
        except Exception as e:
            print(f"⚠️ 現在値表示更新エラー: {e}")
    
    def update_history_display(self):
        """履歴表示の更新"""
        try:
            # 最新の20件のみ表示
            recent_history = self.change_history[-20:]
            
            self.history_text.delete(1.0, tk.END)
            for entry in recent_history:
                self.history_text.insert(tk.END, entry + "\n")
            
            # 最下部にスクロール
            self.history_text.see(tk.END)
        except Exception as e:
            print(f"⚠️ 履歴表示更新エラー: {e}")
    
    def clear_history(self):
        """履歴クリア"""
        self.change_history.clear()
        self.history_text.delete(1.0, tk.END)
        print("🧹 変更履歴をクリアしました")
    
    def run(self):
        """アプリケーション実行"""
        try:
            print("🎬 双方向バインディング デモ開始！")
            print("   1. スライダーやチェックボックスを操作してください")
            print("   2. ボタンでコード側からも設定を変更できます")
            print("   3. 双方向同期の動作を確認してください")
            
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n👋 デモ終了")
        finally:
            # クリーンアップ
            if self.binder:
                self.binder.destroy_all()
            print("🏁 双方向バインディング デモ終了")


def main():
    """メイン実行関数"""
    print("🔄 双方向バインディングシステム デモ")
    print("=" * 50)
    
    if not GUI_AVAILABLE:
        print("❌ GUI環境が利用できません。tkinterをインストールしてください。")
        return 1
    
    if not BINDING_AVAILABLE:
        print("❌ 双方向バインディングシステムが見つかりません。")
        return 1
    
    # デモ実行
    try:
        demo = BidirectionalBindingDemo()
        demo.run()
        return 0
    except Exception as e:
        print(f"❌ デモ実行エラー: {e}")
        return 1


if __name__ == '__main__':
    exit(main()) 