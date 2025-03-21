from device_management.general_device import Measurement_device
from config.config_dat import read_config_device
import platform
import numpy as np
import logging
import os
import sys
import inspect
from numpy import sin, pi, log, linspace

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

if platform.system() == "Linux":
    from uldaq import (
        get_daq_device_inventory,
        DaqDevice,
        AInScanFlag,
        AOutScanFlag,
        ScanOption,
        ScanStatus,
        create_float_buffer,
        InterfaceType,
        AiInputMode,
        IepeMode,
        CouplingMode,
    )


def find_uldaq_devices():
    devices_local = get_daq_device_inventory(InterfaceType.ANY)
    return devices_local


class Uldevice(Measurement_device):
    def __init__(self, number, backend=None) -> None:
        self.type = "uldaq"
        super().__init__(self.type, number, backend)
        self.get_device(self.config["device"]["uID"])
        self.has_device = True
        self.ai_is_connected = False
        self.ao_is_connected = False
        self.is_connected = False
        self.pid = None

    def get_device(self, uID=None):
        devices_local = get_daq_device_inventory(InterfaceType.ANY)
        if uID is None:
            uID = self.config["device"]["uID"]
        for i, device in enumerate(devices_local):
            if device.unique_id == uID:
                self.daq_device = DaqDevice(device)
                return None

        logging.info(
            f"given uID not found using device {
                devices_local[0].product_name} with uID {
                devices_local[0].unique_id}"
        )
        self.daq_device = DaqDevice(devices_local[0])
        self.has_device = True
        return None

    def connect_ai(self):
        if self.ai_is_connected:
            return None
        if not self.has_device:
            self.get_device()

        self.ai_device = self.daq_device.get_ai_device()
        self.ai_info = self.ai_device.get_info()
        print("got ai")
        self.ai_is_connected = True
        return None

    def connect_ao(self):

        if self.ao_is_connected:
            return None
        if not self.has_device:
            self.get_device()

        self.ao_device = self.daq_device.get_ao_device()
        print("got ao")
        self.ao_info = self.ao_device.get_info()
        self.ao_is_connected = True
        return None

    def create_output_data(self, amplitude, offset):
        """Populate the buffer with sine wave data for the specified number of
        channels."""

        def sine_sweep_exponential(
            t,
            amplitude=1,
            offset=0,
            f0=1,
            f1=20,
            T=300,
        ):
            return (
                amplitude * sin(2 * pi * f0 * T * ((f1 / f0) ** (t / T) - 1) / log(f1 / f0))
                + offset
            )

        def sine_sweep_linear(
            t,
            amplitude=1,
            offset=0,
            f0=1,
            f1=20,
            T=300,
        ):
            return amplitude * sin(2 * pi * (f0 * t + ((f1 - f0) * t**2) / (2 * T))) + offset

        data_buffer = self.out_buffer
        sample_rate = 10000
        form = self.config["output_form"]
        samples_per_cycle = self.samples_per_cycle
        number_of_channels = self.num_channel_out
        T = self.config["output_sweep_T"]
        f0 = self.config["output_sweep_f0"]
        f1 = self.config["output_sweep_f1"]
        if form == "white_noise":
            for _chan in range(number_of_channels):
                mean = offset
                std = amplitude
                samples = np.random.normal(mean, std, size=samples_per_cycle)
                data_buffer[_chan::number_of_channels] = samples

        elif form == "sine":
            for _chan in range(number_of_channels):
                data_buffer[_chan::number_of_channels] = [
                    amplitude * sin(2 * pi * sample / samples_per_cycle) + offset
                    for sample in range(samples_per_cycle)
                ]
        elif form == "rect":
            for _chan in range(number_of_channels):
                data_buffer[_chan::number_of_channels] = [
                    (
                        amplitude + offset
                        if sample <= samples_per_cycle // 2
                        else -amplitude + offset
                    )
                    for sample in range(samples_per_cycle)
                ]
        elif form == "sine_sweep_exponential":
            for _chan in range(number_of_channels):
                data_buffer[_chan::number_of_channels] = [
                    sine_sweep_exponential(t, amplitude=amplitude, offset=offset, f0=f0, f1=f1, T=T)
                    for t in linspace(0, T, int(sample_rate * T))
                ]
        elif form == "sine_sweep_linear":
            for _chan in range(number_of_channels):
                data_buffer[_chan::number_of_channels] = [
                    sine_sweep_linear(t, amplitude=amplitude, offset=offset, f0=f0, f1=f1, T=T)
                    for t in linspace(0, T, int(sample_rate * T))
                ]
        else:
            logging.warning("Output Form {form} nicht bekannt")

    def start_output_scan(self, voltage_range_index=0):
        """under construction : currently starts a sinoidial output with an amplitude of 1 and a"""

        self.config = read_config_device(self.type, self.number)

        if not self.ao_is_connected:
            self.connect_ao()
        if not self.is_connected:
            self.daq_device.connect(connection_code=0)
            self.is_connected = True
        low_channel = self.config["low_channel_out"]
        high_channel = self.config["high_channel_out"]
        self.num_channel_out = high_channel - low_channel + 1
        voltage_range = self.ao_info.get_ranges()[voltage_range_index]
        sample_rate = 10000  # self.config['output_sample_rate']
        if self.config["output_form"] in ["white_noise", "sine", "rect"]:
            self.samples_per_cycle = int(sample_rate / self.config["output_freq"])
        elif self.config["output_form"] in [
            "sine_sweep_exponential",
            "sine_sweep_linear",
        ]:
            self.samples_per_cycle = int(sample_rate * self.config["output_sweep_T"])
        self.out_buffer = create_float_buffer(self.num_channel_out, self.samples_per_cycle)
        amplitude = self.config["output_amp"]
        offset = self.config["output_offset"]  # 10 Hz sine wave
        scan_options = ScanOption.CONTINUOUS
        scan_flags = AOutScanFlag.DEFAULT

        self.create_output_data(amplitude, offset)
        # print(low_channel, high_channel,
        #       voltage_range, self.samples_per_cycle,
        #       sample_rate, scan_options,
        #       scan_flags, self.out_buffer)

        sample_rate = self.ao_device.a_out_scan(
            low_channel,
            high_channel,
            voltage_range,
            self.samples_per_cycle,
            sample_rate,
            scan_options,
            scan_flags,
            self.out_buffer,
        )

    def start_output_const(self, volt_out=0, channel=0, voltage_range_index=0):
        if not (self.ao_is_connected):
            self.connect_ao()
        if not (self.is_connected):
            self.daq_device.connect(connection_code=0)
            self.is_connected = True
        voltage_range = self.ao_info.get_ranges()[voltage_range_index]
        scan_flags = AOutScanFlag.DEFAULT
        self.ao_device.a_out(channel, voltage_range, scan_flags, float(volt_out))
        # print(channel, voltage_range, scan_flags, float(volt_out), sample_rate)

    def get_ranges(self, input_mode=AiInputMode.SINGLE_ENDED):
        if not self.has_device:
            self.get_device()
        if not self.ai_is_connected:
            self.connect_ai()
        return self.ai_info.get_ranges(input_mode)

    def start_scan_sub(self):

        self.config = read_config_device(self.type, self.number)
        """IEPE Analog input scan example."""
        if not self.has_device:
            self.get_device()
        if not self.ai_is_connected:
            self.connect_ai()
        self.status = ScanStatus.IDLE
        scan_options = ScanOption.CONTINUOUS
        flags = AInScanFlag.DEFAULT
        range_index = 0
        coupling = CouplingMode.AC
        self.sensor_sensitivity = 1.0  # volts per unit
        low_channel = self.config["low_channel"]
        high_channel = self.config["high_channel"]
        self.num_channel = high_channel - low_channel + 1
        self.CHANNEL_COUNT = self.num_channel
        samples_per_channel = self.config["samples_per_channel"]
        rate = self.config["sample_rate"]
        # scan_options = ScanOption.CONTINUOUS
        # flags = AInScanFlag.DEFAULT
        self.ai_config = self.ai_device.get_config()
        input_mode = self.config["inputmode"]
        ranges = self.ai_info.get_ranges(input_mode)
        # print(ranges)
        ##

        self.measuredchannels = []
        self.num_chunks = 0
        if range_index >= len(ranges):
            range_index = len(ranges) - 1
        for chan in range(low_channel, high_channel + 1):
            self.measuredchannels.append(chan)  # a sorted list of channels that are measured

            if chan in self.config["iepe_config"]:  # settings for iepe
                self.ai_config.set_chan_iepe_mode(chan, IepeMode.ENABLED)
                self.ai_config.set_chan_coupling_mode(chan, coupling)
                self.ai_config.set_chan_sensor_sensitivity(chan, self.sensor_sensitivity)
            else:
                pass
                # self.ai_config.set_chan_iepe_mode(chan, IepeMode.DISABLED)
                # self.ai_config.set_chan_sensor_sensitivity(chan, self.sensor_sensitivity)

        self.config["channels_on"] = self.measuredchannels
        if not (self.is_connected):
            self.daq_device.connect(connection_code=0)
            self.is_connected = True
        self.data = create_float_buffer(self.num_channel, samples_per_channel)
        self.index_last = 0
        if self.config["sensor_sensitivity"] in ranges:
            volt_range = self.config["sensor_sensitivity"]
        else:
            # print('couldnt find given voltrange using range[0]')
            volt_range = ranges[0]
        # print(f'''a_in_scan:{low_channel, high_channel, input_mode,
        # volt_range, samples_per_channel,
        # rate, scan_options, flags, self.data}''')
        sample_rate = self.ai_device.a_in_scan(
            low_channel,
            high_channel,
            input_mode,
            volt_range,
            samples_per_channel,
            rate,
            scan_options,
            flags,
            self.data,
        )
        self.config["sample_rate"] = sample_rate
        print(f"started scan rate {sample_rate}")
        return self.config, self.measuredchannels

    def read_buffer(self):
        self.status, self.transfer_status = self.ai_device.get_scan_status()
        # print(self.status, self.transfer_status)
        # print(self.CHANNEL_COUNT)
        index = self.transfer_status.current_index - (
            self.transfer_status.current_index % self.CHANNEL_COUNT
        )
        if index > self.index_last:
            data_out = self.data[self.index_last : index + self.num_channel]
        else:
            data_out = self.data[self.index_last :]
            data_out.extend(self.data[: index + self.num_channel])
        # print(data_out)
        self.index_last = index + self.num_channel
        # print(self.index_last,index+self.num_channel)
        self.add_numpy_data_to_buffer(self.put_raw_data_into_numpy_data(data_out))

    def stop_output(self):
        try:
            self.ao_device.scan_stop()
            print("stopped output")
        except BaseException:
            pass

    def stop_clean_up(self):
        try:
            self.ai_device.scan_stop()
            print("stopped scan")
        except BaseException:
            pass
        try:
            self.daq_device.disconnect()
            print("disconnected device")
        except BaseException:
            pass
        try:
            self.daq_device.release()
            print("device released")
        except BaseException:
            pass
        self.has_device = False
        self.is_connected = False
        self.ai_is_connected = False
        self.ao_is_connected = False


if __name__ == "__main__":
    from time import sleep

    devices = find_uldaq_devices()
    print(devices)
    uldevice = Uldevice(0)
    uldevice.start_scan()
    sleep(1)
    print(uldevice.read_buffer())
    sleep(10)
