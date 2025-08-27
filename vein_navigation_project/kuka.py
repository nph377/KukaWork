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

        self.kuka_connected = False
        self.kuka_state = "idle"

        self.connect()
        self.position = [0, 0, 0]


    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((KUKA_HOST, KUKA_PORT))
        print(f"Connected to KUKA robot at {KUKA_HOST}:{KUKA_PORT}")
        self.kuka_connected = True
        self.kuka_state = "idle"

    def disconnect(self):
        try:
            self.socket.sendall("exit\n".encode())
        except:
            print("unable to send exit to kuka")
        finally:
            print("kuka disconnected")
            self.kuka_connected = False
            self.kuka_state = None

    def string_command(self, cmd: str):
        self.socket.sendall((cmd + "\n").encode())

    def string_response(self):
        #TODO
        return

    # def async_move(self, x: int, y: int, z: int, waiting_time=.5):
    #     cmd = f"move {x} {y} {z}"
    #     self.socket.sendall((cmd + "\n").encode())
    #     self.position = [x, y, z]
    #     time.sleep(waiting_time)


if __name__ == "__main__":
    kuka = Kuka()

    kuka.string_command("hi")

    # kuka.async_move(0,0,1)
    kuka.disconnect()
