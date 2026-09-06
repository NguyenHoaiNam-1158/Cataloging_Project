@echo off
title Cataloging_Project - Backend (FastAPI :8000)
set "ROOT=%~dp0.."
pushd "%ROOT%\backend"

if not exist "..\.env" (
  echo [!] Chua co file .env - chay scripts\setup.bat truoc.
  popd & pause & exit /b 1
)

echo Backend API : http://localhost:8000/docs
echo Ctrl+C de dung.
echo.
rem Tham so truyen thang qua, vd: start-backend.bat --batch --use-ocr
uv run python main.py %*

popd
pause
