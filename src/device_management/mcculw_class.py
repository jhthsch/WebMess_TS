import platform
import sys
import os
import inspect
import logging
from time import sleep
from ctypes import c_double, cast, POINTER
from config.config_dat import read_config_device

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
# from config_dat import read_config_mcculw
# print('imported')
if platform.system() == "Windows":

    from mcculw import ul

    ul.ignore_instacal()
    from mcculw.enums import (
        InterfaceType,
        AnalogInputMode,
        ULRange,
        FunctionType,
        ScanOptions,
        Status,
    )
    from mcculw.ul import ULError
    from mcculw.device_info import DaqDeviceInfo

    # from mcculw.ul import (get_daq_device_inventory, create_daq_device)
    from device_management.general_device import Measurement_device

#    from measurement_classes.uldaq_helper.daq_device import DaqDevice


def find_mcculw_devices():
    print("called daq_dev inventory")
    devices_local = ul.get_daq_device_inventory(InterfaceType.ANY)
    mcculw_daq_list = []
    for i, device in enumerate(devices_local):
        mcculw_daq_list.append(str(device.product_name))
        # print('mcculwdev', device, device.unique_id)
    return mcculw_daq_list


def show_ul_error(ul_error):
    message = "A UL Error occurred.\n\n" + str(ul_error)
    print("Error", message)


class McculwDevice(Measurement_device):

    def __init__(self, number, backend) -> None:
        self.type = "mcculw"
        super().__init__(self.type, number, backend)
        self.board_number = number
        self.device = self.get_device(self.config["device"]["uID"])
        self.daq_dev_info = DaqDeviceInfo(number)
        print(
            "\nActive DAQ device: ",
            self.daq_dev_info.product_name,
            " (",
            self.daq_dev_info.unique_id,
            ")\n",
            sep="",
        )
        self.ai_info = self.daq_dev_info.get_ai_info()
        self.has_device = True
        self.ai_is_connected = False
        self.ao_is_connected = False
        self.is_connected = False
        self.pid = None
        self.device_info = None
        self.ai_info = None
        self.ranges = []

    """Find all mcculw devices and there board numbers,
       names are adopted from the examples of the mcculw github
    """

    def get_device(self, uID=None):
        # print("get deivce funciton")

        devices_local = ul.get_daq_device_inventory(InterfaceType.ANY)
        # print(devices_local[0].product_name,
        #      devices_local[0].product_id, devices_local[0].unique_id)
        if uID == "":
            uID = self.config["device"]["uID"]
        for i, device in enumerate(devices_local):
            if device.unique_id == uID:
                print("get_device", uID)
                ul.release_daq_device(self.number)
                self.daq_device = ul.create_daq_device(self.number, device)
                return None

        logging.info(
            f"given uID not found using device {
                devices_local[0].product_name} with uID {
                devices_local[0].unique_id}"
        )
        ul.release_daq_device(self.board_number)
        uID = self.config["device"]["uID"] = devices_local[0].unique_id
        self.daq_device = ul.create_daq_device(self.board_number, devices_local[0])
        self.has_device = True
        return None

    def flash_led(
        self,
    ):
        # print("led")
        try:
            # Flash the device LED
            ul.flash_led(self.board_number)
        except ULError as e:
            show_ul_error(e)

    def get_ranges(self, input_mode=AnalogInputMode.SINGLE_ENDED):
        # print("get_ramges")
        if not self.has_device:
            self.ranges.append(ULRange.BIP10VOLTS)
        if input_mode == AnalogInputMode.SINGLE_ENDED:
            self.ranges.append(ULRange.BIP10VOLTS)
        elif input_mode == AnalogInputMode.DIFFERENTIAL:
            self.ranges.append(ULRange.BIP20VOLTS)
            self.ranges.append(ULRange.BIP10VOLTS)
            self.ranges.append(ULRange.BIP5VOLTS)
            self.ranges.append(ULRange.BIP4VOLTS)
            self.ranges.append(ULRange.BIP2PT5VOLTS)
            self.ranges.append(ULRange.BIP2VOLTS)
            self.ranges.append(ULRange.BIP1PT25VOLTS)
            self.ranges.append(ULRange.BIP1VOLTS)
            print("get_ranges", self.ranges)
        return self.ranges

    def start_scan_sub(self):
        # print("start_sub")
        self.config = read_config_device(self.type, self.number)
        if not self.has_device:
            self.get_device()
        Status.IDLE
        scan_options = ScanOptions.CONTINUOUS
        low_channel = self.config["low_channel"]
        high_channel = self.config["high_channel"]
        range_index = 0
        self.num_channel = high_channel - low_channel + 1
        samples_per_channel = self.config["samples_per_channel"]
        rate = self.config["sample_rate"]
        input_mode = self.config["inputmode"]
        ranges = self.get_ranges(input_mode)
        print("ranges", ranges)

        self.measuredchannels = []
        self.num_chunks = 0
        if range_index >= len(ranges):
            range_index = len(ranges) - 1
        for chan in range(low_channel, high_channel + 1):
            self.measuredchannels.append(chan)  # a sorted list of channels that are measured
        try:
            ul.a_input_mode(self.board_number, input_mode)
        except Exception:
            print("change in input mode: ")
        self.config["channels_on"] = self.measuredchannels

        self.ul_buffer_count = samples_per_channel * self.num_channel

        ai_range = 1  # self.config['inputrange']

        scan_options = ScanOptions.BACKGROUND | ScanOptions.CONTINUOUS | ScanOptions.SCALEDATA

        # self.data = create_float_buffer(self.num_channel, samples_per_channel)
        self.data_handle = memhandle = ul.scaled_win_buf_alloc(self.ul_buffer_count)
        if memhandle:
            self.data = cast(memhandle, POINTER(c_double))
        else:
            raise RuntimeError("Failed to allocate memory for the buffer")
        self.data = cast(memhandle, POINTER(c_double))
        self.index_last = 0
        self.cur_count = 0

        # print(f'''a_in_scan:{low_channel, high_channel, input_mode,
        # samples_per_channel,rate, self.data}''')
        # print(f'board_number start: {self.board_number}')
        sample_rate = ul.a_in_scan(
            self.board_number,
            low_channel,
            high_channel,
            self.ul_buffer_count,
            rate,
            ai_range,
            memhandle,
            scan_options,
        )
        self.config["sample_rate"] = sample_rate
        # print(f'started scan rate {sample_rate}')

        return self.config, self.measuredchannels

    def read_buffer(self):
        # print("read_buffer")

        status = ul.get_status(self.board_number, FunctionType.AIFUNCTION)
        # print(status)
        index_new = status.cur_index - (
            status.cur_index % self.CHANNEL_COUNT
        )  # % 1#self.CHANNEL_COUNT
        # this function checks if there has been any new values written since
        # last reading
        if status.cur_count == self.cur_count:
            return None
        else:
            self.cur_count = status.cur_count
        if index_new > self.index_last:
            data_out = self.data[self.index_last: index_new + self.num_channel]
        else:
            data_out = self.data[self.index_last: -1]
            data_out.extend(self.data[: index_new + self.num_channel])

        self.index_last = index_new
        self.add_numpy_data_to_buffer(self.put_raw_data_into_numpy_data(data_out))
        return None


# Start the example if this module is being run
if __name__ == "__main__":
    # Start the example
    dev = McculwDevice(0, backend=None)
    # find_mcculw_devices()
    # dev.select_device(0)
    # dev.flash_led()
    # sleep(10)
    # dev.connect_ai()
    dev.start_scan()
    for i in range(10):
        sleep(0.5)
        dev.read_buffer()
        print(len(dev.channels[0].buffer))
