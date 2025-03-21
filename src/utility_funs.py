import socket
import pickle
import lzma
import logging
import os
from flask import request
import numpy as np
from tkinter import Tk
from tkinter.filedialog import askopenfilename, askdirectory
from colorama import Fore

import csv


def save_arrays_to_csv(filename, x_array, y_array):
    """
    Save two NumPy arrays into a CSV file with two columns.

    Parameters:
    - filename: str, name of the CSV file
    - x_array: numpy array (first column)
    - y_array: numpy array (second column)
    """
    # Ensure both arrays have the same length
    assert len(x_array) == len(y_array), "Error: Arrays must have the same length!"

    # Save to CSV
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["X", "Y"])  # Header row
        for x, y in zip(x_array, y_array):  # Iterate row-wise
            writer.writerow([x, y])  # Write each row

    print(f"CSV file '{filename}' saved successfully!")


def printc(Color=Fore.CYAN, Text="Hello!"):
    print(Color, Text)


def clean_full_filename(path_filename):
    return "".join(
        "_" if char in '<>"/:\\|?*' else char for char in path_filename
    )  # sonderzeichen entfernen


def get_measurement_paths(config):
    """paths for data storage"""
    measurement_paths = dict(
        path_measurements=os.path.join(config["data_path"], "measurements"),
        path_trigger_reports=os.path.join(config["data_path"], "reports"),
        path_daily_reports=os.path.join(config["data_path"], "daily_reports"),
    )
    return measurement_paths


def get_ip_address():
    """Utility function to get the IP address of the device."""
    ip_address = "127.0.0.1"  # Default to localhost
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("1.1.1.1", 1))  # Does not have to be reachable
        ip_address = sock.getsockname()[0]
    except BaseException:
        pass
    finally:
        sock.close()
    # print('------------------>ip_address: ', ip_address)
    return ip_address


def shutdown():
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()


def find_nearest(array, value):  # utillity function to find the closest value in an array
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx, array[idx]


def save_xz(filename, data, args):
    print(
        "save_xz ---> ",
        filename,
    )
    with lzma.open(filename, "wb") as f:
        pickle.dump(data, f)
    if args == "report":
        logging.info("created trigger report: " + args)
    else:
        logging.info("saved data reason: " + args)
    return None


def flatten(t):
    return [item for sublist in t for item in sublist]


def create_meta(device, t0, t_end):
    """creates a dict that has, hopfully, all necessary data which are needed to describe the measurement"""
    meta = device.config
    meta["t_start"] = t0
    meta["t_end"] = t_end
    return meta


def init_figure(config_list):
    """initializes the figure used in the layout"""
    legend = dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    figure = dict(data=[], layout={"title_text": "time", "legend": legend})

    for i, config in enumerate(config_list):
        for channel in config["channels_on"]:
            quantity = config["quantity"][channel]
            unit = config["units"][channel]
            figure["data"].append(dict(x=[], y=[], name=f"Channel {channel}  {quantity} in {unit}"))
    return figure


def init_figure_2_traces(config_list):
    """2 traces per channel"""
    legend = dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    figure = dict(
        data=[],
        layout={"title_text": "time", "yaxis_range": [None, None], "legend": legend},
    )
    for i, config in enumerate(config_list):
        for channel in config["channels_on"]:
            quantity = config["quantity"][channel]
            unit = config["units"][channel]
            figure["data"].append(dict(x=[], y=[], name=f"Channel {channel}  {quantity} in {unit}"))
            figure["data"].append(
                dict(x=[], y=[], name=f"_Channel {channel}  {quantity} in {unit}")
            )
    return figure


def gen_sin(x, a, b, f, c):
    """generell sinus function for fitting purposes"""
    return a + b * np.sin(2 * np.pi * f * x + c)


def fit_r_2(xdata, ydata, params, model, max_nfev=100):
    result = model.fit(ydata, params, x=xdata, max_nfev=100)
    ydata = np.array(ydata, dtype="double")
    r_2 = 1 - result.residual.var() / np.var(ydata)
    return (result.params, r_2)


def hidden_or_visible(bool_var):
    if bool_var:
        return {"display": "block"}
    else:
        return {"display": "none"}


def custom_filenames(multiple=True, initialdir=None):
    root = Tk()
    root.withdraw()
    root.update()
    root.wm_attributes("-topmost", 1)
    filenames = askopenfilename(multiple=multiple, initialdir=initialdir)
    return filenames


def custom_directory():
    root = Tk()
    root.withdraw()
    root.update()
    root.wm_attributes("-topmost", 1)
    filenames = askdirectory()
    return filenames
