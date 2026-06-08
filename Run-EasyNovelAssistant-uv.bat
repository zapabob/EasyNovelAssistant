@echo off
chcp 65001 > NUL
pushd %~dp0

where uv > NUL 2> NUL
if %errorlevel% neq 0 (
  echo uv が見つかりません。https://docs.astral.sh/uv/ を参考に uv をインストールしてください。
  pause
  popd
  exit /b 1
)

uv run python EasyNovelAssistant\src\easy_novel_assistant.py
if %errorlevel% neq 0 ( pause & popd & exit /b 1 )

popd
