# third party
from datetime import datetime
from collections import deque
from config.config_dat import device_config_path, read_config_device
import numpy as np
from scipy import signal
import logging
from lmfit import Model

# self developed scripts
from IIR import IIR_GeophoneFilter

# from custom_email import *
from utility_funs import gen_sin


# from web_server_AR_new import restart_after_error


class Channel:
    """
    Class that holds all properties of a channel such as buffer, filter properties, name, etc.
    """

    def __init__(self, channel_num, config):
        self.channel_num = channel_num
        self.quantity = config["quantity"][channel_num]
        self.unit = config["units"][channel_num]
        self.model = Model(gen_sin)
        self.IIRFilter = IIR_GeophoneFilter(
            fv=0.5,
            fn=0.6,
            f1=config["natural_frequency"][channel_num],
            d1=config["damping"][channel_num],
            f2=0.25,
            d2=1.0,
            T=1 / float(config["sample_rate"]),
            Bandbegrenzung=True,
            f_bb_u=0.8,
            f_bb_o=100.0,
        )
        self.params_sinus = self.model.make_params(a=0.0, b=1.0, f=1.0, c=0.0)
        self.params_sinus["a"].max = 10
        self.params_sinus["a"].min = -10
        self.params_sinus["b"].max = 10
        self.params_sinus["b"].min = -10
        self.params_sinus["f"].max = 800
        self.params_sinus["f"].min = 0.1
        self.params_sinus["c"].max = 2 * np.pi
        self.params_sinus["c"].min = 0
        self.sinus_r2 = 0
        self.data = []
        self.fit_queue = deque(maxlen=100)
        self.buffer = deque()
        self.buffers_graph = deque(maxlen=100)
        self.max_value = 0
        self.max = 0
        self.min = 0
        self.peak_peak = 0
        self.average = 0
        self.fft_frequs = []
        self.fft_vals = []
        self.controlled_devices = []
        self.setpoint = None
        self.statistic_values = {}
        return None

    def calc_statistic_values(self, channel_num):
        from scipy.integrate import simps
        from scipy.stats import skew, kurtosis

        data = np.array(self.buffer)
        self.statistic_values["Max"] = np.max(data)
        self.statistic_values["Index Minimum"] = data.argmin()
        self.statistic_values["Min"] = np.min(data)
        self.statistic_values["Index Maximum"] = data.argmax()
        self.statistic_values["Peak to peak"] = np.ptp(data)
        self.statistic_values["Median"] = np.median(data)
        self.statistic_values["Average"] = np.average(data)
        self.statistic_values["STD"] = np.std(data)
        self.statistic_values["Variance"] = np.var(data)
        self.statistic_values["Corrcoef"] = np.corrcoef(data)
        self.statistic_values["Integral_trapez"] = np.trapz(data, dx=1 / 2000)
        self.statistic_values["Integral_simps"] = simps(data, dx=1 / 2000)
        self.statistic_values["RMS"] = np.sqrt(np.mean(np.square(data)))
        self.statistic_values["Skewness"] = skew(data, axis=0, bias=True)
        self.statistic_values["Kurtosis"] = kurtosis(data, axis=0, bias=True)
        return self.statistic_values

    def data_detrend(self, type="constant"):
        """Removes a trend from the collected data.

        Args:
            type (str): Type of detrending ('linear', 'constant').
        """
        from scipy.signal import detrend

        return detrend(self.data, type)

    def data_filt50Hz(self, n=4, fu=49, fo=51):
        import iir_filter

        sos_bstop50Hz = signal.butter(
            n, [fu / self.fs * 2, fo / self.fs * 2], "bandstop", output="sos"
        )
        iir_bstop50Hz = iir_filter.IIR_filter(sos_bstop50Hz)
        return [iir_bstop50Hz.filter(value) for value in self.data]

    def apply_filter(self, order=2, cutoff=0.1, filter_type="low"):
        """Applies a Butterworth filter to the collected data.

        Args:
            order (int): Order of the filter.
            cutoff (float): Cutoff frequency of the filter, relative to the Nyquist frequency.
            filter_type (str): Type of the filter ('low', 'high', 'bandpass').
        """
        from scipy.signal import filtfilt, butter

        b, a = butter(order, cutoff, btype=filter_type)
        return filtfilt(b, a, self.data)


class Measurement_device:
    """Class that maps on DAQ hat and other devices
    device_type: 0 DAQ hat
    device_type: 1 ULDAQ device
    """

    def __init__(self, device_type, number, backend):
        self.number = number
        self.backend = backend
        self.channels = []
        self.config = read_config_device(device_type, self.number)
        self.configpath = device_config_path(device_type, number)
        import iir_filter

        fs = self.config["sample_rate"]
        n = 4
        fu = 49
        fo = 51
        sos_bstop50Hz = signal.butter(n, [fu / fs * 2, fo / fs * 2], "bandstop", output="sos")
        iir_bstop50Hz = iir_filter.IIR_filter(sos_bstop50Hz)
        self.iirfilt50Hz = iir_bstop50Hz

    def start_scan(self):
        """Initializes buffer and starts scan of device"""
        self.scan_segment_start = datetime.now()
        self.t0 = self.scan_segment_start
        self.config, self.measuredchannels = self.start_scan_sub()
        self.CHANNEL_COUNT = len(self.measuredchannels)
        self.channels = []
        for channel_num in self.measuredchannels:
            self.channels.append(Channel(channel_num, self.config))
        return None

    def start_scan_sub(self):
        """This is a placeholder for device-specific functions. If called, it returns an error."""
        logging.error("start_scan_sub function needs to be called from a child class")

    def stop_clean_up(self):
        """This is a placeholder for device-specific functions. If called, it returns an error."""
        logging.error("stop_clean_up function needs to be called from a child class")

    def put_raw_data_into_numpy_data(self, data_in):
        """Takes the raw output of a measurement device and multiplies it with the scaling factor.
        Returns a 2-dimensional numpy array where the first dimension is the channel and the second dimension is the time.
        """
        numpy_data = np.empty((self.CHANNEL_COUNT, len(data_in) // self.CHANNEL_COUNT))
        for i, channel in enumerate(self.channels):
            numpy_data[i, :] = (
                np.array(data_in[i :: self.CHANNEL_COUNT])
                * self.config["scalingfactor"][channel.channel_num]
            )
        return numpy_data

    def add_numpy_data_to_buffer(self, numpy_data):
        """Takes numpy data from a measurement device (2-dimensional np array where dim1: channel, dim2: time)
        and merges it with the time the measurement has been taken.
        The data is checked for its maximum and if the respective channel threshold (if set) is reached.
        """
        if numpy_data.shape[1] == 0:
            return None
        self.time_last_mes = datetime.now()
        for i, channel in enumerate(self.channels):
            data_channel = numpy_data[i, :]
            if channel.channel_num in self.config["filter_l"]:
                data_channel_fil = channel.IIRFilter.filter_fun2(data_channel)
                eval_data = data_channel_fil
            else:
                eval_data = data_channel

            if channel.channel_num in self.config["detrend_l"]:
                eval_data = signal.detrend(eval_data, type="constant")
            if channel.channel_num in self.config["filt50Hz_l"]:
                eval_data = [self.iirfilt50Hz.filter(value) for value in eval_data]

            data_channel_max = np.max(np.abs(eval_data))
            if data_channel_max > channel.max_value:
                channel.max_value = data_channel_max
            if self.backend is not None:
                if (
                    channel.channel_num in self.config["activetriggers"]
                    and not self.backend.is_triggered
                    and self.config["threshold_list"][i] != 0
                ):
                    self.backend.check_trigger(
                        data_channel_max,
                        self.config["threshold_list"][i],
                        channel.channel_num,
                    )

            channel.buffer.append([data_channel, [self.scan_segment_start, self.time_last_mes]])
            channel.fit_queue.append([eval_data, [self.scan_segment_start, self.time_last_mes]])
            channel.buffers_graph.append([eval_data, [self.scan_segment_start, self.time_last_mes]])
        self.scan_segment_start = self.time_last_mes
        return None
