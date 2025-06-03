@echo off
chcp 65001 > NUL
cd /d "%~dp0"

echo 🎯 EasyNovelAssistant v3.0 ポータブル版起動
echo    KoboldCpp + GGUF統合対応版
echo ====================================
echo.

REM EXEファイルの存在確認
if exist "dist\EasyNovelAssistant.exe" (
    echo 📁 EXE版を起動中...
    "dist\EasyNovelAssistant.exe"
) else if exist "EasyNovelAssistant.exe" (
    echo 📁 EXE版を起動中...
    "EasyNovelAssistant.exe"
) else (
    echo 📁 Pythonスクリプト版を起動中...
    if exist "easy_novel_assistant.py" (
        py -3 easy_novel_assistant.py
    ) else (
        echo ❌ 起動ファイルが見つかりません
        echo    以下のファイルのいずれかが必要です：
        echo    - dist\EasyNovelAssistant.exe
        echo    - EasyNovelAssistant.exe  
        echo    - easy_novel_assistant.py
        pause
        exit /b 1
    )
)

if %errorlevel% neq 0 (
    echo.
    echo ❌ エラーが発生しました (終了コード: %errorlevel%)
    echo 詳細はコンソール出力を確認してください
    pause
) 