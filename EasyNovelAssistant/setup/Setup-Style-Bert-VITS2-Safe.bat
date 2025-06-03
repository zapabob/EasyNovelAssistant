@echo off
chcp 65001 > NUL
echo 🛡️ Style-Bert-VITS2 安全セットアップ（修復済み環境保護版）
echo ======================================================

pushd %~dp0..\..

@REM 既存の修復済み環境をチェック
if exist Style-Bert-VITS2\venv\Scripts\python.exe (
    echo 📋 既存のStyle-Bert-VITS2仮想環境を発見
    echo.
    
    @REM 修復済み環境の動作確認
    pushd Style-Bert-VITS2
    echo 🧪 既存環境の動作確認中...
    venv\Scripts\python.exe -c "import torch; import transformers; import gradio; print('✅ 既存環境は正常に動作しています')" 2>nul
    if %errorlevel% equ 0 (
        echo ✅ 既存のStyle-Bert-VITS2環境は正常です
        echo    セットアップをスキップします
        popd
        popd
        pause
        exit /b 0
    ) else (
        echo ⚠️ 既存環境に問題があります
        popd
    )
    
    echo.
    echo 選択してください:
    echo 1) 既存環境をバックアップして新規セットアップ
    echo 2) 既存環境を保持してセットアップをキャンセル
    echo 3) 強制的に既存環境を上書き
    echo.
    set /p choice="選択 (1-3): "
    
    if "%choice%"=="2" (
        echo 📄 セットアップをキャンセルしました
        popd
        pause
        exit /b 0
    )
    
    if "%choice%"=="1" (
        echo 💾 既存環境をバックアップ中...
        if exist Style-Bert-VITS2_backup\ ( rd /s /q Style-Bert-VITS2_backup\ )
        xcopy /E /I /Q Style-Bert-VITS2 Style-Bert-VITS2_backup\
        echo ✅ バックアップ完了: Style-Bert-VITS2_backup\
    )
    
    if "%choice%"=="3" (
        echo ⚠️ 強制上書きモード
    )
    
    echo.
)

@REM メインセットアップを実行
echo 🚀 Style-Bert-VITS2セットアップを開始...
call "%~dp0Setup-Style-Bert-VITS2.bat"
if %errorlevel% neq 0 ( 
    echo ❌ セットアップ失敗
    if exist Style-Bert-VITS2_backup\ (
        echo 🔄 バックアップから復元しますか？ (Y/N)
        set /p restore="復元する場合はYを入力: "
        if /i "%restore%"=="Y" (
            rd /s /q Style-Bert-VITS2\
            xcopy /E /I /Q Style-Bert-VITS2_backup Style-Bert-VITS2\
            echo ✅ バックアップから復元完了
        )
    )
    pause 
    popd
    exit /b 1 
)

popd

echo.
echo 🎉 Style-Bert-VITS2 安全セットアップ完了！
echo    修復済み環境が保護されました
echo.
pause
exit /b 0 