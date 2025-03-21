"""actually reads other files

Returns:
    [type]: [description]
"""

# from read_pickle import *
import csv
import math
import iir_filter
import matplotlib.pyplot as plt
import lzma
from IIR import IIR_GeophoneFilter
from utility_funs import init_figure_2_traces
import logging
import pandas as pd
import numpy as np
from scipy.fft import fft, fftfreq
import datetime
import pickle
from scipy import signal
from tkinter import Tk
from tkinter.filedialog import askopenfilename, askdirectory
import plotly.graph_objs as go
import os
import plotly.io as pio

pio.renderers.default = "browser"

# from daqhats import (hat_list, mcc128, HatIDs, OptionFlags, AnalogInputMode,
#                     AnalogInputRange)


def getfilenames(multiple=True, initialdir="/home/pi/Measurements_web_app"):
    """funktion that opens a file explorer window and returns the manually selected files
    the root windo is set to the root window of the saves of the dash app
    returns a list of filenames"""
    root = Tk()
    root.withdraw()
    root.update()
    root.wm_attributes("-topmost", 1)
    filenames = askopenfilename(multiple=multiple, initialdir=initialdir)
    root.destroy()
    return filenames


def getfilenames_from_directory(initialdir="/home/pi/Measurements_web_app"):
    """funktion that opens a file explorer window and returns the manually selected files
    the root windo is set to the root window of the saves of the dash app
    returns a list of filenames"""
    root = Tk()
    root.withdraw()
    root.update()
    root.wm_attributes("-topmost", 1)
    dir = askdirectory(initialdir=initialdir)

    root.destroy()

    list_of_files = []
    for root, dirs, files in os.walk(top=dir, topdown=True):
        for i, file in enumerate(files):
            list_of_files.append(os.path.join(root, file))

    return list_of_files


def check_coherent_dates(filenames):
    """
    splits the given file list in smaller lists of files that can be merged
    """
    outlist = []  # the actual returned list
    currentlist = []  # list that temporarily saves the related files
    i = 0
    for i, filename in enumerate(filenames):
        if i == 0:
            with lzma.open(filename, "rb") as handle:
                (meta, _) = pickle.load(handle)
            currentlist = [filename]
        else:
            with lzma.open(filename, "rb") as handle:
                (meta_n, _) = pickle.load(handle)
            if meta["t_end"] == meta_n["t_start"]:
                meta["t_end"] = meta_n["t_end"]
                currentlist.append(filename)
            else:
                outlist.append(currentlist)
                currentlist = [filename]
                meta = meta_n
    outlist.append(currentlist)
    return outlist


def read_pickle(filenames=None, filter_all=False):
    """function that reads a pickle files from a list of filepathes
    those can be get by the function getfilenames(if == None) or directly passed
    returns
        meta: a dictionary with information about the measured data such as time, samples rate etc
        channel_data_list: a list each element stores the measured data of a channel raw
        channel_data_list_filtered: a list each element stores the measured data of a channel filtered
        total_points: number of measurement points per channel
        time_vector: an estimated vector of datetimes for each element
        list_of_indizes_of_max_values_raw: a list each element stores the indice of the maximum value of the channel during the measurement (raw)
        list_of_indizes_of_max_values_filtered: a list each element stores the indice of the maximum value of the channel during the measurement (filtered)
    """
    if filenames is None:
        filenames = getfilenames()

    filenames = list(filenames)
    filenames.sort()

    for num_file, filename in enumerate(filenames):
        if num_file == 0:
            with lzma.open(filename, "rb") as handle:
                (meta_l, channel_data_list) = pickle.load(handle)
                print(filename)
        else:
            with lzma.open(filename, "rb") as handle:
                (meta_l_n, channel_data_list_n) = pickle.load(handle)
            # if meta_l[0]['t_end']==meta_l_n[0]['t_start']:
            for i, meta in enumerate(meta_l):
                meta_l[i]["t_end"] = meta_l_n[i]["t_end"]
            for i, channel_data_n in enumerate(channel_data_list_n):
                channel_data_list[i] = np.append(channel_data_list[i], channel_data_n)
            print(filename)
            # else:
            # filenames.remove(filename)
            # logging.warning(f'file {filename} does not match with previous file')
        logging.info(f"read the following files :{filenames}")
    channel_data_list_filtered = []

    time_vectors = []

    for meta in meta_l:
        # print(meta)
        j = 0
        IIRFilter = IIR_GeophoneFilter(
            fv=0.4,
            fn=0.25,
            f1=meta["natural_frequency"][j],
            d1=meta["damping"][j],
            f2=0.25,
            d2=1.0,
            T=1 / meta["sample_rate"],
            Bandbegrenzung=True,
            f_bb_u=1.0,
            f_bb_o=80.0,
            Poles_Zeros=True,
            KB_Filter=False,
            fv_fn=True,
            bstop50Hz=True,
        )
        for channel in meta["channels_on"]:
            channel_data_list_filtered.append(IIRFilter.filter_fun2(channel_data_list[j]))
            len_dat = len(channel_data_list[j])
            time_vectors.append(
                pd.date_range(
                    meta["t_end"] - datetime.timedelta(seconds=len_dat // meta["sample_rate"]),
                    meta["t_end"],
                    periods=len_dat,
                )
            )
            j += 1
    for channel_data in channel_data_list:
        max_val_ind = np.argmax(channel_data)
        # list_of_indizes_of_max_values_raw.append(max_val_ind)
    list_of_indizes_of_max_values_filtered = []
    for channel_data in channel_data_list_filtered:
        max_val_ind = np.argmax(channel_data)
        list_of_indizes_of_max_values_filtered.append(max_val_ind)

    return meta_l, channel_data_list, time_vectors, channel_data_list_filtered


def getfilenames_from_datetimes(
    start_date=datetime.datetime.now() - datetime.timedelta(minutes=30),
    end_date=datetime.datetime.now(),
    directory_path="/home/pi/Measurements_web_app/measurements",
):
    """checks the saved files and converts the names to datetimes which are than compared to the given datetimes

    Args:
        start_date ([datetime], optional): [description]. Defaults to datetime:now-30min.
        end_date ([datetime], optional): [description]. Defaults to datetime.now.
        directory_path (str, optional): [description]. Defaults to '/home/pi/Measurements_web_app/measurements'.

    Returns:
        [type]: [description]
    """
    list_of_files = []
    for root, dirs, files in os.walk(top=directory_path, topdown=True):
        for i, file in enumerate(files):
            try:
                filedate = datetime.datetime.fromisoformat(file[:26])
                if start_date <= filedate <= end_date:
                    list_of_files.append(os.path.join(root, file))
            except Exception as e:
                logging.warning(f"error getting date: {e} file: {file}")
    return list_of_files


def create_daqhat_df(loaded_data):
    (
        meta,
        channel_data_list,
        channel_data_list_filtered,
        total_points,
        time_vector,
        _,
        _,
    ) = loaded_data
    df_daqhat = pd.DataFrame()
    df_daqhat["time"] = time_vector
    index = 0
    for channel in meta["channels_on"]:
        df_daqhat[
            f'Channel {channel}_raw: {
                meta["quantity"][channel]} in {
                meta["units"][channel]}'
        ] = channel_data_list[index]
        df_daqhat[
            f'Channel {channel}_filtered: {
                meta["quantity"][channel]} in {
                meta["units"][channel]}'
        ] = channel_data_list_filtered[index]
        index += 1
    return df_daqhat


def read_pickle_geophone_data(
    filenames=None, Geophone_Filter=True, Band_Filter=False, KB_Filter=False
):
    """function that reads a pickle files from a list of filepathes
    those can be get by the function getfilenames(if == None) or directly passed
    returns
        meta: a dictionary with information about the measured data such as time, samples rate etc
        channel_data_list: a list each element stores the measured data of a channel raw
        channel_data_list_filtered: a list each element stores the measured data of a channel filtered
        total_points: number of measurement points per channel
        time_vector: an estimated vector of datetimes for each element
        list_of_indizes_of_max_values_raw: a list each element stores the indice of the maximum value of the channel during the measurement (raw)
        list_of_indizes_of_max_values_filtered: a list each element stores the indice of the maximum value of the channel during the measurement (filtered)
    """
    if filenames is None:
        filenames = getfilenames()

    filenames = list(filenames)
    filenames.sort()

    for num_file, filename in enumerate(filenames):
        if num_file == 0:
            with lzma.open(filename, "rb") as handle:
                (meta_l, channel_data_list) = pickle.load(handle)
                print(filename)
        else:
            with lzma.open(filename, "rb") as handle:
                (meta_l_n, channel_data_list_n) = pickle.load(handle)
            # if meta_l[0]['t_end']==meta_l_n[0]['t_start']:
            for i, meta in enumerate(meta_l):
                meta_l[i]["t_end"] = meta_l_n[i]["t_end"]
            for i, channel_data_n in enumerate(channel_data_list_n):
                channel_data_list[i] = np.append(channel_data_list[i], channel_data_n)
            print(filename)
            # else:
            # filenames.remove(filename)
            # logging.warning(f'file {filename} does not match with previous file')
        logging.info(f"read the following files :{filenames}")

    # Zeitvektoren erstellen
    time_vectors = []
    for meta in meta_l:
        # print(meta)
        j = 0
        for channel in meta["channels_on"]:
            len_dat = len(channel_data_list[j])
            time_vectors.append(
                pd.date_range(
                    meta["t_end"] - datetime.timedelta(seconds=len_dat // meta["sample_rate"]),
                    meta["t_end"],
                    periods=len_dat,
                )
            )
        j += 1

        # Signal filtern oder nicht
        channel_data_list_filtered = channel_data_list

        if Geophone_Filter:
            for meta in meta_l:
                print("Geofilt")
                j = 0
                IIRFilter = IIR_GeophoneFilter(
                    fv=0.4,
                    fn=0.25,
                    f1=meta["natural_frequency"][j],
                    d1=meta["damping"][j],
                    f2=0.25,
                    d2=1,
                    T=1 / meta["sample_rate"],
                    Bandbegrenzung=Band_Filter,
                    f_bb_u=1.0,
                    f_bb_o=80.0,
                    KB_Filter=KB_Filter,
                )
                for channel in meta["channels_on"]:
                    channel_data_list_filtered.append(IIRFilter.filter_fun2(channel_data_list[j]))
                    len_dat = len(channel_data_list[j])
                j += 1
                for channel_data in channel_data_list_filtered:
                    max_val_ind = np.argmax(channel_data)
                    # list_of_indizes_of_max_values_raw.append(max_val_ind)
                list_of_indizes_of_max_values_filtered = []
                for channel_data in channel_data_list_filtered:
                    max_val_ind = np.argmax(channel_data)
                    list_of_indizes_of_max_values_filtered.append(max_val_ind)

    return meta_l, time_vectors, channel_data_list_filtered


def load_csv_data(filename=None, skiprows=0, sep=";", decimal="."):
    if filename is None:
        filename = getfilenames(
            multiple=False,
            initialdir="C:/Users/anrothas/Nextcloud2/_SHARED/Geophone/soundkarte_werte",
        )
    df_csv = pd.read_csv(filename, skiprows=skiprows, sep=sep, index_col=False, decimal=decimal)
    return df_csv


def merge_pd(df_csv, df_daqhat, delta_t=0, save_csv=False, filename_out="merge.csv"):
    """requires same sample rate for both measurements"""
    df_csv["Messzeit[s]"] = df_csv["Messzeit[s]"] + delta_t
    df_daqhat["Messzeit[s]"] = (df_daqhat["time"] - df_daqhat["time"][0]).astype(
        "timedelta64[us]"
    ) * 1e-6
    df_merge = pd.merge_asof(
        df_daqhat, df_csv, on="Messzeit[s]", direction="nearest", tolerance=0.001
    )
    # df_csv['time']=[df_daqhat['time'][0]+datetime.timedelta(seconds=delta_t)+datetime.timedelta(seconds=i) for i in df_csv.iloc[:, 0]]
    if save_csv:
        df_merge.to_csv(filename_out, sep=";", decimal=",")
    return df_merge


def pickle_to_csv(filename_out=None, filenames=None):
    def format_date(date):
        return date.strftime("%d:%m:%Y %H:%M:%S.%f")

    if filenames is None:
        filenames = getfilenames()
    meta_l, channel_data_list, time_vectors, channel_data_list_filtered = read_pickle(filenames)
    j = 0
    df = pd.DataFrame()
    for i, config in enumerate(meta_l):
        time_column_name = f'time {config["device"]["product_name"]}'
        df = pd.concat([df, pd.DataFrame({time_column_name: time_vectors[j]})], axis=1)
        df[time_column_name + " formatted"] = df[time_column_name].apply(format_date)
        df = df.drop(time_column_name, axis="columns")
        for channel in config["channels_on"]:
            quantity = config["quantity"][channel]
            unit = config["units"][channel]
            print(len(channel_data_list[j]))
            df = pd.concat(
                [
                    df,
                    pd.DataFrame(
                        {f"Channel {channel}  {quantity} in {unit}": channel_data_list[j]}
                    ),
                ],
                axis=1,
            )
            df = pd.concat(
                [
                    df,
                    pd.DataFrame(
                        {
                            f"Channel {channel}  {quantity} in {unit} (filtered)": channel_data_list_filtered[
                                j
                            ]
                        }
                    ),
                ],
                axis=1,
            )
            j += 1

    if filename_out is None:
        # +config["device"]["product_name"]
        filename_out = filenames[0][:-2] + "csv"
    df.to_csv(filename_out, sep=";", decimal=",")
    print(f"saved csv at {filename_out}")
    return None


def read_channel_data(downsampling=1, filtered=True, KB_Filter=False, plot=False):
    filenames = getfilenames()
    meta_l, time_vectors, channel_data_list = read_pickle_geophone_data(
        filenames, Geophone_Filter=filtered, KB_Filter=KB_Filter
    )
    print(meta_l)
    t = np.array(100000)
    # data = np.array(100000)
    data = np.array(100000)

    for i, (channel_data, time_vector) in enumerate(zip(channel_data_list, time_vectors)):
        t = time_vector[::downsampling]
        data = channel_data[::downsampling]
        if plot:
            plt.plot(t, data)
            plt.title(filenames[i])

    if plot:
        plt.show()

    return t, data


def create_min_max_val_graph(time_interval=900):
    """creates a graph with the min max values of each channel in the given time_intervals"""

    def split(list_a, chunk_size):
        for i in range(0, len(list_a), chunk_size):
            yield list_a[i : i + chunk_size]

    filenames = getfilenames()
    meta_l, channel_data_list, time_vectors, channel_data_list_filtered = read_pickle(filenames)
    # print(meta_l)
    fig = init_figure_2_traces((meta_l))
    # downsampling=5
    i = 0
    for meta in meta_l:
        print(meta)
        num_points_per_interval = int(time_interval * meta["sample_rate"])
        for channel in meta["channels_on"]:
            fig["data"][i]["x"] = time_vectors[i // 2][::num_points_per_interval]
            fig["data"][i]["y"] = [
                max(chunk) for chunk in split(channel_data_list[i // 2], num_points_per_interval)
            ]
            i += 1
            fig["data"][i]["x"] = time_vectors[i // 2][::num_points_per_interval]
            fig["data"][i]["y"] = [
                min(chunk) for chunk in split(channel_data_list[i // 2], num_points_per_interval)
            ]
            i += 1
    pio.show(fig)


def calc_KBft(KB, dt, tau=0.125):
    dim = KB.size
    KB_Ft = np.zeros(dim)
    KB_Ft[0] = KB[0]
    m = 1 - math.exp(-dt / tau)

    for i in range(1, dim):
        KB_F_t = math.sqrt(
            math.pow(KB_Ft[i - 1], 2) + m * (math.pow(KB[i], 2) - math.pow(KB_Ft[i - 1], 2))
        )
        KB_Ft[i] = KB_F_t

    return KB_Ft


def calc_KBt(v, T):
    dim = v.size
    KB_t = np.zeros(dim)
    nyq = 0.5 / T
    sos_KB = signal.butter(1, 5.6 / nyq, "highpass", output="sos")
    iir_KB = iir_filter.IIR_filter(sos_KB)

    KB_t = [iir_KB.filter(value) for value in v]
    return KB_t


# berechnen der Taktmaximalwerte, des Taktmaximal-Effektivwertes und die
# Anzahl de Takte
def calc_KBFTi(KBFt, Takt=30):
    def split(list_a, chunk_size):
        for i in range(0, len(list_a), chunk_size):
            yield list_a[i : i + chunk_size]

    KBFT_i = [max(chunk) for chunk in split(KBFt, Takt)]

    KBFTm = 0
    N = len(KBFT_i)
    for i in range(0, N):
        if KBFT_i[i] <= 0.1:
            KBFT_i[i] = 0.0
        KBFTm += math.pow(KBFT_i[i], 2)

    KBFTm = math.sqrt(KBFTm / N)

    return KBFT_i, KBFTm, N


# Berechnen der absoluten Maxima je Zeitabschnit dt
def calc_max_v_dt(v, dT=600000):
    def split(list_a, chunk_size):
        for i in range(0, len(list_a), chunk_size):
            yield list_a[i : i + chunk_size]

    v_max_dt = [max(chunk) for chunk in split(v, dT)]
    return v_max_dt


def read_csv():
    rows = []
    with open("v-vkb.csv", "r") as file:
        csvreader = csv.reader(file, sep=";", decimal=",")
        header = next(csvreader)
        for row in csvreader:
            rows.append(row)
    print(header)
    print(rows)


class Channel:
    def __init__(self, meta, channel_num, measurement, data, time_vector, data_filtered) -> None:
        self.meta, self.channel_num, self.measurement = meta, channel_num, measurement
        self.data, self.time_vector, self.data_filtered = (
            data,
            time_vector,
            data_filtered,
        )
        quantity = self.meta["quantity"][channel_num]
        unit = self.meta["units"][channel_num]
        device_str = f"{self.meta['type']}"
        self.name = f"{device_str}  Channel {channel_num}  {quantity} in {unit}"

    def create_trace(self, downsampling=1):
        trace = go.Scatter(
            x=self.time_vector[::downsampling],
            y=self.data[::downsampling],
            name=self.name,
        )
        return trace

    def fft_on_channel(self):
        N = len(self.data)
        xf = fftfreq(N, 1 / self.meta["sample_rate"])[: N // 2]
        yf = fft(self.data)
        return xf, yf

    def create_trace_fft(self):
        xf, yf = self.fft_on_channel()
        trace = go.Scatter(x=xf, y=np.abs(yf))
        return trace


class Measurement:
    def __init__(self) -> None:
        (
            self.meta_l,
            self.channel_data_list,
            self.time_vectors,
            self.channel_data_list_filtered,
        ) = read_pickle()
        self.channels = []
        i = 0
        for meta in self.meta_l:
            print(meta)
            for channel_num in meta["channels_on"]:
                self.channels.append(
                    Channel(
                        meta,
                        channel_num,
                        self,
                        self.channel_data_list[i],
                        self.time_vectors[i],
                        self.channel_data_list_filtered[i],
                    )
                )
                i += 1

    def create_graph_all_channel(self, downsampling=1, filtered=False):
        fig = go.Figure()
        for channel in self.channels:
            fig.add_trace(channel.create_trace())
        return fig

    def create_graph_all_channel_fft(self, downsampling=1, filtered=False):
        fig = go.Figure()
        for channel in self.channels:
            fig.add_trace(channel.create_trace_fft())
        return fig

    def create_min_max_val_graph(time_interval=900, filtered=False):
        """creates a graph with the min max values of each channel in the given time_intervals"""

        def split(list_a, chunk_size):
            for i in range(0, len(list_a), chunk_size):
                yield list_a[i : i + chunk_size]

        filenames = getfilenames()
        meta_l, channel_data_list, time_vectors, channel_data_list_filtered = read_pickle(filenames)
        # print(meta_l)
        fig = init_figure_2_traces((meta_l))
        # downsampling=5
        i = 0
        for meta in meta_l:
            print(meta)
            num_points_per_interval = int(time_interval * meta["sample_rate"])
            for channel in meta["channels_on"]:
                fig["data"][i]["x"] = time_vectors[i // 2][::num_points_per_interval]
                fig["data"][i]["y"] = [
                    max(chunk)
                    for chunk in split(channel_data_list[i // 2], num_points_per_interval)
                ]
                i += 1
                fig["data"][i]["x"] = time_vectors[i // 2][::num_points_per_interval]
                fig["data"][i]["y"] = [
                    min(chunk)
                    for chunk in split(channel_data_list[i // 2], num_points_per_interval)
                ]
                i += 1
        pio.show(fig)


if __name__ == "__main__":
    # print(getfilenames_from_directory())
    mes = Measurement()
    fig = mes.create_graph_all_channel()
    fig.write_html("first_figure.html", auto_open=True)
    # fig.show()
    # fig = mes.create_graph_all_channel_fft(filtered=True)
    # fig.show()
    # read_channel_data(plot=True)
    # read_pickle_geophone_data(Geophone_Filter=True, Band_Filter=True,KB_Filter=False)
    # pickle_to_csv()
