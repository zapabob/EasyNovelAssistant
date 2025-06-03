@echo off
chcp 65001 > NUL
echo 🚀 Style-Bert-VITS2 CUDA版セットアップ（RTX3080対応）
echo =======================================================

@REM メインセットアップを実行
call "%~dp0Setup-Style-Bert-VITS2.bat"
if %errorlevel% neq 0 ( 
    echo ❌ メインセットアップ失敗
    pause 
    exit /b 1 
)

echo.
echo 🔧 CUDA版PyTorchへアップグレード中...
pushd %~dp0..\..\Style-Bert-VITS2

call %~dp0ActivateVirtualEnvironment.bat
if %errorlevel% neq 0 ( popd & exit /b 1 )

@REM CPU版PyTorchをアンインストール
echo pip uninstall -y torch torchvision torchaudio
pip uninstall -y torch torchvision torchaudio

@REM CUDA 12.1版PyTorchをインストール（RTX3080対応）
echo pip install torch^<2.4 torchvision^<0.19 torchaudio^<2.4 --index-url https://download.pytorch.org/whl/cu121
pip install torch^<2.4 torchvision^<0.19 torchaudio^<2.4 --index-url https://download.pytorch.org/whl/cu121
if %errorlevel% neq 0 ( 
    echo ❌ CUDA版PyTorchインストール失敗
    pause 
    popd 
    exit /b 1 
)

@REM CUDA動作確認
echo.
echo 🧪 CUDA動作確認中...
python -c "import torch; print(f'✅ PyTorch: {torch.__version__}'); print(f'✅ CUDA available: {torch.cuda.is_available()}'); print(f'✅ GPU count: {torch.cuda.device_count()}' if torch.cuda.is_available() else '⚠️ CUDA not available')"
if %errorlevel% neq 0 ( 
    echo ❌ CUDA動作確認失敗
    pause 
    popd 
    exit /b 1 
)

popd

echo.
echo 🎉 Style-Bert-VITS2 CUDA版セットアップ完了！
echo    RTX3080でのGPU加速が利用可能です
echo.
pause
exit /b 0 