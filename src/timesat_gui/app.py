# src/timesat_gui/app.py
from __future__ import annotations

import os
import tempfile
import threading
import webbrowser
from typing import Optional

import psutil
from flask import Flask, render_template, send_from_directory, session

# -----------------------------------------------------------------------------
# Application factory
# -----------------------------------------------------------------------------
def create_app(
    *,
    secret_key: Optional[str] = None,
    max_upload_mb: int = 4096,  # 4 GB, matches your previous config
) -> Flask:
    """
    Create and configure the Flask app.

    - Templates and static assets are expected at:
        src/timesat_gui/templates/
        src/timesat_gui/static/
    - Blueprints are imported from local package modules.
    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # Config
    app.secret_key = secret_key or os.getenv("TIMESAT_GUI_SECRET", "supersecretkey")
    app.config["MAX_CONTENT_LENGTH"] = max_upload_mb * 1024 * 1024

    # --- Blueprint registration (relative imports within the package) ---
    # Make sure these modules live under src/timesat_gui/, and update their imports to
    # use relative form (e.g., `from .ts_functions import ...`) where needed.
    from .file_list_input import file_list_input_bp
    from .tab_settings import tab_settings_bp
    from .tab_output import tab_output_bp
    from .tab_save_load import tab_save_load_bp
    from .tab_run import tab_run_bp

    app.register_blueprint(file_list_input_bp)
    app.register_blueprint(tab_settings_bp)
    app.register_blueprint(tab_output_bp)
    app.register_blueprint(tab_save_load_bp)
    app.register_blueprint(tab_run_bp)

    # -----------------------------------------------------------------------------
    # Routes (same behavior as your previous webTIMESAT.py)
    # -----------------------------------------------------------------------------
    @app.route("/")
    def home():
        info = {
            "version": "4.1.7",
            "release_date": "Jan 2025",
            "logos": {
                "malmo": "malmo-university-vector-logo.png",
                "lund": "LundUniversity_C2line_RGB.png",
                "timesat": "Slide_flat.jpg",
                "sidebar": "Slide2.jpg",
            },
            "contacts": [
                {
                    "name": "Zhanzhang Cai, Lund University, Sweden",
                    "email": "zhanzhang.cai@nateko.lu.se",
                },
                {
                    "name": "Lars Eklundh, Lund University, Sweden",
                    "email": "lars.eklundh@nateko.lu.se",
                },
                {
                    "name": "Per Jonsson, Malmö University, Sweden",
                    "email": "per.jonsson@mah.se",
                },
            ],
            "website_url": "https://github.com/TIMESAT",
        }

        number_of_cores = os.cpu_count() or 1
        total_memory = psutil.virtual_memory().total / (1024**3)  # GB
        default_temp_dir = tempfile.gettempdir()
        session["ray_dir"] = default_temp_dir

        return render_template(
            "mainapp.html",
            **info,
            runcores=number_of_cores,
            runmemory=total_memory,
            tempfolder=default_temp_dir,
        )

    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(
            os.path.join(app.root_path, "static"),
            "favicon.ico",
            mimetype="image/vnd.microsoft.icon",
        )

    @app.route("/quitapp", methods=["POST"])
    def quit_app():
        return "Thank you for using TIMESAT!"

    return app


# -----------------------------------------------------------------------------
# Launcher
# -----------------------------------------------------------------------------
def open_browser(url: str) -> None:
    try:
        webbrowser.open_new(url)
    except Exception:
        # In headless/CI environments this can fail; silently ignore.
        pass


def main() -> None:
    """
    Default entry point used by:
    - `python -m timesat_gui`
    - the console script `timesat-gui`
    """
    host = os.getenv("TIMESAT_GUI_HOST", "127.0.0.1")
    port = int(os.getenv("TIMESAT_GUI_PORT", "5000"))
    debug = os.getenv("TIMESAT_GUI_DEBUG", "0") == "1"

    app = create_app()

    # Open the browser shortly after the server starts (like your original script)
    threading.Timer(1.0, lambda: open_browser(f"http://{host}:{port}/")).start()

    # threaded=True matches your original behavior
    app.run(host=host, port=port, debug=debug, threaded=True)


# Allow `python src/timesat_gui/app.py` during local dev (optional)
if __name__ == "__main__":
    main()
