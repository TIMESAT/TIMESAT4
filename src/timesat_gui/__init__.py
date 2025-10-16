# src/timesat_gui/__init__.py

# Optional: define a version string (keep in sync with pyproject.toml if you set one there)
__version__ = "0.1.0.dev0"

# Re-export create_app for convenience in tests and WSGI servers
from .app import create_app  # noqa: F401
