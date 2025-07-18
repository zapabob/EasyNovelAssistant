@echo off
chcp 65001 > NUL
pushd %~dp0
set CURL_CMD=C:\Windows\System32\curl.exe -k

@REM 7B: 33, 35B: 41, 70B: 65
set GPU_LAYERS=0

@REM 2048, 4096, 8192, 16384, 32768, 65536, 131072
set CONTEXT_SIZE=8192

if not exist command-r-plus-Q3_K_M-00001-of-00002.gguf (
    start "" https://huggingface.co/pmysl/c4ai-command-r-plus-GGUF
    %CURL_CMD% -LO https://huggingface.co/pmysl/c4ai-command-r-plus-GGUF/resolve/main/command-r-plus-Q3_K_M-00001-of-00002.gguf
)
if not exist command-r-plus-Q3_K_M-00002-of-00002.gguf (
    start "" https://huggingface.co/pmysl/c4ai-command-r-plus-GGUF
    %CURL_CMD% -LO https://huggingface.co/pmysl/c4ai-command-r-plus-GGUF/resolve/main/command-r-plus-Q3_K_M-00002-of-00002.gguf
)

koboldcpp.exe --gpulayers %GPU_LAYERS% --usecublas --contextsize %CONTEXT_SIZE% command-r-plus-Q3_K_M-00001-of-00002.gguf
if %errorlevel% neq 0 ( pause & popd & exit /b 1 )
popd
