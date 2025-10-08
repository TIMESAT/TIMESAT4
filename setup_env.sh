#!/usr/bin/env bash
# setup_env.sh
set -euo pipefail

# --- Settings ---
CONDA_ENV_NAME="py312"
PY_VER="3.12"
TIMESAT_VER="4.1.7.dev0"

# --- Sanity checks ---
if ! command -v conda >/dev/null 2>&1; then
  echo "Conda not found. Please install Miniconda/Anaconda and ensure 'conda' is in PATH."
  exit 1
fi

echo ">>> Using Conda: $(conda --version)"

# --- Create env if needed ---
if conda env list | awk '{print $1}' | grep -qx "$CONDA_ENV_NAME"; then
  echo ">>> Step 1: Conda environment '$CONDA_ENV_NAME' already exists; skipping creation."
else
  echo ">>> Step 1: Creating Conda environment '$CONDA_ENV_NAME' (Python $PY_VER)"
  conda create -y -n "$CONDA_ENV_NAME" "python=$PY_VER"
fi

# --- Upgrade pip/wheel inside the env ---
echo ">>> Step 2: Upgrade pip and wheel in '$CONDA_ENV_NAME'"
conda run -n "$CONDA_ENV_NAME" python -m pip install -U pip wheel

# --- Install project dependencies if requirements.txt is present ---
echo ">>> Step 3: Install dependencies from requirements.txt (if present)"
if [ -f requirements.txt ]; then
  conda run -n "$CONDA_ENV_NAME" python -m pip install -r requirements.txt
else
  echo "⚠️ requirements.txt not found; skipping dependency installation."
fi

# --- Install TIMESAT from TestPyPI ---
echo ">>> Step 4: Install TIMESAT $TIMESAT_VER from TestPyPI"
conda run -n "$CONDA_ENV_NAME" python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple \
  "timesat==$TIMESAT_VER"

# --- Verify TIMESAT import ---
echo ">>> Step 5: Verify TIMESAT installation"
conda run -n "$CONDA_ENV_NAME" python - <<'PYCODE'
import timesat, timesat._timesat as _
print(f"TIMESAT {timesat.__version__} OK")
PYCODE

echo
echo "✅ Environment setup complete."
echo "To activate later, run:"
echo "  source \"$(conda info --base)/etc/profile.d/conda.sh\""
echo "  conda activate $CONDA_ENV_NAME"
