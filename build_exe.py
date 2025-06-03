# -*- coding: utf-8 -*-
"""
EasyNovelAssistant EXE ビルドスクリプト
KoboldCpp + GGUF統合対応版

機能:
1. PyInstallerでEXE作成
2. GGUFファイル管理
3. 一括パッケージング
4. デプロイメント準備
"""

import os
import sys
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import json
from typing import List, Dict, Optional
import threading
import time

class EXEBuilder:
    """EXE ビルダー"""
    
    def __init__(self):
        self.project_root = Path('.').absolute()
        self.kobold_dir = self.project_root / 'KoboldCpp'
        self.dist_dir = self.project_root / 'dist'
        self.build_dir = self.project_root / 'build'
        
        # ビルド設定
        self.build_config = {
            'include_gguf_files': True,
            'include_style_bert': True,
            'create_installer': True,
            'compress_exe': True,
            'debug_mode': False,
            'selected_gguf_files': []
        }
        
        self.setup_gui()
    
    def setup_gui(self):
        """GUI設定"""
        self.root = tk.Tk()
        self.root.title("EasyNovelAssistant EXE ビルダー v3.0")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # スタイル設定
        style = ttk.Style()
        style.theme_use('clam')
        
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # タイトル
        title_label = ttk.Label(main_frame, text="🎯 EasyNovelAssistant EXE ビルダー", 
                              font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 設定フレーム
        self.setup_config_frame(main_frame)
        
        # GGUFファイル管理フレーム
        self.setup_gguf_frame(main_frame)
        
        # ビルドフレーム
        self.setup_build_frame(main_frame)
        
        # ログフレーム
        self.setup_log_frame(main_frame)
        
        # ウィンドウのサイズ調整
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
    
    def setup_config_frame(self, parent):
        """設定フレーム"""
        config_frame = ttk.LabelFrame(parent, text="📋 ビルド設定", padding="10")
        config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # チェックボックス
        self.include_gguf_var = tk.BooleanVar(value=self.build_config['include_gguf_files'])
        self.include_style_bert_var = tk.BooleanVar(value=self.build_config['include_style_bert'])
        self.create_installer_var = tk.BooleanVar(value=self.build_config['create_installer'])
        self.compress_exe_var = tk.BooleanVar(value=self.build_config['compress_exe'])
        self.debug_mode_var = tk.BooleanVar(value=self.build_config['debug_mode'])
        
        ttk.Checkbutton(config_frame, text="GGUFファイルを含める", 
                       variable=self.include_gguf_var).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(config_frame, text="Style-Bert-VITS2を含める", 
                       variable=self.include_style_bert_var).grid(row=0, column=1, sticky=tk.W)
        ttk.Checkbutton(config_frame, text="インストーラーを作成", 
                       variable=self.create_installer_var).grid(row=1, column=0, sticky=tk.W)
        ttk.Checkbutton(config_frame, text="EXE圧縮を有効化", 
                       variable=self.compress_exe_var).grid(row=1, column=1, sticky=tk.W)
        ttk.Checkbutton(config_frame, text="デバッグモード", 
                       variable=self.debug_mode_var).grid(row=2, column=0, sticky=tk.W)
    
    def setup_gguf_frame(self, parent):
        """GGUFファイル管理フレーム"""
        gguf_frame = ttk.LabelFrame(parent, text="📁 GGUFファイル管理", padding="10")
        gguf_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # ボタンフレーム
        button_frame = ttk.Frame(gguf_frame)
        button_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(button_frame, text="GGUFファイルを追加", 
                  command=self.add_gguf_files).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="選択したファイルを削除", 
                  command=self.remove_gguf_files).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(button_frame, text="KoboldCppディレクトリをスキャン", 
                  command=self.scan_kobold_directory).grid(row=0, column=2, padx=(0, 5))
        
        # ファイルリスト
        list_frame = ttk.Frame(gguf_frame)
        list_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Treeview
        self.gguf_tree = ttk.Treeview(list_frame, columns=('Size', 'Path'), show='tree headings')
        self.gguf_tree.heading('#0', text='ファイル名')
        self.gguf_tree.heading('Size', text='サイズ')
        self.gguf_tree.heading('Path', text='パス')
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.gguf_tree.yview)
        self.gguf_tree.configure(yscrollcommand=scrollbar.set)
        
        self.gguf_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        gguf_frame.columnconfigure(0, weight=1)
        gguf_frame.rowconfigure(1, weight=1)
        

        # 初期スキャン（ログ設定後に実行）
        self.root.after(100, self.scan_kobold_directory)
    
    def setup_build_frame(self, parent):
        """ビルドフレーム"""
        build_frame = ttk.LabelFrame(parent, text="🔨 ビルド実行", padding="10")
        build_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # プログレスバー
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(build_frame, variable=self.progress_var, 
                                          maximum=100, length=400)
        self.progress_bar.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # ステータスラベル
        self.status_var = tk.StringVar(value="準備完了")
        status_label = ttk.Label(build_frame, textvariable=self.status_var)
        status_label.grid(row=1, column=0, columnspan=3, pady=(0, 10))
        
        # ボタン
        ttk.Button(build_frame, text="🔨 EXE ビルド開始", 
                  command=self.start_build, style='Accent.TButton').grid(row=2, column=0, padx=(0, 5))
        ttk.Button(build_frame, text="📁 出力フォルダを開く", 
                  command=self.open_output_folder).grid(row=2, column=1, padx=(0, 5))
        ttk.Button(build_frame, text="🧹 ビルドキャッシュ削除", 
                  command=self.clean_build_cache).grid(row=2, column=2)
        
        build_frame.columnconfigure(0, weight=1)
        build_frame.columnconfigure(1, weight=1)
        build_frame.columnconfigure(2, weight=1)
    
    def setup_log_frame(self, parent):
        """ログフレーム"""
        log_frame = ttk.LabelFrame(parent, text="📜 ビルドログ", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # テキストエリア
        text_frame = ttk.Frame(log_frame)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = tk.Text(text_frame, wrap=tk.WORD, height=15)
        log_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
    
    def log(self, message: str):
        """ログメッセージを追加"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.root.update()
    
    def scan_kobold_directory(self):
        """KoboldCppディレクトリをスキャン"""
        self.log("KoboldCppディレクトリをスキャン中...")
        
        # 既存のアイテムをクリア
        for item in self.gguf_tree.get_children():
            self.gguf_tree.delete(item)
        
        if not self.kobold_dir.exists():
            self.log("❌ KoboldCppディレクトリが見つかりません")
            return
        
        # GGUFファイルを検索
        gguf_files = list(self.kobold_dir.glob('*.gguf'))
        
        for gguf_file in gguf_files:
            size_mb = gguf_file.stat().st_size / (1024 * 1024)
            size_str = f"{size_mb:.1f} MB"
            
            self.gguf_tree.insert('', tk.END, text=gguf_file.name, 
                                values=(size_str, str(gguf_file)))
        
        self.log(f"✅ {len(gguf_files)}個のGGUFファイルを検出")
    
    def add_gguf_files(self):
        """GGUFファイルを追加"""
        files = filedialog.askopenfilenames(
            title="GGUFファイルを選択",
            filetypes=[("GGUF files", "*.gguf"), ("All files", "*.*")]
        )
        
        if not files:
            return
        
        copied_count = 0
        for file_path in files:
            src_path = Path(file_path)
            dst_path = self.kobold_dir / src_path.name
            
            try:
                if dst_path.exists():
                    result = messagebox.askyesno(
                        "ファイル上書き確認",
                        f"{src_path.name} は既に存在します。上書きしますか？"
                    )
                    if not result:
                        continue
                
                shutil.copy2(src_path, dst_path)
                copied_count += 1
                self.log(f"📁 {src_path.name} をコピーしました")
                
            except Exception as e:
                self.log(f"❌ {src_path.name} のコピーに失敗: {e}")
        
        if copied_count > 0:
            self.scan_kobold_directory()
            self.log(f"✅ {copied_count}個のファイルを追加完了")
    
    def remove_gguf_files(self):
        """選択したGGUFファイルを削除"""
        selected_items = self.gguf_tree.selection()
        
        if not selected_items:
            messagebox.showinfo("選択エラー", "削除するファイルを選択してください")
            return
        
        result = messagebox.askyesno(
            "削除確認",
            f"{len(selected_items)}個のファイルを削除しますか？"
        )
        
        if not result:
            return
        
        deleted_count = 0
        for item in selected_items:
            file_path = Path(self.gguf_tree.item(item)['values'][1])
            try:
                file_path.unlink()
                deleted_count += 1
                self.log(f"🗑️ {file_path.name} を削除しました")
            except Exception as e:
                self.log(f"❌ {file_path.name} の削除に失敗: {e}")
        
        if deleted_count > 0:
            self.scan_kobold_directory()
            self.log(f"✅ {deleted_count}個のファイルを削除完了")
    
    def start_build(self):
        """ビルド開始"""
        # ビルド設定を更新
        self.build_config.update({
            'include_gguf_files': self.include_gguf_var.get(),
            'include_style_bert': self.include_style_bert_var.get(),
            'create_installer': self.create_installer_var.get(),
            'compress_exe': self.compress_exe_var.get(),
            'debug_mode': self.debug_mode_var.get(),
        })
        
        # バックグラウンドでビルド実行
        threading.Thread(target=self.build_exe, daemon=True).start()
    
    def build_exe(self):
        """EXE ビルド実行"""
        try:
            self.status_var.set("ビルド準備中...")
            self.progress_var.set(0)
            
            self.log("🔨 EXE ビルド開始")
            
            # ステップ1: 依存関係確認
            self.status_var.set("依存関係確認中...")
            self.progress_var.set(10)
            self.check_dependencies()
            
            # ステップ2: ビルドキャッシュクリア
            self.status_var.set("ビルドキャッシュクリア中...")
            self.progress_var.set(20)
            self.clean_build_cache()
            
            # ステップ3: PyInstaller実行
            self.status_var.set("PyInstaller実行中...")
            self.progress_var.set(30)
            self.run_pyinstaller()
            
            # ステップ4: 追加ファイル配置
            self.status_var.set("追加ファイル配置中...")
            self.progress_var.set(60)
            self.copy_additional_files()
            
            # ステップ5: インストーラー作成（オプション）
            if self.build_config['create_installer']:
                self.status_var.set("インストーラー作成中...")
                self.progress_var.set(80)
                self.create_installer()
            
            # ステップ6: 完了
            self.status_var.set("ビルド完了！")
            self.progress_var.set(100)
            self.log("🎉 EXE ビルド完了！")
            
            messagebox.showinfo("ビルド完了", "EXE ビルドが正常に完了しました！")
            
        except Exception as e:
            self.status_var.set(f"ビルドエラー: {e}")
            self.log(f"❌ ビルドエラー: {e}")
            messagebox.showerror("ビルドエラー", f"ビルド中にエラーが発生しました:\n{e}")
    
    def check_dependencies(self):
        """依存関係確認"""
        self.log("📋 依存関係確認中...")
        
        # PyInstallerの確認
        try:
            import PyInstaller
            self.log(f"✅ PyInstaller {PyInstaller.__version__} 検出")
        except ImportError:
            raise Exception("PyInstallerがインストールされていません")
        
        # メインファイルの確認
        main_file = self.project_root / 'easy_novel_assistant.py'
        if not main_file.exists():
            raise Exception("easy_novel_assistant.py が見つかりません")
        
        self.log("✅ 依存関係確認完了")
    
    def run_pyinstaller(self):
        """PyInstaller実行"""
        self.log("🔨 PyInstaller実行中...")
        
        spec_file = self.project_root / 'build_exe.spec'
        
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            str(spec_file)
        ]
        
        if self.build_config['debug_mode']:
            cmd.append('--debug=all')
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.project_root))
        
        if result.returncode != 0:
            self.log(f"❌ PyInstaller エラー: {result.stderr}")
            raise Exception(f"PyInstaller failed: {result.stderr}")
        
        self.log("✅ PyInstaller実行完了")
    
    def copy_additional_files(self):
        """追加ファイルのコピー"""
        self.log("📁 追加ファイル配置中...")
        
        # 出力ディレクトリ
        output_dir = self.dist_dir / 'EasyNovelAssistant'
        
        if not output_dir.exists():
            raise Exception("ビルド出力ディレクトリが見つかりません")
        
        # READMEファイル
        readme_file = self.project_root / 'README.md'
        if readme_file.exists():
            shutil.copy2(readme_file, output_dir)
            self.log("📄 README.md をコピー")
        
        # ライセンスファイル
        license_file = self.project_root / 'LICENSE.txt'
        if license_file.exists():
            shutil.copy2(license_file, output_dir)
            self.log("📄 LICENSE.txt をコピー")
        
        self.log("✅ 追加ファイル配置完了")
    
    def create_installer(self):
        """インストーラー作成"""
        self.log("📦 インストーラー作成中...")
        
        # NSIS用のスクリプトを作成（簡易版）
        installer_script = self.project_root / 'installer.nsi'
        
        nsi_content = f'''
!define APPNAME "EasyNovelAssistant"
!define VERSION "3.0.0"
!define PUBLISHER "EasyNovelAssistant Team"

OutFile "EasyNovelAssistant-v3.0.0-Installer.exe"
InstallDir "$PROGRAMFILES\\EasyNovelAssistant"

Page directory
Page instfiles

Section "install"
    SetOutPath $INSTDIR
    File /r "dist\\EasyNovelAssistant\\*"
    
    CreateDirectory "$SMPROGRAMS\\EasyNovelAssistant"
    CreateShortCut "$SMPROGRAMS\\EasyNovelAssistant\\EasyNovelAssistant.lnk" "$INSTDIR\\EasyNovelAssistant.exe"
    CreateShortCut "$DESKTOP\\EasyNovelAssistant.lnk" "$INSTDIR\\EasyNovelAssistant.exe"
    
    WriteUninstaller $INSTDIR\\uninstaller.exe
SectionEnd

Section "uninstall"
    Delete "$SMPROGRAMS\\EasyNovelAssistant\\EasyNovelAssistant.lnk"
    Delete "$DESKTOP\\EasyNovelAssistant.lnk"
    RMDir "$SMPROGRAMS\\EasyNovelAssistant"
    
    RMDir /r $INSTDIR
SectionEnd
'''
        
        with open(installer_script, 'w', encoding='utf-8') as f:
            f.write(nsi_content)
        
        self.log("📦 インストーラースクリプト作成完了")
    
    def clean_build_cache(self):
        """ビルドキャッシュ削除"""
        self.log("🧹 ビルドキャッシュ削除中...")
        
        # buildディレクトリ
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
            self.log("🗑️ build ディレクトリを削除")
        
        # distディレクトリ
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
            self.log("🗑️ dist ディレクトリを削除")
        
        # __pycache__ディレクトリ
        for pycache_dir in self.project_root.rglob('__pycache__'):
            shutil.rmtree(pycache_dir)
        
        self.log("✅ ビルドキャッシュ削除完了")
    
    def open_output_folder(self):
        """出力フォルダを開く"""
        if self.dist_dir.exists():
            os.startfile(str(self.dist_dir))
        else:
            messagebox.showinfo("フォルダなし", "出力フォルダがまだ作成されていません")
    
    def run(self):
        """GUI実行"""
        self.root.mainloop()


def main():
    """メイン関数"""
    print("🔨 EasyNovelAssistant EXE ビルダー v3.0")
    print("   KoboldCpp + GGUF統合対応版")
    print("=" * 50)
    
    builder = EXEBuilder()
    builder.run()


if __name__ == "__main__":
    main() 