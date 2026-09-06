@echo off
setlocal enabledelayedexpansion
title Cataloging_Project - Setup may moi

rem ROOT = thu muc cha cua scripts\
set "ROOT=%~dp0.."
pushd "%ROOT%"

echo ============================================================
echo   CATALOGING_PROJECT - CAI DAT TREN MAY MOI
echo ============================================================
echo   Thu muc du an: %CD%
echo.
echo   Lan chay dau se tai Python 3.12 (qua uv), torch, faiss,
echo   paddleocr... co the ~1-2 GB va mat vai phut. Hay kien nhan.
echo ============================================================
echo.

rem ---------------------------------------------------------------
rem  [1/5] Cong cu bat buoc: git, node, npm
rem ---------------------------------------------------------------
echo [1/5] Kiem tra cong cu...
set "MISSING="
where git  >nul 2>nul || set "MISSING=!MISSING! git"
where node >nul 2>nul || set "MISSING=!MISSING! node"
where npm  >nul 2>nul || set "MISSING=!MISSING! npm"

if defined MISSING (
  echo   [X] Thieu:!MISSING!
  echo.
  echo       git      -^> winget install Git.Git
  echo       node/npm -^> winget install OpenJS.NodeJS.LTS   ^(can Node 20+^)
  echo.
  echo   Cai xong, MO LAI cua so CMD roi chay lai scripts\setup.bat
  goto :fail
)
echo   [OK] git, node, npm

rem ---------------------------------------------------------------
rem  [2/5] uv - trinh quan ly Python package (tu cai neu thieu)
rem ---------------------------------------------------------------
where uv >nul 2>nul
if errorlevel 1 (
  echo   [..] Chua co 'uv' - dang cai bang winget...
  winget install --id astral-sh.uv -e --source winget --accept-package-agreements --accept-source-agreements
  if errorlevel 1 (
    echo   [..] winget khong dung duoc - thu script chinh thuc cua astral...
    powershell -ExecutionPolicy Bypass -NoProfile -c "irm https://astral.sh/uv/install.ps1 | iex"
  )
  rem nap tam duong dan uv cho phien CMD hien tai
  if exist "%USERPROFILE%\.local\bin\uv.exe" set "PATH=%USERPROFILE%\.local\bin;%PATH%"
)

where uv >nul 2>nul
if errorlevel 1 (
  echo   [X] Van chua thay 'uv'. Hay MO LAI CMD roi chay lai scripts\setup.bat
  goto :fail
)
for /f "tokens=*" %%v in ('uv --version') do echo   [OK] %%v

rem ---------------------------------------------------------------
rem  [3/5] File .env
rem ---------------------------------------------------------------
echo.
echo [3/5] Chuan bi file .env...
if not exist ".env" (
  copy /y ".env.example" ".env" >nul
  echo   [OK] Da tao  .env  tu .env.example
  set "NEED_KEY=1"
) else (
  echo   [OK] .env da co - giu nguyen
)
if not exist "frontend_react\.env" (
  copy /y "frontend_react\.env.example" "frontend_react\.env" >nul
  echo   [OK] Da tao  frontend_react\.env
)

rem ---------------------------------------------------------------
rem  [4/5] Python deps: backend + ai-agent (uv sync)
rem ---------------------------------------------------------------
echo.
echo [4/5] Cai dependency Python (uv tu tai Python 3.12 neu can)...

echo   -^> backend
pushd backend
uv sync
if errorlevel 1 ( popd & goto :fail )
popd
echo   [OK] backend

echo   -^> ai-agent
pushd ai-agent
uv sync
if errorlevel 1 ( popd & goto :fail )
popd
echo   [OK] ai-agent

rem ---------------------------------------------------------------
rem  [5/5] Frontend deps: npm install
rem ---------------------------------------------------------------
echo.
echo [5/5] Cai dependency frontend_react (npm install)...
pushd frontend_react
call npm install
if errorlevel 1 ( popd & goto :fail )
popd
echo   [OK] frontend_react

rem ---------------------------------------------------------------
echo.
echo ============================================================
echo   HOAN TAT CAI DAT
echo ============================================================
if defined NEED_KEY (
  echo   !! BAT BUOC: mo file  .env  va dien:
  echo        GEMINI_API_KEY=your_key_here      ^(lay tai https://aistudio.google.com/apikey^)
  echo      QWEN_API_KEY la tuy chon ^(fallback khi Gemini loi^).
  echo.
)
echo   Chay he thong:
echo     scripts\start-backend.bat     ^(FastAPI  -^> http://localhost:8000/docs^)
echo     scripts\start-frontend.bat    ^(Vite     -^> http://localhost:5173^)
echo     scripts\start-dev.bat         ^(chay ca hai trong 2 cua so^)
echo ============================================================
popd
pause
exit /b 0

:fail
echo.
echo *************  CAI DAT THAT BAI - doc loi phia tren  *************
popd
pause
exit /b 1
