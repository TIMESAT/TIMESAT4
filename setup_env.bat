@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

set "ENV_NAME=py312"
set "PY_VER=3.12"
set "TIMESAT_VER=4.1.7.dev0"

echo ======================================================
echo  Step 1: Create or update Conda environment "%ENV_NAME%"
echo ======================================================
where conda >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Conda not found. Please install Miniconda or Anaconda first.
    pause
    exit /b 1
)

:: Check if the environment already exists
call conda env list | findstr /r "^\s*%ENV_NAME%\s" >nul
if errorlevel 1 (
    echo Creating new environment "%ENV_NAME%" with Python %PY_VER%...
    call conda create -y -n %ENV_NAME% python=%PY_VER%
) else (
    echo Environment "%ENV_NAME%" already exists. Proceeding...
)

echo ======================================================
echo  Step 2: Activate the environment
echo ======================================================
call conda activate %ENV_NAME%
if errorlevel 1 (
    echo [ERROR] Failed to activate environment.
    pause
    exit /b 1
)

echo ======================================================
echo  Step 3: Upgrade pip and wheel
echo ======================================================
python -m pip install -U pip wheel

echo ======================================================
echo  Step 4: Install dependencies from requirements.txt
echo ======================================================
if exist requirements.txt (
    python -m pip install -r requirements.txt
) else (
    echo ⚠️ requirements.txt not found, skipping dependency installation.
)

echo ======================================================
echo  Step 5: Install TIMESAT %TIMESAT_VER% from TestPyPI
echo ======================================================
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple timesat==4.1.7.dev0
python -c "import timesat, timesat._timesat as _; print('timesat', timesat.__version__, 'OK')"
if errorlevel 1 (
    echo [ERROR] TIMESAT installation failed.
    pause
    exit /b 1
)


echo ======================================================
echo  ✅ Environment setup complete
echo ======================================================
echo To activate later, run:
echo     conda activate %ENV_NAME%
echo.
pause
endlocal
