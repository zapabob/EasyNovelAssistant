@echo off
chcp 65001 > NUL
setlocal

set "ROOT=%~dp0"
set "HYPURA_URL=http://127.0.0.1:8080/api/tags"
set "PROXY_SCRIPT=%ROOT%proxy\kobold_to_hypura_proxy.py"
set "PROXY_LISTEN=127.0.0.1:5001"
set "PROXY_HYPURA=127.0.0.1:8080"

echo [INFO] Optional launcher: Kobold-compatible proxy to Hypura
echo [INFO] Default dual-path operation now uses real KoboldCpp for EasyNovelAssistant.

echo [1/3] Checking Hypura endpoint: %HYPURA_URL%
C:\Windows\System32\curl.exe -sS "%HYPURA_URL%" > NUL
if errorlevel 1 (
  echo [ERROR] Hypura is not reachable on 127.0.0.1:8080
  echo Start Hypura first, then rerun this launcher.
  pause
  exit /b 1
)

if not exist "%PROXY_SCRIPT%" (
  echo [ERROR] Proxy script not found: "%PROXY_SCRIPT%"
  pause
  exit /b 1
)

echo [2/3] Starting Kobold-compatible proxy on %PROXY_LISTEN%
start "Kobold->Hypura Proxy" cmd /k py -3 "%PROXY_SCRIPT%" --listen %PROXY_LISTEN% --hypura %PROXY_HYPURA%
timeout /t 1 /nobreak > NUL

echo [3/3] Launching EasyNovelAssistant
call "%ROOT%Run-EasyNovelAssistant.bat"
exit /b %errorlevel%
