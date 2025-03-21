from utility_funs import find_nearest
from inspect import currentframe, getframeinfo
from device_management.general_device import Measurement_device
from config.config_dat import read_config_device
import platform
from ctypes import c_int, c_ulong, c_int32, c_double, c_char_p, create_string_buffer, byref
import sys
import logging
from ctypes import cdll
import os
import inspect
from pathlib import Path

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

if platform.system() == "Windows":
    mqlib = cdll.LoadLibrary(
        str(Path.home()) + "\\MEDAQLib-4.12.0.31896\\Release-x64\\MEDAQLib.dll"
    )
elif platform.system() == "Linux":
    mqlib = cdll.LoadLibrary("/usr/lib/libMEDAQLib.so")


# **********************  SENSOR IDs  **********************
with open(parentdir + "/device_management/micro_eps/Sensor_ids.txt", "r") as f:
    lines = f.readlines()
sensors = dict()
for line in lines:
    key, rest = line.split("=")
    rest = rest.split("#")
    sensors[key] = int(rest[0])

# **********************************************************


# find all eps sensors/devices in the system
def find_eps_devices():
    return 0


# *********************  ERROR VALUES  *********************
with open(parentdir + "/device_management/micro_eps/errors.txt", "r") as f:
    lines = f.readlines()
errors = []
for line in lines:
    errors.append(line.split("=")[0])


def Error(sensor):
    """Read errors from sensor"""
    buf = create_string_buffer(1024)
    mqlib.GetError(c_ulong(sensor), buf, len(buf))
    out = buf.value
    logging.error(out)
    return -1


def return_errors(err, frameinfo):
    if err != 0:
        logging.error(
            f"{err} " + errors[-err] + f" in {frameinfo.filename} line {frameinfo.lineno}"
        )


def str2cstr(srti):
    return c_char_p(srti.encode("utf-8"))


# Choose function for a subclass
def EpsDevice_chooser(number, backend=None):
    config = read_config_device("eps", number)
    if config["device"]["product_name"] == "ILD1900":
        return ILD1900(number, backend)
    elif config["device"]["product_name"] == "ILD1420":
        return ILD1420(number, backend)


class EpsDevice(Measurement_device):

    def __init__(self, number, backend=None):
        self.type = "eps"
        super().__init__(self.type, number, backend)

    def set_laser_power(self, level):
        # ILD1900 level: 0 Full, 1 Off, 2 Reduced, 3 Medium
        # self.set_laser_power_sub()
        return_errors(
            mqlib.SetIntExecSCmd(
                self.sensor,
                str2cstr("Set_LaserPower"),
                str2cstr("SP_LaserPower"),
                c_int32(level),
            ),
            getframeinfo(currentframe()),
        )

    def poll(self, n=1):
        """Retrieves last n values from sensor
        ERR_CODE Poll (uint32_t instanceHandle, int32_t *rawData, double *scaledData,
        int32_t maxValues);"""

        data = c_double(n)
        # dbl_array = c_double * (n)#?
        return_errors(
            mqlib.Poll(c_ulong(self.sensor), None, byref(data), c_int(n)),
            getframeinfo(currentframe()),
        )  #

        return data.value

    def start_scan_sub(self):
        self.config = read_config_device(self.type, self.number)
        print(self.sensor_model)
        self.sensor = mqlib.CreateSensorInstance(self.sensor_model)
        # print(self.sensor)
        if self.sensor == 0:
            logging.error("Cannot create driver instance!")
            exit()
        # Setzen der Interfaceparameter und Öffnen der Schnittstelle
        # return_errors(mqlib.SetParameterString(self.sensor,
        # "IP_Interface".encode('utf-8'),
        # "RS232".encode('utf-8')),getframeinfo(currentframe()))#422#"RS232"
        return_errors(
            mqlib.SetParameterString(
                self.sensor,
                "IP_Interface".encode("utf-8"),
                self.config["device"]["interface"].encode("utf-8"),
            ),
            getframeinfo(currentframe()),
        )
        return_errors(
            mqlib.SetParameterString(
                self.sensor,
                str2cstr("IP_Port"),
                str2cstr(self.config["device"]["com_port"]),
            ),
            getframeinfo(currentframe()),
        )  #
        return_errors(
            mqlib.SetParameterInt(self.sensor, "IP_DeviceInstance".encode("utf-8"), c_int32(0)),
            getframeinfo(currentframe()),
        )
        return_errors(
            mqlib.SetParameterInt(self.sensor, "IP_ChannelNumber".encode("utf-8"), c_int32(0)),
            getframeinfo(currentframe()),
        )

        print(f"sensor {self.sensor}")
        return_errors(mqlib.OpenSensor(self.sensor), getframeinfo(currentframe()))
        # return_errors(mqlib.OpenSensorIF2004_USB( self.sensor, c_int32(1), str2cstr('22060121'), str2cstr(COM_Port),c_int32(0)),getframeinfo(currentframe()))
        self.init_transfer = False
        self.set_interface()
        n = self.config["samples_per_channel"]
        self.set_measurement_rate(self.config["sample_rate"] / 1000)
        self.set_laser_power(0)
        dbl_array = c_double * (n)
        self.dbl_array = dbl_array()
        expectedBlockSize = c_int * (1)
        self.expectedBlockSize = expectedBlockSize()
        self.expectedBlockSize = n
        gotBlocksize = c_int * (1)
        self.gotBlocksize = gotBlocksize()
        self.init_transfer = True
        return_errors(
            mqlib.TransferData(
                self.sensor,
                None,
                self.dbl_array,
                self.expectedBlockSize,
                self.gotBlocksize,
            ),
            getframeinfo(currentframe()),
        )
        return self.config, [0]

    def read_buffer(self):
        return_errors(
            mqlib.TransferData(
                self.sensor,
                None,
                self.dbl_array,
                self.expectedBlockSize,
                self.gotBlocksize,
            ),
            getframeinfo(currentframe()),
        )
        # print(self.dbl_array[:self.gotBlocksize[0]][::250])

        self.add_numpy_data_to_buffer(
            self.put_raw_data_into_numpy_data(self.dbl_array[: self.gotBlocksize[0]])
        )

    def stop_clean_up(self):
        try:
            self.set_laser_power(1)
            if self.sensor != 0:
                if mqlib.CloseSensor(c_ulong(self.sensor)) != errors[0]:
                    logging.error("Cannot close sensor!")
                if mqlib.ReleaseSensorInstance(c_ulong(self.sensor)) != errors[0]:
                    logging.error("Cannot release driver instance!")
        except BaseException:
            pass


class ILD1900(EpsDevice):

    def __init__(self, number, backend):
        super().__init__(number, backend)
        self.sensor_model = sensors["SENSOR_ILD1900"]

    def set_interface(self):
        return_errors(
            mqlib.SetParameterString(
                self.sensor, "IP_Interface".encode("utf-8"), "RS232".encode("utf-8")
            ),
            getframeinfo(currentframe()),
        )

    def set_measurement_rate(self, measurement_rate):
        """Minimum: 0.3 at ILD1750, 0.25 at ILD1900
            Maximum: 7.5 at ILD1750, 10.0 at ILD1900
            Unit: kHz
        Valid for sensor:
            ILD1750
            ILD1900"""
        if measurement_rate > 10.0:
            measurement_rate = 10.0
        if measurement_rate < 0.25:
            measurement_rate = 0.25
        return_errors(
            mqlib.SetDoubleExecSCmd(
                self.sensor,
                str2cstr("Set_Samplerate"),
                str2cstr("SP_Measrate"),
                c_double(measurement_rate),
            ),
            getframeinfo(currentframe()),
        )
        return_errors(
            mqlib.SetDoubleExecSCmd(
                self.sensor,
                str2cstr("Get_Samplerate"),
                str2cstr("SP_Measrate"),
                c_double(measurement_rate),
            ),
            getframeinfo(currentframe()),
        )
        print(measurement_rate)


class ILD1420(EpsDevice):

    def __init__(self, number, backend):
        super().__init__(number, backend)
        self.sensor_model = sensors["SENSOR_ILD1420"]

    def set_measurement_rate(self, measurement_rate):
        """Valid values:
            0.25, 0.5, 1.0, 2.0 (only at ILD1320 and ILD1420) 4.0 (only at ILD1420)
        Unit: kHz
        """
        valid_values = [0.25, 0.5, 1.0, 2.0, 4.0]

        _, output = find_nearest(valid_values, measurement_rate)
        # output=c_double(output)
        # print(output)
        return_errors(
            mqlib.SetDoubleExecSCmd(
                self.sensor,
                str2cstr("Set_Samplerate"),
                str2cstr("SP_Measrate"),
                c_double(output),
            ),
            getframeinfo(currentframe()),
        )
        # return_errors(mqlib.SetDoubleExecSCmd(self.sensor,str2cstr('Get_Samplerate'), str2cstr('SP_Measrate'), output,getframeinfo(currentframe())))
        return output

    def set_interface(self, val=1):
        mqlib.SetIntExecSCmd(
            self.sensor,
            str2cstr("Set_DataOutInterface"),
            str2cstr("SP_DataOutInterface"),
            c_int(val),
        )  # 1 = RS422


if __name__ == "__main__":
    sensor = EpsDevice_chooser(1)
    print(type(sensor))
