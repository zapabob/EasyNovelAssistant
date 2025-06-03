#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EasyNovelAssistant クイックEXEビルドスクリプト
設定ファイル付き軽量版
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import json
import time

def log(message):
    """ログメッセージ出力"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def quick_build():
    """クイックビルド実行"""
    log("🚀 EasyNovelAssistant クイックビルド開始")
    log("   設定ファイル付き軽量版")
    print("=" * 50)
    
    start_time = time.time()
    
    # ビルドディレクトリクリア
    if Path('build').exists():
        shutil.rmtree('build')
        log("🗑️ build ディレクトリを削除")
    
    if Path('dist').exists():
        shutil.rmtree('dist')
        log("🗑️ dist ディレクトリを削除")
    
    # PyInstallerで設定ファイルを含むビルド
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--console',
        '--name', 'EasyNovelAssistant',
        '--add-data', 'config.json;.',
        '--add-data', 'llm.json;.',
        '--add-data', 'llm_sequence.json;.',
        '--add-data', 'README.md;.',
        '--add-data', 'LICENSE.txt;.',
        '--hidden-import', 'tkinter',
        '--hidden-import', 'tkinter.ttk',
        '--hidden-import', 'tkinter.filedialog',
        '--hidden-import', 'tkinter.messagebox',
        '--hidden-import', 'PIL',
        '--hidden-import', 'PIL.Image',
        '--hidden-import', 'PIL.ImageTk',
        '--hidden-import', 'requests',
        '--hidden-import', 'tqdm',
        '--hidden-import', 'psutil',
        '--exclude-module', 'pytest',
        '--exclude-module', 'black',
        '--exclude-module', 'flake8',
        '--exclude-module', 'mypy',
        '--exclude-module', 'torch',
        '--exclude-module', 'transformers',
        'easy_novel_assistant.py'
    ]
    
    log("🔨 PyInstaller実行中...")
    log("   この処理には数分かかる場合があります...")
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True, cwd='.')
        
        if result.returncode != 0:
            log(f"❌ PyInstaller エラー")
            return False
        else:
            log("✅ PyInstaller実行完了")
            
    except Exception as e:
        log(f"❌ PyInstaller実行エラー: {e}")
        return False
    
    # EXEファイルの確認
    exe_file = Path('dist/EasyNovelAssistant.exe')
    if exe_file.exists():
        size_mb = exe_file.stat().st_size / (1024 * 1024)
        log(f"✅ EXEファイル作成完了: {size_mb:.1f} MB")
        
        # 起動スクリプト作成
        create_launch_script()
        
        # 完了
        build_time = time.time() - start_time
        log(f"🎉 クイックビルド完了！ (所要時間: {build_time:.1f}秒)")
        log("📁 出力先: dist/EasyNovelAssistant.exe")
        
        return True
    else:
        log("❌ EXEファイルが作成されませんでした")
        return False

def create_launch_script():
    """起動スクリプト作成"""
    log("📜 起動スクリプト作成中...")
    
    dist_dir = Path('dist')
    
    # Windows用起動スクリプト
    bat_content = """@echo off
chcp 65001 > NUL
cd /d "%~dp0"

echo 🎯 EasyNovelAssistant v3.0 起動中...
echo    設定ファイル付き軽量版
echo ====================================

EasyNovelAssistant.exe

if %errorlevel% neq 0 (
    echo.
    echo ❌ エラーが発生しました
    echo 詳細はコンソール出力を確認してください
    pause
)
"""
    
    bat_file = dist_dir / 'Launch_EasyNovelAssistant.bat'
    with open(bat_file, 'w', encoding='shift_jis') as f:
        f.write(bat_content)
    log("📜 Launch_EasyNovelAssistant.bat を作成")
    
    # 使用方法ファイル作成
    readme_content = """# EasyNovelAssistant v3.0 - 設定ファイル付き軽量版

## 🚀 起動方法
1. Launch_EasyNovelAssistant.bat をダブルクリック
   または
2. EasyNovelAssistant.exe を直接起動

## 📁 必要ファイル
この軽量版には以下の設定ファイルが含まれています：
- config.json (基本設定)
- llm.json (LLM設定)
- llm_sequence.json (シーケンス設定)

## 🔧 KoboldCppの設定
KoboldCppとGGUFファイルを使用する場合：
1. KoboldCpp/ フォルダを作成
2. koboldcpp.exe と GGUFファイルを配置
3. アプリケーションから接続設定

## 📋 バージョン情報
- Version: 3.0.0
- Type: Quick Build (設定ファイル付き軽量版)
- Size: 約11MB (大容量ファイル除外)

## 🆘 サポート
問題が発生した場合：
1. コンソール出力を確認
2. GitHubのIssuesで報告
"""
    
    readme_file = dist_dir / 'README_QUICK.txt'
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    log("📄 README_QUICK.txt を作成")

def main():
    """メイン関数"""
    if quick_build():
        input("\n✅ クイックビルド完了。Enterキーで終了...")
        return 0
    else:
        input("\n❌ クイックビルド失敗。Enterキーで終了...")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 