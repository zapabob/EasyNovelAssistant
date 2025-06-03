# -*- coding: utf-8 -*-
"""
プロット記憶パネル v3.2 デモアプリケーション
作家体験革命 - 章管理・整合性チェック・プロット記憶

GUI v3.2の新機能体験デモ
"""

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import sys
import os
from typing import Dict, Any

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.insert(0, src_dir)

try:
    from ui.plot_memory_panel import PlotMemoryPanel
    print("✅ プロット記憶パネル v3.2 読み込み成功")
except ImportError as e:
    print(f"❌ プロット記憶パネル読み込み失敗: {e}")
    sys.exit(1)


class PlotMemoryDemoApp:
    """プロット記憶パネル v3.2 デモアプリケーション"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔥 EasyNovelAssistant - プロット記憶パネル v3.2 デモ")
        self.root.geometry("1200x800")
        
        # アプリケーション設定
        self.setup_app_config()
        
        # メインGUI構築
        self.build_main_gui()
        
        # デモデータの初期化
        self.setup_demo_data()
        
        print("🚀 プロット記憶パネル v3.2 デモ起動完了！")
    
    def setup_app_config(self):
        """アプリケーション設定"""
        # ウィンドウアイコン設定（もしあれば）
        try:
            self.root.iconbitmap("assets/icon.ico")
        except:
            pass
        
        # スタイル設定
        style = ttk.Style()
        style.theme_use('clam')  # モダンなテーマ
        
        # カスタムスタイル
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Subtitle.TLabel', font=('Arial', 12))
        style.configure('Demo.TButton', font=('Arial', 10, 'bold'))
    
    def build_main_gui(self):
        """メインGUI構築"""
        # === ヘッダー ===
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        title_label = ttk.Label(
            header_frame, 
            text="📚 プロット記憶パネル v3.2 - 作家体験革命デモ",
            style='Title.TLabel'
        )
        title_label.pack(side="left")
        
        # バージョン情報
        version_label = ttk.Label(
            header_frame, 
            text="Phase 3 完了記念版 🎉",
            style='Subtitle.TLabel'
        )
        version_label.pack(side="right")
        
        # === 説明エリア ===
        info_frame = ttk.LabelFrame(self.root, text="✨ 新機能紹介", padding="5")
        info_frame.pack(fill="x", padx=10, pady=5)
        
        info_text = """
🎯 作家のプロット管理を革命的に改善！

• 📖 章ごと要約管理 - プロットの全体像を把握
• 👥 キャラクター自動追跡 - 登場状況を一目で確認  
• 🗺️ 場所レジストリ - 舞台設定の整合性管理
• 🔍 自動整合性チェック - 矛盾を即座に検出
• 📊 プロット分析 - 物語構造の可視化
• ⚡ リアルタイム更新 - 執筆しながら同期更新
        """
        
        info_label = ttk.Label(info_frame, text=info_text.strip(), justify="left")
        info_label.pack(anchor="w")
        
        # === メインコンテンツエリア ===
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # プロット記憶パネルを配置
        self.plot_panel = PlotMemoryPanel(
            main_frame, 
            ctx=self,  # コンテキストとしてアプリ自体を渡す
            on_memory_changed=self.on_plot_memory_changed
        )
        self.plot_panel.pack(fill="both", expand=True)
        
        # === フッター（操作ガイド） ===
        footer_frame = ttk.LabelFrame(self.root, text="🎮 操作ガイド", padding="5")
        footer_frame.pack(fill="x", padx=10, pady=5)
        
        # 操作ボタン群
        button_frame = ttk.Frame(footer_frame)
        button_frame.pack(fill="x")
        
        ttk.Button(
            button_frame, 
            text="📝 サンプル小説読み込み", 
            command=self.load_sample_novel,
            style='Demo.TButton'
        ).pack(side="left", padx=5)
        
        ttk.Button(
            button_frame, 
            text="🔍 整合性デモ", 
            command=self.demo_consistency_check,
            style='Demo.TButton'
        ).pack(side="left", padx=5)
        
        ttk.Button(
            button_frame, 
            text="📊 分析デモ", 
            command=self.demo_plot_analysis,
            style='Demo.TButton'
        ).pack(side="left", padx=5)
        
        ttk.Button(
            button_frame, 
            text="🧹 リセット", 
            command=self.reset_demo,
            style='Demo.TButton'
        ).pack(side="left", padx=5)
        
        ttk.Button(
            button_frame, 
            text="❓ ヘルプ", 
            command=self.show_help,
            style='Demo.TButton'
        ).pack(side="right", padx=5)
        
        # ステータス表示
        status_text = "💡 「サンプル小説読み込み」からスタート！ 章管理・整合性チェックを体験してみてください。"
        status_label = ttk.Label(footer_frame, text=status_text, foreground="blue")
        status_label.pack(pady=5)
    
    def setup_demo_data(self):
        """デモ用データの初期設定"""
        # データディレクトリ作成
        os.makedirs("data", exist_ok=True)
        
        print("📁 デモ環境準備完了")
    
    def on_plot_memory_changed(self, chapter_memory):
        """プロット記憶変更時のコールバック"""
        print(f"📝 章データ更新: 第{chapter_memory.chapter_num}章 - {chapter_memory.title}")
    
    def load_sample_novel(self):
        """サンプル小説データの読み込み"""
        try:
            # サンプルデータを直接作成
            from ui.plot_memory_panel import ChapterMemory
            import json
            from datetime import datetime
            
            sample_chapters = {
                1: ChapterMemory(
                    chapter_num=1,
                    title="邂逅の夜",
                    summary="主人公の太郎が謎の少女・花子と運命的な出会いを果たす。古い図書館で起こった不思議な現象をきっかけに、二人の冒険が始まる。",
                    characters=["太郎", "花子", "図書館司書"],
                    locations=["古い図書館", "太郎の家", "商店街"],
                    plot_points=["太郎と花子の出会い", "図書館での不思議な現象", "謎の古書の発見"],
                    foreshadowing=["古書に記された予言", "花子の正体への伏線"],
                    character_states={"太郎": "困惑している", "花子": "秘密を隠している"},
                    timestamp=datetime.now().isoformat(),
                    word_count=3500
                ),
                2: ChapterMemory(
                    chapter_num=2,
                    title="隠された真実",
                    summary="花子の正体が明らかになる。彼女は別の世界からやってきた魔法使いだった。太郎は信じられない現実に戸惑いながらも、花子を助けることを決意する。",
                    characters=["太郎", "花子", "敵の魔法使い・黒羽"],
                    locations=["太郎の家", "秘密の地下洞窟", "花子の故郷（異世界）"],
                    plot_points=["花子の正体暴露", "太郎の決意", "黒羽の初登場", "地下洞窟の発見"],
                    foreshadowing=["黒羽の真の目的", "太郎の隠された力"],
                    character_states={"太郎": "決意を固めた", "花子": "安堵している", "黒羽": "計画を進めている"},
                    timestamp=datetime.now().isoformat(),
                    word_count=4200
                ),
                3: ChapterMemory(
                    chapter_num=3,
                    title="最初の試練",
                    summary="太郎と花子は黒羽から逃れるため、地下洞窟の奥へ向かう。そこで古代の封印を解く試練に挑戦する。太郎は初めて自分の魔法の才能に気づく。",
                    characters=["太郎", "花子", "古代の守護者・石像"],
                    locations=["地下洞窟", "古代の祭壇", "封印の間"],
                    plot_points=["地下洞窟探索", "古代の試練", "太郎の魔法覚醒", "封印の一部解除"],
                    foreshadowing=["完全な封印解除の条件", "太郎の真の出生"],
                    character_states={"太郎": "自信を得た", "花子": "太郎を信頼している"},
                    timestamp=datetime.now().isoformat(),
                    word_count=3800
                )
            }
            
            # プロット記憶パネルにデータ設定
            self.plot_panel.chapters = sample_chapters
            
            # キャラクタープロファイル作成
            self.plot_panel.character_profiles = {
                "太郎": {
                    "name": "太郎",
                    "appearances": [1, 2, 3],
                    "traits": ["勇敢", "優しい", "魔法の才能"],
                    "relationships": {"花子": "運命の相手"},
                    "first_appearance": 1
                },
                "花子": {
                    "name": "花子",
                    "appearances": [1, 2, 3],
                    "traits": ["神秘的", "魔法使い", "別世界出身"],
                    "relationships": {"太郎": "信頼している"},
                    "first_appearance": 1
                },
                "黒羽": {
                    "name": "黒羽",
                    "appearances": [2],
                    "traits": ["悪役", "強力な魔法使い", "謎の目的"],
                    "relationships": {"花子": "敵対"},
                    "first_appearance": 2
                }
            }
            
            # 場所レジストリ作成
            self.plot_panel.location_registry = {
                "古い図書館": {
                    "name": "古い図書館",
                    "appearances": [1],
                    "description": "物語の始まりの場所",
                    "first_appearance": 1
                },
                "地下洞窟": {
                    "name": "地下洞窟",
                    "appearances": [2, 3],
                    "description": "古代の秘密が眠る場所",
                    "first_appearance": 2
                },
                "太郎の家": {
                    "name": "太郎の家",
                    "appearances": [1, 2],
                    "description": "主人公の日常空間",
                    "first_appearance": 1
                }
            }
            
            # 表示更新
            self.plot_panel.refresh_chapter_list()
            self.plot_panel.update_statistics()
            
            messagebox.showinfo("読み込み完了", "サンプル小説「魔法少女と太郎の冒険」を読み込みました！\n\n📖 3章分のプロットデータが利用可能です。")
            
        except Exception as e:
            messagebox.showerror("エラー", f"サンプル読み込みに失敗: {e}")
    
    def demo_consistency_check(self):
        """整合性チェックのデモ"""
        if not self.plot_panel.chapters:
            messagebox.showwarning("警告", "先にサンプル小説を読み込んでください")
            return
        
        # 意図的にいくつかの矛盾を作成してデモ
        from ui.plot_memory_panel import ConsistencyAlert
        
        # デモ用アラート作成
        demo_alerts = [
            ConsistencyAlert(
                alert_type="character",
                severity="high",
                message="キャラクター「黒羽」が第2章以降で長期間未登場",
                chapter_refs=[2, 3]
            ),
            ConsistencyAlert(
                alert_type="location",
                severity="medium",
                message="場所名の表記ゆれ: 「古い図書館」と「図書館」",
                chapter_refs=[1]
            ),
            ConsistencyAlert(
                alert_type="plot",
                severity="low",
                message="伏線「太郎の真の出生」が未回収",
                chapter_refs=[3]
            )
        ]
        
        self.plot_panel.consistency_alerts = demo_alerts
        self.plot_panel.refresh_alerts_display()
        
        messagebox.showinfo(
            "整合性チェック完了", 
            f"デモ用整合性スキャンを実行しました。\n\n"
            f"🔴 重要: 1件\n"
            f"🟡 中程度: 1件\n"
            f"🟢 軽微: 1件\n\n"
            f"右パネルのアラートをダブルクリックして詳細を確認してください。"
        )
    
    def demo_plot_analysis(self):
        """プロット分析のデモ"""
        if not self.plot_panel.chapters:
            messagebox.showwarning("警告", "先にサンプル小説を読み込んでください")
            return
        
        # プロット分析を実行
        self.plot_panel.run_plot_analysis()
    
    def reset_demo(self):
        """デモのリセット"""
        if messagebox.askyesno("リセット確認", "デモデータをリセットしますか？"):
            self.plot_panel.new_project()
            messagebox.showinfo("リセット完了", "デモデータをリセットしました。")
    
    def show_help(self):
        """ヘルプ表示"""
        help_text = """
🎯 プロット記憶パネル v3.2 使い方ガイド

━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 基本操作
━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ サンプル小説読み込み
   • 「サンプル小説読み込み」ボタンでデモデータを読み込み

2️⃣ 章管理
   • 左パネルで章を選択・追加・削除
   • 中央パネルで章の詳細を編集

3️⃣ 整合性チェック
   • 「整合性スキャン」でプロットの矛盾を自動検出
   • アラートをダブルクリックで詳細表示

4️⃣ データベース管理
   • 「キャラ図鑑」でキャラクター情報を一覧
   • 「場所一覧」で舞台設定を管理

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔥 新機能ハイライト
━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ リアルタイム統計更新
✨ 自動整合性アラート
✨ プロット密度分析
✨ キャラクター追跡
✨ 場所レジストリ管理

━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase 3 完了記念！作家体験革命をお楽しみください🎉
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("❓ ヘルプ - プロット記憶パネル v3.2")
        help_window.geometry("600x500")
        
        help_text_widget = tk.Text(help_window, wrap="word", font=("Arial", 10))
        help_text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        help_text_widget.insert(1.0, help_text)
        help_text_widget.config(state="disabled")
        
        # 閉じるボタン
        close_button = ttk.Button(help_window, text="閉じる", command=help_window.destroy)
        close_button.pack(pady=10)
    
    def run(self):
        """アプリケーション実行"""
        print("🎬 GUI v3.2 デモ開始！")
        print("   作家体験革命をお楽しみください✨")
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n👋 デモ終了")
        except Exception as e:
            print(f"❌ エラー発生: {e}")
        finally:
            print("🏁 プロット記憶パネル v3.2 デモ終了")


def main():
    """メイン実行関数"""
    print("🚀 プロット記憶パネル v3.2 デモ起動中...")
    
    # デモアプリケーション作成・実行
    app = PlotMemoryDemoApp()
    app.run()


if __name__ == "__main__":
    main() 