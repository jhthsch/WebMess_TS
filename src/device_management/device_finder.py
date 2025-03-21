import platform
import configparser
import os
from config.config_dat import (
    read_config,
    replace_entries,
    read_config_main,
    write_config,
    get_vals,
    MAIN_CONFIG_PATH,
    config_dict_main,
)

current_platform = platform.system()


def find_available_devices():
    config = configparser.ConfigParser()
    if not os.path.exists(MAIN_CONFIG_PATH):
        os.makedirs(os.path.dirname(MAIN_CONFIG_PATH), exist_ok=True)
        config["config"] = {key: val["default_val"] for key, val in config_dict_main.items()}
        with open(MAIN_CONFIG_PATH, "w") as configfile:
            config.write(configfile)

    config.read(MAIN_CONFIG_PATH)
    if not config.has_section("config"):
        config["config"] = {key: val["default_val"] for key, val in config_dict_main.items()}
        with open(MAIN_CONFIG_PATH, "w") as configfile:
            config.write(configfile)

    try:
        config.get("config", "type")
    except configparser.NoSectionError:
        configOptions = {"config": {"type": "default"}}
        write_config(MAIN_CONFIG_PATH, **configOptions)

    try:
        config = read_config(MAIN_CONFIG_PATH)
        config_path = MAIN_CONFIG_PATH
        config.read(config_path)
        config.get("config", "type")
    except Exception:
        configOptions = get_vals(config, config_dict_main)
        write_config(MAIN_CONFIG_PATH, **configOptions)

    try:
        from device_management import audio_class

        audio_devices = audio_class.find_audio_devices()
    except Exception as e:
        print(e)
        audio_devices = False
    if audio_devices:
        replace_entries(["audio_devices_enabled"], [True], MAIN_CONFIG_PATH)
    try:
        from device_management import eps_class

        eps_devices = eps_class.find_eps_devices()  # sigma-epsilon-Laser
    except Exception as e:
        print(e)
        eps_devices = False
    if eps_devices:
        replace_entries(["eps_devices_enabled"], [True], MAIN_CONFIG_PATH)

    if current_platform == "Linux":
        try:
            from device_management import mccdaqhat_class
            mccdaqhats_devices = mccdaqhat_class.find_mccdaqhat_devices()  # daqhats for pi
        except Exception as e:
            print(e)
            mccdaqhats_devices = False
        if mccdaqhats_devices:
            replace_entries(["mccdaqhat_devices_enabled"], [True], MAIN_CONFIG_PATH)
        try:
            from device_management import uldaq_class
            uldaq_devices = uldaq_class.find_uldaq_devices()  # measurement computing devices
        except Exception as e:
            print(e)
            uldaq_devices = False
        if uldaq_devices:
            replace_entries(["uldaq_devices_enabled"], [True], MAIN_CONFIG_PATH)
        try:
            from device_management import usbdux_class
            usbdux_devices = usbdux_class.find_usbdux_devices()  # measurement computing devices
            print(usbdux_devices)
        except Exception as e:
            print(e)
            usbdux_devices = False
        if usbdux_devices:
            replace_entries(["usbdux_devices_enabled"], [True], MAIN_CONFIG_PATH)
    elif current_platform == "Windows":
        try:
            from device_management import mcculw_class
            mcculw_devices = mcculw_class.find_mcculw_devices()
        except Exception:
            mcculw_devices = False
        if mcculw_devices:
            replace_entries(["mcculw_devices_enabled"], [True], MAIN_CONFIG_PATH)
            print("mcculw", config_dict_main["mcculw_devices_enabled"])
        try:
            from device_management import nidaqmx_class
            nidaqmx_devices = nidaqmx_class.find_nidaqmx_devices()
        except Exception as e:
            print(e)
            nidaqmx_devices = False
        if nidaqmx_devices:
            replace_entries(["nidaqmx_devices_enabled"], [True], MAIN_CONFIG_PATH)

    return None


if __name__ == "__main__":
    configs = read_config_main()
    configOptions = get_vals(configs, config_dict_main)
    find_available_devices()
