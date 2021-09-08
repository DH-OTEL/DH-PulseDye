#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 22:59:55 2020

@author: thomasusherwood
"""

from GUI_Vars import GUI_Vars
import numpy as np
from pandas import read_csv
from scipy import interpolate, signal
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt
from getextinctioncoef import getextinctioncoef
from remezord import remezord
from typing import List
import tkinter as tk
from tkinter import ttk
import time
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from AIF_Saving import AIF_Saving
from collections import Counter
import statistics


class TI_to_AIF:
    """
    Handles interactive GUI and signal processing parts of creating the AIF file
    """

    def __init__(self, filename: str, gui_vars, wv: List[float] = [805, 940], inv: bool = False,
                 filt_method: str = 'upenn', savedata: int = 0):
        """
        Constructor for TI_to_AIF
        """

        self.filename = filename
        self.gui_vars = gui_vars
        self.wv = wv
        self.inv = inv
        self.filt_method = filt_method
        self.savedata = savedata

        self.x0 = 0
        self.x1 = []

        self.collect_x0 = False
        self.collect_x1 = False

    def calculate_AIF(self):
        """
        Main function for TI_to_AIF. Calculates PSD for heart rate using pwelch.
        """
        np.seterr(divide='raise', invalid='raise')

        fid = open(self.filename, "r")
        X1 = np.loadtxt(fid, skiprows=6, delimiter=',')
        fid.close()
        if self.gui_vars.SaO2 != 0:
            SaO2 = self.gui_vars.SaO2
        else:
            SaO2 = 0.98
        if self.gui_vars.tHb != 0:
            tHb = self.gui_vars.tHb
        else:
            tHb = 14

        print("Sa02 = ", SaO2, ", tHb = ", tHb)

        # Calculate sampling Rate
        len_X1 = len(X1[:, 6])
        tint = [None] * len_X1  # list for int values for timestamps
        sdps = []  # list for number of data points for each second

        for i in range(len_X1):
            tint[i] = int(X1[i, 6])

        tot = Counter(tint)  # Gives totals of data points for each second

        # finds least common time counter to delete last second from averages
        lcn = tot.most_common()[:-1-1:-1]
        print("lcn = ", lcn)

        llcn = (lcn[0])
        # print(llcn[0])
        del tot[llcn[0]]
        print(tot)

        mean = statistics.mean(tot.values())
        print("mean = ", mean)

        fs = 300  # sampling rate
        fs = round(mean)  # sampling rate
        print("sampling rate = ", fs)
        tbl = [10, 60]  # reliable baseline data

        # red and ir channels (raw)
        RED = X1[:, 4].T
        IR = X1[:, 5].T

        # if you're using the original Nihon Kohden probes, you'll want to flip
        # these around.
        if self.inv:
            RED_t = RED
            RED = IR
            IR = RED_t

        # baseline signal from which to calculate heart-rate
        RED_base = np.array(RED[1000:41000])
        IR_base = np.array(IR[1000:41000])
        welch_base = np.vstack((RED_base, IR_base))

        # powerspectrum
        f, P = signal.welch(welch_base, fs=fs, nperseg=welch_base.shape[1]/4)

        # Embeds PSD plot into GUI, and allows user to choose points
        bpm = f * 60
        self.embedHRplot(bpm, P, RED, IR, fs, SaO2, tHb, tbl)

    def embedHRplot(self, bpm, P, RED, IR, fs, SaO2, tHb, tbl):
        """Embeds PSD plot for heart rate into Tkinter GUI, and allows user to choose points

        Args:
            bpm (ndarray): frequency values for plot
            P (ndarray): powerspectrum values for plot
            RED (ndarray): Red voltage signal
            IR (ndarray): IR voltage signal
            fs (int): sampling rate
            SaO2 (float): oxygen saturation
            tHb (float): total hemoglobin
            tbl (list[int]): reliable baseline data
        """
        def onclick(event):
            """Saves x-coordinate of point clicked, draws vertical line.

            Args:
                event (Event): clicking event
            """
            if self.collect_x0:
                # Saves x-coord
                self.collect_x0 = False
                self.x0 = event.xdata
                # Plots vertical line
                ax.axvline(self.x0, color='red', linestyle='dashed')
                self.gui_vars.canvas.draw()
                self.gui_vars.canvas.flush_events()
                # time.sleep(1)

                # Resize Tkinter window
                self.msg = ttk.Label(self.gui_vars.root, text='  ')
                self.msg.grid(row=8)
                self.gui_vars.root.geometry("460x285")
                print("x0 = ", self.x0)
                self.gui_vars.fig.clf()

                # Run signal processing code on Red and IR signals
                self.filter_signal(RED, IR, fs, SaO2, tHb, tbl)

        # Enables contents of onclick function for this instance of mpl_connect
        self.collect_x0 = True

        # Plot data and embed plot in GUI
        ax = self.gui_vars.fig.add_subplot()
        ax.plot(bpm.T, P[0, :], bpm.T, P[1, :])
        ax.set_title("Select center of the heart-rate peak")
        ax.set_xlim(12, 180)
        ax.set_xlabel("frequency (beats per min).")
        self.gui_vars.fig.subplots_adjust(left=.12)

        # tracks clicks in figure
        cid = self.gui_vars.fig.canvas.mpl_connect(
            'button_press_event', onclick)

        self.gui_vars.canvas.draw()

        # placing the canvas on the Tkinter window
        self.gui_vars.canvas.get_tk_widget().grid(row=9, columnspan=3, padx=10)
        self.gui_vars.root.geometry("525x705")

        self.gui_vars.root.mainloop()

    def filter_signal(self, RED, IR, fs, SaO2, tHb, tbl):
        """Filters Red and IR signals based on HR information

        Args:
            RED (ndarray): Red voltage signal
            IR (ndarray): IR voltage signal
            fs (int): sampling rate
            SaO2 (float): oxygen saturation
            tHb (float): total hemoglobin
            tbl (list[int]): reliable baseline data

        Raises:
            NameError: invalid filter method

        Returns:
            [tuple]: ndarrays for t (time) and Ca (concentration)
        """

        ghr = self.x0
        fhr = ghr / 60

        # Demodulate signal and compute the flux ratio and concentration.
        # get carrier signal from envelope (could also apply a bandpass filter)
        if self.filt_method == 'simple':
            fRED = savgol_filter(-np.log(RED), 20, 3)
            fIR = savgol_filter(-np.log(IR), 20, 3)
        elif self.filt_method == 'upenn':  # custom filter: upenn method (slow)
            fhwid = 0.10
            fl = (1 - fhwid) * fhr
            fh = (1 + fhwid) * fhr

            # Correcting stopband and passband values for remezord
            A_SB_inp = 60
            A_SB = 10.**(-A_SB_inp/20.)
            A_PB_inp = 1
            A_PB = (10. ** (A_PB_inp / 20.) - 1) / \
                (10 ** (A_PB_inp / 20.) + 1) * 2
            A_SB2_inp = 60
            A_SB2 = 10. ** (-A_SB2_inp / 20.)

            # Generate remez filter parameters with remezord
            (N_upenn, F_upenn, A_upenn, W_upenn) = \
                remezord([fl - 0.2, fl, fh, fh + 0.2], [1, 0, 1],
                         [A_SB, A_PB, A_SB2], Hz=fs)

            # Generate taps using remez
            taps = signal.remez(N_upenn, F_upenn*fs, [0, 1, 0], weight=W_upenn,
                                fs=fs)

            # Filter Red and IR signals
            fRED = signal.lfilter(taps, 1, -np.log(RED))
            fIR = signal.lfilter(taps, 1, -np.log(IR))
        else:  # if filt_method isn't valid, raise NameError
            raise NameError("Invalid filt_method")

        # find the peaks - min peak distance is defined as half the heart-rate
        locsir, _ = signal.find_peaks(fIR, distance=round((0.5 / fhr) * fs))
        pksir = np.array(self.find_peak_heights(fIR, locsir))

        # find the troughs
        tir = np.zeros((1, len(locsir) - 1))
        minir = np.zeros((1, len(locsir) - 1))
        locsirmin = np.zeros((1, len(locsir) - 1))
        pksir = pksir[0:len(pksir) - 1].T
        tmpt = np.array([i / fs for i in range(1, len(fIR) + 1)])
        for k in range(len(locsir) - 1):
            tir[0, k] = np.mean(tmpt[locsir[k]:locsir[k+1]])
            locsir_sublist = np.array(fIR[locsir[k]:locsir[k+1]])
            minir[0, k] = locsir_sublist.min()
            loctmp = np.where(locsir_sublist == minir[0, k])[0][0]
            locsirmin[0, k] = locsir[k] + loctmp - 1

        # interpolate red from IR peaks and troughs. uses scipy's interpolate
        # library
        f_interp = interpolate.interp1d(tmpt, fRED)
        pksred = f_interp(tmpt[locsir[0:len(locsir) - 1].tolist()])
        minred = f_interp(tmpt[[int(i) for i in locsirmin[0, :]]])

        # truncate in case some channels are shorter than others (by usually 1 or
        # 2)
        trunc = min([len(pksred[:]), len(minred[:]), len(pksir[:]),
                    len(minir[:].T)])
        pksred = pksred[0:trunc]
        pksir = pksir[0:trunc]
        minred = minred[0:trunc]
        minir = minir[0:trunc]

        # amplitude
        Ared = 0.5 * (pksred[:] - minred[:])
        Air = 0.5 * (pksir[:] - minir[:])

        eHbO2red, eHbred, _, eicg = getextinctioncoef(
            self.gui_vars, np.array([self.wv[0]]))
        eHbO2ir, eHbir, _, _ = getextinctioncoef(
            self.gui_vars, np.array([self.wv[1]]))

        eHbO2red = eHbO2red[0]
        eHbred = eHbred[0]
        eicg = eicg[0]
        eHbO2ir = eHbO2ir[0]
        eHbir = eHbir[0]

        # Flux of light. Corrects for div/0 errors in Air and Ared
        # phi = Air / Ared
        phi = np.array([])

        for i in range(len(Air.T)):
            try:
                phi = np.append(phi, Air[:, i][0] / Ared[i])
            except FloatingPointError:
                phi = np.append(phi, 0)
            except RuntimeError:
                phi = np.append(phi, 0)

        I = np.logical_and(tir > tbl[0], tir < tbl[1])
        # choose a baseline Phi for d calculation.
        phi0 = np.mean(phi[I.reshape((len(I.T),))])

        # distance of expansion, which is converted to concentration.
        d = phi0 * (eHbO2ir * SaO2 + eHbir * (1 - SaO2)) / (eHbO2red * SaO2 +
                                                            eHbred * (1 - SaO2))

        # find a d value to bring Ci to zero.
        Ci = (phi / d * (eHbO2ir * SaO2 + eHbir * (1 - SaO2)) - eHbO2red * SaO2 -
              eHbred * (1 - SaO2)) * tHb / eicg

        # iterpolate t and ca to the current temporal resolution of the SPY Elite,
        # which is fast enough preserve any features. sgolay filtering 51 x 3.
        t = np.linspace(tir[0, 0], tir[0, -1],
                        num=int(np.round(tir[0, -1] / 0.267)))

        cainterp = interpolate.PchipInterpolator(tir[0, :], Ci)
        ci_interp = cainterp(t)

        # interpolation to correct for nonlinearly spaced time points
        interp_ci = interpolate.interp1d(t, ci_interp)

        ci_result = interp_ci(np.linspace(t[0], t[-1], num=len(t)))
        # print("ci_result = ", ci_result)

        Ca = savgol_filter(ci_result, 51, 3)

        self.embedAIFplot(t, Ca)

        if self.savedata == 1:
            xout = np.hstack(
                (t.reshape((len(t), 1)), Ca.reshape((len(Ca), 1))))

            # parse the filename of the input file to suggest where to save the
            # output and what to call it.
            slashloc = self.strfind(self.filename, "/")

            sugpath = self.filename[0:slashloc[-1]+1]
            fnamein = self.filename[slashloc[-1]+1:]

            emdashloc = self.strfind(fnamein, '_')
            fnameout = 'AIF_' + \
                fnamein[(emdashloc[1]+1):(fnamein.find('.xls')-1)] + '.csv'

            # save file
            np.savetxt(sugpath + fnameout, xout, delimiter=",")

        return (t, Ca)

    def embedAIFplot(self, t, Ca):
        """Embeds raw AIF plot (concentration vs time) into Tkinter GUI. Allows user to choose left and right bounds of data to save

        Args:
            t (ndarray): time values
            Ca (ndarray): concentration values
        """
        def onclick(event):
            """When user clicks, add vertical lines. After second point, start saving data

            Args:
                event (Event): mouseclick event
            """
            if self.collect_x1:
                # Append to array of x-values
                self.x1.append(event.xdata)
                print("x1 = ", self.x1[-1])

                # vertical line at clicked point
                ax.axvline(self.x1[-1], color='red', linestyle='dashed')
                self.gui_vars.canvas.draw()
                self.gui_vars.canvas.flush_events()

                # If 2 points have been chosen
                if len(self.x1) == 2:
                    time.sleep(1)

                    # Stop collecting data from this instance of mpl_connect
                    self.collect_x1 = False
                    self.msg = ttk.Label(self.gui_vars.root, text='  ')
                    self.msg.grid(row=8)

                    # Make GUI smaller
                    self.gui_vars.root.geometry("460x285")

                    # Save data
                    s = AIF_Saving(self.x1, self.gui_vars)
                    s.crop_data(t, Ca)
                    self.gui_vars.fig.clf()
                    # self.gui_vars.msg = ttk.Label(self.gui_vars.root, text='AIF Saved')
                    self.gui_vars.msg.config(text='AIF Saved')

        # Enable this instance of mpl_connect
        self.collect_x1 = True

        # Plot data
        ax = self.gui_vars.fig.add_subplot()
        ax.plot(t, Ca)
        ax.set_xlabel('time (sec)')
        ax.set_ylabel('Concentration (uM)')
        ax.set_title(
            'Select the left and right bounds for the data to be saved')
        self.gui_vars.fig.subplots_adjust(left=.15)

        # Make plot respond to mouseclicks
        cid = self.gui_vars.fig.canvas.mpl_connect(
            'button_press_event', onclick)
        self.gui_vars.canvas.draw()

        # placing the canvas on the Tkinter window
        self.msg = ttk.Label(self.gui_vars.root, text='  ')
        self.msg.grid(row=8)
        self.gui_vars.canvas.get_tk_widget().grid(row=9, columnspan=2, padx=10)
        self.gui_vars.root.geometry("525x705")

        self.gui_vars.root.mainloop()

    def strfind(self, string: str, elt: str) -> tuple:
        """Finds indices of a substring in a string

        Args:
            string (str): string to be searched
            elt (str): single character to be found

        Returns:
            tuple: tuple of indices where character is located
        """
        result = []
        length = len(string)
        for i in range(length):
            if elt == string[i]:
                result.append(i)

        return result

    def find_peak_heights(self, data: list, indices: list) -> list:
        """Returns a list of the peak heights in data based on the indices of these peaks        

        Args:
            data (list): data in which peaks need to be found
            indices (list): list of indices where peaks appear

        Returns:
            list: returns list of the heights of the peaks specified in indices
        """

        result = []
        for i in indices:
            result.append(data[i])

        return result
