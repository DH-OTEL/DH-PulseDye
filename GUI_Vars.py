class GUI_Vars:
    def __init__(self, root, fig, canvas, dir, msg, current_dir, SaO2, tHb):
        self.root = root
        self.fig = fig
        self.canvas = canvas
        self.ax = None

        self.dir = dir
        self.msg = msg

        self.current_dir = current_dir

        self.SaO2 = float(SaO2)
        self.tHb = float(tHb)

        # # <-- absolute dir the script is in
        # self.script_dir = os.path.dirname(__file__)
