from flask import Blueprint, render_template, session, request, jsonify, send_file
import plotly
import plotly.graph_objs as go
import numpy as np
from . import ts_functions
import pandas as pd
import json
import datetime
import io

import json
import threading
import sys
from multiprocessing import Process, Queue
from PyQt5.QtWidgets import QApplication, QFileDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt  # Import for window modality

tab_save_load_bp = Blueprint('tab_save_load', __name__)

# Global variable to track if the dialog is open
is_dialog_open = False
lock = threading.Lock()

def _form_json_(session_data_json):
    # define and form settings
    data_to_write = {
        # 'inputs': {
        #     'input_type': {
        #         'value': session_data_json['input_type'],
        #         'description': 'Input data type: image, csv.'
        #     },
        #     'image_list_file': {
        #         'value': session_data_json['image_list_file'],
        #         'description': 'A file containing number of images & a list of full path image files.'
        #     },
        #     'quality_list_file': {
        #         'value': session_data_json['quality_list_file'],
        #         'description': 'A file containing number of images & a list of full path quality files (image).'
        #     },
        #     'image_file_names': {
        #         'value': session_data_json['image_file_names'],
        #         'description': 'A list of full path image files.'
        #     },
        #     'qa_file_names': {
        #         'value': session_data_json['qa_file_names'],
        #         'description': 'A list of full path quality files (image).'
        #     },
        #     'table_data': {
        #         'value': session_data_json['table_data'],
        #         'description': 'data from table format inputs.'
        #     },
        #     'num_of_data': {
        #         'value': session_data_json['num_of_data'],
        #         'description': 'Number of time steps/images.'
        #     },
        #     'imwindow': {
        #         'value': [0, 0, 0, 0],
        #         'description': 'Range and weights for mask data conversion.'
        #     }
        # },
        # 'outputs':{
        #     'output_folder': {
        #         'value': session_data_json['output_folder'],
        #         'description': 'A directory where output files will be saved.'
        #     }
        # },
        'settings': {
            'p_ignoreday': {
                'value': session_data_json['p_ignoreday'],
                'description': 'Ignore this day in leap years.'
            },
            'data-range': {
                'value': [session_data_json['data-range-min'], session_data_json['data-range-max']],
                'description': 'Data range with minimum and maximum limits.'
            },
            'p_davailwin': {
                'value': session_data_json['p_davailwin'],
                'description': 'A window size to check data availibility.'
            },
            'outliers': {
                'value': session_data_json['outliers'],
                'description': '0/1 switch of outlier detection.'
            },
            'p_a': {
                'value': [session_data_json['a1'], session_data_json['a2'], session_data_json['a3'], session_data_json['a4'], session_data_json['a5'], session_data_json['a6'], session_data_json['a7'], session_data_json['a8'], session_data_json['a9']],
                'description': 'Range and weights for mask data conversion.'
            },
            'base-level': {
                'value': session_data_json['base-level'],
                'description': 'Parameter for defining the base level percentile.'
            },
            'p_fitmethod': {
                'value': session_data_json['p_fitmethod'],
                'description': 'Fitting method. 1: DL; 2: Spline; 3: DL-SP.'
            },
            'smoothing-par': {
                'value': session_data_json['smoothing-par'],
                'description': 'Smoothing parameter for smoothing spline.'
            },
            'envelope-iterations': {
                'value': session_data_json['envelope-iterations'],
                'description': 'Number of envelope iterations. 1: no iteration; 2: one iteration; 3: two iterations.'
            },
            'adaptation-strength': {
                'value': session_data_json['adaptation-strength'],
                'description': 'Adaptation strength factor. Value range from 1 - 10.'
            },
            'p_outststep': {
                'value': session_data_json['p_outststep'],
                'description': 'Time step of the fitting data.'
            },
            'seasonal-method': {
                'value': session_data_json['seasonal-method'],
                'description': 'Method of determining coarse seasons. 1: irregular season; 2: regular season.'
            },
            'seasonal-par': {
                'value': session_data_json['seasonal-par'],
                'description': 'Parameter for defining the level to detect small seasonal variations.'
            },
            'season-start-method': {
                'value': session_data_json['season-start-method'],
                'description': 'Method used for determining the start of the season.'
            },
            'season-start': {
                'value': [session_data_json['season-start'],session_data_json['season-end']],
                'description': 'Parameters for determining the start of the season.'
            },
            'nodata-out': {
                'value': session_data_json['nodata-out'],
                'description': 'Value to represent no data in the output.'
            },
            'debug_mod': {
                'value': session_data_json['debug_mod'],
                'description': 'Debuging option.'
            },
            'n_core': {
                'value': session_data_json['n_core'],
                'description': 'Number of core.'
            },
            'n_memory': {
                'value': session_data_json['n_memory'],
                'description': 'Number of memory.'
            }
        }
    }
    return data_to_write


def choose_output_folder_process(queue):
    app = QApplication(sys.argv)
    app.setApplicationName("Choose Output Folder")
    app.setWindowIcon(QIcon('Slide5.JPG'))

    # Create the file dialog and set it to always stay on top
    file_dialog = QFileDialog()
    file_dialog.setWindowModality(Qt.ApplicationModal)  # Modal dialog to stay on top
    file_dialog.setWindowFlags(file_dialog.windowFlags() | Qt.WindowStaysOnTopHint)

    folder_path = file_dialog.getExistingDirectory(None, "Select Output Folder", "")
    queue.put(folder_path if folder_path else None)


def choose_output_folder():
    queue = Queue()
    p = Process(target=choose_output_folder_process, args=(queue,))
    p.start()
    p.join()

    return {"path": queue.get()}


@tab_save_load_bp.route('/choose_folder_and_save', methods=['GET'])
def choose_folder_and_save():
    # Convert the Python dictionary to JSON
    session_data = dict(session)
    # if session_data['input_type'] == 'image':
    #     session_data['image_file_names'] = ts_functions.load4memory_image_file_names()
    #     session_data['qa_file_names'] = ts_functions.load4memory_qa_file_names()
    #     session_data['table_data'] = ''
    # elif session_data['input_type'] == 'table':
    #     session_data['time_data'] = ''
    #     session_data['image_file_names'] = ''
    #     session_data['qa_file_names'] = ''
    #     table_data = ts_functions.load4memory_table_data()
    #     # Ensure all datetime columns are converted to strings
    #     for col in table_data.columns:
    #         if pd.api.types.is_datetime64_any_dtype(table_data[col]):
    #             table_data[col] = table_data[col].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else None)

    #     session_data['table_data'] = table_data.to_dict(orient="records")

    json_data = json.dumps(_form_json_(dict(session_data)), indent=4)
    
    # Create a BytesIO object to hold the JSON data
    file_object = io.BytesIO(json_data.encode('utf-8'))
    
    # Return the file as a downloadable attachment
    return send_file(file_object, as_attachment=True, download_name='settings.json', mimetype='application/json')


@tab_save_load_bp.route('/choose_output_folder', methods=['POST'])
def choose_output_folder_route():
    global is_dialog_open

    with lock:
        if is_dialog_open:
            return jsonify({"message": "Operation in progress: Folder dialog is already open."}), 400
        is_dialog_open = True

    try:
        output = choose_output_folder()
        folder_path = output.get('path')

        if not folder_path:
            return jsonify({"message": "Operation failed: No folder selected."}), 400

        session['output_folder'] = folder_path

        return jsonify({"message": "Folder selected successfully.", "path": folder_path})

    except Exception as e:
        return jsonify({"message": f"Operation failed: {str(e)}"}), 500

    finally:
        with lock:
            is_dialog_open = False

@tab_save_load_bp.route('/load-geojson-data', methods=['POST'])
def load_geojson_data():
    file = request.files.get('file')
    if not file:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400

    if not (file.filename.endswith('.json') or file.filename.endswith('.geojson')):
        return jsonify({'status': 'error', 'message': 'Invalid file type'}), 400

    try:
        json_data = json.load(file)

        # Extracting and setting variables
        variables = {
            "data-range-min": json_data.get('settings', {}).get("data-range", {}).get("value", [-10000])[0],
            "data-range-max": json_data.get('settings', {}).get("data-range", {}).get("value", [10000])[1],
            "p_davailwin": json_data.get('settings', {}).get("p_davailwin", {}).get("value", 999),
            "outliers": json_data.get('settings', {}).get("outliers", {}).get("value", 0),
            "a1": json_data.get('settings', {}).get("p_a", {}).get("value", [-10000])[0],
            "a2": json_data.get('settings', {}).get("p_a", {}).get("value", [10000])[1],
            "a3": json_data.get('settings', {}).get("p_a", {}).get("value", [1])[2],
            "a4": json_data.get('settings', {}).get("p_a", {}).get("value", [-10000])[3],
            "a5": json_data.get('settings', {}).get("p_a", {}).get("value", [10000])[4],
            "a6": json_data.get('settings', {}).get("p_a", {}).get("value", [1])[5],
            "a7": json_data.get('settings', {}).get("p_a", {}).get("value", [-10000])[6],
            "a8": json_data.get('settings', {}).get("p_a", {}).get("value", [10000])[7],
            "a9": json_data.get('settings', {}).get("p_a", {}).get("value", [1])[8],
            "base-level": json_data.get('settings', {}).get("base-level", {}).get("value", 0.05),
            "p_fitmethod": json_data.get('settings', {}).get("p_fitmethod", {}).get("value", 2),
            "smoothing-par": json_data.get('settings', {}).get("smoothing-par", {}).get("value", 1000),
            "envelope-iterations": json_data.get('settings', {}).get("envelope-iterations", {}).get("value", 0),
            "adaptation-strength": json_data.get('settings', {}).get("adaptation-strength", {}).get("value", 2),
            "p_outststep": json_data.get('settings', {}).get("p_outststep", {}).get("value", 1),
            "seasonal-method": json_data.get('settings', {}).get("seasonal-method", {}).get("value", 1),
            "seasonal-par": json_data.get('settings', {}).get("seasonal-par", {}).get("value", 0.5),
            "season-start-method": json_data.get('settings', {}).get("season-start-method", {}).get("value", 1),
            "season-start": json_data.get('settings', {}).get("season-start", {}).get("value", [0.5])[0],
            "season-end": json_data.get('settings', {}).get("season-start", {}).get("value", [0.5])[1],
            "nodata-out": json_data.get('settings', {}).get("nodata-out", {}).get("value", -9999),
            "debug_mod": json_data.get('settings', {}).get("debug_mod", {}).get("value", 0),
            "n_core": json_data.get('settings', {}).get("n_core", {}).get("value", 1),
            "n_memory": json_data.get('settings', {}).get("n_memory", {}).get("value", 1),
            "output_folder": json_data.get('outputs', {}).get("output_folder", {}).get("value", ''),
            "input_type": json_data.get('inputs', {}).get("input_type", {}).get("value", ''),
            "num_of_data": json_data.get('inputs', {}).get("num_of_data", {}).get("value", 0),
        }

        # Store variables in session for persistence if needed
        session.update(variables)

        print(session)

        if variables['input_type'] == 'image':
            variables['time_data'] = json_data.get('inputs', {}).get("time_data", {}).get("value", [])
            ts_functions.save2menory_time_data(variables['time_data'])
            variables['image_file_names'] = json_data.get('inputs', {}).get("image_file_names", {}).get("value", [])
            ts_functions.save2menory_image_file_names(variables['image_file_names'])
            variables['qa_file_names'] = json_data.get('inputs', {}).get("qa_file_names", {}).get("value", [])
            ts_functions.save2menory_qa_file_names(variables['qa_file_names'])
        elif variables['input_type'] == 'table':        
            table_data = json_data.get('inputs', {}).get("table_data", {}).get("value", [])
            variables['table_data'] = table_data
            table_data = pd.DataFrame(table_data)
            # If the 'Date' column (or any other) needs to be converted back to datetime
            if 'Date' in table_data.columns:
                table_data['Date'] = pd.to_datetime(table_data['Date'])
            ts_functions.save2menory_table_data(table_data)
            min_t, max_t, min_y, max_y, nyear, yrstart, yrend = ts_functions.read_table_data(table_data)

            # Get the number of rows
            npt = len(table_data)

            session['yrstart'] = int(yrstart)
            session['yrend'] = int(yrend)
            session['nyear'] = int(nyear)
        
            session['xlim1'] = min_t
            session['xlim2'] = max_t
            session['ylim1'] = min_y
            session['ylim2'] = max_y

            session['col'] = table_data.shape[1] - 1
            session['row'] = 1
            session['current_col'] = 1
            session['current_row'] = 1
            session['col_start'] = 1
            session['col_end'] = table_data.shape[1] - 1
            session['row_start'] = 1
            session['row_end'] = 1

        return jsonify({'status': 'success', 'variables': variables})

    except json.JSONDecodeError:
        return jsonify({'status': 'error', 'message': 'Error parsing JSON file'}), 400
    

    