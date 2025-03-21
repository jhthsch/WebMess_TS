import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import time
from backend import Backend
import threading
import sys
import signal as signal2
import device_management.device_finder as device_finder
from WebAppTS import start_stop_measurement


class JobMeasurement:
    def __init__(self, bend, job_id, start_time, stop_time):
        self.bend = bend
        self.job_id = job_id
        self.start_time = start_time
        self.stop_time = stop_time
        self.is_active = False  # Status to monitor whether the measurement is active

    def start_measurement(self):
        """Starts the measurement and sets the status to active."""
        self.is_active = True
        print(
            f"Measurement {
                self.job_id} started at: {
                self.start_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.bend.apsched_remove_all_jobs()
        thread = threading.Thread(target=self.start_bend, daemon=True)
        thread.start()
        # Debug-Ausgabe
        # print(f"Measurement {self.job_id} is_active: {self.is_active}")

    def start_bend(self):
        device_finder.find_available_devices()
        time.sleep(0.01)
        self.bend.start_measurement()
        self.bend.is_measuring = False
        self.start_stop_measurement()
        self.while_thread()

    def while_thread(self):
        """main loop for reading measurements and for scheduled events such as saving,
        repots and value evaluation
        """
        # sleep(2)
        "starting while thread"
        while self.bend.is_measuring:
            try:
                self.bend.read_measurement_devices()
                # schedule.run_pending() # apscheduler runs all "added" job
                # automatically
            except Exception as e:
                print(f"in while_thread: {e}")
            except (KeyboardInterrupt, SystemExit):
                self.bend.is_measuring = False
                self.bend.start_stop_measurement()
                self.bendbend.ascheduler.shutdown()
            time.sleep(0.4)

    def signal_handler(_sig, _frame):
        bend.stop_clean_up()
        sys.exit(0)

    def start_stop_measurement(self, _):
        if self.bend.is_measuring:
            self.bend.is_measuring = False
            self.bend.stop_clean_up()
            self.bend.save(args="stopping")
        else:
            # speichern von daily reports, stoppen aller jobs
            # 'autosave','max_value_report','daily_report'
            self.bend.stop_clean_up()
            self.bend.set_tstart(datetime.now())  # startzeit des neuen Messbeginns speichern
            self.bend.start_measurement()  # alle registrierten Messgeraete und jobs s.o. starten
            time.sleep(0.5)  # Zeitgeben zum sicheren Start der Messung
            self.bend.is_measuring = True
            # Dauerschleife für Messung aller Messgräte/Kanäle und laufen
            # lassen aller angemeldet jobs
            threading.Thread(target=self.while_thread).start()
            # print('started measurement')
        # raise PreventUpdate
        return "refresh"

    signal2.signal(signal2.SIGINT, signal_handler)

    def stop_measurement(self):
        """Stops the measurement, calculates the duration, and sets the status to inactive."""
        self.bend.is_measuring = True
        start_stop_measurement()
        self.is_active = False
        print(
            f"Measurement {
                self.job_id} stopped at: {
                self.stop_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        # Debug-Ausgabe
        # print(f"Measurement {self.job_id} is_active: {self.is_active}")

        # Calculate the duration of the measurement
        duration = self.stop_time - self.start_time
        print(
            f"Measured duration for Measurement {
                self.job_id}: {
                str(duration)}"
        )
        return self.job_id, self.stop_time  # Return job details for logging


class JobScheduler:
    def __init__(self, bend):
        self.bend = bend
        self.csv_file = self.bend.config["job_list_filename"]
        self.measurement_jobs = []  # List to store all valid measurements
        self.job_scheduler = BackgroundScheduler()

    def load_and_validate_times(self):
        """Loads and validates measurement times from the CSV file."""
        try:
            data = pd.read_csv(self.csv_file)
            current_time = datetime.now()

            # Each row in the CSV is treated as a measurement
            for index, row in data.iterrows():
                start_time_str = row["Start Time"]
                stop_time_str = row["Stop Time"]

                # Convert strings to datetime objects
                start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                stop_time = datetime.strptime(stop_time_str, "%Y-%m-%d %H:%M:%S")

                # Validate times
                if start_time >= stop_time:
                    print(
                        f"Error in row {
                            index +
                            1}: Start time must be before stop time."
                    )
                    continue
                if start_time <= current_time or stop_time <= current_time:
                    print(
                        f"Error in row {
                            index +
                            1}: Times must be in the future."
                    )
                    continue

                # Create a valid measurement and add it to the list
                measurement = JobMeasurement(self.bend, index + 1, start_time, stop_time)
                self.measurement_jobs.append(measurement)

            return len(self.measurement_jobs) > 0  # Returns True if there are valid measurements
        except Exception as e:
            print("Error reading or validating times:", e)
            return False

    def schedule_measurements(self):
        """Schedules all loaded and validated measurements with APScheduler."""
        for measurement in self.measurement_jobs:
            # Schedule start and stop times with APScheduler
            self.job_scheduler.add_job(
                measurement.start_measurement, "date", run_date=measurement.start_time
            )
            self.job_scheduler.add_job(
                self.stop_measurement_wrapper,
                "date",
                run_date=measurement.stop_time,
                args=[measurement],
            )

            print(
                f"Measurement {
                    measurement.job_id} scheduled from {
                    measurement.start_time.strftime('%Y-%m-%d %H:%M:%S')} "
                f"to {
                    measurement.stop_time.strftime('%Y-%m-%d %H:%M:%S')}."
            )

    def stop_measurement_wrapper(self, measurement):
        """Wrapper to call stop_measurement and handle exceptions."""
        try:
            self.stop_measurement(measurement)
        except Exception as e:
            print(
                f"Error in stop_measurement_wrapper for measurement {
                    measurement.job_id}: {e}"
            )

    def stop_measurement(self, measurement):
        """Stops a specific measurement and logs completion."""
        # print(f"Stopping measurement {measurement.job_id}...")  #
        # Debug-Ausgabe
        job_id, stop_time = measurement.stop_measurement()
        # print(f"Job {job_id} has been completed at {stop_time.strftime('%Y-%m-%d %H:%M:%S')}.")

    def start_scheduler(self):
        """Starts the APScheduler and waits until all measurements are complete."""
        print("Starting the scheduler...")
        self.job_scheduler.start()

        try:
            while True:  # Loop continuously
                # Get all currently active jobs
                active_jobs = self.job_scheduler.get_jobs()
                print(f"Active jobs: {len(active_jobs)}")  # Debug-Ausgabe

                # Check if there are any active jobs in the scheduler
                if not active_jobs:  # No active jobs left
                    print("No active jobs remaining. Exiting...")
                    break
                time.sleep(0.5)
        except (KeyboardInterrupt, SystemExit):
            print("Scheduler interrupted. Exiting...")
        finally:
            self.job_scheduler.shutdown()
            print("Program terminated.")


# Main program execution
if __name__ == "__main__":
    bend = Backend()
    job_scheduler = JobScheduler(bend)

    if job_scheduler.load_and_validate_times():
        job_scheduler.schedule_measurements()
        job_scheduler.start_scheduler()
    else:
        print("No valid measurements to schedule found.")
