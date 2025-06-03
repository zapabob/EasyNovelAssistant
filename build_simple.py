# -*- coding: utf-8 -*-
"""
EasyNovelAssistant シンプルEXEビルドスクリプト
KoboldCpp + GGUF統合対応版（コマンドライン版）
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

def check_dependencies():
    """依存関係確認"""
    log("📋 依存関係確認中...")
    
    # PyInstallerの確認
    try:
        import PyInstaller
        log(f"✅ PyInstaller {PyInstaller.__version__} 検出")
    except ImportError:
        log("❌ PyInstallerがインストールされていません")
        log("   以下のコマンドでインストールしてください:")
        log("   py -3 -m pip install pyinstaller")
        return False
    
    # メインファイルの確認
    if not Path('easy_novel_assistant.py').exists():
        log("❌ easy_novel_assistant.py が見つかりません")
        return False
    
    log("✅ 依存関係確認完了")
    return True

def clean_build_cache():
    """ビルドキャッシュ削除"""
    log("🧹 ビルドキャッシュ削除中...")
    
    # buildディレクトリ
    if Path('build').exists():
        shutil.rmtree('build')
        log("🗑️ build ディレクトリを削除")
    
    # distディレクトリ
    if Path('dist').exists():
        shutil.rmtree('dist')
        log("🗑️ dist ディレクトリを削除")
    
    # __pycache__ディレクトリ
    for pycache_dir in Path('.').rglob('__pycache__'):
        try:
            shutil.rmtree(pycache_dir)
        except:
            pass
    
    log("✅ ビルドキャッシュ削除完了")

def scan_gguf_files():
    """GGUFファイルスキャン"""
    log("📁 GGUFファイルスキャン中...")
    
    kobold_dir = Path('KoboldCpp')
    if not kobold_dir.exists():
        log("⚠️ KoboldCppディレクトリが見つかりません")
        return []
    
    gguf_files = list(kobold_dir.glob('*.gguf'))
    
    for gguf_file in gguf_files:
        size_mb = gguf_file.stat().st_size / (1024 * 1024)
        log(f"📄 {gguf_file.name} ({size_mb:.1f} MB)")
    
    log(f"✅ {len(gguf_files)}個のGGUFファイルを検出")
    return gguf_files

def create_simple_spec():
    """シンプルなspec ファイルを作成"""
    log("📝 PyInstaller設定ファイル作成中...")
    
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# プロジェクトルート
project_root = Path('.').absolute()

# データファイル設定
datas = []

# 設定ファイル
for config_file in ['config.json', 'llm.json', 'llm_sequence.json']:
    if os.path.exists(config_file):
        datas.append((config_file, '.'))

# KoboldCpp関連
kobold_dir = project_root / 'KoboldCpp'
if kobold_dir.exists():
    # KoboldCpp実行ファイル
    koboldcpp_exe = kobold_dir / 'koboldcpp.exe'
    if koboldcpp_exe.exists():
        datas.append((str(koboldcpp_exe), 'KoboldCpp'))
    
    # GGUFファイル（小さいもののみ - サイズ制限）
    for gguf_file in kobold_dir.glob('*.gguf'):
        file_size_mb = gguf_file.stat().st_size / (1024 * 1024)
        if file_size_mb < 1000:  # 1GB未満のみ含める
            datas.append((str(gguf_file), 'KoboldCpp'))
    
    # バッチファイル
    for bat_file in kobold_dir.glob('*.bat'):
        datas.append((str(bat_file), 'KoboldCpp'))

# テンプレートディレクトリ
for dir_name in ['config', 'data', 'templates']:
    dir_path = project_root / dir_name
    if dir_path.exists():
        for file_path in dir_path.rglob('*'):
            if file_path.is_file():
                rel_path = file_path.relative_to(project_root)
                datas.append((str(file_path), str(rel_path.parent)))

# 隠れたインポート
hiddenimports = [
    'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
    'PIL', 'PIL.Image', 'PIL.ImageTk',
    'numpy', 'pandas', 'tqdm', 'requests',
    'fugashi', 'unidic_lite', 'mecab',
    'torch', 'transformers',
    'librosa', 'soundfile',
    'psutil', 'gc', 'threading', 'asyncio',
    'const', 'context', 'form', 'generator', 'kobold_cpp', 'movie_maker', 'path', 'style_bert_vits2',
]

# PyInstaller設定
a = Analysis(
    ['easy_novel_assistant.py'],
    pathex=['.', 'src', 'EasyNovelAssistant/src'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'black', 'flake8', 'mypy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='EasyNovelAssistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
    
    with open('build_simple.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    log("✅ PyInstaller設定ファイル作成完了")

def run_pyinstaller():
    """PyInstaller実行"""
    log("🔨 PyInstaller実行中...")
    log("   この処理には数分かかる場合があります...")
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        'build_simple.spec'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='.')
        
        if result.returncode != 0:
            log(f"❌ PyInstaller エラー:")
            log(result.stderr)
            return False
        else:
            log("✅ PyInstaller実行完了")
            return True
            
    except Exception as e:
        log(f"❌ PyInstaller実行エラー: {e}")
        return False

def copy_additional_files():
    """追加ファイルのコピー"""
    log("📁 追加ファイル配置中...")
    
    dist_dir = Path('dist/EasyNovelAssistant')
    if not dist_dir.exists():
        log("❌ ビルド出力ディレクトリが見つかりません")
        return False
    
    # READMEファイル
    if Path('README.md').exists():
        shutil.copy2('README.md', dist_dir)
        log("📄 README.md をコピー")
    
    # ライセンスファイル
    if Path('LICENSE.txt').exists():
        shutil.copy2('LICENSE.txt', dist_dir)
        log("📄 LICENSE.txt をコピー")
    
    # 使用方法ファイルを作成
    usage_content = """# EasyNovelAssistant v3.0 使用方法

## 起動方法
1. EasyNovelAssistant.exe をダブルクリックして起動

## GGUFファイルの追加
1. KoboldCppフォルダに新しいGGUFファイルをコピー
2. アプリケーションを再起動

## サポート
- GitHub: https://github.com/EasyNovelAssistant/EasyNovelAssistant
- 問題報告: Issues タブからお知らせください

## バージョン情報
- Version: 3.0.0
- Build: KoboldCpp + GGUF統合対応版
- 32K context対応
- 高度反復抑制システム v3 (90%成功率)
- NKAT理論統合システム
"""
    
    usage_file = dist_dir / 'USAGE.txt'
    with open(usage_file, 'w', encoding='utf-8') as f:
        f.write(usage_content)
    log("📄 USAGE.txt を作成")
    
    log("✅ 追加ファイル配置完了")
    return True

def create_launch_scripts():
    """起動スクリプト作成"""
    log("📜 起動スクリプト作成中...")
    
    dist_dir = Path('dist/EasyNovelAssistant')
    
    # Windows用起動スクリプト
    bat_content = """@echo off
chcp 65001 > NUL
cd /d "%~dp0"

echo 🎯 EasyNovelAssistant v3.0 起動中...
echo    KoboldCpp + GGUF統合対応版
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
    
    log("✅ 起動スクリプト作成完了")

def main():
    """メイン関数"""
    print("🔨 EasyNovelAssistant シンプルEXEビルダー")
    print("   KoboldCpp + GGUF統合対応版")
    print("=" * 50)
    
    start_time = time.time()
    
    # ステップ1: 依存関係確認
    if not check_dependencies():
        return 1
    
    # ステップ2: GGUFファイルスキャン
    scan_gguf_files()
    
    # ステップ3: ビルドキャッシュクリア
    clean_build_cache()
    
    # ステップ4: 設定ファイル作成
    create_simple_spec()
    
    # ステップ5: PyInstaller実行
    if not run_pyinstaller():
        return 1
    
    # ステップ6: 追加ファイル配置
    if not copy_additional_files():
        return 1
    
    # ステップ7: 起動スクリプト作成
    create_launch_scripts()
    
    # 完了
    build_time = time.time() - start_time
    log(f"🎉 EXE ビルド完了！ (所要時間: {build_time:.1f}秒)")
    log("📁 出力先: dist/EasyNovelAssistant/")
    log("🚀 Launch_EasyNovelAssistant.bat で起動できます")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    
    if exit_code == 0:
        input("\n✅ ビルド完了。Enterキーで終了...")
    else:
        input("\n❌ ビルド失敗。Enterキーで終了...")
    
    sys.exit(exit_code) 