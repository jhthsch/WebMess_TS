import json
from dash import html, dcc
from config.config_dat import device_config_path
import sounddevice as sd


#### Layout##
# some parts of the layout are created in a more dynamic way this has to be done in callbacks or beforehand
# the latter can be seen here


def create_status_display(IS_SCANNING):
    if not (IS_SCANNING):
        status_display = html.H2(
            id="status_output_label",
            children="Idle",  # 'Running',
            style={
                "display": "inline",
                "color": "orange",
                "padding-right": 25,
            },  # {'display':'inline','color': 'green'}
        )
        status_button = html.Button(
            id="status_button",
            n_clicks=0,
            children="Start",  # 'Running',
            style={
                "width": 150,
                "height": 35,
                "text-align": "center",
                "margin-top": 10,
                "display": "inline",
                "font-weight": "bold",
            },
            # {'display':'inline','color': 'green'}
        )
    else:
        status_display = html.H2(
            id="status_output_label",
            children="Running",
            style={"display": "inline", "color": "green", "padding-right": 25},
        )
        status_button = html.Button(
            id="status_button",
            children="Stop",  # 'Running',
            style={
                "width": 150,
                "height": 35,
                "text-align": "center",
                "margin-top": 10,
                "display": "inline",
                "font-weight": "bold",
            },
        )

    div_status_display = html.Div(
        id="div_status_display",
        children=[status_display, status_button],
        style={"display": "inline"},
    )

    return div_status_display


def create_mccdaqhat_selector(config_dat, i):
    """
    Gets a list of available MCC 128 devices and creates a corresponding
    dash-core-components Dropdown element for the user interface.

    Returns:
        dcc.Dropdown: A dash-core-components Dropdown object.
    """
    # if  not config_dat['mccdaqhat_devices_enabled']:
    #    return dcc.Dropdown( disabled=True)
    from daqhats import hat_list

    hats = hat_list()  # filter_by_id=HatIDs.MCC_128
    hat_selection_options = []
    for hat in hats:
        # Create the label from the address and product name
        label = "{0}: {1}".format(hat.address, hat.product_name)
        # Create the value by converting the descriptor to a JSON object
        option = {"label": label, "value": json.dumps(hat._asdict())}
        hat_selection_options.append(option)

    selection = None
    if hat_selection_options:
        if config_dat["device"] in hat_selection_options:
            selection = config_dat["device"]
        else:
            selection = hat_selection_options[0]["value"]

    return dcc.Dropdown(  # pylint: disable=no-member
        id={"type": "mccdaqhats_config", "index": f"mccdaqhats_device_{i}"},
        options=hat_selection_options,
        disabled=False,
        value=selection,
        clearable=False,
        style={"width": 200, "height": 35, "text-align": "center", "margin-top": 10},
    )


def create_uldaq_selector(config_dat_uldaq, i):
    """
    Gets a list of available Data translation devices and creates a corresponding
    dash-core-components Dropdown element for the user interface.

    Returns:
        dcc.Dropdown: A dash-core-components Dropdown object.
    """
    from uldaq import get_daq_device_inventory, InterfaceType

    # gets list of devices device.product_name,device.product_id,
    # device.dev_interface, device.dev_string, device.unique_id
    daq_devices = get_daq_device_inventory(InterfaceType.ANY)
    daq_selection_options = []
    for device in daq_devices:
        # Create the label from the address and product name

        label = f"{
            device.product_name} Interface:{
            device.dev_interface} uID:{
            device.unique_id}"
        # Create the value by converting the descriptor to a JSON object
        option = dict(
            label=label,
            value=json.dumps(
                dict(
                    product_name=device.product_name,
                    interface=device.dev_interface,
                    uID=device.unique_id,
                )
            ),
        )
        daq_selection_options.append(option)

    selection = None
    if config_dat_uldaq["device"] in daq_selection_options:
        selection = config_dat_uldaq["device"]
    else:
        try:
            selection = daq_selection_options[0]["value"]
        except BaseException:
            return None
    # print(daq_selection_options)
    # print(selection)
    # print(0)
    return dcc.Dropdown(  # pylint: disable=no-member
        id={"type": "ul_config", "index": f"ul_device_{i}"},
        options=daq_selection_options,
        value=selection,
        clearable=False,
        style={"width": 200, "height": 35, "text-align": "center", "margin-top": 10},
    )


def create_mcculw_selector(config_dat_mcculw, i):
    """
    Gets a list of available Data translation devices and creates a corresponding
    dash-core-components Dropdown element for the user interface.

    Returns:
        dcc.Dropdown: A dash-core-components Dropdown object.
    """

    from mcculw import ul
    from mcculw.enums import InterfaceType

    # ul.ignore_instacal()
    daq_devices = ul.get_daq_device_inventory(InterfaceType.ANY)

    daq_selection_options = []
    for i, device in enumerate(daq_devices):
        # Create the label from the address and product name
        label = f"{device.product_name} uID:{device.unique_id}"
        # Create the value by converting the descriptor to a JSON object
        option = dict(
            label=label,
            value=json.dumps(dict(product_name=device.product_name, uID=device.unique_id)),
        )
        daq_selection_options.append(option)

    selection = None
    if config_dat_mcculw["device"] in daq_selection_options:
        selection = config_dat_mcculw["device"]
    else:
        try:
            selection = daq_selection_options[0]["value"]
        except BaseException:
            return None
    # print(daq_selection_options)
    # print(selection)
    # print(0)
    return dcc.Dropdown(  # pylint: disable=no-member
        id={"type": "ul_config", "index": f"uld_device_{i}"},
        options=daq_selection_options,
        value=selection,
        clearable=False,
        style={"width": 200, "height": 35, "text-align": "center", "margin-top": 10},
    )


def create_audio_selector(config_dat_audio, i):
    """
    Gets a list of available audio devices and creates a corresponding
    dash-core-components Dropdown element for the user interface.

    Returns:
        dcc.Dropdown: A dash-core-components Dropdown object.
    """
    audio_devices = sd.query_devices()
    labels = str(audio_devices).splitlines()
    selection_options = []
    for j, device in enumerate(audio_devices):
        # print(device)
        # Create the label from the address and product name

        label = labels[j]
        # print('create_audio_selector: '+label)
        # Create the value by converting the descriptor to a JSON object
        try:
            option = dict(
                label=label,
                value=json.dumps(dict(product_name=device["name"], descriptor=device["index"])),
            )
        except BaseException:
            option = dict(
                label=label,
                value=json.dumps(dict(product_name=device["name"], descriptor=j)),
            )
        selection_options.append(option)

    selection = None
    if json.dumps(config_dat_audio["device"]) in selection_options:
        selection = json.dumps(config_dat_audio["device"])
    else:
        try:
            selection = selection_options[0]["value"]
        except BaseException:
            return None
    # print(0)
    return dcc.Dropdown(  # pylint: disable=no-member
        id={"type": "config_selector", "index": f"audio_device_{i}"},
        options=selection_options,
        value=selection,
        clearable=False,
        style={"width": 600, "height": 35, "text-align": "center", "margin-top": 10},
    )


def create_usbdux_selector(config_dat_usbdux, i):
    """
    Gets a list of available audio devices and creates a corresponding
    dash-core-components Dropdown element for the user interface.

    Returns:
        dcc.Dropdown: A dash-core-components Dropdown object.
    """
    from device_management import usbdux_class

    usbdux_devices = usbdux_class.find_usbdux_devices()
    selection_options = []
    for device in usbdux_devices:
        # print(device)
        # Create the label from the address and product name
        """
        ID = device.get('ID')
        label = device.get('product_name')

        # Create the value by converting the descriptor to a JSON object [{'ID': 0, 'product_name': 'usbduxsigma'}]
        try:
            option = dict(label=ID, value=device)
        except:
            option = dict(label=ID, value=json.dumps(dict(product_name=device['product_name'])))
        """
        option = dict(label=str(device), value=json.dumps(device))
        selection_options.append(option)

    selection = None
    if json.dumps(config_dat_usbdux["device"]) in selection_options:
        selection = json.dumps(config_dat_usbdux["device"])
    else:
        try:
            selection = selection_options[0]["value"]
        except BaseException:
            return None
    # print(0)
    return dcc.Dropdown(  # pylint: disable=no-member
        id={"type": "config_selector", "index": f"usbdux_device_{i}"},
        options=selection_options,
        value=selection,
        clearable=False,
        style={"width": 600, "height": 35, "text-align": "center", "margin-top": 10},
    )


def create_nidaqmx_selector(config_dat_nidaqmx, i):
    """
    Gets a list of available audio devices and creates a corresponding
    dash-core-components Dropdown element for the user interface.

    Returns:
        dcc.Dropdown: A dash-core-components Dropdown object.
    """
    from device_management.nidaqmx_class import find_nidaqmx_devices

    nidaqmx_devices = find_nidaqmx_devices()
    selection_options = []
    for device in nidaqmx_devices:
        # print(device)
        # Create the label from the address and product name

        label = device.get("product_name")
        # Create the value by converting the descriptor to a JSON object
        # print('product_name',label)
        option = dict(label=label, value=json.dumps(device))
        selection_options.append(option)

    selection = None
    if json.dumps(config_dat_nidaqmx["device"]) in [x["value"] for x in selection_options]:
        selection = json.dumps(config_dat_nidaqmx["device"])
    else:
        try:
            selection = selection_options[0]["value"]
        except BaseException:
            return None
    # print(0)
    # print(selection_options)
    return dcc.Dropdown(  # pylint: disable=no-member
        id={"type": "nidaqmx_config", "index": f"nidaqmx_device_{i}"},
        options=selection_options,
        value=selection,
        clearable=False,
        style={"width": 600, "height": 35, "text-align": "center", "margin-top": 10},
    )


def create_config_tab_main(config_main):
    """
    helper function to hide/unhide labels, buttons etc
    """

    def return_block_or_hidden(x):
        return "block" if x else "none"

    tab_out = dcc.Tab(
        id="config_tab_main",
        label="Aquistion Settings & Configuration",
        style={"vertical-align": "top"},
        children=[
            # MCCDaqhat
            html.Label(
                "Number of MCCDaqHat devices",
                style={
                    "width": 600,
                    "font-weight": "bold",
                    "display": return_block_or_hidden(config_main["mccdaqhat_devices_enabled"]),
                    "margin-top": 10,
                },
            ),
            dcc.Input(
                id={"type": "config_main", "index": "num_mccdaqhat_devices"},
                type="number",
                value=config_main["num_mccdaqhat_devices"],
                style={
                    "width": 600,
                    "display": return_block_or_hidden(config_main["mccdaqhat_devices_enabled"]),
                },
            ),
            # NiDaq nu
            html.Label(
                "Number of NiDaqmx devices",
                style={
                    "width": 600,
                    "font-weight": "bold",
                    "display": return_block_or_hidden(config_main["nidaqmx_devices_enabled"]),
                    "margin-top": 10,
                },
            ),
            dcc.Input(
                id={"type": "config_main", "index": "num_nidaqmx_devices"},
                type="number",
                value=config_main["num_nidaqmx_devices"],
                style={
                    "width": 600,
                    "display": return_block_or_hidden(config_main["nidaqmx_devices_enabled"]),
                },
            ),
            # Uldaq
            html.Label(
                "Number of uldaq devices",
                style={
                    "width": 600,
                    "font-weight": "bold",
                    "display": return_block_or_hidden(config_main["uldaq_devices_enabled"]),
                    "margin-top": 10,
                },
            ),
            dcc.Input(
                id={"type": "config_main", "index": "num_uldaq_devices"},
                type="number",
                value=config_main["num_uldaq_devices"],
                style={
                    "width": 600,
                    "display": return_block_or_hidden(config_main["uldaq_devices_enabled"]),
                },
            ),
            # MCCWULW
            html.Label(
                "Number of mcculw devices",
                style={
                    "width": 600,
                    "font-weight": "bold",
                    "display": return_block_or_hidden(config_main["mcculw_devices_enabled"]),
                    "margin-top": 10,
                },
            ),
            dcc.Input(
                id={"type": "config_main", "index": "num_mcculw_devices"},
                type="number",
                value=config_main["num_mcculw_devices"],
                style={
                    "width": 600,
                    "display": return_block_or_hidden(config_main["mcculw_devices_enabled"]),
                },
            ),
            # Audio
            html.Label(
                "Number of audio devices",
                style={
                    "width": 600,
                    "font-weight": "bold",
                    "display": return_block_or_hidden(config_main["audio_devices_enabled"]),
                    "margin-top": 10,
                },
            ),
            dcc.Input(
                id={"type": "config_main", "index": "num_audio_devices"},
                type="number",
                value=config_main["num_audio_devices"],
                style={
                    "width": 600,
                    "display": return_block_or_hidden(config_main["audio_devices_enabled"]),
                },
            ),
            # Eps Device
            html.Label(
                "Number of Micro Epsilon Devices",
                style={
                    "width": 600,
                    "font-weight": "bold",
                    "display": return_block_or_hidden(config_main["eps_devices_enabled"]),
                    "margin-top": 10,
                },
            ),
            dcc.Input(
                id={"type": "config_main", "index": "num_eps_devices"},
                type="number",
                value=config_main["num_eps_devices"],
                style={
                    "width": 600,
                    "display": return_block_or_hidden(config_main["eps_devices_enabled"]),
                },
            ),
            # usbdux
            html.Label(
                "Number of USB-DUX Devices",
                style={
                    "width": 600,
                    "font-weight": "bold",
                    "display": return_block_or_hidden(config_main["usbdux_devices_enabled"]),
                    "margin-top": 10,
                },
            ),
            dcc.Input(
                id={"type": "config_main", "index": "num_usbdux_devices"},
                type="number",
                value=config_main["num_usbdux_devices"],
                style={
                    "width": 600,
                    "display": return_block_or_hidden(config_main["usbdux_devices_enabled"]),
                },
            ),
            html.Label(
                "Path to store measurements and reports",
                style={
                    "width": 600,
                    "font-weight": "bold",
                    "display": "block",
                    "margin-top": 10,
                },
            ),
            dcc.Input(
                id={"type": "config_main", "index": "data_path"},
                type="text",
                value=config_main["data_path"],
                style={"width": 600, "display": "block"},
            ),
            html.Label(
                "Send triggers to following E-Mails (comma seperated, no space)",
                style={
                    "width": 600,
                    "font-weight": "bold",
                    "display": "block",
                    "margin-top": 10,
                },
            ),
            dcc.Input(
                id={"type": "config_main", "index": "email_list"},
                type="text",
                value=config_main["email_list"],
                style={"width": 600, "display": "block"},
            ),
            html.Label(
                "IP-Address of web Application",
                style={
                    "width": 600,
                    "font-weight": "bold",
                    "display": "block",
                    "margin-top": 10,
                },
            ),
            dcc.Input(
                id={"type": "config_main", "index": "ip_address"},
                type="text",
                value=config_main["ip_address"],
                style={"width": 600, "display": "block"},
            ),
            html.Label(
                "Port Number of web Application",
                style={
                    "width": 600,
                    "font-weight": "bold",
                    "display": "block",
                    "margin-top": 10,
                },
            ),
            dcc.Input(
                id={"type": "config_main", "index": "web_app_port"},
                type="number",
                value=config_main["web_app_port"],
                style={"width": 600, "display": "block"},
            ),
            html.Div(
                children=[
                    html.Div(
                        children=[
                            html.Label(
                                "Trigger pretime in s",
                                style={
                                    "width": 200,
                                    "font-weight": "bold",
                                    "display": "block",
                                    "margin-top": 10,
                                },
                            ),
                            dcc.Input(
                                id={"type": "config_main", "index": "trigger_pre"},
                                type="number",
                                value=config_main["trigger_pre"],
                            ),
                        ]
                    ),
                    html.Div(
                        children=[
                            html.Label(
                                "Trigger posttime in s",
                                style={
                                    "width": 200,
                                    "font-weight": "bold",
                                    "display": "block",
                                    "margin-top": 10,
                                },
                            ),
                            dcc.Input(
                                id={"type": "config_main", "index": "trigger_post"},
                                type="number",
                                value=config_main["trigger_post"],
                            ),
                        ]
                    ),
                ]
            ),
            html.Label(
                "Save settings",
                style={
                    "font-weight": "bold",
                    "display": "block",
                    "margin-top": 10,
                    "width": "100%",
                },
            ),
            dcc.RadioItems(
                id={"type": "config_main", "index": "save_opt"},
                options=[
                    {"label": "autosave", "value": "auto"},
                    {"label": "manual only", "value": "manu"},
                    {"label": "discard measurements", "value": "discar"},
                ],
                value=config_main["save_opt"],
            ),
            html.Label(
                "Autosave timer(s)",
                style={
                    "font-weight": "bold",
                    "display": "block",
                    "margin-top": 10,
                    "width": "100%",
                },
            ),
            dcc.Input(
                id={"type": "config_main", "index": "autosave_sec"},
                type="number",
                value=config_main["autosave_sec"],
                style={"display": "inline-block", "width": 150},
            ),
            html.Label(
                "Report interval in seconds",
                style={
                    "width": 200,
                    "font-weight": "bold",
                    "display": "block",
                    "margin-top": 10,
                },
            ),
            dcc.Input(
                id={"type": "config_main", "index": "max_val_report_interval_sec"},
                type="number",
                value=config_main["max_val_report_interval_sec"],
            ),
            html.Button(
                id="apply_main_config",
                children="save/apply main config",
                style={
                    "width": 200,
                    "height": 35,
                    "text-align": "center",
                    "margin-top": 10,
                    "display": "block",
                },
            ),
        ],
    )
    return tab_out


def create_config_tab(config, i, IS_SCANNING):
    cotype = config["type"]
    print("create_config_tab: ", cotype)
    filepath = device_config_path(cotype, i)
    with open(filepath, "r") as file:
        file_contents = file.read()
    if IS_SCANNING:
        device_selector = html.Div()
    elif cotype == "mcc":
        device_selector = create_mccdaqhat_selector(config, i)
    elif cotype == "nidaqmx":
        device_selector = create_nidaqmx_selector(config, i)
    elif cotype == "uldaq":
        device_selector = create_uldaq_selector(config, i)
    elif cotype == "audio":
        device_selector = create_audio_selector(config, i)
    elif cotype == "eps":
        device_selector = html.Div()  # TODOcreate_(config,i)
    elif cotype == "mcculw":
        device_selector = create_mcculw_selector(config, i)
    elif cotype == "usbdux":
        device_selector = create_usbdux_selector(config, i)
    else:
        print("wrong config type couldnt create device selector")
        # logging.warning('wrong config type')
        device_selector = html.Div()

    tab_out = dcc.Tab(
        id=f"config_tab_{cotype}{i}",
        label=f"{cotype} device configurator {i}",
        style={"vertical-align": "top"},
        children=[
            html.Label(
                f"Select a {cotype} device (Make sure to only use input devices)",
                style={"font-weight": "bold"},
            ),
            device_selector,  # je type erzeugen
            dcc.Textarea(
                id={"type": "textarea_config", "index": f"{cotype}_device_{i}"},
                value=file_contents,  # Step  3: Set the value property to the file contents
                style={"width": "100%", "height": 200},
                disabled=IS_SCANNING,
            ),
            html.Button(
                "Save",
                id={"type": "save_config", "index": f"{cotype}_device_{i}"},
                n_clicks=0,
            ),  # Button to trigger saving
            # html.Div(id='output_container')  # Placeholder for any output
            # message
        ],
    )
    return tab_out


def create_left_content_graph(bend):
    # config_main,list_configs_mcc,list_configs_dt=config_merge
    left_content_graph = html.Div(
        id="leftContent",
        children=[],
        style={
            "width": "18%",
            "display": "inline-block",
            "margin-top": 20,
            "padding-top": 20,
            "vertical-align": "top",
        },
    )
    ### General settings###
    left_content_graph.children.append(
        html.Button(
            children="Stop animation",
            id="Start_stop_graph",
            style={
                "width": 100,
                "height": 35,
                "text-align": "center",
                "margin-top": 10,
            },
        ),
    )
    left_content_graph.children.append(
        html.Label(
            "Samples to display",
            style={"font-weight": "bold", "display": "block", "margin-top": 10},
        ),
    )
    left_content_graph.children.append(
        html.Div(
            children=[
                dcc.Input(
                    id="samplesToDisplay",
                    type="number",
                    min=1,
                    step=1,
                    value=bend.config["samples_to_display"],
                    style={"width": 100, "display": "inline-block"},
                ),
                html.Button(
                    id="apply_samples_to_display",
                    style={"width": 100, "display": "inline-block"},
                    children="Apply",
                ),
            ]
        ),
    )
    left_content_graph.children.append(
        html.Label(
            "Fetch rate in ms",
            style={"font-weight": "bold", "display": "block", "margin-top": 10},
        ),
    )
    left_content_graph.children.append(
        html.Div(
            children=[
                dcc.Input(
                    id="fetch_rate",
                    type="number",
                    min=1,
                    step=1,
                    value=bend.config["fetch_rate"],
                    style={"width": 100, "display": "inline-block"},
                ),
                html.Button(
                    id="apply_fetch_rate",
                    style={"width": 100, "display": "inline-block"},
                    children="Apply",
                ),
            ]
        ),
    )
    #### Everything device specific ####
    for i, device in enumerate(bend.measurement_devices):
        # Header for the device

        left_content_graph.children.append(
            html.H3(
                f'{
                    device.config["type"]}{
                    device.number}: {
                    device.config["device"]["product_name"]}'
            )
        )
        left_content_graph.children.append(
            html.Label(
                f'Measurement rate: {
                    device.config["sample_rate"]}',
                style={"font-weight": "bold", "display": "block", "margin-top": 10},
            )
        )

        # downsampling menu
        left_content_graph.children.append(
            html.Label(
                "Downsampling",
                style={"font-weight": "bold", "display": "block", "margin-top": 10},
            )
        )
        left_content_graph.children.append(
            html.Div(
                children=[
                    dcc.Input(
                        id={"type": "front_config", "index": f"downsampling_{i}"},
                        type="number",
                        min=1,
                        max=100,
                        step=1,
                        value=device.config["downsampling"],
                        style={"width": 100, "display": "inline-block"},
                    ),
                ]
            ),
        )
        left_content_graph.children.append(
            html.Label(
                "Geophone filter",
                style={"font-weight": "bold", "display": "block", "margin-top": 10},
            )
        )
        filter_opts = []
        filt50Hz_opts = []
        detrend_opts = []
        html_input_triggers = html.Div(
            children=[],
            style={
                "width": "49%",
                "display": "inline-block",
                "vertical-align": "bottom",
            },
        )
        for channel in device.config["channels_on"]:
            filter_opts.append({"label": f"Channel {channel}", "value": channel})
            filt50Hz_opts.append({"label": f"Channel {channel}", "value": channel})
            detrend_opts.append({"label": f"Channel {channel}", "value": channel})
            html_input_triggers.children.append(
                dcc.Input(
                    id={
                        "type": "front_config_array",
                        "index": f"threshold_list{channel}{i}",
                    },
                    type="number",
                    min=0,
                    step=0.001,
                    value=device.config["threshold_list"][channel],
                    style={
                        "width": "100%",
                        "display": "block",
                        "vertical-align": "top",
                        "height": 15,
                    },
                )
            )

        left_content_graph.children.append(
            dcc.Checklist(
                id={"type": "front_config", "index": f"filter_l_{i}"},
                options=filter_opts,
                labelStyle={"display": "block"},
                value=device.config["filter_l"],
            )
        )

        left_content_graph.children.append(
            html.Label(
                "Filter 50Hz",
                style={"font-weight": "bold", "display": "block", "margin-top": 10},
            )
        )
        left_content_graph.children.append(
            dcc.Checklist(
                id={"type": "front_config", "index": f"filt50Hz_l_{i}"},
                options=filt50Hz_opts,
                labelStyle={"display": "block"},
                value=device.config["filt50Hz_l"],
            )
        )

        left_content_graph.children.append(
            html.Label(
                "Detrend",
                style={"font-weight": "bold", "display": "block", "margin-top": 10},
            )
        )
        left_content_graph.children.append(
            dcc.Checklist(
                id={"type": "front_config", "index": f"detrend_l_{i}"},
                options=detrend_opts,
                labelStyle={"display": "block"},
                value=device.config["detrend_l"],
            )
        )

        left_content_graph.children.append(
            html.Div(
                [
                    html.Div(
                        id=f"lefttrigger_{i}",
                        children=[
                            html.Label(
                                "Active Triggers",
                                style={
                                    "font-weight": "bold",
                                    "display": "block",
                                    "margin-top": 10,
                                },
                            ),
                            dcc.Checklist(
                                id={
                                    "type": "front_config",
                                    "index": f"activetriggers_{i}",
                                },
                                options=filter_opts,
                                labelStyle={"display": "block", "height": 20},
                                value=device.config["activetriggers"],
                            ),
                        ],
                        style={
                            "width": "49%",
                            "display": "inline-block",
                            "vertical-align": "bottom",
                        },
                    ),
                    html_input_triggers,
                ]
            )
        )
        if device.config["type"] == "uldaq":
            # options_channel_selector
            left_content_graph.children.append(
                html.Div(
                    [
                        html.Label(
                            "Device Outputs",
                            style={
                                "font-weight": "bold",
                                "display": "block",
                                "margin-top": 10,
                            },
                        ),
                        html.Div(
                            children=[
                                html.Label("Active output", style={"display": "block"}),
                                dcc.RadioItems(
                                    id={
                                        "type": "front_config",
                                        "index": f"active_output_{i}",
                                    },
                                    options=[
                                        {"label": "True", "value": True},
                                        {"label": "False", "value": False},
                                    ],
                                    value=device.config["active_output"],
                                ),
                            ]
                        ),
                        html.Div(
                            children=[
                                html.Div(
                                    style={"display": "inline-block", "width": 150},
                                    children=[
                                        html.Label("Low Channel", style={"display": "block"}),
                                        dcc.Input(
                                            id={
                                                "type": "front_config",
                                                "index": f"low_channel_out_{i}",
                                            },
                                            type="number",
                                            value=device.config["low_channel_out"],
                                        ),
                                    ],
                                ),
                                html.Div(
                                    style={"display": "inline-block", "width": 150},
                                    children=[
                                        html.Label("High Channel", style={"display": "block"}),
                                        dcc.Input(
                                            id={
                                                "type": "front_config",
                                                "index": f"high_channel_out_{i}",
                                            },
                                            type="number",
                                            value=device.config["high_channel_out"],
                                        ),
                                    ],
                                ),
                            ]
                        ),
                        html.Label("Output frequency", style={"display": "block"}),
                        dcc.Input(
                            id={"type": "front_config", "index": f"output_freq_{i}"},
                            type="number",
                            step=0.01,
                            value=device.config["output_freq"],
                        ),
                        html.Label("Output amplitude", style={"display": "block"}),
                        dcc.Input(
                            id={"type": "front_config", "index": f"output_amp_{i}"},
                            type="number",
                            step=0.01,
                            value=device.config["output_amp"],
                        ),
                        html.Label("Output offset", style={"display": "block"}),
                        dcc.Input(
                            id={"type": "front_config", "index": f"output_offset_{i}"},
                            type="number",
                            step=0.01,
                            value=device.config["output_offset"],
                        ),
                        html.Label("Sweep min Frequenz", style={"display": "block"}),
                        dcc.Input(
                            id={
                                "type": "front_config",
                                "index": f"output_sweep_f0_{i}",
                            },
                            type="number",
                            step=0.1,
                            value=device.config["output_sweep_f0"],
                        ),
                        html.Label("Sweep max Frequenz", style={"display": "block"}),
                        dcc.Input(
                            id={
                                "type": "front_config",
                                "index": f"output_sweep_f1_{i}",
                            },
                            type="number",
                            step=0.1,
                            value=device.config["output_sweep_f1"],
                        ),
                        html.Label("Sweep time", style={"display": "block"}),
                        dcc.Input(
                            id={"type": "front_config", "index": f"output_sweep_T_{i}"},
                            type="number",
                            step=0.1,
                            value=device.config["output_sweep_T"],
                        ),
                        html.Label("Output type", style={"display": "block"}),
                        dcc.RadioItems(
                            id={"type": "front_config", "index": f"output_form_{i}"},
                            options=[
                                {"label": "Sine wave", "value": "sine"},
                                {"label": "Square wave", "value": "rect"},
                                {"label": "White Noise", "value": "white_noise"},
                                {
                                    "label": "Sine sweep exp",
                                    "value": "sine_sweep_exponential",
                                },
                                {
                                    "label": "Sine sweep lin",
                                    "value": "sine_sweep_linear",
                                },
                            ],
                            labelStyle={"display": "block"},
                            value=device.config["output_form"],
                        ),
                        html.Label(
                            "Control please only select one Channel",
                            style={"display": "block", "font-weight": "bold"},
                        ),
                        create_pid_channel_selector(bend, device),
                        html.Label(
                            "Setpoint",
                            style={"display": "block", "font-weight": "bold"},
                        ),
                        dcc.Input(
                            id={
                                "type": "front_config",
                                "index": f"output_setpoint_{i}",
                            },
                            type="number",
                            step=0.01,
                            value=device.config["output_setpoint"],
                        ),
                    ]
                )
            )

    left_content_graph.children.append(
        html.Div(children=[], style={"margin-top": 20}),
    )
    return left_content_graph


def create_eval_channel_selector(bend):
    div_out = html.Div(children=[])

    for i, device in enumerate(bend.measurement_devices):
        div_out.children.append(
            html.Label(
                f'{
                    device.config["type"]}{
                    device.number}: {
                    device.config["device"]["product_name"]}'
            )
        )
        options = []
        for channel in device.config["channels_on"]:
            options.append({"label": f"Channel {channel}", "value": channel})
        div_out.children.append(
            dcc.Checklist(
                id={"type": "front_config", "index": f"eval_channels_{i}"},
                options=options,
                value=device.config["eval_channels"],
            )
        )

    return div_out


def create_pid_channel_selector(bend, device_out):
    div_out = html.Div(children=[])

    for i, device in enumerate(bend.measurement_devices):
        options = []
        value = []
        div_out.children.append(
            html.Label(
                f'{
                    device.config["type"]}{
                    device.number}: {
                    device.config["device"]["product_name"]}'
            )
        )
        for channel in device.channels:
            channelnum = channel.channel_num
            options.append({"label": f"Channel {channelnum}", "value": channelnum})
            if device_out in channel.controlled_devices:
                value.append(channelnum)
                print("wtf")
        div_out.children.append(
            dcc.Checklist(
                id={
                    "type": "front_config_pid",
                    "index": f"control_channel{device_out.number}{i}",
                },
                options=options,
                value=value,
            )
        )
    return div_out
