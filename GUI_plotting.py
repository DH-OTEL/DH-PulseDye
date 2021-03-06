#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May  9 09:55:24 2021
@author: thomasusherwood
"""

import matplotlib
import matplotlib.pyplot as plt
import csv
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import serial
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
import os
import time
from o_loadAIF import o_loadAIF
from scipy import interpolate, signal
import numpy as np
from GUI_Vars import GUI_Vars


class SerialPlotting:
    # def __init__(self, filename):
    def __init__(self):

        # self.fileName = "Finger Probe Voltage_test.csv"
        self.COMt = None
        self.com = None
        self.now = None
        self.dt_string = None
        # Variables to store incoming data
        self.xs = []  # store sample numbers here (n)
        self.ys = []  # store RED temp values here
        self.y2s = []  # Store IR temp values here
        self.y3s = []  # Store RED ambient values here
        self.y4s = []  # Store IR ambient values here
        self.y5s = []  # Store RED raw - RED ambient values here
        self.y6s = []  # Store IR raw - IR ambient values here
        self.running = False
        self.prevtrue = False
        self.cfn = False
        self.fncreated = False
        self.msg = None
        self.progressbar = None
        self.SampleCount = 0
        # setting up csv file for arduino data
        self.fields = ['Ch : RED', 'Ch : RED AMBIENT', 'Ch : IR',
                       'Ch: IR AMBIENT', 'Ch : RED - RED AMBIENT', 'Ch : IR - IR AMBIENT']
        # Sets current directory for file management
        self.current_dir = os.getcwd()

        # To initialize tkinter, we have to create a Tk root widget, which is a window
        # with a title bar and other decoration provided by the window manager. The
        # root widget has to be created before any other widgets and there can only
        # be one root widget.
        self.root = tk.Tk()

        self.x0 = 0
        self.y0 = 0
        self.HR_fig_complete = False

    def getcom(self):
        self.com = self.COMt.get()
        print("com port =", self.com)

    def ComSelect(self, comframe):
        """
        Creates combo box selection of com port
        """
        self.COMt = tk.StringVar()
        combobox = ttk.Combobox(comframe, textvariable=self.COMt)
        combobox.grid(row=1, column=0)
        combobox.config(values=('COM1', 'COM2', 'COM3', 'COM4',
                        'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'COM10'))
        self.COMt.set('COM9')

    def openserial(self):
        # Intialize Serial Port
        self.getcom()  # sets COM port to whatever is selected in the combobox

        try:
            # sets baud rate
            # self.arduino = serial.Serial(self.com, 450000)
            self.arduino = serial.Serial(self.com, 230400)
        except:  # NameError:  # exception arduino not defined
            self.show_error("Wrong com port selected")

        # Check Serial Port is Open
        if self.arduino.is_open == True:
            print("\nAll right, serial port now open. Configuration:\n")
            print(self.arduino, "\n")  # print serial parameters

        # display the data to the terminal
        getData = str(self.arduino.readline())
        data = getData[0:][:-2]
        print(data)

    def CreateDateTime(self):
        # Create date and time variable dd/mm/YY H: M: S
        self.now = datetime.now()
        print(self.now)
        self.dt_string = [
            f'{self.now.month}/{self.now.day}/{self.now.year} ' +
            f'{self.now.hour}:{self.now.minute}:{self.now.second}']
        print("date and time =", self.dt_string)

    def cleardata(self):
        """
        Clears data to enable multiple runs using start & preview buttons
        """
        self.SampleCount = 0
        self.xs.clear()
        self.ys.clear()
        self.y2s.clear()
        self.y3s.clear()
        self.y4s.clear()
        self.y5s.clear()
        self.y6s.clear()

    def writedata(self, redraw, irraw, redtemp, irtemp, redtot, irtot):
        """
        Writes data to CSV
        """
        # Sets data directory for data storage
        dat_dir = self.current_dir + "/Data"

        # Creates Folder for Volts and ICG
        path = os.path.join(dat_dir, self.folderName)
        new_dir = os.mkdir(path)
        print(path)

        print(dat_dir)
        os.chdir(path)
        print(os.getcwd)

        print(self.fileName)

        with open(self.fileName, 'w', newline='') as f:
            # creating a csv writer object
            wc = csv.writer(f)

            # Write Field Names
            # wc.writerow(self.dt_string)
            wc.writerow([self.SaO2])
            # wc.writerow(['Volts'])
            wc.writerow([self.HbO2])
            wc.writerow(self.fields)
            print("Created File")

        with open(self.fileName, 'a', newline='') as f:
            # creating a csv writer object
            wc = csv.writer(f)

            for i in range(len(self.ys)):
                irow = [redraw[i], irraw[i], redtemp[i],
                        irtemp[i], redtot[i], irtot[i]]
                wc.writerow(irow)

    def stop_preview(self):
        end = time.time()
        self.running = False
        # show_message("Data from Preview, close windows to collect data")
        self.progressbar.stop()
        self.new_message("")

        # self.root.quit()
        self.prevtrue = False
        self.arduino.close()
        print("Time elapsed: ", end - self.start)
        self.plotdata()

    def dataread(self):
        """
        This function reads and stores the SPI data
        """
        if self.running:
            # Aquire and parse data from serial port
            line = self.arduino.readline()[:-2]
            line_as_list = line.split(b',')
            count = line_as_list[0]

            try:
                if len(line_as_list) != 4:  # Verifies that serial data is voltage values
                    raise Exception
                    # print("line as list = ", line_as_list)

            except Exception:
                print("skipped ", count)

            else:
                # i = int(line_as_list[0])
                REDtemp = line_as_list[0]
                IRtemp = line_as_list[1]
                REDamb = line_as_list[2]
                IRamb = line_as_list[3]

                REDtemp_as_list = REDtemp.split(b'\n')
                IRtemp_as_list = IRtemp.split(b'\n')
                REDamb_as_list = REDamb.split(b'\n')
                IRamb_as_list = IRamb.split(b'\n')

                try:
                    REDtemp_float = float(REDtemp_as_list[0])
                    IRtemp_float = float(IRtemp_as_list[0])
                    REDamb_float = float(REDamb_as_list[0])
                    IRamb_float = float(IRamb_as_list[0])

                    REDminus_float = REDtemp_float - REDamb_float
                    IRminus_float = IRtemp_float - IRamb_float
                except Exception as err:
                    print(err)
                else:

                    # Add x and y to lists
                    self.SampleCount += 1
                    self.xs.append(self.SampleCount)
                    self.ys.append(REDtemp_float)
                    self.y2s.append(IRtemp_float)
                    self.y3s.append(REDamb_float)
                    self.y4s.append(IRamb_float)
                    self.y5s.append(REDminus_float)
                    self.y6s.append(IRminus_float)
                    # print('Sample # = ', SampleCount, ', IR Raw = ',
                    #   IRtemp_float, ', RED Raw = ', REDtemp_float)
        if self.prevtrue:
            # progressbar.step(1)
            if self.SampleCount == 1500:
                self.stop_preview()
                # root.quit()
                # prevtrue = False

        self.root.update_idletasks()
        self.root.after(1, self.dataread)

    def plotdata(self):
        """
        Plots the data after it has been collected for verification
        """
        fig3, (ax1, ax2) = plt.subplots(nrows=2)

        ax1.plot(self.xs[5:-1], self.y6s[5:-1], label="IR Ambient")
        ax2.plot(self.xs[5:-1], self.y5s[5:-1],
                 label="RED Ambient", color='darkred')

        # Format plot
        plt.xticks(rotation=45, ha='right')
        plt.subplots_adjust(bottom=0.30)

        ax1.set_ylabel('IR Raw - Ambient (V)')
        ax2.set_ylabel('Red Raw - Ambient (V)')
        plt.xlabel('Sample #')

        plt.tight_layout()
        plt.show()

    def createfilename(self, patID, injID):
        """
        Creates filename from user input and datetime
        """
        # fn_string = [
        # f'{patID}_{injID}_{self.now.year}{self.now.month}{self.now.day}' +
        # f'_{self.now.hour}{self.now.minute}{self.now.second}.csv']

        fn_string = [
            f'{patID}_{injID}_{self.now.year}{self.now.month}{self.now.day}' +
            f'_{self.now.hour}{self.now.minute}{self.now.second}']

        # fileName = patID + "_" + injID + "_" + now.year + now.
        print("filename =", fn_string)
        fn_string = ' '.join(map(str, fn_string))

        self.fileName = fn_string + '_Volts' + '.csv'
        self.folderName = fn_string

    def dataentry(self, IDframe):
        """
        Creates widget to bring in user input for Patient and Injection ID
        """
        def retrieve():
            self.CreateDateTime()
            patID = my_entry.get()
            injID = my_entry2.get()
            print(patID)
            print(injID)
            self.cfn = True
            if self.cfn:
                self.createfilename(patID, injID)
                self.fncreated = True

        # sets the size of the GUI & prevents user from being able to resize
        self.root.geometry("450x245")
        # self.root.resizable(False, False)

        frame = ttk.Frame(self.root)
        frame.grid()

        my_entry = tk.Entry(IDframe, width=25)
        my_entry.insert(0, 'Patient ID (eg. DH-xxx)')
        my_entry.grid(row=1, column=0, padx=5, pady=5)

        my_entry2 = tk.Entry(IDframe, width=25)
        my_entry2.insert(0, 'Injection ID (eg. ICG-xx)')
        my_entry2.grid(row=2, column=0, padx=5, pady=5)
        submitbutton = tk.Button(IDframe, text="Submit", command=retrieve)
        submitbutton.grid(row=1, column=1, rowspan=2)

    def SaHb_input(self, SaHbframe):
        """
        User entry for SaO2 and HbO2
        """
        SaHblabel = ttk.Label(SaHbframe, text='Enter SaO2 & HbO2:',
                              font=('Arial', 10, 'bold'))
        SaHblabel.grid(row=0, column=0, columnspan=2)

        self.SaO2_label = ttk.Label(
            SaHbframe, text='SaO2 (decimal value):')
        self.SaO2_label.grid(row=1, column=0)
        self.SaO2_label.config(wraplength=80)

        self.SaO2_ent = ttk.Entry(SaHbframe, width=10)
        self.SaO2_ent.grid(row=1, column=1, padx=5, pady=5)

        self.HbO2_label = ttk.Label(SaHbframe, text='HbO2 (g/dL):')
        self.HbO2_label.grid(row=2, column=0, padx=5)
        self.HbO2_label.config(wraplength=75)

        self.HbO2_ent = ttk.Entry(SaHbframe, width=10)
        self.HbO2_ent.grid(row=2, column=1, padx=5, pady=5)

    def show_error(self, text):
        tk.messagebox.showerror("Error", text)

    def show_message(self, txt):
        # shows a message in the GUI
        self.msg = ttk.Label(self.root, text=txt)
        self.msg.grid(row=7, column=0)

    def new_message(self, txt):
        # Reconfigures message from GUI to allow new message
        self.msg.config(text=txt)

    def stop_collection(self):
        """
        Button to stop data collection & export collected data to CSV with timestamp
        """
        self.new_message("Data Collection complete")
        self.progressbar.stop()

        self.running = False

        # pulls in the SaO2 and HbO2 from entry boxes (defaults to 0 for both)
        self.SaO2 = self.SaO2_ent.get()
        self.HbO2 = self.HbO2_ent.get()
        if not self.SaO2:
            self.SaO2 = str(0)
        if not self.HbO2:
            self.HbO2 = str(0)

        print(self.SaO2)
        print(self.HbO2)

        self.writedata(self.ys, self.y3s, self.y2s, self.y4s, self.y5s,
                       self.y6s)
        print("filename = ", self.fileName)

        self.arduino.close()

        self.ICG_button["state"] = "normal"
        # print("you enabled it, great job!")

        self.plotdata()

    def start_collection(self):
        """
        Defines the command for starting the data collection
        """
        self.ICG_button["state"] = "disable"
        if self.fncreated:
            self.cleardata()  # Clears data from previous collection
            self.progressbar.config(mode='indeterminate')
            try:
                self.openserial()
            except:
                print("Serial Already Open")
            self.running = True
            self.progressbar.start()

            try:
                self.new_message("Data Collection in Progress")
            except:
                self.show_message("Data Collection in Progress")

            # Re-enters loop to read data from shield
            self.dataread()

        else:
            self.show_error("Enter Patient ID and Injection ID First")

    def preview_data(self):
        """
        Creates a preview of the Data
        """
        # progressbar.config(mode='determinate', maximum=1500, value=1)
        self.cleardata()

        self.running = True
        self.prevtrue = True
        self.openserial()

        self.dataread()
        try:
            self.new_message("Collecting Data for Preview")
        except:
            self.show_message("Collecting Data for Preview")

        self.progressbar.config(mode='indeterminate')
        self.progressbar.start()
        self.start = time.time()

    def ICG_Curve(self):
        print("ICG")
        o_loadAIF(self.folderName, GUI_Vars(
            self.root, self.fig, self.canvas))  # self.root)

    def start_GUI(self):
        print(self.current_dir)

        # Gives title to GUI
        self.root.title("Dye Densiometer GUI")

        # Configure Color for GUI
        self.root.configure(background='SlateGray3')
        self.style = ttk.Style()
        self.style.configure('Tframe', background='SlateGray3')
        self.style.configure('TButton', background='SlateGray3')
        self.style.configure('TLabel', background='SlateGray3')

        # Brings in pngs for GUI buttons & Icon
        stop_image = Image.open('Icons/stop3.bmp')

        # The (20, 20) is (height, width)
        stop_image = stop_image.resize((20, 20), Image.ANTIALIAS)
        end_button = ImageTk.PhotoImage(stop_image)

        start_image = Image.open('Icons/start3.bmp')
        # The (20, 20) is (height, width)
        start_image = start_image.resize((20, 20), Image.ANTIALIAS)
        record_button = ImageTk.PhotoImage(start_image)

        icon_image = Image.open('Icons/program_icon.png')
        icon = ImageTk.PhotoImage(icon_image)

        # creates gui figure
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)

        # Creates a Frame for Selections
        selframe = tk.Frame(self.root, background='Slategray3')
        selframe.grid(row=0, column=0)

        # Creates COM Port Selection Frame with embedded SaHb frame
        comframe = tk.Frame(selframe, background='Slategray3')
        comframe.grid(row=0, column=0, padx=10)
        commsg = ttk.Label(comframe, text='Select correct COM Port:',
                           font=('Arial', 10, 'bold'))
        commsg.grid(row=0, column=0)
        self.ComSelect(comframe)

        blankspace = ttk.Label(comframe, text=' ', )
        blankspace.grid(row=2, column=0)

        SaHbframe = tk.Frame(comframe, background='Slategray3')
        SaHbframe.grid(row=4, column=0, padx=5)

        # Creates the Patient ID and Injection ID Entry Frame
        IDframe = tk.Frame(selframe, background='Slategray3')
        IDframe.grid(row=0, column=2, pady=5)
        IDmsg = ttk.Label(
            IDframe, text="""Enter Patient & Injection ID
        then click \'submit\'""", font=('Arial', 10, 'bold'))
        IDmsg.grid(row=0, column=0)

        # Places widgets into the the GUI
        self.SaHb_input(SaHbframe)
        self.dataentry(IDframe)

        # Creates frame for preview, start and stop buttons in GUI
        frame = ttk.Frame(self.root)
        frame.grid(row=3, column=0, rowspan=3)

        # Creates a Preview Button for Previewing the Data
        preview_button = tk.Button(frame, text="Preview", fg="white",
                                   bg="black", command=self.preview_data,
                                   font=('Arial', 18))

        # Brings in GUI Icon
        self.root.iconphoto(False, icon)

        # Create a start button, passing two options:
        start_button = tk.Button(frame, text="Start", fg="green",
                                 command=self.start_collection,
                                 font=('Arial', 18), image=record_button)
        start_button.config(compound='left')

        # Create a stop button, passing two options:
        stop_button = tk.Button(frame, text="Stop", fg="red",
                                command=self.stop_collection,
                                font=('Arial', 18), image=end_button)
        stop_button.config(compound='left')

        # Create a ICG button, passing two options:
        self.ICG_button = tk.Button(frame, text="ICG Curve", fg="purple3",
                                    command=lambda: self.embedHRplot(GUI_Vars(self.root, self.fig, self.canvas)),
                                    font=('Arial', 18))
        self.ICG_button.config(compound='left')

        # Creates a progress bar
        self.progressbar = ttk.Progressbar(self.root, orient='horizontal',
                                           length=200)

        # Adds start, stop buttons, and progressbar to the frame
        preview_button.grid(row=0, column=0)
        start_button.grid(row=0, column=1)
        stop_button.grid(row=0, column=2)
        self.ICG_button.grid(row=0, column=3)
        self.progressbar.grid(row=6, column=0)
        self.progressbar.config(mode='indeterminate')

        # def onclick(event):
        #     x0 = event.xdata
        #     y0 = event.ydata
        #     print("x0 = ", x0, "y0 = ", y0)

        # t = np.arange(0, 3, .01)
        # self.fig.add_subplot().plot(t, 2 * np.sin(2 * np.pi * t))

        # cid = self.fig.canvas.mpl_connect('button_press_event', onclick)

        # canvas.draw()
        # canvas.get_tk_widget().grid(row=7)

        # Enters into the Tkinter event loop to make window appear:
        # After 1 millisecond, call scanning
        # self.root.after(1, self.dataread)

        # fig2 = plt.figure("t,ca plot")
        # plt.plot([i for i in range(101)], [i ** 2 for i in range(101)])
        # plt.xlabel('time (sec)')
        # plt.ylabel('Concentration (uM)')

        # self.drawframe = ttk.Frame(self.root)
        # self.drawframe.grid(row=4, column=0)

        # root1 = tk.Tk()
        # canvas = FigureCanvasTkAgg(fig2,
        #                            master=self.drawframe)
        # canvas.draw()

        # # placing the canvas on the Tkinter window
        # canvas.get_tk_widget().pack()

        # # creating the Matplotlib toolbar
        # toolbar = NavigationToolbar2Tk(canvas,
        #                                self.drawframe)
        # toolbar.update()

        # # placing the toolbar on the Tkinter window
        # canvas.get_tk_widget().pack()

        self.root.mainloop()

    def embedHRplot(self, gui_vars):
        """
        Embeds matplotlib figure into TKinter so that points can be selected from it
        """

        def onclick(event):
            if self.x0 == 0 and self.y0 == 0:
                self.x0 = event.xdata
                self.y0 = event.ydata
                print(f'{self.x0},{self.y0}')
                # gui_vars.fig.clf()
                plt.show(block=False)
                plt.close('all')
                gui_vars.canvas.draw()
                gui_vars.root.geometry("450x245")
                gui_vars.fig.set(facecolor=[159/255, 182/255, 205/255])
            else:
                print('inelse')
                plt.clf()
                return
                self.HR_fig_complete = True
                fig.canvas.mpl_disconnect(cid)

        ax = gui_vars.fig.add_subplot()

        x = [i for i in range(200)]
        y1 = [i**2 for i in range(200)]
        y2 = [2*i**2 for i in range(200)]

        ax.plot(x, y1, x, y2)
        ax.set_title("select the center of the heart-rate peak")
        ax.set_xlim(12, 180)
        ax.set_xlabel("frequency (beats per min).")

        # ('bpm vs P')
        # fig = plt.figure('bpm vs P')

        # plt.plot(bpm.T, P[0, :])
        # plt.plot(bpm.T, P[1, :])
        # plt.show()
        plt.title('Select the center of the heart-rate peak')
        plt.xlim(12, 180)
        # gui_vars.fig.add_subplot().xlabel('frequency (beats per min).')

        cid = gui_vars.fig.canvas.mpl_connect('button_press_event', onclick)


        # root = tk.Tk()
        # gui_vars.root.canvas = FigureCanvasTkAgg(gui_vars.fig,
        #  master=gui_vars.root)
        gui_vars.canvas.draw()

        # placing the canvas on the Tkinter window
        gui_vars.canvas.get_tk_widget().grid(row=8)
        gui_vars.root.geometry("500x650")

        # # creating the Matplotlib toolbar
        # # toolbar = NavigationToolbar2Tk(root.canvas,
        # #    root)
        # # toolbar.update()

        # # placing the toolbar on the Tkinter window
        # # root.canvas.get_tk_widget().grid()
        # gui_vars.root.canvas.get_tk_widget().grid(row=7)

        # ghr = plt.ginput(n=1, timeout=0, show_clicks=True)
        # ghr = ghr[0][0]
        # fhr = ghr / 60
        # plt.close('bpm vs P')
        gui_vars.root.mainloop()


if __name__ == "__main__":
    # splot = SerialPlotting("Finger Probe Voltage_002.csv")
    splot = SerialPlotting()
    splot.start_GUI()
