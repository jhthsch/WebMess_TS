import nidaqmx
from device_management.general_device import Measurement_device
from nidaqmx.stream_readers import AnalogMultiChannelReader
from nidaqmx.constants import AcquisitionType
import sys
import os
import inspect
import queue
import numpy as np

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)


def find_nidaqmx_devices():
    local_system = nidaqmx.system.System.local()
    driver_version = local_system.driver_version

    nidaqmx_driver_version = "DAQmx {0}.{1}.{2}".format(
        driver_version.major_version,
        driver_version.minor_version,
        driver_version.update_version,
    )
    print(nidaqmx_driver_version)
    dev_list = []
    for device in local_system.devices:
        dev_list.append(
            dict(
                Device_Name=device.name,
                Product_Category=str(device.product_category),
                product_name=device.product_type,
            )
        )
        # "Device Name: {0}, Product Category: {1}, Product Type: {2}".format(
        #        device.name, device.product_category, device.product_type
        #    )
        # print('NI-Driver', nidaqmx_driver_version, 'nidaq_device:',device)
    return dev_list


class NidaqDevice(Measurement_device):
    """setup everything to get nidaqmx devices runnging"""

    def __init__(self, number, backend=None) -> None:
        """_summary_

        Args:
            number (_type_): _description_
            backend (_type_, optional): _description_. Defaults to None.
        initialize all device parameters read from the config_nidaqmxX.ini
        file.


        """
        self.type = "nidaqmx"
        super().__init__(self.type, number, backend)
        self.channels_on = self.config["channels_on"]
        self.sample_rate = self.config["sample_rate"]
        self.input_range = self.config["input_range"]
        self.input_mode = self.config["input_mode"]
        device_name = self.config["device"]
        self.device_name = device_name["Device Name: "]
        self.task = None
        self.is_running = False
        self.is_paused = False
        self.data_out = None  # np.empty(shape=(len(self.channels_on), self.sample_rate))
        self.q = queue.Queue()

    def create_task(self):
        """
        Create a read task
        """
        # print("reader input channels:", self.channels_on)
        try:
            self.task = nidaqmx.Task(self.device_name)
        except OSError:
            print("DAQ is not connected, task could not be created")
            return

        try:
            for ch in self.channels_on:
                channel_name = self.device_name + "/ai" + str(ch)
                self.task.ai_channels.add_ai_voltage_chan(channel_name)
                print(channel_name)
        except Exception as e:
            print(e)
            print("DAQ is not connected, channel could not be added")
            return

        self.task.timing.cfg_samp_clk_timing(
            rate=self.sample_rate, sample_mode=AcquisitionType.CONTINUOUS
        )
        self.task.start()
        self.is_running

        self.reader = AnalogMultiChannelReader(self.task.in_stream)
        self.data_out = np.empty(shape=(len(self.channels_on), self.sample_rate))

    def stop_clean_up(self):
        if self.is_running:
            self.task.stop()
            self.task.close()
        self.is_running = False

    def start_scan_sub(self):
        print("in start_scan_sub_nid")
        if not self.is_running:
            print("call task")
            self.create_task()
            self.is_running = True
        return self.config, self.channels_on

    def read_buffer(self):
        self.reader.read_many_sample(
            data=self.data_out, number_of_samples_per_channel=self.sample_rate
        )
        data_out = self.data_out
        while not self.q.empty():
            chunk = self.q.get()
            print(chunk.shape)
            data_out = np.concatenate((data_out, chunk), axis=0)
            data_out = data_out.transpose()
        for i, channel in enumerate(self.channels):
            data_out[i, :] = data_out[i, :] * self.config["scalingfactor"][channel.channel_num]
        self.add_numpy_data_to_buffer(data_out)
        # print (data_out)


if __name__:
    find_nidaqmx_devices()
    # nidaq = NidaqDevice(None)
