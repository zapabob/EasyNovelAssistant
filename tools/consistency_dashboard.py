# -*- coding: utf-8 -*-
"""
EasyNovelAssistant 一貫性監視ダッシュボード
NKAT文章一貫性処理の統計情報をリアルタイムで表示
"""

import json
import os
import sys
import time
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
import tkinter as tk
from tkinter import ttk, scrolledtext
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from collections import deque

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


class ConsistencyDashboard:
    """
    一貫性監視ダッシュボード
    NKAT処理の統計情報をリアルタイムで表示
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("EasyNovelAssistant - 一貫性監視ダッシュボード")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2b2b2b')
        
        # データ保持
        self.consistency_data = deque(maxlen=100)
        self.character_stats = {}
        self.processing_stats = {}
        self.nkat_enabled = False
        
        # 更新制御
        self.update_interval = 2000  # 2秒間隔
        self.is_running = True
        
        # 日本語フォント設定
        self.setup_japanese_font()
        
        # GUI初期化
        self.setup_gui()
        
        # 統計データ読み込み
        self.load_initial_data()
        
        # 定期更新開始
        self.start_update_loop()
        
        print("一貫性監視ダッシュボードを起動しました")
    
    def setup_japanese_font(self):
        """日本語フォント設定"""
        try:
            # システムの日本語フォントを検索
            available_fonts = fm.findSystemFonts()
            japanese_fonts = ['NotoSansCJK-Regular', 'MSGothic', 'MS Gothic', 'YuGothic', 'Meiryo']
            
            self.japanese_font = None
            for font_name in japanese_fonts:
                if any(font_name in font_path for font_path in available_fonts):
                    self.japanese_font = font_name
                    break
            
            if not self.japanese_font:
                self.japanese_font = 'DejaVu Sans'  # フォールバック
            
            # matplotlibの日本語フォント設定
            plt.rcParams['font.family'] = self.japanese_font
            plt.rcParams['font.size'] = 10
            
        except Exception as e:
            print(f"フォント設定警告: {e}")
            self.japanese_font = 'DejaVu Sans'
    
    def setup_gui(self):
        """GUI構築"""
        # メインフレーム
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # タイトル
        title_label = ttk.Label(
            main_frame, 
            text="NKAT文章一貫性監視ダッシュボード",
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 10))
        
        # 上部フレーム（統計サマリー）
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.create_summary_panel(top_frame)
        
        # 中央フレーム（グラフとキャラクター情報）
        center_frame = ttk.Frame(main_frame)
        center_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左側（グラフエリア）
        left_frame = ttk.Frame(center_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.create_chart_panel(left_frame)
        
        # 右側（詳細情報）
        right_frame = ttk.Frame(center_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        self.create_details_panel(right_frame)
        
        # 下部フレーム（ログ表示）
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.create_log_panel(bottom_frame)
    
    def create_summary_panel(self, parent):
        """統計サマリーパネル作成"""
        summary_frame = ttk.LabelFrame(parent, text="処理統計サマリー", padding=10)
        summary_frame.pack(fill=tk.X)
        
        # サマリー項目
        summary_grid = ttk.Frame(summary_frame)
        summary_grid.pack(fill=tk.X)
        
        # NKAT状態
        ttk.Label(summary_grid, text="NKAT状態:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.nkat_status_label = ttk.Label(summary_grid, text="確認中...", foreground="orange")
        self.nkat_status_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # 処理済みテキスト数
        ttk.Label(summary_grid, text="処理済みテキスト:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.processed_count_label = ttk.Label(summary_grid, text="0")
        self.processed_count_label.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))
        
        # 一貫性改善率
        ttk.Label(summary_grid, text="一貫性改善率:").grid(row=0, column=4, sticky=tk.W, padx=(0, 10))
        self.improvement_rate_label = ttk.Label(summary_grid, text="0.0%")
        self.improvement_rate_label.grid(row=0, column=5, sticky=tk.W, padx=(0, 20))
        
        # 平均処理時間
        ttk.Label(summary_grid, text="平均処理時間:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.avg_time_label = ttk.Label(summary_grid, text="0.000s")
        self.avg_time_label.grid(row=1, column=1, sticky=tk.W, padx=(0, 20))
        
        # アクティブキャラクター
        ttk.Label(summary_grid, text="アクティブキャラクター:").grid(row=1, column=2, sticky=tk.W, padx=(0, 10))
        self.active_char_label = ttk.Label(summary_grid, text="なし")
        self.active_char_label.grid(row=1, column=3, sticky=tk.W, padx=(0, 20))
        
        # キャラクター総数
        ttk.Label(summary_grid, text="登録キャラクター数:").grid(row=1, column=4, sticky=tk.W, padx=(0, 10))
        self.char_count_label = ttk.Label(summary_grid, text="0")
        self.char_count_label.grid(row=1, column=5, sticky=tk.W)
    
    def create_chart_panel(self, parent):
        """グラフパネル作成"""
        chart_frame = ttk.LabelFrame(parent, text="一貫性トレンド", padding=10)
        chart_frame.pack(fill=tk.BOTH, expand=True)
        
        # matplotlib図表
        self.fig = Figure(figsize=(12, 6), dpi=100)
        self.fig.patch.set_facecolor('#f0f0f0')
        
        # サブプロット作成
        self.ax1 = self.fig.add_subplot(221)  # 一貫性スコア
        self.ax2 = self.fig.add_subplot(222)  # 処理時間
        self.ax3 = self.fig.add_subplot(223)  # 感情強度
        self.ax4 = self.fig.add_subplot(224)  # キャラクター分布
        
        # グラフの初期化
        self.init_charts()
        
        # キャンバス作成
        self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # ツールバー
        toolbar_frame = ttk.Frame(chart_frame)
        toolbar_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(toolbar_frame, text="更新", command=self.refresh_charts).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="データクリア", command=self.clear_data).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="エクスポート", command=self.export_data).pack(side=tk.LEFT)
    
    def create_details_panel(self, parent):
        """詳細情報パネル作成"""
        details_frame = ttk.LabelFrame(parent, text="詳細情報", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        # キャラクター詳細
        char_frame = ttk.LabelFrame(details_frame, text="キャラクター詳細", padding=5)
        char_frame.pack(fill=tk.X, pady=(0, 10))
        
        # キャラクター選択
        ttk.Label(char_frame, text="キャラクター:").pack(anchor=tk.W)
        self.char_combo = ttk.Combobox(char_frame, state="readonly")
        self.char_combo.pack(fill=tk.X, pady=(0, 5))
        self.char_combo.bind('<<ComboboxSelected>>', self.on_character_selected)
        
        # キャラクター統計表示
        self.char_details_text = scrolledtext.ScrolledText(
            char_frame, height=10, wrap=tk.WORD, font=('Consolas', 9)
        )
        self.char_details_text.pack(fill=tk.BOTH, expand=True)
        
        # 設定パネル
        settings_frame = ttk.LabelFrame(details_frame, text="設定", padding=5)
        settings_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 更新間隔設定
        ttk.Label(settings_frame, text="更新間隔(秒):").pack(anchor=tk.W)
        self.interval_var = tk.StringVar(value="2")
        interval_spin = ttk.Spinbox(
            settings_frame, from_=1, to=30, textvariable=self.interval_var,
            command=self.update_interval_changed
        )
        interval_spin.pack(fill=tk.X, pady=(0, 5))
        
        # 制御ボタン
        control_frame = ttk.Frame(settings_frame)
        control_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.pause_button = ttk.Button(control_frame, text="一時停止", command=self.toggle_pause)
        self.pause_button.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(control_frame, text="リセット", command=self.reset_dashboard).pack(side=tk.LEFT)
    
    def create_log_panel(self, parent):
        """ログパネル作成"""
        log_frame = ttk.LabelFrame(parent, text="ログ", padding=10)
        log_frame.pack(fill=tk.X)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=8, wrap=tk.WORD, font=('Consolas', 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # ログ制御
        log_control_frame = ttk.Frame(log_frame)
        log_control_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(log_control_frame, text="ログクリア", command=self.clear_log).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(log_control_frame, text="ログ保存", command=self.save_log).pack(side=tk.LEFT)
    
    def init_charts(self):
        """グラフの初期化"""
        # 一貫性スコアグラフ
        self.ax1.set_title('一貫性スコア推移', fontsize=10)
        self.ax1.set_xlabel('時間')
        self.ax1.set_ylabel('スコア')
        self.ax1.grid(True, alpha=0.3)
        
        # 処理時間グラフ
        self.ax2.set_title('処理時間推移', fontsize=10)
        self.ax2.set_xlabel('時間')
        self.ax2.set_ylabel('時間(秒)')
        self.ax2.grid(True, alpha=0.3)
        
        # 感情強度グラフ
        self.ax3.set_title('感情強度分布', fontsize=10)
        self.ax3.set_xlabel('強度')
        self.ax3.set_ylabel('頻度')
        self.ax3.grid(True, alpha=0.3)
        
        # キャラクター分布
        self.ax4.set_title('キャラクター出現頻度', fontsize=10)
        
        self.fig.tight_layout()
    
    def load_initial_data(self):
        """初期データ読み込み"""
        try:
            # NKATの状態確認
            self.check_nkat_status()
            
            # 既存の統計データがあれば読み込み
            self.load_consistency_data()
            
            self.log_message("初期データ読み込み完了")
            
        except Exception as e:
            self.log_message(f"初期データ読み込みエラー: {e}")
    
    def check_nkat_status(self):
        """NKAT機能の状態確認"""
        try:
            # config.jsonからNKAT設定を確認
            with open("config.json", "r", encoding="utf-8-sig") as f:
                config = json.load(f)
            
            self.nkat_enabled = config.get("nkat_enabled", False)
            
            # NKAT統合モジュールの存在確認
            nkat_module_exists = os.path.exists("src/nkat/nkat_integration.py")
            advanced_module_exists = os.path.exists("src/nkat/advanced_consistency.py")
            
            if self.nkat_enabled and nkat_module_exists and advanced_module_exists:
                status = "有効（高度モード対応）"
                color = "green"
            elif self.nkat_enabled and nkat_module_exists:
                status = "有効（標準モード）"
                color = "blue"
            elif nkat_module_exists:
                status = "無効（設定でOFF）"
                color = "orange"
            else:
                status = "未インストール"
                color = "red"
            
            self.nkat_status_label.config(text=status, foreground=color)
            
        except Exception as e:
            self.nkat_status_label.config(text=f"エラー: {e}", foreground="red")
    
    def load_consistency_data(self):
        """一貫性データの読み込み"""
        try:
            # セッションデータディレクトリを確認
            log_dir = "logs/consistency"
            if os.path.exists(log_dir):
                # 最新のセッションファイルを取得
                session_files = [f for f in os.listdir(log_dir) if f.startswith("session_")]
                if session_files:
                    latest_file = max(session_files, key=lambda x: os.path.getctime(os.path.join(log_dir, x)))
                    
                    with open(os.path.join(log_dir, latest_file), 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    self.processing_stats = session_data.get("report", {})
                    self.character_stats = self.processing_stats.get("character_statistics", {})
                    
                    self.log_message(f"セッションデータを読み込み: {latest_file}")
        
        except Exception as e:
            self.log_message(f"データ読み込みエラー: {e}")
    
    def start_update_loop(self):
        """定期更新ループ開始"""
        self.update_dashboard()
    
    def update_dashboard(self):
        """ダッシュボード更新"""
        if not self.is_running:
            return
        
        try:
            # NKAT統計取得（実際のアプリケーションが動いている場合）
            self.fetch_current_stats()
            
            # GUI更新
            self.update_summary_display()
            self.update_character_list()
            self.refresh_charts()
            
        except Exception as e:
            self.log_message(f"更新エラー: {e}")
        
        # 次回更新をスケジュール
        self.root.after(self.update_interval, self.update_dashboard)
    
    def fetch_current_stats(self):
        """現在の統計情報を取得"""
        try:
            # EasyNovelAssistantが動作している場合の統計取得
            # ここでは簡易的なデータ生成
            if self.nkat_enabled:
                # ダミーデータ生成（実際にはアプリケーションから取得）
                current_time = datetime.now()
                
                # 一貫性データ追加
                consistency_score = 0.7 + 0.3 * np.random.random()
                processing_time = 0.05 + 0.1 * np.random.random()
                emotion_intensity = np.random.random()
                
                self.consistency_data.append({
                    'timestamp': current_time,
                    'consistency_score': consistency_score,
                    'processing_time': processing_time,
                    'emotion_intensity': emotion_intensity
                })
                
                # 処理統計更新
                self.processing_stats = {
                    'total_generations': len(self.consistency_data),
                    'average_improvement_score': np.mean([d['consistency_score'] for d in self.consistency_data]),
                    'consistency_trend': [d['consistency_score'] for d in list(self.consistency_data)[-20:]]
                }
        
        except Exception as e:
            self.log_message(f"統計取得エラー: {e}")
    
    def update_summary_display(self):
        """サマリー表示更新"""
        try:
            # 処理済みテキスト数
            processed_count = self.processing_stats.get('total_generations', 0)
            self.processed_count_label.config(text=str(processed_count))
            
            # 一貫性改善率
            avg_score = self.processing_stats.get('average_improvement_score', 0)
            improvement_rate = avg_score * 100
            self.improvement_rate_label.config(text=f"{improvement_rate:.1f}%")
            
            # 平均処理時間
            if self.consistency_data:
                avg_time = np.mean([d['processing_time'] for d in self.consistency_data])
                self.avg_time_label.config(text=f"{avg_time:.3f}s")
            
            # アクティブキャラクター
            if self.character_stats:
                most_recent_char = max(self.character_stats.keys(), 
                                     key=lambda x: self.character_stats[x].get('count', 0))
                self.active_char_label.config(text=most_recent_char)
            
            # キャラクター総数
            char_count = len(self.character_stats)
            self.char_count_label.config(text=str(char_count))
            
        except Exception as e:
            self.log_message(f"サマリー更新エラー: {e}")
    
    def update_character_list(self):
        """キャラクターリスト更新"""
        try:
            current_chars = list(self.character_stats.keys())
            self.char_combo['values'] = current_chars
            
            if current_chars and self.char_combo.get() not in current_chars:
                self.char_combo.set(current_chars[0])
                self.on_character_selected()
        
        except Exception as e:
            self.log_message(f"キャラクターリスト更新エラー: {e}")
    
    def refresh_charts(self):
        """グラフ更新"""
        try:
            self.ax1.clear()
            self.ax2.clear()
            self.ax3.clear()
            self.ax4.clear()
            
            if self.consistency_data:
                timestamps = [d['timestamp'] for d in self.consistency_data]
                
                # 一貫性スコア推移
                consistency_scores = [d['consistency_score'] for d in self.consistency_data]
                self.ax1.plot(range(len(consistency_scores)), consistency_scores, 'b-', linewidth=2)
                self.ax1.set_title('一貫性スコア推移')
                self.ax1.set_ylabel('スコア')
                self.ax1.grid(True, alpha=0.3)
                
                # 処理時間推移
                processing_times = [d['processing_time'] for d in self.consistency_data]
                self.ax2.plot(range(len(processing_times)), processing_times, 'g-', linewidth=2)
                self.ax2.set_title('処理時間推移')
                self.ax2.set_ylabel('時間(秒)')
                self.ax2.grid(True, alpha=0.3)
                
                # 感情強度分布
                emotion_intensities = [d['emotion_intensity'] for d in self.consistency_data]
                self.ax3.hist(emotion_intensities, bins=20, alpha=0.7, color='orange')
                self.ax3.set_title('感情強度分布')
                self.ax3.set_xlabel('強度')
                self.ax3.set_ylabel('頻度')
                
                # キャラクター分布
                if self.character_stats:
                    char_names = list(self.character_stats.keys())
                    char_counts = [self.character_stats[name].get('count', 0) for name in char_names]
                    
                    if char_counts:
                        self.ax4.pie(char_counts, labels=char_names, autopct='%1.1f%%', startangle=90)
                        self.ax4.set_title('キャラクター出現頻度')
            
            self.fig.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            self.log_message(f"グラフ更新エラー: {e}")
    
    def on_character_selected(self, event=None):
        """キャラクター選択時の処理"""
        try:
            selected_char = self.char_combo.get()
            if selected_char and selected_char in self.character_stats:
                char_data = self.character_stats[selected_char]
                
                details = f"キャラクター: {selected_char}\n"
                details += f"出現回数: {char_data.get('count', 0)}\n"
                details += f"平均スコア: {char_data.get('avg_score', 0):.3f}\n"
                details += f"最新スコア: {char_data.get('scores', [0])[-1] if char_data.get('scores') else 0:.3f}\n"
                
                # スコア履歴
                scores = char_data.get('scores', [])
                if scores:
                    details += f"\nスコア履歴（最新10件）:\n"
                    recent_scores = scores[-10:]
                    for i, score in enumerate(recent_scores, 1):
                        details += f"  {i}: {score:.3f}\n"
                
                self.char_details_text.delete('1.0', tk.END)
                self.char_details_text.insert('1.0', details)
        
        except Exception as e:
            self.log_message(f"キャラクター詳細表示エラー: {e}")
    
    def update_interval_changed(self):
        """更新間隔変更"""
        try:
            new_interval = int(self.interval_var.get()) * 1000
            self.update_interval = new_interval
            self.log_message(f"更新間隔を{new_interval/1000}秒に変更")
        except ValueError:
            self.log_message("無効な更新間隔値")
    
    def toggle_pause(self):
        """更新一時停止/再開"""
        self.is_running = not self.is_running
        if self.is_running:
            self.pause_button.config(text="一時停止")
            self.update_dashboard()
            self.log_message("更新を再開")
        else:
            self.pause_button.config(text="再開")
            self.log_message("更新を一時停止")
    
    def reset_dashboard(self):
        """ダッシュボードリセット"""
        self.consistency_data.clear()
        self.character_stats.clear()
        self.processing_stats.clear()
        
        self.refresh_charts()
        self.update_summary_display()
        self.char_combo.set('')
        self.char_details_text.delete('1.0', tk.END)
        
        self.log_message("ダッシュボードをリセットしました")
    
    def clear_data(self):
        """データクリア"""
        self.consistency_data.clear()
        self.refresh_charts()
        self.log_message("グラフデータをクリアしました")
    
    def export_data(self):
        """データエクスポート"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"consistency_dashboard_export_{timestamp}.json"
            
            export_data = {
                "timestamp": timestamp,
                "processing_stats": self.processing_stats,
                "character_stats": self.character_stats,
                "consistency_data": [
                    {
                        "timestamp": d["timestamp"].isoformat(),
                        "consistency_score": d["consistency_score"],
                        "processing_time": d["processing_time"],
                        "emotion_intensity": d["emotion_intensity"]
                    }
                    for d in self.consistency_data
                ]
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.log_message(f"データをエクスポート: {filename}")
            
        except Exception as e:
            self.log_message(f"エクスポートエラー: {e}")
    
    def clear_log(self):
        """ログクリア"""
        self.log_text.delete('1.0', tk.END)
    
    def save_log(self):
        """ログ保存"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dashboard_log_{timestamp}.txt"
            
            log_content = self.log_text.get('1.0', tk.END)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(log_content)
            
            self.log_message(f"ログを保存: {filename}")
            
        except Exception as e:
            self.log_message(f"ログ保存エラー: {e}")
    
    def log_message(self, message: str):
        """ログメッセージ追加"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # ログ行数制限
        lines = self.log_text.get('1.0', tk.END).split('\n')
        if len(lines) > 1000:
            # 古いログを削除
            self.log_text.delete('1.0', f'{len(lines)-500}.0')
    
    def run(self):
        """ダッシュボード実行"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()
    
    def on_closing(self):
        """終了処理"""
        self.is_running = False
        self.log_message("ダッシュボードを終了します")
        self.root.quit()
        self.root.destroy()


if __name__ == "__main__":
    try:
        print("一貫性監視ダッシュボードを起動中...")
        dashboard = ConsistencyDashboard()
        dashboard.run()
    except Exception as e:
        print(f"ダッシュボード起動エラー: {e}")
        import traceback
        traceback.print_exc() 