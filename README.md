# TIMESAT GUI

`TIMESAT GUI` is a Python-based graphical interface and workflow manager for the [TIMESAT](https://test.pypi.org/project/timesat/) package.  
It provides a simple web dashboard to configure, run, and visualize TIMESAT outputs.

---

## Requirements

Before you begin, make sure you have:

- **Miniconda** or **Anaconda**  
  Download: [https://docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/en/latest/miniconda.html)
- **Internet access** (to install packages and TIMESAT)
- **Python 3.12** (installed automatically via Conda)
- Optional: a web browser to use the interface.

---

## Manual Environment Setup

You can set up the environment manually using Conda and pip.

### Step 1 — Create and activate a Conda environment
```bash
conda create -y -n py312 python=3.12
conda activate py312
```

### Step 2 — Upgrade pip and wheel
```bash
python -m pip install -U pip wheel
```

### Step 3 — Install dependencies
Make sure you are in the same folder as `requirements.txt`, then run:
```bash
python -m pip install -r requirements.txt
```

### Step 4 — Install TIMESAT from TestPyPI
TIMESAT 4.1.7.dev0 is hosted on TestPyPI, not the regular PyPI.  
Install it using:
```bash
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple timesat
```

### Step 5 — Verify TIMESAT installation
Run the following test:
```bash
python -c "import timesat, timesat._timesat as _; print('TIMESAT', timesat.__version__, 'OK')"
```
Expected output:
>>TIMESAT 4.1.7.dev0 OK


---

## Run TIMESAT GUI

Once your environment is active, start the app with:
```bash
python webTIMESAT.py
```

You’ll see output similar to:
```
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

Open that link in your browser to access the GUI.

---

## Project Structure

```
TIMESAT_GUI/
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
│
├── templates/             ← HTML templates
└── static/                ← Static files (CSS, JS, figures)
```

---

## License

This project is distributed under the GPL license.  
Please update this section as needed.
