@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

set "CONDA_ENV_NAME=py312"
set "PY_VER=3.12"
set "TIMESAT_VER=4.1.7.dev0"

echo ======================================================
echo  Step 1: Check for conda
echo ======================================================
where conda >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Conda not found. Please install Miniconda/Anaconda and ensure it is on PATH.
    pause
    exit /b 1
)

echo.
echo ======================================================
echo  Step 2: Create Conda environment "%CONDA_ENV_NAME%" (Python %PY_VER%)
echo ======================================================
call conda env list | findstr /r "^\s*%CONDA_ENV_NAME%\s" >nul
if errorlevel 1 (
    echo Creating new environment "%CONDA_ENV_NAME%"...
    call conda create -y -n %CONDA_ENV_NAME% python=%PY_VER%
) else (
    echo Environment "%CONDA_ENV_NAME%" already exists. Skipping creation.
)

echo.
echo ======================================================
echo  Step 3: Upgrade pip and wheel inside "%CONDA_ENV_NAME%"
echo ======================================================
call conda run -n %CONDA_ENV_NAME% python -m pip install -U pip wheel
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip/wheel.
    pause
    exit /b 1
)

echo.
echo ======================================================
echo  Step 4: Install dependencies from requirements.txt (if present)
echo ======================================================
if exist requirements.txt (
    echo Installing from requirements.txt...
    call conda run -n %CONDA_ENV_NAME% python -m pip install -r requirements.txt
) else (
    echo ⚠️  requirements.txt not found. Skipping dependency installation.
)

echo.
echo ======================================================
echo  Step 5: Install TIMESAT %TIMESAT_VER% from TestPyPI
echo ======================================================
call conda run -n %CONDA_ENV_NAME% python -m pip install ^
  --index-url https://test.pypi.org/simple/ ^
  --extra-index-url https://pypi.org/simple ^
  timesat==%TIMESAT_VER%
if errorlevel 1 (
    echo [ERROR] TIMESAT installation failed.
    pause
    exit /b 1
)

echo.
echo ======================================================
echo  Step 6: Verify TIMESAT installation
echo ======================================================
call conda run -n %CONDA_ENV_NAME% python - <<PYCODE
import timesat, timesat._timesat as _
print(f"TIMESAT {timesat.__version__} OK")
PYCODE
if errorlevel 1 (
    echo [ERROR] TIMESAT verification failed.
    pause
    exit /b 1
)

echo.
echo ======================================================
echo  ✅ Environment setup complete!
echo ======================================================
echo To activate the environment, run:
echo     conda activate %CONDA_ENV_NAME%
echo.
pause
endlocal
