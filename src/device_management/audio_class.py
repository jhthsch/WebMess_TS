from device_management.general_device import Measurement_device
from config.config_dat import read_config_device
import sounddevice as sd
import sys
import os
import inspect
import queue
import numpy as np
from time import sleep

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)


def find_audio_devices():
    return sd.query_devices()


class Audiodevice(Measurement_device):

    def __init__(self, number, backend) -> None:
        self.type = "audio"
        super().__init__(self.type, number, backend)
        self.downsampling = 1
        self.stream = None
        self.mapping = None
        self.q = queue.Queue()

    def start_scan_sub(self, config=None):

        def audio_callback(indata, frames, time, status):
            """This is called (from a separate thread) for each audio block."""
            if status:
                print(status, file=sys.stderr)
            # Fancy indexing with mapping creates a (necessary!) copy:
            self.q.put((indata[:: self.downsampling]))

        self.config = read_config_device(self.type, self.number)
        # not sure if RawInputStream stream that returns plain buffer or Inputstream that returns numpy array
        # print(sd.query_devices(self.config['device']['descriptor']))
        stream_sample_rate = 44100  # 48000
        self.downsampling = round(stream_sample_rate / self.config["sample_rate"])
        self.config["sample_rate"] = stream_sample_rate / self.downsampling
        # equal to 0.25 seconds of recording
        blocksize = int(stream_sample_rate * 0.25)
        # this is to make sure that the blocksize is a multiple of the
        # downsampling value
        blocksize = blocksize - (blocksize % self.downsampling)

        self.stream = sd.InputStream(
            device=self.config["device"]["descriptor"],
            channels=max(self.config["channels_on"]) + 1,
            samplerate=stream_sample_rate,
            blocksize=blocksize,
            callback=audio_callback,
        )

        # print(colored('audio_class.start_scan', 'yellow'))

        self.stream.start()
        return self.config, self.config["channels_on"]

    def read_buffer(self):
        """reads all the chunks from the"""
        data_out = np.empty([0, max(self.config["channels_on"]) + 1])

        while not self.q.empty():
            chunk = self.q.get()
            data_out = np.concatenate((data_out, chunk), axis=0)
        data_out = data_out.transpose()
        for i, channel in enumerate(self.channels):
            data_out[i, :] = data_out[i, :] * self.config["scalingfactor"][channel.channel_num]
        self.add_numpy_data_to_buffer(data_out)

    def stop_clean_up(self):
        try:
            self.stream.stop()
            self.stream.close()
        except Exception as e:
            print(e)


if __name__ == "__main__":
    print(find_audio_devices())
    a = Audiodevice(0, backend=None)
    a.start_scan_sub()
    for i in range(5):
        sleep(0.5)
        print("Audio read_buffer: ", i)
        a.read_buffer()
