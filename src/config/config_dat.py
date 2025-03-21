import configparser
import ast
import logging
import os
from pathlib import Path

MAIN_CONFIG_PATH = os.path.join("config", "config.ini")

logging.basicConfig(level=logging.DEBUG)

def device_config_path(device_type, i):
    return os.path.join("config", f"config_{device_type}{i}.ini")


config_dict_main = dict(
    type={"default_val": "main", "type": "string"},
    data_path={
        "default_val": os.path.join(Path.home(), "Measurements_web_app"),
        "type": "string",
    },
    email_list={"default_val": "", "type": "string"},
    auto_restart_after_error={"default_val": True, "type": "bool"},
    samples_to_display={"default_val": 1000, "type": "int"},
    save_opt={"default_val": "auto", "type": "string"},
    job_manager={"default_val": False, "type": "bool"},
    job_list_filename={
        "default_val": str(os.path.join(Path.home()) + "job_list.csv"),
        "type": "string",
    },
    autosave_sec={"default_val": 600, "type": "int"},
    trigger_pre={"default_val": 5, "type": "int"},
    trigger_post={"default_val": 5, "type": "int"},
    downsampling={"default_val": 5, "type": "int"},
    max_val_report_interval_sec={"default_val": 600, "type": "int"},
    iir_delay_sec={"default_val": 20, "type": "int"},
    mccdaqhat_devices_enabled={"default_val": False, "type": "bool"},
    nidaqmx_devices_enabled={"default_val": False, "type": "bool"},
    uldaq_devices_enabled={"default_val": False, "type": "bool"},
    mcculw_devices_enabled={"default_val": False, "type": "bool"},
    audio_devices_enabled={"default_val": False, "type": "bool"},
    eps_devices_enabled={"default_val": False, "type": "bool"},
    usbdux_devices_enabled={"default_val": False, "type": "bool"},
    num_mccdaqhat_devices={"default_val": 0, "type": "int"},
    num_nidaqmx_devices={"default_val": 0, "type": "int"},
    num_uldaq_devices={"default_val": 0, "type": "int"},
    num_mcculw_devices={"default_val": 0, "type": "int"},
    num_audio_devices={"default_val": 0, "type": "int"},
    num_eps_devices={"default_val": 0, "type": "int"},
    num_usbdux_devices={"default_val": 0, "type": "int"},
    ip_address={"default_val": "", "type": "string"},
    web_app_port={"default_val": 8080, "type": "int"},
    fetch_rate={"default_val": 1000, "type": "int"},
    eval_opts={"default_val": ["min_max"], "type": "array"},
    eval_period={"default_val": 2, "type": "float"},
    eval_time={"default_val": 2, "type": "float"},
)

config_dict_mccdaqhats = dict(
    type={"default_val": "mcc", "type": "string"},
    device={
        "default_val": {
            "address": 0,
            "id": 326,
            "version": 1,
            "product_name": "MCC 128 Voltage HAT",
        },
        "type": "dict",
    },
    channels_on={"default_val": [0, 1, 2], "type": "array"},
    sample_rate={"default_val": 1000, "type": "int"},
    quantity={
        "default_val": [
            "velocity",
            "velocity",
            "velocity",
            "velocity",
            "velocity",
            "velocity",
            "velocity",
            "velocity",
            "velocity",
            "velocity",
            "velocity",
            "velocity",
            "velocity",
            "velocity",
            "velocity",
            "velocity",
        ],
        "type": "array",
    },
    units={
        "default_val": [
            "mm/s",
            "mm/s",
            "mm/s",
            "mm/s",
            "mm/s",
            "mm/s",
            "mm/s",
            "mm/s",
            "mm/s",
            "mm/s",
            "mm/s",
            "mm/s",
            "mm/s",
            "mm/s",
            "mm/s",
            "mm/s",
        ],
        "type": "array",
    },
    scalingfactor={
        "default_val": [
            34.72,
            34.72,
            34.72,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
        ],
        "type": "array",
    },
    inputrange={"default_val": 3, "type": "int"},
    inputmode={"default_val": 1, "type": "int"},
    downsampling={"default_val": 1, "type": "int"},
    iir_delay_sec={"default_val": 20, "type": "int"},
    activetriggers={"default_val": [], "type": "array"},
    threshold_list={
        "default_val": [
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ],
        "type": "array",
    },
    filter_l={"default_val": [0, 1, 2], "type": "array"},
    filt50Hz_l={"default_val": [], "type": "array"},
    detrend_l={"default_val": [0, 1, 2], "type": "array"},
    iepe_config={"default_val": [0], "type": "array"},
    natural_frequency={
        "default_val": [
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
        ],
        "type": "array",
    },
    damping={
        "default_val": [
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
        ],
        "type": "array",
    },
    eval_channels={"default_val": [0, 1, 2], "type": "array"},
)
config_dict_nidaqmx = dict(
    type={"default_val": "nidaqmx", "type": "string"},
    device={
        "default_val": {
            "Device Name: ": "Dev1",
            "Product Category: ": "ProductCategory.M_SERIES_DAQ",
            "product_name": "USB-6210",
        },
        "type": "dict",
    },
    channels_on={"default_val": [0, 2], "type": "array"},
    sample_rate={"default_val": 10, "type": "int"},
    quantity={"default_val": "velocity", "type": "array"},
    units={"default_val": "mm/s", "type": "array"},
    scalingfactor={
        "default_val": [
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
        ],
        "type": "array",
    },
    input_range={"default_val": 1, "type": "int"},
    input_mode={"default_val": 0, "type": "int"},
    downsampling={"default_val": 1, "type": "int"},
    iir_delay_sec={"default_val": 20, "type": "int"},
    activetriggers={"default_val": [], "type": "array"},
    threshold_list={
        "default_val": [
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ],
        "type": "array",
    },
    filter_l={"default_val": [], "type": "array"},
    filt50Hz_l={"default_val": [], "type": "array"},
    detrend_l={"default_val": [], "type": "array"},
    natural_frequency={
        "default_val": [
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
        ],
        "type": "array",
    },
    damping={
        "default_val": [
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
        ],
        "type": "array",
    },
    eval_channels={"default_val": [1], "type": "array"},
)
config_dict_usbdux = dict(
    type={"default_val": "usbdux", "type": "string"},
    device={"default_val": {"ID": 0, "product_name": "USBDUX-sigma"}, "type": "dict"},
    input_range={"default_val": 1, "type": "int"},
    input_mode={"default_val": 0, "type": "int"},
    sample_rate={"default_val": 1000, "type": "int"},
    downsampling={"default_val": 1, "type": "int"},
    channels_on={"default_val": [0, 1, 2], "type": "array"},
    eval_channels={"default_val": [0, 1, 2, 3], "type": "array"},
    num_channels={"default_val": 1, "type": "int"},
    channel_name={
        "default_val": [
            "MP01_x",
            "MP01_y",
            "MP01_z",
            "MP02_x",
            "MP02_y",
            "MP02_z",
            "MP03_x",
            "MP03-y",
            "MP03-z",
        ],
        "type": "array",
    },
    channel_postion={
        "default_val": [
            "KG_x",
            "KG_y",
            "KG_z",
            "OG_x",
            "OG_y",
            "OG_z",
            "DG_x",
            "DG-y",
            "DG-z",
        ],
        "type": "array",
    },
    quantity={
        "default_val": [
            "velocity",
            "velocity",
            "velocity",
            "velocity",
            "velocity",
            "velocity",
            "velocity",
            "velocity",
        ],
        "type": "array",
    },
    units={
        "default_val": ["mm/s", "mm/s", "mm/s", "mm/s", "mm/s", "mm/s", "mm/s", "mm/s"],
        "type": "array",
    },
    natural_frequency={
        "default_val": [
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
        ],
        "type": "array",
    },
    damping={
        "default_val": [
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
        ],
        "type": "array",
    },
    scalingfactor={
        "default_val": [
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
        ],
        "type": "array",
    },
    threshold_list={
        "default_val": [
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ],
        "type": "array",
    },
    iir_delay_sec={"default_val": 20, "type": "int"},
    activetriggers={"default_val": [], "type": "array"},
    filter_l={"default_val": [], "type": "array"},
    filt50Hz_l={"default_val": [], "type": "array"},
    detrend_l={"default_val": [], "type": "array"},
)
config_dict_uldaq = dict(
    type={"default_val": "uldaq", "type": "string"},
    device={
        "default_val": {"uID": 326, "interface": "USB", "product_name": "DT whatever"},
        "type": "dict",
    },
    sensor_sensitivity={"default_val": 1, "type": "int"},
    channels_on={"default_val": [0, 1, 2, 3], "type": "array"},
    samples_per_channel={"default_val": 10000, "type": "int"},
    sample_rate={"default_val": 10000, "type": "int"},
    quantity={
        "default_val": [
            "velocity",
            "velocity",
            "velocity",
            "velocity",
            "velocity",
            "velocity",
            "velocity",
            "velocity",
        ],
        "type": "array",
    },
    units={
        "default_val": ["mm/s", "mm/s", "mm/s", "mm/s", "mm/s", "mm/s", "mm/s", "mm/s"],
        "type": "array",
    },
    scalingfactor={
        "default_val": [
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
        ],
        "type": "array",
    },
    inputrange={"default_val": 5, "type": "int"},
    inputmode={"default_val": 2, "type": "int"},
    downsampling={"default_val": 1, "type": "int"},
    low_channel={"default_val": 0, "type": "int"},
    high_channel={"default_val": 0, "type": "int"},
    activetriggers={"default_val": [0], "type": "array"},
    threshold_list={
        "default_val": [
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ],
        "type": "array",
    },
    filter_l={"default_val": [0, 1, 2, 3], "type": "array"},
    filt50Hz_l={"default_val": [], "type": "array"},
    detrend_l={"default_val": [0, 1, 2, 3], "type": "array"},
    iepe_config={"default_val": [], "type": "array"},
    natural_frequency={
        "default_val": [
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
        ],
        "type": "array",
    },
    damping={
        "default_val": [
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
        ],
        "type": "array",
    },
    eval_channels={"default_val": [0, 1, 2, 3], "type": "array"},
    active_measurement={"default_val": True, "type": "bool"},
    active_output={"default_val": False, "type": "bool"},
    output_freq={"default_val": 4, "type": "float"},
    output_amp={"default_val": 1, "type": "float"},
    output_offset={"default_val": 1, "type": "float"},
    output_sample_rate={"default_val": 5000, "type": "int"},
    output_form={"default_val": "sine", "type": "string"},
    output_sweep_f0={"default_val": 1, "type": "float"},
    output_sweep_f1={"default_val": 10, "type": "float"},
    output_sweep_T={"default_val": 60, "type": "float"},
    low_channel_out={"default_val": 0, "type": "int"},
    high_channel_out={"default_val": 0, "type": "int"},
    output_setpoint={"default_val": 1, "type": "float"},
)
config_dict_mcculw = dict(
    type={"default_val": "mcculw ", "type": "string"},
    device={
        "default_val": {
            "uID": "1EE9340",
            "interface": "USB",
            "product_name": "usb-1208-FS/Plus",
        },
        "type": "dict",
    },
    sensor_sensitivity={"default_val": 1, "type": "int"},
    channels_on={"default_val": [0, 1, 2, 3], "type": "array"},
    samples_per_channel={"default_val": 10000, "type": "int"},
    sample_rate={"default_val": 10000, "type": "int"},
    quantity={"default_val": ["velocity"] * 16, "type": "array"},
    units={"default_val": ["mm/s"] * 16, "type": "array"},
    scalingfactor={
        "default_val": [
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
        ],
        "type": "array",
    },
    inputrange={"default_val": 5, "type": "int"},
    inputmode={"default_val": 2, "type": "int"},
    downsampling={"default_val": 1, "type": "int"},
    low_channel={"default_val": 0, "type": "int"},
    high_channel={"default_val": 0, "type": "int"},
    activetriggers={"default_val": [0], "type": "array"},
    threshold_list={
        "default_val": [
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ],
        "type": "array",
    },
    filter_l={"default_val": [0, 1, 2, 3], "type": "array"},
    filt50Hz_l={"default_val": [], "type": "array"},
    detrend_l={"default_val": [0, 1, 2, 3], "type": "array"},
    iepe_config={"default_val": [], "type": "array"},
    natural_frequency={
        "default_val": [
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
        ],
        "type": "array",
    },
    damping={
        "default_val": [
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
        ],
        "type": "array",
    },
    eval_channels={"default_val": [0, 1, 2, 3], "type": "array"},
    active_measurement={"default_val": True, "type": "bool"},
    active_output={"default_val": False, "type": "bool"},
    output_freq={"default_val": 4, "type": "float"},
    output_amp={"default_val": 1, "type": "float"},
    output_offset={"default_val": 1, "type": "float"},
    output_sample_rate={"default_val": 5000, "type": "int"},
    output_form={"default_val": "sine", "type": "string"},
    output_sweep_f0={"default_val": 1, "type": "float"},
    output_sweep_f1={"default_val": 10, "type": "float"},
    output_sweep_T={"default_val": 60, "type": "float"},
    low_channel_out={"default_val": 0, "type": "int"},
    high_channel_out={"default_val": 0, "type": "int"},
    output_setpoint={"default_val": 1, "type": "float"},
)
config_dict_eps = dict(
    type={"default_val": "eps", "type": "string"},
    device={
        "default_val": {
            "Serial number": "00321010155",
            "interface": "RS232",
            "com_port": "/dev/ttyUSB0",
            "product_name": "ILD1900",
        },
        "type": "dict",
    },
    samples_per_channel={"default_val": 50000, "type": "int"},
    sample_rate={"default_val": 4000, "type": "int"},
    quantity={"default_val": ["distance"], "type": "array"},
    units={"default_val": ["mm"], "type": "array"},
    scalingfactor={
        "default_val": [
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
        ],
        "type": "array",
    },
    downsampling={"default_val": 1, "type": "int"},
    activetriggers={"default_val": [0], "type": "array"},
    threshold_list={"default_val": [0.0], "type": "array"},
    filter_l={"default_val": [], "type": "array"},
    filt50Hz_l={"default_val": [], "type": "array"},
    detrend_l={"default_val": [], "type": "array"},
    natural_frequency={
        "default_val": [
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
        ],
        "type": "array",
    },
    damping={
        "default_val": [
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
        ],
        "type": "array",
    },
    eval_channels={"default_val": [0], "type": "array"},
    laser_intensity={"default_val": 0, "type": "int"},
    channels_on={"default_val": [0], "type": "array"},
)
config_dict_audio = dict(
    type={"default_val": "audio", "type": "string"},
    device={
        "default_val": {"product_name": "default", "descriptor": "input"},
        "type": "dict",
    },
    channels_on={"default_val": [1], "type": "array"},
    sample_rate={"default_val": 1000, "type": "int"},
    quantity={"default_val": ["Volt", "Volt"], "type": "array"},
    units={"default_val": ["Volt", "Volt"], "type": "array"},
    scalingfactor={
        "default_val": [
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
        ],
        "type": "array",
    },
    downsampling={"default_val": 1, "type": "int"},
    iir_delay_sec={"default_val": 20, "type": "int"},
    activetriggers={"default_val": [], "type": "array"},
    threshold_list={
        "default_val": [
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ],
        "type": "array",
    },
    filter_l={"default_val": [], "type": "array"},
    filt50Hz_l={"default_val": [], "type": "array"},
    detrend_l={"default_val": [], "type": "array"},
    natural_frequency={
        "default_val": [
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
        ],
        "type": "array",
    },
    damping={
        "default_val": [
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
            0.56,
        ],
        "type": "array",
    },
    eval_channels={"default_val": [1], "type": "array"},
)

# Neues Dictionary für Projekte
config_dict_projects = dict(
    type={"default_val": "project", "type": "string"},
    project_name={"default_val": "Default Project", "type": "string"},
    project_description={"default_val": "", "type": "string"},
    created_at={"default_val": "", "type": "string"},
    updated_at={"default_val": "", "type": "string"},
    active={"default_val": True, "type": "bool"},
    devices={"default_val": [], "type": "array"},
)

# Funktion zum Generieren des Pfads für Projektkonfigurationen
def project_config_path(project_name):
    return os.path.join("config", f"config_project_{project_name}.ini")

def get_dict_from_type(cotype):
    config_dicts = {
        "main": config_dict_main,
        "mcc": config_dict_mccdaqhats,
        "nidaqmx": config_dict_nidaqmx,
        "uldaq": config_dict_uldaq,
        "audio": config_dict_audio,
        "eps": config_dict_eps,
        "mcculw": config_dict_mcculw,
        "usbdux": config_dict_usbdux,
        "project": config_dict_projects,
    }
    return config_dicts.get(cotype, {})


def read_config(path):
    config = configparser.ConfigParser()
    config.read(path)
    return config


def get_vals(config, config_dict):
    config_options = {}
    for key, val in config_dict.items():
        try:
            if (val["type"] == "string"):
                config_options[key] = config.get("config", key)
            elif (val["type"] == "int"):
                config_options[key] = config.getint("config", key)
            elif (val["type"] == "float"):
                config_options[key] = config.getfloat("config", key)
            elif val["type"] in {"array", "bool", "dict"}:
                config_options[key] = ast.literal_eval(config.get("config", key))
            else:
                logging.warning(f"Unsupported datatype: {val['type']}")
        except Exception:
            config_options[key] = val["default_val"]
            logging.warning(f"Replaced {key} with default value: {val['default_val']}")
    return config_options


def write_config(filepath, **kwargs):
    config = configparser.ConfigParser()
    config["config"] = kwargs
    with open(filepath, "w") as configfile:
        config.write(configfile)


def read_config_main():
    logging.debug("Reading main configuration...")
    config = read_config(MAIN_CONFIG_PATH)
    config_options = get_vals(config, config_dict_main)
    write_config(MAIN_CONFIG_PATH, **config_options)
    logging.debug(f"Configuration loaded: {config_options}")
    return config_options


def read_config_device(device_type, i):
    path = device_config_path(device_type, i)
    config_dict = get_dict_from_type(device_type)
    config = read_config(path)
    config_options = get_vals(config, config_dict)
    write_config(path, **config_options)
    return config_options

# Neue Funktion zum Lesen und Schreiben von Projektkonfigurationen
def read_config_project(project_name):
    path = project_config_path(project_name)
    config_dict = config_dict_projects
    config = read_config(path)
    config_options = get_vals(config, config_dict)
    write_config(path, **config_options)
    return config_options

def replace_entries(entries, newvals, path):
    config = read_config(path)
    cotype = config.get("config", "type")
    config_options = get_vals(config, get_dict_from_type(cotype))
    for entry, newval in zip(entries, newvals):
        config_options[entry] = newval
    write_config(path, **config_options)


def replace_val_of_array_entry(entry, newval, index, path):
    config = read_config(path)
    cotype = config.get("config", "type")
    config_options = get_vals(config, get_dict_from_type(cotype))
    config_options[entry][index] = newval
    write_config(path, **config_options)


if __name__ == "__main__":
    print(read_config_main())
    config = read_config(device_config_path("mcculw", 0))
    print(config.options("config"))
    for option in config.options("config"):
        val = config.get("config", option)
        try:
            print(eval(val), type(eval(val)))
        except Exception:
            print(f"Could not handle: {val}")
