import socket
from threading import Thread
import time
import datetime
import numpy as np
import os
import csv

from config import KUKA_HOST, KUKA_PORT


class Kuka:
    def __init__(self, no_connect = False):
        if no_connect:
            return

        self.connect()
        self.position = [0, 0, 0]

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((KUKA_HOST, KUKA_PORT))
        print(f"Connected to KUKA robot at {KUKA_HOST}:{KUKA_PORT}")
        self.g_state.kuka_connected = True
        self.g_state.kuka_state = "idle"

    def disconnect(self):
        try:
            self.socket.sendall("exit\n".encode())
        finally:
            print("kuka disconnected")
            self.g_state.kuka_connected = False
            self.g_state.kuka_state = None

    def async_move(self, x: int, y: int, z: int, waiting_time=.5):
        cmd = f"move {x} {y} {z}"
        self.socket.sendall((cmd + "\n").encode())
        self.position = [x, y, z]
        time.sleep(waiting_time)

    def wait_for_encoder_data(self):
        self.g_state.encoder_value = None

        while not self.g_state.labview_connected:
            time.sleep(1)

        # wait for encoder_value to update to confirm labview comms are working
        print("waiting for encoder_value data stream...")
        for _ in range(30):
            if self.g_state.encoder_value is not None:
                break
            else:
                time.sleep(1)
        if self.g_state.encoder_value is None:
            print("encoder_value is not set. terminating connection to kuka")
            self.disconnect()
            return
        else:
            print("encoder_value is being updated properly.")

        return

    def wait_for_labview_state_data(self):
        while not self.g_state.labview_connected:
            time.sleep(1)

        # wait for encoder_value to update to confirm labview comms are working
        print("waiting for labview_state data stream...")
        for _ in range(30):
            if self.g_state.labview_state in ("finished", "start", "sweeping"):
                break
            else:
                time.sleep(1)
        if self.g_state.encoder_value is None:
            print("labview_state is not set. terminating connection to kuka")
            self.disconnect()
            return
        else:
            print("labview_state is being updated properly.")

        return



if __name__ == "__main__":
    kuka = Kuka(no_connect=True)

    # kuka.async_move(0,0,1)
    # kuka.disconnect()
