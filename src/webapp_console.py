import threading
import time
import sys
import signal as signal2
from threading import Thread
import datetime  #
from time import sleep
from backend import Backend
from apscheduler.schedulers.background import BackgroundScheduler
import device_management.device_finder as device_finder
from job_manager import JobScheduler

bend = Backend()
ascheduler = BackgroundScheduler()
ascheduler.start()
job_scheduler = JobScheduler(bend)


# Globale Variable, um den Status des Messprogramms zu steuern
running = False


def clear_lines(n):
    """
    Bewegt den Cursor nach oben und löscht n Zeilen.
    """
    for _ in range(n):
        print("\033[A\033[K", end="")  # Cursor hoch + Zeile löschen


def messprogramm():
    """
    Funktion, die das Messprogramm simuliert.
    """
    global running
    i = 0
    print("Messprogramm läuft. Drücke 'Stop' im Menü, um es zu beenden.")
    while running:
        i += 1
        # Simuliere das Sammeln von Messdaten
        print("Messe Daten...:", i)
        clear_lines(1)
        time.sleep(1)


def menue():
    """
    Konsolenmenü für Start, Stop und Exit.
    """
    global running
    thread = None  # Speichere den Thread des Messprogramms
    auswahl = 4
    while True:
        print("\n--- Menü ---")
        print("1. Start continiuos measurement")
        print("2. Start job measurement")
        print("3. Stop")
        print("4. Exit")

        # Eingabe vom Benutzer
        auswahl = input("Wähle eine Option (1/2/3/4): ")

        if auswahl == "1":
            if running:
                print("Das Messprogramm läuft bereits!")
            else:
                running = True
                bend.apsched_remove_all_jobs()
                thread = threading.Thread(target=start_bend, daemon=True)
                thread.start()
                print("Messprogramm gestartet.")

        elif auswahl == "2":
            if running:
                print("Das Messprogramm läuft bereits!")
            else:
                print("Messjobs werden eingelesen...")
                job_scheduler = JobScheduler(bend)

                if job_scheduler.load_and_validate_times():
                    job_scheduler.schedule_measurements()
                    job_scheduler.start_scheduler()
                else:
                    print("No valid measurements to schedule found.")
                # bend.is_measuring=True
                # start_stop_measurement()

        elif auswahl == "3":
            if not running:
                print("Das Messprogramm läuft nicht.")
            else:
                running = False
                print("Messprogramm wird gestoppt...")
                if auswahl == 1:
                    bend.is_measuring = True
                    start_stop_measurement()
                elif auswahl == 2:
                    pass

        elif auswahl == "4":
            if running:
                running = False
                print("Messprogramm wird gestoppt...")
                time.sleep(1)  # Warte kurz, bis der Thread beendet wird
                start_stop_measurement()
            print("Programm wird beendet. Auf Wiedersehen!")
            break
        else:
            print("Ungültige Auswahl. Bitte 1, 2, 3 oder 4 eingeben.")


def start_bend():
    device_finder.find_available_devices()
    sleep(0.01)
    # bend = Backend()
    bend.start_measurement()
    bend.is_measuring = False
    start_stop_measurement()
    while_thread()


def while_thread():
    """main loop for reading measurements and for scheduled events such as saving,
    repots and value evaluation
    """
    # sleep(2)
    "starting while thread"
    while bend.is_measuring:
        try:
            bend.read_measurement_devices()
            # schedule.run_pending() # apscheduler runs all "added" job
            # automatically
        except Exception as e:
            print(f"in while_thread: {e}")
        except (KeyboardInterrupt, SystemExit):
            bend.is_measuring = False
            start_stop_measurement()
            ascheduler.shutdown()
        sleep(0.4)


def signal_handler(_sig, _frame):
    bend.stop_clean_up()
    sys.exit(0)


def start_stop_measurement():
    if bend.is_measuring:
        bend.is_measuring = False
        bend.stop_clean_up()
        bend.save(args="stopping")
    else:
        # speichern von daily reports, stoppen aller jobs
        # 'autosave','max_value_report','daily_report'
        bend.stop_clean_up()
        bend.set_tstart(datetime.datetime.now())  # startzeit des neuen Messbeginns speichern
        bend.start_measurement()  # alle registrierten Messgeraete und jobs s.o. starten
        sleep(0.5)  # Zeitgeben zum sicheren Start der Messung
        bend.is_measuring = True
        # Dauerschleife für Messung aller Messgräte/Kanäle und laufen lassen
        # aller angemeldet jobs
        Thread(target=while_thread).start()
        # print('started measurement')
    # raise PreventUpdate
    return "refresh"


signal2.signal(signal2.SIGINT, signal_handler)

if __name__ == "__main__":
    menue()
