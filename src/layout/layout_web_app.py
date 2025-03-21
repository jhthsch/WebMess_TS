import json
from dash import html, dcc, dash_table
import plotly.graph_objects as go
from config.config_dat import read_config_device
from utility_funs import init_figure, hidden_or_visible, get_measurement_paths
from layout.layout_funs import create_status_display, create_eval_channel_selector, create_left_content_graph, create_config_tab, create_config_tab_main


def create_layout(bend):
    """creates a layout for a dash app

    Args:
        inst (_type_): web_app instance
        IS_SCANNING (_type_): bool

    Returns:
        layout for dash app
    """
    ### INITIALIZING####
    print("-------CREADTE_LAYOUT--------------------->")
    config_main = bend.config
    list_configs_mcc = []
    list_configs_uldaq = []
    list_configs_mcculw = []
    list_configs_audio = []
    #list_configs_eps = []
    list_configs_nidaqmx = []
    list_configs_usbdux = []

    for i in range(config_main["num_mccdaqhat_devices"]):
        list_configs_mcc.append(read_config_device("mcc", i))
    for i in range(config_main["num_uldaq_devices"]):
        list_configs_mcc.append(read_config_device("uldaq", i))
    for i in range(config_main["num_mcculw_devices"]):
        list_configs_mcc.append(read_config_device("mcculw", i))
    for i in range(config_main["num_audio_devices"]):
        list_configs_mcc.append(read_config_device("audio", i))
    for i in range(config_main["num_eps_devices"]):
        list_configs_mcc.append(read_config_device("eps", i))
    for i in range(config_main["num_nidaqmx_devices"]):
        list_configs_mcc.append(read_config_device("nidaqmx", i))
    for i in range(config_main["num_usbdux_devices"]):
        list_configs_mcc.append(read_config_device("usbdux", i))
    # sleep(0.1)#make sure all configs are written
    device_config_list = []
    for measurement_device in bend.measurement_devices:
        device_config_list.append(measurement_device.config)
    graph_div = html.Div(
        id="graph_div",
        children=[
            html.Div(
                children=[
                    html.Label(children="y axis min:", style={"padding-top": "10px"}),
                    dcc.Input(id="y_axis_range_min", value=0),
                    html.Label(children="y axis max:", style={"padding-top": "10px"}),
                    dcc.Input(id="y_axis_range_max", value=0),
                    html.Button(
                        id="button_apply_y_axis_range",
                        children="fixed Range",
                        style={"heigth": "10px"},
                    ),
                    html.Button(
                        id="button_apply_y_axis_autorange",
                        children="Autorange",
                        style={"heigth": "10px"},
                    ),
                    # html.Div(id='Start_Time',children='Start Time:',style={'font-weight': 'bold','display': 'block'}),
                    html.Div(
                        id="update_seconds",
                        style={
                            "font-weight": "bold",
                            "display": "block",
                            "padding-top": "10px",
                        },
                    ),
                    dcc.Interval(
                        id="interval-component",
                        interval=1 * 1000,  # in milliseconds
                        n_intervals=0,
                    ),
                ],
                style={"padding-top": "20px"},
            ),
            dcc.Loading(
                id="loading",
                children=[
                    dcc.Graph(
                        id="stripChart",
                        style={"height": 900},
                        figure=init_figure(device_config_list),
                    ),
                ],
            ),
            html.Div(
                id="errorDisplay",
                children="",
                style={"font-weight": "bold", "color": "red"},
            ),
        ],
        style={
            "width": "55%",
            "display": "inline-block",
            "vertical-align": "top",
            # 'border' : '1px grey solid'
        },
    )

    right_content_graph = html.Div(
        id="right_content_graph",
        children=[
            html.Div(
                children=[
                    html.Label(
                        children="eval period in seconds",
                        style={"font-weight": "bold", "display": "block"},
                    ),
                    dcc.Input(
                        id="input_eval_period",
                        type="number",
                        step=0.1,
                        value=config_main["eval_period"],
                        min=0.2,
                    ),
                    html.Label(
                        children="eval timewindow in seconds",
                        style={
                            "font-weight": "bold",
                            "display": "block",
                        },
                    ),
                    dcc.Input(
                        id="input_eval_time",
                        type="number",
                        step=0.1,
                        value=config_main["eval_time"],
                        min=0.1,
                        max=10,
                    ),
                ],
                style={"display": "inline-block"},
            ),
            html.Div(
                children=[
                    html.Button(
                        id="apply_eval_time",
                        children="Apply eval time options",
                        style={"height": 50, "font-weight": "bold"},
                    ),
                ],
                style={"display": "inline-block", "vertical-align": 20},
            ),
            html.Div(
                children=[
                    html.Label(
                        children="Evaluated channels",
                        style={"font-weight": "bold", "display": "block"},
                    ),
                    create_eval_channel_selector(bend),
                ],
                style={"display": "block"},
            ),
            html.Label(
                children="Evaluation options",
                style={"font-weight": "bold", "display": "block"},
            ),
            dcc.Checklist(
                id="eval_opts",
                options=[
                    {"label": "min,max,average", "value": "min_max"},
                    {"label": "Sinus_fit", "value": "sin_fit"},
                    {"label": "FFT", "value": "fft"},
                ],
                value=config_main["eval_opts"],
            ),
            html.Div(
                id="min_max",
                style=hidden_or_visible("min_max" in config_main["eval_opts"]),
                children=[
                    html.Label(children="min,max,average", style={"font-weight": "bold"}),
                    dash_table.DataTable(
                        id="min_max_out",
                        columns=[
                            {"name": i, "id": i}
                            for i in ["channel", "min", "max", "mean", "peak_peak"]
                        ],
                        data=None,
                    ),
                ],
            ),
            html.Div(
                id="sin_fit",
                style=hidden_or_visible("sin_fit" in config_main["eval_opts"]),
                children=[
                    html.Label(
                        "Sinus fit: a+b*sin(2*\u03c0*f*t+c)",
                        style={"font-weight": "bold"},
                    ),
                    dash_table.DataTable(
                        id="fit_out",
                        columns=[{"name": i, "id": i} for i in ["channel", "a", "b", "c", "f"]],
                        data=None,
                    ),
                ],
            ),
            html.Div(
                id="fft",
                style=hidden_or_visible("fft" in config_main["eval_opts"]),
                children=[
                    html.Label(children="FFT", style={"font-weight": "bold"}),
                    dcc.Graph(
                        id="fft_out",
                        figure=go.Figure(layout=dict(legend=dict(x=0.1, y=0.99))),
                    ),
                ],
            ),
        ],
        style={
            "width": "23%",
            "display": "inline-block",
            "margin-top": 20,
            "padding-top": 20,
            "vertical-align": "top",
        },
    )

    tab_graph = dcc.Tab(
        label="Data Aquistion - Graph",
        children=[
            create_left_content_graph(bend),
            graph_div,
            right_content_graph,
            # ], style={'position': 'relative', 'display': 'block',
            #        }),#'overflow': 'hidden'
            # html.Div(id='trigger_log',children=[]),
            # html.Div(id='last_trigger',children=None,style={'display': 'none'}),
        ],
        style={"position": "absolute"},
    )

    tab_log = dcc.Tab(
        label="Logging Information",
        style={"vertical-align": "top"},
        children=[
            html.Div(id="current_log", children=[]),
            html.Button(id="get_log", children="Get log"),
        ],
    )
    paths = get_measurement_paths(config_main)
    path_measurements = paths["path_measurements"]
    path_trigger_reports = paths["path_trigger_reports"]
    path_daily_reports = paths["path_daily_reports"]

    tab_load = dcc.Tab(
        label="Load Measurment Data or Trigger Event Data",
        style={"vertical-align": "top"},
        children=[
            dcc.Graph(id="loadChart", style={"height": 600}, figure=init_figure([])),
            html.Div(
                id="load_graph_options",
                children=[
                    html.Label(
                        "Progress(updates Graph)",
                        style={
                            "font-weight": "bold",
                            "display": "inline-block",
                            "margin-top": 10,
                            "width": "100%",
                        },
                    ),
                    dcc.RangeSlider(id="progress_load", min=0, max=1, value=[0, 1], step=1),
                    html.Label(
                        "Samples displayed (0 equals all)",
                        style={
                            "font-weight": "bold",
                            "display": "inline-block",
                            "margin-top": 10,
                            "width": "100%",
                        },
                    ),
                    dcc.Input(
                        id="samples_displayed_load",
                        type="number",
                        value=2000,
                        step=1,
                        min=0,
                    ),
                    html.Label(
                        "Downsampling",
                        style={
                            "font-weight": "bold",
                            "display": "inline-block",
                            "margin-top": 10,
                            "width": "100%",
                        },
                    ),
                    dcc.Input(id="downsampling_load", type="number", value=2, step=1, min=1),
                    html.Label(
                        "Display raw values",
                        style={
                            "font-weight": "bold",
                            "display": "inline-block",
                            "margin-top": 10,
                            "width": "100%",
                        },
                    ),
                    dcc.Checklist(id="raw_load", options={}, value=[]),
                    html.Label(
                        "Display filtered values",
                        style={
                            "font-weight": "bold",
                            "display": "inline-block",
                            "margin-top": 10,
                            "width": "100%",
                        },
                    ),
                    dcc.Checklist(id="filtered_load", options={}, value=[0, 1, 2, 3, 4, 5, 6, 7]),
                    dcc.Store(id="loaded_data", data=[]),
                    dcc.Store(id="fetched_data_load", data=dict(time_current=None)),
                    dcc.Interval(
                        id="load_interval", disabled=True, interval=3000
                    ),  # timer for loading pickle files
                ],
                style={"display": "none"},
            ),
            # html.Div([
            #    #html.Label("Start Time:"),
            #    dash_datetimepicker.DashDatetimepicker(
            #        id="start-time-input_load",
            #        #label='Start Time:'
            #        startDate=dt.datetime.now()-dt.timedelta(days=1),
            #        endDate=dt.datetime.now(),
            #    ),
            # ]),
            dcc.RadioItems(
                id="file_type",
                options=[
                    {"label": "measurements", "value": path_measurements},
                    {"label": "trigger reports", "value": path_trigger_reports},
                    {"label": "daily reports", "value": path_daily_reports},
                ],
                value=path_measurements,
            ),
            # html.Div([
            # html.Label("End Time:"),
            # dash_datetimepicker.DashDatetimepicker(
            #    id="end-time-input_load",
            #    #label='End Time:'
            # ),
            # ]),
            html.Button(
                id="get_filenames",
                children="Get files",
                style={
                    "font-weight": "bold",
                    "display": "block",
                    "margin-top": 10,
                    "width": "200",
                },
            ),
            # ,
            html.Div(
                id="output_files",
                children=[dcc.RadioItems(id="output_files_radio", options=[])],
            ),
            html.Div(
                id="hide_load_button",
                children=[
                    html.Button(
                        id="load_pickle",
                        children="Load files",
                        style={"font-weight": "bold", "margin-top": 10, "width": "200"},
                    ),
                ],
                style={"display": "none"},
            ),
            dcc.ConfirmDialog(
                id="inform_filenames",
                # message='Danger danger! Are you sure you want to continue?',
            ),
        ],
    )

    tablist = [tab_graph, tab_log, create_config_tab_main(config_main), tab_load]


    for i, config_mccdaqhats in enumerate(list_configs_mcc):
        tablist.append(create_config_tab(config_mccdaqhats, i, bend.is_measuring))
    for i, config_mcculw in enumerate(list_configs_mcculw):
        tablist.append(create_config_tab(config_mcculw, i, bend.is_measuring))
    for i, config_uldaq in enumerate(list_configs_uldaq):
        tablist.append(create_config_tab(config_uldaq, i, bend.is_measuring))
    for i, config_audio in enumerate(list_configs_audio):
        tablist.append(create_config_tab(config_audio, i, bend.is_measuring))
    for i, config_nidaqmx in enumerate(list_configs_nidaqmx):
        tablist.append(create_config_tab(config_nidaqmx, i, bend.is_measuring))
    for i, config_usbdux in enumerate(list_configs_usbdux):
        tablist.append(create_config_tab(config_usbdux, i, bend.is_measuring))

    layout_out = html.Div(
        id="whole_web_page",  # the html object that contains the whole webpage
        children=[
            # html.H1(
            #    children='Multi DAQ Web Server TS',
            #    id='exampleTitle'
            # ),
            html.Div(
                children=[
                    html.H2(children="WEB_DAQ Status: ", style={"display": "inline"}),
                    create_status_display(bend.is_measuring),
                    html.Button(
                        id="save_but",
                        children="Save",
                        style={
                            "margin-left": 50,
                            "height": 35,
                            "width": 150,
                            "display": "inline-block",
                            "font-weight": "bold",
                        },
                    ),
                    html.Button(
                        id="exit_but",
                        children="Exit",
                        n_clicks=0,
                        disabled=True,
                        style={
                            "margin-left": 350,
                            "height": 35,
                            "width": 150,
                            "display": "inline-block",
                            "font-weight": "bold",
                        },
                    ),
                    # html.Button(id='refresh_uldaq',children='Refresh Uldaq list', style={'display':'inline', 'allign':'right'}),
                ]
            ),
            dcc.Tabs(children=tablist),
            html.Button(
                id="debug",
                children="debug",
                style={
                    "width": 200,
                    "height": 35,
                    "text-align": "center",
                    "margin-top": 10,
                },
            ),
            dcc.Interval(
                id="timer_update_figure",  # live graph update
                interval=1000,  # in milliseconds
                n_intervals=0,
            ),
            # hidden Divs
            html.Div(
                id="chartInfo",
                style={"display": "none"},
                children=json.dumps({"sample_count": 0}),
            ),
            dcc.Store(id="fetched_data", data=dict(t=list(), y=list(), last_num=0)),
            html.Div(
                id="status",
            ),
            html.Div(id="callback_autosave", style={"display": "none"}),
            html.Div(id="debug_out"),
            html.Div(id="debug_out2"),
            html.Div(id="debug_out3"),
            html.Div(id="debug_out4"),
            html.Div(id="debug_out5"),
        ],
    )
    for i in range(5):
        layout_out.children.append(html.Div(id=f"refresh_help{i}", children=None))  # in use:0,1

    print("<-------CREADTE_LAYOUT-OUT--------------------")

    return layout_out
