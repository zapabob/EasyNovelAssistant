@echo off
chcp 65001 > NUL
pushd %~dp0
set CURL_CMD=C:\Windows\System32\curl.exe -k

@REM 7B: 33, 35B: 41, 70B: 65
set GPU_LAYERS=0

@REM 2048, 4096, 8192, 16384, 32768, 65536, 131072
set CONTEXT_SIZE=4096

if not exist Antler-7B-Novel-Writing_IQ4_XS.gguf (
    start "" https://huggingface.co/Aratako/Antler-7B-Novel-Writing-GGUF
    %CURL_CMD% -LO https://huggingface.co/Aratako/Antler-7B-Novel-Writing-GGUF/resolve/main/Antler-7B-Novel-Writing_IQ4_XS.gguf
)

koboldcpp.exe --gpulayers %GPU_LAYERS% --usecublas --contextsize %CONTEXT_SIZE% Antler-7B-Novel-Writing_IQ4_XS.gguf
if %errorlevel% neq 0 ( pause & popd & exit /b 1 )
popd
