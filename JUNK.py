from GUI_Vars import GUI_Vars
import numpy as np
from pandas import read_csv
from typing import List
import os
# from GUI_Vars import GUI_Vars

script_dir = GUI_Vars.dir
# script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
rel_path = "AIF_Processing"
abs_file_path = os.path.join(script_dir, rel_path)

file_loc = 'AIF_Processing'
hb_file = os.path.join(file_loc, 'hemoglobin.dat')
nw_file = os.path.join(file_loc, 'newwater.dat')
icg_file = os.path.join(file_loc, 'icg.dat')
print(icg_file)
hemoglobin = np.array(
    read_csv(hb_file, delim_whitespace=True, header=None))
