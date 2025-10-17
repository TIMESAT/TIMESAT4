# TIMESAT GUI

`TIMESAT GUI` is a graphical user interface and workflow manager for the [TIMESAT](https://pypi.org/project/timesat/) package.  
It provides a simple web dashboard to configure and run TIMESAT.

---

## Requirements

Before you begin, make sure you have:

- **Miniconda** or **Anaconda** (for environment management)  
  Download: [https://docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/en/latest/miniconda.html)
- **Python 3.10+**
- **Internet access** (for package installation and updates)
- Optional: a modern web browser to access the interface.

---

## Installation

`timesat-gui` is available on **TestPyPI** and can be installed using **pip** or **uv**.  
Although it is not published on Conda, you can safely install it *inside* a Conda environment.

### Option 1 — Install inside a Conda environment

```bash
conda create -n timesat python=3.12
conda activate timesat
pip install timesat-gui
```

> This approach uses Conda only for environment isolation.  
> The installation itself is handled by pip, which will automatically install `timesat` and all required dependencies.

---

### Option 2 — Install via uv (recommended for pure Python environments)

[`uv`](https://github.com/astral-sh/uv) is a modern, high-performance alternative to pip and venv.

1. Install `uv`:

   ```bash
   pip install uv
   # or
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Create a virtual environment and install the package:

   ```bash
   uv venv .venv
   source .venv/bin/activate
   uv pip install timesat-gui
   ```

> `uv` provides faster dependency resolution and caching.  
> It will automatically install `timesat` and related dependencies.

---

### Option 3 — Direct installation with pip

If you already have Python 3.10+ installed:

```bash
pip install timesat-gui
```

---

## Launch the Application

After installation, start the GUI with:

```bash
timesat-gui
```

---

## License and Legal Notice

### 🧾 TIMESAT-GUI License

**TIMESAT-GUI** is released under the **GNU General Public License (GPL)**.  
You are free to use, modify, and distribute this software under the terms of the GPL.

The GPL license applies **only to the TIMESAT-GUI source code and assets** provided in this repository.

### ⚠️ TIMESAT License and Restrictions

`timesat-gui` depends on the **TIMESAT** Python bindings, which link to the proprietary TIMESAT Fortran core.  
The TIMESAT package is **not open source** and is distributed under the following proprietary terms:

```
SPDX-License-Identifier: LicenseRef-Proprietary-TIMESAT
TIMESAT Python Bindings License
Version 4.1.7 — © 2025 Zhanzhang Cai, Lars Eklundh, and Per Jönsson

This software provides Python bindings to the proprietary TIMESAT Fortran core.
Redistribution, modification, or commercial use is prohibited except as explicitly
permitted in this license agreement or by written consent of the authors.

You are granted a non-transferable, non-exclusive, revocable license 
to use the precompiled binary libraries distributed with this package 
solely for the purpose of building and running the Python interface code 
distributed with this repository.

Further restrictions apply to redistribution, reverse engineering, modification,
and commercial use. For details, refer to the full license terms in the TIMESAT
package documentation or at https://github.com/TIMESAT/.
```

By using `timesat-gui`, you implicitly agree to the terms of the **TIMESAT Proprietary License** for any code, data, or binaries included from the TIMESAT package.

### 📦 Dependency Licenses

- `timesat-gui` may install additional open-source dependencies (e.g., Flask, pandas, NumPy).  
- Each dependency retains its own license (MIT, BSD, Apache, etc.).  
- Before redistributing or bundling this software, review the license terms of each dependency carefully.

### ⚖️ Summary

| Component        | License Type | Notes |
|------------------|--------------|-------|
| TIMESAT-GUI      | GPL v3       | Open source, modification and redistribution permitted under GPL. |
| TIMESAT          | Proprietary  | All rights reserved. Redistribution and modification prohibited without written consent. |
| Other Dependencies | Various (MIT/BSD/Apache) | Check individual package licenses before redistribution. |

For detailed license information, refer to the license files distributed with each installed package.

---

## Citation

If you use **TIMESAT** or **TIMESAT-GUI** in your research, please cite the corresponding release on Zenodo:

> Cai, Z., Eklundh, L., & Jönsson, P. (2025). *TIMESAT4:  is a software package for analysing time-series of satellite sensor data* (Version 4.1.x) [Computer software]. Zenodo.   
> [https://doi.org/10.5281/zenodo.17369757](https://doi.org/10.5281/zenodo.17369757)

---

## Acknowledgments

- [TIMESAT](https://www.nateko.lu.se/TIMESAT) — Original analysis framework for satellite time-series data.  
- This project provides a user-friendly interface to make TIMESAT more accessible for research and operational workflows.

---

