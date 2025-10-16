from flask import Flask, Response, Blueprint, session, jsonify
import threading
import time
from . import ts_functions
from . import tab_settings
from . import ts_full_run
import json

import numpy as np
import rasterio
import datetime
import copy
import timesat
from rasterio.windows import Window
import ray

tab_run_bp = Blueprint('tab_run', __name__)

# Global flag to control the background job
stop_signal = threading.Event()

# Shared list for progress updates
progress_updates = []

# Job thread reference
job_thread = None

# Flag to indicate whether the job is done
job_done = False

def long_running_job(input_type,session_data_json,ym3,wm3,lc3):
    global job_done

    progress_updates.append("\n----------------------\nJob started!\n")

    flist = session_data_json['image_file_names']

    tv_yyyymmdd, tv_yyyydoy, nyear, nyearstart, nyearend = ts_functions.read_time_vector_data(flist)


    array_params = ts_functions.load4array_params()

    qlist = session_data_json['qa_file_names']
    outfolder = session_data_json['output_folder']

    p_outststep = session_data_json['p_outststep']
    p_nodata = session_data_json['p_nodata']
    p_davailwin = session_data_json['p_davailwin']
    p_ignoreday = session_data_json['p_ignoreday']
    p_ylu = [session_data_json['data-range-min'], session_data_json['data-range-max']] 
    p_a = [session_data_json['a1'], session_data_json['a2'], session_data_json['a3'], session_data_json['a4'], session_data_json['a5'], session_data_json['a6'], session_data_json['a7'], session_data_json['a8'], session_data_json['a9']]
    p_printflag = session_data_json['debug_mod']
    p_outlier = session_data_json['outliers']
    p_hrvppformat = session_data_json['p_hrvppformat']

    p_fitmethod = array_params['p_fitmethod']
    p_smooth = array_params['p_smooth']
    p_nenvi = array_params['p_nenvi']
    p_wfactnum = array_params['p_wfactnum']
    p_startmethod = array_params['p_startmethod']
    p_startcutoff = array_params['p_startcutoff']
    p_low_percentile = array_params['p_low_percentile']
    p_fillbase = array_params['p_fillbase']
    p_seasonmethod = array_params['p_seasonmethod']
    p_seapar = array_params['p_seapar']

    num_core = session_data_json['n_core']
    max_memory_gb = session_data_json['n_memory']
    ray_dir = session_data_json['ray_dir']

    if num_core > 1:
        ray.init(_temp_dir=ray_dir, ignore_reinit_error=True, num_cpus=num_core)

    z = len(flist)
    progress_updates.append(f'num of images: {z}')
    progress_updates.append('First image: ' + flist[0])
    progress_updates.append('Last image: ' + flist[z - 1])

    p_outindex = np.arange(1, nyear*365+1)[::p_outststep]
    p_outindex_num = len(p_outindex)

    local_st_folder, local_vpp_folder = ts_full_run._createlocaloutputfolder_(outfolder)  # need to modify if using S3 bucket

    vppname = ["SOSD", "SOSV", "LSLOPE", "EOSD", "EOSV", "RSLOPE", "LENGTH", "MINV", "MAXD", "MAXV", "AMPL", "TPROD", "SPROD"]

    imwindow = [0, 0, 0, 0]

    outyfitfn = ["" for x in range(p_outindex_num)]
    band_names = ["" for x in range(p_outindex_num)]
    outvppfn = ["" for x in range(13 * 2 * (nyearend - nyearstart + 1))]
    i = 0
    j = 0
    for i_tv in p_outindex:
        yfitdate = datetime.date(nyearstart, 1, 1) + datetime.timedelta(days=int(i_tv)) - datetime.timedelta(days=1)
        outyfitfn[i] = local_st_folder + '/TIMESAT_' + yfitdate.strftime('%Y-%m-%d') + '.tif'
        band_names[i] = 'TIMESAT_' + yfitdate.strftime('%Y-%m-%d')
        i += 1
    for i_nyear in range(nyearstart, nyearend + 1):
        for i_seas in range(2):
            for i_seaspar in range(13):
                outvppfn[j] = local_vpp_folder + '/TIMESAT_' + str(i_nyear) +\
                              '_season_' + str(i_seas + 1) + '_' + vppname[i_seaspar] + '.tif'
                j += 1
    outnsfn = local_vpp_folder + '/TIMESAT_nsperyear.tif'

    if input_type == 'imagelist':
        with rasterio.open(flist[0], 'r') as temp:
            img_profile = temp.profile

        if sum(imwindow) == 0:
            dx = img_profile['width']
            dy = img_profile['height']
        else:
            dx = imwindow[2]
            dy = imwindow[3]

        img_profile_st = copy.deepcopy(img_profile)
        img_profile_st.update(compress='lzw')

        img_profile_vpp = copy.deepcopy(img_profile)
        img_profile_vpp.update(nodata=p_nodata, dtype=rasterio.float32, compress='lzw')
        img_profile_ns = copy.deepcopy(img_profile)
        img_profile_ns.update(nodata=255, compress='lzw')


        #with rasterio.open(outnsfn, 'w', **img_profile_ns) as outnsfile:
        #    0
        for i in outvppfn:
            with rasterio.open(i, 'w', **img_profile_vpp) as outvppfile:
                0
        for i in outyfitfn:
            with rasterio.open(i, 'w', **img_profile_st) as outstfile:
                0

        # Check the data type specified in img_profile_st
        data_type = img_profile['dtype']

        num_layers = p_outindex_num + z * 2 + (13 * 2) * nyear
        # Number of elements in the array
        num_elements = dx * num_layers * dy
        # Memory required per element in bytes (32 bits / 8 bits per byte)
        memory_per_element_bytes = 32 / 8
        # Total memory required in bytes
        total_memory_bytes = num_elements * memory_per_element_bytes
        # Convert total memory required to megabytes (1 GB = 2^30 bytes)
        total_memory_mb = total_memory_bytes / (2 ** 30)

        progress_updates.append('maximum Memory Needed: ' + str(total_memory_mb) + 'GB')

        progress_updates.append('Memory used: ' + str(max_memory_gb) + 'GB')

        # Memory per element in bytes for 32-bit floating point
        memory_per_element_bytes = 4

        # Calculate max dy
        max_memory_bytes = max_memory_gb * (2 ** 30)
        dy_max = max_memory_bytes / (dx * num_layers * memory_per_element_bytes * num_core)

        y_slice_size = min(np.floor(dy_max), dy)

        progress_updates.append('y_slice_size = ' + str(y_slice_size))

        num_block = int(np.ceil(dy / y_slice_size))

        if dy % y_slice_size > 0:
            y_slice_end = dy % y_slice_size
        else:
            y_slice_end = y_slice_size

        for iblock in range(num_block):
            if stop_signal.is_set():
                # If the stop signal is set, stop the job immediately.
                print(f"Stop signal detected at block {iblock}")
                progress_updates.append(f"Job stopped at block {iblock} of {num_block}\n")
                job_done = True
                return  # Exit the function, stopping the job.

            progress_updates.append('Processing block: ' + str(iblock + 1) + '/' + str(num_block) + '  starttime: ' +
                  str(datetime.datetime.now()))

            x = dx
            if iblock != num_block - 1:
                y = int(y_slice_size)  # 5490
            else:
                y = int(y_slice_end)
            x_map = int(imwindow[0])
            y_map = int(iblock * y_slice_size + imwindow[1])

            vi, qa = ts_full_run._openimagedatafiles_(x_map, y_map, x, y, flist, qlist, data_type, num_core)

            progress_updates.append('--- start TIMESAT processing ---' + '  starttime: ' +
                  str(datetime.datetime.now()))

            vi = np.nan_to_num(vi, nan=p_ylu[0]-1)
            qa = np.nan_to_num(qa, nan=0)

            # print(tv_yyyydoy)
            # vi=vi[100,100,:]
            # # Add new axes to reshape
            # vi = vi[np.newaxis, np.newaxis, :]
            # qa=qa[100,100,:]
            # # Add new axes to reshape
            # qa = qa[np.newaxis, np.newaxis, :]
            # print(vi.shape)
            # print(qa.reshape)
            # vpp, vppqa, nseason, yfit, yfitqa, seasonfit, tseq = timesat.tsfprocess(
            #     nyear, vi, qa, tv_yyyydoy, p_outindex,
            #     p_ignoreday, p_ylu, p_a, 1, p_fitmethod, p_smooth, p_nodata, p_davailwin, p_outlier, p_nenvi, p_wfactnum,
            #     p_startmethod, p_startcutoff, p_low_percentile, p_fillbase, p_hrvppformat, p_seasonmethod, p_seapar,
            #     1, 1, z, p_outindex_num)
            # return

            if num_core > 1:

                @ray.remote
                def runtimesat(vi_temp, qa_temp):
                    vpp_para, vppqa, nseason_para, yfit_para, yfitqa, seasonfit, tseq = timesat.tsfprocess(
                        nyear, vi_temp, qa_temp, tv_yyyydoy, p_outindex,
                        p_ignoreday, p_ylu, p_a, p_printflag, p_fitmethod, p_smooth, p_nodata, p_davailwin, p_outlier, p_nenvi, p_wfactnum,
                        p_startmethod, p_startcutoff, p_low_percentile, p_fillbase, p_hrvppformat, p_seasonmethod, p_seapar,
                        1, x, z, p_outindex_num)
                    vpp_para = vpp_para[0, :, :]
                    yfit_para = yfit_para[0, :, :]
                    nseason_para = nseason_para[0, :]
                    return vpp_para, yfit_para, nseason_para

                futures = [runtimesat.remote(np.expand_dims(vi[i, :, :], axis=0), np.expand_dims(qa[i, :, :], axis=0)) for i
                           in range(y)]
                futures_out = ray.get(futures)
                vpp = np.stack([item[0] for item in futures_out], axis=0)
                yfit = np.stack([item[1] for item in futures_out], axis=0)
                nseason = np.stack([item[2] for item in futures_out], axis=0)
                futures_out = None

            else:
                vpp, vppqa, nseason, yfit, yfitqa, seasonfit, tseq = timesat.tsfprocess(
                    nyear, vi, qa, tv_yyyydoy, p_outindex,
                    p_ignoreday, p_ylu, p_a, p_printflag, p_fitmethod, p_smooth, p_nodata, p_davailwin, p_outlier, p_nenvi, p_wfactnum,
                    p_startmethod, p_startcutoff, p_low_percentile, p_fillbase, p_hrvppformat, p_seasonmethod, p_seapar,
                    y, x, z, p_outindex_num)

            vpp = np.moveaxis(vpp, -1, 0)
            yfit = np.moveaxis(yfit, -1, 0).astype(img_profile['dtype'])


            progress_updates.append('--- start writing geotif ---' + '  starttime: ' +
                  str(datetime.datetime.now()))
            if num_core > 1:
                @ray.remote
                def write_outputs_vpp(nlayer, arr):
                    with rasterio.open(nlayer, 'r+', **img_profile_vpp) as outfile:
                        outfile.write(arr, window=Window(x_map, y_map, x, y), indexes=1)

                [write_outputs_vpp.remote(outvppfn[i - 1], arr) for i, arr in enumerate(vpp, 1)]
                @ray.remote
                def write_outputs_st(nlayer, arr):
                    with rasterio.open(nlayer, 'r+', **img_profile_st) as outfile:
                        outfile.write(arr, window=Window(x_map, y_map, x, y), indexes=1)

                [write_outputs_st.remote(outyfitfn[i - 1], arr) for i, arr in enumerate(yfit, 1)]
            else:
                for i, arr in enumerate(vpp, 1):
                    with rasterio.open('{}'.format(outvppfn[i - 1]), 'r+', **img_profile_vpp) as outvppfile:
                        outvppfile.write(arr, window=Window(x_map, y_map, x, y), indexes=1)
                for i, arr in enumerate(yfit, 1):
                    with rasterio.open('{}'.format(outyfitfn[i - 1]), 'r+', **img_profile_st) as outstfile:
                        outstfile.write(arr, window=Window(x_map, y_map, x, y), indexes=1)

            with rasterio.open(outnsfn, 'r+', **img_profile_ns) as outnsfile:
                outnsfile.write(nseason, window=Window(x_map, y_map, x, y), indexes=1)

            progress_updates.append('Block: ' + str(iblock + 1) + '/' + str(num_block) + '  finishedtime: ' +
                  str(datetime.datetime.now()))
    elif input_type == 'imagestack':
        img_profile = ts_functions.load4geotifprofile()

        if sum(imwindow) == 0:
            x = img_profile['width']
            y = img_profile['height']
        else:
            x = imwindow[2]
            y = imwindow[3]

        img_profile_st = copy.deepcopy(img_profile)
        img_profile_st.update(compress='lzw')
        img_profile_st.update(count=p_outindex_num)

        img_profile_vpp = copy.deepcopy(img_profile)
        img_profile_vpp.update(count=1)
        img_profile_vpp.update(nodata=p_nodata, dtype=rasterio.float32, compress='lzw')
        img_profile_ns = copy.deepcopy(img_profile)
        img_profile_ns.update(count=1)
        img_profile_ns.update(nodata=255, compress='lzw')


        with rasterio.open(outnsfn, 'w', **img_profile_ns) as outnsfile:
            0
        for i in outvppfn:
            with rasterio.open(i, 'w', **img_profile_vpp) as outvppfile:
                0
        with rasterio.open(i, 'w', **img_profile_st) as outstfile:
            0

        # Check the data type specified in img_profile_st
        data_type = img_profile['dtype']

        vi = ts_functions.load4ym3()
        vi = np.nan_to_num(vi, nan=p_ylu[0]-1)
        qa = ts_functions.load4wm3()
        qa = np.nan_to_num(qa, nan=0)
        lc = ts_functions.load4lc3()
        p_nclasses = 1 # need to modify later
        landuse = np.ones(255, dtype='uint8')

        if num_core > 1:

            @ray.remote
            def runtimesat(vi_temp, qa_temp):
                vpp_para, vppqa, nseason_para, yfit_para, yfitqa, seasonfit, tseq = timesat.tsf2py(
                    nyear, vi_temp, qa_temp, tv_yyyydoy, lc, p_nclasses, landuse, p_outindex,
                    p_ignoreday, p_ylu, p_printflag, p_fitmethod, p_smooth, p_nodata, p_davailwin, p_outlier, p_nenvi, p_wfactnum,
                    p_startmethod, p_startcutoff, p_low_percentile, p_fillbase, p_hrvppformat, p_seasonmethod, p_seapar,
                    1, x, z, p_outindex_num)
                vpp_para = vpp_para[0, :, :]
                yfit_para = yfit_para[0, :, :]
                nseason_para = nseason_para[0, :]
                return vpp_para, yfit_para, nseason_para

            futures = [runtimesat.remote(np.expand_dims(vi[i, :, :], axis=0), np.expand_dims(qa[i, :, :], axis=0)) for i
                       in range(y)]
            futures_out = ray.get(futures)
            vpp = np.stack([item[0] for item in futures_out], axis=0)
            yfit = np.stack([item[1] for item in futures_out], axis=0)
            nseason = np.stack([item[2] for item in futures_out], axis=0)
            futures_out = None

        else:

            vpp, vppqa, nseason, yfit, yfitqa, seasonfit, tseq = timesat.tsf2py(
                nyear, vi, qa, tv_yyyydoy, lc, p_nclasses, landuse, p_outindex,
                p_ignoreday, p_ylu, p_printflag, p_fitmethod, p_smooth, p_nodata, p_davailwin, p_outlier, p_nenvi, p_wfactnum,
                p_startmethod, p_startcutoff, p_low_percentile, p_fillbase, p_hrvppformat, p_seasonmethod, p_seapar,
                y, x, z, p_outindex_num)

        vpp = np.moveaxis(vpp, -1, 0)
        yfit = np.moveaxis(yfit, -1, 0).astype(img_profile['dtype'])


        progress_updates.append('--- start writing geotif ---' + '  starttime: ' +
              str(datetime.datetime.now()))

        for i, arr in enumerate(vpp, 1):
            with rasterio.open('{}'.format(outvppfn[i - 1]), 'r+', **img_profile_vpp) as outvppfile:
                outvppfile.write(arr, indexes=1)
        with rasterio.open(local_st_folder + '/TIMESAT_' + str(nyearstart) + '_' + str(nyearend) + '.tif', 'w', **img_profile_st) as dst:
            # write the entire stack into the window
            dst.write(yfit)
            dst.descriptions = tuple(band_names)
        #with rasterio.open(outnsfn, 'r+', **img_profile_ns) as outnsfile:
        #    outnsfile.write(nseason, indexes=1)

    
    # If the job completed without the stop signal, mark it as done
    if not stop_signal.is_set():
        progress_updates.append("Job finished!\n----------------------\n")
        job_done = True  # Indicate that the job is done


@tab_run_bp.route('/start', methods=['GET'])
def start():
    global job_thread, job_done
    # Reset stop signal and clear progress updates
    stop_signal.clear()
    progress_updates.clear()
    job_done = False  # Reset job done flag

    # Check if the job is already running
    if job_thread and job_thread.is_alive():
        return jsonify({"message": "Job is already running"}), 400
    
    session_data = dict(session)
    session_data['image_file_names'] = ts_functions.load4memory_image_file_names()
    session_data['qa_file_names'] = ts_functions.load4memory_qa_file_names()
    input_type = session_data['input_type']

    # Start the job in a new thread if it's not already running
    job_thread = threading.Thread(target=long_running_job, args=(input_type,session_data,ts_functions.load4ym3(),ts_functions.load4wm3(),ts_functions.load4lc3()))
    job_thread.start()

    # Immediately return the stream response to the client while the job runs in the background
    return Response(stream_progress(), mimetype='text/event-stream')

def stream_progress():
    last_index = 0
    while True:
        # Check if there are new progress updates to send
        if len(progress_updates) > last_index:
            for update in progress_updates[last_index:]:
                yield f"data: {update}\n\n"
            last_index = len(progress_updates)
        
        # Check if the job is done and stop streaming
        if job_done:
            break
        
        time.sleep(1)  # Sleep for a second before checking for new updates

    # Send a final update indicating the stream is closing
    yield "data: Stream closed\n\n"


@tab_run_bp.route('/stop', methods=['POST'])
def stop():
    global job_thread

    # Set the stop signal to stop the background job
    print("Stop signal received in /stop route")  # Debugging statement
    stop_signal.set()

    # Wait for the job to finish
    if job_thread and job_thread.is_alive():
        print("Waiting for job to finish...")
        job_thread.join()

    return jsonify({"message": "Job stopped"}), 200
