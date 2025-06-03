@echo off
chcp 65001 > NUL
cd /d "%~dp0"

echo 🎯 EasyNovelAssistant v3.0 ポータブル版起動
echo    KoboldCpp + GGUF統合対応版
echo ====================================
echo.

REM プロジェクトディレクトリの確認
if not exist "easy_novel_assistant.py" (
    echo ❌ プロジェクトディレクトリが正しくありません
    echo    このバッチファイルはプロジェクトルートから実行してください
    pause
    exit /b 1
)

REM EXEファイルの存在確認と優先起動
if exist "dist\EasyNovelAssistant.exe" (
    echo 📁 EXE版を起動中... [dist\EasyNovelAssistant.exe]
    echo.
    echo 🚀 アプリケーション起動中...
    echo    初回起動時は時間がかかる場合があります
    echo.
    
    REM エラーハンドリング付きでEXE実行
    "dist\EasyNovelAssistant.exe"
    set exit_code=%errorlevel%
    
    if %exit_code% equ 0 (
        echo ✅ アプリケーションが正常に終了しました
    ) else (
        echo ❌ アプリケーション実行エラー (終了コード: %exit_code%)
        echo.
        echo 💡 トラブルシューティング:
        echo    1. Pythonスクリプト版で動作確認をしてください
        echo    2. KoboldCppディレクトリが正しく配置されているか確認
        echo    3. 必要なDLLファイルがインストールされているか確認
        echo       - Visual C++ 再頒布可能パッケージ
        echo       - CUDA ランタイム (GPU使用時)
        echo.
        pause
        exit /b %exit_code%
    )
    
) else if exist "EasyNovelAssistant.exe" (
    echo 📁 EXE版を起動中... [EasyNovelAssistant.exe]
    echo.
    echo 🚀 アプリケーション起動中...
    echo    初回起動時は時間がかかる場合があります
    echo.
    
    "EasyNovelAssistant.exe"
    set exit_code=%errorlevel%
    
    if %exit_code% equ 0 (
        echo ✅ アプリケーションが正常に終了しました
    ) else (
        echo ❌ アプリケーション実行エラー (終了コード: %exit_code%)
        echo.
        echo 💡 Pythonスクリプト版での動作確認を推奨します
        pause
        exit /b %exit_code%
    )
    
) else (
    echo 📁 Pythonスクリプト版を起動中...
    echo.
    
    REM Python環境の確認
    py -3 --version >NUL 2>&1
    if %errorlevel% neq 0 (
        echo ❌ Python 3が見つかりません
        echo    Python 3.8以上をインストールしてください
        echo    https://www.python.org/downloads/
        pause
        exit /b 1
    )
    
    echo 🐍 Python環境検出: 
    py -3 --version
    echo.
    
    REM 必要な依存関係の簡易チェック
    echo 📋 依存関係確認中...
    py -3 -c "import tkinter; print('✅ tkinter: OK')" 2>NUL || echo "⚠️ tkinter: 確認失敗"
    py -3 -c "import requests; print('✅ requests: OK')" 2>NUL || echo "⚠️ requests: インストール推奨"
    echo.
    
    if exist "easy_novel_assistant.py" (
        echo 🚀 EasyNovelAssistant起動中...
        echo.
        py -3 easy_novel_assistant.py
        set exit_code=%errorlevel%
        
        if %exit_code% equ 0 (
            echo ✅ アプリケーションが正常に終了しました
        ) else (
            echo ❌ Pythonスクリプト実行エラー (終了コード: %exit_code%)
            echo.
            echo 💡 トラブルシューティング:
            echo    1. 依存関係をインストール: pip install -r requirements.txt
            echo    2. 必要なディレクトリ構造を確認
            echo    3. Python環境が正しく設定されているか確認
            pause
            exit /b %exit_code%
        )
    ) else (
        echo ❌ 起動ファイルが見つかりません
        echo.
        echo    以下のファイルのいずれかが必要です：
        echo    📄 dist\EasyNovelAssistant.exe
        echo    📄 EasyNovelAssistant.exe  
        echo    📄 easy_novel_assistant.py
        echo.
        echo 💡 解決方法:
        echo    1. 正しいプロジェクトディレクトリにいることを確認
        echo    2. EXEビルドが完了している場合は distフォルダを確認
        echo    3. ソースコードから実行する場合は easy_novel_assistant.py を確認
        pause
        exit /b 1
    )
)

echo.
echo 📝 起動完了報告:
echo    アプリケーション: EasyNovelAssistant v3.0
echo    起動日時: %date% %time%
echo    プロジェクトディレクトリ: %cd%
echo.
echo 💭 問題が発生した場合:
echo    1. GitHub Issues: https://github.com/zapabob/EasyNovelAssistant/issues
echo    2. ドキュメント: README.md を参照
echo    3. 設定ファイル: config.json を確認
echo. 