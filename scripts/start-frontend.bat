@echo off
title Cataloging_Project - Frontend (Vite :5173)
set "ROOT=%~dp0.."
pushd "%ROOT%\frontend_react"

if not exist "node_modules" (
  echo [!] Chua cai node_modules - chay scripts\setup.bat truoc.
  popd & pause & exit /b 1
)

echo Frontend : http://localhost:5173   (proxy /api -^> http://localhost:8000)
echo Ctrl+C de dung.
echo.
call npm run dev

popd
pause
