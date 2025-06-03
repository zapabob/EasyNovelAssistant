# -*- coding: utf-8 -*-
"""
GGUF ファイル管理システム
KoboldCpp + GGUF統合対応版

機能:
1. GGUFファイルの自動検出
2. 新しいGGUFファイルの追加
3. 設定バッチファイルの自動生成
4. モデル情報の表示
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

class GGUFManager:
    """GGUF ファイル管理システム"""
    
    def __init__(self, kobold_dir: str = "KoboldCpp"):
        self.kobold_dir = Path(kobold_dir)
        self.gguf_files = []
        self.model_configs = {}
        self.load_model_configs()
        self.scan_gguf_files()
    
    def load_model_configs(self):
        """モデル設定の読み込み"""
        config_file = self.kobold_dir / "model_configs.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.model_configs = json.load(f)
            except Exception as e:
                print(f"⚠️ モデル設定読み込みエラー: {e}")
                self.model_configs = {}
        else:
            self.model_configs = {}
    
    def save_model_configs(self):
        """モデル設定の保存"""
        config_file = self.kobold_dir / "model_configs.json"
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.model_configs, f, indent=2, ensure_ascii=False)
            print(f"✅ モデル設定を保存: {config_file}")
        except Exception as e:
            print(f"❌ モデル設定保存エラー: {e}")
    
    def scan_gguf_files(self):
        """GGUFファイルのスキャン"""
        if not self.kobold_dir.exists():
            print(f"⚠️ KoboldCppディレクトリが見つかりません: {self.kobold_dir}")
            return
        
        self.gguf_files = []
        
        for gguf_file in self.kobold_dir.glob('*.gguf'):
            file_info = self.get_file_info(gguf_file)
            self.gguf_files.append(file_info)
        
        print(f"📁 {len(self.gguf_files)}個のGGUFファイルを検出")
        
        # バッチファイルも更新
        self.update_batch_files()
    
    def get_file_info(self, gguf_file: Path) -> Dict:
        """ファイル情報の取得"""
        stat = gguf_file.stat()
        size_mb = stat.st_size / (1024 * 1024)
        size_gb = size_mb / 1024
        
        # ファイル名からモデル情報を推測
        model_name = gguf_file.stem
        
        # 設定があれば読み込み
        config = self.model_configs.get(model_name, {})
        
        return {
            'name': model_name,
            'filename': gguf_file.name,
            'path': str(gguf_file),
            'size_mb': size_mb,
            'size_gb': size_gb,
            'size_display': f"{size_gb:.1f} GB" if size_gb >= 1 else f"{size_mb:.1f} MB",
            'modified': time.ctime(stat.st_mtime),
            'description': config.get('description', self.guess_model_description(model_name)),
            'context_length': config.get('context_length', self.guess_context_length(model_name)),
            'quantization': self.extract_quantization(model_name),
            'recommended_layers': config.get('recommended_layers', 0),
        }
    
    def guess_model_description(self, model_name: str) -> str:
        """モデル説明の推測"""
        name_lower = model_name.lower()
        
        if 'ninja' in name_lower:
            return "Ninja系モデル - 創作・ロールプレイ特化"
        elif 'command' in name_lower:
            return "Command R系モデル - 指示従行性に優れた汎用モデル"
        elif 'qwen' in name_lower:
            return "Qwen系モデル - 多言語対応・高性能"
        elif 'vecteus' in name_lower:
            return "Vecteus系モデル - 日本語特化"
        elif 'antler' in name_lower:
            return "Antler系モデル - 小説執筆特化"
        elif 'lightchat' in name_lower:
            return "LightChat系モデル - 軽量・高速"
        elif 'fugaku' in name_lower:
            return "Fugaku系モデル - 日本語大規模モデル"
        else:
            return "汎用言語モデル"
    
    def guess_context_length(self, model_name: str) -> int:
        """コンテキスト長の推測"""
        name_lower = model_name.lower()
        
        if '128k' in name_lower:
            return 128000
        elif '32k' in name_lower:
            return 32000
        elif '16k' in name_lower:
            return 16000
        elif '8k' in name_lower or 'c8k' in name_lower:
            return 8000
        elif '4k' in name_lower or 'c4k' in name_lower:
            return 4000
        else:
            return 8000  # デフォルト
    
    def extract_quantization(self, model_name: str) -> str:
        """量子化形式の抽出"""
        import re
        
        # Q4_K_M, IQ4_XS, Q6_K などの量子化パターンを抽出
        quant_patterns = [
            r'IQ\d+_[A-Z]+',
            r'Q\d+_[A-Z]+',
            r'Q\d+_\d+',
            r'Q\d+'
        ]
        
        for pattern in quant_patterns:
            match = re.search(pattern, model_name, re.IGNORECASE)
            if match:
                return match.group(0).upper()
        
        return "不明"
    
    def update_batch_files(self):
        """バッチファイルの更新"""
        for file_info in self.gguf_files:
            self.create_batch_file(file_info)
    
    def create_batch_file(self, file_info: Dict):
        """個別バッチファイルの作成"""
        model_name = file_info['name']
        context_length = file_info['context_length']
        
        # バッチファイル名
        bat_filename = f"Run-{model_name}-C{context_length//1000}K-L0.bat"
        bat_path = self.kobold_dir / bat_filename
        
        # バッチファイル内容
        bat_content = f"""@echo off
chcp 65001 > NUL
cd /d "%~dp0"

echo 🎯 EasyNovelAssistant KoboldCpp サーバー起動
echo モデル: {model_name}
echo 量子化: {file_info['quantization']}
echo コンテキスト: {context_length:,} トークン
echo サイズ: {file_info['size_display']}
echo ====================================

REM KoboldCppサーバー起動
koboldcpp.exe ^
    --model "{file_info['filename']}" ^
    --contextsize {context_length} ^
    --threads 8 ^
    --usecublas ^
    --gpulayers 0 ^
    --port 5001 ^
    --host 127.0.0.1

if %errorlevel% neq 0 (
    echo.
    echo ❌ KoboldCppサーバーの起動に失敗しました
    echo GPU関連のエラーの場合は、--usecublasを削除してください
    pause
)
"""
        
        try:
            with open(bat_path, 'w', encoding='shift_jis') as f:
                f.write(bat_content)
            print(f"📜 {bat_filename} を作成")
        except Exception as e:
            print(f"❌ バッチファイル作成エラー ({bat_filename}): {e}")
    
    def add_gguf_file(self, source_path: str, description: str = "", context_length: int = 0) -> bool:
        """新しいGGUFファイルの追加"""
        source_file = Path(source_path)
        
        if not source_file.exists():
            print(f"❌ ファイルが見つかりません: {source_path}")
            return False
        
        if not source_file.suffix.lower() == '.gguf':
            print(f"❌ GGUFファイルではありません: {source_path}")
            return False
        
        # コピー先
        dest_file = self.kobold_dir / source_file.name
        
        try:
            # ディレクトリ作成
            self.kobold_dir.mkdir(exist_ok=True)
            
            # ファイルコピー
            shutil.copy2(source_file, dest_file)
            print(f"📁 {source_file.name} をコピーしました")
            
            # 設定保存
            model_name = source_file.stem
            if description or context_length:
                self.model_configs[model_name] = {
                    'description': description or self.guess_model_description(model_name),
                    'context_length': context_length or self.guess_context_length(model_name),
                    'added_date': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.save_model_configs()
            
            # 再スキャン
            self.scan_gguf_files()
            
            return True
            
        except Exception as e:
            print(f"❌ ファイル追加エラー: {e}")
            return False
    
    def remove_gguf_file(self, model_name: str) -> bool:
        """GGUFファイルの削除"""
        # ファイル検索
        target_file = None
        for file_info in self.gguf_files:
            if file_info['name'] == model_name:
                target_file = Path(file_info['path'])
                break
        
        if not target_file:
            print(f"❌ モデルが見つかりません: {model_name}")
            return False
        
        try:
            # ファイル削除
            target_file.unlink()
            print(f"🗑️ {target_file.name} を削除しました")
            
            # 対応するバッチファイルも削除
            for bat_file in self.kobold_dir.glob(f"Run-{model_name}-*.bat"):
                bat_file.unlink()
                print(f"🗑️ {bat_file.name} を削除しました")
            
            # 設定からも削除
            if model_name in self.model_configs:
                del self.model_configs[model_name]
                self.save_model_configs()
            
            # 再スキャン
            self.scan_gguf_files()
            
            return True
            
        except Exception as e:
            print(f"❌ ファイル削除エラー: {e}")
            return False
    
    def list_models(self) -> List[Dict]:
        """モデル一覧の取得"""
        return self.gguf_files
    
    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """特定モデルの詳細情報"""
        for file_info in self.gguf_files:
            if file_info['name'] == model_name:
                return file_info
        return None
    
    def create_model_selection_gui(self):
        """モデル選択GUI"""
        if not self.gguf_files:
            messagebox.showinfo("モデルなし", "GGUFファイルが見つかりません")
            return None
        
        selection_window = tk.Toplevel()
        selection_window.title("🎯 GGUFモデル選択")
        selection_window.geometry("800x600")
        
        # フレーム作成
        main_frame = ttk.Frame(selection_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # タイトル
        title_label = ttk.Label(main_frame, text="📁 利用可能なGGUFモデル", 
                              font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # モデルリスト
        columns = ('name', 'size', 'quantization', 'context', 'description')
        tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=15)
        
        # カラム設定
        tree.heading('name', text='モデル名')
        tree.heading('size', text='サイズ')
        tree.heading('quantization', text='量子化')
        tree.heading('context', text='コンテキスト')
        tree.heading('description', text='説明')
        
        tree.column('name', width=200)
        tree.column('size', width=80)
        tree.column('quantization', width=80)
        tree.column('context', width=80)
        tree.column('description', width=300)
        
        # データ挿入
        for file_info in self.gguf_files:
            tree.insert('', tk.END, values=(
                file_info['name'],
                file_info['size_display'],
                file_info['quantization'],
                f"{file_info['context_length']:,}",
                file_info['description']
            ))
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ボタンフレーム
        button_frame = ttk.Frame(selection_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def on_select():
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                model_name = item['values'][0]
                selection_window.destroy()
                return model_name
            else:
                messagebox.showwarning("選択なし", "モデルを選択してください")
        
        ttk.Button(button_frame, text="選択", command=on_select).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="キャンセル", command=selection_window.destroy).pack(side=tk.LEFT)
        
        return selection_window


def main():
    """テスト実行"""
    print("🎯 GGUF ファイル管理システム テスト")
    print("=" * 40)
    
    manager = GGUFManager()
    
    print(f"\n📁 検出されたモデル ({len(manager.gguf_files)}個):")
    for file_info in manager.gguf_files:
        print(f"  {file_info['name']}")
        print(f"    サイズ: {file_info['size_display']}")
        print(f"    量子化: {file_info['quantization']}")
        print(f"    コンテキスト: {file_info['context_length']:,} トークン")
        print(f"    説明: {file_info['description']}")
        print()


if __name__ == "__main__":
    main() 