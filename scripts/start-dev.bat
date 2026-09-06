@echo off
rem Mo backend va frontend, moi cai 1 cua so CMD rieng.
set "HERE=%~dp0"
start "Cataloging - Backend"  cmd /k "%HERE%start-backend.bat"
timeout /t 2 >nul
start "Cataloging - Frontend" cmd /k "%HERE%start-frontend.bat"
echo Da mo 2 cua so. Dong cua so nay duoc.
