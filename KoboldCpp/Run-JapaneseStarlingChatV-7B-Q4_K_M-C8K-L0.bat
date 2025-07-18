@echo off
chcp 65001 > NUL
pushd %~dp0
set CURL_CMD=C:\Windows\System32\curl.exe -k

@REM 7B: 33, 35B: 41, 70B: 65
set GPU_LAYERS=0

@REM 2048, 4096, 8192, 16384, 32768, 65536, 131072
set CONTEXT_SIZE=8192

if not exist japanese-starling-chatv-7b.Q4_K_M.gguf (
    start "" https://huggingface.co/TFMC/Japanese-Starling-ChatV-7B-GGUF
    %CURL_CMD% -LO https://huggingface.co/TFMC/Japanese-Starling-ChatV-7B-GGUF/resolve/main/japanese-starling-chatv-7b.Q4_K_M.gguf
)

koboldcpp.exe --gpulayers %GPU_LAYERS% --usecublas --contextsize %CONTEXT_SIZE% japanese-starling-chatv-7b.Q4_K_M.gguf
if %errorlevel% neq 0 ( pause & popd & exit /b 1 )
popd
