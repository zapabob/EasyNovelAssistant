@echo off
chcp 65001 > NUL
pushd %~dp0
set CURL_CMD=C:\Windows\System32\curl.exe -k

@REM 7B: 33, 35B: 41, 70B: 65
set GPU_LAYERS=0

@REM 2048, 4096, 8192, 16384, 32768, 65536, 131072
set CONTEXT_SIZE=4096

if not exist DataPilot-ArrowPro-7B-KUJIRA-IQ4_XS.gguf (
    start "" https://huggingface.co/mmnga/DataPilot-ArrowPro-7B-KUJIRA-gguf
    %CURL_CMD% -LO https://huggingface.co/mmnga/DataPilot-ArrowPro-7B-KUJIRA-gguf/resolve/main/DataPilot-ArrowPro-7B-KUJIRA-IQ4_XS.gguf
)

koboldcpp.exe --gpulayers %GPU_LAYERS% --usecublas --contextsize %CONTEXT_SIZE% DataPilot-ArrowPro-7B-KUJIRA-IQ4_XS.gguf
if %errorlevel% neq 0 ( pause & popd & exit /b 1 )
popd
