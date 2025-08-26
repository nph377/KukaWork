import socket
from config import WIFI_HOST, WIFI_PORT, BUFFER_SIZE
from global_state import GlobalState

class LabviewTCP:
    def __init__(self, g_state: GlobalState):
        self.g_state = g_state
        self.connect()

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((WIFI_HOST, WIFI_PORT))
            self.socket.listen(1)
            print(f"Waiting for labview TCP connection on port {WIFI_PORT}...")

            conn, addr = self.socket.accept()
            self.conn = conn
            self.addr = addr
            self.g_state.labview_connected = True
            self.g_state.labview_state = None
            print(f"Connected to labview TCP client: {addr}")
        except Exception as e:
            print(f"excpetion: {e}")


    def disconnect(self):
        g_state.end_labview_connection = True

    def receive_data(self):
        try:
            while not self.g_state.end_labview_connection:
                data = self.conn.recv(BUFFER_SIZE).decode()
                # print(f"received: {data} from labview")
                if isnum(data):
                    self.g_state.encoder_value = float(data)
                elif data.lower() in ("finished", "start", "sweeping"):
                    self.g_state.labview_state = data.lower()
                else:
                    print(f"labview data not recognized: {data=}, {type(data)=}")
        except Exception as e:
            print(f"Exception: {e}")
        finally:
            print("Ending labview TCP connection")
            self.g_state.labview_connected = False
            self.g_state.labview_state = None
            self.g_state.encoder_value = None

def isnum(data_string):
    try:
        data = float(data_string)
        return True
    except:
        return False

if __name__ == "__main__":
    g_state = GlobalState
    labview = LabviewTCP(g_state)


