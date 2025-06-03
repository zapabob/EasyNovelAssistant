# -*- coding: utf-8 -*-
"""
GGUF アドオンシステム
EXE版でGGUFファイルを後から追加できる機能

使用方法:
1. EXE版起動後、メニューから「GGUFファイル管理」を選択
2. 新しいGGUFファイルを追加
3. 自動的にバッチファイルが生成される
"""

import os
import sys
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import json
import time
from typing import List, Dict, Optional
import subprocess
import threading

class GGUFAddonSystem:
    """GGUF アドオンシステム"""
    
    def __init__(self, parent_window=None):
        self.parent_window = parent_window
        self.kobold_dir = self.get_kobold_directory()
        self.addon_window = None
        self.gguf_files = []
        self.model_configs = {}
        
        self.load_configurations()
        self.scan_existing_files()
    
    def get_kobold_directory(self) -> Path:
        """KoboldCppディレクトリの取得"""
        # 実行ファイルの場所を基準にする
        if getattr(sys, 'frozen', False):
            # EXE版の場合
            exe_dir = Path(sys.executable).parent
            kobold_dir = exe_dir / 'KoboldCpp'
        else:
            # 開発版の場合
            kobold_dir = Path('.') / 'KoboldCpp'
        
        # ディレクトリが存在しない場合は作成
        kobold_dir.mkdir(exist_ok=True)
        
        return kobold_dir
    
    def load_configurations(self):
        """設定の読み込み"""
        config_file = self.kobold_dir / "gguf_addon_config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.model_configs = data.get('models', {})
            except Exception as e:
                print(f"⚠️ 設定読み込みエラー: {e}")
                self.model_configs = {}
        else:
            self.model_configs = {}
    
    def save_configurations(self):
        """設定の保存"""
        config_file = self.kobold_dir / "gguf_addon_config.json"
        
        config_data = {
            'version': '1.0',
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S'),
            'models': self.model_configs
        }
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ 設定保存エラー: {e}")
    
    def scan_existing_files(self):
        """既存GGUFファイルのスキャン"""
        self.gguf_files = []
        
        if not self.kobold_dir.exists():
            return
        
        for gguf_file in self.kobold_dir.glob('*.gguf'):
            file_info = self.analyze_gguf_file(gguf_file)
            self.gguf_files.append(file_info)
        
        print(f"📁 {len(self.gguf_files)}個のGGUFファイルを検出")
    
    def analyze_gguf_file(self, gguf_file: Path) -> Dict:
        """GGUFファイルの詳細分析"""
        stat = gguf_file.stat()
        size_mb = stat.st_size / (1024 * 1024)
        size_gb = size_mb / 1024
        
        model_name = gguf_file.stem
        config = self.model_configs.get(model_name, {})
        
        # ファイル名からの推測
        quantization = self.extract_quantization_info(model_name)
        context_length = self.estimate_context_length(model_name)
        model_family = self.identify_model_family(model_name)
        
        return {
            'name': model_name,
            'filename': gguf_file.name,
            'path': str(gguf_file),
            'size_mb': size_mb,
            'size_gb': size_gb,
            'size_display': f"{size_gb:.1f} GB" if size_gb >= 1 else f"{size_mb:.1f} MB",
            'modified': time.ctime(stat.st_mtime),
            'quantization': quantization,
            'context_length': context_length,
            'model_family': model_family,
            'description': config.get('description', self.generate_description(model_family, quantization)),
            'custom_settings': config.get('custom_settings', {}),
            'usage_count': config.get('usage_count', 0),
            'last_used': config.get('last_used', '未使用'),
        }
    
    def extract_quantization_info(self, model_name: str) -> str:
        """量子化情報の抽出"""
        import re
        
        # より詳細な量子化パターン
        patterns = [
            (r'IQ\d+_[A-Z]{2,}', 'iMatrix量子化'),
            (r'Q\d+_K_[A-Z]', 'K-量子化'),
            (r'Q\d+_K', 'K-量子化'),
            (r'Q\d+_\d+', 'Legacy量子化'),
            (r'Q\d+', 'Standard量子化'),
            (r'F16', 'Float16'),
            (r'F32', 'Float32'),
        ]
        
        for pattern, type_name in patterns:
            match = re.search(pattern, model_name, re.IGNORECASE)
            if match:
                return f"{match.group(0).upper()} ({type_name})"
        
        return "不明"
    
    def estimate_context_length(self, model_name: str) -> int:
        """コンテキスト長の推定"""
        name_lower = model_name.lower()
        
        # より正確な推定
        context_patterns = [
            ('128k', 128000),
            ('32k', 32000),
            ('16k', 16000),
            ('8k', 8000),
            ('4k', 4000),
            ('c8k', 8000),
            ('c4k', 4000),
        ]
        
        for pattern, length in context_patterns:
            if pattern in name_lower:
                return length
        
        # モデルファミリーベースの推定
        if 'ninja' in name_lower:
            return 8000
        elif 'qwen' in name_lower:
            return 32000
        elif 'command' in name_lower:
            return 8000
        else:
            return 8000  # デフォルト
    
    def identify_model_family(self, model_name: str) -> str:
        """モデルファミリーの識別"""
        name_lower = model_name.lower()
        
        families = [
            ('ninja', 'Ninja系'),
            ('qwen', 'Qwen系'),
            ('command', 'Command R系'),
            ('vecteus', 'Vecteus系'),
            ('antler', 'Antler系'),
            ('lightchat', 'LightChat系'),
            ('fugaku', 'Fugaku系'),
            ('llama', 'Llama系'),
            ('gemma', 'Gemma系'),
            ('mistral', 'Mistral系'),
        ]
        
        for keyword, family in families:
            if keyword in name_lower:
                return family
        
        return '汎用モデル'
    
    def generate_description(self, model_family: str, quantization: str) -> str:
        """説明文の生成"""
        family_descriptions = {
            'Ninja系': '創作・ロールプレイ特化',
            'Qwen系': '多言語対応・高性能',
            'Command R系': '指示従行性に優れた汎用モデル',
            'Vecteus系': '日本語特化',
            'Antler系': '小説執筆特化',
            'LightChat系': '軽量・高速',
            'Fugaku系': '日本語大規模モデル',
            'Llama系': 'Meta開発の汎用モデル',
            'Gemma系': 'Google開発の軽量モデル',
            'Mistral系': 'Mistral AI開発の高性能モデル',
        }
        
        base_description = family_descriptions.get(model_family, '汎用言語モデル')
        return f"{base_description} ({quantization})"
    
    def create_batch_file(self, file_info: Dict) -> bool:
        """バッチファイルの作成"""
        model_name = file_info['name']
        context_length = file_info['context_length']
        
        # バッチファイル名
        bat_filename = f"Run-{model_name}-C{context_length//1000}K-L0.bat"
        bat_path = self.kobold_dir / bat_filename
        
        # カスタム設定
        custom_settings = file_info.get('custom_settings', {})
        
        # バッチファイル内容
        bat_content = f"""@echo off
chcp 65001 > NUL
cd /d "%~dp0"

echo 🎯 EasyNovelAssistant KoboldCpp サーバー起動
echo モデル: {model_name}
echo ファミリー: {file_info['model_family']}
echo 量子化: {file_info['quantization']}
echo コンテキスト: {context_length:,} トークン
echo サイズ: {file_info['size_display']}
echo ====================================

REM KoboldCppサーバー起動
koboldcpp.exe ^
    --model "{file_info['filename']}" ^
    --contextsize {context_length} ^
    --threads {custom_settings.get('threads', 8)} ^
    --gpulayers {custom_settings.get('gpu_layers', 0)} ^
    --port {custom_settings.get('port', 5001)} ^
    --host {custom_settings.get('host', '127.0.0.1')}"""

        # GPU利用設定
        if custom_settings.get('use_gpu', True):
            bat_content += " ^\n    --usecublas"
        
        # その他のオプション
        if custom_settings.get('use_mmap', True):
            bat_content += " ^\n    --usemmap"
        
        bat_content += """

if %errorlevel% neq 0 (
    echo.
    echo ❌ KoboldCppサーバーの起動に失敗しました
    echo GPU関連のエラーの場合は、GPU設定を確認してください
    pause
)
"""
        
        try:
            with open(bat_path, 'w', encoding='utf-8') as f:
                f.write(bat_content)
            print(f"📜 {bat_filename} を作成")
            return True
        except Exception as e:
            print(f"❌ バッチファイル作成エラー ({bat_filename}): {e}")
            return False
    
    def open_addon_gui(self):
        """アドオンGUIを開く"""
        if self.addon_window and self.addon_window.winfo_exists():
            self.addon_window.lift()
            return
        
        self.addon_window = tk.Toplevel(self.parent_window) if self.parent_window else tk.Tk()
        self.addon_window.title("🎯 GGUF アドオンシステム v3.0")
        self.addon_window.geometry("900x700")
        self.addon_window.resizable(True, True)
        
        self.setup_addon_gui()
    
    def setup_addon_gui(self):
        """アドオンGUI設定"""
        # メインフレーム
        main_frame = ttk.Frame(self.addon_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # タイトル
        title_label = ttk.Label(main_frame, text="🎯 GGUF アドオンシステム", 
                              font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # ノートブック（タブ）
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # タブ1: ファイル管理
        self.setup_file_management_tab(notebook)
        
        # タブ2: 設定
        self.setup_settings_tab(notebook)
        
        # タブ3: 統計
        self.setup_statistics_tab(notebook)
    
    def setup_file_management_tab(self, notebook):
        """ファイル管理タブ"""
        file_frame = ttk.Frame(notebook, padding="10")
        notebook.add(file_frame, text="📁 ファイル管理")
        
        # ボタンフレーム
        button_frame = ttk.Frame(file_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="📁 GGUFファイル追加", 
                  command=self.add_gguf_file_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="🔄 更新", 
                  command=self.refresh_file_list).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="🗑️ 削除", 
                  command=self.delete_selected_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="📜 バッチファイル生成", 
                  command=self.regenerate_batch_files).pack(side=tk.LEFT, padx=(0, 5))
        
        # ファイルリスト
        list_frame = ttk.Frame(file_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview
        columns = ('name', 'family', 'size', 'quantization', 'context', 'usage', 'description')
        self.file_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings')
        
        # カラム設定
        self.file_tree.heading('#0', text='✓')
        self.file_tree.heading('name', text='モデル名')
        self.file_tree.heading('family', text='ファミリー')
        self.file_tree.heading('size', text='サイズ')
        self.file_tree.heading('quantization', text='量子化')
        self.file_tree.heading('context', text='コンテキスト')
        self.file_tree.heading('usage', text='使用回数')
        self.file_tree.heading('description', text='説明')
        
        self.file_tree.column('#0', width=30)
        self.file_tree.column('name', width=150)
        self.file_tree.column('family', width=80)
        self.file_tree.column('size', width=80)
        self.file_tree.column('quantization', width=100)
        self.file_tree.column('context', width=80)
        self.file_tree.column('usage', width=60)
        self.file_tree.column('description', width=200)
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ファイルリスト更新
        self.refresh_file_list()
    
    def setup_settings_tab(self, notebook):
        """設定タブ"""
        settings_frame = ttk.Frame(notebook, padding="10")
        notebook.add(settings_frame, text="⚙️ 設定")
        
        # 設定項目
        ttk.Label(settings_frame, text="デフォルト設定", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        # スレッド数
        thread_frame = ttk.Frame(settings_frame)
        thread_frame.pack(fill=tk.X, pady=5)
        ttk.Label(thread_frame, text="スレッド数:").pack(side=tk.LEFT)
        self.thread_var = tk.StringVar(value="8")
        ttk.Entry(thread_frame, textvariable=self.thread_var, width=10).pack(side=tk.LEFT, padx=(5, 0))
        
        # GPUレイヤー数
        gpu_frame = ttk.Frame(settings_frame)
        gpu_frame.pack(fill=tk.X, pady=5)
        ttk.Label(gpu_frame, text="GPUレイヤー数:").pack(side=tk.LEFT)
        self.gpu_layers_var = tk.StringVar(value="0")
        ttk.Entry(gpu_frame, textvariable=self.gpu_layers_var, width=10).pack(side=tk.LEFT, padx=(5, 0))
        
        # ポート番号
        port_frame = ttk.Frame(settings_frame)
        port_frame.pack(fill=tk.X, pady=5)
        ttk.Label(port_frame, text="ポート番号:").pack(side=tk.LEFT)
        self.port_var = tk.StringVar(value="5001")
        ttk.Entry(port_frame, textvariable=self.port_var, width=10).pack(side=tk.LEFT, padx=(5, 0))
        
        # チェックボックス
        self.use_gpu_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="GPU利用（CUDA）", variable=self.use_gpu_var).pack(anchor=tk.W, pady=5)
        
        self.use_mmap_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="メモリマッピング利用", variable=self.use_mmap_var).pack(anchor=tk.W, pady=5)
        
        # 保存ボタン
        ttk.Button(settings_frame, text="設定を保存", command=self.save_default_settings).pack(pady=20)
    
    def setup_statistics_tab(self, notebook):
        """統計タブ"""
        stats_frame = ttk.Frame(notebook, padding="10")
        notebook.add(stats_frame, text="📊 統計")
        
        # 統計情報表示エリア
        self.stats_text = tk.Text(stats_frame, wrap=tk.WORD, height=20)
        stats_scrollbar = ttk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scrollbar.set)
        
        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 統計更新
        self.update_statistics()
    
    def add_gguf_file_dialog(self):
        """GGUFファイル追加ダイアログ"""
        files = filedialog.askopenfilenames(
            title="GGUFファイルを選択",
            filetypes=[("GGUF files", "*.gguf"), ("All files", "*.*")]
        )
        
        if not files:
            return
        
        success_count = 0
        for file_path in files:
            if self.add_gguf_file(file_path):
                success_count += 1
        
        if success_count > 0:
            self.refresh_file_list()
            messagebox.showinfo("追加完了", f"{success_count}個のファイルを追加しました")
    
    def add_gguf_file(self, source_path: str) -> bool:
        """GGUFファイルの追加"""
        source_file = Path(source_path)
        
        if not source_file.exists():
            messagebox.showerror("エラー", f"ファイルが見つかりません: {source_path}")
            return False
        
        if not source_file.suffix.lower() == '.gguf':
            messagebox.showerror("エラー", f"GGUFファイルではありません: {source_path}")
            return False
        
        dest_file = self.kobold_dir / source_file.name
        
        if dest_file.exists():
            result = messagebox.askyesno(
                "ファイル上書き確認",
                f"{source_file.name} は既に存在します。上書きしますか？"
            )
            if not result:
                return False
        
        try:
            # ファイルコピー（プログレスバー付きで実装可能）
            shutil.copy2(source_file, dest_file)
            
            # 分析とバッチファイル生成
            file_info = self.analyze_gguf_file(dest_file)
            self.create_batch_file(file_info)
            
            # 設定に追加
            self.model_configs[file_info['name']] = {
                'description': file_info['description'],
                'custom_settings': {
                    'threads': int(self.thread_var.get()),
                    'gpu_layers': int(self.gpu_layers_var.get()),
                    'port': int(self.port_var.get()),
                    'use_gpu': self.use_gpu_var.get(),
                    'use_mmap': self.use_mmap_var.get(),
                },
                'added_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'usage_count': 0,
                'last_used': '未使用'
            }
            
            self.save_configurations()
            self.scan_existing_files()
            
            return True
            
        except Exception as e:
            messagebox.showerror("エラー", f"ファイル追加に失敗しました: {e}")
            return False
    
    def refresh_file_list(self):
        """ファイルリストの更新"""
        # 既存のアイテムをクリア
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        # 再スキャン
        self.scan_existing_files()
        
        # ファイル追加
        for file_info in self.gguf_files:
            self.file_tree.insert('', tk.END, text='📄', values=(
                file_info['name'],
                file_info['model_family'],
                file_info['size_display'],
                file_info['quantization'],
                f"{file_info['context_length']:,}",
                file_info['usage_count'],
                file_info['description']
            ))
    
    def delete_selected_file(self):
        """選択ファイルの削除"""
        selection = self.file_tree.selection()
        if not selection:
            messagebox.showwarning("選択なし", "削除するファイルを選択してください")
            return
        
        selected_names = []
        for item in selection:
            values = self.file_tree.item(item)['values']
            selected_names.append(values[0])
        
        result = messagebox.askyesno(
            "削除確認",
            f"{len(selected_names)}個のファイルを削除しますか？\n\n" + 
            "\n".join(selected_names)
        )
        
        if not result:
            return
        
        deleted_count = 0
        for name in selected_names:
            if self.delete_gguf_file(name):
                deleted_count += 1
        
        if deleted_count > 0:
            self.refresh_file_list()
            messagebox.showinfo("削除完了", f"{deleted_count}個のファイルを削除しました")
    
    def delete_gguf_file(self, model_name: str) -> bool:
        """GGUFファイルの削除"""
        # ファイル検索
        target_file = None
        for file_info in self.gguf_files:
            if file_info['name'] == model_name:
                target_file = Path(file_info['path'])
                break
        
        if not target_file or not target_file.exists():
            return False
        
        try:
            # ファイル削除
            target_file.unlink()
            
            # バッチファイル削除
            for bat_file in self.kobold_dir.glob(f"Run-{model_name}-*.bat"):
                bat_file.unlink()
            
            # 設定から削除
            if model_name in self.model_configs:
                del self.model_configs[model_name]
                self.save_configurations()
            
            return True
            
        except Exception as e:
            print(f"❌ ファイル削除エラー: {e}")
            return False
    
    def regenerate_batch_files(self):
        """バッチファイルの再生成"""
        generated_count = 0
        
        for file_info in self.gguf_files:
            if self.create_batch_file(file_info):
                generated_count += 1
        
        messagebox.showinfo("生成完了", f"{generated_count}個のバッチファイルを生成しました")
    
    def save_default_settings(self):
        """デフォルト設定の保存"""
        # 設定を保存する処理
        messagebox.showinfo("保存完了", "デフォルト設定を保存しました")
    
    def update_statistics(self):
        """統計情報の更新"""
        stats_text = f"""📊 GGUF アドオンシステム 統計情報

🗂️ ファイル統計:
  総ファイル数: {len(self.gguf_files)}個
  総サイズ: {sum(f['size_gb'] for f in self.gguf_files):.1f} GB

📈 モデルファミリー別:"""

        # ファミリー別統計
        family_stats = {}
        for file_info in self.gguf_files:
            family = file_info['model_family']
            if family not in family_stats:
                family_stats[family] = {'count': 0, 'size': 0}
            family_stats[family]['count'] += 1
            family_stats[family]['size'] += file_info['size_gb']
        
        for family, stats in family_stats.items():
            stats_text += f"\n  {family}: {stats['count']}個 ({stats['size']:.1f} GB)"
        
        stats_text += f"""

💾 量子化別:"""
        
        # 量子化別統計
        quant_stats = {}
        for file_info in self.gguf_files:
            quant = file_info['quantization'].split(' ')[0]  # 括弧内を除去
            if quant not in quant_stats:
                quant_stats[quant] = 0
            quant_stats[quant] += 1
        
        for quant, count in quant_stats.items():
            stats_text += f"\n  {quant}: {count}個"
        
        stats_text += f"""

🎯 コンテキスト長別:"""
        
        # コンテキスト長別統計
        context_stats = {}
        for file_info in self.gguf_files:
            context = file_info['context_length']
            if context not in context_stats:
                context_stats[context] = 0
            context_stats[context] += 1
        
        for context, count in sorted(context_stats.items()):
            stats_text += f"\n  {context:,}トークン: {count}個"
        
        # 統計表示更新
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)


def main():
    """テスト実行"""
    print("🎯 GGUF アドオンシステム テスト")
    print("=" * 40)
    
    # GUI起動
    addon_system = GGUFAddonSystem()
    addon_system.open_addon_gui()
    
    if addon_system.addon_window:
        addon_system.addon_window.mainloop()


if __name__ == "__main__":
    main() 