@echo off
setlocal
set "PROJECT_ROOT=%~dp0."
set "PYTHON_EXE=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python.exe"

"%PYTHON_EXE%" "%PROJECT_ROOT%\data_pipeline\local_runtime.py" start --project-root "%PROJECT_ROOT%" --port 8765 --interval-minutes 60
if errorlevel 1 (
  echo.
  echo StockTest failed to start. Check .runtime\server-error.log and .runtime\refresh-error.log.
  pause
  exit /b 1
)

echo.
echo StockTest is running at http://127.0.0.1:8765/index.html
endlocal
