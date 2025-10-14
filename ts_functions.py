"""
TSPreProcessing Module

Author: Zhanzhang Cai
Date: September 2024

Description:
This script contains the TSPreProcessing class used for reading and processing
time vector data from a file. The file is expected to have the first line as the number
of time steps, followed by the time steps in YYYYMMDD format. The script also includes
error handling for various scenarios, such as non-numeric header variables or
mismatched number of time steps. Error messages are displayed using a simple GUI message box.
"""
import numpy as np
from datetime import datetime, timedelta, date
import rasterio
import timesat
import pandas as pd
from typing import List, Tuple
import re


image_file_names = ''
qa_file_names = ''
table_data = ''
tv_yyyymmdd = None
tv_yyyydoy = None
ym3 = None
wm3 = None
lc3 = None


def save2menory_image_file_names(x):
    global image_file_names
    image_file_names = x

def load4memory_image_file_names():
    global image_file_names
    return image_file_names

def load4ym3():
    global ym3
    return ym3

def load4wm3():
    global wm3
    return wm3

def load4lc3():
    global lc3
    return lc3

def save2bounds(x):
    global bounds
    bounds = x

def load4bounds():
    global bounds
    return bounds

def save2geotifnodata(x):
    global geotifnodata
    geotifnodata = x

def load4geotifnodata():
    global geotifnodata
    return geotifnodata

def save2geotifprofile(x):
    global geotifprofile
    geotifprofile = x

def load4geotifprofile():
    global geotifprofile
    return geotifprofile

def save2menory_qa_file_names(x):
    global qa_file_names
    qa_file_names = x

def load4memory_qa_file_names():
    global qa_file_names
    return qa_file_names

def save2menory_table_data(x):
    global table_data
    table_data = x

def load4memory_table_data():
    global table_data
    return table_data

def save2array_params(x):
    global array_params
    array_params = x

def load4array_params():
    global array_params
    return array_params

def read_time_vector_data(lines):
    global tv_yyyymmdd, tv_yyyydoy

    # Check if file exists
    try:
        """
        Extract dates from band names.
        Returns two aligned lists (same length):
          - tv_yyyymmdd: [YYYYMMDD, ...]
          - tv_yyyydoy:  [YYYYDOY, ...]
        """
        tv_yyyymmdd = []
        tv_yyyydoy = []

        patterns = [
            r"(\d{4})(\d{2})(\d{2})",          # YYYYMMDD
            r"(\d{4})(\d{3})",                 # YYYYDOY
            r"(\d{4})[-_](\d{2})[-_](\d{2})",  # YYYY-MM-DD or YYYY_MM_DD
            r"(\d{4})[-_](\d{3})",             # YYYY-DOY or YYYY_DOY
        ]

        for name in lines:
            parsed_date = None

            for pat in patterns:
                m = re.search(pat, name)
                if not m:
                    continue

                groups = m.groups()
                try:
                    if len(groups) == 3:  # YYYY MM DD
                        year, month, day = map(int, groups)
                        parsed_date = datetime(year, month, day).date()
                    elif len(groups) == 2 and len(groups[1]) == 3:  # YYYY + DOY
                        year, doy = int(groups[0]), int(groups[1])
                        parsed_date = (datetime(year, 1, 1) + timedelta(days=doy - 1)).date()
                except Exception:
                    parsed_date = None
                break

            if parsed_date:
                # YYYYMMDD
                yyyymmdd = int(parsed_date.strftime("%Y%m%d"))
                # YYYYDOY
                yyyydoy = int(parsed_date.strftime("%Y%j"))
                tv_yyyymmdd.append(yyyymmdd)
                tv_yyyydoy.append(yyyydoy)
            else:
                tv_yyyymmdd.append(None)
                tv_yyyydoy.append(None)

        # Convert lists to numpy arrays
        tv_yyyymmdd = np.array(tv_yyyymmdd, dtype=int)
        tv_yyyydoy = np.array(tv_yyyydoy, dtype=int)

        # Extract year and calculate the number of unique years from YYYYMMDD format
        yv = tv_yyyymmdd // 10000  # Extract year from YYYYMMDD (integer division by 10000)
        yrstart = np.min(yv)  # First year
        yrend = np.max(yv)  # First year
        nyear = np.max(yv) - yrstart + 1  # Number of unique years (inclusive)

        return tv_yyyymmdd, tv_yyyydoy, nyear, yrstart, yrend

    except FileNotFoundError:
        return None, None

def extract_dates_strlist(band_names: List[str], input_ym3: np.ndarray):
    global ym3, wm3, lc3, tv_yyyymmdd, tv_yyyydoy

    # Initialize 3D arrays
    ym3 = np.array(input_ym3, dtype=np.float32, copy=True)
    wm3 = np.ones_like(ym3, dtype=np.float32)
    lc3 = np.ones(ym3.shape[:2], dtype=np.uint8)

    tv_yyyymmdd, tv_yyyydoy, nyear, yrstart, yrend = read_time_vector_data(band_names)
    # 假设 tv_yyyymmdd 是一个包含日期的数组
    min_t = str(tv_yyyymmdd.min())  # 获取最小值并转换为字符串
    max_t = str(tv_yyyymmdd.max())  # 获取最大值并转换为字符串

    # 将 'YYYYMMDD' 格式转换为 'YYYY-MM-DD' 格式
    min_t = f"{min_t[:4]}-{min_t[4:6]}-{min_t[6:]}"
    max_t = f"{max_t[:4]}-{max_t[4:6]}-{max_t[6:]}"

    min_y = float(np.nanmin(ym3))
    max_y = float(np.nanmax(ym3))

    return min_t, max_t, min_y, max_y, nyear, yrstart, yrend

def read_image_list_file(img_file_name,lines):
    # Open and read the text file

    try:
        with open(img_file_name, 'r') as file:
            lines = file.readlines()
    except:
        0
    
    # First line contains the number of images
    num_images = int(lines[0].strip())

    # From the second line onwards, it's the image paths
    image_paths = [line.strip() for line in lines[1:]]

    if num_images > 0 and len(image_paths) > 0:
        # Load the first image
        first_image_path = image_paths[0]
        with rasterio.open(first_image_path) as img:
            # Get the size of the first image (width, height)
            n_col = img.width  # Number of columns (width)
            n_row = img.height  # Number of rows (height)
    
        return n_col, n_row , num_images, image_paths
    else:
        # Return None or an appropriate response if no images are listed
        return 0, 0, 0, []


def read_table_data(df):
    global ym3, wm3, lc3, tv_yyyymmdd, tv_yyyydoy

    # Identify the first column dynamically
    first_col_name = df.columns[0]

    # Convert the first column to datetime
    dates = pd.to_datetime(df[first_col_name])

    # Convert dates to the desired format yyyyDOY
    tv_yyyydoy = dates.dt.strftime('%Y%j').tolist()

    # Convert the first column to the desired format (assuming it contains dates)
    tv_yyyymmdd = dates.dt.strftime('%Y%m%d').tolist()

    # Get the number of rows
    npt = len(df)

    col = df.shape[1] - 1

    # Initialize 3D arrays
    ym3 = np.zeros((col, 1, npt), dtype=np.float32)
    wm3 = np.ones((col, 1, npt), dtype=np.float32)
    lc3 = np.ones((col, 1), dtype=np.float32)

    # Save data from the second column to the end into ym3
    # Transpose the slice to align with the shape (col, 1, npt)
    ym3[:, 0, :] = df.iloc[:, 1:].T.values.astype(np.float32)

    # Convert lists to numpy arrays
    tv_yyyymmdd = np.array(tv_yyyymmdd, dtype=int)
    tv_yyyydoy = np.array(tv_yyyydoy, dtype=int)

    # Extract year and calculate the number of unique years from YYYYMMDD format
    yv = tv_yyyymmdd // 10000  # Extract year from YYYYMMDD (integer division by 10000)
    yrstart = np.min(yv)  # First year
    yrend = np.max(yv)  # First year
    nyear = np.max(yv) - yrstart + 1  # Number of unique years (inclusive)

    # 假设 tv_yyyymmdd 是一个包含日期的数组
    min_t = str(tv_yyyymmdd.min())  # 获取最小值并转换为字符串
    max_t = str(tv_yyyymmdd.max())  # 获取最大值并转换为字符串

    # 将 'YYYYMMDD' 格式转换为 'YYYY-MM-DD' 格式
    min_t = f"{min_t[:4]}-{min_t[4:6]}-{min_t[6:]}"
    max_t = f"{max_t[:4]}-{max_t[4:6]}-{max_t[6:]}"

    min_y = float(np.nanmin(ym3))
    max_y = float(np.nanmax(ym3))


    return min_t, max_t, min_y, max_y, nyear, yrstart, yrend




def read_images(image_file_names, qa_file_names, landcover_file_name, npt, row_off, col_off, sub_height, sub_width):
    global ym3, wm3, lc3, tv_yyyymmdd
    """
    Function to read GeoTIFF data using rasterio and process them into 3D arrays.
    
    Parameters:
        row_pin (int): Start row.
        col_pin (int): Stop row.
        filename (str): Path to the list of sensor data GeoTIFF files.
        weightname (str): Path to the list of weight GeoTIFF files (optional).
        landcovername (str): Path to the landcover GeoTIFF file (optional).
        
    Returns:
        npt (int): Number of data points.
        ym3 (numpy.ndarray): 3D array of time-series data.
        wm3 (numpy.ndarray): 3D array of weight data.
        lc3 (numpy.ndarray): 3D array of landcover data (if applicable).
        err (int): Error code (0 if no error).
    """
    err = 0
    # Initialize 3D arrays
    ym3 = np.zeros((sub_height, sub_width, npt), dtype=np.float32)
    wm3 = np.ones((sub_height, sub_width, npt), dtype=np.float32)
    lc3 = np.ones((sub_height, sub_width), dtype=np.float32)
    # Define the window range
    window = rasterio.windows.Window(row_off, col_off, sub_height, sub_width)
    
    # 假设 tv_yyyymmdd 是一个包含日期的数组
    min_t = str(tv_yyyymmdd.min())  # 获取最小值并转换为字符串
    max_t = str(tv_yyyymmdd.max())  # 获取最大值并转换为字符串

    # 将 'YYYYMMDD' 格式转换为 'YYYY-MM-DD' 格式
    min_t = f"{min_t[:4]}-{min_t[4:6]}-{min_t[6:]}"
    max_t = f"{max_t[:4]}-{max_t[4:6]}-{max_t[6:]}"

    # Read sensor data
    for i, sensor_file in enumerate(image_file_names):
        with rasterio.open(sensor_file) as src:
            # Read the data for the window and assign it to the appropriate slice in the 3D array
            temp_data = src.read(1, window=window)
            ym3[:, :, i] = temp_data.T
            min_y = float(np.nanmin(ym3))
            max_y = float(np.nanmax(ym3))
    
    # Read weight data (if applicable)
    if qa_file_names:
        for i, weight_file in enumerate(qa_file_names):
            with rasterio.open(weight_file) as src:
                temp_data = src.read(1, window=window)
                wm3[:, :, i] = temp_data.T

    # Read landcover data (if applicable)
    if landcover_file_name:
        with rasterio.open(landcover_file_name) as src:
            temp_data = src.read(1, window=window)
            lc3 = temp_data.T

    return min_y, max_y, min_t, max_t


def raw_single_extraction(current_row, current_col):
    global ym3, wm3, lc3, tv_yyyymmdd, tv_yyyydoy

    raw_y = ym3[current_row:current_row+1, current_col:current_col+1, :]
    raw_w = wm3[current_row:current_row+1, current_col:current_col+1, :]
    raw_lc = lc3[current_row:current_row+1, current_col:current_col+1]

    return raw_y, raw_w, raw_lc, tv_yyyymmdd, tv_yyyydoy


def ts_single_run(raw_y, raw_w, raw_lc, yrstart, nyear, z, 
    p_outststep, 
    p_ignoreday, p_ylu, p_a, p_printflag, p_fitmethod, p_smooth, p_nodata, p_outlier, p_nenvi, p_wfactnum,
    p_startmethod, p_startcutoff, p_low_percentile, p_fillbase, p_hrvppformat, p_seasonmethod, p_seapar):
    global tv_yyyymmdd, tv_yyyydoy

    p_outindex = np.arange(1, nyear*365+1)[::p_outststep]
    p_outindex_num = len(p_outindex)
    print('TIMESAT run start')

    # Replace NaN values with -9999
    raw_y = np.nan_to_num(raw_y, nan=p_ylu[0]-1)

    lc = np.ones(raw_y.shape[:2], dtype=np.uint8)
    p_nclasses = 1 # need to modify later
    landuse = np.ones(255, dtype='uint8')


    # import pickle, os
    # from pathlib import Path

    # # Toggle this manually
    # SAVE_TIMESAT_INPUTS = True   # set False in production

    # def dump_timesat_inputs(**kwargs):
    #     if not SAVE_TIMESAT_INPUTS:
    #         return None
    #     try:
    #         dump_dir = Path("timesat_inputs")
    #         dump_dir.mkdir(exist_ok=True)
    #         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    #         path = dump_dir / f"inputs_{timestamp}.pkl"
    #         with open(path, "wb") as f:
    #             pickle.dump(kwargs, f, protocol=pickle.HIGHEST_PROTOCOL)
    #         print(f"[debug] Saved inputs to {path}")
    #         return str(path)
    #     except Exception as e:
    #         print(f"[debug] Failed to save inputs: {e}")
    #         return None

    # if SAVE_TIMESAT_INPUTS:
    #     dump_timesat_inputs(
    #         nyr=nyear, vi=raw_y, qa=raw_w, td=tv_yyyydoy,
    #         lc=lc, p_nclasses=p_nclasses, landuse=landuse, p_outindex=p_outindex,
    #         p_ignoreday=p_ignoreday, p_ylu=p_ylu, p_printflag=p_printflag,
    #         p_fitmethod=p_fitmethod, p_smooth=p_smooth, p_nodata=p_nodata,
    #         p_outlier=p_outlier, p_nenvi=p_nenvi, p_wfactnum=p_wfactnum,
    #         p_startmethod=p_startmethod, p_startcutoff=p_startcutoff,
    #         p_lpbase=p_low_percentile, p_fillbase=p_fillbase,
    #         p_hrvppformat=p_hrvppformat, p_seasonmethod=p_seasonmethod,
    #         p_seapar=p_seapar, nimg=z, p_outindex_num=p_outindex_num, row=1, col=1
    #     )

    vpp, vppqa, nseason, yfit, yfitqa, seasonfit, tseq = timesat.tsf2py(
        nyear, raw_y, raw_w, tv_yyyydoy, lc, p_nclasses, landuse, p_outindex,
        p_ignoreday, p_ylu, p_printflag, p_fitmethod, p_smooth, p_nodata, p_outlier, p_nenvi, p_wfactnum,
        p_startmethod, p_startcutoff, p_low_percentile, p_fillbase, p_hrvppformat, p_seasonmethod, p_seapar,
        1, 1, z, p_outindex_num)

    daily_timestep = []
    for year in range(yrstart, yrstart + nyear):
        for day in range(365):
            # Start at January 1st and add `day` days to ensure only 365 days
            daily_timestep.append(datetime(year, 1, 1) + timedelta(days=day))
    daily_timestep = daily_timestep[::p_outststep]
    print('TIMESAT run OK!!!!!')

    return vpp, vppqa, nseason, yfit, yfitqa, seasonfit, daily_timestep


def ts_full_run(raw_y, raw_w, raw_lc, yrstart, nyear, z, 
    p_outststep, 
    p_ignoreday, p_ylu, p_a, p_printflag, p_fitmethod, p_smooth, p_nodata, p_outlier, p_nenvi, p_wfactnum,
    p_startmethod, p_startcutoff, p_low_percentile, p_fillbase, p_hrvppformat, p_seasonmethod, p_seapar):
    global tv_yyyymmdd, tv_yyyydoy

    p_outindex = np.arange(1, nyear*365+1)[::p_outststep]
    p_outindex_num = len(p_outindex)
    print('TIMESAT run start')

    # Replace NaN values with -9999
    raw_y = np.nan_to_num(raw_y, nan=p_ylu[0]-1)

    vpp, vppqa, nseason, yfit, yfitqa, seasonfit, tseq = timesat.tsfprocess(
        nyear, raw_y, raw_w, tv_yyyydoy, lc, p_nclasses, landuse, p_outindex,
        p_ignoreday, p_ylu, p_printflag, p_fitmethod, p_smooth, p_nodata, p_outlier, p_nenvi, p_wfactnum,
        p_startmethod, p_startcutoff, p_low_percentile, p_fillbase, p_hrvppformat, p_seasonmethod, p_seapar,
        1, 1, z, p_outindex_num)

    daily_timestep = []
    for year in range(yrstart, yrstart + nyear):
        for day in range(365):
            # Start at January 1st and add `day` days to ensure only 365 days
            daily_timestep.append(datetime(year, 1, 1) + timedelta(days=day))
    daily_timestep = daily_timestep[::p_outststep]
    print('TIMESAT run OK!!!!!')

    return vpp, vppqa, nseason, yfit, yfitqa, seasonfit, daily_timestep

def vpp_to_table(vpp, yrstart, nodata_out, fit_method_name):
    vpp[vpp == nodata_out] = np.nan
    vpp_reshaped = vpp.reshape(-1, 13)

    # selected_column_0 = vpp_reshaped[:, 0]
    # date_column = [map_day_to_date(day) for day in selected_column_0]
    # ordinal_dates = [date.toordinal() for date in date_column]
    # vpp_reshaped[:, 0] = ordinal_dates

    

    vpp_list = vpp_reshaped.tolist()
    vpp_list = [[None if np.isnan(x) else x for x in row] for row in vpp_list]
    vpp_list = process_vpp_list_dates(vpp_list)

    sos_x = [row[0] for row in vpp_list]
    sos_y = [row[1] for row in vpp_list]
    eos_x = [row[3] for row in vpp_list]
    eos_y = [row[4] for row in vpp_list]

    vpp_list = process_vpp_list_significant(vpp_list)

    # form final table
    periods = [f'{yrstart + i//2}-s{i%2 + 1}' for i in range(len(vpp_list))]
    for i in range(len(vpp_list)):
        vpp_list[i] = [periods[i]] + vpp_list[i]

    new_column = [fit_method_name] + ['' for _ in range(len(vpp_list) - 1)]

    for i in range(len(vpp_list)):
        vpp_list[i] = [new_column[i]] + vpp_list[i]

    return vpp_list, sos_x, sos_y, eos_x, eos_y


def round_to_significant_digits(value, digits=4):
    # Handle the case if value is None or NaN
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return value
    if isinstance(value, (int, float)):
        # Round to the desired number of significant digits
        return float(f"{value:.{digits}g}")
    if isinstance(value, (datetime, date)):  # Check if the value is a date or datetime
        return value.date().strftime('%Y-%m-%d')  # Format as 'yyyy-mm-dd'
    return value  # Return the original value if it's not a number

def process_vpp_list_significant(vpp_list):
    # Walk through each row and column
    for row in vpp_list:
        for i in range(len(row)):
            # Apply rounding to numeric elements
            row[i] = round_to_significant_digits(row[i])
    return vpp_list

def process_vpp_list_dates(vpp_list):
    # Walk through each row and specific columns [0, 3, 8]
    for row in vpp_list:
        for col in [0, 3, 8]:
            if row[col] is not None:
                row[col] = convert_to_date(row[col])
    return vpp_list

def convert_to_date(value):
    # Handle the None case or invalid data
    if value is None:
        return None
    try:
        # Extract year and day of the year
        year = int(value // 1000) + 2000
        day_of_year = value % 1000
        # Calculate the date starting from January 1st of the given year
        date_out = datetime(year, 1, 1) + timedelta(days=day_of_year - 1)
        return date_out
    except:
        return None  # In case of invalid data