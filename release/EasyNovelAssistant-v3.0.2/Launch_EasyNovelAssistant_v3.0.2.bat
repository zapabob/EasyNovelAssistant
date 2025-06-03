@echo off
chcp 65001 > NUL
cd /d "%~dp0"

echo 🎯 EasyNovelAssistant v3.0.2 起動中...
echo    統合システムv3搭載版
echo =====================================
echo.
echo ✅ 反復抑制システムv3
echo ✅ LoRA協調システム 
echo ✅ クロス抑制システム
echo ✅ θ最適化エンジン
echo ✅ BLEURT代替評価
echo.
echo 起動中... しばらくお待ちください
echo.

EasyNovelAssistant.exe

if %errorlevel% neq 0 (
    echo.
    echo ❌ エラーが発生しました
    echo 詳細はコンソール出力を確認してください
    echo.
    echo 🔧 トラブルシューティング:
    echo   - Windows Defenderの除外設定確認
    echo   - 管理者権限で実行
    echo   - Visual C++ Redistributableのインストール
    echo.
    pause
) 