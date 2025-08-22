class GlobalState:
    def __init__(self):
        self.kuka_state = None
        self.kuka_connected = False
        self.labview_state = None
        self.labview_connected = False
        self.end_labview_connection = False
        self.encoder_value = None
