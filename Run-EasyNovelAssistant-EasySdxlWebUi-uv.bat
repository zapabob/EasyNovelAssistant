@echo off
chcp 65001 > NUL
pushd %~dp0

if "%EASY_SDXL_WEBUI_DIR%"=="" (
  if exist H:\EasySdxlWebUi\SdxlWebUi-forge.bat (
    set "EASY_SDXL_WEBUI_DIR=H:\EasySdxlWebUi"
  ) else (
    set "EASY_SDXL_WEBUI_DIR=%~dp0EasySdxlWebUi"
  )
)

if not exist "%EASY_SDXL_WEBUI_DIR%\SdxlWebUi-forge.bat" (
  echo EasySdxlWebUi が見つかりません: %EASY_SDXL_WEBUI_DIR%
  echo EASY_SDXL_WEBUI_DIR に EasySdxlWebUi の展開先を指定してください。
  pause
  popd
  exit /b 1
)

where uv > NUL 2> NUL
if %errorlevel% neq 0 (
  echo uv が見つかりません。https://docs.astral.sh/uv/ を参考に uv をインストールしてください。
  pause
  popd
  exit /b 1
)

set DISABLE_LISTEN_AUTOLAUNCH=1
start "EasySdxlWebUi Forge API" /D "%EASY_SDXL_WEBUI_DIR%" "%EASY_SDXL_WEBUI_DIR%\SdxlWebUi-forge.bat" --api

uv run python EasyNovelAssistant\src\easy_novel_assistant.py
if %errorlevel% neq 0 ( pause & popd & exit /b 1 )

popd
