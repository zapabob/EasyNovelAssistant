# -*- coding: utf-8 -*-
"""
EasyNovelAssistant テスト用軽量EXEビルダー
GGUFファイルを除外した高速ビルド
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import time

def log(message):
    """ログメッセージ出力"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def clean_test_build():
    """テストビルドキャッシュ削除"""
    log("🧹 テストビルドキャッシュ削除中...")
    
    test_dirs = ['build_test', 'dist_test']
    for dir_name in test_dirs:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            log(f"🗑️ {dir_name} ディレクトリを削除")
    
    log("✅ テストビルドキャッシュ削除完了")

def create_test_spec():
    """軽量テスト用specファイル作成"""
    log("📝 テスト用PyInstaller設定ファイル作成中...")
    
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# プロジェクトルート
project_root = Path('.').absolute()

# データファイル設定（軽量版）
datas = []

# 設定ファイル（小さいもののみ）
for config_file in ['config.json', 'llm.json', 'llm_sequence.json']:
    if os.path.exists(config_file):
        datas.append((config_file, '.'))

# KoboldCpp関連（実行ファイルとバッチファイルのみ、GGUFは除外）
kobold_dir = project_root / 'KoboldCpp'
if kobold_dir.exists():
    # KoboldCpp実行ファイル
    koboldcpp_exe = kobold_dir / 'koboldcpp.exe'
    if koboldcpp_exe.exists():
        datas.append((str(koboldcpp_exe), 'KoboldCpp'))
    
    # バッチファイル（最初の3つのみ）
    bat_files = list(kobold_dir.glob('*.bat'))[:3]
    for bat_file in bat_files:
        datas.append((str(bat_file), 'KoboldCpp'))

# 必要最小限のテンプレート
template_files = []
config_dir = project_root / 'config'
if config_dir.exists():
    for file_path in config_dir.rglob('*.json'):
        if file_path.stat().st_size < 1024 * 100:  # 100KB未満のみ
            rel_path = file_path.relative_to(project_root)
            datas.append((str(file_path), str(rel_path.parent)))

# 隠れたインポート（最小限）
hiddenimports = [
    'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
    'numpy', 'pandas', 'tqdm', 'requests',
    'const', 'context', 'form', 'generator', 'kobold_cpp', 'path',
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
    excludes=[
        'pytest', 'black', 'flake8', 'mypy',
        'torch', 'transformers',  # 重いライブラリを除外
        'librosa', 'soundfile',   # 音声処理を除外
        'PIL', 'matplotlib',      # 画像処理を除外
    ],
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
    name='EasyNovelAssistant_Test',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # 高速化のためUPX無効
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
    
    with open('build_test.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    log("✅ テスト用PyInstaller設定ファイル作成完了")

def run_test_build():
    """テスト用PyInstaller実行"""
    log("🔨 テスト用PyInstaller実行中...")
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        '--distpath', 'dist_test',
        '--workpath', 'build_test',
        'build_test.spec'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='.')
        
        if result.returncode != 0:
            log(f"❌ PyInstaller エラー:")
            print(result.stderr)
            return False
        else:
            log("✅ テスト用PyInstaller実行完了")
            return True
            
    except Exception as e:
        log(f"❌ PyInstaller実行エラー: {e}")
        return False

def create_test_launcher():
    """テスト用起動スクリプト作成"""
    log("📜 テスト用起動スクリプト作成中...")
    
    dist_dir = Path('dist_test')
    
    # テスト用起動スクリプト
    bat_content = """@echo off
chcp 65001 > NUL
cd /d "%~dp0"

echo 🎯 EasyNovelAssistant テスト版 起動中...
echo    軽量ビルド - 動作確認用
echo ====================================

EasyNovelAssistant_Test.exe

if %errorlevel% neq 0 (
    echo.
    echo ❌ エラーが発生しました
    pause
)
"""
    
    bat_file = dist_dir / 'Launch_Test.bat'
    try:
        with open(bat_file, 'w', encoding='utf-8') as f:
            f.write(bat_content)
        log("📜 Launch_Test.bat を作成")
    except Exception as e:
        log(f"❌ 起動スクリプト作成エラー: {e}")
    
    # README作成
    readme_content = """# EasyNovelAssistant テスト版

これは軽量テスト版です。以下の機能が制限されています：
- GGUFファイルは含まれていません（別途追加が必要）
- 音声合成機能は無効です
- 一部の高度な機能が制限されています

## 起動方法
Launch_Test.bat をダブルクリック

## 本格版の作成
軽量版での動作確認後、本格版をビルドしてください
"""
    
    readme_file = dist_dir / 'README_TEST.txt'
    try:
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        log("📄 README_TEST.txt を作成")
    except Exception as e:
        log(f"❌ README作成エラー: {e}")

def main():
    """メイン関数"""
    print("🔨 EasyNovelAssistant テスト用軽量EXEビルダー")
    print("   軽量版 - 動作確認用")
    print("=" * 50)
    
    start_time = time.time()
    
    # 依存関係確認
    try:
        import PyInstaller
        log(f"✅ PyInstaller {PyInstaller.__version__} 検出")
    except ImportError:
        log("❌ PyInstallerがインストールされていません")
        return 1
    
    # メインファイル確認
    if not Path('easy_novel_assistant.py').exists():
        log("❌ easy_novel_assistant.py が見つかりません")
        return 1
    
    # ステップ1: テストビルドキャッシュクリア
    clean_test_build()
    
    # ステップ2: テスト設定ファイル作成
    create_test_spec()
    
    # ステップ3: テスト用PyInstaller実行
    if not run_test_build():
        return 1
    
    # ステップ4: テスト用起動スクリプト作成
    create_test_launcher()
    
    # 完了
    build_time = time.time() - start_time
    log(f"🎉 テスト用EXE ビルド完了！ (所要時間: {build_time:.1f}秒)")
    log("📁 出力先: dist_test/")
    log("🚀 Launch_Test.bat で起動テストができます")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    
    if exit_code == 0:
        print("\n✅ テストビルド完了。")
        print("📝 動作確認後、本格版をビルドしてください")
    else:
        print("\n❌ テストビルド失敗。")
    
    input("Enterキーで終了...")
    sys.exit(exit_code) 