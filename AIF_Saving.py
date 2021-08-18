import os
import csv
import numpy as np
from typing import List


class AIF_Saving:
    """
    Class for saving the AIF file from processed data
    """

    def __init__(self, xdata, gui_vars):
        """
        Constructor for AIF_Saving
        """
        self.xdata = xdata
        self.gui_vars = gui_vars

    def crop_data(self, t, Ca):
        """Crops data based on inputs into second graph embedded into the GUI

        Args:
            t (ndarray): time values
            Ca (ndarray): Concentration values
        """
        xmin = min(self.xdata)
        xmax = max(self.xdata)

        # crop to the approprate part.
        x1 = self.find(t > xmin, True)
        x2 = self.find(t > xmax, True)

        # Rearrange cropped data into horizontally stacked matrix for saving to csv
        t_cropped = t[x1 - 1:x2] - t[x1]
        t_cropped = t_cropped.reshape((len(t_cropped), 1))
        Ca_cropped = Ca[x1 - 1:x2]
        Ca_cropped = Ca_cropped.reshape((len(Ca_cropped), 1))
        csv_matrix = np.hstack((t_cropped, Ca_cropped))

        # Find path to save file
        dir = self.gui_vars.dir
        path = os.path.normpath(dir)
        path_split = path.split(os.sep)

        # save to csv
        with open(dir + '_AIF.csv', 'w', newline='', encoding='utf-8') as csvfile:
            csvwriter = csv.writer(csvfile)
            for r in range(len(csv_matrix)):
                csvwriter.writerow(csv_matrix[r, :])

    def find(self, lst: List[float], elt: float) -> int:
        """Finds the index of the first instance of an element in a list

        Args:
            lst (List[float]): list to be searched
            elt (float): element to be found

        Returns:
            int: int index of the first instance of elt
        """
        for i in range(len(lst)):
            if elt == lst[i]:
                return i
