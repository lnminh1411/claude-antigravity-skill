@echo off
rem Double-click installer for Windows. Arguments pass through, e.g. install.cmd -Project C:\path\to\repo
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
echo.
pause
