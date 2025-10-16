from flask import Blueprint, render_template, session, request, jsonify, send_file, make_response
import io
import rasterio
import json
from rasterio.warp import transform_bounds
import numpy as np
import matplotlib.cm as cm
from . import ts_functions
from PIL import Image
import pandas as pd

file_list_input_bp = Blueprint('file_list_input', __name__)

@file_list_input_bp.route('/waiting_page')
def waiting_page():
    # This will just render a waiting page with a spinner or message
    return render_template('waiting_page.html')

@file_list_input_bp.route('/upload_input_file', methods=['POST'])
def upload_input_file():

    image_file_names = []
    stack_data = []
    table_data = []

    if 'data_list' not in request.files:
        return "No file part in the request", 400

    file = request.files['data_list']

    if file.filename == '':
        return "No file selected", 400

    # Check if the file is a txt or csv file

    if file.filename.endswith('.txt'):
        file_content = file.read().decode('utf-8')  # Read the file content
        lines = file_content.splitlines()  # Split content by lines

        if len(lines) < 1:
            return "File is empty", 400

        # First line processing
        first_line = lines[0].strip().split()
        
        # Case: One integer (image file names)
        if len(first_line) == 1 and first_line[0].isdigit():
            input_type = 'imagelist'
            session['current_row'] = None
            session['current_col'] = None
            npt = int(first_line[0])
            image_file_names = [line.strip() for line in lines[1:npt + 1]]
            ts_functions.extract_dates_strlist(image_file_names)
        else:
            return "Invalid format in the first line of the file", 400

    # Handle geotif stack file
    elif file.filename.endswith('.tif') or file.filename.endswith('.tiff'):
        input_type = 'imagestack'
        with rasterio.open(file) as src:
            minx, miny, maxx, maxy = transform_bounds(src.crs, 'EPSG:4326', *src.bounds)
            ts_functions.save2bounds([minx, miny, maxx, maxy])
            ts_functions.save2geotifnodata(src.nodata)
            ts_functions.save2geotifprofile(src.profile)
            npt = src.count
            stack_data = src.read()
            stack_data = np.moveaxis(stack_data, 0, -1)
            
            band_names = []
            for i in range(1, src.count + 1):  # rasterio bands are 1-based
                desc = src.descriptions[i-1]   # description for each band
                if desc is None:
                    desc = f"Band {i}"
                band_names.append(desc)
        image_file_names = band_names
        min_t, max_t, min_y, max_y, nyear, yrstart, yrend = ts_functions.extract_image_stack(band_names, stack_data)

        session['yrstart'] = int(yrstart)
        session['yrend'] = int(yrend)
        session['nyear'] = int(nyear)
    
        session['xlim1'] = min_t
        session['xlim2'] = max_t
        session['ylim1'] = min_y
        session['ylim2'] = max_y

        session['row'] = stack_data.shape[0]
        session['col'] = stack_data.shape[1]
        session['current_col'] = 1
        session['current_row'] = 1
        session['row_start'] = 1
        session['row_end'] = stack_data.shape[0]
        session['col_start'] = 1
        session['col_end'] = stack_data.shape[1]

    # Handle table files
    elif file.filename.endswith('.csv') or file.filename.endswith('.xls') or file.filename.endswith('.xlsx'):
        input_type = 'table'
        if file.filename.endswith('.csv'):
            # Read the CSV file into a DataFrame
            table_data = pd.read_csv(file)
        elif file.filename.endswith('.xls') or file.filename.endswith('.xlsx'):
            # Read the Excel file into a DataFrame
            table_data = pd.read_excel(file)
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

    else:
        return "Invalid file format", 400

    # Return or process the time series data as needed
    session['input_type'] = input_type
    ts_functions.save2menory_image_file_names(image_file_names)
    ts_functions.save2menory_table_data(table_data)
    session['num_of_data'] = npt
    return jsonify({
        'input_type': input_type,
        'num_of_data': npt,
        'geotiff_filenames': image_file_names,
    })

@file_list_input_bp.route('/get_geotiff_info/<int:geotiff_index>')
def get_geotiff_info(geotiff_index):
    current_geotiff_paths = ts_functions.load4memory_image_file_names()
    if geotiff_index < 0 or geotiff_index >= len(current_geotiff_paths):
        return jsonify({'error': 'Invalid GeoTIFF index'}), 400

    geotiff_path = current_geotiff_paths[geotiff_index]

    try:
        with rasterio.open(geotiff_path) as src:
            # Get geographic bounds in EPSG:4326
            minx, miny, maxx, maxy = transform_bounds(src.crs, 'EPSG:4326', *src.bounds)
            width = src.width
            height = src.height

            # Return GeoTIFF metadata
            return jsonify({
                'bounds': [minx, miny, maxx, maxy],
                'width': width,
                'height': height,
                'geotiff_url': f'/generate_geotiff_image/{geotiff_index}',
            })
    except Exception as e:
        return jsonify({'error': f'Error reading GeoTIFF: {str(e)}'}), 400


@file_list_input_bp.route('/generate_geotiff_image/<int:geotiff_index>')
def generate_geotiff_image(geotiff_index):
    current_geotiff_paths = ts_functions.load4memory_image_file_names()
    if geotiff_index < 0 or geotiff_index >= len(current_geotiff_paths):
        return jsonify({'error': 'Invalid GeoTIFF index'}), 400

    geotiff_path = current_geotiff_paths[geotiff_index]

    try:
        with rasterio.open(geotiff_path) as src:
            band1 = src.read(1).astype(np.float32)  # Read the first band
            nodata_value = src.nodata

            if nodata_value is not None:
                band1 = np.where(band1 == nodata_value, np.nan, band1)

            # Normalize the band data for display (0-255 range)
            min_val = np.nanmin(band1)
            max_val = np.nanmax(band1)

            normalized_band = (band1 - min_val) / (max_val - min_val) * 255
            normalized_band = np.nan_to_num(normalized_band, nan=0).astype(np.uint8)

            # Create a color map using matplotlib
            cmap = cm.get_cmap('jet')  # You can choose other colormaps if you prefer
            rgba_image = cmap(normalized_band)  # Apply the colormap

            # Convert the matplotlib RGBA image to a PIL image
            rgba_image = (rgba_image * 255).astype(np.uint8)
            pil_image = Image.fromarray(rgba_image, 'RGBA')

            # Save the image as PNG to a bytes buffer
            img_io = io.BytesIO()
            pil_image.save(img_io, 'PNG')
            img_io.seek(0)

            # Send the image as a PNG response
            return send_file(img_io, mimetype='image/png')

    except Exception as e:
        return jsonify({'error': f'Error generating GeoTIFF image: {str(e)}'}), 400

@file_list_input_bp.route('/calculate_row_col', methods=['POST'])
def calculate_row_col():
    # Reset session row/col (optional)
    session['current_row'] = None
    session['current_col'] = None

    data = request.get_json(silent=True) or {}
    input_type = data.get('input_type', 'imagelist')  # 'imagelist' | 'imagestack'
    geotiff_index = data.get('geotiff_index')
    lat = data.get('lat')
    lng = data.get('lng')

    # Basic validation
    if lat is None or lng is None:
        return jsonify({'error': 'Missing required parameters: lat/lng'}), 400

    # Branch by input type
    if input_type == 'imagelist':
        # Validate index
        current_geotiff_paths = ts_functions.load4memory_image_file_names()
        try:
            geotiff_index = int(geotiff_index)
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid geotiff_index'}), 400

        if geotiff_index < 0 or geotiff_index >= len(current_geotiff_paths):
            return jsonify({'error': 'Invalid GeoTIFF index'}), 400

        geotiff_path = current_geotiff_paths[geotiff_index]

        try:
            with rasterio.open(geotiff_path) as src:
                # Transform WGS84 lon/lat -> dataset CRS x/y
                if src.crs is None:
                    return jsonify({'error': 'Dataset has no CRS'}), 400

                xs, ys = rio_transform('EPSG:4326', src.crs, [lng], [lat])
                x, y = xs[0], ys[0]

                # Quick bounds check in dataset CRS
                left, bottom, right, top = src.bounds
                if not (left <= x <= right and bottom <= y <= top):
                    return jsonify({'error': 'Point is outside the GeoTIFF bounds'}), 400

                # Rasterio-native pixel index (row, col)
                row, col = src.index(x, y)

                # Image dimensions
                height, width = src.height, src.width

                # Clamp to valid range (edge clicks can land exactly on width/height)
                row = int(np.clip(row, 0, height - 1))
                col = int(np.clip(col, 0, width - 1))

                # Save to session (1-based for UI, if you prefer)
                session['row'] = height
                session['col'] = width
                session['current_row'] = row + 1
                session['current_col'] = col + 1

                return jsonify({'row': row + 1, 'col': col + 1})

        except Exception as e:
            return jsonify({'error': f'Error calculating row/col (imagelist): {str(e)}'}), 500

    elif input_type == 'imagestack':
        # Use in-memory stack + bounds
        try:
            ym3 = ts_functions.load4ym3()  # shape (H, W, Z)
            bounds = ts_functions.load4bounds()  # [minX, minY, maxX, maxY] in EPSG:4326
        except Exception as e:
            return jsonify({'error': f'Error loading stack/bounds: {str(e)}'}), 500

        if ym3 is None or bounds is None:
            return jsonify({'error': 'Stack or bounds not available'}), 500

        H, W, *_ = ym3.shape
        minx, miny, maxx, maxy = bounds  # assumed WGS84

        # Check within bounds (inclusive on min; exclusive on max to avoid off-by-one)
        if not (minx <= lng < maxx and miny <= lat < maxy):
            return jsonify({'error': 'Point is outside the stack bounds'}), 400

        # Pixel size
        xres = (maxx - minx) / float(W)
        yres = (maxy - miny) / float(H)

        # Compute 0-based indices (top-left origin)
        col = int((lng - minx) / xres)
        row = int((maxy - lat) / yres)

        # Clamp to valid range
        row = int(np.clip(row, 0, H - 1))
        col = int(np.clip(col, 0, W - 1))

        # Persist to session (optional)
        session['row'] = H
        session['col'] = W
        session['current_row'] = row + 1
        session['current_col'] = col + 1

        return jsonify({'row': row + 1, 'col': col + 1})

    else:
        return jsonify({'error': f'Unknown input_type: {input_type}. Upload a GeoTIFF or file list first.'}), 400


def percentile_stretch(arr, nodata=None):
    a = arr.astype("float32")
    if nodata is not None:
        a[a == nodata] = np.nan
    mask = np.isfinite(a)
    if not np.any(mask):
        return np.zeros_like(a, dtype="uint8")
    lo = np.nanpercentile(a[mask], 2)
    hi = np.nanpercentile(a[mask], 98)
    if hi <= lo:
        return np.zeros_like(a, dtype="uint8")
    a = np.clip((a - lo) / (hi - lo), 0, 1)
    a = np.nan_to_num(a, nan=0)   # Replace NaN with 0 safely
    return a

@file_list_input_bp.route("/get_vi_stack_info/<int:index>")
def get_vi_stack_info(index):
    H, W, Z = ts_functions.load4ym3().shape
    return jsonify({
        "bounds": ts_functions.load4bounds(),       # [minX, minY, maxX, maxY]
        "num_slices": int(Z),
        "render_base_url": "/render_vi_slice",
        "has_dates": False,            # set True and add "dates" if you have them
        "dates": None,
        "nodata": ts_functions.load4geotifnodata()
    })

@file_list_input_bp.route("/render_vi_slice")
def render_vi_slice():
    i = request.args.get("i", type=int)       # <-- selected stack index
    t = request.args.get("t", type=int)       # 1-based slice
    if i is None or t is None:
        abort(400, "Provide ?i=<stack index>&t=<1-based slice index>")

    ym3 = ts_functions.load4ym3()            # <-- load the correct stack
    nodata = ts_functions.load4geotifnodata()

    if nodata is not None:
        band1 = np.where(band1 == nodata_value, np.nan, band1)

    band = ym3[:, :, i]

    out8 = percentile_stretch(band, nodata=nodata)
    # Create a color map using matplotlib
    cmap = cm.get_cmap('jet')  # You can choose other colormaps if you prefer
    rgba_image = cmap(out8)  # Apply the colormap
    rgba_image = (rgba_image * 255).astype(np.uint8)
    img = Image.fromarray(rgba_image, 'RGBA')
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@file_list_input_bp.route('/load_input_Files', methods=['POST'])
def load_input_Files():
    """
    Loads inputs and prepares a small subwindow around the selected pixel.

    Conventions used here:
      - current_row/current_col in session are 1-based (UI-friendly).
      - We convert to 0-based when slicing arrays (Python/raster convention).
    """
    try:
        input_type = session.get('input_type', None)

        # You always need a pinned pixel (row/col) for both imagelist and imagestack
        cur_row_1b = session.get('current_row', None)
        cur_col_1b = session.get('current_col', None)
        if input_type in ('imagelist', 'imagestack') and (cur_row_1b is None or cur_col_1b is None):
            return jsonify({'error': 'Pin a location on the map.'}), 400

        # ---- imagelist: your original logic (fixed + clarified) -----------------
        if input_type == 'imagelist':
            num_of_data = session.get('num_of_data', None)
            image_file_names = ts_functions.load4memory_image_file_names()
            qa_file_names = ts_functions.load4memory_qa_file_names()
            landcover_file_name = None

            # Basic consistency checks
            if qa_file_names and (len(qa_file_names) != len(image_file_names)):
                return jsonify({'error': "Input files and QA files are not consistent."}), 400

            # NOTE: 'row' and 'col' stored in session are total image HEIGHT/WIDTH (1-based in your code)
            # Convert to 0-based max indices
            height_max_idx = (session.get('row', None) or 0) - 1
            width_max_idx  = (session.get('col', None) or 0) - 1

            # Convert current position to 0-based for slicing
            current_row = cur_row_1b - 1
            current_col = cur_col_1b - 1

            # Build a +-10 px subwindow, clamped to image bounds
            row_off = max(current_row - 10, 0)
            row_end = min(current_row + 10, height_max_idx)
            sub_height = row_end - row_off + 1

            col_off = max(current_col - 10, 0)
            col_end = min(current_col + 10, width_max_idx)
            sub_width = col_end - col_off + 1

            # Save 1-based window bounds to session (if your downstream expects that)
            session['row_start'] = row_off + 1
            session['row_end']   = row_end + 1
            session['col_start'] = col_off + 1
            session['col_end']   = col_end + 1

            # Time vector → min/max (dates come back as strings)
            tv_yyyymmdd, tv_yyyydoy, nyear, yrstart, yrend = ts_functions.read_time_vector_data(image_file_names)
            session['yrstart'] = int(yrstart)
            session['yrend']   = int(yrend)
            session['nyear']   = int(nyear)

            # Build ym3/wm3 from disk for the subwindow; returns plotting ranges
            min_y, max_y, min_t, max_t = ts_functions.read_images(
                image_file_names, qa_file_names, landcover_file_name,
                num_of_data, row_off, col_off, sub_height, sub_width
            )

            session['xlim1'] = min_t
            session['xlim2'] = max_t
            session['ylim1'] = min_y
            session['ylim2'] = max_y

        elif input_type == 'imagestack':

            # Require a pinned pixel (1-based from your UI)
            cur_row_1b = session.get('current_row', None)
            cur_col_1b = session.get('current_col', None)
            if cur_row_1b is None or cur_col_1b is None:
                return jsonify({'error': 'Pin a location on the map.'}), 400

            ym3 = ts_functions.load4ym3()           # shape (H, W, Z)
            if ym3 is None:
                return jsonify({'error': 'In-memory stack is not available.'}), 500

            H, W, Z = ym3.shape
            nodata = ts_functions.load4geotifnodata()

            # Convert to 0-based and clamp to valid range
            r0 = int(cur_row_1b) - 1
            c0 = int(cur_col_1b) - 1
            r0 = int(np.clip(r0, 0, H - 1))
            c0 = int(np.clip(c0, 0, W - 1))

            # Persist dims and current pixel back to session (1-based for UI)
            session['row'] = H
            session['col'] = W
            session['current_row'] = r0 + 1
            session['current_col'] = c0 + 1

            min_t = session.get('xlim1')
            max_t = session.get('xlim2')
            min_y = session.get('ylim1')
            max_y = session.get('ylim2')

        # ---- table/csv (your existing path; kept as-is) --------------------------
        elif input_type in ('table', 'csv'):
            min_t = session.get('xlim1')
            max_t = session.get('xlim2')
            min_y = session.get('ylim1')
            max_y = session.get('ylim2')

        else:
            return jsonify({'error': 'Unknown input type. Upload inputs first.'}), 400

        return jsonify({
            "message": 'Data Loaded.',
            "min_y": float(min_y) if min_y is not None else None,
            "max_y": float(max_y) if max_y is not None else None,
            "min_t": min_t,
            "max_t": max_t
        }), 200

    except Exception as e:
        return jsonify({'error': f'Error loading data: {str(e)}'}), 500




@file_list_input_bp.route('/upload_qa_file', methods=['POST'])
def upload_qa_file():

    qa_file_names = []

    if 'quality_list' not in request.files:
        return "No file part in the request", 400

    file = request.files['quality_list']

    if file.filename == '':
        return "No file selected", 400

    # Check if the file is a txt or table file
    input_type = session.get('input_type', '')
    if input_type == 'imagelist':
        file_content = file.read().decode('utf-8')  # Read the file content
        lines = file_content.splitlines()  # Split content by lines

        if len(lines) < 1:
            return "File is empty", 400

        # First line processing
        first_line = lines[0].strip().split()
        
        # Case: One integer (image file names)
        if len(first_line) == 1 and first_line[0].isdigit():
            npt = int(first_line[0])
            qa_file_names = [line.strip() for line in lines[1:npt + 1]]
        else:
            return "Invalid format in the first line of the file", 400

    # Handle geotif stack file
    elif input_type == 'imagestack':
        with rasterio.open(file) as src:
            
            stack_data = src.read()
            stack_data = np.moveaxis(stack_data, 0, -1)
            
            band_names = []
            for i in range(1, src.count + 1):  # rasterio bands are 1-based
                desc = src.descriptions[i-1]   # description for each band
                if desc is None:
                    desc = f"Band {i}"
                band_names.append(desc)
        ym_wm_check = ts_functions.extract_qa_stack(band_names, stack_data)
        if ym_wm_check == 1:
            qa_file_names = band_names

    # Handle table files
    elif input_type == 'table':
        file_content = file.read().decode('utf-8')
        # not finish yet!!!!!!!!!
        # Process CSV file content as needed
        return file_content[:100]  # Just as a placeholder to display first 100 chars

    else:
        return "Invalid file format", 400

    # Return or process the time series data as needed
    ts_functions.save2menory_qa_file_names(qa_file_names)
    return jsonify({
        'geotiff_filenames': qa_file_names
    })


