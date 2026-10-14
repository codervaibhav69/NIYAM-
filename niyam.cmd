@echo off
if /I "%~1 %~2"=="wake up" (
    cd /d "%USERPROFILE%\Niyam"
    "%USERPROFILE%\Niyam\.venv\Scripts\python.exe" "%USERPROFILE%\Niyam\main.py"
) else (
    echo Usage: NIYAM wake up
)
