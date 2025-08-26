import socket
from threading import Thread
import time
import datetime
import numpy as np
import os
import csv

from config import xspan, yspan, d, zspan, dz, encoder_value_delta_threshold
from config import n_sweep_points
from config import KUKA_HOST, KUKA_PORT
from global_state import GlobalState


class Kuka:
    def __init__(self, g_state: GlobalState, no_connect = False):
        self.g_state = g_state

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

    def trace(self):
        self.g_state.kuka_state = "trace"
        self.wait_for_encoder_data()

        x = 0
        y = 0
        dy = d
        assert yspan == 0 or dy > yspan
        dx = d
        positions = []

        while x <= xspan: 
            while y >= 0 and y <= yspan:
                print(f"moving to next point: {x}, {y}")
                self.async_move(x, y, 0)

                print(f"moving down to contact surface")
                e0 = self.g_state.encoder_value
                z = 0
                while abs(e0 - self.g_state.encoder_value) < encoder_value_delta_threshold and abs(z) < zspan:
                    z -= dz 
                    self.async_move(x, y, z)

                print("recording surface data")
                time.sleep(1)
                encoder_deflection = (e0 - self.g_state.encoder_value) / 1000
                print(f"{encoder_deflection = }")
                z_record = z + encoder_deflection
                if abs(z_record) > zspan:
                    z_record = zspan * np.sign(z_record)
                print(f"record: {x},{y},{z_record}")
                positions.append([x,y,z_record])

                print("moving back up to z0")
                self.async_move(x, y, 0, waiting_time = 1)

                if yspan > 0:
                    y += dy
                else:
                    break

            x += dx
            print(f"x={x}/{xspan}")
            dy *= -1

        print(f"trace complete. {x=}, {xspan=}, {y=}, {yspan=}")
        self.save_data(positions)
        self.async_move(0, 0, 0, waiting_time=5)
        self.g_state.kuka_state = "trace done"
        self.g_state.encoder_data = None

        return


    def sweep(self):
        positions = self.load_data()
        x, y, z = self.position
        assert x==0 and y==0 and z <= 0
        self.g_state.kuka_state = "sweep"
        self.wait_for_labview_state_data()

        i_points = [int(i*(len(positions)-1)/(n_sweep_points-1)) for i in range(n_sweep_points)]
        z_offset = 50
        assert z_offset > 10

        for n,i in enumerate(i_points):
            x, y, z = positions[i]
            if n > 0:
                print(f"sweep point {n+1}/{len(i_points)}, moving kuka to {x}, {y}, {z}")
                self.async_move(x, y, z_offset, waiting_time=1)
            self.async_move(x, y, z, waiting_time=1)

            print("waiting for labview to begin sweep")
            while self.g_state.labview_state not in ("start", "sweeping"):
                time.sleep(.1)

            print("waiting for labview to finish sweep...")
            while self.g_state.labview_state != "finished":
                time.sleep(.1)

            self.async_move(x, y, z_offset, waiting_time=1)

        # move back to starting position
        self.async_move(0, 0, z_offset, waiting_time = 2)
        self.g_state.kuka_state = "sweep done"

        return


    def save_data(self, positions, prefix = "surface_data"):
        positions = np.array(positions)
        epoch_time = time.time()
        dt_object = datetime.datetime.fromtimestamp(epoch_time)
        formatted_time = dt_object.strftime("%Y-%m-%d_%H-%M-%S")
        filename = prefix + "_" + formatted_time
        np.savetxt(f"surface_data/{filename}.csv", positions, delimiter=",", header="x,y,z", comments='', fmt="%.3f")
        print(f"saved {prefix} in {os.getcwd()}")

    def load_data(self, prefix="surface_data"):
        csv_files = [
            os.path.join("surface_data", f)
            for f in os.listdir("surface_data")
            if f.lower().endswith('.csv')
            and os.path.isfile(os.path.join("surface_data", f))
            and f.startswith(prefix)
        ]
        if not csv_files:
            raise FileNotFoundError(f"no surface_data files found")

        # Find the most recently modified CSV file
        most_recent_file = max(csv_files, key=os.path.getmtime)
        print(f"loaded {prefix} from: {most_recent_file}")

        # Read the CSV file into a list of rows
        with open(most_recent_file, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            data = list(reader)

        positions = [[float(x), float(y), float(z)] for x,y,z in data[1:]]

        return positions


if __name__ == "__main__":
    g_state = GlobalState

    kuka = Kuka(g_state, no_connect=True)
    dummy_positions = []
    for i in range(400):
        dummy_positions.append([i, 2*i, 3*i])
    kuka.save_data(dummy_positions, prefix="dummy_data")
    positions = kuka.load_data(prefix="dummy_data")
    kuka.sweep(positions)


    # kuka = Kuka(g_state)
    # kuka.async_move(0,0,1)
    # kuka.disconnect()
