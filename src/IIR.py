import numpy as np
from scipy import signal
from numpy import pi
import plotly.graph_objs as go
from collections import deque
import iir_filter
from scipy.fftpack import fft, fftfreq


#
# (C) 2020-2021 Bernd Porr, mail@berndporr.me.uk
# Apache 2.0 license
#
import unittest


class IIR2_filter:
    """2nd order IIR filter"""

    def __init__(self, s):
        """Instantiates a 2nd order IIR filter
        s -- numerator and denominator coefficients
        """
        self.numerator0 = s[0]
        self.numerator1 = s[1]
        self.numerator2 = s[2]
        self.denominator1 = s[4]
        self.denominator2 = s[5]
        self.buffer1 = 0
        self.buffer2 = 0

    def filter(self, v):
        """Sample by sample filtering
        v -- scalar sample
        returns filtered sample
        """
        input = v - (self.denominator1 * self.buffer1) - (self.denominator2 * self.buffer2)
        output = (
            (self.numerator1 * self.buffer1)
            + (self.numerator2 * self.buffer2)
            + input * self.numerator0
        )
        self.buffer2 = self.buffer1
        self.buffer1 = input
        return output


class IIR_filter:
    """IIR filter"""

    def __init__(self, sos):
        """Instantiates an IIR filter of any order
        sos -- array of 2nd order IIR filter coefficients
        """
        self.cascade = []
        for s in sos:
            self.cascade.append(IIR2_filter(s))

    def filter(self, v):
        """Sample by sample filtering
        v -- scalar sample
        returns filtered sample
        """
        for f in self.cascade:
            v = f.filter(v)
        return v


class TestFilters(unittest.TestCase):

    coeff1 = [[0.02008337, 0.04016673, 0.02008337, 1.0, -1.56101808, 0.64135154]]

    input1 = [-1.0, 0.5, 1.0]

    result1 = [-2.00833656e-02, -6.14755450e-02, -6.30005740e-02]

    coeff2 = [
        [
            1.78260999e-03,
            3.56521998e-03,
            1.78260999e-03,
            1.00000000e00,
            -1.25544047e00,
            4.09013783e-01,
        ],
        [
            1.00000000e00,
            2.00000000e00,
            1.00000000e00,
            1.00000000e00,
            -1.51824184e00,
            7.03962657e-01,
        ],
    ]

    input2 = [-1, 0.5, -1, 0.5, -0.3, 3, -1e-5]

    result2 = [
        -0.00178261,
        -0.01118353,
        -0.03455084,
        -0.07277369,
        -0.11973872,
        -0.158864,
        -0.15873629,
    ]

    def test1(self):
        f = IIR_filter(self.coeff1)
        for i, r in zip(self.input1, self.result1):
            self.assertAlmostEqual(r, f.filter(i))

    def test2(self):
        f = IIR_filter(self.coeff2)
        for i, r in zip(self.input2, self.result2):
            self.assertAlmostEqual(r, f.filter(i))

    def test3(self):
        f = IIR2_filter(self.coeff1[0])
        for i, r in zip(self.input1, self.result1):
            self.assertAlmostEqual(r, f.filter(i))


# if __name__ == '__main__':
#     unittest.main()


class IIR_GeophoneFilter:

    # v - array mit Messwerten ohne Filterkorrektur
    # fv - Frequenz des Butterworth Vorfilters mit Filtergrad 2
    # fn - Frequenz des Butterworth Nachfilters mit Filtergrad 2
    # f1 - Eigenfrequenz des Geophons
    # f2 - Eigenfrequenz=Zielfrequenz für das gefiltere Geophon
    # d1 - Dämpfung des Geophones - standard 0.56 /0.7
    # d2 - Dämpfung des Zielgeophones - standard 0.7071
    # T  - Abtastrate = 1/f - standard 1/1024 = 0.00976563 s
    # y3 - Rückgabe der gefilterten Messwerte
    # Bandbegrenzung bool ob Bandbegrenzung nach DIN 45669-1:2020-06 Formel(3) angewand werden soll
    # f_bb_u- Frequenz für Bandbegrenzung nach DIN 45669-1:2020-06 Formel(3) #0.8
    # f_bb_o Frequenzband für Bandbegrenzung nach DIN 45669-1:2020-06
    # Formel(3) #100 für fu=1 fo=80/ 394 für fo=315

    def __init__(
        self,
        fv=0.4,
        fn=0.25,
        f1=4.5,
        d1=0.56,
        f2=0.5,
        d2=1.0,
        T=1 / 1000,
        Bandbegrenzung=False,
        f_bb_u=0.8,
        f_bb_o=100.0,
        Poles_Zeros=True,
        KB_Filter=False,
        fv_fn=True,
        bstop50Hz=False,
    ):

        self.T = T
        # Nyquist-Frequenz
        self.nyq = 0.5 / T
        self.fs = 1 / T
        self.fv_fn = fv_fn
        # Vorfilter
        self.bv, self.av = signal.butter(2, fv / self.nyq, "highpass")  # ,fs=1/T
        self.ziv = signal.lfilter_zi(self.bv, self.av)
        # GeoFilter
        w1 = 2 * pi * f1
        w2 = 2 * pi * f2

        p = []
        q = []

        # inverser Filter nach Poles and Zeros
        if Poles_Zeros:
            # Nenner
            a = np.tan(w2 * T * 0.5)
            p.append(1 + 2 * d2 * a + a * a)
            p.append(2 * a * a - 2)
            p.append(1 - 2 * d2 * a + a * a)
            # Zähler
            a = np.tan(w1 * T * 0.5)
            q.append(1 + 2 * d1 * a + a * a)
            q.append(2 * a * a - 2)
            q.append(1 - 2 * d1 * a + a * a)

        # inverser Filter nach Schwarzenau
        else:
            # Nenner
            p.append(4 + 4 * d2 * w2 * T + w2 * w2 * T * T)
            p.append(2 * w2 * w2 * T * T - 8)
            p.append(4 - 4 * d2 * w2 * T + w2 * w2 * T * T)
            # Zähler
            q.append(4 + 4 * d1 * w1 * T + w1 * w1 * T * T)
            q.append(2 * w1 * w1 * T * T - 8)
            q.append(4 - 4 * d1 * w1 * T + w1 * w1 * T * T)

        self.q_norm = (q[0] / p[0], q[1] / p[0], q[2] / p[0])
        self.p_norm = (p[0] / p[0], p[1] / p[0], p[2] / p[0])
        self.zi = signal.lfilter_zi(self.p_norm, self.q_norm)

        # print('p_norm =', self.p_norm)
        # print('q_norm =', self.q_norm)

        # Nachfilter
        self.bn, self.an = signal.butter(2, fn / self.nyq, "highpass")  # ,fs=1/T
        self.zin = signal.lfilter_zi(self.bn, self.an)
        self.predata = deque(maxlen=50)
        # for i in range(50):
        #    self.predata.put([0]*1000)
        # Bandbegrenzung nach DIN 45669-1:2020-06 Formel(3)
        # Bandpass
        self.bstop50Hz = bstop50Hz
        self.Bandbegrenzung = Bandbegrenzung
        if KB_Filter:
            self.Bandbegrenzung = True
        self.KB_Filter = KB_Filter
        # if self.Bandbegrenzung:
        #    #self.b_bb_u, self.a_bb_u= signal.butter(2, f_bb_u, 'highpass',fs=1/T)
        #    #self.b_bb_o, self.a_bb_o= signal.butter(2, f_bb_o, 'lowpass',fs=1/T)
        # self.b_bb, self.a_bb = signal.butter(2,
        # [f_bb_u/self.nyq,f_bb_o/self.nyq], 'bandpass')# ,fs=1/T

        # alle Filterkoeffizienten aller benötigten Filter berechnuen
        sos_v = signal.butter(2, fv / self.nyq, "highpass", output="sos")
        sos_norm = signal.tf2sos(self.q_norm, self.p_norm)
        sos_n = signal.butter(2, fn / self.nyq, "highpass", output="sos")
        sos_KB = signal.butter(1, 5.6 / self.nyq, "highpass", output="sos")
        # sos_bb_u = signal.butter(2, f_bb_u / self.nyq, 'highpass', output='sos')
        # sos_bb_o = signal.butter(2, f_bb_o / self.nyq, 'lowpass', output='sos')
        sos_band = signal.butter(
            2, [f_bb_u / self.fs * 2, f_bb_o / self.fs * 2], "bandpass", output="sos"
        )
        sos_bstop50Hz = signal.butter(
            4, [48.0 / self.fs * 2, 52.0 / self.fs * 2], "bandstop", output="sos"
        )

        # die IIR-Filter berechnen
        self.iir_v = iir_filter.IIR_filter(sos_v)  # der Geophonvorfilter
        self.iir_norm = iir_filter.IIR_filter(sos_norm)  # der eigendliche Geophonfilter
        self.iir_n = iir_filter.IIR_filter(sos_n)  # der Geophonnachfilter
        # der KB-Bewertungsfilter des Geophonsignals, muss vorher gebanpassed
        # werden
        self.iir_KB = iir_filter.IIR_filter(sos_KB)
        # self.iir_bb_u= iir_filter.IIR_filter(sos_bb_u) # der untere Filter für den Bandpassfilter nach DIN 4150-2
        # self.iir_bb_o= iir_filter.IIR_filter(sos_bb_o) # der obere Filter für den Bandpassfilter nach DIN 4150-2
        # der obere Filter für den Bandpassfilter nach DIN 4150-2
        self.iir_bstop50Hz = iir_filter.IIR_filter(sos_bstop50Hz)
        self.iir_band = iir_filter.IIR_filter(sos_band)

    def filter_fun(self, v):

        y, self.ziv = signal.lfilter(self.bv, self.av, v, zi=self.ziv)
        y, self.zi = signal.lfilter(self.q_norm, self.p_norm, y, zi=self.zi)
        y, self.zin = signal.lfilter(self.bn, self.an, y, zi=self.zin)

        # if self.Bandbegrenzung:
        # y = signal.lfilter(self.b_bb, self.a_bb, y)
        # y= signal.lfilter(self.b_bb_u, self.a_bb_u, y)
        # y= signal.lfilter(self.b_bb_o, self.a_bb_o, y)
        # print(len(v))
        # self.iir_n.filter(self.iir_norm.filter(self.iir_v.filter(v)))
        return -y
        # -y  # - um den 180° Phasenversatz zu kompensieren

    def filter_fun2(self, v):
        # uses the iir_filter function needs inputs with the same blocksize

        # zuerst die Netzfrequenz herausfiltern
        if self.bstop50Hz:
            filtered_vector = [self.iir_bstop50Hz.filter(value) for value in v]

        # jetzt den Geophonfilter mit Vor- und Nachfilter anwenden
        if self.fv_fn:
            # print('vor - normGeo - nach - Filter')
            filtered_vector = [
                self.iir_n.filter(self.iir_norm.filter(self.iir_v.filter(value))) for value in v
            ]
        else:
            # print('normGeo  - Filter')
            filtered_vector = [self.iir_norm.filter(value) for value in v]

        # dann dieses Signal mit dem Norm-Bandfilter (1-80/315Hz) filtern
        if self.Bandbegrenzung:
            # print('band - Filter')
            filtered_vector = [self.iir_band.filter(value) for value in filtered_vector]

        # das Bandgefilterte Signal zur Bewertung von Erschütterungen auf Menschen in Gebäuden
        # mit einem Bewertungsfilter 5.6 Hz bewerten - DIN 4150-2
        if self.KB_Filter:
            # print('kb - Filter')
            filtered_vector = [self.iir_KB.filter(value) for value in v]

        return filtered_vector


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from scipy.signal import chirp
    import pandas as pd

    sampling_rate = 3000
    # Generate or load your data
    t = np.linspace(0.0, 320, 320 * sampling_rate)
    data = np.zeros(320 * sampling_rate)
    data = chirp(t, f0=1.0, f1=320, t1=320, phi=270, method="logarithmic")

    # Initialize your IIR filter object
    iir = IIR_GeophoneFilter(
        fv=0.45,
        fn=0.25,
        f2=0.35,
        d2=0.707,
        T=1 / sampling_rate,
        Bandbegrenzung=False,
        fv_fn=True,
    )

    # Apply filtering and capture the filtered data
    filtered_data = iir.filter_fun2(data)

    # Convert the filtered data to a NumPy array if not already
    filtered_data_array = np.array(filtered_data)

    # Calculate the FFT of the filtered data
    filtered_data_fft = fft(filtered_data_array[5 * sampling_rate:])
    df = pd.read_csv("d:\\programming\\src\\webapp_mcc128ts\\CHIRP-FILT_FreCor.txt", sep=";")
    sm6_data = np.array(df["1.Kanal"])

    
    sm6_fft = fft(sm6_data[5 * sampling_rate:])

    # Calculate the absolute value of the FFT
    abs_filtered_data_fft = np.abs(filtered_data_fft)
    abs_sm6_fft = np.abs(sm6_fft)
    freq_fft = fftfreq(len(filtered_data_array), 1 / sampling_rate)

    # Select only the positive frequency side (excluding DC component)
    pos_freq_index = np.where(freq_fft > 0)[0]
    pos_freq_fft = abs_filtered_data_fft[pos_freq_index]
    pos_sm6_fft = abs_sm6_fft[pos_freq_index]

    # Plotting the absolute value of the FFT for positive frequencies with log
    # scale
    plt.figure(figsize=(10, 6))
    plt.plot(t, filtered_data)
    # plt.plot(freq_fft[pos_freq_index], pos_freq_fft)
    # plt.plot(freq_fft[pos_freq_index], pos_sm6_fft)
    # plt.xscale('log')  # Set x-axis to logarithmic scale
    # plt.title('Absolute Value of FFT for Positive Frequencies (Log Scale)')
    # plt.xlabel('Frequency [Hz]')
    # plt.ylabel('Magnitude')
    plt.grid(True)
    plt.show()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Zeit"], y=df["1.Kanal"], name="Meda"))
    fig.add_trace(go.Scatter(x=t, y=filtered_data_array, name="filtered_data"))
    fig.write_html("iir-sm6-fft.html")
    # fig.show()

    # df.to_csv('Chirp-filt.csv', sep=';', index=False)

    # iir_data = iir.filter_fun2(df['ohne'].to_numpy())
    # iir1_data = iir1.filter_fun2(df['ohne'].to_numpy())
    # fig = go.Figure()
    # fig.add_trace(go.Scatter(x=df['Zeit'],y=df['Hardware'],name='Hardware'))
    # fig.add_trace(go.Scatter(x=df['Zeit'],y=df['Software'], name ='Software'))
    # fig.add_trace(go.Scatter(x=df['Zeit'],y=df['ohne'],name='ohne'))
    # fig.add_trace(go.Scatter(x=df['Zeit'],y=iir_data,name = 'iir'))
    # fig.add_trace(go.Scatter(x=df['Zeit'],y=iir1_data,name = 'iir1'))
    # fig.update_legends()
    # fig.show()
