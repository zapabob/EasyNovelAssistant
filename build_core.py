# -*- coding: utf-8 -*-
"""
EasyNovelAssistant コア機能EXEビルドスクリプト
基本メニュー含む最小限の動作版
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

def create_core_spec():
    """コア機能spec ファイルを作成"""
    log("📝 コア機能PyInstaller設定ファイル作成中...")
    
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

import sys
sys.setrecursionlimit(sys.getrecursionlimit() * 5)

import os
from pathlib import Path

# プロジェクトルート
project_root = Path('.').absolute()

# データファイル設定
datas = []

# 設定ファイル
config_files = ['config.json', 'llm.json', 'llm_sequence.json']
for config_file in config_files:
    if os.path.exists(config_file):
        datas.append((config_file, '.'))

# menuディレクトリをデータとして追加
if os.path.exists('menu'):
    datas.append(('menu', 'menu'))

# コア機能の隠れたインポート
hiddenimports = [
    # GUI関連（必須）
    'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
    'tkinterdnd2',
    
    # 基本データ処理
    'requests', 'json', 'threading', 'subprocess',
    
    # プロジェクト固有モジュール（コア）
    'const', 'context', 'form', 'generator', 'kobold_cpp', 'path',
    'input_area', 'output_area', 'gen_area',
    
    # メニューシステム
    'menu.file_menu', 'menu.gen_menu', 'menu.help_menu', 
    'menu.model_menu', 'menu.sample_menu', 'menu.setting_menu', 
    'menu.speech_menu', 'menu.tool_menu',
]

# PyInstaller設定（コア機能）
a = Analysis(
    ['easy_novel_assistant.py'],
    pathex=['.', 'menu'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 重いライブラリを除外
        'torch', 'transformers', 'librosa', 'soundfile',
        'matplotlib', 'seaborn', 'plotly',
        'scipy', 'sklearn', 'pandas',
        'PIL', 'PIL.Image', 'PIL.ImageTk',
        'numpy', 'tqdm',
        # Style-Bert-VITS2関連
        'style_bert_vits2',
        # テスト関連
        'pytest', 'black', 'flake8', 'mypy',
        # 開発ツール
        'IPython', 'jupyter', 'notebook',
        # 統合システム関連（問題のあるモジュール）
        'integration_control_panel', 'job_queue', 'gguf_manager', 'gguf_addon_system',
        # 映画作成
        'movie_maker',
        # src配下の重いモジュール
        'src',
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
    name='EasyNovelAssistant_Core',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPXを無効化
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True, # デバッグのためコンソール表示
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
    
    with open('build_core.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    log("✅ コア機能PyInstaller設定ファイル作成完了")

def patch_form_imports():
    """form.pyの統合システム関連インポートをコメントアウト"""
    log("🔧 form.py パッチ適用中...")
    
    with open('form.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # バックアップ作成
    with open('form.py.backup', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # パッチ適用（統合システム関連をコメントアウト）
    lines = content.split('\n')
    patched_lines = []
    skip_integration_block = False
    
    for line in lines:
        if 'from integration_control_panel import' in line:
            patched_lines.append(f"# PATCHED: {line}")
            skip_integration_block = True
        elif skip_integration_block and ('INTEGRATION_PANEL_AVAILABLE' in line or 'print("⚠️ 統合システム制御パネル読み込み失敗")' in line):
            patched_lines.append(f"# PATCHED: {line}")
            if 'print("⚠️ 統合システム制御パネル読み込み失敗")' in line:
                skip_integration_block = False
        elif 'INTEGRATION_PANEL_AVAILABLE' in line and 'if' in line:
            # 統合システム関連のif文をすべてFalseにする
            patched_lines.append("        # PATCHED: 統合システム関連機能は無効")
            patched_lines.append("        pass  # 統合システム無効版")
        elif 'self.integration_panel' in line or 'integration_panel' in line:
            patched_lines.append(f"# PATCHED: {line}")
        else:
            patched_lines.append(line)
    
    # パッチされたファイルを保存
    with open('form.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(patched_lines))
    
    log("✅ form.py パッチ適用完了")

def restore_form():
    """form.pyを元に戻す"""
    log("🔄 form.py 復元中...")
    
    if Path('form.py.backup').exists():
        shutil.copy2('form.py.backup', 'form.py')
        os.remove('form.py.backup')
        log("✅ form.py 復元完了")

def run_core_build():
    """コア機能PyInstaller実行"""
    log("🔨 コア機能PyInstaller実行中...")
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        'build_core.spec'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True, cwd='.')
        
        if result.returncode != 0:
            log(f"❌ PyInstaller エラー")
            return False
        else:
            log("✅ PyInstaller実行完了")
            return True
            
    except Exception as e:
        log(f"❌ PyInstaller実行エラー: {e}")
        return False

def main():
    """メイン関数"""
    print("🚀 EasyNovelAssistant コア機能EXEビルダー")
    print("   基本メニュー含む最小限の動作版")
    print("=" * 50)
    
    start_time = time.time()
    
    # ビルドキャッシュクリア
    if Path('build').exists():
        shutil.rmtree('build')
        log("🗑️ build ディレクトリを削除")
    
    if Path('dist').exists():
        shutil.rmtree('dist')
        log("🗑️ dist ディレクトリを削除")
    
    try:
        # form.pyにパッチ適用
        patch_form_imports()
        
        # コア機能設定ファイル作成
        create_core_spec()
        
        # PyInstaller実行
        if not run_core_build():
            return 1
        
        # 完了
        build_time = time.time() - start_time
        log(f"🎉 コア機能EXE ビルド完了！ (所要時間: {build_time:.1f}秒)")
        log("📁 出力先: dist/EasyNovelAssistant_Core.exe")
        
        return 0
    
    finally:
        # 必ず元に戻す
        restore_form()

if __name__ == "__main__":
    exit_code = main()
    
    if exit_code == 0:
        print("\n✅ コア機能ビルド完了")
        print("📋 機能:")
        print("  - 基本的なGUI操作")
        print("  - KoboldCppとの連携")
        print("  - テキスト生成")
        print("  - ファイル操作")
        print("  - 統合システムは無効")
        input("\nEnterキーで終了...")
    else:
        input("\n❌ コア機能ビルド失敗。Enterキーで終了...")
    
    sys.exit(exit_code) 