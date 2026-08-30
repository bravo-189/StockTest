@echo off
setlocal
set "PROJECT_ROOT=%~dp0."
set "PYTHON_EXE=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python.exe"

"%PYTHON_EXE%" "%PROJECT_ROOT%\data_pipeline\local_runtime.py" stop --project-root "%PROJECT_ROOT%" --port 8765 --interval-minutes 60
echo.
echo StockTest local services stopped.
endlocal
