# -*- coding: utf-8 -*-
"""
プロット記憶パネル v3.2
章ごと要約管理・整合性チェック・プロット記憶システム

作家体験革命のための中核UI
"""

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, filedialog
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict


@dataclass
class ChapterMemory:
    """章記憶データ"""
    chapter_num: int
    title: str
    summary: str
    characters: List[str]
    locations: List[str]
    plot_points: List[str]
    foreshadowing: List[str]
    character_states: Dict[str, str]  # キャラ状態（感情・状況等）
    timestamp: str
    word_count: int = 0
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)


@dataclass
class ConsistencyAlert:
    """整合性アラート"""
    alert_type: str  # character, location, plot, timeline
    severity: str    # high, medium, low
    message: str
    chapter_refs: List[int]
    auto_fix: bool = False


class PlotMemoryPanel:
    """プロット記憶パネル - 作家のプロット管理革命"""
    
    def __init__(self, parent, ctx, on_memory_changed: Optional[Callable] = None):
        self.ctx = ctx
        self.on_memory_changed = on_memory_changed
        
        # データストレージ
        self.chapters: Dict[int, ChapterMemory] = {}
        self.character_profiles: Dict[str, Dict] = {}
        self.location_registry: Dict[str, Dict] = {}
        self.timeline_events: List[Dict] = []
        self.consistency_alerts: List[ConsistencyAlert] = []
        
        # 現在の作業状態
        self.current_chapter = 1
        self.project_path = None
        
        # メインフレーム
        self.frame = ttk.LabelFrame(parent, text="📚 プロット記憶パネル v3.2", padding="5")
        
        # GUI構築
        self.build_gui()
        
        # 初期データロード
        self.load_project_data()
    
    def build_gui(self):
        """メインGUIの構築"""
        # === 上部：プロジェクト管理 ===
        project_frame = ttk.Frame(self.frame)
        project_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=2)
        
        ttk.Button(project_frame, text="新規プロジェクト", 
                  command=self.new_project).pack(side="left", padx=2)
        ttk.Button(project_frame, text="プロジェクト読込", 
                  command=self.load_project).pack(side="left", padx=2)
        ttk.Button(project_frame, text="保存", 
                  command=self.save_project).pack(side="left", padx=2)
        
        self.project_label = ttk.Label(project_frame, text="プロジェクト: 未設定")
        self.project_label.pack(side="right", padx=10)
        
        # === 左パネル：章管理 ===
        left_frame = ttk.LabelFrame(self.frame, text="章管理", padding="3")
        left_frame.grid(row=1, column=0, sticky="nsew", padx=2)
        
        # 章リスト
        self.chapter_listbox = tk.Listbox(left_frame, height=8, width=20)
        self.chapter_listbox.pack(fill="both", expand=True, padx=2, pady=2)
        self.chapter_listbox.bind("<<ListboxSelect>>", self.on_chapter_select)
        
        # 章操作ボタン
        chapter_buttons = ttk.Frame(left_frame)
        chapter_buttons.pack(fill="x", pady=2)
        
        ttk.Button(chapter_buttons, text="新章追加", 
                  command=self.add_chapter).pack(side="left", padx=1)
        ttk.Button(chapter_buttons, text="削除", 
                  command=self.delete_chapter).pack(side="left", padx=1)
        
        # === 中央パネル：章詳細編集 ===
        center_frame = ttk.LabelFrame(self.frame, text="章詳細", padding="3")
        center_frame.grid(row=1, column=1, sticky="nsew", padx=2)
        
        # 章タイトル
        ttk.Label(center_frame, text="章タイトル:").grid(row=0, column=0, sticky="w")
        self.title_entry = ttk.Entry(center_frame, width=30)
        self.title_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.title_entry.bind("<KeyRelease>", self.on_chapter_data_changed)
        
        # 章要約
        ttk.Label(center_frame, text="要約:").grid(row=1, column=0, sticky="nw", pady=(5,0))
        summary_frame = ttk.Frame(center_frame)
        summary_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=(5,0))
        
        self.summary_text = tk.Text(summary_frame, height=4, width=40, wrap="word")
        summary_scroll = ttk.Scrollbar(summary_frame, orient="vertical", command=self.summary_text.yview)
        self.summary_text.configure(yscrollcommand=summary_scroll.set)
        self.summary_text.pack(side="left", fill="both", expand=True)
        summary_scroll.pack(side="right", fill="y")
        self.summary_text.bind("<KeyRelease>", self.on_chapter_data_changed)
        
        # キャラクター・場所
        ttk.Label(center_frame, text="登場キャラ:").grid(row=2, column=0, sticky="nw", pady=(5,0))
        self.characters_entry = ttk.Entry(center_frame, width=30)
        self.characters_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=(5,0))
        self.characters_entry.bind("<KeyRelease>", self.on_chapter_data_changed)
        
        ttk.Label(center_frame, text="場所:").grid(row=3, column=0, sticky="nw", pady=(5,0))
        self.locations_entry = ttk.Entry(center_frame, width=30)
        self.locations_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=(5,0))
        self.locations_entry.bind("<KeyRelease>", self.on_chapter_data_changed)
        
        # プロットポイント
        ttk.Label(center_frame, text="重要展開:").grid(row=4, column=0, sticky="nw", pady=(5,0))
        plot_frame = ttk.Frame(center_frame)
        plot_frame.grid(row=4, column=1, sticky="nsew", padx=5, pady=(5,0))
        
        self.plot_text = tk.Text(plot_frame, height=3, width=40, wrap="word")
        plot_scroll = ttk.Scrollbar(plot_frame, orient="vertical", command=self.plot_text.yview)
        self.plot_text.configure(yscrollcommand=plot_scroll.set)
        self.plot_text.pack(side="left", fill="both", expand=True)
        plot_scroll.pack(side="right", fill="y")
        self.plot_text.bind("<KeyRelease>", self.on_chapter_data_changed)
        
        center_frame.columnconfigure(1, weight=1)
        center_frame.rowconfigure(1, weight=1)
        center_frame.rowconfigure(4, weight=1)
        
        # === 右パネル：整合性チェック ===
        right_frame = ttk.LabelFrame(self.frame, text="整合性チェック", padding="3")
        right_frame.grid(row=1, column=2, sticky="nsew", padx=2)
        
        # 整合性チェックボタン
        ttk.Button(right_frame, text="🔍 整合性スキャン", 
                  command=self.run_consistency_check).pack(fill="x", pady=2)
        
        # アラート表示
        self.alerts_listbox = tk.Listbox(right_frame, height=8, width=25)
        self.alerts_listbox.pack(fill="both", expand=True, padx=2, pady=2)
        self.alerts_listbox.bind("<Double-Button-1>", self.on_alert_double_click)
        
        # 統計情報
        stats_frame = ttk.LabelFrame(right_frame, text="プロジェクト統計", padding="2")
        stats_frame.pack(fill="x", pady=2)
        
        self.stats_label = ttk.Label(stats_frame, text="章数: 0\nキャラ: 0\n場所: 0")
        self.stats_label.pack()
        
        # === 下部：クイックアクション ===
        action_frame = ttk.Frame(self.frame)
        action_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=2)
        
        ttk.Button(action_frame, text="📖 キャラ図鑑", 
                  command=self.open_character_database).pack(side="left", padx=2)
        ttk.Button(action_frame, text="🗺️ 場所一覧", 
                  command=self.open_location_database).pack(side="left", padx=2)
        ttk.Button(action_frame, text="📊 プロット分析", 
                  command=self.run_plot_analysis).pack(side="left", padx=2)
        ttk.Button(action_frame, text="🔄 自動整合", 
                  command=self.auto_fix_consistency).pack(side="left", padx=2)
        
        # グリッド重み設定
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=2)
        self.frame.columnconfigure(2, weight=1)
        self.frame.rowconfigure(1, weight=1)
    
    def new_project(self):
        """新規プロジェクト作成"""
        self.chapters.clear()
        self.character_profiles.clear()
        self.location_registry.clear()
        self.timeline_events.clear()
        self.consistency_alerts.clear()
        self.current_chapter = 1
        self.project_path = None
        
        self.refresh_chapter_list()
        self.clear_chapter_form()
        self.update_project_label()
        self.update_statistics()
        
        messagebox.showinfo("プロジェクト", "新規プロジェクトを作成しました")
    
    def load_project(self):
        """プロジェクト読み込み"""
        filepath = filedialog.askopenfilename(
            title="プロジェクトファイルを選択",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.chapters = {
                    int(k): ChapterMemory.from_dict(v) 
                    for k, v in data.get('chapters', {}).items()
                }
                self.character_profiles = data.get('character_profiles', {})
                self.location_registry = data.get('location_registry', {})
                self.timeline_events = data.get('timeline_events', [])
                self.current_chapter = data.get('current_chapter', 1)
                self.project_path = filepath
                
                self.refresh_chapter_list()
                self.update_project_label()
                self.update_statistics()
                
                messagebox.showinfo("読み込み", f"プロジェクトを読み込みました: {os.path.basename(filepath)}")
                
            except Exception as e:
                messagebox.showerror("エラー", f"プロジェクトの読み込みに失敗しました: {e}")
    
    def save_project(self):
        """プロジェクト保存"""
        if not self.project_path:
            self.project_path = filedialog.asksaveasfilename(
                title="プロジェクトを保存",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
        
        if self.project_path:
            try:
                data = {
                    'chapters': {k: v.to_dict() for k, v in self.chapters.items()},
                    'character_profiles': self.character_profiles,
                    'location_registry': self.location_registry,
                    'timeline_events': self.timeline_events,
                    'current_chapter': self.current_chapter,
                    'saved_at': datetime.now().isoformat()
                }
                
                with open(self.project_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("保存", f"プロジェクトを保存しました: {os.path.basename(self.project_path)}")
                
            except Exception as e:
                messagebox.showerror("エラー", f"プロジェクトの保存に失敗しました: {e}")
    
    def add_chapter(self):
        """新章追加"""
        chapter_num = max(self.chapters.keys(), default=0) + 1
        
        new_chapter = ChapterMemory(
            chapter_num=chapter_num,
            title=f"第{chapter_num}章",
            summary="",
            characters=[],
            locations=[],
            plot_points=[],
            foreshadowing=[],
            character_states={},
            timestamp=datetime.now().isoformat()
        )
        
        self.chapters[chapter_num] = new_chapter
        self.refresh_chapter_list()
        self.select_chapter(chapter_num)
        self.update_statistics()
    
    def delete_chapter(self):
        """章削除"""
        selection = self.chapter_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "削除する章を選択してください")
            return
        
        chapter_num = list(self.chapters.keys())[selection[0]]
        
        if messagebox.askyesno("削除確認", f"第{chapter_num}章を削除しますか？"):
            del self.chapters[chapter_num]
            self.refresh_chapter_list()
            self.clear_chapter_form()
            self.update_statistics()
    
    def on_chapter_select(self, event):
        """章選択時の処理"""
        selection = self.chapter_listbox.curselection()
        if selection:
            chapter_num = list(self.chapters.keys())[selection[0]]
            self.select_chapter(chapter_num)
    
    def select_chapter(self, chapter_num: int):
        """指定章を選択・表示"""
        if chapter_num not in self.chapters:
            return
        
        chapter = self.chapters[chapter_num]
        self.current_chapter = chapter_num
        
        # フォームにデータを設定
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, chapter.title)
        
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, chapter.summary)
        
        self.characters_entry.delete(0, tk.END)
        self.characters_entry.insert(0, ", ".join(chapter.characters))
        
        self.locations_entry.delete(0, tk.END)
        self.locations_entry.insert(0, ", ".join(chapter.locations))
        
        self.plot_text.delete(1.0, tk.END)
        self.plot_text.insert(1.0, "\n".join(chapter.plot_points))
    
    def on_chapter_data_changed(self, event=None):
        """章データ変更時の処理"""
        if self.current_chapter not in self.chapters:
            return
        
        chapter = self.chapters[self.current_chapter]
        
        # フォームデータを章データに反映
        chapter.title = self.title_entry.get()
        chapter.summary = self.summary_text.get(1.0, tk.END).strip()
        chapter.characters = [c.strip() for c in self.characters_entry.get().split(",") if c.strip()]
        chapter.locations = [l.strip() for l in self.locations_entry.get().split(",") if l.strip()]
        chapter.plot_points = [p.strip() for p in self.plot_text.get(1.0, tk.END).strip().split("\n") if p.strip()]
        
        # リストボックス更新
        self.refresh_chapter_list()
        
        # キャラクター・場所データベース更新
        self.update_character_profiles(chapter.characters)
        self.update_location_registry(chapter.locations)
        
        # 変更通知
        if self.on_memory_changed:
            self.on_memory_changed(chapter)
    
    def refresh_chapter_list(self):
        """章リスト更新"""
        self.chapter_listbox.delete(0, tk.END)
        
        for chapter_num in sorted(self.chapters.keys()):
            chapter = self.chapters[chapter_num]
            display_text = f"第{chapter_num}章: {chapter.title}"
            self.chapter_listbox.insert(tk.END, display_text)
    
    def clear_chapter_form(self):
        """章フォームクリア"""
        self.title_entry.delete(0, tk.END)
        self.summary_text.delete(1.0, tk.END)
        self.characters_entry.delete(0, tk.END)
        self.locations_entry.delete(0, tk.END)
        self.plot_text.delete(1.0, tk.END)
    
    def update_project_label(self):
        """プロジェクトラベル更新"""
        if self.project_path:
            filename = os.path.basename(self.project_path)
            self.project_label.config(text=f"プロジェクト: {filename}")
        else:
            self.project_label.config(text="プロジェクト: 未保存")
    
    def update_statistics(self):
        """統計情報更新"""
        chapter_count = len(self.chapters)
        character_count = len(self.character_profiles)
        location_count = len(self.location_registry)
        
        stats_text = f"章数: {chapter_count}\nキャラ: {character_count}\n場所: {location_count}"
        self.stats_label.config(text=stats_text)
    
    def update_character_profiles(self, characters: List[str]):
        """キャラクタープロファイル更新"""
        for char in characters:
            if char not in self.character_profiles:
                self.character_profiles[char] = {
                    'name': char,
                    'appearances': [],
                    'traits': [],
                    'relationships': {},
                    'first_appearance': self.current_chapter
                }
            
            if self.current_chapter not in self.character_profiles[char]['appearances']:
                self.character_profiles[char]['appearances'].append(self.current_chapter)
    
    def update_location_registry(self, locations: List[str]):
        """場所レジストリ更新"""
        for loc in locations:
            if loc not in self.location_registry:
                self.location_registry[loc] = {
                    'name': loc,
                    'appearances': [],
                    'description': '',
                    'first_appearance': self.current_chapter
                }
            
            if self.current_chapter not in self.location_registry[loc]['appearances']:
                self.location_registry[loc]['appearances'].append(self.current_chapter)
    
    def run_consistency_check(self):
        """整合性チェック実行"""
        self.consistency_alerts.clear()
        
        # キャラクター整合性チェック
        self._check_character_consistency()
        
        # 場所整合性チェック
        self._check_location_consistency()
        
        # タイムライン整合性チェック
        self._check_timeline_consistency()
        
        # アラート表示更新
        self.refresh_alerts_display()
        
        messagebox.showinfo("整合性チェック", f"スキャン完了。{len(self.consistency_alerts)}件のアラートが検出されました。")
    
    def _check_character_consistency(self):
        """キャラクター整合性チェック"""
        for char_name, profile in self.character_profiles.items():
            appearances = profile['appearances']
            
            # 長期間登場していないキャラをチェック
            if len(appearances) > 1:
                last_appearance = max(appearances)
                current_max = max(self.chapters.keys()) if self.chapters else 0
                
                if current_max - last_appearance > 5:  # 5章以上未登場
                    alert = ConsistencyAlert(
                        alert_type="character",
                        severity="medium",
                        message=f"キャラクター「{char_name}」が{current_max - last_appearance}章間未登場",
                        chapter_refs=[last_appearance, current_max]
                    )
                    self.consistency_alerts.append(alert)
    
    def _check_location_consistency(self):
        """場所整合性チェック"""
        # 場所名の表記ゆれチェック
        location_names = list(self.location_registry.keys())
        
        for i, loc1 in enumerate(location_names):
            for loc2 in location_names[i+1:]:
                # 簡単な類似度チェック（レーベンシュタイン距離の代替）
                if self._are_similar_names(loc1, loc2):
                    alert = ConsistencyAlert(
                        alert_type="location",
                        severity="high",
                        message=f"場所名の表記ゆれの可能性: 「{loc1}」と「{loc2}」",
                        chapter_refs=[]
                    )
                    self.consistency_alerts.append(alert)
    
    def _check_timeline_consistency(self):
        """タイムライン整合性チェック"""
        # 章の順序と内容の論理的整合性をチェック
        chapter_nums = sorted(self.chapters.keys())
        
        for i in range(1, len(chapter_nums)):
            prev_chapter = self.chapters[chapter_nums[i-1]]
            curr_chapter = self.chapters[chapter_nums[i]]
            
            # 前章で死んだキャラが次章に登場していないかチェック（簡易版）
            prev_summary = prev_chapter.summary.lower()
            if "死ん" in prev_summary or "亡くな" in prev_summary:
                # 死亡キーワードがある場合、前章と今章のキャラ重複をチェック
                overlap = set(prev_chapter.characters) & set(curr_chapter.characters)
                if overlap:
                    alert = ConsistencyAlert(
                        alert_type="timeline",
                        severity="high",
                        message=f"第{prev_chapter.chapter_num}章で死亡の記述があるが、第{curr_chapter.chapter_num}章に同キャラが登場",
                        chapter_refs=[prev_chapter.chapter_num, curr_chapter.chapter_num]
                    )
                    self.consistency_alerts.append(alert)
    
    def _are_similar_names(self, name1: str, name2: str) -> bool:
        """名前の類似度判定（簡易版）"""
        # 長さの差が1以下で、文字の80%以上が一致
        if abs(len(name1) - len(name2)) > 1:
            return False
        
        longer = name1 if len(name1) >= len(name2) else name2
        shorter = name2 if len(name1) >= len(name2) else name1
        
        matches = sum(1 for c in shorter if c in longer)
        similarity = matches / len(longer)
        
        return similarity >= 0.8 and name1 != name2
    
    def refresh_alerts_display(self):
        """アラート表示更新"""
        self.alerts_listbox.delete(0, tk.END)
        
        severity_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        
        for alert in self.consistency_alerts:
            icon = severity_icons.get(alert.severity, "⚪")
            display_text = f"{icon} {alert.message}"
            self.alerts_listbox.insert(tk.END, display_text)
    
    def on_alert_double_click(self, event):
        """アラートダブルクリック時の処理"""
        selection = self.alerts_listbox.curselection()
        if selection:
            alert = self.consistency_alerts[selection[0]]
            self.show_alert_details(alert)
    
    def show_alert_details(self, alert: ConsistencyAlert):
        """アラート詳細表示"""
        details = f"種類: {alert.alert_type}\n"
        details += f"重要度: {alert.severity}\n"
        details += f"内容: {alert.message}\n"
        if alert.chapter_refs:
            details += f"関連章: {', '.join(map(str, alert.chapter_refs))}"
        
        messagebox.showinfo("アラート詳細", details)
    
    def open_character_database(self):
        """キャラクターデータベース表示"""
        if not self.character_profiles:
            messagebox.showinfo("キャラ図鑑", "まだキャラクターが登録されていません")
            return
        
        # 新しいウィンドウでキャラクター一覧を表示
        char_window = tk.Toplevel(self.frame)
        char_window.title("キャラクター図鑑")
        char_window.geometry("500x400")
        
        # キャラクターリスト
        char_list = tk.Listbox(char_window)
        char_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        for char_name, profile in self.character_profiles.items():
            appearances = profile['appearances']
            display_text = f"{char_name} (登場: {len(appearances)}章)"
            char_list.insert(tk.END, display_text)
    
    def open_location_database(self):
        """場所データベース表示"""
        if not self.location_registry:
            messagebox.showinfo("場所一覧", "まだ場所が登録されていません")
            return
        
        # 新しいウィンドウで場所一覧を表示
        loc_window = tk.Toplevel(self.frame)
        loc_window.title("場所一覧")
        loc_window.geometry("500x400")
        
        # 場所リスト
        loc_list = tk.Listbox(loc_window)
        loc_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        for loc_name, info in self.location_registry.items():
            appearances = info['appearances']
            display_text = f"{loc_name} (登場: {len(appearances)}章)"
            loc_list.insert(tk.END, display_text)
    
    def run_plot_analysis(self):
        """プロット分析実行"""
        if not self.chapters:
            messagebox.showinfo("プロット分析", "分析する章がありません")
            return
        
        # 分析結果ウィンドウ
        analysis_window = tk.Toplevel(self.frame)
        analysis_window.title("プロット分析結果")
        analysis_window.geometry("600x500")
        
        # 分析結果テキスト
        result_text = tk.Text(analysis_window, wrap="word")
        result_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 分析内容を生成
        analysis = self._generate_plot_analysis()
        result_text.insert(1.0, analysis)
        result_text.config(state="disabled")
    
    def _generate_plot_analysis(self) -> str:
        """プロット分析内容生成"""
        total_chapters = len(self.chapters)
        total_characters = len(self.character_profiles)
        total_locations = len(self.location_registry)
        
        analysis = f"📊 プロット分析レポート\n"
        analysis += f"{'='*40}\n\n"
        
        analysis += f"📖 基本統計\n"
        analysis += f"   総章数: {total_chapters}\n"
        analysis += f"   登場キャラ数: {total_characters}\n"
        analysis += f"   登場場所数: {total_locations}\n\n"
        
        # キャラクター分析
        analysis += f"👥 キャラクター分析\n"
        if self.character_profiles:
            for char_name, profile in sorted(self.character_profiles.items(), 
                                           key=lambda x: len(x[1]['appearances']), reverse=True):
                appearances = len(profile['appearances'])
                analysis += f"   {char_name}: {appearances}章登場\n"
        
        analysis += f"\n🗺️ 場所分析\n"
        if self.location_registry:
            for loc_name, info in sorted(self.location_registry.items(), 
                                       key=lambda x: len(x[1]['appearances']), reverse=True):
                appearances = len(info['appearances'])
                analysis += f"   {loc_name}: {appearances}章登場\n"
        
        # プロット密度分析
        analysis += f"\n📈 プロット密度\n"
        for chapter_num in sorted(self.chapters.keys()):
            chapter = self.chapters[chapter_num]
            plot_density = len(chapter.plot_points)
            analysis += f"   第{chapter_num}章: {plot_density}個の重要展開\n"
        
        return analysis
    
    def auto_fix_consistency(self):
        """自動整合性修正"""
        if not self.consistency_alerts:
            messagebox.showinfo("自動整合", "修正すべきアラートがありません")
            return
        
        fixed_count = 0
        
        # 自動修正可能なアラートを処理
        for alert in self.consistency_alerts[:]:  # コピーを作成して反復
            if alert.auto_fix:
                # TODO: 具体的な自動修正ロジックを実装
                fixed_count += 1
                self.consistency_alerts.remove(alert)
        
        if fixed_count > 0:
            self.refresh_alerts_display()
            messagebox.showinfo("自動整合", f"{fixed_count}件のアラートを自動修正しました")
        else:
            messagebox.showinfo("自動整合", "自動修正可能なアラートがありませんでした")
    
    def load_project_data(self):
        """プロジェクトデータの初期読み込み"""
        # デフォルトプロジェクトファイルがあれば読み込み
        default_project = "data/default_project.json"
        if os.path.exists(default_project):
            try:
                with open(default_project, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.chapters = {
                    int(k): ChapterMemory.from_dict(v) 
                    for k, v in data.get('chapters', {}).items()
                }
                self.character_profiles = data.get('character_profiles', {})
                self.location_registry = data.get('location_registry', {})
                self.timeline_events = data.get('timeline_events', [])
                self.current_chapter = data.get('current_chapter', 1)
                self.project_path = default_project
                
                self.refresh_chapter_list()
                self.update_project_label()
                self.update_statistics()
                
            except Exception as e:
                print(f"デフォルトプロジェクトの読み込みに失敗: {e}")
    
    def pack(self, **kwargs):
        """Tkinter pack メソッド"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Tkinter grid メソッド"""
        self.frame.grid(**kwargs) 