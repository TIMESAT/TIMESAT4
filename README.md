# TIMESAT GUI

`TIMESAT GUI` is a Python-based graphical interface and workflow manager for the [TIMESAT](https://test.pypi.org/project/timesat/) package.  
It provides a simple web dashboard to configure, run, and visualize TIMESAT outputs.

---

## Requirements

Before you begin, ensure you have the following installed:

- **Miniconda** or **Anaconda**
  - Download from [https://docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/en/latest/miniconda.html)
- **Internet access** (to install dependencies and TIMESAT from TestPyPI)
- **Python 3.12** (installed automatically by Conda)
- Optional: a web browser to access the user interface.

---

## Environment Setup

The project provides two setup scripts—one for **Windows** and one for **macOS/Linux**.  
These scripts will automatically:
1. Create a Conda environment (`py312`)
2. Upgrade `pip` and `wheel`
3. Install dependencies from `requirements.txt` (if present)
4. Install **TIMESAT** from [TestPyPI](https://test.pypi.org/)
5. Verify that TIMESAT was installed successfully

### **Windows**

1. Open **Anaconda Prompt** (or CMD where Conda is available)
2. Navigate to the project directory:
   ```bat
   cd C:\path\to\TIMESAT_GUI
   ```
3. Run the setup script:
   ```bat
   setup_env.bat
   ```
4. After successful setup, activate the environment:
   ```bat
   conda activate py312
   ```

### **macOS / Linux**

1. Open your terminal
2. Navigate to the project directory:
   ```bash
   cd /path/to/TIMESAT_GUI
   ```
3. Make the setup script executable (first time only):
   ```bash
   chmod +x setup_env.sh
   ```
4. Run the setup script:
   ```bash
   ./setup_env.sh
   ```
5. Activate the environment:
   ```bash
   source "$(conda info --base)/etc/profile.d/conda.sh"
   conda activate py312
   ```

---

## Manual Setup (optional)

If you prefer to create the environment manually:

```bash
conda create -y -n py312 python=3.12
conda activate py312
pip install -r requirements.txt
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple timesat==4.1.7.dev0
```

---

## Running webTIMESAT

Once the environment is set up and activated:

```bash
python webTIMESAT.py
```

This will start the web-based TIMESAT interface.  
By default, it usually runs on:
```
http://127.0.0.1:5000/
```

Open that link in your browser to use the application.

---

## Verifying TIMESAT Installation

You can manually test if TIMESAT is properly installed:
```bash
python -c "import timesat, timesat._timesat as _; print('TIMESAT', timesat.__version__, 'OK')"
```

Expected output:
```
TIMESAT 4.1.7.dev0 OK
```

---

## Folder Structure

Example layout of your project directory:

```
webTIMESAT/
│
├── webTIMESAT.py
├── ts_functions.py
├── ts_full_run.py
├── file_list_input.py
├── tab_data_input.py
├── tab_output.py
├── tab_run.py
├── tab_save_load.py
├── tab_settings.py
│
├── requirements.txt
├── setup_env.bat          ← Windows setup script
├── setup_env.sh           ← macOS/Linux setup script
│
├── templates/             ← HTML templates
└── static/                ← Static files (CSS, JS, figures)
```

---

## License

This project is distributed under the terms of GPL.  
Please update this section accordingly.

---
