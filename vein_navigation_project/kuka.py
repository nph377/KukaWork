"""
for use with python_control.java
"""

import socket
import time
import sys

from config import KUKA_HOST, KUKA_PORT

class KukaState:
    IDLE = 0

class Kuka:
    def __init__(self):
        self.kuka_connected = False
        self.kuka_state = None

        self.connect()
        self.position = [0, 0, 0]

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((KUKA_HOST, KUKA_PORT))
        print(f"Connected to KUKA robot at {KUKA_HOST}:{KUKA_PORT}")
        self.kuka_connected = True
        self.kuka_state = KukaState.IDLE

    def disconnect(self):
        self.socket.sendall("exit\n".encode())
        print("kuka disconnected")
        self.kuka_connected = False
        self.kuka_state = None

    def send_command(self, cmd: str) -> str:
        self.socket.sendall((cmd + "\n").encode())

        response = None
        response = self.socket.recv(4096)

        return response
    
    def get_coordinates(self, print_log = False):
        """
        returns list: [x,y,z,a,b,c]
        x,y,z are in mm
        a,b,c are in radians
        """
        cmd = "send_coordinates"
        if print_log:
            cmd += " print_log"
        coords = self.send_command(cmd)
        coords = [float(v) for v in coords.strip().decode().split()]

        return coords

    # def async_move(self, x: int, y: int, z: int, waiting_time=.5):
    #     cmd = f"move {x} {y} {z}"
    #     self.socket.sendall((cmd + "\n").encode())
    #     self.position = [x, y, z]
    #     time.sleep(waiting_time)


if __name__ == "__main__":

    kuka = Kuka()

    # cmd = "send_coordinates print_log"
    # print(f"command: {cmd}")
    # r = kuka.send_command(cmd)
    # print(f"response: {r}, {sys.getsizeof(r)} bytes")

    c = kuka.get_coordinates(True)
    for v in c:
        print(v)

    kuka.disconnect()
