@echo off
chcp 65001 > NUL
setlocal

set "ROOT=%~dp0"
set "KOBOLD_URL=http://127.0.0.1:5001/api/v1/model"

echo [1/2] Checking KoboldCpp endpoint: %KOBOLD_URL%
C:\Windows\System32\curl.exe -sS "%KOBOLD_URL%" > NUL
if errorlevel 1 (
  echo [ERROR] KoboldCpp is not reachable on 127.0.0.1:5001
  echo Start KoboldCpp and load a model first, then rerun this launcher.
  pause
  exit /b 1
)

echo [2/2] Launching EasyNovelAssistant
call "%ROOT%Run-EasyNovelAssistant.bat"
exit /b %errorlevel%
