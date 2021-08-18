import os
import csv
import numpy as np
from TI_to_AIF import TI_to_AIF
import matplotlib.pyplot as plt
from typing import List

import time


class o_loadAIF:
    """
    Finds filename for appropriate volts file for post-processing to make AIF file
    """

    def __init__(self):
        """
        Constructor for o_loadAIF
        """
        self.xvals = []

    def save_AIF_file(self, gui_vars):
        """Finds filename for AIF file and calls AIF calculation functions

        Args:
            gui_vars (GUI_vars): GUI variables that need to be passed through several function calls
        """
        dir = gui_vars.dir

        # file was found with 'Volts' in it.
        path = os.path.normpath(dir)
        path_split = path.split(os.sep)
        filename = path_split[-1] + '_Volts.csv'

        wv = [804, 938]  # wavelength of probe LEDs.

        # Calculate and save AIF
        filt_method = 'upenn'  # upenn is best, simple is faster.
        t = TI_to_AIF(filename, gui_vars, wv, False, filt_method, 0)
        t.calculate_AIF()
