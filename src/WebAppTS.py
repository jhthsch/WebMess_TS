# third party
import configparser
import datetime
import logging
import os
import platform
import signal as signal2
import sys
import webbrowser
from threading import Thread
from time import sleep

import pandas as pd
import plotly.graph_objs as go
from dash import ALL, MATCH, Dash, Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate

import device_management.device_finder as device_finder
from backend import Backend
from config.config_dat import (
    MAIN_CONFIG_PATH,
    device_config_path,
    replace_entries,
    replace_val_of_array_entry,
)
from layout.layout_web_app import create_layout
from read_pickle import getfilenames_from_directory, read_pickle
from utility_funs import flatten, get_ip_address, hidden_or_visible, init_figure

# initializing
log_filename = "log.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s",
)  # config logger

num_lines_old = 0
if os.path.exists(log_filename):
    with open(log_filename) as logfile:
        num_lines_old = len(logfile.readlines())

# check current platform for import and hardware check
current_platform = platform.system()

# create instance of class and Dash
device_finder.find_available_devices()
sleep(0.01)
bend = Backend()
_app = Dash(__name__, update_title=None)
_app.layout = create_layout(bend)


# Callbacks und Funktionen
@_app.callback(
    Output("update_seconds", "children"),
    [Input("interval-component", "n_intervals"), Input("status_button", "n_clicks")],
)
def show_start_time(nintval, n):
    # print('-----------update sec-------------------')
    if bend.is_measuring:
        start_time = (
            bend.get_tstart()
        )  # datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_time = datetime.datetime.now()
        elapsed_time = current_time - start_time
        return html.Div(
            f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')} - Current Time: {
                current_time.strftime('%Y-%m-%d %H:%M:%S')
            } - Elasped time: {elapsed_time.seconds} seconds"
        )
    else:
        html.Div()


@_app.callback(
    Output("fit_out", "data"),
    Output("min_max_out", "data"),
    Output("fft_out", "figure"),
    Input("timer_update_figure", "n_intervals"),
    State("fft_out", "figure"),
    prevent_initial_call=True,
)
def fetch_eva_data(_, fft_out):
    if "sin_fit" in bend.config["eval_opts"]:
        data_fit_out = [
            [
                {
                    "channel": channel.quantity,
                    "a": f"{channel.params_sinus['a'].value:2f}",
                    "b": f"{channel.params_sinus['b'].value:2f}",
                    "c": f"{channel.params_sinus['c'].value:2f}",
                    "f": f"{channel.params_sinus['f'].value:2f}",
                }
                for channel in device.channels
                if channel.channel_num in device.config["eval_channels"]
            ]
            for device in bend.measurement_devices
        ]
        data_fit_out = flatten(data_fit_out)
    else:
        data_fit_out = []
    if "min_max" in bend.config["eval_opts"]:
        data_min_max_out = [
            [
                {
                    "channel": channel.quantity,
                    "min": f"{channel.min:6f}",
                    "max": f"{channel.max:6f}",
                    "mean": f"{channel.average:6f}",
                    "peak_peak": f"{channel.peak_peak:6f}",
                }
                for channel in device.channels
                if channel.channel_num in device.config["eval_channels"]
            ]
            for device in bend.measurement_devices
        ]
        data_min_max_out = flatten(data_min_max_out)
    else:
        data_min_max_out = []
    if "fft" in bend.config["eval_opts"]:
        fft_out = go.Figure(
            layout={"uirevision": "fft_zoom_state", "legend": dict(x=0.1, y=0.99)}
        )
        for device in bend.measurement_devices:
            for channel in device.channels:
                if channel.channel_num in device.config["eval_channels"]:
                    fft_out.add_trace(
                        go.Scatter(x=channel.fft_frequs, y=channel.fft_vals)
                    )
    return data_fit_out, data_min_max_out, fft_out


@_app.callback(
    Output("fetched_data", "data"),
    Input("timer_update_figure", "n_intervals"),
    # Input('loading', 'loading_state'),
    State("fetched_data", "data"),
    prevent_initial_call=True,
)
def fetch_data(_, data):
    # if data['last_num']==bend.num_chunks:
    # print(type(loading_state))
    if not bend.is_measuring:
        raise PreventUpdate
    # if loading_state.is_loading:
    #    raise PreventUpdate
    else:
        list_t = []
        list_y = []
        local_num_chunks = bend.num_chunks

        for (
            measurement_device
        ) in bend.measurement_devices:  # iteratting over all devices
            for i, channel in enumerate(
                measurement_device.channels
            ):  # iteratting over all channels in a device
                fetched_data_channel = []
                fetched_data_channel_time = None
                while channel.buffers_graph:
                    chunk = channel.buffers_graph.popleft()
                    fetched_data_channel.extend(
                        chunk[0][:: measurement_device.config["downsampling"]]
                    )
                    if fetched_data_channel_time is None:
                        fetched_data_channel_time = chunk[1]
                    else:
                        fetched_data_channel_time[1] = chunk[1][1]

                list_y.append(fetched_data_channel)
                list_t.append(fetched_data_channel_time)

        data["last_num"] = local_num_chunks
        data["t"] = []
        for t_v, y in zip(list_t, list_y):
            if t_v is None:
                data["t"].append([])
            else:
                [t_s, t_e] = t_v
                data["t"].append(pd.date_range(t_s, t_e, len(y) + 1, inclusive="left"))

        data["y"] = list_y
        data["num_samples"] = bend.config["samples_to_display"]
        return data


# function in javascript that is sent to the client and excecuted by the
# browser (check browser compability)


js_function_new = """
function fun(data) {
    const y_out = []
    const t_out = []
    for (const trace of data.y) {
        y_out.push([].concat.apply([], trace))
    }
    for (const trace of data.t) {
        t_out.push([].concat.apply([], trace))
    }

    return  [[{x: t_out, y: y_out}, [...Array(data.y.length).keys()], data.num_samples]]

}
"""

_app.clientside_callback(
    js_function_new,
    [Output("stripChart", "extendData")],
    [Input("fetched_data", "data")],
    prevent_initial_call=True,
)


@_app.callback(
    Output("stripChart", "figure"),
    Input("button_apply_y_axis_range", "n_clicks"),
    State("y_axis_range_min", "value"),
    State("y_axis_range_max", "value"),
    State("stripChart", "figure"),
    prevent_initial_call=True,
)
def apply_y_axis_range(_, y_axis_min, y_axis_max, graph):
    """applies the y_axis range accoring to given inputs"""
    # graph.update_yaxes({'range':[y_axis_min, y_axis_max]})
    graph["layout"]["yaxis"]["range"] = [y_axis_min, y_axis_max]
    graph["layout"]["yaxis"]["autorange"] = False
    return graph


@_app.callback(
    Output("loading", "children"),
    Input("button_apply_y_axis_autorange", "n_clicks"),
    State("stripChart", "figure"),
    prevent_initial_call=True,
)
def apply_y_axis_autorange(_, graph):
    """applies the y_axis range accoring to given inputs"""
    # graph.update_yaxes({'range':[y_axis_min, y_axis_max]})
    # graph['layout']['yaxis']['range'] = [y_axis_min, y_axis_max]
    graph["layout"]["yaxis"]["autorange"] = True
    return [dcc.Graph(id="stripChart", style={"height": 900}, figure=graph)]


# All callbacks relatet to loading files not really supported anymore
@_app.callback(
    Output("output_files", "children"),
    Output("hide_load_button", "style"),
    Input("get_filenames", "n_clicks"),
    State("file_type", "value"),
    prevent_initial_call=True,
)
def find_files(n, directory_path):
    if n is None or n == 0:
        raise PreventUpdate
    else:
        print(directory_path)
        filenames = getfilenames_from_directory(initialdir=directory_path)
        options_radiobutton = []
        for filename in filenames:
            if not (filename.endswith(".html")):
                options_radiobutton.append(
                    {"label": os.path.basename(filename), "value": filename}
                )
        radio_out = dcc.Checklist(
            id="output_files_radio",
            options=options_radiobutton,
        )
        if len(options_radiobutton) >= 1:
            return [radio_out], {"display": "block"}
        else:
            raise PreventUpdate


@_app.callback(
    [
        Output("load_interval", "disabled"),
        Output("loadChart", "figure"),
        Output("loaded_data", "data"),
        Output("load_graph_options", "style"),
    ],
    Input("load_pickle", "n_clicks"),
    State("output_files_radio", "value"),
    State("file_type", "value"),
    prevent_initial_call=True,
)
def call_read_pickle(n, filelist: list, file_type: any):
    """opens a window to choose files to load (files have to be match(end time_n=startime_{n+1}))
       creates a first figure based on default values
       shows the settings to "navigate" through loaded file
    Args:
        n ([type]): [description]

    Raises:
        PreventUpdate: [description]

    Returns:
        [type]: [description]
    """
    if n is None or n == 0 or filelist is None or len(filelist) == 0:
        raise PreventUpdate
    else:
        data_out = {}
        if filelist[0].endswith(".csv"):
            df = pd.read_csv(filelist[0])
            fig = go.Figure()
            for columnName, columnData in df.iteritems():
                if not (columnName == "Time"):
                    fig.add_trace(
                        go.Scatter(
                            x=df["Time"], y=columnData, name=columnName, mode="lines"
                        )
                    )

            return True, fig, data_out, {"display": "block", "width": "100%"}

        else:
            print("read_pickle", filelist)
            meta_l, channel_data_list, time_vectors, channel_data_list_filtered = (
                read_pickle(filelist)
            )
            data_out["meta_l"] = meta_l
            data_out["channel_data_list"] = channel_data_list
            data_out["time_vectors"] = []
            for time_vector in time_vectors:
                time_vector = [time.timestamp() for time in time_vector]
                data_out["time_vectors"].append(time_vector)
            data_out["time_start"] = time_vectors[0][0].timestamp()
            data_out["time_end"] = time_vectors[0][-1].timestamp()
            return (
                False,
                init_figure(meta_l),
                data_out,
                {"display": "block", "width": "100%"},
            )


@_app.callback(
    Output("fetched_data_load", "data"),
    Input("load_interval", "n_intervals"),
    State("loaded_data", "data"),
    State("fetched_data_load", "data"),
    prevent_initial_call=True,
)
def fetch_data_load(_, data, data_last):
    if data_last["time_current"] == data["time_start"]:
        raise PreventUpdate
    data_out = {"t": [], "y": []}
    if data_last["time_current"] is None:
        data_last["time_current"] = data["time_start"]
        data_last["last_index"] = 0
    time_end_chunk = data_last["time_current"] + 3  # +timedelta(milliseconds=3000)
    for i, time_vector in enumerate(data["time_vectors"]):
        index_start = data_last["last_index"]
        index_end = index_start + 3000
        t_out = time_vector[index_start:index_end]
        t_out = [datetime.datetime.fromtimestamp(t) for t in t_out]
        data_out["t"].append(t_out)
        data_out["y"].append(data["channel_data_list"][i][index_start:index_end])

    data_out["last_index"] = index_end
    data_out["time_current"] = time_end_chunk
    if data_out["time_current"] > data["time_end"]:
        data_out["time_current"] = data["time_start"]
    data_out["num_samples"] = 100000

    return data_out


_app.clientside_callback(
    js_function_new,
    [Output("loadChart", "extendData")],
    [Input("fetched_data_load", "data")],
    prevent_initial_call=True,
)


@_app.callback(
    [Output("timer_update_figure", "disabled"), Output("Start_stop_graph", "children")],
    Input("Start_stop_graph", "n_clicks"),
    State("timer_update_figure", "disabled"),
    prevent_initial_call=True,
)
# enables disables the timer to update the graph
def toggle_figure_update(n, state):
    if n is not None and n > 0:
        if not state:
            return [True, "Start Animation"]
        else:
            return [False, "Stop Animation"]
    else:
        return [False, "Stop Animation"]


@_app.callback(
    Output({"type": "front_config_pid", "index": MATCH}, "value"),
    Input({"type": "front_config_pid", "index": MATCH}, "value"),
    State({"type": "front_config_pid", "index": MATCH}, "id"),
    prevent_initial_call=True,
)
def apply_front_config_change_1(value, id):
    print("apply_front_config_change_1", id)
    num_device_in = int(
        id["index"][-1]
    )  # last char of the id gives the index of the device
    num_device_out = int(
        id["index"][-2]
    )  # last char of the id gives the index of the device
    device_in = bend.measurement_devices[num_device_in]
    device_out = bend.measurement_devices[num_device_out]
    for device in bend.measurement_devices:
        for channel in device.channels:
            if device_out in channel.controlled_devices:
                channel.controlled_devices.remove(device_out)
    if len(value) == 0:
        raise PreventUpdate
    elif len(value) == 1:
        device_in.channels[value[0]].controlled_devices.append(device_out)
        raise PreventUpdate
    if len(value) > 1:
        return []


@_app.callback(
    Output({"type": "front_config", "index": MATCH}, "value"),
    Input({"type": "front_config", "index": MATCH}, "value"),
    State({"type": "front_config", "index": MATCH}, "id"),
    prevent_initial_call=True,
)
def apply_front_config_change_2(value, id):
    print("apply_front_config_change_2", id)
    i = int(id["index"][-1])  # last char of the id gives the index of the device
    config_key = id["index"][:-2]
    bend.measurement_devices[i].config[config_key] = value
    replace_entries([config_key], [value], bend.measurement_devices[i].configpath)
    if config_key == "active_output":
        if value:
            bend.measurement_devices[i].start_output_scan()
        else:
            bend.measurement_devices[i].stop_output()
            bend.measurement_devices[i].start_output_const(volt_out=0)
    raise PreventUpdate


@_app.callback(
    Output({"type": "front_config_array", "index": MATCH}, "value"),
    Input({"type": "front_config_array", "index": MATCH}, "value"),
    State({"type": "front_config_array", "index": MATCH}, "id"),
    prevent_initial_call=True,
)
def apply_front_tigger_config_array(value, id):
    # last char of the id gives the index of the device
    print("apply_fornt_trigger_config_array", id)
    i = int(id["index"][-1])
    j = int(id["index"][-2])
    config_key = id["index"][:-2]
    bend.measurement_devices[i].config[config_key][j] = value
    print(config_key, value, j, bend.measurement_devices[i].configpath)
    replace_val_of_array_entry(
        config_key, value, j, bend.measurement_devices[i].configpath
    )

    raise PreventUpdate


@_app.callback(
    Output("min_max", "style"),
    Output("sin_fit", "style"),
    Output("fft", "style"),
    Input("eval_opts", "value"),
    prevent_initial_call=True,
)
def apply_eval_opts(eval_opts):
    bend.config["eval_opts"] = eval_opts
    replace_entries(["eval_opts"], [eval_opts], MAIN_CONFIG_PATH)
    bend.set_eval_apschedules()  # Korrigierte Methode
    return (
        hidden_or_visible("min_max" in eval_opts),
        hidden_or_visible("sin_fit" in eval_opts),
        hidden_or_visible("fft" in eval_opts),
    )


@_app.callback(
    Output("apply_eval_time", "children"),
    Input("apply_eval_time", "n_clicks"),
    State("input_eval_period", "value"),
    State("input_eval_time", "value"),
    prevent_initial_call=True,
)
def apply_eval_time(_, eval_period, eval_time):
    bend.config["eval_perdiod"] = eval_period
    bend.config["eval_time"] = eval_time
    replace_entries(
        ["eval_perdiod", "eval_time"], [eval_period, eval_time], MAIN_CONFIG_PATH
    )
    bend.set_eval_schedules()
    raise PreventUpdate


@_app.callback(
    Output("apply_samples_to_display", "children"),
    Input("apply_samples_to_display", "n_clicks"),
    State("samplesToDisplay", "value"),
    prevent_initial_call=True,
)
def change_samples_to_display(
    _, newval: int
):  # change the refreshinterval of the figure update
    bend.config["samples_to_display"] = newval
    replace_entries(["samples_to_display"], [newval], MAIN_CONFIG_PATH)
    raise PreventUpdate


@_app.callback(
    Output("timer_update_figure", "interval"),
    Input("apply_fetch_rate", "n_clicks"),
    State("fetch_rate", "value"),
    prevent_initial_call=True,
)
def change_fetch_rate(_, newval):  # change the refreshinterval of the figure update
    print
    bend.config["fetch_rate"] = newval
    replace_entries(["fetch_rate"], [newval], MAIN_CONFIG_PATH)
    return newval


def inf_thread2():
    """somehow the mcculw devices are stopping as soon as the function that startet the measurement is left
    this seemed to be the easiest solultion"""

    # while bend.is_measuring:
    #    sleep(1)


@_app.callback(
    Output("refresh_help0", "children"),  # help0 helper
    Input("status_button", "n_clicks"),
    prevent_initial_call=True,
)
def start_stop_measurement(_):
    if bend.is_measuring:
        bend.is_measuring = False
        bend.stop_clean_up()
        bend.save(args="stopping")
    else:
        # speicher von daily reports, stoppen aller jobs
        # 'autosave','max_value_report','daily_report'
        bend.stop_clean_up()
        bend.set_tstart(
            datetime.datetime.now()
        )  # startzeit des neuen Messbeginns speichern

        bend.start_measurement()  # alle registrierten Messgeraete und jobs s.o. starten
        # Thread(target=inf_thread2).start()
        sleep(0.5)  # Zeitgeben zum sicheren Start der Messung
        bend.is_measuring = True
        # Dauerschleife für Messung aller Messgräte/Kanäle und laufen lassen
        # aller angemeldet jobs
        Thread(target=while_thread).start()
        # print('started measurement')
    # raise PreventUpdate
    return "refresh"


@_app.callback(
    Output("whole_web_page", "children"),
    Input("refresh_help0", "children"),  # start stop measurement
    Input("refresh_help1", "children"),  # apply main config
    Input("refresh_help2", "children"),
    Input("refresh_help3", "children"),
    Input("refresh_help4", "children"),
    prevent_initial_call=True,
)
def refresh_web_page(*helper_children_list):
    print("refreshes whole side if triggered by refresh")
    if "refresh" not in helper_children_list:
        print("NOT refreshed")
        raise PreventUpdate
    else:
        print("refreshed")
        _app.layout = create_layout(bend)
        return _app.layout.children


@_app.callback(
    Output("refresh_help1", "children"),
    Input("apply_main_config", "n_clicks"),
    State({"type": "config_main", "index": ALL}, "value"),
    State({"type": "config_main", "index": ALL}, "id"),
    prevent_initial_call=True,
)
def apply_main_config(n, values, ids_all):
    """applies main config"""
    print("apply_main_config: n", n, values, ids_all)
    if n is None or n == 0:
        raise PreventUpdate
    else:
        ids = []
        for id_all in ids_all:
            ids.append(id_all["index"])
        for id, value in zip(ids, values):
            bend.config[id] = value
        print(ids, values)
        replace_entries(ids, values, path=MAIN_CONFIG_PATH)
        logging.info("main config changed")
    return "refresh"


@_app.callback(
    Output({"type": "textarea_config", "index": MATCH}, "value"),
    Input({"type": "config_selector", "index": MATCH}, "value"),
    State({"type": "textarea_config", "index": MATCH}, "value"),
    prevent_initial_call=True,
)
def change_device_selector(device: str, config_txt: str) -> str:
    print("changing textarea")
    print(config_txt)
    lines = config_txt.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith("device"):
            lines[i] = f"device = {device} \n"
    return "".join(lines)


@_app.callback(
    Output({"type": "save_config", "index": MATCH}, "children"),
    Input({"type": "save_config", "index": MATCH}, "n_clicks"),
    State({"type": "save_config", "index": MATCH}, "id"),
    State({"type": "textarea_config", "index": MATCH}, "value"),
    prevent_initial_call=True,
)
def apply_device_config(_, button_id: dict, config_txt: str) -> None:
    """callback that updates config no change in GUI"""
    print("applied_device")
    config = configparser.ConfigParser()
    config.read_string(config_txt)
    config_type = config.get("config", "type")
    i = int(button_id["index"][-1])
    # config_type = None
    filepath = device_config_path(config_type, i)
    with open(filepath, "w") as f:
        f.write(config_txt)

    raise PreventUpdate


@_app.callback(Output("exit_but", "disabled"), Input("exit_but", "n_clicks"))
def exit_app(n_clicks):
    if n_clicks is None:
        n_clicks = 0  # Wenn n_clicks None ist, setze es auf 0
    if n_clicks > 0:
        print("------------Exit!----------------")
        # start_stop_measurement()
        bend.save()
        bend.stop_clean_up()
        sleep(1)
        os._exit(0)  # Beendet die App sofort
    return False


@_app.callback(
    Output("debug_out3", "children"),
    Input("save_but", "n_clicks"),
    prevent_initial_call=True,
)
def man_save(n):
    if n is None or n == 0:
        raise PreventUpdate
    else:
        bend.save(args="manual")
        return None


@_app.callback(
    Output("current_log", "children"),
    Input("get_log", "n_clicks"),
    prevent_initial_call=True,
)
def display_log(_):
    children = []
    with open("log.log") as logfile:
        lines = logfile.readlines()
    for line in lines[num_lines_old:]:
        children.append(html.Div(children=line, style={"display": "block"}))
    return children


def while_thread():
    """main loop for reading measurements and for scheduled events such as saving,
    repots and value evaluation
    """
    # sleep(2)
    "starting while thread"
    while bend.is_measuring:
        try:
            bend.read_measurement_devices()
            # schedule.run_pending() # apscheduler runs all "added" job
            # automatically
        except Exception as e:
            print(f"in while_thread: {e}")
        except (KeyboardInterrupt, SystemExit):
            from backend import ascheduler

            ascheduler.shutdown()
            bend.is_measuring = False
            start_stop_measurement()
        sleep(0.4)


def signal_handler(_sig, _frame):
    bend.stop_clean_up()
    sys.exit(0)


signal2.signal(signal2.SIGINT, signal_handler)

# Funktion zum automatischen Öffnen des Browsers


class BrowserWindowManager:
    def __init__(self):
        self.window_opened = False

    def open_window(self, url):
        if not self.window_opened:
            print("Webbrowser------------------>ip_address: ", url)
            webbrowser.open_new(url)
            self.window_opened = True
        else:
            print("Window is already opened")

    def close_window(self):
        if self.window_opened:
            if current_platform == "Windows":
                os.system("taskkill /im chrome.exe /f")
            elif current_platform == "Darwin":
                os.system("pkill -f 'Google Chrome'")
            elif current_platform == "Linux":
                os.system("pkill -f 'chrome'")
            self.window_opened = False
        else:
            print("No window is currently opened")


def main():
    browsermanager = BrowserWindowManager()
    url = str(get_ip_address()) + ":" + str(bend.config["web_app_port"])

    if bend.config["ip_address"] == "":
        sleep(1)
        browsermanager.open_window(url)
        _app.run_server(
            host=get_ip_address(),
            port=bend.config["web_app_port"],
            debug=True,
            use_reloader=False,
        )
    else:
        try:
            _app.run_server(
                host=bend.config["ip_address"],
                port=bend.config["web_app_port"],
                debug=True,
            )
        except OSError:
            logging.info("Could not host on configured IP, trying automatic resolve")
            _app.run_server(
                host=get_ip_address(),
                port=bend.config["web_app_port"],
                debug=True,
                use_reloader=False,
            )
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
        finally:
            pass


if __name__ == "__main__":
    main()
