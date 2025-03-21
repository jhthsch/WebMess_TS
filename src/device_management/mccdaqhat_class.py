# third party
from time import sleep
import logging

# self developed scripts


# from utility_funs import *
from device_management.general_device import Measurement_device
import platform
from config.config_dat import read_config_device

if platform.system() == "Linux":
    from daqhats import (
        hat_list,
        mcc128,
        mcc118,
        mcc134,
        mcc152,
        mcc172,
        OptionFlags,
        AnalogInputMode,
        SourceType,
    )


def find_mccdaqhat_devices():
    hats = hat_list()
    return hats  # filter_by_id=HatIDs.MCC_128


class mccdaqhat(Measurement_device):
    def __init__(self, number, backend):
        self.type = "mcc"
        super().__init__(self.type, number, backend)
        self.ALL_AVAILABLE = -1
        self.RETURN_IMMEDIATELY = 0
        self.error = dict()
        self.hat = None

    def start_scan_sub(
        self, actually_start=True
    ):  # if actually start is False it only reads the config, which is needed for the layout
        self.config = read_config_device(self.type, self.number)
        """
        self.IIR_delay=self.config_dat['IIR_delay_sec']
        self.filter_l=self.config_dat['filter_l']
        self.threshold_list=self.config_dat['threshold_list']
        self.activeTriggers=self.config_dat['activeTriggers']
        self.scalingFactor = self.config_dat['scalingFactor']
        self.quantity=self.config_dat['quantity']
        self.units=self.config_dat['units']
        """
        # self.sample_rate=self.config_dat['sample_rate']# in Hz
        # self.dT=1/float(self.sample_rate)# in s
        # self.samples_to_display=self.config_dat['samples_to_display']
        # self.hat_descriptor = hat_list(filter_by_id=HatIDs.MCC_128)[self.config_dat['hat_descriptor_adress']]
        self.channels_on = self.config["channels_on"]  # 0 for off 1 for on
        # self.email_list=self.config_dat['email_list']
        # self.downsampling=self.config_dat['downsampling']
        channel_mask = 0
        self.CHANNEL_COUNT = 0
        # initialiing lists that are dynamicly created in a loop descriptions
        # can be found in loop
        if self.config["inputmode"] == AnalogInputMode.DIFF:
            num_mes_opts = 4
        else:
            num_mes_opts = 8
        if "MCC 172" in self.config["device"]["product_name"]:
            num_mes_opts = 2
        self.measuredchannels = []
        for i in range(num_mes_opts):  # enumerate(self.channels_on):
            if i in self.channels_on:
                # channel mask that describes which channel is measured (in
                # binary if 2^channel = 1 the channel is measured)
                channel_mask += 2**i
                self.CHANNEL_COUNT += (
                    1  # a value that stores how many channels are measued in total
                )
                self.measuredchannels.append(i)  # a sorted list of channels that are measured

        self.config["channels_on"] = self.measuredchannels

        self.channel_mask = channel_mask

        range_set = [
            "± 10V",
            "± 5V",
            "± 2V",
            "± 1V",
        ]  # used to convert the read range into a human readable string
        self.range_val = range_set[self.config["inputrange"]]  #
        mode_set = ["Single Ended", "Diffential"]
        self.mode = mode_set[self.config["inputmode"]]
        self.stop_clean_up()
        # print(self.channel_mask, self.samples_to_buffer, self.sample_rate, OptionFlags.CONTINUOUS)
        # print(type(self.channel_mask),type( self.samples_to_buffer),type( self.sample_rate), type(OptionFlags.CONTINUOUS))
        if actually_start:
            if "MCC 128" in self.config["device"]["product_name"]:
                self.hattype = 128
                self.hat = mcc128(self.config["device"]["address"])
                self.hat.a_in_mode_write(int(self.config["inputmode"]))
                self.hat.a_in_range_write(int(self.config["inputrange"]))
                self.hat.a_in_scan_start(
                    self.channel_mask,
                    self.config["sample_rate"] * 10,
                    self.config["sample_rate"],
                    OptionFlags.CONTINUOUS,
                )
            elif "MCC 118" in self.config["device"]["product_name"]:
                self.hattype = 118
                self.hat = mcc118(self.config["device"]["address"])
                self.hat.a_in_mode_write(int(self.config["inputmode"]))
                self.hat.a_in_range_write(int(self.config["inputrange"]))
                self.hat.a_in_scan_start(
                    self.channel_mask,
                    self.config["sample_rate"] * 10,
                    self.config["sample_rate"],
                    OptionFlags.CONTINUOUS,
                )
            elif "MCC 134" in self.config["device"]["product_name"]:
                self.hattype = 138
                self.hat = mcc134(self.config["device"]["address"])
            elif "MCC 152" in self.config["device"]["product_name"]:
                self.hattype = 158
                self.hat = mcc152(self.config["device"]["address"])
            elif "MCC 172" in self.config["device"]["product_name"]:
                self.hattype = 172
                self.hat = mcc172(self.config["device"]["address"])
                self.hat.a_in_clock_config_write(SourceType.LOCAL, self.config["sample_rate"])
                # for channel,IEPE_setting in enumerate(self.config['IEPE_config']):
                #    self.hat.iepe_config_write(channel, IEPE_setting)
                for channel in range(2):
                    if channel in self.config["iepe_config"]:
                        self.hat.iepe_config_write(channel, 1)  # on
                        print("a")
                    else:
                        self.hat.iepe_config_write(channel, 0)  # off
                    # print(f'channel {channel} mode {self.hat.iepe_config_read(channel)}')

                synced = False
                while not synced:
                    (_source_type, actual_scan_rate, synced) = self.hat.a_in_clock_config_read()
                    if not synced:
                        sleep(0.005)
                print(
                    self.channel_mask,
                    self.config["sample_rate"] * 2,
                    OptionFlags.CONTINUOUS,
                )
                self.hat.a_in_scan_start(
                    self.channel_mask,
                    self.config["sample_rate"] * 20,
                    OptionFlags.CONTINUOUS,
                )

                self.config["sample_rate"] = actual_scan_rate
            else:
                logging.warning("not supported daqhat selected")
                return None
        return self.config, self.measuredchannels

    def read_buffer(self):  # ,activeTriggers,threshold_list,filter_l
        """To_list
        function that needs to be called in regular intervals empties the bufffer of the daq head and adds it to the own buffer, where it can be used for storage, display and to trigger alarms
        has the option to activate the IIR filter which is set as class attribute
        Inputs:
            self
            activeTriggers: a list representing all measured channels containing if they can trigger or not (bool)
            threshold_list: a list representing all measured channels containing the thresholdvalue for the trigger
        Outputs:
            if an alarm was triggered a human readable string containig time and channel otherwise None
        """
        read_result = self.hat.a_in_scan_read(self.ALL_AVAILABLE, self.RETURN_IMMEDIATELY)  #
        if read_result.hardware_overrun:
            print("\n\nHardware overrun\n")
            mccdaqhat.backend.restart_after_error()
            # send_email(self.config['email_list'].split(','),
            #            t=datetime.now().isoformat(' ', 'seconds'),
            # filename=None, channel=0,report_str='hardware_overrun')

        elif read_result.buffer_overrun:
            print("\n\nBuffer overrun\n")
            mccdaqhat.backend.restart_after_error()
            # send_email(self.config['email_list'].split(','),
            #            t=datetime.now().isoformat(' ', 'seconds'),
            #            filename=None, channel=0,report_str='buffer_overrun')

        """
        if ('hardware_overrun' not in self.error.keys()
                or not self.error['hardware_overrun']):
            logging.error('hardware_overrun')
            self.error['hardware_overrun'] = read_result.hardware_overrun
            #
        if ('buffer_overrun' not in self.error.keys()
                or not self.error['buffer_overrun']):
            logging.error('hardware_overrun')
            self.error['buffer_overrun'] = read_result.buffer_overrun
            #logging.error('buffer_overrun')
        """
        self.add_numpy_data_to_buffer(self.put_raw_data_into_numpy_data(read_result.data))

    def stop_clean_up(self):
        if self.hat is not None:
            self.hat.a_in_scan_stop()
            self.hat.a_in_scan_cleanup()
        return None
