from flask import Blueprint, render_template, session, request, jsonify
import plotly
import plotly.graph_objs as go
import numpy as np
from . import ts_functions
import pandas as pd
import json
import datetime

tab_settings_bp = Blueprint('tab_settings', __name__)

# Default parameter values
default_params = {
    "time_list": '',
    "image_list_file": '',
    "quality_list_file": '',
    "csv_file": '',
    # "image_file_names": '',
    # "qa_file_names": '',
    "output_folder": '',
    "num_of_data": None,
    "p_outststep": 5,
    "p_ignoreday": 365,
    "data-range-min": -10000,
    "data-range-max": 10000,
    "p_davailwin": 999,
    "a1": -10000,
    "a2": 10000,
    "a3": 1,
    "a4": -10000,
    "a5": 10000,
    "a6": 1,
    "a7": -10000,
    "a8": 10000,
    "a9": 1,
    "debug_mod": 0, 
    "p_fitmethod": 0,
    "fit-dl": 0,
    "fit-dlsp": 0,
    "fit-sp": 0, 
    "smoothing-par": 1000, 
    "p_nodata": -9999, 
    "outliers": 0, 
    "envelope-iterations": 1, 
    "adaptation-strength": 2,
    "season-start-method": 1, 
    "season-start": 0.5,
    "season-end": 0.5, 
    "base-level": 0.05, 
    "p_fillbase": 1, 
    "p_hrvppformat": 1,
    "seasonal-method": 1, 
    "seasonal-par": 0.5,
    "seasonStartStop": 0,
    "coarseseason": 0,
    "xlim1": None,
    "xlim2": None,
    "ylim1": None,
    "ylim2": None,
    "nodata-out": -9999,
    "xTick": 0,
    "n_core": 1,
    "n_memory": 1
}

def load4array_params():
    global ARRAY_PARAMS
    return ARRAY_PARAMS

def _build_array_params_from_defaults(defaults):
    return {
        'p_fitmethod': np.full(255, defaults.get('p_fitmethod', 0), dtype='uint8'),
        'p_smooth': np.full(255, defaults.get('smoothing-par', 1000), dtype='float64'),
        'p_nenvi': np.full(255, defaults.get('envelope-iterations', 1), dtype='uint8'),
        'p_wfactnum': np.full(255, defaults.get('adaptation-strength', 2), dtype='float64'),
        'p_startmethod': np.full(255, defaults.get('season-start-method', 1), dtype='uint8'),
        'p_startcutoff': np.full((255, 2),
                                 [defaults.get('season-start', 0.5), defaults.get('season-end', 0.5)],
                                 dtype='float64', order='F'),
        'p_low_percentile': np.full(255, defaults.get('base-level', 0.05), dtype='float64'),
        'p_fillbase': np.full(255, defaults.get('p_fillbase', 0), dtype='uint8'),
        'p_seasonmethod': np.full(255, defaults.get('seasonal-method', 1), dtype='uint8'),
        'p_seapar': np.full(255, defaults.get('seasonal-par', 0.5), dtype='float64'),
    }

@tab_settings_bp.route('/initialize_session', methods=['POST'])
def initialize_session():
    global ARRAY_PARAMS
    # init scalars per session (fine to keep in session)
    for k, v in default_params.items():
        session[k] = v
    # init arrays in global (single-user local)
    ARRAY_PARAMS = _build_array_params_from_defaults(default_params)
    ts_functions.save2array_params(ARRAY_PARAMS)
    return '', 204


# 更新变量并生成曲线图
@tab_settings_bp.route("/update_plot", methods=["POST"])
def update_plot():
    global ARRAY_PARAMS
    # 确保所有参数都从 session 中获取（即使只更新一个参数）
    col_start = session.get('col_start', 1) - 1
    col_end = session.get('col_end', 1) - 1
    row_start = session.get('row_start', 1) - 1
    row_end = session.get('row_end', 1) - 1

    current_col = session.get('current_col', 1) - 1
    current_row = session.get('current_row', 1) - 1
    yrstart = session.get('yrstart', 2015)
    yrend = session.get('yrend', 2015)
    nyear = session.get('nyear', 0)
    num_of_data = session.get('num_of_data', 0)

    # Retrieve the data sent from the frontend
    data = request.get_json()

    # Update session parameters based on user input
    # Check and update the session for the specific parameter sent
    for key, value in data.items():
        if key in session:
            # Update session with new value
            session[key] = value
        else:
            print(f"Warning: {key} is not found in session.")

    # methods
    fit_dl = session.get('fit-dl')
    fit_dlsp = session.get('fit-dlsp')
    fit_sp = session.get('fit-sp')

    p_outststep = session.get('p_outststep')
    p_ignoreday = session.get('p_ignoreday')
    p_ylu = [session.get('data-range-min'), session.get('data-range-max')]
    p_a = [session.get('a1'),session.get('a2'),session.get('a3'),session.get('a4'),session.get('a5'),session.get('a6'),session.get('a7'),session.get('a8'),session.get('a9')]

    p_printflag = int(session.get('debug_mod'))

    p_hrvppformat = session.get('p_hrvppformat')
    p_nodata = session.get('nodata-out')
    p_davailwin = session.get('p_davailwin')
    p_outlier = session.get('outliers')

    # temporary — fill 255-length arrays with session scalar values

    p_fitmethod      = np.full(255, session.get('p_fitmethod', 0), dtype='uint8')
    p_smooth         = np.full(255, session.get('smoothing-par', 1000), dtype='float64')
    p_nenvi          = np.full(255, session.get('envelope-iterations', 1), dtype='uint8')
    p_wfactnum       = np.full(255, session.get('adaptation-strength', 2), dtype='float64')
    p_startmethod    = np.full(255, session.get('season-start-method', 1), dtype='uint8')
    p_startcutoff    = np.full((255, 2), 
                               [session.get('season-start', 0.5),
                                session.get('season-end', 0.5)], 
                               dtype='float64', order='F')
    p_low_percentile = np.full(255, session.get('base-level', 0.05), dtype='float64')
    p_fillbase       = np.full(255, session.get('p_fillbase', 1), dtype='uint8')
    p_seasonmethod   = np.full(255, session.get('seasonal-method', 1), dtype='uint8')
    p_seapar         = np.full(255, session.get('seasonal-par', 0.5), dtype='float64')

    # select the slot to update
    idlu = int(session.get('idlu', 0))
    if not (0 <= idlu < 255):
        raise ValueError(f"idlu {idlu} out of range (0–254)")

    ap = ARRAY_PARAMS
    ap['p_fitmethod'][idlu]      = p_fitmethod[idlu]
    ap['p_smooth'][idlu]         = p_smooth[idlu]
    ap['p_nenvi'][idlu]          = p_nenvi[idlu]
    ap['p_wfactnum'][idlu]       = p_wfactnum[idlu]
    ap['p_startmethod'][idlu]    = p_startmethod[idlu]
    ap['p_low_percentile'][idlu] = p_low_percentile[idlu]
    ap['p_fillbase'][idlu]       = p_fillbase[idlu]
    ap['p_seasonmethod'][idlu]   = p_seasonmethod[idlu]
    ap['p_seapar'][idlu]         = p_seapar[idlu]

    # 2D array: write both columns for this slot
    ap['p_startcutoff'][idlu, 0] = p_startcutoff[idlu, 0]
    ap['p_startcutoff'][idlu, 1] = p_startcutoff[idlu, 1]

    seasonStartStop_show = session.get('seasonStartStop')
    coarseseason = session.get('coarseseason')
    xlim1 = session.get('xlim1')
    xlim2 = session.get('xlim2')
    ylim1 = session.get('ylim1')
    ylim2 = session.get('ylim2')

    nodata_out = session.get('nodata-out')
    xTick_year = session.get('xTick')


    # extract raw data from the current pixel

    raw_y, raw_w, raw_lc, raw_yyyymmdd, raw_yyyydoy = ts_functions.raw_single_extraction(
        current_row - row_start, current_col - col_start)

    # Convert yyyymmdd to datetime objects using pandas (this is the most efficient way)
    x_dates = pd.to_datetime(raw_yyyymmdd.astype(str), format='%Y%m%d')

    vpptable = []

    # 使用 Plotly 创建图表
    fig = go.Figure()
    
    # 添加第一条曲线
    fig.add_trace(go.Scatter(
    	x=x_dates, 
    	y=raw_y[0, 0, :], 
    	mode='markers', 
    	name='Raw data', 
    	marker=dict(color='rgba(0.7, 0.7, 0.7, 1)', size=6)
    	))

    # 添加第二条曲线
    fig.add_trace(go.Scatter(
    	x=x_dates, 
    	y=raw_y[0, 0, :], 
    	mode='lines', 
    	name='Raw data',
    	line=dict(color='rgba(0.7, 0.7, 0.7, 1)', width=2),
        visible='legendonly'  # This hides the curve by default
    	))

    # Modify values in raw_w[0, 0, :] based on conditions
    raw_w_slice = raw_w[0, 0, :]
    raw_w_modified = np.zeros_like(raw_w_slice)  # Initialize with zeros

    # Apply conditions and update values
    raw_w_modified = np.where((raw_w_slice >= p_a[0]) & (raw_w_slice <= p_a[1]), p_a[2], raw_w_modified)
    raw_w_modified = np.where((raw_w_slice >= p_a[3]) & (raw_w_slice <= p_a[4]), p_a[5], raw_w_modified)
    raw_w_modified = np.where((raw_w_slice >= p_a[6]) & (raw_w_slice <= p_a[7]), p_a[8], raw_w_modified)
    # Normalize raw_w to range from 0 to 6
    # Assuming raw_w is a 1D or 2D array (you may need to adjust the shape indexing accordingly)
    normalized_marker_size = raw_w_modified * 8  # Scale raw_w to range from 0 to 6

    # Ensure marker sizes are within a reasonable range
    normalized_marker_size = np.clip(normalized_marker_size, 0, 8)  # Clip to ensure the size is between 0 and 6

    # 添加第三条曲线
    fig.add_trace(go.Scatter(
        x=x_dates, 
        y=raw_y[0, 0, :], 
        mode='markers', 
        name='Quality',
        marker=dict(color='rgba(255, 0, 0, 1)', size=normalized_marker_size, symbol='circle-open'),
        visible='legendonly'  # This hides the curve by default
        ))

    if fit_dl == 1:
        p_fitmethod[0] = 1
        session['p_fitmethod'] = 1
        ap['p_fitmethod'][idlu] = 1
        fit_method_name = 'DL'
        vpp, vppqa, nseason, yfit, yfitqa, seasonfit, daily_timestep = ts_functions.ts_single_run(
        raw_y, raw_w, raw_lc, yrstart, nyear, num_of_data,
        p_outststep, 
        p_ignoreday, p_ylu, p_a, p_printflag, p_fitmethod, p_smooth, p_nodata, p_davailwin, p_outlier, p_nenvi, p_wfactnum,
        p_startmethod, p_startcutoff, p_low_percentile, p_fillbase, p_hrvppformat, p_seasonmethod, p_seapar
        )
        # 添加dl曲线
        fig.add_trace(go.Scatter(
            x=daily_timestep, 
            y=yfit[0, 0, :], 
            mode='lines', 
            name='Double logistic',
            line=dict(color='rgba(0, 0, 255, 1)', width=2)
            ))

        vpp_list, sos_x, sos_y, eos_x, eos_y = ts_functions.vpp_to_table(vpp,yrstart,nodata_out,fit_method_name)
        vpptable = vpptable + vpp_list

        if seasonStartStop_show == 1:
            # 添加dl曲线
            fig.add_trace(go.Scatter(
                x=sos_x + eos_x, 
                y=sos_y + eos_y, 
                mode='markers', 
                name='DL start/end',
                marker=dict(color='rgba(0, 0, 255, 1)', size=8)
                ))

    if fit_sp == 1:
        p_fitmethod[0] = 2
        session['p_fitmethod'] = 2
        ap['p_fitmethod'][idlu] = 2
        fit_method_name = 'SP'
        print(p_hrvppformat)
        vpp, vppqa, nseason, yfit, yfitqa, seasonfit, daily_timestep = ts_functions.ts_single_run(
        raw_y, raw_w, raw_lc, yrstart, nyear, num_of_data,
        p_outststep, 
        p_ignoreday, p_ylu, p_a, p_printflag, p_fitmethod, p_smooth, p_nodata, p_davailwin, p_outlier, p_nenvi, p_wfactnum,
        p_startmethod, p_startcutoff, p_low_percentile, p_fillbase, p_hrvppformat, p_seasonmethod, p_seapar
        )
        # 添加dl曲线
        fig.add_trace(go.Scatter(
            x=daily_timestep, 
            y=yfit[0, 0, :], 
            mode='lines', 
            name='Smoothing spline',
            line=dict(color='rgba(255, 0, 0, 1)', width=2)
            ))

        vpp_list, sos_x, sos_y, eos_x, eos_y = ts_functions.vpp_to_table(vpp,yrstart,nodata_out,fit_method_name)
        vpptable = vpptable + vpp_list

        if seasonStartStop_show == 1:
            # 添加dl曲线
            fig.add_trace(go.Scatter(
                x=sos_x + eos_x, 
                y=sos_y + eos_y, 
                mode='markers', 
                name='SP start/end',
                marker=dict(color='rgba(255, 0, 0, 1)', size=8)
                ))

    if fit_dlsp == 1:
        p_fitmethod[0] = 3
        session['p_fitmethod'] = 3
        ap['p_fitmethod'][idlu] = 3
        fit_method_name = 'DL-SP'
        vpp, vppqa, nseason, yfit, yfitqa, seasonfit, daily_timestep = ts_functions.ts_single_run(
        raw_y, raw_w, raw_lc, yrstart, nyear, num_of_data,
        p_outststep, 
        p_ignoreday, p_ylu, p_a, p_printflag, p_fitmethod, p_smooth, p_nodata, p_davailwin, p_outlier, p_nenvi, p_wfactnum,
        p_startmethod, p_startcutoff, p_low_percentile, p_fillbase, p_hrvppformat, p_seasonmethod, p_seapar
        )
        # 添加dl曲线
        fig.add_trace(go.Scatter(
            x=daily_timestep, 
            y=yfit[0, 0, :], 
            mode='lines', 
            name='DLSP',
            line=dict(color='rgba(0, 255, 0, 1)', width=2)
            ))

        vpp_list, sos_x, sos_y, eos_x, eos_y = ts_functions.vpp_to_table(vpp,yrstart,nodata_out,fit_method_name)
        vpptable = vpptable + vpp_list

        if seasonStartStop_show == 1:
            # 添加dl曲线
            fig.add_trace(go.Scatter(
                x=sos_x + eos_x, 
                y=sos_y + eos_y, 
                mode='markers', 
                name='DLSP start/end',
                marker=dict(color='rgba(0, 255, 0, 1)', size=8)
                ))

    if coarseseason == 1:
        vpp, vppqa, nseason, yfit, yfitqa, seasonfit, daily_timestep = ts_functions.ts_single_run(
        raw_y, raw_w, raw_lc, yrstart, nyear, num_of_data,
        p_outststep, 
        p_ignoreday, p_ylu, p_a, p_printflag, p_fitmethod, p_smooth, p_nodata, p_davailwin, p_outlier, p_nenvi, p_wfactnum,
        p_startmethod, p_startcutoff, p_low_percentile, p_fillbase, p_hrvppformat, p_seasonmethod, p_seapar
        )
        # 添加dl曲线
        fig.add_trace(go.Scatter(
            x=daily_timestep, 
            y=seasonfit, 
            mode='lines', 
            name='Coarse season',
            line=dict(color='rgba(0.5, 0.5, 0.5, 1)', width=2)
            ))

    ts_functions.save2array_params(ap)

    # 更新图表布局
    fig.update_layout(
        title=f'Row: {current_row + 1}, Col: {current_col + 1}',
        #xaxis_title="Time",
        #yaxis_title="Data",
        xaxis=dict(range=[xlim1, xlim2], tickformat="%Y-%m-%d"),  # Keep tick format as 'yyyy-mm-dd'),
        yaxis=dict(range=[ylim1, ylim2]),
        showlegend=True,
        legend=dict(
	        orientation="h",  # 水平布局
	        x=0.5,            # 水平居中
	        y=-0.1,           # 在图表下方
	        xanchor="center",  # 以图例的中心对齐
	        yanchor="top"     # 以顶部对齐
	    )
    )

    if xTick_year == 1:
        fig.update_layout(
            xaxis=dict(
                dtick="M12",            # Set ticks to appear every 12 months (1 year)
                tickvals=[f"{year}-01-01" for year in range(int(xlim1[:4]), int(xlim2[:4])+1)],  # Set ticks on 'yyyy-01-01'
            )
        )

    # 将 Plotly 图表转换为 JSON 格式
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # 返回图表的 JSON 数据
    return jsonify({
        "graph": graph_json,  # Plotly graph JSON
        "vpptable": vpptable  # The reshaped table data
    })

@tab_settings_bp.route('/update_para', methods=['POST'])
def update_para():
    data = request.get_json()
    print(data)
    
    for key, value in data.items():
        if key in session:
            # Update session with new value
            session[key] = value
        else:
            print(f"Warning: {key} is not found in session.")
    
    return jsonify({"message": "Plot limits updated successfully"}), 200


@tab_settings_bp.route("/update_rowcol", methods=["POST"])
def update_rowcol():
    col_start = session.get('col_start', 1) 
    col_end = session.get('col_end', 1) 
    row_start = session.get('row_start', 1) 
    row_end = session.get('row_end', 1) 
    # Get the current row and col from the session
    current_row = session.get('current_row', 1)
    current_col = session.get('current_col', 1)
    
    # Get the action (up, down, left, right) from the request
    data = request.get_json()
    action = data.get('action')

    # Initialize a variable to store messages
    message = ""
    
    # Update the session based on the action
    if action == 'up' and current_row>row_start:
        session['current_row'] = current_row - 1  # Move row up
    elif action == 'down' and current_row<row_end:
        session['current_row'] = current_row + 1  # Move row down
    elif action == 'left' and current_col>col_start:
        session['current_col'] = current_col - 1  # Move col left
    elif action == 'right' and current_col<col_end:
        session['current_col'] = current_col + 1  # Move col right
    else:
        # If we reach the boundary, set the message
        message = "You've reached the edge of the subwindow. You can select a new location in the Input tab."

    # Return only the message if it's set
    return jsonify({
        "message": message
    })

