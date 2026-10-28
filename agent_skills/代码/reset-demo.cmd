@echo off
setlocal
cd /d "%~dp0"
uv run --frozen python -m app.reset_demo
echo.
pause
