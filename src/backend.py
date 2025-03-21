# third party
import queue
from time import sleep
from datetime import datetime, timedelta
import plotly.io as pio
from plotly.subplots import make_subplots
import plotly.graph_objs as go
import os
import platform  # Importing the platform module

import numpy as np

from scipy.fft import fft, fftfreq

from pathlib import Path
from threading import Thread
from multiprocessing import Process
import logging
import pandas as pd

# import schedule
from apscheduler.schedulers.background import BackgroundScheduler
from config.config_dat import read_config_main
from utility_funs import get_measurement_paths

# from simple_pid import PID

# self developed scripts
from custom_email import send_email
from utility_funs import init_figure, flatten, create_meta, save_xz, fit_r_2

# from general_device import measurement_device
# config_dict_main = read_config_main()

ascheduler = BackgroundScheduler()
ascheduler.start()


class Backend:
    """class that:
    - communicates with the daq
    - buffers values until they are stored in pickle files
    - checks the read data and compares it with threshholds (thresholds are set in the web interface)
    - creates a trigger thread if these thresholds exceeded
    - create figures containing the buffered data
    - needs to be configured first with external config_dat.py
    - has the option to activate an IIR filter
    """

    def __init__(self):
        """initiates the data scan and passes the active channel information used to create the web interface"""
        self.is_triggered = False
        self.is_measuring = False
        self.config = read_config_main()
        self.job_manager = self.config["job_manager"]
        # if self.job_manager:
        #     self.job_active = True
        #     self.config['save_opt']= 'job'
        self.measurement_devices = []
        self.list_measurement_devices()
        self.report_queue = queue.Queue()
        self.num_chunks = 0
        self.t0 = datetime.now()  # saves when a scan or a save has started
        self.tstart = self.t0
        self.t0_0 = self.t0.timestamp()
        self.scan_segment_start = self.t0
        self.t_max_val_0 = self.t0  # saves from when to when tha max values have been saved
        self.error = dict()

    def read_measurement_devices(self):
        for measurement_device in self.measurement_devices:
            measurement_device.read_buffer()
        self.num_chunks += 1

    def list_measurement_devices(self):
        self.measurement_devices = []
        for j in range(self.config["num_mccdaqhat_devices"]):
            from device_management.mccdaqhat_class import mccdaqhat

            self.measurement_devices.append(mccdaqhat(j, self))
        for j in range(self.config["num_nidaqmx_devices"]):
            from device_management.nidaqmx_class import NidaqDevice

            self.measurement_devices.append(NidaqDevice(j, self))
        for j in range(self.config["num_uldaq_devices"]):
            from device_management.uldaq_class import Uldevice

            self.measurement_devices.append(Uldevice(j, self))
        for j in range(self.config["num_mcculw_devices"]):
            from device_management.mcculw_class import McculwDevice

            self.measurement_devices.append(McculwDevice(j, self))
        for j in range(self.config["num_audio_devices"]):
            from device_management.audio_class import Audiodevice

            self.measurement_devices.append(Audiodevice(j, self))
        for j in range(self.config["num_eps_devices"]):
            from device_management.eps_class import EpsDevice_chooser

            self.measurement_devices.append(EpsDevice_chooser(j, self))
        for j in range(self.config["num_usbdux_devices"]):
            from device_management.usbdux_class import USBDuxDevice

            self.measurement_devices.append(USBDuxDevice(j, self))

    def start_measurement(self):
        # self.list_measurement_devices()
        self.report_queue = queue.Queue()
        for measurementdevice in self.measurement_devices:
            try:
                if measurementdevice.config["type"] == "uldaq":
                    if measurementdevice.config["active_output"]:
                        # print('start_measurement->measurement.start_ouput_scan')
                        measurementdevice.start_output_scan()
                # print(colored('start_measurement->measurement.start_scan', 'yellow'))
                measurementdevice.start_scan()
            except Exception:
                # print(colored('start_measurement->fehlstart ', 'red'))
                logging.error("could not connect to measurement device")

        self.is_measuring = True
        self.num_chunks = 0

        self.t0 = datetime.now()  # saves when a scan or a save has started
        self.t0_0 = self.t0.timestamp()
        self.scan_segment_start = self.t0
        self.t_max_val_0 = self.t0  # saves from when to when tha max values have been saved
        self.error = dict()
        # self.sched_remove_all_jobs()
        # self.sched_add_all_jobs()
        # self.set_eval_schedules()
        self.apsched_remove_all_jobs()
        self.apsched_add_all_jobs()
        self.set_eval_apschedules()
        logging.info("(re)started scan")
        return None

    def get_t0(self):
        return self.t0

    def get_tstart(self):
        return self.tstart

    def set_tstart(self, start_time):
        self.tstart = start_time

    # def set_eval_schedules(self):
    #     schedule.clear('eval_funs')
    #     if self.is_measuring:
    #         if self.config['eval_opts'] != []:
    #             schedule.every(self.config['eval_period']).seconds.do(self.eval_funs).tag('eval_funs')
    #     return None

    def set_eval_apschedules(self):
        if ascheduler.get_job("eval_funs"):
            ascheduler.remove_job("eval_funs")
        if self.is_measuring:
            if self.config["eval_opts"] != []:
                ascheduler.add_job(
                    self.eval_funs,
                    "interval",
                    seconds=self.config["eval_period"],
                    id="eval_funs",
                )
        return None

    def apsched_remove_all_jobs(self):
        if ascheduler.get_job("autosave"):
            ascheduler.remove_job("autosave")
        if ascheduler.get_job("max_value_report"):
            ascheduler.remove_job("max_value_report")
        if ascheduler.get_job("daily_report"):
            ascheduler.remove_job("daily_report")
        # self.eval_funs, startet und stoppt selbst
        return None

    # def sched_remove_all_jobs(self):
    #     schedule.clear('autosave')
    #     schedule.clear('max_value_report')
    #     schedule.clear('daily_report')
    #     # eval_funs, startet und stoppt selbst
    #     schedule.every(self.config['eval_period']).seconds.do(self.eval_funs).tag('eval_funs')
    #     return None

    # def sched_add_all_jobs(self):
    #     save_opt = self.config['save_opt']

    #     schedule.every(self.config['max_val_report_interval_sec']).seconds.do(self.report_max_values).tag('max_value_report')
    #     schedule.every().day.at('00:00').do(self.daily_report).tag('daily_report')
    #     if save_opt == 'discar':
    #         schedule.every(self.config['autosave_sec']).seconds.do(self.save, args='auto', discard=True).tag('autosave')
    #     if save_opt == 'auto':
    #         schedule.every(self.config['autosave_sec']).seconds.do(self.save, args='auto', discard=False).tag('autosave')
    #     # if save_opt == 'job':
    #     #     if self.job_active:
    #     #         schedule.every(self.config['autosave_sec']).seconds.do(self.save, args='auto', discard=True).tag('autosave')
    #     #     else:
    #     #         schedule.every(self.config['autosave_sec']).seconds.do(self.save, args='auto', discard=False).tag('autosave')

    #     else:
    #         pass
    #     self.set_eval_schedules()

    #     print('schedule jobs started: ',schedule.get_jobs())

    def apsched_add_all_jobs(self):
        save_opt = self.config["save_opt"]

        ascheduler.add_job(
            self.report_max_values,
            "interval",
            seconds=self.config["max_val_report_interval_sec"],
            id="max_value_report",
        )
        ascheduler.add_job(self.daily_report, "cron", hour=0, minute=0, id="daily_report")
        if save_opt == "discar":
            # ascheduler.add_job(self.save, 'interval', seconds=self.config['autosave_sec'], args=['auto', False], id='autosave')
            ascheduler.add_job(
                self.save,
                "interval",
                seconds=self.config["autosave_sec"],
                args=["auto"],
                kwargs={"discard": True},
                id="autosave",
            )
        if save_opt == "auto":
            # ascheduler.add_job(self.save, 'interval', seconds=self.config['autosave_sec'], args=['auto', True], id='autosave')
            ascheduler.add_job(
                self.save,
                "interval",
                seconds=self.config["autosave_sec"],
                args=["auto"],
                kwargs={"discard": False},
                id="autosave",
            )
        # if save_opt == 'job':
        #     if self.job_active:
        #         # schedule.every(self.config['autosave_sec']).seconds.do(self.save, args='auto', discard=True).tag('autosave')
        #         ascheduler.add_job(self.save, 'interval', seconds=self.config['autosave_sec'], args=['auto', True], id='autosave')
        #     else:
        #         # schedule.every(self.config['autosave_sec']).seconds.do(self.save, args='auto', discard=False).tag('autosave')
        #         ascheduler.add_job(self.save, 'interval', seconds=self.config['autosave_sec'], args=['auto', False], id='autosave')

        else:
            pass
        self.set_eval_apschedules()

        # if not ascheduler.start(): ascheduler.start()

        # for job in ascheduler.get_jobs():
        #     print('job: ', job)

    def stop_clean_up(self):
        # damit die aktuellen Daten gespeichert werden auch wenn daily_report
        # noch nicht drann war
        self.daily_report()

        for measurementdevice in self.measurement_devices:
            measurementdevice.stop_clean_up()
        self.is_measuring = False
        # self.sched_remove_all_jobs()
        # self.sched_add_all_jobs()
        # self.set_eval_schedules()
        self.apsched_remove_all_jobs()
        # self.apsched_add_all_jobs()
        self.set_eval_apschedules()

    def check_trigger(self, data_channel_max, tres, trigchannel):
        """
        checks if the data in a channel exceeds its threshold and calls the trigger routine if it does.
        if the trigger routine is runnign no other alarm can be triggered
        Inputs:
            the scanned data from the respective channel
            the treshold of that channel
            the number of the channel which shall be checked
        Outputs
            human readible string containing time of the trigger and the channel
        """
        # print(data_channel_max,tres)
        if data_channel_max > tres:  # any(abs(data_point) > tres for data_point in  data_channel):

            self.is_triggered = True  # blocks autosave
            t_event = datetime.now()
            thread = Thread(
                target=self.trigger_routine,
                args=(
                    trigchannel,
                    t_event,
                ),
            )
            thread.start()
            thread.join()
            # thread.join() alternative zum Schließen des threads
            logging.info("triggered from Channel " + str(trigchannel))
            trigger_log = (
                "triggered at " + t_event.isoformat()[:15] + " from Channel " + str(trigchannel)
            )
            return trigger_log
        else:
            return None

    def trigger_routine(self, trig_channel, t_event):
        """gather the information of all channels 30 seconds before and after the event
        saves it in an extra file and reports it to a given email list
        after the routine is done it can be triggered again
        the routine does not interfere with the continous display and storage of data
        """
        print("---->triggered")

        sleep(
            self.config["trigger_post"]
        )  # to gather information 30 seconds before and after the event
        # create a copy to access deque without mutating
        data_d_l = []
        meta_list = []
        report_str = ""
        fig = init_figure(self.get_all_device_configs())
        i = 0
        for device in self.measurement_devices:
            for channel in device.channels:
                data_d = []
                buffer_copy = channel.buffer.copy()
                t_start = device.time_last_mes
                t_end = device.time_last_mes
                while (
                    t_start > t_event - timedelta(seconds=self.config["trigger_pre"])
                    and len(buffer_copy) > 0
                ):
                    chunk = buffer_copy.pop()
                    data_d.insert(0, chunk[0])
                    t_start = chunk[1][0]
                data_d.reverse()
                data_d = flatten(data_d)

                max_val = np.max(np.array(data_d))

                report_str += f'|{
                    device.config["type"]}{
                    device.number} {
                    channel.channel_num} : {max_val} '
                data_d_l.append(data_d)
                fig["data"][i]["x"] = pd.date_range(t_start, t_end, len(data_d) + 1)
                fig["data"][i]["y"] = data_d
                i += 1
            meta_list.append(
                create_meta(
                    device,
                    t_event - timedelta(seconds=self.config["trigger_pre"]),
                    t_event + timedelta(seconds=self.config["trigger_post"]),
                )
            )
        paths = get_measurement_paths(self.config)
        path0 = paths["path_trigger_reports"]
        # path0 = os.path.join(Path.home(), "Measurements_web_app", "reports")
        # path0 = f"/home/{os.getlogin()}/Measurements_web_app/reports/"
        filename = ""  # device.config['type']+str(device.number)
        computer_name = platform.node()
        filename = filename + computer_name + "_"  # evtl. in config.ini ein Messpunktname o.ä
        time_string = t_event.isoformat().replace(":", "-")
        Path(path0 + time_string[:10]).mkdir(parents=True, exist_ok=True)
        path1 = path0 + time_string[:10] + "/"
        filename += time_string
        full_path = path1 + filename
        # full_path = clean_full_filename(full_path) #fuer alle os ohne
        # Sonderzeichen
        dump = (meta_list, data_d_l)
        # pio.write_html(fig, file=full_path + '.html')
        pio.write_image(fig, file=full_path + ".svg")
        save_report = Process(target=save_xz, args=(full_path + ".xz", dump, "report"))
        save_report.start()
        filetype = ".svg"
        try:
            send_email(
                self.config["email_list"].split(","),
                t_event,
                filename=full_path + filetype,
                channel=trig_channel,
                report_str=report_str,
            )
        except Exception as e:
            logging.info(f"Exception while trying to send E-Mail {e}")
        self.is_triggered = False
        logging.info("send report to " + str(self.config["email_list"]))
        # print('---->triggered', full_path + '.xz')

        return None

    def save(self, args="", discard=False):
        """saves the data of alls measurement devices"""
        meta_list = []
        data_d_l = []
        t_end = None
        for device in self.measurement_devices:
            t_end = device.t0
            for channel in device.channels:
                data_d = []
                bufferrest = 0
                if bufferrest > len(channel.buffer):
                    return None
                while len(channel.buffer) > bufferrest:
                    chunk = channel.buffer.popleft()
                    data_d.extend(chunk[0])
                    t_end = chunk[1][1]
                data_d = np.array(data_d, dtype="single")
                data_d_l.append(data_d)

            meta_list.append(create_meta(device, device.t0, t_end))
            device.t0 = t_end
        # print(meta_list)
        paths = get_measurement_paths(self.config)
        path0 = paths[
            "path_measurements"
        ]  # os.path.join(Path.home(), "Measurements_web_app", "measurements")
        # print ('in save: ',path0)
        filename = ""
        computer_name = platform.node()
        filename = filename + computer_name + "_"  # evtl. in config.ini ein Messpunktname o.ä
        time_string = self.t0.isoformat().replace(":", "-")
        path1 = os.path.join(path0, time_string[:10])
        Path(path1).mkdir(parents=True, exist_ok=True)
        # path1=path0+time_string[:10]+'/'
        filename += time_string.replace(":", "-") + args + ".xz"
        # filename = clean_full_filename(filename)
        full_path = os.path.join(path1, filename)
        # full_path=path1+filename
        # print('backend - save is: ', discard, full_path)

        self.t0 = t_end
        if not discard:
            # print('not discard')
            dump = (meta_list, data_d_l)
            Process(target=save_xz, args=(full_path, dump, args)).start()
        else:
            logging.info("discarded data reason: " + args)
        return None

    def report_max_values(self):
        # email
        t_max_end = datetime.now()
        report_str = ""
        t_average = self.t_max_val_0 + (t_max_end - self.t_max_val_0) / 2
        stored_list = [t_average]  # time is the first value in the list
        for device in self.measurement_devices:
            for channel in device.channels:
                report_str += f'|{
                    device.config["type"]}{
                    device.number} {
                    channel.channel_num} : {
                    channel.max_value} '
                stored_list.append(channel.max_value)
                channel.max_value = 0
        logging.info(
            f"The maximum measured values between {
                self.t_max_val_0} and {t_max_end} are {report_str}"
        )

        # the rest is added later
        self.report_queue.put(stored_list)
        self.t_max_val_0 = t_max_end
        return None

    def daily_report(self):
        reports_list = []
        if self.report_queue.empty():
            return None
        while not self.report_queue.empty():
            reports_list.append(self.report_queue.get())
        # create picture csv
        report_matrix = np.array(reports_list)

        figure = make_subplots(rows=1, cols=1)
        # create a dataframe for csv
        df = pd.DataFrame({"Time": report_matrix[:, 0]})
        i = 1
        for device in self.measurement_devices:
            for channel in device.measuredchannels:
                name = f'{
                    device.config["type"]}{
                    device.number} channel:{channel} : {
                    device.config["quantity"][channel]} in {
                    device.config["units"][channel]}'
                scatter_serie = go.Scatter(
                    x=report_matrix[:, 0],
                    y=report_matrix[:, i],
                    name=name,
                    # marker={'color': self.colors[channel]}
                )
                figure.add_trace(scatter_serie)
                df[name] = report_matrix[:, i]
                i += 1
        figure.update_xaxes(title_text="time", row=1, col=1)
        paths = get_measurement_paths(self.config)
        path0 = paths["path_daily_reports"]
        # path0 = f"/user/{os.getlogin()}/Measurements_web_app/daily_reports"
        Path(path0).mkdir(parents=True, exist_ok=True)
        time_string = report_matrix[0, 0].isoformat().replace(":", "-")
        path1 = os.path.join(path0, time_string[:19])
        pio.write_html(figure, file=path1 + ".html")
        # df = df.applymap(lambda x: f"{x:.8f}".replace('.', ',') if isinstance(x, float) else x)
        df.to_csv(path1 + ".csv", index=False, sep=";")
        logging.info("created daily report")
        return None

    def restart_after_error(self):
        """saves all data in the buffer and restarts the scan after an error occured"""
        self.trying_to_restart = True
        self.save()
        self.stop_clean_up()
        self.start_measurement()

        while self.trying_to_restart:
            try:
                # sleep(2)
                print("trying to restart")
                self.start_measurement()
                self.trying_to_restart = False
            except Exception as e:
                print(e)
                self.stop_clean_up()
        print("restarted scan")
        return ""

    def eval_funs(self):
        if self.config["eval_opts"] == []:
            return None
        for device in self.measurement_devices:
            # print(device.config['sample_rate'],self.config['eval_time'])
            num_datapoints = int(device.config["sample_rate"] * self.config["eval_time"])
            for i, channel in enumerate(device.channels):
                data = []
                queue_copy = channel.fit_queue.copy()
                if not (queue_copy):
                    return None
                while queue_copy:
                    chunk = queue_copy.pop()[0]
                    if len(chunk) + len(data) < num_datapoints:
                        data = [*chunk, *data]
                    else:
                        try:
                            data = [*chunk[len(data) - num_datapoints :], *data]
                        finally:
                            break
                else:
                    # print('chagned_num')
                    num_datapoints = len(data)
                # data=np.array(data)
                # print(data.shape)
                t_vec = np.linspace(0, self.config["eval_time"], num_datapoints)
                if "sin_fit" in self.config["eval_opts"]:
                    channel.params_sinus, channel.sinus_r2 = fit_r_2(
                        t_vec, data, channel.params_sinus, channel.model, max_nfev=5
                    )
                if "min_max" in self.config["eval_opts"]:
                    channel.max = np.max(data)
                    channel.min = np.min(data)
                    channel.average = np.average(data)
                    channel.peak_peak = channel.max - channel.min
                    # print('p_p',channel.peak_peak)
                    for device_output in channel.controlled_devices:
                        setpoint = device_output.config["output_setpoint"]
                        control = (setpoint / channel.peak_peak) * device_output.config[
                            "output_amp"
                        ]
                        if control > 10:
                            control = 10
                        elif control < 0.1:
                            control = 0.1
                        amplitude_change = control / device_output.config["output_amp"]
                        """
                        if device_output.pid==None:
                            device_output.pid=PID()
                            device_output.pid.setpoint = 2
                            device_output.pid.tunings = (0.5, 0, 0)
                            device_output.pid.sample_time = 0.1
                            device_output.pid.output_limits = (0.01, 10)    # Output value will be between 0 and 10
                            control = device_output.pid(channel.peak_peak)
                        else:
                            control = device_output.pid(channel.peak_peak)
                            amplitude_change=(control/device_output.config['output_amp'])
                            print(control)
                        """
                        device_output.out_buffer[:] = [
                            amplitude_change * x for x in device_output.out_buffer
                        ]  # device_output.out_buffer*amplitude_change
                        device_output.config["output_amp"] = control

                if "fft" in self.config["eval_opts"]:
                    channel.fft_frequs = fftfreq(num_datapoints, 1 / device.config["sample_rate"])[
                        : num_datapoints // 2
                    ]
                    channel.fft_vals = np.abs(
                        fft(data)[: num_datapoints // 2]
                    )  # np.hamming(num_datapoints//2)*
        return None

    def get_all_device_configs(self):
        config_list = []
        for device in self.measurement_devices:
            config_list.append(device.config)
        return config_list


if __name__ == "__main__":
    import device_management.device_finder as device_finder
    from WebAppTS import while_thread, start_stop_measurement

    # initializing
    log_filename = "log.log"
    logging.basicConfig(
        filename=log_filename,  # handlers=[logging.StreamHandler()],
        level=logging.DEBUG,
        format="%(asctime)s:%(levelname)s:%(message)s",
    )  # config logger

    if os.path.exists(log_filename):
        with open(
            "log.log"
        ) as logfile:  # reading the logfile to only display newly written loglines
            num_lines_old = len(logfile.readlines())
    else:
        num_lines_old = 0

    # check current platform for import and hardware check
    current_platform = platform.system()

    device_finder.find_available_devices()
    sleep(0.01)
    bend = Backend()
    bend.start_measurement()
    bend.is_measuring = True
    start_stop_measurement("")
    while_thread()
