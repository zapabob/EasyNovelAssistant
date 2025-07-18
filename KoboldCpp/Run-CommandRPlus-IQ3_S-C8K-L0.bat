@echo off
chcp 65001 > NUL
pushd %~dp0
set CURL_CMD=C:\Windows\System32\curl.exe -k

@REM 7B: 33, 35B: 41, 70B: 65
set GPU_LAYERS=0

@REM 2048, 4096, 8192, 16384, 32768, 65536, 131072
set CONTEXT_SIZE=8192

if not exist ggml-c4ai-command-r-plus-104b-iq3_s.gguf (
    start "" https://huggingface.co/dranger003/c4ai-command-r-plus-iMat.GGUF
    %CURL_CMD% -LO https://huggingface.co/dranger003/c4ai-command-r-plus-iMat.GGUF/resolve/main/ggml-c4ai-command-r-plus-104b-iq3_s.gguf
)

koboldcpp.exe --gpulayers %GPU_LAYERS% --usecublas --contextsize %CONTEXT_SIZE% ggml-c4ai-command-r-plus-104b-iq3_s.gguf
if %errorlevel% neq 0 ( pause & popd & exit /b 1 )
popd
