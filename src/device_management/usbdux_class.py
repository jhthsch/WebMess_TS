from config.config_dat import read_config_device
from device_management.general_device import Measurement_device
try:
    import pyusbdux as dux
except ImportError:
    dux = None
import sys
import os
import inspect
from collections import deque
import numpy as np
from time import sleep

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)


def find_usbdux_devices() -> list[dict]:
    device_list = []
    i = 0
    while True:
        try:
            dux.open(i)
            device = dict(ID=i, product_name=dux.get_board_name())
            device_list.append(device)
            i += 1

        except Exception:
            # print(e)
            break
    return device_list


class USBDuxDevice(Measurement_device):
    """setup everything to get usbdux devices runnging"""

    any_devices_open = False

    def __init__(self, number, backend=None) -> None:
        """_summary_

        Args:
            number (_type_): _description_
            backend (_type_, optional): _description_. Defaults to None.
        initialize all device parameters read from the config_usbduxX.ini
        file.


        """
        self.type = "usbdux"
        super().__init__(self.type, number, backend)
        self.channels_on = self.config["channels_on"]
        self.sample_rate = self.config["sample_rate"]
        self.input_range = self.config["input_range"]
        self.input_mode = self.config["input_mode"]
        self.config["device"]
        # self.device_name = device_name['Device_Name']
        self.is_running = False
        self.is_paused = False
        self.data_out = None  # np.empty(shape=(len(self.channels_on), self.sample_rate))
        self.buffer_queue = deque()

    def stop_clean_up(self):
        if self.__class__.any_devices_open:
            try:
                dux.stop()
            except BaseException:
                pass
            try:
                dux.close()
            except BaseException:
                pass
        self.__class__.any_devices_open = False

    class DataCallback(dux.Callback):
        def __init__(self, outer):  # acces outer class
            super().__init__()  # the initial __initfunction of dux.Callback
            self.outer = outer

        def hasSample(self, sample):  # sample arrived
            self.outer.add_sample(sample)

    def start_scan_sub(self):
        self.config = read_config_device(self.type, self.number)
        self.buffer_ind = 0
        self.config["channels_on"] = [*range(self.config["num_channels"])]
        try:
            self.config["device"]["ID"] = int(self.config["device"]["ID"])
        except BaseException:
            print("issue with id setting it to 0")
            self.config["device"]["ID"] = 0
        print(f"trzing to open device {self.config['device']['ID']}")
        dux.open(self.config["device"]["ID"])
        print("device opened")
        # callback to fill buffer

        self.cb = self.DataCallback(self)
        # print(self.cb,self.config['num_channels'],self.config['sample_rate'])
        dux.start(self.cb, self.config["num_channels"], self.config["sample_rate"])
        self.__class__.any_devices_open = True
        self.config["sample_rate"] = dux.getSamplingRate()
        self.measuredchannels = self.config["channels_on"]
        return self.config, self.measuredchannels

    def add_sample(self, sample):

        self.buffer_queue.append(sample[: self.config["num_channels"]])  #

    def read_buffer(self):
        # print(list(self.buffer_queue))
        # print(np.array(list(self.buffer_queue)).shape)
        data_out = np.transpose(np.array(list(self.buffer_queue)))
        # print(data_out[0])
        self.buffer_queue.clear()
        # print(data_out[])
        for i, channel in enumerate(self.channels):
            data_out[i, :] = data_out[i, :] * self.config["scalingfactor"][channel.channel_num]
        self.add_numpy_data_to_buffer(data_out)
        # print (data_out)


if __name__ == "__main__":

    usbdux_devices = find_usbdux_devices()

    # duxdev1 = USBDuxDevice(0)
    # duxdev2 = USBDuxDevice(1)
    # duxdev1.start_scan()
    # duxdev2.start_scan()
    # print("measuring")
    # sleep(2)
    # print(10)
    # duxdev1.stop_clean_up()
    # print(11)
    # duxdev2.stop_clean_up()
    import plotly.graph_objects as go

    fig = go.Figure()
    dux_dev = USBDuxDevice(0)
    dux_dev.start_scan()
    for i in range(10):
        sleep(0.5)
        dux_dev.read_buffer()

    for channel in dux_dev.channels:
        y = channel.buffer
        fig.add_trace(x=go.Scatter(x=range(len()), name=channel.channel_num))
    fig.show()
