@echo off
chcp 65001 > NUL
setlocal

set "ROOT=%~dp0"
set "KOBOLD_URL=http://127.0.0.1:5001/api/v1/model"
set "KCPP_ROOT=C:\Users\downl\Desktop\koboldcpp-turboquant-integration\koboldcpp"
set "KCPP_MODEL=%~1"

if not exist "%KCPP_ROOT%\koboldcpp.py" (
  echo [ERROR] koboldcpp.py not found: %KCPP_ROOT%
  pause
  exit /b 1
)

echo [1/3] Checking KoboldCpp endpoint: %KOBOLD_URL%
C:\Windows\System32\curl.exe -sS "%KOBOLD_URL%" > NUL
if errorlevel 1 (
  echo [2/3] Starting KoboldCpp TurboQuant server...
  pushd "%KCPP_ROOT%"
  if "%KCPP_MODEL%"=="" (
    start "KoboldCpp TurboQuant" py -3 koboldcpp.py --host 127.0.0.1 --port 5001 --usecublas --turboquant --tq-triality-mix 0.50
  ) else (
    start "KoboldCpp TurboQuant" py -3 koboldcpp.py --model "%KCPP_MODEL%" --host 127.0.0.1 --port 5001 --usecublas --turboquant --tq-triality-mix 0.50
  )
  popd
  timeout /t 8 > NUL
)

echo [3/3] Launching EasyNovelAssistant
call "%ROOT%Run-EasyNovelAssistant.bat"
exit /b %errorlevel%
